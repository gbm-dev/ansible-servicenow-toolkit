# ServiceNow ITSM Integration Guide

Complete guide for integrating with ServiceNow ITSM objects including incidents, change requests, and problem records.

## Overview

The `servicenow_itsm` role provides a unified wrapper for creating and managing ServiceNow ITSM objects. It supports three main object types with proper validation, duplicate prevention, and CI association.

## Supported ITSM Objects

### Incidents

Incidents represent service disruptions or issues that need resolution.

```yaml
- include_role:
    name: servicenow_itsm
  vars:
    itsm_type: incident
    incident_caller: "admin"                    # Required
    incident_short_description: "Device down"  # Required
    incident_description: "{{ custom_desc }}"  # Optional with default
    incident_correlation_id: "device_issue_{{ inventory_hostname }}"
    incident_urgency: high
    incident_impact: high
    incident_assignment_group: "Network Operations"
```

### Change Requests

Change requests manage planned changes to the infrastructure.

```yaml
- include_role:
    name: servicenow_itsm
  vars:
    itsm_type: change
    change_type: normal                         # standard|normal|emergency (Required)
    change_short_description: "Maintenance"    # Required
    change_description: "{{ custom_desc }}"    # Required
    change_correlation_id: "maintenance_{{ inventory_hostname }}"
    change_priority: moderate
    change_risk: low
    change_implementation_plan: "Detailed implementation steps"
    change_backout_plan: "Rollback procedures"
```

### Problem Records

Problem records identify root causes of recurring incidents.

```yaml
- include_role:
    name: servicenow_itsm
  vars:
    itsm_type: problem
    problem_short_description: "Recurring issue" # Required
    problem_description: "{{ custom_desc }}"     # Required
    problem_correlation_id: "recurring_{{ inventory_hostname }}"
    problem_impact: medium
    problem_urgency: medium
    problem_known_error: false
    problem_root_cause_known: false
```

## File Attachments

The ServiceNow role supports attaching files to incidents, problems, and change requests. This feature allows you to include diagnostic logs, configuration files, screenshots, or any other relevant documentation.

### Basic File Attachment

Attach a single file to an incident:

```yaml
- include_role:
    name: servicenow_itsm
  vars:
    itsm_type: incident
    incident_caller: "admin"
    incident_short_description: "Interface failure with logs"
    incident_description: "Network interface has failed, diagnostic logs attached"
    incident_correlation_id: "interface_failure_{{ inventory_hostname }}"
    incident_attachments:
      - path: "/tmp/interface_logs.txt"
        name: "interface_diagnostic.txt"
        content_type: "text/plain"
```

### Multiple File Attachments

Attach multiple files with different content types:

```yaml
- include_role:
    name: servicenow_itsm
  vars:
    itsm_type: incident
    incident_caller: "admin"
    incident_short_description: "System failure with diagnostics"
    incident_description: "Multiple diagnostic files attached for analysis"
    incident_correlation_id: "system_failure_{{ inventory_hostname }}"
    incident_attachments:
      - path: "/var/log/system.log"
        name: "system_log.txt"
        content_type: "text/plain"
      - path: "/tmp/diagnostic_report.json"
        name: "diagnostics.json"
        content_type: "application/json"
      - path: "/tmp/config_backup.conf"
        name: "device_config.conf"
        content_type: "text/plain"
```

### Problem Attachments

Attach files to problem records:

```yaml
- include_role:
    name: servicenow_itsm
  vars:
    itsm_type: problem
    problem_short_description: "Recurring network issues"
    problem_description: "Analysis data attached for root cause investigation"
    problem_correlation_id: "network_recurring_{{ inventory_hostname }}"
    problem_attachments:
      - path: "/tmp/network_analysis.csv"
        name: "network_trends.csv"
        content_type: "text/csv"
      - path: "/tmp/error_logs.txt"
        name: "error_analysis.txt"
        content_type: "text/plain"
```

### Change Request Attachments

Attach implementation and backout documentation:

```yaml
- include_role:
    name: servicenow_itsm
  vars:
    itsm_type: change
    change_type: normal
    change_short_description: "Network maintenance with documentation"
    change_description: "Scheduled maintenance with detailed procedures"
    change_correlation_id: "maintenance_{{ inventory_hostname }}"
    change_attachments:
      - path: "/tmp/implementation_plan.pdf"
        name: "implementation_procedure.pdf"
        content_type: "application/pdf"
      - path: "/tmp/rollback_steps.txt"
        name: "rollback_procedure.txt"
        content_type: "text/plain"
```

### Attachment Parameters

Each attachment supports the following parameters:

- **`path`** (Required): Local file system path to the file
- **`name`** (Optional): Name for the file in ServiceNow (defaults to basename of path)
- **`content_type`** (Optional): MIME type for the file (defaults to "text/plain")

