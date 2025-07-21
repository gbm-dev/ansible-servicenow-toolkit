# Using Asset Tags with ServiceNow Integration

## Overview

The ServiceNow incident creator role now supports associating incidents with Configuration Items (CIs) using asset tags. This ensures incidents are properly linked to the correct hardware in your CMDB.

## Configuration

### 1. In Your Inventory

Add the `device_asset_tag` variable to devices:

```yaml
network_devices:
  hosts:
    core-sw-01:
      ansible_host: 10.1.1.1
      device_asset_tag: "P1000002"  # Asset tag from ServiceNow CMDB
```

### 2. In Health Check Roles

The asset tag is automatically passed to ServiceNow when creating incidents:

```yaml
- name: Create ServiceNow incident for connectivity failure
  include_role:
    name: servicenow_incident_creator
  vars:
    incident_short_description: "Device {{ inventory_hostname }} unreachable"
    # ... other vars ...
    # Asset tag is automatically included from inventory
```

### 3. Direct Usage

You can also specify asset tags directly when creating incidents:

```yaml
- name: Create incident with specific asset tag
  include_role:
    name: servicenow_incident_creator
  vars:
    incident_short_description: "Hardware failure detected"
    incident_asset_tag: "P1000002"
    # ... other vars ...
```

## How It Works

1. When an incident is created, the role checks if `incident_asset_tag` is provided
2. If found, it queries ServiceNow CMDB for CIs with that asset tag
3. The first matching CI is associated with the incident
4. If no asset tag is provided, it falls back to searching by hostname

## Benefits

- **Accurate CI Association**: Incidents are linked to the correct hardware
- **Better Impact Analysis**: ServiceNow can determine affected services
- **Simplified Inventory**: Use existing asset tags from your CMDB
- **Flexible Configuration**: Works with or without asset tags

## Example Output

When an incident is created with asset tag association:

```
ServiceNow Incident CREATED
- Number: INC0010005
- Sys ID: 2126fe72c3feae50a41c37cc05013136
- CI Associated: Yes
```

The incident is now linked to the CI with asset tag P1000002 in ServiceNow.