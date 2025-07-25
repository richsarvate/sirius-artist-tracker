FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install cron
RUN apt-get update && apt-get install -y cron

# Copy scripts
COPY . .

# Add cron jobs
RUN echo "*/30 * * * * python3 /app/getTracks.py >> /app/log.txt 2>&1" > /etc/cron.d/sirius-cron
RUN echo "0 2 * * 1 python3 /app/updateTrackedArtists.py >> /app/log.txt 2>&1" >> /etc/cron.d/sirius-cron
RUN echo "2 2 * * 1 curl http://backend:8000/restart >> /app/log.txt 2>&1" >> /etc/cron.d/sirius-cron
RUN chmod 0644 /etc/cron.d/sirius-cron
RUN crontab /etc/cron.d/sirius-cron

# Create log file
RUN touch /app/log.txt

# Start cron
CMD ["cron", "-f"]
