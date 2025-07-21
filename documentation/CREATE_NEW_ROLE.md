# Creating New Monitoring Roles

This guide explains how to create new monitoring roles that integrate with the ServiceNow ITSM system and are automatically discovered by the scheduling factory.

## Overview

Monitoring roles in this project follow a standardized pattern:

1. **Health Check Logic**: Perform monitoring activities (ping, SNMP, API calls, etc.)
2. **Template Rendering**: Generate incident content using Jinja2 templates
3. **ServiceNow Integration**: Create/update/close ServiceNow ITSM objects
4. **Automatic Discovery**: Configuration allows scheduler factory to discover and schedule the role

## Role Structure

### Directory Layout

```
roles/your_monitoring_role/
├── defaults/
│   └── main.yml              # Role configuration and monitoring_config
├── tasks/
│   └── main.yml              # Main monitoring logic
├── templates/
│   ├── failure_description.j2      # Incident description template
│   ├── failure_work_notes.j2       # Incident work notes template
│   ├── resolved_close_notes.j2     # Incident closure notes template
│   └── resolved_work_notes.j2      # Incident closure work notes template
├── meta/
│   └── main.yml              # Role metadata and dependencies
└── README.md                 # Role-specific documentation
```

## Step-by-Step Guide

### Step 1: Create Role Structure

```bash
# Create the role directory structure
mkdir -p roles/your_monitoring_role/{defaults,tasks,templates,meta}
```

### Step 2: Configure Role Defaults

Create `roles/your_monitoring_role/defaults/main.yml`:

```yaml
---
# Role-specific configuration
your_role_timeout: 30
your_role_retries: 3
your_role_port: 443

# ServiceNow incident parameters
your_role_incident_urgency: medium
your_role_incident_impact: medium
your_role_assignment_group: "IT Operations"

# Monitoring scheduler configuration (REQUIRED for auto-discovery)
monitoring_config:
  enabled: true
  role_type: your_monitoring_type           # e.g., security_monitoring, performance_monitoring
  default_schedule: "*/10 * * * *"          # Cron format - every 10 minutes
  description: "Your monitoring role description"
  inventory_groups:                         # Target inventory groups
    - network_devices
    - your_device_group
  timeout: 600                              # Execution timeout in seconds
  retry_count: 3                           # Retry attempts on failure
  playbook_args: "--limit={{inventory_group}} -e your_role_timeout={{timeout}}"
```

### Step 3: Implement Monitoring Logic

Create `roles/your_monitoring_role/tasks/main.yml`:

```yaml
---
# Purpose: [Describe your monitoring purpose]
# Design Pattern: [Describe your monitoring pattern, e.g., Health check with state management]

- name: Your monitoring check with incident lifecycle
  block:
    # SUCCESS PATH - Device/Service is healthy
    - name: Perform your health check
      # Your monitoring logic here
      # Examples:
      # - ansible.builtin.uri: (for HTTP/API checks)
      # - ansible.builtin.ping: (for connectivity)  
      # - community.general.snmp_facts: (for SNMP)
      # - custom module or script
      register: health_check_result
      timeout: "{{ your_role_timeout | default(30) }}"

    - name: Log successful check
      ansible.builtin.debug:
        msg: "{{ inventory_hostname }} health check PASSED"
      when: health_check_result is succeeded

    - name: Generate incident closure content from templates
      set_fact:
        rendered_close_notes: "{{ lookup('template', 'resolved_close_notes.j2') }}"
        rendered_close_work_notes: "{{ lookup('template', 'resolved_work_notes.j2') }}"
      when: health_check_result is succeeded

    - name: Close any open incidents for this device
      include_role:
        name: servicenow_itsm
        tasks_from: close_incident
      vars:
        incident_correlation_id: "your_role_{{ inventory_hostname }}"
        incident_close_code: "Resolved by caller"
        incident_close_notes: "{{ rendered_close_notes }}"
        incident_close_work_notes: "{{ rendered_close_work_notes }}"
      when: health_check_result is succeeded

  rescue:
    # FAILURE PATH - Device/Service has issues
    - name: Generate incident content from templates
      set_fact:
        rendered_description: "{{ lookup('template', 'failure_description.j2') }}"
        rendered_work_notes: "{{ lookup('template', 'failure_work_notes.j2') }}"

    - name: Create ServiceNow incident for monitoring failure
      include_role:
        name: servicenow_itsm
      vars:
        itsm_type: incident
        incident_caller: "{{ your_role_incident_caller | default(servicenow_default_caller) }}"
        incident_short_description: "[YOUR_TYPE] {{ inventory_hostname }} monitoring failure"
        incident_description: "{{ rendered_description }}"
        incident_work_notes: "{{ rendered_work_notes }}"
        incident_correlation_id: "your_role_{{ inventory_hostname }}"
        incident_urgency: "{{ your_role_incident_urgency | default('medium') }}"
        incident_impact: "{{ your_role_incident_impact | default('medium') }}"
        incident_assignment_group: "{{ your_role_assignment_group | default('IT Operations') }}"
        incident_category: your_category
        incident_subcategory: your_subcategory
        incident_asset_tag: "{{ device_asset_tag | default(omit) }}"
```

