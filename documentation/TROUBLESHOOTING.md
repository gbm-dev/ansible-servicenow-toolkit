# Troubleshooting Guide

Comprehensive troubleshooting guide for the Ansible ServiceNow monitoring system.

## Common Issues

### Role Discovery Issues

#### Role Not Discovered by Scheduler

**Symptoms:**
- Role doesn't appear in `python3 scheduler.py discover`
- No systemd services created for your role

**Causes and Solutions:**

1. **Missing monitoring_config**
   ```yaml
   # Add to roles/your_role/defaults/main.yml
   monitoring_config:
     enabled: true
     role_type: your_monitoring_type
     default_schedule: "*/5 * * * *"
     description: "Your role description"
     inventory_groups: [network_devices]
   ```

2. **Role in excluded list**
   ```python
   # Check if your role name is in EXCLUDED_ROLES
   # scheduler/monitoring_role_factory.py
   EXCLUDED_ROLES = {
       'servicenow_itsm',      # ServiceNow API wrapper
       'common',               # Common utilities  
       'base',                 # Base configurations
   }
   ```

3. **Invalid YAML syntax**
   ```bash
   # Validate YAML syntax
   python3 -c "import yaml; yaml.safe_load(open('roles/your_role/defaults/main.yml'))"
   ```

4. **File permissions**
   ```bash
   # Check file permissions
   ls -la roles/your_role/defaults/main.yml
   # Should be readable by your user
   ```

#### Role Discovery Debug

```bash
# Enable debug logging
cd scheduler/
python3 -c "
import logging
logging.basicConfig(level=logging.DEBUG)
from monitoring_role_factory import MonitoringRoleFactory
factory = MonitoringRoleFactory()
roles = factory.discover_monitoring_roles()
"
```

### ServiceNow Integration Issues

#### Authentication Failures

**Symptoms:**
- "Invalid user credentials" error
- "Access denied" messages
- HTTP 401/403 responses

**Solutions:**

1. **Verify credentials in vault**
   ```bash
   # Decrypt and check vault file
   ansible-vault view group_vars/all/vault.yml
   ```

2. **Test ServiceNow API access**
   ```bash
   # Test with curl
   curl -u "username:password" \
        "https://your-instance.service-now.com/api/now/table/incident?sysparm_limit=1"
   ```

3. **Check ServiceNow user permissions**
   - User needs `itil` role for incidents
   - User needs `change_manager` role for changes
   - User needs `problem_manager` role for problems

#### Field Validation Errors

**Symptoms:**
- "Required ServiceNow incident fields missing" error
- "Invalid choice" errors for dropdown fields

**Solutions:**

1. **Check required fields**
   ```yaml
   # Always provide required fields
   vars:
     itsm_type: incident
     incident_caller: "admin"              # Required
     incident_short_description: "Issue"  # Required
   ```

2. **Validate field values**
   ```bash
   # Check valid choices in ServiceNow
   # Go to System Definition > Choice Lists
   # Search for field name (e.g., "incident.urgency")
   ```

3. **Use correct field mapping**
   ```yaml
   # Check servicenow_itsm role defaults for field mappings
   cat roles/servicenow_itsm/defaults/main.yml
   ```

#### Duplicate Prevention Issues

**Symptoms:**
- Multiple incidents created for same issue
- "correlation_id not found" warnings

**Solutions:**

1. **Verify correlation_id consistency**
   ```yaml
   # Use consistent correlation_id patterns
   incident_correlation_id: "device_connectivity_{{ inventory_hostname }}"
   ```

2. **Check ServiceNow query**
   ```yaml
   # Debug duplicate check
   - name: Manual duplicate check
     servicenow.itsm.incident_info:
       instance: "{{ servicenow_instance }}"
       sysparm_query: "correlation_id=your_test_correlation_id^state!=6"
     register: existing_incidents
     
   - debug:
       var: existing_incidents
   ```

### Template Issues

#### Template Rendering Errors

**Symptoms:**
- "template not found" errors
- "undefined variable" errors in templates
- Malformed incident descriptions

**Solutions:**

1. **Check template path**
   ```bash
   # Verify template exists
   ls -la roles/your_role/templates/your_template.j2
   ```

2. **Validate template syntax**
   ```bash
   # Test template rendering
   ansible localhost -m template \
     -a "src=roles/device_uptime/templates/connectivity_failure_description.j2 dest=/tmp/test.txt" \
     -e "inventory_hostname=test-device"
   ```

