# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install cron and any required packages
RUN apt-get update && apt-get install -y cron nano && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Make the Python scripts executable
RUN chmod +x main.py

# Ensure the logs directory exist
RUN mkdir -p /app/logs

# Configure cron job
RUN echo "* * * * * /usr/local/bin/python /app/main.py >> /var/log/cron.log 2>&1" > /etc/cron.d/python-cron && \
    chmod 0644 /etc/cron.d/python-cron && \
    crontab /etc/cron.d/python-cron

# Create the log file to be able to run tail
RUN touch /var/log/cron.log

# Run the cron in the foreground and tail the log file
CMD cron && tail -f /var/log/cron.log