import os
import oci
import requests
import logging
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
    return usage_client.request_summarized_usages(
        request_summarized_usages_details=usage_request
    )


def process_usage_data(usage_data):
    """Process the usage data and send alerts if necessary."""
    for item in usage_data.data.items:
        cost = item.computed_amount
        currency = item.currency
        if cost != 0:
            alert_message = (
                "⚠️ Oracle Cloud Billing Alert!\n\n"
                f"Cost is not zero. Cost: {cost} {currency}\n\n"
                f"[Cost Management](https://cloud.oracle.com/account-management/cost-analysis?region={oci_config['region']})"
            )
            send_telegram_message(alert_message, chat_id, parse_mode="Markdown")
        else:
            logging.info(f"Cost: {cost} {currency}")


def check_billing_and_notify():
    """Main function to check billing and notify if there are any issues."""
    try:
        start_time = get_start_of_current_day()
        end_time = get_end_of_current_day()
        usage_data = fetch_usage_data(start_time, end_time)
        process_usage_data(usage_data)
    except oci.exceptions.ServiceError as e:
        error_message = f"⚠️ Oracle Cloud Billing - Service error occurred: {str(e)}"
        logging.error(error_message)
        send_telegram_message(error_message, log_group_id)
    except requests.RequestException as e:
        error_message = f"⚠️ Oracle Cloud Billing - Request error occurred: {str(e)}"
        logging.error(error_message)
        send_telegram_message(error_message, log_group_id)
    except Exception as e:
        error_message = f"⚠️ Oracle Cloud Billing - Unexpected error occurred: {str(e)}"
        logging.error(error_message)
        send_telegram_message(error_message, log_group_id)


if __name__ == "__main__":
    check_billing_and_notify()
