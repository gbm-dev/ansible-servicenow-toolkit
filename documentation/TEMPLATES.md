# Template Development Guide

Guide for developing and customizing Jinja2 templates for ServiceNow incident content generation.

## Overview

The template system uses Jinja2 to generate dynamic content for ServiceNow ITSM objects. Templates are stored in individual monitoring roles and rendered before calling the ServiceNow ITSM wrapper.

## Template Architecture

### Design Pattern: Template Rendering in Health Check Roles

```
Health Check Role → Render Templates → ServiceNow ITSM Role → ServiceNow API
```

**Benefits:**
- **Separation of Concerns**: Content logic stays with monitoring logic
- **Flexibility**: Each role can have custom templates
- **Reusability**: ServiceNow role remains a pure API wrapper
- **Testability**: Templates can be tested independently

### Template Location

Templates are stored in the monitoring role's `templates/` directory:

```
roles/device_uptime/
├── templates/
│   ├── connectivity_failure_description.j2
│   ├── connectivity_failure_work_notes.j2
│   ├── connectivity_resolved_close_notes.j2
│   └── connectivity_resolved_work_notes.j2
```

## Template Types

### Incident Creation Templates

#### Description Template
**Purpose**: Detailed incident description with technical information
**Template**: `*_failure_description.j2`

```jinja2
Network Device Connectivity Failure

Device Details:
- Hostname: {{ inventory_hostname }}
- IP Address: {{ ansible_host }}
- Device Type: {{ device_type | default('network_device') }}
- Location: {{ device_location | default('Unknown') }}
- Asset Tag: {{ device_asset_tag }}

Failure Information:
- Check Type: ICMP Ping Test
- Timeout: {{ uptime_check_timeout | default(10) }}s
- Failed Task: {{ ansible_failed_task.name }}
- Error Message: {{ ansible_failed_result.msg | default('Connection timeout') }}

Impact:
This device is not responding to network connectivity tests and may be offline,
affecting network services and connected systems.

Recommended Actions:
1. Verify physical connectivity and power status
2. Check upstream network devices
3. Review recent configuration changes
4. Check device logs if accessible via console
```

#### Work Notes Template
**Purpose**: Brief technical notes for internal tracking
**Template**: `*_failure_work_notes.j2`

```jinja2
Automated detection by Ansible health check
Previous check status: {{ last_check_status | default('Unknown') }}
```

### Incident Closure Templates

#### Close Notes Template
**Purpose**: Resolution details for incident closure
**Template**: `*_resolved_close_notes.j2`

```jinja2
Device connectivity restored

Resolution Details:
- Device: {{ inventory_hostname }} ({{ ansible_host }})
- Resolved Time: {{ ansible_date_time.iso8601 }}
- Resolution: Device is now responding to health checks
- Check Type: {{ check_type | default('ICMP Ping Test') }}
- Success Timeout: {{ uptime_check_timeout | default(10) }}s

Automated closure by Ansible health check monitoring
```

#### Close Work Notes Template
**Purpose**: Brief closure notes for internal tracking
**Template**: `*_resolved_work_notes.j2`

```jinja2
Device back online - automatically closing incident
Last successful check: {{ ansible_date_time.iso8601 }}
Health check status: PASS
```

## Template Rendering

### Rendering in Monitoring Roles

Templates are rendered using the `lookup('template')` function:

```yaml
- name: Generate incident content from templates
  set_fact:
    rendered_description: "{{ lookup('template', 'connectivity_failure_description.j2') }}"
    rendered_work_notes: "{{ lookup('template', 'connectivity_failure_work_notes.j2') }}"

- name: Create ServiceNow incident
  include_role:
    name: servicenow_itsm
  vars:
    incident_description: "{{ rendered_description }}"
    incident_work_notes: "{{ rendered_work_notes }}"
```

### Available Variables

Templates have access to all Ansible variables:

