FROM python:3.11-slim
WORKDIR /app
COPY . /app
RUN pip install psycopg2-binary requests
# Install cron
RUN apt-get update && apt-get install -y cron
# Add crontab file
COPY crontab.txt /etc/cron.d/anomaly-cron
# Give execution rights on the cron job
RUN chmod 0644 /etc/cron.d/anomaly-cron
# Apply cron job
RUN crontab /etc/cron.d/anomaly-cron
# Start cron and run ingest.py once at container start
CMD service cron start && python ingest.py && tail -f /dev/null
