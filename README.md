
# Oracle Cloud Billing Checker

This project monitors Oracle Cloud billing usage to ensure it remains within Always Free limits and sends alerts to a Telegram chat if the cost exceeds 0. It runs inside a Docker container with a cron job executing the script every minute.

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

1. Configures logging to console and to a folder.
2. Loads OCI configuration from environment variables.
3. Initializes the `UsageapiClient` with the OCI configuration.
4. Defines functions to get the start and end times of the current day in UTC.
5. Sends messages via Telegram bot.
6. Fetches and processes usage data from Oracle Cloud.
7. Checks billing and sends notifications if any issues are detected.

### Dockerfile

This Dockerfile:

1. Uses an official Python runtime as the parent image.
2. Sets the working directory to `/app`.
3. Copies the current directory contents into the container at `/app`.
4. Installs the required packages specified in `requirements.txt`.
5. Installs cron and nano.
6. Ensures the logs directory exists.
7. Creates a custom crontab file to run the Python script every minute.
8. Runs the cron job when the container launches.

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

RUN apt-get update && apt-get install -y cron nano &&     apt-get clean &&     rm -rf /var/lib/apt/lists/*

RUN chmod +x main.py

RUN mkdir -p /app/logs

RUN echo "* * * * * /usr/local/bin/python /app/main.py >> /var/log/cron.log 2>&1" > /etc/cron.d/python-cron && \
    chmod 0644 /etc/cron.d/python-cron && \
    crontab /etc/cron.d/python-cron

RUN touch /var/log/cron.log

CMD cron && tail -f /var/log/cron.log
```

### docker-compose.yaml

Defines the Docker service:

```yaml
version: '3.8'

services:
  billing_checker:
    image: oci-billing-checker:latest
    build:
      context: .
      dockerfile: Dockerfile
    container_name: oci-billing-checker
    volumes:
      - ./config:/app/config
      - ./logs:/app/logs
    env_file:
      - .env
```

### requirements.txt

Necessary Python packages:

```
oci==2.129.2
requests==2.32.3
python-dotenv==1.0.1
```

## Running the Project

1. **Ensure the `.env` file and `oci_private_key.pem` file are present**: Verify that the `.env` file is correctly filled and located in your project directory, and the `oci_private_key.pem` file is in the `config` directory.

2. **Build the Docker image**: 
   ```sh
   docker compose build
   ```

3. **Run the Docker container**: 
   ```sh
   docker compose up -d
   ```

4. **Check logs**:
   ```sh
   docker compose logs -f
   ```

This project will continuously monitor your Oracle Cloud billing usage and send alerts to the specified Telegram chat if any charges are detected.