#### Ansible Built-in Variables
- `inventory_hostname`: Target host name
- `ansible_host`: IP address of target
- `ansible_date_time`: Date/time information
- `ansible_failed_task`: Information about failed task
- `ansible_failed_result`: Error details from failed task

#### Role-Specific Variables
- Variables defined in role `defaults/main.yml`
- Variables passed to the role
- Facts gathered during execution

#### Host Variables
- Variables from inventory (host_vars, group_vars)
- Device-specific information (asset tags, locations, etc.)

## Template Best Practices

### Content Structure

1. **Clear Sections**: Use consistent section headers
2. **Technical Details**: Include relevant technical information
3. **Context**: Provide business impact context
4. **Actions**: List recommended troubleshooting steps

### Variable Handling

#### Safe Defaults
Always provide defaults for optional variables:

```jinja2
- Device Type: {{ device_type | default('network_device') }}
- Location: {{ device_location | default('Unknown') }}
- Timeout: {{ uptime_check_timeout | default(10) }}s
```

#### Conditional Content
Use conditionals for optional sections:

```jinja2
{% if device_criticality is defined %}
Device Criticality: {{ device_criticality | upper }}
{% endif %}

{% if upstream_devices is defined %}
- Upstream Dependencies: {{ upstream_devices | join(', ') }}
{% endif %}
```

#### Data Validation
Check if variables exist before using:

```jinja2
{% if last_successful_check is defined %}
- Last Successful Check: {{ last_successful_check }}
{% else %}
- Last Successful Check: Unknown
{% endif %}
```

### Formatting

#### Lists and Arrays
Handle arrays safely:

```jinja2
{% if error_list is defined and error_list | length > 0 %}
Errors Detected:
{% for error in error_list %}
- {{ error }}
{% endfor %}
{% endif %}
```

#### Date/Time Formatting
Use consistent time formats:

```jinja2
- Detection Time: {{ ansible_date_time.iso8601 }}
- Local Time: {{ ansible_date_time.date }} {{ ansible_date_time.time }}
```

### Content Guidelines

#### Professional Tone
- Use clear, professional language
- Avoid technical jargon when possible
- Provide context for business impact

#### Actionable Information
- Include specific troubleshooting steps
- Reference relevant documentation
- Provide escalation paths

#### Consistent Formatting
- Use bullet points for lists
- Keep line lengths reasonable
- Use consistent indentation

## Advanced Template Patterns

### Multi-Type Monitoring

For roles that perform multiple check types:

```jinja2
{% if check_type == 'connectivity' %}
Network Connectivity Failure

Device is not responding to ping tests.

Recommended Actions:
1. Check physical connectivity
2. Verify network configuration
{% elif check_type == 'performance' %}
Performance Degradation Detected

Device response times are above threshold.

Recommended Actions:
1. Check CPU and memory usage
2. Review traffic patterns
{% endif %}
```

### Dynamic Criticality

Adjust content based on device importance:

```jinja2
{% if device_type in ['core', 'critical'] %}
**CRITICAL INFRASTRUCTURE FAILURE**

This is a critical network device failure requiring immediate attention.
Service impact is likely affecting multiple downstream systems.

Escalation: Page on-call engineer immediately
{% else %}
Device connectivity failure detected. Standard troubleshooting procedures apply.
{% endif %}
```

### Error Classification

Categorize different types of errors:

```jinja2
{% if 'timeout' in ansible_failed_result.msg | lower %}
Error Classification: Timeout
Likely Cause: Network connectivity or device overload

{% elif 'refused' in ansible_failed_result.msg | lower %}
Error Classification: Connection Refused  
Likely Cause: Service not running or firewall blocking

{% else %}
Error Classification: Unknown
Error Details: {{ ansible_failed_result.msg }}
{% endif %}
```

### Rich Context Information

Include comprehensive context:

