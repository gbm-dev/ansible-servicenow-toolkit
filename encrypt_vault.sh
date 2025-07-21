#!/bin/bash
# Script to encrypt ServiceNow credentials with ansible-vault

echo "This script will encrypt your ServiceNow credentials using ansible-vault"
echo "You will be prompted to create a vault password"
echo ""

# Encrypt the vault file
ansible-vault encrypt group_vars/all/vault.yml

echo ""
echo "Vault encrypted successfully!"
echo ""
echo "To run playbooks with the vault, use one of these methods:"
echo "1. ansible-playbook -i inventory.yml playbook.yml --ask-vault-pass"
echo "2. Create a vault password file and use: --vault-password-file vault_pass.txt"
echo ""
echo "To edit the vault file later:"
echo "ansible-vault edit group_vars/all/vault.yml"