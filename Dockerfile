# Use a smaller official Python runtime as a parent image
FROM python:3.9-alpine as base

# Install build dependencies and cron
RUN apk add --no-cache --virtual .build-deps gcc musl-dev libffi-dev \
    && apk add --no-cache cron

# Set the working directory to /app
WORKDIR /app

# Copy only the requirements.txt first, to leverage Docker cache
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Make the Python scripts executable
RUN chmod +x main.py

# Ensure the logs directory exists and create a placeholder for the error counter file
RUN mkdir -p /app/logs && \
    echo '{"none_counter": 0, "last_error_time": null}' > /app/logs/error_counter.json

# Configure cron job to run the script every hour
RUN echo "0 * * * * /usr/local/bin/python /app/main.py >> /var/log/cron.log 2>&1" > /etc/cron.d/python-cron && \
    chmod 0644 /etc/cron.d/python-cron && \
    crontab /etc/cron.d/python-cron

# Create the log file to be able to run tail
RUN touch /var/log/cron.log

# Run the cron in the foreground and tail the log file
CMD cron && tail -f /var/log/cron.log

# Final image
FROM base as final

# Remove build dependencies to reduce the image size
RUN apk del .build-deps

# Run the cron in the foreground and tail the log file
CMD cron && tail -f /var/log/cron.log