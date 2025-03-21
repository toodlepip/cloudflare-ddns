# Cloudflare Dynamic DNS Updater

This script updates a Cloudflare DNS record dynamically when the public IP address changes. It's going to come in handy if you have a server hosted on an ISP that allocated IP addresses via DHCP.

The script is written for Linux/macOS but could be easily adapted for other environments. Logging, error reporting and log rotation are handled on the first run, if they're not set up.

Error reporting via email will only be triggered, on error, if the email settings are included in settings.py.

## How It Works

- The script checks the current public IP address.
- It retrieves the existing DNS record from Cloudflare.
- If the public IP has changed, the script updates the Cloudflare DNS record.
- If an error occurs, an email notification is sent.

## Requirements

- A Cloudflare account with API access.
- An API Token with permissions to update DNS records.
- A domain managed in Cloudflare.
- Python 3 installed on your system.

## Setup

1. Clone this repository:
   ```sh
   git clone https://github.com/toodlepip/cloudflare-ddns.git
   cd cloudflare-ddns
   ```

2. Install required dependencies:
   ```sh
   pip install requests
   ```

3. Copy `settings.example.py` to `settings.py` and update it with your credentials:
   ```sh
   cp settings.example.py settings.py
   ```

4. Edit `settings.py` with your Cloudflare and email credentials:
   ```python
   CLOUDFLARE_API_KEY = "your-api-key-here"
   CLOUDFLARE_EMAIL = "your-email@example.com"
   ZONE_ID = "your-cloudflare-zone-id"
   RECORD_NAME = "your.domain.com"

   SMTP_SERVER = "your-smtp-server"
   SMTP_PORT = 587
   SMTP_USERNAME = "your-smtp-username"
   SMTP_PASSWORD = "your-smtp-password"
   EMAIL_FROM = "your-email@example.com"
   EMAIL_TO = "your-email@example.com"
   ```

## Usage

- Run the script manually:
  ```sh
  sudo python3 cf-update-dns.py
  ```

- Automate using a cron job:
  ```sh
  sudo vi /etc/crontab
  ```
  Add the following line to run the script every hour at 15 minutes past the hour:
  ```sh
  15 * * * * root /usr/bin/python3 /var/local/cloudflare-ddns/cf-update-dns.py
  ```

## Security Considerations

- **Do not commit `settings.py`** as it contains sensitive credentials.
- Use **strong API tokens** with limited permissions.
- Restrict file permissions for `settings.py`:
  ```sh
  chmod 600 settings.py
  ```

## Logging

- Logs are written to `/var/log/cloudflare-ddns.log`.
- Log rotation is automatically configured to prevent excessive growth.

## Troubleshooting

- Ensure you have the correct API permissions in Cloudflare.
- Check logs for errors:
  ```sh
  cat /var/log/cloudflare-ddns.log
  ```
- Verify that the script has the correct Python dependencies installed.

## License

MIT License