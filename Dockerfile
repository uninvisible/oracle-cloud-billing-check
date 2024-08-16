# Stage 1: Build stage
FROM python:3.9-slim as builder

# Set the working directory
WORKDIR /app

# Copy only requirements.txt to leverage Docker cache
COPY requirements.txt .

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application to the image
COPY . .

# Stage 2: Production stage
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy the application from the builder stage
COPY --from=builder /app /app

# Copy installed Python packages from the builder stage
COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Install cron and nano without updating cache
RUN apt-get update && apt-get install -y --no-install-recommends cron nano && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Ensure the logs directory exists
RUN mkdir -p /app/logs && touch /var/log/cron.log

# Configure cron job in one RUN command to reduce layers
RUN echo "0 * * * * /usr/local/bin/python /app/main.py >> /var/log/cron.log 2>&1" > /etc/cron.d/python-cron && \
    chmod 0644 /etc/cron.d/python-cron && \
    crontab /etc/cron.d/python-cron

# Run the cron in the foreground and tail the log file
CMD cron && tail -f /var/log/cron.log