### Step 4: Create Jinja2 Templates

#### Failure Description Template

Create `roles/your_monitoring_role/templates/failure_description.j2`:

```jinja2
Your Monitoring Type Failure

Device/Service Details:
- Hostname: {{ inventory_hostname }}
- IP Address: {{ ansible_host }}
- Service Type: {{ your_service_type | default('Unknown') }}
- Location: {{ device_location | default('Unknown') }}
- Asset Tag: {{ device_asset_tag }}

Failure Information:
- Check Type: {{ check_type | default('Your Check Type') }}
- Timeout: {{ your_role_timeout | default(30) }}s
- Failed Task: {{ ansible_failed_task.name }}
- Error Message: {{ ansible_failed_result.msg | default('Check failed') }}
- Detection Time: {{ ansible_date_time.iso8601 }}

{% if additional_context is defined %}
Additional Context:
{{ additional_context }}
{% endif %}

Impact Assessment:
[Describe the impact of this failure type]

Recommended Actions:
1. [First troubleshooting step]
2. [Second troubleshooting step]
3. [Third troubleshooting step]
{% if your_service_type in ['critical', 'high_priority'] %}
4. [Additional steps for critical services]
5. [Escalation procedures if needed]
{% endif %}
```

#### Failure Work Notes Template

Create `roles/your_monitoring_role/templates/failure_work_notes.j2`:

```jinja2
Automated detection by Ansible {{ role_name | default('monitoring') }} check
Detection time: {{ ansible_date_time.iso8601 }}
Check timeout: {{ your_role_timeout | default(30) }}s
Previous status: {{ last_check_status | default('Unknown') }}
```

#### Resolution Templates

Create `roles/your_monitoring_role/templates/resolved_close_notes.j2`:

```jinja2
Your Monitoring Type Resolved

Resolution Details:
- Device/Service: {{ inventory_hostname }} ({{ ansible_host }})
- Resolved Time: {{ ansible_date_time.iso8601 }}
- Resolution: Service is now responding to health checks
- Check Type: {{ check_type | default('Your Check Type') }}

{% if resolution_details is defined %}
Resolution Context:
{{ resolution_details }}
{% endif %}

Automated closure by Ansible {{ role_name | default('monitoring') }} check
```

Create `roles/your_monitoring_role/templates/resolved_work_notes.j2`:

```jinja2
Service back online - automatically closing incident
Last successful check: {{ ansible_date_time.iso8601 }}
Health check status: PASS
```

### Step 5: Configure Role Dependencies

Create `roles/your_monitoring_role/meta/main.yml`:

```yaml
---
galaxy_info:
  author: your_name
  description: Your monitoring role description
  company: your_company
  license: MIT
  min_ansible_version: 2.9
  
  platforms:
    - name: EL
      versions:
        - 7
        - 8
    - name: Ubuntu
      versions:
        - 18.04
        - 20.04

  galaxy_tags:
    - monitoring
    - servicenow
    - automation

dependencies:
  - role: servicenow_itsm
    when: monitoring_config.enabled | default(false)
```

### Step 6: Create Role Documentation

Create `roles/your_monitoring_role/README.md`:

```markdown
# Your Monitoring Role

[Role description]

## Requirements

- [List requirements]
- ServiceNow ITSM Collection
- Network access to monitored services

## Role Variables

### Monitoring Configuration
- `your_role_timeout`: Check timeout in seconds (default: 30)
- `your_role_retries`: Retry attempts (default: 3)
- `your_role_incident_urgency`: ServiceNow incident urgency (default: medium)

### ServiceNow Configuration  
- `your_role_incident_caller`: ServiceNow caller ID
- `your_role_assignment_group`: ServiceNow assignment group

## Dependencies

- servicenow_itsm

## Example Playbook

\`\`\`yaml
---
- hosts: your_devices
  roles:
    - your_monitoring_role
\`\`\`

## Automatic Scheduling

This role is automatically discovered by the monitoring scheduler.
Configure scheduling in `defaults/main.yml` under `monitoring_config`.

## License

MIT
```

### Step 7: Test Your Role

Create a test playbook `test_your_role.yml`:

```yaml
---
- name: Test Your Monitoring Role
  hosts: localhost
  gather_facts: yes
  
  vars:
    # ServiceNow connection
    servicenow_host: "{{ vault_servicenow_host }}"
    servicenow_username: "{{ vault_servicenow_username }}"
    servicenow_password: "{{ vault_servicenow_password }}"
    servicenow_default_caller: "{{ vault_servicenow_default_caller }}"
    
    # Test device simulation
    inventory_hostname: "test-device-01"
    ansible_host: "192.168.1.100"
    device_asset_tag: "P1000099"
    
  tasks:
    - name: Test your monitoring role
      include_role:
        name: your_monitoring_role
```

### Step 8: Verify Auto-Discovery

Test that your role is discovered by the scheduler:

```bash
# Discover your new role
cd scheduler/
python3 scheduler.py discover

# Should show your role in the output
# Example output:
# Discovered 2 monitoring roles:
#   - device_uptime: device-uptime-monitor
#   - your_monitoring_role: your-monitoring-role-monitor
```

## Advanced Patterns

### Multiple Check Types

For roles that perform multiple types of checks:

```yaml
- name: Multi-check monitoring
  block:
    - name: HTTP API Check
      ansible.builtin.uri:
        url: "https://{{ ansible_host }}/api/health"
      register: api_check
      
    - name: Service Port Check
      ansible.builtin.wait_for:
        host: "{{ ansible_host }}"
        port: 443
        timeout: 10
      register: port_check
      
    - name: All checks passed
      ansible.builtin.debug:
        msg: "All health checks passed"
      when: api_check is succeeded and port_check is succeeded
      
  rescue:
    - name: Determine failure type
      set_fact:
        failure_type: "{{ 'api' if api_check is failed else 'connectivity' if port_check is failed else 'unknown' }}"
        
    - name: Render failure-specific templates
      set_fact:
        rendered_description: "{{ lookup('template', failure_type + '_failure_description.j2') }}"
```

### Dynamic Scheduling

For roles that need different schedules based on device type:

```yaml
monitoring_config:
  enabled: true
  role_type: adaptive_monitoring
  default_schedule: "*/5 * * * *"  # Default for most devices
  description: "Adaptive monitoring with dynamic scheduling"
  inventory_groups:
    - network_devices
  timeout: 300
  # Override schedules per group in group_vars/
```

Then in `group_vars/critical_devices/main.yml`:

```yaml
monitoring_config:
  default_schedule: "*/1 * * * *"  # Every minute for critical devices
```

### Custom ITSM Object Types

For roles that create change requests or problem records:

```yaml
# In rescue block for change request
- name: Create ServiceNow change request
  include_role:
    name: servicenow_itsm
  vars:
    itsm_type: change
    change_type: emergency
    change_short_description: "Emergency change for {{ inventory_hostname }}"
    change_description: "{{ rendered_change_description }}"
    # ... other change fields
```

## Best Practices

### Naming Conventions

- **Role names**: Use descriptive, lowercase with underscores (e.g., `security_scan`, `disk_usage`)
- **Correlation IDs**: Use pattern `{role_type}_{hostname}` (e.g., `security_scan_core-sw-01`)
- **Template files**: Descriptive names ending in purpose (e.g., `ssl_certificate_failure_description.j2`)

### Error Handling

- Always use `block`/`rescue` pattern for health checks
- Include meaningful error messages in templates  
- Set appropriate timeouts for external calls
- Use `register` to capture results for template rendering

### Performance

- Use appropriate check intervals (don't over-monitor)
- Set reasonable timeouts
- Consider batching operations for multiple devices
- Use `when` conditions to skip unnecessary tasks

### Security

- Never log sensitive information
- Use ansible-vault for credentials
- Limit ServiceNow API user permissions
- Validate input parameters

### Testing

- Create test playbooks for each role
- Test both success and failure scenarios
- Verify template rendering with sample data
- Test ServiceNow integration with dev instance

## Common Patterns

### HTTP/API Monitoring

```yaml
- name: HTTP endpoint health check
  ansible.builtin.uri:
    url: "https://{{ ansible_host }}/health"
    method: GET
    timeout: "{{ api_timeout | default(30) }}"
    status_code: 200
  register: api_health_check
```

### SNMP Monitoring

```yaml
- name: SNMP system information check
  community.general.snmp_facts:
    host: "{{ ansible_host }}"
    version: v2c
    community: "{{ snmp_community | default('public') }}"
  register: snmp_facts
```

### Database Connectivity

```yaml
- name: Database connection check
  community.postgresql.postgresql_ping:
    login_host: "{{ ansible_host }}"
    login_user: "{{ db_user }}"
    login_password: "{{ db_password }}"
  register: db_ping
```

### File System Monitoring

```yaml
- name: Check disk usage
  ansible.builtin.setup:
    filter: ansible_mounts
  register: disk_facts

- name: Verify disk space
  ansible.builtin.fail:
    msg: "Disk usage critical on {{ item.mount }}"
  when: (item.size_available / item.size_total * 100) < 10
  loop: "{{ disk_facts.ansible_facts.ansible_mounts }}"
```

## Troubleshooting

### Role Not Discovered

1. Check `monitoring_config.enabled: true` in `defaults/main.yml`
2. Verify YAML syntax is valid
3. Ensure role name doesn't match excluded patterns
4. Run `python3 scheduler.py discover` with debug logging

### Template Errors

1. Check Jinja2 syntax in template files
2. Verify all variables are available in template context
3. Test template rendering with `ansible-playbook --check`
4. Use `ansible.builtin.debug` to inspect available variables

### ServiceNow Integration Issues

1. Verify required fields are provided (caller, short_description)
2. Check ServiceNow credentials and permissions
3. Test with `itsm_type: incident` first
4. Review ServiceNow collection documentation

### Scheduling Issues

1. Verify cron schedule format
2. Check systemd timer creation with `--dry-run`
3. Monitor systemd logs: `journalctl -u your-role-monitor.service`
4. Validate inventory groups exist

## Examples

See the existing `device_uptime` role for a complete working example of all these patterns.

Additional example roles can be found in the `examples/roles/` directory.

## Support

For questions about creating new monitoring roles:

1. Review existing role implementations
2. Check the troubleshooting guide
3. Test with simple examples first
4. Create an issue with specific questions