# Ansible ServiceNow Network Monitoring Integration

Automated network device monitoring with ServiceNow incident lifecycle management.

## Features

- **Automatic Incident Creation**: Creates incidents when devices fail health checks
- **Automatic Incident Closure**: Closes incidents when devices recover
- **Duplicate Prevention**: Won't create multiple incidents for the same issue
- **Asset Tag Integration**: Associates incidents with Configuration Items (CIs)
- **Configurable Urgency/Impact**: Based on device criticality (core vs access)
- **Scalable Design**: Handles hundreds of devices efficiently

## Quick Test

Test the incident lifecycle (create and auto-close):
```bash
ansible-playbook -i test_inventory.yml test_incident_lifecycle.yml
```

## Production Setup

1. Configure your devices in `inventory.yml`
2. Run `./monitoring_setup.sh` for setup instructions
3. Monitor runs every minute and:
   - Creates incidents for down devices
   - Closes incidents for recovered devices

## How It Works

### Device Goes Down
1. Health check fails (ping timeout)
2. Incident created with:
   - Correlation ID: `device_connectivity_HOSTNAME`
   - Asset tag association (if configured)
   - Appropriate urgency/impact

### Device Comes Back Up
1. Health check succeeds
2. System queries for open incidents with same correlation ID
3. Incidents automatically closed with resolution notes

## Incident Lifecycle Example

```
Time 00:00 - Device core-sw-01 fails ping test
           → Incident INC0010006 created (High urgency)

Time 00:05 - Device core-sw-01 responds to ping
           → Incident INC0010006 automatically closed
           → Close notes: "Device connectivity restored"
```

## Configuration

### Inventory with Asset Tags
```yaml
core-sw-01:
  ansible_host: 10.1.1.1
  device_asset_tag: "P1000002"  # Links to ServiceNow CI
```

### Urgency/Impact Rules
- Core devices: High/High
- Access devices: Medium/Medium
- Other devices: Low/Low

## ServiceNow Integration

- **Instance**: dev191473.service-now.com
- **Default Caller**: admin
- **Default Assignment Group**: Network
- **Categories**: network/connectivity

## Monitoring Architecture

```
Every Minute:
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Ansible   │────▶│ Device Check │────▶│  ServiceNow │
│   Playbook  │     │   (Ping)     │     │   API       │
└─────────────┘     └──────────────┘     └─────────────┘
                           │                      │
                           ▼                      ▼
                    ┌─────────────┐       ┌─────────────┐
                    │   Success   │       │   Failure   │
                    │ Close Ticket│       │Create Ticket│
                    └─────────────┘       └─────────────┘
```

## Testing

1. **Test connectivity**: `ansible -m ping -i inventory.yml all`
2. **Test incident creation**: `./test_failed_device.yml`
3. **Test full lifecycle**: `./test_incident_lifecycle.yml`
4. **Production run**: `./run_monitoring.yml`