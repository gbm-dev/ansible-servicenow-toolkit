#!/usr/bin/env python3
"""
Purpose: Ansible ServiceNow Monitoring Role Factory
Design Pattern: Factory Pattern with Role Discovery and Dynamic Service Generation
Complexity: O(n) for role discovery, O(1) for service generation per role
"""

import os
import yaml
import json
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass
from pathlib import Path

@dataclass
class MonitoringRole:
    """
    Data class representing a discovered monitoring role
    Contains role metadata and configuration for systemd service generation
    """
    name: str
    path: str
    config: Dict
    description: str
    schedule: str
    inventory_groups: List[str]
    systemd_service_name: str
    timeout: int
    retry_count: int
    playbook_args: str
    
    @property
    def is_enabled(self) -> bool:
        return self.config.get('enabled', False)
    
    @property
    def role_type(self) -> str:
        return self.config.get('role_type', 'unknown')

class MonitoringRoleFactory:
    """
    Factory class for discovering and managing Ansible monitoring roles
    Implements automatic role discovery with systemd service generation
    """
    
    # Roles to exclude from monitoring (wrapper/utility roles)
    EXCLUDED_ROLES = {
        'servicenow_itsm',      # ServiceNow API wrapper
        'common',               # Common utilities
        'base',                 # Base configurations
    }
    
    def __init__(self, roles_path: str = "/home/gmorris/ansible-servicenow/roles"):
        """
        Initialize the factory with roles directory path
        
        Args:
            roles_path: Path to Ansible roles directory
        """
        self.roles_path = Path(roles_path)
        self.logger = self._setup_logging()
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration for the factory"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
    
    def _derive_systemd_name(self, role_name: str) -> str:
        """
        Derive a consistent systemd service name from role name
        Follows systemd naming conventions and ensures uniqueness
        
        Args:
            role_name: Original Ansible role name
            
        Returns:
            Systemd-compatible service name
        """
        # Convert to systemd-friendly format
        # Replace underscores with hyphens, add monitoring suffix
        systemd_name = role_name.replace('_', '-').lower()
        
        # Add consistent suffix for monitoring services
        if not systemd_name.endswith('-monitor'):
            systemd_name += '-monitor'
            
        # Ensure name doesn't start with number or special char
        if systemd_name[0].isdigit() or not systemd_name[0].isalpha():
            systemd_name = f"ansible-{systemd_name}"
            
        return systemd_name
    
    def discover_monitoring_roles(self) -> List[MonitoringRole]:
        """
        Discover all monitoring-capable roles in the roles directory
        
        Returns:
            List of MonitoringRole objects found
        """
        discovered_roles = []
        
        if not self.roles_path.exists():
            self.logger.error(f"Roles path does not exist: {self.roles_path}")
            return discovered_roles
            
        self.logger.info(f"Scanning roles directory: {self.roles_path}")
        
        for role_dir in self.roles_path.iterdir():
            if not role_dir.is_dir():
                continue
                
            role_name = role_dir.name
            
            # Skip excluded roles
            if role_name in self.EXCLUDED_ROLES:
                self.logger.debug(f"Skipping excluded role: {role_name}")
                continue
                
            # Check if role has monitoring configuration
            defaults_file = role_dir / "defaults" / "main.yml"
            if not defaults_file.exists():
                self.logger.debug(f"No defaults/main.yml found for role: {role_name}")
                continue
                
            monitoring_role = self._parse_role_config(role_name, str(role_dir), defaults_file)
            if monitoring_role:
                discovered_roles.append(monitoring_role)
                self.logger.info(f"✅ Discovered monitoring role: {role_name}")
            else:
                self.logger.debug(f"Role {role_name} not configured for monitoring")
                
        self.logger.info(f"Discovery complete. Found {len(discovered_roles)} monitoring roles")
        return discovered_roles
    
    def _parse_role_config(self, role_name: str, role_path: str, defaults_file: Path) -> Optional[MonitoringRole]:
        """
        Parse role defaults file to extract monitoring configuration
        
        Args:
            role_name: Name of the role
            role_path: Full path to role directory  
            defaults_file: Path to defaults/main.yml file
            
        Returns:
            MonitoringRole object if valid monitoring config found, None otherwise
        """
        try:
            with open(defaults_file, 'r') as f:
                defaults = yaml.safe_load(f) or {}
                
            monitoring_config = defaults.get('monitoring_config', {})
            
            # Check if role has monitoring configuration and is enabled
            if not monitoring_config or not monitoring_config.get('enabled', False):
                return None
                
            # Extract configuration with defaults
            return MonitoringRole(
                name=role_name,
                path=role_path,
                config=monitoring_config,
                description=monitoring_config.get('description', f'{role_name} monitoring'),
                schedule=monitoring_config.get('default_schedule', '*/10 * * * *'),
                inventory_groups=monitoring_config.get('inventory_groups', ['all']),
                systemd_service_name=self._derive_systemd_name(role_name),
                timeout=monitoring_config.get('timeout', 300),
                retry_count=monitoring_config.get('retry_count', 3),
                playbook_args=monitoring_config.get('playbook_args', '--limit={{inventory_group}}')
            )
            
        except yaml.YAMLError as e:
            self.logger.error(f"Failed to parse YAML in {defaults_file}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error parsing role config for {role_name}: {e}")
            return None
    
    def get_role_summary(self, roles: List[MonitoringRole]) -> Dict:
        """
        Generate summary information about discovered roles
        
        Args:
            roles: List of MonitoringRole objects
            
        Returns:
            Dictionary containing role summary statistics
        """
        summary = {
            'total_roles': len(roles),
            'enabled_roles': len([r for r in roles if r.is_enabled]),
            'role_types': {},
            'inventory_groups': set(),
            'schedules': {}
        }
        
        for role in roles:
            # Count role types
            role_type = role.role_type
            summary['role_types'][role_type] = summary['role_types'].get(role_type, 0) + 1
            
            # Collect all inventory groups
            summary['inventory_groups'].update(role.inventory_groups)
            
            # Count schedule patterns
            schedule = role.schedule
            summary['schedules'][schedule] = summary['schedules'].get(schedule, 0) + 1
            
        # Convert set to list for JSON serialization
        summary['inventory_groups'] = list(summary['inventory_groups'])
        
        return summary
    
    def validate_role(self, role: MonitoringRole) -> List[str]:
        """
        Validate a monitoring role configuration
        
        Args:
            role: MonitoringRole to validate
            
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        # Check required fields
        if not role.name:
            errors.append("Role name is required")
            
        if not role.schedule:
            errors.append("Schedule is required")
            
        if not role.inventory_groups:
            errors.append("At least one inventory group is required")
            
        # Validate cron schedule format (basic check)
        if role.schedule:
            parts = role.schedule.split()
            if len(parts) != 5:
                errors.append(f"Invalid cron schedule format: {role.schedule}")
                
        # Check systemd service name format
        if role.systemd_service_name:
            if not role.systemd_service_name.replace('-', '').replace('_', '').isalnum():
                errors.append(f"Invalid systemd service name: {role.systemd_service_name}")
                
        # Validate timeout
        if role.timeout <= 0:
            errors.append("Timeout must be greater than 0")
            
        return errors

if __name__ == "__main__":
    # Example usage for testing
    factory = MonitoringRoleFactory()
    roles = factory.discover_monitoring_roles()
    
    print(f"Discovered {len(roles)} monitoring roles:")
    for role in roles:
        print(f"  - {role.name}: {role.description}")
        print(f"    Schedule: {role.schedule}")
        print(f"    Groups: {', '.join(role.inventory_groups)}")
        
        # Validate role
        errors = factory.validate_role(role)
        if errors:
            print(f"    ⚠️  Validation errors: {', '.join(errors)}")
        else:
            print(f"    ✅ Valid configuration")
        print()
    
    # Print summary
    summary = factory.get_role_summary(roles)
    print("Summary:")
    print(json.dumps(summary, indent=2))