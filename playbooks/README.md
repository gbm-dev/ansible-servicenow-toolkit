# Production Playbooks

Simple playbooks for running monitoring roles in production. These playbooks include the necessary ServiceNow vault variables and call the monitoring roles.

## Available Playbooks

- `connectivity_monitoring.yml` - Device reachability monitoring with ServiceNow incident management
- `interface_monitoring.yml` - Interface up/down monitoring with diagnostic log collection  
- `config_backup.yml` - Configuration backup with change detection

## Usage

```bash
# Run connectivity monitoring
ansible-playbook playbooks/connectivity_monitoring.yml

# Run interface monitoring
ansible-playbook playbooks/interface_monitoring.yml

# Run config backup
ansible-playbook playbooks/config_backup.yml

# Run against specific group
ansible-playbook playbooks/connectivity_monitoring.yml --limit critical_devices
```

## Scheduling

These playbooks control their own scheduling using `playbook_schedule` configuration:

```bash
cd scheduler/
python3 scheduler_factory.py           # Discover schedulable playbooks
python3 scheduler.py create-timers      # Create systemd timers
```

### Scheduling Inheritance

Playbooks can define their own schedule or inherit from roles:

**Playbook-defined schedule (preferred):**
```yaml
vars:
  playbook_schedule:
    enabled: true
    schedule: "*/5 * * * *"
    description: "Custom monitoring schedule"
```

**Role inheritance (automatic fallback):**
If no `playbook_schedule` is defined, the scheduler inherits from the role's `default_schedule_config`.

This gives you control over scheduling while maintaining backward compatibility.

## Variables

ServiceNow credentials are automatically loaded from inventory `group_vars/all.yml` which references vault variables. To override ServiceNow settings for specific playbooks, add a `vars:` section:

```yaml
- name: Custom Monitoring
  hosts: network_devices
  vars:
    servicenow_default_assignment_group: "network.critical"
    incident_urgency: "high"
  tasks:
    - include_role: { name: connectivity_monitoring }
```