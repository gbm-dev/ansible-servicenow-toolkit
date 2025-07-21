#!/bin/bash
# Test script for ServiceNow integration without vault encryption

echo "Running ServiceNow integration test..."
echo "This will test connectivity to device 5.78.128.250 and create an incident if it fails"
echo ""

# Run the test playbook without vault password (since vault is unencrypted for testing)
ansible-playbook -i examples/inventory.yml test_servicenow.yml -v

echo ""
echo "Test complete. Check your ServiceNow instance for any created incidents."
echo "URL: https://dev191473.service-now.com"