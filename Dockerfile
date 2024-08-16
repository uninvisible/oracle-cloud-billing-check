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

# Install cron and any required packages in a single RUN command
RUN apt-get update && apt-get install -y --no-install-recommends cron nano && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Make the Python scripts executable
RUN chmod +x main.py

# Ensure the logs directory exists
RUN mkdir -p /app/logs

# Configure cron job in one RUN command to reduce layers
RUN echo "* * * * * /usr/local/bin/python /app/main.py >> /var/log/cron.log 2>&1" > /etc/cron.d/python-cron && \
    chmod 0644 /etc/cron.d/python-cron && \
    crontab /etc/cron.d/python-cron && \
    touch /var/log/cron.log

# Stage 2: Production stage
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy only necessary files from the builder stage
COPY --from=builder /app /app
COPY --from=builder /etc/cron.d/python-cron /etc/cron.d/python-cron
COPY --from=builder /var/log/cron.log /var/log/cron.log

# Install cron and nano without updating cache
RUN apt-get update && apt-get install -y --no-install-recommends cron nano && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Run cron and also tail the log file to stdout
CMD ["sh", "-c", "cron && tail -f /var/log/cron.log"]