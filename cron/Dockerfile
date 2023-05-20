FROM mapapylife/api:latest
LABEL maintainer="David Sn <divad.nnamtdeis@gmail.com>"

# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends cron && rm -rf /var/lib/apt/lists/*

# Copy files and install crontab
ADD crontab /etc/cron.d/crontab
ADD cronjob.sh entrypoint.sh /usr/local/bin/
RUN crontab /etc/cron.d/crontab
RUN chmod +x /usr/local/bin/cronjob.sh /usr/local/bin/entrypoint.sh
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