### Supported Content Types

Common content types for attachments:

- **Text Files**: `text/plain`, `text/csv`, `text/html`
- **Logs**: `text/plain`, `application/octet-stream`
- **Configuration**: `text/plain`, `application/xml`
- **JSON Data**: `application/json`
- **Documents**: `application/pdf`, `application/msword`
- **Images**: `image/png`, `image/jpeg`, `image/gif`
- **Archives**: `application/zip`, `application/gzip`

### File Validation

The system automatically validates attachments:

1. **File Existence**: Verifies files exist before upload
2. **Access Permissions**: Checks read permissions on files
3. **Upload Status**: Reports success/failure for each file
4. **Error Handling**: Continues processing other attachments if one fails

### Example: Interface Monitoring with Logs

Real-world example from the interface monitoring role:

```yaml
# Collect diagnostic logs
- name: Get interface diagnostics
  cisco.ios.ios_command:
    commands:
      - "show interface {{ interface_name }}"
      - "show logging | grep {{ interface_name }}"
  register: interface_logs

# Save logs to file
- name: Save diagnostic data
  copy:
    content: |
      Interface Diagnostic Report
      Generated: {{ ansible_date_time.iso8601 }}
      
      === INTERFACE STATUS ===
      {{ interface_logs.stdout[0] }}
      
      === INTERFACE LOGS ===
      {{ interface_logs.stdout[1] }}
    dest: "/tmp/{{ interface_name }}_diagnostics.txt"

# Create incident with logs attached
- name: Create incident with diagnostic attachment
  include_role:
    name: servicenow_itsm
  vars:
    itsm_type: incident
    incident_caller: "network.automation"
    incident_short_description: "[INTERFACE DOWN] {{ interface_name }} on {{ inventory_hostname }}"
    incident_description: "Interface failure detected with diagnostic logs attached"
    incident_correlation_id: "interface_down_{{ inventory_hostname }}_{{ interface_name }}"
    incident_urgency: "high"
    incident_impact: "medium"
    incident_category: "network"
    incident_subcategory: "connectivity"
    incident_attachments:
      - path: "/tmp/{{ interface_name }}_diagnostics.txt"
        name: "{{ interface_name }}_diagnostic_logs.txt"
        content_type: "text/plain"
```

### Attachment Status and Debugging

The system provides detailed feedback on attachment processing:

```yaml
# After running servicenow_itsm role with attachments
- name: Check attachment results
  debug:
    msg: |
      Attachment Results:
      {% for result in servicenow_attachment_results %}
      - {{ result.attachment.name }}: {{ 'SUCCESS' if result.status == 201 else 'FAILED' }}
      {% endfor %}
```

### Best Practices for Attachments

1. **File Size**: Keep files under 100MB for optimal performance
2. **Meaningful Names**: Use descriptive filenames in ServiceNow
3. **Content Types**: Set appropriate MIME types for proper display
4. **Security**: Don't attach files containing sensitive credentials
5. **Cleanup**: Remove temporary files after successful upload
6. **Error Handling**: Check attachment results and handle failures

### Troubleshooting Attachments

Common attachment issues and solutions:

1. **File Not Found**: Verify file path and permissions
2. **Upload Failed**: Check ServiceNow API permissions and network connectivity
3. **Size Limit**: ServiceNow may reject large files
4. **Content Type**: Some file types may be restricted by ServiceNow policy
5. **Authentication**: Ensure ServiceNow user has attachment permissions

## Field Requirements

### Required Fields

The following fields are validated and must be provided:

#### Incidents
- `incident_caller`: ServiceNow user ID (e.g., 'admin', 'john.doe')
- `incident_short_description`: Brief summary of the incident

#### Change Requests  
- `change_type`: Type of change (`standard`, `normal`, `emergency`)
- `change_short_description`: Brief summary of the change
- `change_description`: Detailed change description

#### Problem Records
- `problem_short_description`: Brief summary of the problem
- `problem_description`: Detailed problem description

### Optional Fields with Defaults

These fields have sensible defaults but can be overridden:

#### Common Fields
- `urgency`: `low`, `medium`, `high` (default: `medium`)
- `impact`: `low`, `medium`, `high` (default: `medium`)
- `assignment_group`: ServiceNow group name (default: from vault/config)
- `category`: ServiceNow category (default: `network`)
- `subcategory`: ServiceNow subcategory (default: from config)
- `work_notes`: Additional notes (default: 'Created by Ansible automation')

#### Incident-Specific Fields
- `description`: Detailed description (default: 'Created by Ansible automation')
- `service`: ServiceNow service
- `service_offering`: ServiceNow service offering
- `channel`: How incident was reported
- `assigned_to`: Specific user assignment