```jinja2
Environmental Context:
- Check Frequency: Every {{ monitoring_interval | default(5) }} minutes
- Last Success: {{ last_successful_check | default('Never') }}
- Failure Count: {{ consecutive_failures | default(1) }}

{% if related_incidents is defined and related_incidents | length > 0 %}
Related Incidents:
{% for incident in related_incidents %}
- {{ incident.number }}: {{ incident.short_description }}
{% endfor %}
{% endif %}

{% if maintenance_window is defined %}
Maintenance Window: {{ maintenance_window }}
{% endif %}
```

## Template Testing

### Local Testing

Test templates locally before deployment:

```bash
# Test template rendering
ansible localhost -m template -a "src=roles/device_uptime/templates/connectivity_failure_description.j2 dest=/tmp/test_template.txt" -e "inventory_hostname=test-device"

# Review output
cat /tmp/test_template.txt
```

### Playbook Testing

Create test playbooks for template validation:

```yaml
---
- name: Test Template Rendering
  hosts: localhost
  vars:
    inventory_hostname: "test-device-01"
    ansible_host: "192.168.1.100"
    device_type: "cisco_ios"
    device_location: "Test Lab"
    device_asset_tag: "P1000099"
    ansible_failed_task:
      name: "Test connectivity check"
    ansible_failed_result:
      msg: "Connection timeout after 10 seconds"
    
  tasks:
    - name: Render failure description template
      set_fact:
        test_description: "{{ lookup('template', 'roles/device_uptime/templates/connectivity_failure_description.j2') }}"
        
    - name: Display rendered template
      debug:
        var: test_description
```

### Validation Checklist

Before deploying templates:

- [ ] All variables have safe defaults
- [ ] Conditional content renders correctly
- [ ] No undefined variables in output
- [ ] Content is professionally formatted
- [ ] Technical details are accurate
- [ ] Recommended actions are relevant

## Custom Template Examples

### Security Monitoring Template

```jinja2
# roles/security_scan/templates/security_vulnerability_description.j2
Security Vulnerability Detected

Device Information:
- Hostname: {{ inventory_hostname }}
- IP Address: {{ ansible_host }}
- Scan Type: {{ scan_type | default('Port Scan') }}
- Asset Tag: {{ device_asset_tag }}

Vulnerability Details:
- Severity: {{ vulnerability_severity | upper }}
- CVE ID: {{ cve_id | default('Pending Classification') }}
- Affected Service: {{ affected_service }}
- Port: {{ vulnerable_port | default('Multiple') }}

{% if vulnerability_description is defined %}
Description:
{{ vulnerability_description }}
{% endif %}

Risk Assessment:
{% if vulnerability_severity == 'critical' %}
CRITICAL: Immediate remediation required. This vulnerability poses significant security risk.
{% elif vulnerability_severity == 'high' %}
HIGH: Schedule remediation within 48 hours.
{% else %}
MEDIUM/LOW: Include in next maintenance window.
{% endif %}

Remediation Steps:
1. Isolate affected system if critical
2. Apply security patches: {{ patch_information | default('See security bulletin') }}
3. Verify remediation with follow-up scan
4. Update security documentation

Security Contact: {{ security_team_contact | default('security@company.com') }}
```

### Performance Monitoring Template

```jinja2
# roles/performance_check/templates/performance_degradation_description.j2
Performance Degradation Alert

System Information:
- Hostname: {{ inventory_hostname }}
- IP Address: {{ ansible_host }}
- Monitoring Type: {{ performance_check_type }}
- Asset Tag: {{ device_asset_tag }}

Performance Metrics:
- CPU Usage: {{ cpu_usage | default('Unknown') }}%
- Memory Usage: {{ memory_usage | default('Unknown') }}%
- Disk Usage: {{ disk_usage | default('Unknown') }}%
- Network Utilization: {{ network_utilization | default('Unknown') }}%

Threshold Violations:
{% for metric, value in threshold_violations.items() %}
- {{ metric }}: {{ value.current }} (threshold: {{ value.threshold }})
{% endfor %}

Performance Impact:
Response times have increased beyond acceptable thresholds, potentially affecting user experience and system reliability.

Investigation Steps:
1. Review system resource utilization
2. Check for recent configuration changes
3. Analyze traffic patterns and usage spikes
4. Review system logs for errors or warnings
5. Consider scaling resources if consistently high

{% if performance_history is defined %}
Historical Context:
- Average {{ performance_metric }}: {{ performance_history.average }}
- Peak {{ performance_metric }}: {{ performance_history.peak }}
- Trend: {{ performance_history.trend }}
{% endif %}
```

