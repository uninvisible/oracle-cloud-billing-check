import os
import oci
import requests
import logging
import json
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone

# Load .env variables
load_dotenv()

# Configure logging to console and file
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.getenv("LOG_FILE_PATH")),
    ],
)

# Load OCI configuration from environment variables
oci_config = {
    "user": os.getenv("OCI_USER"),
    "fingerprint": os.getenv("OCI_FINGERPRINT"),
    "tenancy": os.getenv("OCI_TENANCY"),
    "region": os.getenv("OCI_REGION"),
    "key_file": os.getenv("OCI_KEY_FILE_PATH"),
}

# Initialize the UsageClient with the configuration
usage_client = oci.usage_api.UsageapiClient(oci_config)

# Specify the compartment OCID
compartment_id = os.getenv("COMPARTMENT_ID")

# Telegram bot details
bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
chat_id = os.getenv("TELEGRAM_CHAT_ID")
log_group_id = os.getenv("TELEGRAM_LOG_GROUP_ID")

# Path for the error counter JSON file
log_error_file_path = os.getenv("LOG_ERROR_FILE_PATH")


def initialize_counter_file():
    """Initialize the counter file if it doesn't exist."""
    if not os.path.exists(log_error_file_path):
        with open(log_error_file_path, "w") as file:
            json.dump({"none_counter": 0, "last_error_time": None}, file)


def read_counter_data():
    """Read the counter data from the JSON file."""
    with open(log_error_file_path, "r") as file:
        return json.load(file)


def write_counter_data(none_counter, last_error_time):
    """Write the counter data to the JSON file."""
    with open(log_error_file_path, "w") as file:
        json.dump({"none_counter": none_counter, "last_error_time": last_error_time}, file)


def get_start_of_current_day():
    """Get the start time of the current day in UTC."""
    now = datetime.now(timezone.utc)
    start_of_day = datetime(now.year, now.month, now.day, tzinfo=timezone.utc).strftime(
        "%Y-%m-%dT00:00:00.000Z"
    )
    return start_of_day


def get_end_of_current_day():
    """Get the end time of the current day in UTC."""
    start_of_next_day = (datetime.now(timezone.utc) + timedelta(days=1)).strftime(
        "%Y-%m-%dT00:00:00.000Z"
    )
    return start_of_next_day


def send_telegram_message(message, chat_id, parse_mode="Markdown"):
    """Send a message to the specified Telegram chat."""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": parse_mode}
    response = requests.post(url, data=payload)

    if response.status_code == 200:
        logging.info(f"Message sent successfully to chat {chat_id}: {message}")
    else:
        logging.error(f"Failed to send message to chat {chat_id}: {response.text}")
    response.raise_for_status()


def fetch_usage_data(start_time, end_time):
    """Fetch usage data from OCI."""
    usage_request = oci.usage_api.models.RequestSummarizedUsagesDetails(
        tenant_id=oci_config["tenancy"],
        time_usage_started=start_time,
        time_usage_ended=end_time,
        granularity="DAILY",
        is_aggregate_by_time=True,
    )
    try:
        response = usage_client.request_summarized_usages(
            request_summarized_usages_details=usage_request
        )
        return response
    except oci.exceptions.ServiceError as e:
        log_and_notify_error("Service error occurred", e)
        return None
    except Exception as e:
        log_and_notify_error("Unexpected error occurred", e)
        return None


def log_and_notify_error(message, exception):
    """Log an error message and notify via Telegram."""
    error_message = f"⚠️ Oracle Cloud Billing - {message}: {str(exception)}"
    logging.error(error_message)
    send_telegram_message(error_message, log_group_id)


def process_usage_data(usage_data):
    """Process the usage data and send alerts if necessary."""
    # Initialize counter file if it doesn't exist
    initialize_counter_file()

    # Read current counter data
    counter_data = read_counter_data()
    none_counter = counter_data["none_counter"]
    last_error_time = counter_data["last_error_time"]
    
    if not usage_data or not usage_data.data.items:
        logging.error("No usage data received or the data is malformed.")
        send_telegram_message("⚠️ Oracle Cloud Billing - No usage data received or the data is malformed.", log_group_id)
        none_counter += 1
        last_error_time = datetime.now(timezone.utc).isoformat()

    else:
        for item in usage_data.data.items:
            # Attempt to use computed_amount, fallback to attributed_cost
            cost = item.computed_amount if item.computed_amount is not None else float(item.attributed_cost)
            currency = item.currency
            if cost is None:
                none_counter += 1
                last_error_time = datetime.now(timezone.utc).isoformat()
                logging.error(f"Cost retrieval error: received None for cost. Data: {item}")
            elif cost == 0:
                logging.info(f"Cost: {cost} {currency} (Zero cost)")
                none_counter = 0  # Reset counter on successful data retrieval
            else:
                alert_message = (
                    "⚠️ Oracle Cloud Billing Alert!\n\n"
                    f"Cost is not zero. Cost: {cost} {currency}\n\n"
                    f"[Cost Management](https://cloud.oracle.com/account-management/cost-analysis?region={oci_config['region']})"
                )
                send_telegram_message(alert_message, chat_id, parse_mode="Markdown")
                none_counter = 0  # Reset counter on successful data retrieval

    # Write updated counter data back to the file
    write_counter_data(none_counter, last_error_time)

    # Send notification if there have been 12 consecutive errors
    if none_counter >= 12:
        error_message = (
            "⚠️ Oracle Cloud Billing - Error in retrieving cost data. "
            "12 consecutive errors detected."
        )
        send_telegram_message(error_message, log_group_id)
        none_counter = 0  # Reset counter after sending the notification
        write_counter_data(none_counter, last_error_time)

def check_billing_and_notify():
    """Main function to check billing and notify if there are any issues."""
    start_time = get_start_of_current_day()
    end_time = get_end_of_current_day()
    usage_data = fetch_usage_data(start_time, end_time)
    process_usage_data(usage_data)


if __name__ == "__main__":
    try:
        check_billing_and_notify()
    except requests.RequestException as e:
        log_and_notify_error("Request error occurred", e)
    except Exception as e:
        log_and_notify_error("Unexpected error occurred", e)
