# Inventory Configuration

This directory contains example inventory files that you should copy and customize for your environment.

## Setup Instructions

1. **Copy example files:**
   ```bash
   # Main inventory
   cp production.yml.example production.yml
   cp staging.yml.example staging.yml
   
   # Group variables
   cp group_vars/all.yml.example group_vars/all.yml
   cp group_vars/network_devices.yml.example group_vars/network_devices.yml
   
   # Host variables (copy and rename for each device)
   cp host_vars/core-sw-01.yml.example host_vars/your-device.yml
   ```

2. **Customize for your environment:**
   - Update device hostnames and IP addresses
   - Configure device credentials (or use vault)
   - Set ServiceNow asset tags for CI linking
   - Adjust monitoring intervals per device criticality
   - Configure device-specific settings

3. **Security:**
   - Store sensitive data in vault files
   - Use host_vars/ for device-specific credentials
   - Never commit real credentials to version control

## File Structure

- `production.yml.example` - Production inventory with network device groups
- `staging.yml.example` - Staging/lab inventory for testing
- `group_vars/all.yml.example` - Global variables for all hosts
- `group_vars/network_devices.yml.example` - Network device specific settings
- `host_vars/*.yml.example` - Individual device configurations

## Device Groups

- **critical_devices** - High priority monitoring (every 2-5 minutes)
- **standard_devices** - Normal priority monitoring (every 5-10 minutes)
- **core_switches** - Core network infrastructure
- **access_switches** - Access layer devices
- **routers** - Routing equipment

Customize these groups based on your network topology and monitoring requirements.