3. **Debug undefined variables**
   ```yaml
   # Add debug task before template rendering
   - name: Debug available variables
     debug:
       var: vars
   ```

#### Template Variable Issues

**Symptoms:**
- Empty or "None" values in rendered content
- Missing device information

**Solutions:**

1. **Provide default values**
   ```jinja2
   - Device Type: {{ device_type | default('Unknown') }}
   - Location: {{ device_location | default('Not specified') }}
   ```

2. **Check variable availability**
   ```yaml
   - name: Check if variables are defined
     debug:
       msg: "Variable device_type is {{ 'defined' if device_type is defined else 'not defined' }}"
   ```

### Systemd Service Issues

#### Timer Creation Failures

**Symptoms:**
- "Permission denied" when creating systemd files
- Services not created in `/etc/systemd/system/`

**Solutions:**

1. **Run with sudo**
   ```bash
   # Systemd service creation requires root
   sudo python3 scheduler.py create-timers
   ```

2. **Check disk space**
   ```bash
   df -h /etc/systemd/system/
   ```

3. **Verify systemd is running**
   ```bash
   systemctl status systemd
   ```

#### Timer Not Executing

**Symptoms:**
- Timer shows as "active" but doesn't run
- No log entries for service execution

**Solutions:**

1. **Check timer status**
   ```bash
   systemctl status device-uptime-monitor.timer
   systemctl list-timers device-uptime-monitor.timer
   ```

2. **Verify schedule format**
   ```bash
   # Check systemd calendar format
   systemd-analyze calendar "*:0/5"  # Every 5 minutes
   ```

3. **Check service dependencies**
   ```bash
   systemctl status device-uptime-monitor.service
   journalctl -u device-uptime-monitor.service
   ```

#### Service Execution Failures

**Symptoms:**
- Service fails when timer triggers
- "ansible-playbook command not found" errors
- Permission denied errors

**Solutions:**

1. **Check service environment**
   ```bash
   # View service file
   cat /etc/systemd/system/device-uptime-monitor.service
   
   # Check PATH and environment
   sudo systemctl show device-uptime-monitor.service -p Environment
   ```

2. **Verify ansible installation**
   ```bash
   # Check ansible path for service user
   sudo -u ansible which ansible-playbook
   ```

3. **Fix file permissions**
   ```bash
   # Ensure project files are readable
   chmod -R 755 /home/gmorris/ansible-servicenow
   ```

### Inventory and Connectivity Issues

#### Device Unreachable

**Symptoms:**
- All devices showing as "down"
- SSH/connection timeouts
- "Host unreachable" errors

**Solutions:**

1. **Test basic connectivity**
   ```bash
   # Test ping
   ansible all -i inventory.yml -m ping
   
   # Test specific host
   ansible core-sw-01 -i inventory.yml -m ping
   ```

2. **Check inventory configuration**
   ```yaml
   # Verify inventory.yml format
   core-sw-01:
     ansible_host: 10.1.1.1
     ansible_connection: network_cli  # For network devices
     ansible_network_os: ios
   ```

3. **Verify credentials**
   ```bash
   # Test with explicit credentials
   ansible core-sw-01 -i inventory.yml -m ping -u username -k
   ```

#### Inventory Parsing Errors

**Symptoms:**
- "Unable to parse inventory" errors
- YAML syntax errors

**Solutions:**

1. **Validate inventory syntax**
   ```bash
   ansible-inventory -i inventory.yml --list
   ```

2. **Check YAML formatting**
   ```bash
   python3 -c "import yaml; yaml.safe_load(open('inventory.yml'))"
   ```

## Debugging Techniques

### Ansible Debug Mode

#### Verbose Output

```bash
# Increase verbosity level
ansible-playbook -vvv playbook.yml

# Different verbosity levels:
# -v    : Verbose mode
# -vv   : More verbose  
# -vvv  : Debug mode
# -vvvv : Connection debug
```

#### Debug Tasks

```yaml
# Add debug tasks to troubleshoot
- name: Debug inventory hostname
  debug:
    var: inventory_hostname

- name: Debug all host variables
  debug:
    var: hostvars[inventory_hostname]

- name: Debug ServiceNow instance config
  debug:
    var: servicenow_instance
```

#### Check Mode

```bash
# Run in check mode (dry run)
ansible-playbook --check playbook.yml

# Show differences
ansible-playbook --check --diff playbook.yml
```

### ServiceNow API Debugging

#### Direct API Testing

