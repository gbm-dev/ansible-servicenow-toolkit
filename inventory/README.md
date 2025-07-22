# Inventory Configuration

This directory contains example inventory files that you should copy and customize for your environment.

## Setup Instructions

1. **Copy example files:**
   ```bash
   # Main inventory
   cp production.yml.example production.yml
   
   # Global variables
   cp group_vars/all.yml.example group_vars/all.yml
   
   # Host variables (optional, copy and rename for specific devices)
   cp host_vars/core-sw-01.yml.example host_vars/your-device.yml
   ```

2. **Customize for your environment:**
   - Update device hostnames and IP addresses  
   - Configure device credentials (use vault for passwords)
   - Set ServiceNow asset tags for CI linking
   - Add device-specific overrides in host_vars/ as needed

3. **Security:**
   - Store sensitive data in vault files
   - Use host_vars/ for device-specific credentials  
   - Never commit real credentials to version control

## File Structure

- `production.yml.example` - Production inventory with network device groups
- `group_vars/all.yml.example` - Essential global variables (ServiceNow config, connection settings)
- `host_vars/*.yml.example` - Device-specific overrides (optional)

## Device Groups

- **core_switches** - Core network infrastructure
- **access_switches** - Access layer devices  
- **routers** - Routing equipment
- **critical_devices** - High priority devices (optional grouping)
- **standard_devices** - Normal priority devices (optional grouping)

Note: Monitoring configuration is handled by role defaults, not inventory variables.