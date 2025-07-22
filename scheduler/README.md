# Ansible ServiceNow Monitoring Scheduler

Automated discovery and systemd-based scheduling for Ansible monitoring roles.

## Overview

The Monitoring Scheduler is a factory-pattern based system that automatically discovers monitoring roles and creates systemd services and timers for reliable, persistent execution. It eliminates the need for manual cron configuration and provides enterprise-grade scheduling with logging and monitoring capabilities.

## Architecture

### Design Patterns

1. **Factory Pattern**: `SchedulerFactory` discovers and validates monitoring roles
2. **Template Pattern**: Jinja2 templates generate systemd service files
3. **Command Pattern**: CLI interface for management operations
4. **Strategy Pattern**: Different scheduling strategies per role type

### Core Components

```
scheduler/
├── scheduler.py                    # Main orchestrator and CLI
├── scheduler_factory.py           # Role discovery factory
├── templates/
│   ├── systemd_service.j2         # Systemd service file template
│   └── systemd_timer.j2           # Systemd timer file template
└── README.md                       # This documentation
```

## How It Works

### Automatic Role Discovery

The factory scans the `roles/` directory and discovers roles with monitoring capabilities:

1. **Scan Process**: Iterates through all role directories  
2. **Configuration Detection**: Looks for `default_schedule_config` in `defaults/main.yml`
3. **Validation**: Ensures required fields are present and valid
4. **Exclusion**: Automatically skips wrapper roles like `servicenow_itsm`

### Role Discovery Criteria

A role is considered "monitorable" if it has a `default_schedule_config` section:

```yaml
# roles/<role_name>/defaults/main.yml
default_schedule_config:
  schedule: "*/5 * * * *"                # Cron-style schedule
  description: "Role description"         # Human-readable description
  inventory_groups: [network_devices]    # Target inventory groups
  timeout: 300                           # Execution timeout (seconds)
```

### Systemd Service Generation

For each discovered role, the scheduler generates:

1. **Service File** (`.service`): Defines how to execute the monitoring role
2. **Timer File** (`.timer`): Defines when to execute (schedule)
3. **Logging**: Centralized logs in `/var/log/ansible-monitoring/`
4. **Security**: Isolated execution with minimal privileges

## Usage

### Command Line Interface

```bash
# Discover available monitoring roles
python3 scheduler.py discover

# Show detailed role summary with statistics
python3 scheduler.py summary

# Create systemd timers (dry run - safe to test)
python3 scheduler.py create-timers --dry-run

# Create systemd timers for production
sudo python3 scheduler.py create-timers --inventory ../inventory/production.yml

# Show status of all monitoring services
python3 scheduler.py status
```

### Discovery Output Example

```bash
$ python3 scheduler.py discover
Discovered 1 monitoring roles:
  - device_uptime: device-uptime-monitor
```

### Summary Output Example

```bash
$ python3 scheduler.py summary
Monitoring Roles Summary:
========================================
{
  "total_roles": 1,
  "enabled_roles": 1,
  "role_types": {
    "device_monitoring": 1
  },
  "inventory_groups": [
    "network_devices",
    "core_switches", 
    "access_switches",
    "routers"
  ],
  "schedules": {
    "*/5 * * * *": 1
  }
}
```

### Status Output Example

```bash
$ python3 scheduler.py status
Monitoring Services Status (1 roles):
============================================================

device_uptime
   Description: Network device connectivity monitoring with ServiceNow integration
   Schedule: */5 * * * *
   Service: ACTIVE
   Timer: ACTIVE
```

## Configuration

### Role Configuration

Each monitoring role must include a `monitoring_config` section in its `defaults/main.yml`:

```yaml
---
# Your role-specific configuration
role_timeout: 30
role_retries: 2

# Default scheduling configuration (for playbook inheritance)
default_schedule_config:
  schedule: "0 */6 * * *"  # Every 6 hours
  description: "Security vulnerability scanning with incident management"
  inventory_groups:
    - network_devices
    - security_critical
  timeout: 600
```

### Configuration Fields Reference

| Field | Required | Description | Example |
|-------|----------|-------------|---------|
| `schedule` | Yes | Cron-format schedule | `"*/5 * * * *"` |
| `description` | Yes | Human-readable description | `"Network monitoring"` |
| `inventory_groups` | Yes | Target Ansible inventory groups | `["network_devices"]` |
| `timeout` | No | Execution timeout in seconds | `300` |

