# Test Suite

This directory contains comprehensive tests for the Ansible ServiceNow monitoring system.

**Important**: All tests create ServiceNow tickets (incidents, changes, or problems) with `[TEST]` prefixes in their short descriptions to clearly identify them as test-generated tickets.

## Test Categories

### Role Testing
- `test_device_uptime_role.yml` - Tests device uptime monitoring role
- `test_config_backup_role.yml` - Tests configuration backup role functionality
- `test_config_backup_real_device.yml` - Tests config backup role with real device
- `test_interface_monitoring_role.yml` - Tests interface monitoring role

### ServiceNow ITSM Feature Testing
- `test_itsm_incidents.yml` - Tests incident creation and management
- `test_itsm_changes.yml` - Tests change request creation and management  
- `test_itsm_problems.yml` - Tests problem record creation and management
- `test_itsm_lifecycle.yml` - Tests complete incident lifecycle (create → close)
- `test_itsm_incident_closure.yml` - Tests incident closure with templates
- `test_itsm_attachments.yml` - Tests file attachment functionality
- `test_itsm_validation.yml` - Tests required field validation

### Integration & Feature Testing
- `test_basic_connectivity.yml` - Basic device connectivity and ticket creation
- `test_template_rendering.yml` - Tests Jinja2 template rendering for incidents
- `test_cmdb_integration.yml` - Tests Configuration Item (CI) association
- `test_basic_logs.yml` - Tests device log collection functionality
- `test_inventory.yml` - Tests inventory structure and variables

## Running Tests

### Quick Start

```bash
# Navigate to tests directory
cd tests/

# Run specific tests
ansible-playbook test_basic_connectivity.yml
ansible-playbook test_device_uptime_role.yml
ansible-playbook test_itsm_incidents.yml
```

### Manual Test Execution

You can also run tests manually with ansible-playbook:

```bash
# Basic connectivity test
ansible-playbook -i ../inventory/production.yml test_basic_connectivity.yml

# Template rendering test with vault
ansible-playbook -i ../inventory/production.yml --vault-password-file ../.vault_pass test_template_rendering.yml

# ITSM lifecycle test with verbose output
ansible-playbook -vvv -i ../inventory/production.yml test_itsm_lifecycle.yml
```

### Common Test Patterns

```bash
# Test a specific role
ansible-playbook test_device_uptime_role.yml
ansible-playbook test_config_backup_role.yml
ansible-playbook test_interface_monitoring_role.yml

# Test ITSM functionality  
ansible-playbook test_itsm_incidents.yml
ansible-playbook test_itsm_changes.yml
ansible-playbook test_itsm_problems.yml

# Test integration features
ansible-playbook test_basic_connectivity.yml
ansible-playbook test_cmdb_integration.yml
ansible-playbook test_template_rendering.yml
```

## Test Requirements

### Prerequisites
- Ansible 2.9+
- ServiceNow ITSM Collection (`servicenow.itsm`)
- Configured vault with ServiceNow credentials
- Valid inventory file with test devices

### ServiceNow Setup
Tests require a working ServiceNow instance with:
- Valid user credentials with ITSM permissions
- Configuration Items (CIs) for asset tag tests
- Proper API access and permissions

### Credentials
Configure ServiceNow credentials in `group_vars/all/vault.yml`:

```yaml
vault_servicenow_host: "https://your-instance.service-now.com"
vault_servicenow_username: "your-username"
vault_servicenow_password: "your-password"
vault_servicenow_default_caller: "admin"
vault_servicenow_default_assignment_group: "IT Operations"
```

## Test Descriptions

### Basic Tests

#### `test_basic_connectivity.yml`
- **Purpose**: Test basic connectivity and ServiceNow ticket creation/closure
- **ServiceNow**: Required
- **What it tests**: Ping, SSH connectivity, and incident lifecycle
- **Duration**: < 1 minute

#### `test_device_uptime_role.yml`  
- **Purpose**: Test device uptime monitoring role end-to-end
- **ServiceNow**: Required
- **What it tests**: Full device_uptime role execution with incident management
- **Duration**: 1-2 minutes

### Validation Tests

#### `test_itsm_validation.yml`
- **Purpose**: Verify required field validation works properly
- **ServiceNow**: Required  
- **What it tests**: Missing caller and short_description fields
- **Expected**: Should show validation errors, then succeed
- **Duration**: < 1 minute

### Incident Management Tests