#### Change-Specific Fields
- `priority`: Change priority (default: `moderate`)
- `risk`: Change risk level (default: `moderate`)
- `requested_by`: User requesting change
- `start_date`: Planned start date
- `end_date`: Planned end date
- `implementation_plan`: Implementation details
- `backout_plan`: Rollback procedures
- `test_plan`: Testing procedures

#### Problem-Specific Fields
- `assigned_to`: User assigned to problem (required for non-new states)
- `category`: Problem category (default: `software`)
- `subcategory`: Problem subcategory (default: `application`)
- `problem_type`: Type of problem (default: `defect`)
- `known_error`: Whether it's a known error (default: `false`)
- `root_cause_known`: Whether root cause is identified (default: `false`)

## Configuration Item (CI) Association

The system automatically associates ITSM objects with Configuration Items when possible:

### Asset Tag Association

If your inventory includes asset tags, the system looks up CIs by asset tag:

```yaml
# inventory.yml
core-sw-01:
  ansible_host: 10.1.1.1
  device_asset_tag: "P1000002"  # Links to ServiceNow CI
```

### Name-Based Association

If no asset tag is provided, the system attempts CI lookup by name:

```yaml
# Uses inventory_hostname for CI lookup
inventory_hostname: "core-sw-01"
```

### CI Configuration

CI association is controlled in the servicenow_itsm role defaults:

```yaml
# roles/servicenow_itsm/defaults/main.yml
servicenow_ci_lookup:
  enabled: true
  field: name  # Use CI name for lookup
```

## Duplicate Prevention

The system prevents duplicate ITSM objects using correlation IDs:

### Correlation ID Patterns

- **Incidents**: `device_connectivity_{{ inventory_hostname }}`
- **Changes**: `device_maintenance_{{ inventory_hostname }}`
- **Problems**: `device_recurring_{{ inventory_hostname }}`

### How It Works

1. **Query ServiceNow**: Check for existing objects with same correlation_id
2. **State Filtering**: Only consider non-closed objects
3. **Action Decision**:
   - **No existing**: Create new object
   - **Existing found**: Update existing object with new occurrence

### State Filtering

- **Incidents**: Excludes state 6 (Closed) and 7 (Resolved)
- **Changes**: Excludes state -4 (Closed Complete)
- **Problems**: Excludes state 7 (Closed)

## Authentication

### ServiceNow Instance Configuration

Configure your ServiceNow connection in `group_vars/all/vault.yml`:

```yaml
# ServiceNow Instance Credentials
vault_servicenow_host: "https://your-instance.service-now.com"
vault_servicenow_username: "your-username"
vault_servicenow_password: "your-password"

# ServiceNow default assignments
vault_servicenow_default_caller: "admin"
vault_servicenow_default_assignment_group: "IT Operations"
```

### Encrypt Credentials

Always encrypt sensitive data:

```bash
ansible-vault encrypt group_vars/all/vault.yml
```

### ServiceNow User Permissions

The ServiceNow user needs appropriate permissions:

#### Minimum Permissions
- **Incidents**: `itil` role or `incident_manager`
- **Changes**: `change_manager` role
- **Problems**: `problem_manager` role
- **Configuration Items**: `cmdb_read` for CI lookups

#### Recommended Setup
1. Create dedicated automation user in ServiceNow
2. Assign minimal required roles
3. Use strong password and regular rotation
4. Monitor API usage and access logs

## Error Handling

### Validation Errors

The system validates required fields before API calls:

```yaml
# This will fail with clear error message
- include_role:
    name: servicenow_itsm
  vars:
    itsm_type: incident
    # Missing required: incident_caller, incident_short_description
    incident_description: "This will fail validation"
```

### API Retry Logic

The system includes automatic retry for transient failures:

```yaml
# roles/servicenow_itsm/defaults/main.yml
servicenow_api_retry:
  retries: 3
  delay: 5  # seconds between retries
```

### Common Error Scenarios

1. **Invalid Credentials**: Check username/password in vault
2. **Missing Permissions**: Verify ServiceNow user roles
3. **Invalid Field Values**: Check ServiceNow documentation for valid options
4. **Network Issues**: Verify connectivity to ServiceNow instance
5. **Rate Limiting**: ServiceNow may throttle API calls

## Advanced Configuration

### Custom Field Mapping

You can extend field mapping by modifying the servicenow_itsm role:

```yaml
# Add custom fields in the 'other' section
other:
  custom_field: "{{ your_custom_value }}"
  u_department: "IT Operations"
  u_cost_center: "CC-12345"
```

### Multiple ServiceNow Instances

For multiple ServiceNow instances, override connection parameters:

```yaml
- include_role:
    name: servicenow_itsm
  vars:
    servicenow_instance:
      host: "https://dev-instance.service-now.com"
      username: "{{ dev_username }}"
      password: "{{ dev_password }}"
```

### Business Rules Integration

ServiceNow business rules may automatically populate fields:

- **Assignment**: Auto-assignment based on category
- **Priority Calculation**: Automatic priority from impact/urgency
- **Notifications**: Email notifications to assignment groups
- **SLA Application**: Automatic SLA assignment

Be aware that business rules may modify your ITSM objects after creation.

## Testing and Validation

### Unit Testing

Test individual ITSM object types:

```bash
# Test incident creation
ansible-playbook test_validation_error.yml

# Test change request workflow
ansible-playbook test_change_request.yml

# Test problem record management
ansible-playbook test_problem_record.yml
```

### Integration Testing

Test complete workflows:

```bash
# Test incident lifecycle (create → update → close)
ansible-playbook test_incident_lifecycle.yml

# Test duplicate prevention
ansible-playbook test_failed_device.yml  # Run twice to test updates
```

### Development Instance

Always test against a ServiceNow development instance first:

1. **Setup Dev Instance**: Use ServiceNow Developer Program
2. **Mirror Configuration**: Copy production CI data to dev
3. **Test Automation**: Run all test playbooks
4. **Validate Results**: Check ServiceNow records manually
5. **Deploy to Production**: Only after successful testing

## Best Practices

### Correlation IDs

- **Be Consistent**: Use predictable patterns for correlation IDs
- **Include Context**: Add device/service identifiers
- **Avoid Collisions**: Ensure uniqueness across different monitoring types

### Field Population

- **Required Fields**: Always provide required fields explicitly
- **Meaningful Descriptions**: Write clear, actionable descriptions
- **Consistent Categorization**: Use standardized categories/subcategories
- **Proper Assignment**: Route to appropriate teams

### Performance

- **Batch Operations**: Group related operations when possible
- **Rate Limiting**: Respect ServiceNow API limits
- **Error Handling**: Implement proper retry logic
- **Monitoring**: Track API usage and response times

### Security

- **Credential Management**: Use ansible-vault for all passwords
- **API User**: Dedicated user with minimal permissions
- **Network Security**: Use HTTPS and proper certificate validation
- **Audit Logging**: Enable ServiceNow API audit logging

## Troubleshooting

### Common Issues

1. **"Required fields missing"**: Check incident_caller and incident_short_description
2. **"CI not found"**: Verify asset_tag exists in ServiceNow CMDB
3. **"Duplicate correlation_id"**: Expected behavior - updates existing record
4. **"Invalid choice"**: Check valid values for category, urgency, impact, etc.

### Debug Mode

Enable debug logging for troubleshooting:

```yaml
# In your playbook
- name: Debug ServiceNow integration
  include_role:
    name: servicenow_itsm
  vars:
    itsm_type: incident
    # ... other vars
  register: snow_result
  
- name: Display result
  debug:
    var: snow_result
```

### ServiceNow Verification

Verify results in ServiceNow:

1. **Search by Number**: Use incident/change/problem number
2. **Search by Correlation ID**: Filter on correlation_id field
3. **Check Audit History**: Review who/when/what changed
4. **Verify CI Association**: Check related CIs tab

## Migration Guide

### From servicenow_incident_creator

If migrating from the old role:

1. **Update Role Name**:
   ```yaml
   # Old
   include_role: name: servicenow_incident_creator
   
   # New  
   include_role: name: servicenow_itsm
   ```

2. **Add ITSM Type**:
   ```yaml
   vars:
     itsm_type: incident  # Required
   ```

3. **Add Required Fields**:
   ```yaml
   vars:
     incident_caller: "{{ servicenow_default_caller }}"  # Now required
   ```

4. **Update Templates**: Move template rendering to calling roles

## API Reference

### ServiceNow REST API

The role uses the ServiceNow REST API through the Ansible ServiceNow collection:

- **Collection**: `servicenow.itsm`
- **Modules**: `incident`, `change_request`, `problem`
- **Documentation**: [ServiceNow ITSM Collection](https://galaxy.ansible.com/servicenow/itsm)

### Rate Limits

ServiceNow enforces API rate limits:

- **Default**: 100 requests per minute per user
- **Burst**: Short bursts may be allowed
- **429 Response**: Rate limit exceeded
- **Best Practice**: Implement backoff and retry

## Support

For ServiceNow integration issues:

1. **Check Documentation**: ServiceNow and Ansible collection docs
2. **Validate Credentials**: Test API access manually
3. **Review Logs**: Check Ansible and ServiceNow logs
4. **Test Incrementally**: Start with simple examples
5. **Contact Support**: ServiceNow support for API issues

## Examples

Complete working examples are available in:

- `test_failed_device.yml` - Incident lifecycle
- `test_change_request.yml` - Change management
- `test_problem_record.yml` - Problem management
- `test_validation_error.yml` - Error handling
- `test_attachment.yml` - File attachment functionality
- `test_interface_monitoring.yml` - Real-world interface monitoring with log attachments