### Schedule Format

Schedules use standard cron format:

```
# ┌───────────── minute (0 - 59)
# │ ┌───────────── hour (0 - 23)
# │ │ ┌───────────── day of the month (1 - 31)
# │ │ │ ┌───────────── month (1 - 12)
# │ │ │ │ ┌───────────── day of the week (0 - 6) (Sunday to Saturday)
# │ │ │ │ │
# │ │ │ │ │
# * * * * *

*/5 * * * *    # Every 5 minutes
0 * * * *      # Every hour
0 0 * * *      # Daily at midnight
0 */6 * * *    # Every 6 hours
```

## Systemd Integration

### Generated Service Files

The scheduler creates systemd service files with:

- **Security hardening**: Minimal privileges, filesystem isolation
- **Logging**: Centralized log files with rotation
- **Environment**: Proper Ansible environment variables
- **Timeouts**: Configurable execution timeouts
- **Working directory**: Set to project root

### Generated Timer Files

Timer files include:

- **Calendar scheduling**: Converted from cron format
- **Randomization**: Prevents thundering herd effects
- **Persistence**: Runs missed executions after boot
- **Accuracy**: Configurable timing precision

### Service Naming Convention

The scheduler automatically derives systemd service names:

- **Pattern**: `<role_name>-monitor`
- **Examples**:
  - `device_uptime` → `device-uptime-monitor.service`
  - `security_scan` → `security-scan-monitor.service`
  - `config_drift` → `config-drift-monitor.service`

### File Locations

```
/etc/systemd/system/
├── device-uptime-monitor.service
├── device-uptime-monitor.timer
└── ...

/var/log/ansible-monitoring/
├── device-uptime-monitor.log
├── device-uptime-monitor.error.log
└── ...
```

## Production Deployment

### Prerequisites

1. **Root/sudo access**: Required for systemd service installation
2. **Python 3.8+**: For scheduler execution
3. **Ansible**: For monitoring role execution
4. **ServiceNow ITSM Collection**: For ServiceNow integration

### Installation Steps

1. **Verify role discovery**:
```bash
python3 scheduler.py discover
```

2. **Test configuration (dry run)**:
```bash
python3 scheduler.py create-timers --dry-run
```

3. **Install services**:
```bash
sudo python3 scheduler.py create-timers --inventory ../inventory.yml
```

4. **Verify installation**:
```bash
python3 scheduler.py status
systemctl list-timers | grep monitor
```

### Post-Installation Verification

```bash
# Check timer status
systemctl status device-uptime-monitor.timer

# View recent executions
journalctl -u device-uptime-monitor.service --since "1 hour ago"

# Monitor real-time logs
tail -f /var/log/ansible-monitoring/device-uptime-monitor.log

# Check next execution time
systemctl list-timers device-uptime-monitor.timer
```

## Monitoring and Maintenance

### Service Management

```bash
# Start/stop/restart timers
sudo systemctl start device-uptime-monitor.timer
sudo systemctl stop device-uptime-monitor.timer
sudo systemctl restart device-uptime-monitor.timer

# Enable/disable timers (persistence across reboots)
sudo systemctl enable device-uptime-monitor.timer
sudo systemctl disable device-uptime-monitor.timer

# Trigger immediate execution (bypass timer)
sudo systemctl start device-uptime-monitor.service
```

### Log Management

```bash
# View service logs
journalctl -u device-uptime-monitor.service

# Follow logs in real-time
journalctl -u device-uptime-monitor.service -f

# View application logs
tail -f /var/log/ansible-monitoring/device-uptime-monitor.log

# Rotate logs (if needed)
sudo logrotate /etc/logrotate.d/ansible-monitoring
```

### Troubleshooting

#### Common Issues

1. **Role not discovered**:
   - Check `default_schedule_config` in `defaults/main.yml`
   - Validate YAML syntax

2. **Service creation fails**:
   - Check sudo permissions
   - Verify systemd is running
   - Check disk space in `/etc/systemd/system/`

3. **Timer not executing**:
   - Check timer status: `systemctl status <service>.timer`
   - Verify schedule format
   - Check system time/timezone

4. **Service execution fails**:
   - Check service logs: `journalctl -u <service>.service`
   - Verify inventory file exists
   - Check Ansible configuration
   - Validate ServiceNow credentials

