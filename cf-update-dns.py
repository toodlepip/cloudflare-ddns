# Built with the guide here:
# https://akashrajpurohit.com/blog/dynamic-dns-made-easy-with-cloudflare-api/
#
# Needs a cron job so this is run at reasonably regular intervals in case the
# IP address changes dynamically. Add to /etc/crontab
# This is fairly infrequently eg.
#
# Every hour at 15 mins past
# 15 * * * * root /usr/bin/python3 /var/local/cloudflare-ddns/cf-update-dns.py

import requests
import json
import logging
import smtplib
from email.mime.text import MIMEText
import os
import grp
import settings  # Confidential values are stored in settings.py

# Ensure correct permissions for the log file
def setup_logging():
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'w'):
            pass  # Create the file if it doesn't exist
    adm_gid = grp.getgrnam("adm").gr_gid
    os.chown(LOG_FILE, 0, adm_gid)  # Ensure user ownership
    os.chmod(LOG_FILE, 0o640)  # Read/write for root, read for adm group

def ensure_logrotate():
    logrotate_config = "/etc/logrotate.d/cloudflare-ddns"
    if not os.path.exists(logrotate_config):
        with open(logrotate_config, 'w') as f:
            f.write(
                "/var/log/cloudflare-ddns.log {\n"
                "    su root adm\n"
                "    weekly\n"
                "    rotate 4\n"
                "    compress\n"
                "    delaycompress\n"
                "    missingok\n"
                "    notifempty\n"
                "    copytruncate\n"
                "}\n"
            )
# -------------------------
# CONFIGURATION
# -------------------------

# Logging
LOG_FILE = "/var/log/cloudflare-ddns.log"

setup_logging()
ensure_logrotate()

# Cloudflare Configuration
CLOUDFLARE_API_KEY = settings.CLOUDFLARE_API_KEY
CLOUDFLARE_EMAIL = settings.CLOUDFLARE_EMAIL
ZONE_ID = settings.ZONE_ID  # Cloudflare Zone ID
RECORD_NAME = settings.RECORD_NAME

# Email Notification Configuration
SMTP_SERVER = settings.SMTP_SERVER  # Replace with actual SMTP server
SMTP_PORT = settings.SMTP_PORT
SMTP_USERNAME = settings.SMTP_USERNAME  # Replace with valid credentials
SMTP_PASSWORD = settings.SMTP_PASSWORD
EMAIL_FROM = settings.EMAIL_FROM
EMAIL_TO = settings.EMAIL_TO

logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Get the current public IP address
def get_public_ip():
    response = requests.get("https://cloudflare.com/cdn-cgi/trace")
    for line in response.text.split("\n"):
        if line.startswith("ip="):
            return line.split("=")[1]
    return None

# Get the current IP address on Cloudflare
def get_cloudflare_ip():
    url = f"https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/dns_records?name={RECORD_NAME}"
    headers = {
        "Authorization": f"Bearer {CLOUDFLARE_API_KEY}",  # Use Bearer for API Token
        "Content-Type": "application/json",
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        records = response.json().get("result", [])
        for record in records:
            if record["name"] == RECORD_NAME:
                return record["content"], record["id"]
    return None, None

# Update the IP address on Cloudflare
def update_cloudflare_ip(record_id, new_ip):
    url = f"https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/dns_records/{record_id}"
    headers = {
        "X-Auth-Email": CLOUDFLARE_EMAIL,
        "Authorization": f"Bearer {CLOUDFLARE_API_KEY}",
        "Content-Type": "application/json",
    }
    data = {
        "type": "A",
        "name": RECORD_NAME,
        "content": new_ip,
        "ttl": 1,
        "proxied": True,
    }

    response = requests.put(url, headers=headers, data=json.dumps(data))
    if response.status_code != 200:
        error_msg = f"Failed to update DNS record. Response: {response.text}"
        logging.error(error_msg)
        send_error_email(error_msg)
        return False
    return True

def send_error_email(error_message):
    subject = "Pickle: Cloudflare DDNS Update Error"
    body = f"An error occurred during the Cloudflare DDNS update:\n\n{error_message}"

    # Ensure email settings are present
    required_settings = [SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, EMAIL_FROM, EMAIL_TO]
    if any(setting in [None, ""] for setting in required_settings):
        logging.warning("Skipping error email: SMTP settings are not fully configured.")
        return

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())
            logging.info("Error email sent successfully.")
    except Exception as e:
        logging.error(f"Failed to send error email: {e}")

def main():
    public_ip = get_public_ip()
    
    if not public_ip:
        error_msg = "Could not determine public IP address."
        logging.error(error_msg)
        send_error_email(error_msg)
        return

    cf_ip, record_id = get_cloudflare_ip()
    if not cf_ip or not record_id:
        error_msg = "Could not retrieve DNS record from Cloudflare."
        logging.error(error_msg)
        send_error_email(error_msg)
        return

    if public_ip != cf_ip:
        if update_cloudflare_ip(record_id, public_ip):
            logging.info(f"Updated Cloudflare DNS record: {RECORD_NAME} -> {public_ip}")
        else:
            error_msg = "Failed to update DNS record."
            logging.error(error_msg)
            send_error_email(error_msg)
    else:
        logging.info("No update needed. IP address is unchanged.")

if __name__ == "__main__":
    main()