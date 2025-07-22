# Test Suite

This directory contains comprehensive tests for the Ansible ServiceNow monitoring system.

## Test Categories

### Basic Connectivity Tests
- `test_connectivity.yml` - Basic device connectivity without ServiceNow integration
- `test_servicenow.yml` - ServiceNow connection and device_uptime role execution

### Incident Management Tests
- `test_failed_device.yml` - Simulates device failure and creates incidents using templates
- `test_incident_creation.yml` - Standalone incident creation test
- `test_incident_closure.yml` - Tests incident closure with templates
- `test_incident_lifecycle.yml` - Complete incident lifecycle (create → close)

### ITSM Object Tests
- `test_change_request.yml` - Change request creation and management
- `test_problem_record.yml` - Problem record creation and management

### Integration Tests  
- `test_asset_tag.yml` - Incident creation with Configuration Item association
- `test_validation_error.yml` - Required field validation testing

## Running Tests

### Quick Start

```bash
# Navigate to tests directory
cd tests/

# Run a specific test
./run_tests.sh connectivity

# Run with verbose output
./run_tests.sh -v incident-lifecycle

# Run all tests
./run_tests.sh all
```

### Manual Test Execution

You can also run tests manually with ansible-playbook:

```bash
# Basic test
ansible-playbook -i ../inventory/production.yml test_connectivity.yml

# With vault password file
ansible-playbook -i ../inventory/production.yml --vault-password-file ../.vault_pass test_failed_device.yml

# With verbose output
ansible-playbook -vvv -i ../inventory/production.yml test_incident_lifecycle.yml
```

### Test Runner Options

```bash
./run_tests.sh [OPTIONS] [TEST_NAME]

Options:
  -v, --verbose                    Run with verbose output (-vvv)
  -i, --inventory FILE            Use specific inventory file
  --vault-password-file FILE      Vault password file
  -h, --help                      Show help message

Available Tests:
  connectivity                    Basic device connectivity (no ServiceNow)
  servicenow                      ServiceNow connection and role execution  
  failed-device                   Incident creation for failed device
  incident-lifecycle              Complete incident lifecycle (create + close)
  incident-creation               Standalone incident creation
  incident-closure                Incident closure with templates
  change-request                  Change request creation
  problem-record                  Problem record creation
  asset-tag                      Incident with asset tag association
  validation-error               Required field validation errors
  all                            Run all tests sequentially
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

#### `test_connectivity.yml`
- **Purpose**: Validate basic Ansible connectivity to target devices
- **ServiceNow**: Not required
- **What it tests**: Ping and SSH connectivity
- **Duration**: < 1 minute

#### `test_servicenow.yml`  
- **Purpose**: Test ServiceNow integration with device monitoring
- **ServiceNow**: Required
- **What it tests**: Full device_uptime role execution
- **Duration**: 1-2 minutes

### Validation Tests

#### `test_validation_error.yml`
- **Purpose**: Verify required field validation works properly
- **ServiceNow**: Required  
- **What it tests**: Missing caller and short_description fields
- **Expected**: Should show validation errors, then succeed
- **Duration**: < 1 minute

### Incident Management Tests

#### `test_failed_device.yml`
- **Purpose**: Test incident creation for device failures with templates
- **ServiceNow**: Required
- **What it tests**: Template rendering and incident creation
- **Creates**: New incident in ServiceNow
- **Duration**: 1-2 minutes

#### `test_incident_creation.yml`
- **Purpose**: Standalone incident creation test
- **ServiceNow**: Required
- **What it tests**: Direct incident creation via servicenow_itsm role
- **Creates**: New incident in ServiceNow
- **Duration**: 1 minute

#### `test_incident_closure.yml`
- **Purpose**: Test incident closure with templates
- **ServiceNow**: Required
- **What it tests**: Template rendering for closure, incident closure logic
- **Requires**: Existing incident with matching correlation_id
- **Duration**: 1 minute

#### `test_incident_lifecycle.yml`
- **Purpose**: Complete incident workflow demonstration
- **ServiceNow**: Required
- **What it tests**: Create incident → wait → auto-close incident
- **Creates**: Incident (created and closed)
- **Duration**: 1-2 minutes

### ITSM Object Tests

#### `test_change_request.yml`
- **Purpose**: Change request creation and field validation
- **ServiceNow**: Required
- **What it tests**: servicenow_itsm role with change request type
- **Creates**: New change request in ServiceNow
- **Duration**: 1-2 minutes

#### `test_problem_record.yml`
- **Purpose**: Problem record creation and management
- **ServiceNow**: Required
- **What it tests**: servicenow_itsm role with problem record type
- **Creates**: New problem record in ServiceNow
- **Duration**: 1-2 minutes

### Integration Tests

#### `test_asset_tag.yml`
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