#### Debug Mode

Enable debug logging:

```bash
# Modify service file temporarily
sudo systemctl edit device-uptime-monitor.service

# Add:
[Service]
Environment="ANSIBLE_DEBUG=1"
Environment="ANSIBLE_VERBOSITY=3"
```

## Advanced Configuration

### Custom Templates

You can customize the systemd service templates:

1. **Copy templates**:
```bash
cp templates/systemd_service.j2 templates/systemd_service.custom.j2
```

2. **Modify template**:
```jinja2
# Add custom environment variables
Environment="CUSTOM_VAR=value"

# Add custom security settings
ProtectKernelTunables=true
```

3. **Update scheduler to use custom template** (modify `scheduler.py`)

### Multiple Inventory Files

This system now uses playbook-level scheduling - see the main README for current scheduling approach.

### Custom Logging

Configure custom log paths:

```python
# In scheduler.py
service_manager = SystemdServiceManager(
    project_path,
    log_path="/custom/log/path"
)
```

## Integration with Existing Systems

### Monitoring Integration

The scheduler services can be monitored by:

- **Nagios/Icinga**: Check timer status and last execution
- **Prometheus**: Export metrics from systemd
- **Grafana**: Visualize execution patterns and failures
- **Zabbix**: Monitor service availability and logs

### Log Aggregation

Integrate with log aggregation systems:

- **ELK Stack**: Forward logs to Elasticsearch
- **Splunk**: Monitor application logs
- **Fluentd**: Collect and forward logs
- **rsyslog**: Centralized logging

### Example Prometheus Monitoring

```bash
# Export systemd metrics
node_exporter --collector.systemd

# Query timer status
systemd_timer_last_trigger_seconds{name="device-uptime-monitor.timer"}
```

## Development

### Adding New Features

1. **Role Discovery**: Modify `SchedulerFactory.discover_schedulable_playbooks()`
2. **Service Generation**: Update templates in `templates/`
3. **CLI Commands**: Add new subcommands in `scheduler.py`
4. **Validation**: Enhance `validate_role()` method

### Testing

```bash
# Test role discovery
python3 -m pytest tests/test_role_discovery.py

# Test service generation
python3 -m pytest tests/test_service_generation.py

# Integration tests
python3 -m pytest tests/test_integration.py
```

## Security Considerations

### Service Isolation

Generated systemd services include security hardening:

```ini
[Service]
# Prevent privilege escalation
NoNewPrivileges=true

# Isolate temporary files
PrivateTmp=true

# Protect system directories
ProtectSystem=strict
ProtectHome=true

# Minimal filesystem access
ReadWritePaths=/path/to/project /var/log/ansible-monitoring
```

### Credential Security

- **Ansible Vault**: Passwords encrypted in playbooks
- **File Permissions**: Restricted access to service files
- **Environment Isolation**: No sensitive data in environment variables
- **Log Security**: Logs don't contain credentials

## Performance Considerations

### Scheduling Optimization

- **Randomization**: Timer randomization prevents system load spikes
- **Resource Limits**: Configure CPU/memory limits per service
- **Parallel Execution**: Multiple roles can run simultaneously
- **Load Balancing**: Distribute execution across time slots

### System Resources

Monitor system impact:

```bash
# Check service resource usage
systemd-cgtop

# Monitor specific service
systemctl status device-uptime-monitor.service
```

## FAQ

### Q: Can I run multiple instances of the same role?

A: Yes, create different inventory groups and configure separate schedules for each group.

### Q: How do I change the execution schedule?

A: Modify the `schedule` in the role's `default_schedule_config` in `defaults/main.yml` and re-run `create-timers`.

### Q: What happens if a service execution takes longer than the schedule interval?

A: Systemd prevents overlapping executions. The next execution waits until the current one completes.

### Q: Can I disable a monitoring role temporarily?

A: Yes, stop the timer with `systemctl stop <service>.timer`.

### Q: How do I add custom environment variables?

A: Modify the systemd service template or use the `playbook_args` to pass environment variables.

## Changelog

### Version 1.0.0
- Initial release with role discovery
- Systemd service generation
- CLI interface for management
- Security hardening
- Centralized logging

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Update documentation
5. Submit a pull request

## License

Same as parent project - MIT License.