```bash
# Test incident creation directly
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -u "username:password" \
  -d '{
    "short_description": "Test incident",
    "description": "Test description"
  }' \
  "https://your-instance.service-now.com/api/now/table/incident"
```

#### Collection Debug Mode

```yaml
# Enable debug mode for ServiceNow collection
- name: Test ServiceNow with debug
  servicenow.itsm.incident:
    instance: "{{ servicenow_instance }}"
    short_description: "Debug test"
    description: "Test incident"
  environment:
    ANSIBLE_DEBUG: "1"
  register: debug_result

- name: Show debug result
  debug:
    var: debug_result
```

### Log Analysis

#### Service Logs

```bash
# View service logs
journalctl -u device-uptime-monitor.service -f

# View timer logs  
journalctl -u device-uptime-monitor.timer -f

# View logs for specific time period
journalctl -u device-uptime-monitor.service --since "1 hour ago"
```

#### Application Logs

```bash
# View Ansible logs
tail -f /var/log/ansible-monitoring/device-uptime-monitor.log

# View error logs
tail -f /var/log/ansible-monitoring/device-uptime-monitor.error.log
```

#### System Logs

```bash
# View system messages
tail -f /var/log/messages

# View authentication logs
tail -f /var/log/auth.log
```

## Performance Issues

### Slow Execution

**Symptoms:**
- Playbooks taking longer than expected
- Timeouts during execution
- High system resource usage

**Solutions:**

1. **Optimize inventory**
   ```yaml
   # Use specific groups instead of 'all'
   ansible-playbook -i inventory.yml --limit network_devices playbook.yml
   ```

2. **Increase timeouts**
   ```yaml
   # In monitoring role defaults
   monitoring_config:
     timeout: 600  # Increase from default 300
   ```

3. **Parallel execution**
   ```yaml
   # Increase forks in ansible.cfg
   [defaults]
   forks = 10
   ```

### High Resource Usage

**Symptoms:**
- High CPU usage during monitoring
- Memory exhaustion
- Disk space issues

**Solutions:**

1. **Monitor system resources**
   ```bash
   # Check system load during execution
   top
   htop
   iotop
   ```

2. **Reduce monitoring frequency**
   ```yaml
   # In role defaults
   monitoring_config:
     default_schedule: "*/10 * * * *"  # Every 10 minutes instead of 5
   ```

3. **Implement log rotation**
   ```bash
   # Configure logrotate for monitoring logs
   sudo vim /etc/logrotate.d/ansible-monitoring
   ```

## Network Issues

### Firewall Problems

**Symptoms:**
- Connection timeouts
- "No route to host" errors
- ServiceNow API calls failing

**Solutions:**

1. **Check firewall rules**
   ```bash
   # Check local firewall
   sudo iptables -L
   sudo ufw status
   
   # Test specific ports
   telnet your-servicenow-instance.com 443
   ```

2. **Verify network connectivity**
   ```bash
   # Test DNS resolution
   nslookup your-instance.service-now.com
   
   # Test HTTPS connectivity
   curl -I https://your-instance.service-now.com
   ```

### DNS Issues

**Symptoms:**
- "Name or service not known" errors
- Intermittent connectivity

**Solutions:**

1. **Check DNS configuration**
   ```bash
   cat /etc/resolv.conf
   ```

2. **Test DNS resolution**
   ```bash
   dig your-instance.service-now.com
   ```

3. **Use IP addresses for testing**
   ```yaml
   # Temporarily use IP instead of hostname
   vault_servicenow_host: "https://1.2.3.4"
   ```

## Environment Issues

### Python Environment

**Symptoms:**
- "Module not found" errors
- Import errors for Ansible modules

**Solutions:**

1. **Check Python path**
   ```bash
   which python3
   python3 -c "import sys; print(sys.path)"
   ```

2. **Verify Ansible installation**
   ```bash
   ansible --version
   pip3 list | grep ansible
   ```

3. **Install missing collections**
   ```bash
   ansible-galaxy collection install servicenow.itsm
   ```

### File Permissions

**Symptoms:**
- "Permission denied" errors
- Unable to read/write files

**Solutions:**

1. **Check file ownership**
   ```bash
   ls -la group_vars/all/vault.yml
   ls -la roles/
   ```

2. **Fix permissions**
   ```bash
   # Make files readable
   chmod 644 group_vars/all/vault.yml
   chmod -R 755 roles/
   ```

## Data Issues

### Configuration Item (CI) Problems

**Symptoms:**
- "CI not found" warnings
- Incidents not associated with CIs

**Solutions:**