#### `test_template_rendering.yml`
- **Purpose**: Test incident creation for device failures with templates
- **ServiceNow**: Required
- **What it tests**: Template rendering and incident creation
- **Creates**: New incident in ServiceNow
- **Duration**: 1-2 minutes

#### `test_itsm_incidents.yml`
- **Purpose**: Standalone incident creation test
- **ServiceNow**: Required
- **What it tests**: Direct incident creation via servicenow_itsm role
- **Creates**: New incident in ServiceNow
- **Duration**: 1 minute

#### `test_itsm_incident_closure.yml`
- **Purpose**: Test incident closure with templates
- **ServiceNow**: Required
- **What it tests**: Template rendering for closure, incident closure logic
- **Requires**: Existing incident with matching correlation_id
- **Duration**: 1 minute

#### `test_itsm_lifecycle.yml`
- **Purpose**: Complete incident workflow demonstration
- **ServiceNow**: Required
- **What it tests**: Create incident → wait → auto-close incident
- **Creates**: Incident (created and closed)
- **Duration**: 1-2 minutes

### ITSM Object Tests

#### `test_itsm_changes.yml`
- **Purpose**: Change request creation and field validation
- **ServiceNow**: Required
- **What it tests**: servicenow_itsm role with change request type
- **Creates**: New change request in ServiceNow
- **Duration**: 1-2 minutes

#### `test_itsm_problems.yml`
- **Purpose**: Problem record creation and management
- **ServiceNow**: Required
- **What it tests**: servicenow_itsm role with problem record type
- **Creates**: New problem record in ServiceNow
- **Duration**: 1-2 minutes

### Integration Tests

#### `test_cmdb_integration.yml`
- **Purpose**: Test Configuration Item (CI) association
- **ServiceNow**: Required (with CI data)
- **What it tests**: Asset tag lookup and CI association
- **Requires**: CI with asset tag "P1000002" in ServiceNow CMDB
- **Duration**: 1-2 minutes

## Test Data

### Test Devices
Tests use simulated device data:
- `core-sw-01` - Primary test device (IP: 10.1.1.1, Asset: P1000002)
- `test-sw-lifecycle` - Lifecycle test device
- `test-router-01` - Router test device
- `core-sw-03` - Asset tag test device

### Asset Tags
- `P1000002` - Must exist as CI in ServiceNow for asset tag tests

## Troubleshooting Tests

### Common Issues

1. **Vault Password Issues**
   ```bash
   ERROR! Attempting to decrypt but no vault secrets found
   ```
   **Solution**: Use `--vault-password-file` or decrypt vault manually

2. **ServiceNow Authentication**
   ```bash
   User authentication failed
   ```
   **Solution**: Check credentials in vault.yml

3. **Missing CI for Asset Tag Tests**
   ```bash
   CI not found for asset tag P1000002
   ```
   **Solution**: Create CI in ServiceNow CMDB or skip asset tag tests

4. **Network Connectivity**
   ```bash
   Connection timeout to ServiceNow instance
   ```
   **Solution**: Check firewall, DNS, ServiceNow instance availability

### Debug Mode

Run tests with maximum verbosity:
```bash
./run_tests.sh -v test_name
```

Or manually:
```bash
ansible-playbook -vvvv test_file.yml
```

### Test Logs

Tests run locally and show output in terminal. For ServiceNow-integrated tests, also check:
- ServiceNow incident/change/problem tables
- ServiceNow system logs for API calls
- Ansible facts and debug output

## Development

### Adding New Tests

1. Create test playbook in `tests/` directory
2. Follow naming convention: `test_[feature].yml`
3. Add test description to this README
4. Update `run_tests.sh` with new test option
5. Test manually before committing

### Test Structure

```yaml
---
# Test description comment

- name: Test Name
  hosts: localhost  # or appropriate target
  gather_facts: yes  # if needed
  
  vars:
    # ServiceNow connection from vault
    servicenow_host: "{{ vault_servicenow_host }}"
    servicenow_username: "{{ vault_servicenow_username }}"
    servicenow_password: "{{ vault_servicenow_password }}"
    
    # Test-specific variables
    test_device: "test-device-name"
    
  tasks:
    - name: Test task description
      include_role:
        name: role_name
      vars:
        # Role variables
```

### Best Practices

- Use descriptive task names
- Include test data cleanup when possible
- Test both success and failure scenarios
- Use consistent correlation_id patterns for test isolation
- Document expected ServiceNow objects created
- Keep tests idempotent where possible