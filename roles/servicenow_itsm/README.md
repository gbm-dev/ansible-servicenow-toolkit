# ServiceNow Incident Creator Role

A reusable Ansible role for creating ServiceNow incidents with duplicate prevention and Configuration Item (CI) association.

## Features

- Creates incidents in ServiceNow ITSM
- Prevents duplicate incidents using correlation IDs
- Automatically associates network devices with their CIs
- Updates existing incidents instead of creating duplicates
- Configurable retry logic for API calls
- Designed for use with rescue blocks in health check roles

## Requirements

- `servicenow.itsm` collection installed
- ServiceNow instance with API access
- Network devices configured as CIs in ServiceNow CMDB

## Role Variables

### Required Variables (must be provided by calling role)

```yaml
incident_short_description: "Brief description of the issue"
incident_description: "Detailed description with context"
incident_correlation_id: "unique_identifier_for_deduplication"
```

### Optional Variables

```yaml
incident_urgency: 3              # 1-3, default: 3
incident_impact: 3               # 1-3, default: 3  
incident_assignment_group: "network.operations"
incident_category: "network"
incident_subcategory: "router"
incident_work_notes: "Additional notes"
incident_ci_name: "device-name"  # defaults to inventory_hostname
```

## Usage Example

### In a Health Check Role

```yaml
# roles/device_uptime/tasks/main.yml
---
- name: Device connectivity check
  block:
    - name: Test device connectivity
      ansible.builtin.ping:
      register: ping_result

  rescue:
    - name: Create incident for failure
      include_role:
        name: servicenow_incident_creator
      vars:
        incident_short_description: "Device {{ inventory_hostname }} unreachable"
        incident_description: |
          Device connectivity check failed
          Error: {{ ansible_failed_result.msg }}
        incident_correlation_id: "connectivity_{{ inventory_hostname }}"
        incident_urgency: 2
```

### In a Playbook

```yaml
---
- name: Network monitoring with ServiceNow
  hosts: network_devices
  vars:
    vault_servicenow_host: "https://instance.service-now.com"
    vault_servicenow_username: "{{ vault_snow_user }}"
    vault_servicenow_password: "{{ vault_snow_pass }}"
  roles:
    - device_uptime
```

## Duplicate Prevention

The role checks for existing incidents with the same `correlation_id` within the configured time window (default: 2 hours). If found, it updates the existing incident instead of creating a new one.

## CI Association

The role automatically looks up the Configuration Item (CI) based on the device hostname and associates it with the incident. This helps with:
- Impact analysis
- Change management correlation
- Asset tracking

## Return Values

The role sets `servicenow_incident_result` fact with:
```yaml
servicenow_incident_result:
  action: "created|updated"
  number: "INC0001234"
  sys_id: "1234567890abcdef"
  ci_associated: true|false
```