#!/bin/bash

# Test runner script for Ansible ServiceNow monitoring system
# This script provides easy execution of various test scenarios

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
VAULT_PASSWORD_FILE=""
INVENTORY_FILE="../examples/inventory.yml"
VERBOSE=""
TEST_FILTER=""

# Usage function
usage() {
    echo "Usage: $0 [OPTIONS] [TEST_NAME]"
    echo ""
    echo "Options:"
    echo "  -v, --verbose           Run with verbose output (-vvv)"
    echo "  -i, --inventory FILE    Use specific inventory file (default: ../examples/inventory.yml)"
    echo "  --vault-password-file FILE  Vault password file"
    echo "  -h, --help              Show this help message"
    echo ""
    echo "Available Tests:"
    echo "  connectivity           Test basic device connectivity (no ServiceNow)"
    echo "  servicenow            Test ServiceNow connection and role execution"  
    echo "  failed-device         Test incident creation for failed device"
    echo "  incident-lifecycle    Test complete incident lifecycle (create + close)"
    echo "  incident-creation     Test standalone incident creation"
    echo "  incident-closure      Test incident closure with templates"
    echo "  change-request        Test change request creation"
    echo "  problem-record        Test problem record creation"
    echo "  asset-tag            Test incident with asset tag association"
    echo "  validation-error     Test required field validation errors"
    echo "  all                  Run all tests sequentially"
    echo ""
    echo "Examples:"
    echo "  $0 connectivity                           # Test basic connectivity"
    echo "  $0 -v incident-lifecycle                  # Test incident lifecycle with verbose output"
    echo "  $0 --vault-password-file .vault_pass all # Run all tests with vault password file"
}

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Run a single test
run_test() {
    local test_name="$1"
    local test_file="$2"
    local description="$3"
    
    log_info "Running test: $test_name"
    log_info "Description: $description"
    
    if [[ ! -f "$test_file" ]]; then
        log_error "Test file not found: $test_file"
        return 1
    fi
    
    # Build ansible-playbook command
    local cmd="ansible-playbook"
    
    if [[ -n "$INVENTORY_FILE" ]]; then
        cmd="$cmd -i $INVENTORY_FILE"
    fi
    
    if [[ -n "$VAULT_PASSWORD_FILE" ]]; then
        cmd="$cmd --vault-password-file $VAULT_PASSWORD_FILE"
    fi
    
    if [[ -n "$VERBOSE" ]]; then
        cmd="$cmd $VERBOSE"
    fi
    
    cmd="$cmd $test_file"
    
    log_info "Executing: $cmd"
    echo "----------------------------------------"
    
    if eval "$cmd"; then
        log_success "Test '$test_name' completed successfully"
    else
        log_error "Test '$test_name' failed"
        return 1
    fi
    
    echo "========================================"
    echo ""
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -v|--verbose)
            VERBOSE="-vvv"
            shift
            ;;
        -i|--inventory)
            INVENTORY_FILE="$2"
            shift 2
            ;;
        --vault-password-file)
            VAULT_PASSWORD_FILE="$2"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        -*)
            log_error "Unknown option $1"
            usage
            exit 1
            ;;
        *)
            TEST_FILTER="$1"
            shift
            ;;
    esac
done

# Check if we're in the tests directory
if [[ ! -d "$(pwd)" =~ tests$ ]]; then
    log_warning "Not in tests directory. Changing to tests directory..."
    cd "$(dirname "$0")"
fi

log_info "Ansible ServiceNow Test Runner"
log_info "=============================="

# Validate prerequisites
if ! command -v ansible-playbook &> /dev/null; then
    log_error "ansible-playbook could not be found. Please install Ansible."
    exit 1
fi

if [[ -n "$VAULT_PASSWORD_FILE" ]] && [[ ! -f "$VAULT_PASSWORD_FILE" ]]; then
    log_error "Vault password file not found: $VAULT_PASSWORD_FILE"
    exit 1
fi

if [[ -n "$INVENTORY_FILE" ]] && [[ ! -f "$INVENTORY_FILE" ]]; then
    log_error "Inventory file not found: $INVENTORY_FILE"
    exit 1
fi

log_info "Using inventory: $INVENTORY_FILE"
if [[ -n "$VAULT_PASSWORD_FILE" ]]; then
    log_info "Using vault password file: $VAULT_PASSWORD_FILE"
fi

# Test execution
case "$TEST_FILTER" in
    connectivity)
        run_test "connectivity" "test_connectivity.yml" "Basic device connectivity test (no ServiceNow)"
        ;;
    servicenow)
        run_test "servicenow" "test_servicenow.yml" "ServiceNow connection and device_uptime role test"
        ;;
    failed-device)
        run_test "failed-device" "test_failed_device.yml" "Incident creation for simulated device failure"
        ;;
    incident-lifecycle)
        run_test "incident-lifecycle" "test_incident_lifecycle.yml" "Complete incident lifecycle (create + auto-close)"
        ;;
    incident-creation)
        run_test "incident-creation" "test_incident_creation.yml" "Standalone incident creation test"
        ;;
    incident-closure)
        run_test "incident-closure" "test_incident_closure.yml" "Incident closure with templates"
        ;;
    change-request)
        run_test "change-request" "test_change_request.yml" "Change request creation test"
        ;;
    problem-record)
        run_test "problem-record" "test_problem_record.yml" "Problem record creation test"
        ;;
    asset-tag)
        run_test "asset-tag" "test_asset_tag.yml" "Incident with asset tag CI association"
        ;;
    validation-error)
        run_test "validation-error" "test_validation_error.yml" "Required field validation testing"
        ;;
    all)
        log_info "Running all tests sequentially..."
        
        # Basic tests first
        run_test "connectivity" "test_connectivity.yml" "Basic device connectivity test (no ServiceNow)" || exit 1
        
        # ServiceNow integration tests
        run_test "validation-error" "test_validation_error.yml" "Required field validation testing" || exit 1
        run_test "failed-device" "test_failed_device.yml" "Incident creation for simulated device failure" || exit 1
        run_test "incident-creation" "test_incident_creation.yml" "Standalone incident creation test" || exit 1
        run_test "incident-closure" "test_incident_closure.yml" "Incident closure with templates" || exit 1
        run_test "incident-lifecycle" "test_incident_lifecycle.yml" "Complete incident lifecycle (create + auto-close)" || exit 1
        run_test "asset-tag" "test_asset_tag.yml" "Incident with asset tag CI association" || exit 1
        
        # ITSM object tests
        run_test "change-request" "test_change_request.yml" "Change request creation test" || exit 1
        run_test "problem-record" "test_problem_record.yml" "Problem record creation test" || exit 1
        
        # Full integration test
        run_test "servicenow" "test_servicenow.yml" "ServiceNow connection and device_uptime role test" || exit 1
        
        log_success "All tests completed successfully!"
        ;;
    "")
        log_error "No test specified. Use --help for available options."
        usage
        exit 1
        ;;
    *)
        log_error "Unknown test: $TEST_FILTER"
        usage
        exit 1
        ;;
esac