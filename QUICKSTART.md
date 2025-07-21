# ServiceNow Incident Creator - Quick Start Guide

## Installation

1. Install the ServiceNow ITSM collection:
```bash
ansible-galaxy collection install servicenow.itsm
```

2. Clone this repository or copy the `servicenow_incident_creator` role to your roles directory.

## Basic Setup

1. Set your ServiceNow credentials (use ansible-vault in production):
```bash
export SERVICENOW_HOST="https://your-instance.service-now.com"
export SERVICENOW_USERNAME="your-username"
export SERVICENOW_PASSWORD="your-password"
```

2. Create a simple monitoring playbook:
```yaml
# monitor.yml
---
- name: Monitor network devices
  hosts: network_devices
  gather_facts: no
  vars:
    servicenow_host: "{{ lookup('env', 'SERVICENOW_HOST') }}"
    servicenow_username: "{{ lookup('env', 'SERVICENOW_USERNAME') }}"
    servicenow_password: "{{ lookup('env', 'SERVICENOW_PASSWORD') }}"
  roles:
    - device_uptime
```

3. Run the playbook:
```bash
ansible-playbook -i inventory.yml monitor.yml
```

## Creating Your Own Health Check Roles

Use this pattern for any health check that needs ServiceNow integration:

```yaml
# roles/your_health_check/tasks/main.yml
---
- name: Your health check with ServiceNow integration
  block:
    - name: Perform health check
      # Your check logic here
      
  rescue:
    - name: Create incident on failure
      include_role:
        name: servicenow_incident_creator
      vars:
        incident_short_description: "Your issue summary"
        incident_description: "Detailed description"
        incident_correlation_id: "unique_id_for_deduplication"
```

## Testing

Test with a single device first:
```bash
ansible-playbook -i inventory.yml monitor.yml --limit edge-rtr-01
```

## Architecture Benefits

- **Modular**: Each health check is a separate role
- **Reusable**: ServiceNow logic is centralized
- **Flexible**: Mix and match health checks as needed
- **Scalable**: Run different checks at different intervals