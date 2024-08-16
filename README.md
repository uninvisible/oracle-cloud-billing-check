
# Oracle Cloud Billing Checker

This project monitors Oracle Cloud billing usage to ensure it remains within Always Free limits and sends alerts to a Telegram chat if the cost exceeds 0. It runs inside a Docker container with a cron job executing the script every hour.

## Setup Instructions

### Prerequisites

- Docker
- Docker Compose

### Environment Variables

Create a `.env` file in the root of your project directory with the following content:

```env
OCI_USER=ocid1.user.oc1..aasasdafsswc12312axalsdfsduskby5lmqsdfaoa
OCI_FINGERPRINT=41:av:dd:11:12:13:14:15:aa:dd:ff:cc:22:cc:71:5a
OCI_TENANCY=ocid1.tenancy.oc1..aasasdafsswc12312axalsdfsduskby5lmqsdfaoa
OCI_REGION=eu-amsterdam-1
OCI_KEY_FILE_PATH=/app/config/oci_private_key.pem
LOG_FILE_PATH=/app/logs/main.log
TELEGRAM_BOT_TOKEN=12345678:AVBhhx5cRsdfkslsdfsdfsAAADSFADh7-hk
TELEGRAM_CHAT_ID=12345678
TELEGRAM_LOG_GROUP_ID=-10012345678
```

You can obtain these environment variables from the Oracle Cloud Infrastructure (OCI) platform. Refer to the [OCI Documentation](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/apisigningkey.htm) for detailed steps on how to generate and obtain these credentials.

### Download the OCI Private Key

Download your `oci_private_key.pem` file, rename it to `oci_private_key.pem`, and place it in the `config` folder of your project directory. Refer to the [OCI Documentation](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/apisigningkey.htm) for instructions on how to generate this key.

## Project Structure

```
.
├── main.py
├── .env
├── Dockerfile
├── docker-compose.yaml
├── requirements.txt
└── config
    └── oci_private_key.pem
```

## Main Components

### main.py

This script:

1. Configures logging to both console and a log file.
2. Loads OCI configuration from environment variables.
3. Initializes the `UsageapiClient` with the OCI configuration.
4. Defines functions to get the start and end times of the current day in UTC.
5. Sends messages via a Telegram bot.
6. Fetches usage data from OCI and processes it.
7. Sends alerts if usage exceeds limits or if there are consecutive errors.

### Dockerfile

The Dockerfile is structured into two stages:

1. **Builder Stage**:
    - Installs Python dependencies and sets up the application.
    - Configures cron to run the script every hour.

2. **Production Stage**:
    - Copies the necessary files and dependencies from the builder stage.
    - Sets up and runs the cron job in the foreground.

### Updated Dockerfile Highlights

- Multi-stage build to reduce image size and improve build times.
- Cron job frequency updated to run the script every hour.
- Dependencies are installed in the builder stage and then copied to the final image.

### Deployment

To deploy the application, use Docker Compose or build the Docker image manually and run it. Ensure that your environment variables are correctly set up and that the `oci_private_key.pem` file is in the correct location.

#### Build and Run with Docker Compose

```sh
docker-compose up --build -d
```

#### Build and Run Manually

```sh
docker build -t oci-billing-checker .
docker run -d --env-file .env oci-billing-checker
```

This setup ensures that the billing checker runs efficiently with minimal overhead, and alerts are sent reliably based on the configured thresholds.