1. **Verify CI exists in ServiceNow**
   ```bash
   # Search for CI by asset tag
   curl -u "username:password" \
     "https://instance.service-now.com/api/now/table/cmdb_ci?sysparm_query=asset_tag=P1000002"
   ```

2. **Check asset tag format**
   ```yaml
   # Ensure consistent asset tag format
   device_asset_tag: "P1000002"  # Exact match with ServiceNow
   ```

3. **Debug CI lookup**
   ```yaml
   - name: Test CI lookup
     servicenow.itsm.configuration_item_info:
       instance: "{{ servicenow_instance }}"
       query:
         - asset_tag: "= {{ device_asset_tag }}"
     register: ci_debug
     
   - debug:
       var: ci_debug
   ```

## Recovery Procedures

### Service Recovery

If monitoring services are stuck or failing:

```bash
# Stop all monitoring timers
sudo systemctl stop device-uptime-monitor.timer

# Restart systemd daemon
sudo systemctl daemon-reload

# Clear failed services
sudo systemctl reset-failed

# Restart timer
sudo systemctl start device-uptime-monitor.timer

# Check status
systemctl status device-uptime-monitor.timer
```

### Data Recovery

If ServiceNow data is corrupted:

1. **Backup current state**
   ```bash
   # Export current incidents
   curl -u "username:password" \
     "https://instance.service-now.com/api/now/table/incident?sysparm_query=correlation_idSTARTSWITHdevice_" \
     > incident_backup.json
   ```

2. **Clean up duplicates**
   ```bash
   # Find duplicate incidents
   # Use ServiceNow UI or API to identify and merge/close duplicates
   ```

### Configuration Rollback

If configuration changes break the system:

```bash
# Revert to previous commit
git log --oneline -10
git checkout <previous-commit-hash>

# Or reset specific files
git checkout HEAD~1 -- roles/servicenow_itsm/defaults/main.yml
```

## Escalation Procedures

### Level 1: Basic Troubleshooting
- Check logs and status
- Verify basic connectivity
- Review recent changes

### Level 2: Advanced Debugging
- Enable debug mode
- Analyze API calls
- Check system resources

### Level 3: Expert Support
- Contact ServiceNow support for API issues
- Review Ansible collection issues on GitHub
- Consult system administrators for infrastructure issues

## Common Error Messages

### "Required ServiceNow incident fields missing"
**Cause**: Missing required fields (caller, short_description)
**Solution**: Add all required fields to role variables

### "Invalid choice for field 'urgency'"
**Cause**: Using invalid urgency value
**Solution**: Use valid values: low, medium, high

### "User authentication failed"
**Cause**: Incorrect ServiceNow credentials
**Solution**: Verify credentials in vault file

### "Template not found"  
**Cause**: Template file doesn't exist or wrong path
**Solution**: Check template location and filename

### "Connection timeout"
**Cause**: Network connectivity issues
**Solution**: Check firewall, DNS, and network connectivity

### "Permission denied /etc/systemd/system"
**Cause**: Insufficient privileges for systemd files
**Solution**: Run scheduler with sudo

## Prevention Strategies

### Monitoring Health Checks

```yaml
# Add health check for monitoring system itself
- name: Check monitoring service health
  systemd:
    name: device-uptime-monitor.timer
    state: started
  register: timer_status
  
- name: Alert if monitoring is down
  fail:
    msg: "Monitoring timer is not active!"
  when: timer_status.status.ActiveState != "active"
```

### Regular Maintenance

1. **Log rotation**: Configure automatic log cleanup
2. **Credential rotation**: Regularly update ServiceNow passwords
3. **System updates**: Keep Ansible and Python updated
4. **Backup**: Regular backup of configuration and templates

### Testing Strategy

1. **Development environment**: Test changes before production
2. **Staged rollouts**: Deploy changes incrementally
3. **Rollback plans**: Always have rollback procedures ready
4. **Documentation**: Keep troubleshooting docs updated

## Getting Help

### Information to Collect

When seeking support, gather:

- Ansible version: `ansible --version`
- Python version: `python3 --version`  
- OS version: `cat /etc/os-release`
- Error messages: Full error text
- Log files: Recent log entries
- Configuration: Relevant config files (sanitize passwords)

### Resources

- **Ansible Documentation**: https://docs.ansible.com/
- **ServiceNow ITSM Collection**: https://galaxy.ansible.com/servicenow/itsm
- **Project Issues**: Create GitHub issue with details
- **ServiceNow Community**: https://community.servicenow.com/