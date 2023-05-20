#!/bin/bash

echo TZ=$TZ >> /etc/environment
echo DB_URL=$DB_URL >> /etc/environment
echo AUTH_TOKEN=$AUTH_TOKEN >> /etc/environment

# Create log file if not exists
if [ ! -f /var/log/cron.log ]; then
    touch /var/log/cron.log
fi

echo "OK!"
cron && tail -f /var/log/cron.log
