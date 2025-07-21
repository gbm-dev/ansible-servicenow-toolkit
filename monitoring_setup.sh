#!/bin/bash
# Setup script for continuous monitoring with ServiceNow integration

cat << 'EOF'
Network Device Monitoring with ServiceNow Integration
====================================================

This monitoring system will:
1. Check device connectivity every minute
2. Create ServiceNow incidents when devices go down
3. Automatically close incidents when devices recover

Setup Instructions:
------------------

1. Encrypt your vault (if not already done):
   ansible-vault encrypt group_vars/all/vault.yml

2. Create systemd service: /etc/systemd/system/network-monitoring.service
   [Unit]
   Description=Network Device Monitoring with ServiceNow
   After=network.target

   [Service]
   Type=simple
   User=ansible
   ExecStart=/usr/bin/ansible-playbook -i /path/to/inventory.yml /path/to/production_monitoring.yml --vault-password-file /path/to/vault_pass.txt
   Restart=on-failure
   RestartSec=60

   [Install]
   WantedBy=multi-user.target

3. Create systemd timer: /etc/systemd/system/network-monitoring.timer
   [Unit]
   Description=Run Network Monitoring every minute
   Requires=network-monitoring.service

   [Timer]
   OnCalendar=*:*:00
   Persistent=true

   [Install]
   WantedBy=timers.target

4. Enable and start the timer:
   sudo systemctl daemon-reload
   sudo systemctl enable network-monitoring.timer
   sudo systemctl start network-monitoring.timer

5. Check status:
   sudo systemctl status network-monitoring.timer
   sudo journalctl -u network-monitoring.service -f

Alternative: Cron Setup
----------------------
Add to crontab:
* * * * * /usr/bin/ansible-playbook -i /path/to/inventory.yml /path/to/production_monitoring.yml --vault-password-file /path/to/vault_pass.txt >> /var/log/network-monitoring.log 2>&1

How It Works:
------------
- Device DOWN: Creates incident with correlation_id = "device_connectivity_HOSTNAME"
- Device UP: Finds open incidents with same correlation_id and closes them
- Duplicate Prevention: Won't create new incidents if one already exists
- Asset Association: Links incidents to CIs using asset tags from inventory

EOF