## Integration with Monitoring Roles

### Template Organization

Organize templates by monitoring role:

```
roles/
├── device_uptime/
│   └── templates/
│       ├── connectivity_failure_description.j2
│       └── connectivity_resolved_close_notes.j2
├── security_scan/  
│   └── templates/
│       ├── security_vulnerability_description.j2
│       └── security_resolved_close_notes.j2
└── performance_check/
    └── templates/
        ├── performance_degradation_description.j2
        └── performance_resolved_close_notes.j2
```

### Shared Templates

For common patterns, create shared templates:

```
roles/
├── common_templates/
│   └── templates/
│       ├── standard_device_info.j2
│       └── common_troubleshooting_steps.j2
```

Include shared templates:

```jinja2
{% include 'roles/common_templates/templates/standard_device_info.j2' %}

Specific Failure Information:
- Check Type: {{ check_type }}
- Error: {{ error_message }}

{% include 'roles/common_templates/templates/common_troubleshooting_steps.j2' %}
```

## Troubleshooting Templates

### Common Issues

1. **Undefined Variable Errors**:
   ```
   'dict object' has no attribute 'xyz'
   ```
   **Solution**: Add default filters: `{{ var | default('fallback') }}`

2. **Template Not Found**:
   ```
   template not found: template_name.j2
   ```
   **Solution**: Verify template path and filename

3. **Rendering Errors**:
   ```
   Error in template evaluation
   ```
   **Solution**: Check Jinja2 syntax and variable references

### Debug Techniques

1. **Variable Inspection**:
   ```yaml
   - name: Debug available variables
     debug:
       var: hostvars[inventory_hostname]
   ```

2. **Template Testing**:
   ```yaml
   - name: Test template with debug
     debug:
       msg: "{{ lookup('template', 'your_template.j2') }}"
   ```

3. **Incremental Development**:
   Start with simple templates and add complexity gradually

## Performance Considerations

### Template Efficiency

- **Minimize Loops**: Avoid complex loops in templates
- **Cache Results**: Store rendered templates in facts when reusing
- **Simple Logic**: Keep conditional logic simple

### Variable Scope

- **Pass Required Variables**: Only pass necessary variables to templates  
- **Use Local Variables**: Set intermediate values in tasks, not templates
- **Avoid Heavy Computations**: Perform complex calculations in tasks

## Maintenance

### Template Versioning

Consider versioning templates for major changes:

```
templates/
├── connectivity_failure_description_v1.j2
├── connectivity_failure_description_v2.j2  # Current
└── connectivity_failure_description.j2     # Symlink to current
```

### Documentation

Document template variables and usage:

```jinja2
{# 
Template: connectivity_failure_description.j2
Purpose: Generate incident description for network connectivity failures
Required Variables:
  - inventory_hostname: Target device hostname
  - ansible_host: Target device IP address
Optional Variables:
  - device_type: Device type classification
  - device_location: Physical location
  - uptime_check_timeout: Check timeout value
#}
```

### Testing Strategy

1. **Unit Tests**: Test individual templates with known variables
2. **Integration Tests**: Test template rendering in full playbook runs
3. **Regression Tests**: Verify existing functionality after changes
4. **Content Review**: Regularly review generated content quality