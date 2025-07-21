#!/usr/bin/env python3
"""
Purpose: Ansible ServiceNow Scheduler Factory
Design Pattern: Factory Pattern with Playbook Discovery and Scheduling
Complexity: O(n) for playbook discovery, O(1) for service generation per playbook
"""

import os
import yaml
import json
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass
from pathlib import Path

@dataclass
class ScheduledPlaybook:
    """
    Data class representing a discovered schedulable playbook
    Contains playbook metadata and scheduling configuration
    """
    name: str
    path: str
    schedule_config: Dict
    description: str
    schedule: str
    inventory_groups: List[str]
    systemd_service_name: str
    timeout: int
    enabled: bool
    
    @property
    def is_enabled(self) -> bool:
        return self.enabled and self.schedule_config.get('enabled', False)

class SchedulerFactory:
    """
    Factory class for discovering and managing schedulable Ansible playbooks
    Supports inheritance from role defaults for scheduling configuration
    """
    
    def __init__(self, playbooks_path: str = "/home/gmorris/ansible-servicenow/playbooks",
                 roles_path: str = "/home/gmorris/ansible-servicenow/roles"):
        """
        Initialize the factory with playbooks and roles directory paths
        
        Args:
            playbooks_path: Path to Ansible playbooks directory
            roles_path: Path to Ansible roles directory (for inheritance)
        """
        self.playbooks_path = Path(playbooks_path)
        self.roles_path = Path(roles_path)
        self.logger = self._setup_logging()
        self.role_defaults_cache = {}
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration for the factory"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
    
    def _derive_systemd_name(self, playbook_name: str) -> str:
        """
        Derive a consistent systemd service name from playbook name
        
        Args:
            playbook_name: Original playbook filename (without .yml)
            
        Returns:
            Systemd-compatible service name
        """
        # Convert to systemd-friendly format
        systemd_name = playbook_name.replace('_', '-').lower()
        
        # Add consistent suffix if not present
        if not systemd_name.endswith('-monitor'):
            systemd_name += '-monitor'
            
        # Ensure name doesn't start with number or special char
        if systemd_name[0].isdigit() or not systemd_name[0].isalpha():
            systemd_name = f"ansible-{systemd_name}"
            
        return systemd_name
    
    def _get_role_defaults(self, role_name: str) -> Dict:
        """
        Get role defaults for inheritance, with caching
        
        Args:
            role_name: Name of the role to get defaults for
            
        Returns:
            Dictionary of role defaults, empty if not found
        """
        if role_name in self.role_defaults_cache:
            return self.role_defaults_cache[role_name]
            
        defaults_file = self.roles_path / role_name / "defaults" / "main.yml"
        defaults = {}
        
        if defaults_file.exists():
            try:
                with open(defaults_file, 'r') as f:
                    defaults = yaml.safe_load(f) or {}
                    self.logger.debug(f"Loaded defaults for role {role_name}")
            except Exception as e:
                self.logger.warning(f"Failed to load defaults for role {role_name}: {e}")
        else:
            self.logger.debug(f"No defaults file found for role {role_name}")
            
        self.role_defaults_cache[role_name] = defaults
        return defaults
    
    def discover_schedulable_playbooks(self) -> List[ScheduledPlaybook]:
        """
        Discover all playbooks with scheduling configuration
        
        Returns:
            List of ScheduledPlaybook objects found
        """
        discovered_playbooks = []
        
        if not self.playbooks_path.exists():
            self.logger.error(f"Playbooks path does not exist: {self.playbooks_path}")
            return discovered_playbooks
            
        self.logger.info(f"Scanning playbooks directory: {self.playbooks_path}")
        
        for playbook_file in self.playbooks_path.glob("*.yml"):
            playbook_name = playbook_file.stem
            
            scheduled_playbook = self._parse_playbook_config(playbook_name, str(playbook_file))
            if scheduled_playbook:
                discovered_playbooks.append(scheduled_playbook)
                self.logger.info(f"✅ Discovered schedulable playbook: {playbook_name}")
            else:
                self.logger.debug(f"Playbook {playbook_name} not configured for scheduling")
                
        self.logger.info(f"Discovery complete. Found {len(discovered_playbooks)} schedulable playbooks")
        return discovered_playbooks
    
    def _parse_playbook_config(self, playbook_name: str, playbook_path: str) -> Optional[ScheduledPlaybook]:
        """
        Parse playbook to extract scheduling configuration with role inheritance
        
        Args:
            playbook_name: Name of the playbook (without .yml)
            playbook_path: Full path to playbook file
            
        Returns:
            ScheduledPlaybook object if valid scheduling config found, None otherwise
        """
        try:
            with open(playbook_path, 'r') as f:
                playbook_content = yaml.safe_load(f)
                
            if not playbook_content or not isinstance(playbook_content, list):
                return None
                
            # Get the first play (assuming single-play playbooks)
            first_play = playbook_content[0]
            playbook_schedule = first_play.get('vars', {}).get('playbook_schedule', {})
            
            # If no playbook-level scheduling, check for role inheritance
            if not playbook_schedule:
                playbook_schedule = self._inherit_from_roles(first_play)
                
            # Skip if no scheduling configuration found
            if not playbook_schedule or not playbook_schedule.get('enabled', False):
                return None
                
            # Extract configuration with defaults
            return ScheduledPlaybook(
                name=playbook_name,
                path=playbook_path,
                schedule_config=playbook_schedule,
                description=playbook_schedule.get('description', f'{playbook_name} execution'),
                schedule=playbook_schedule.get('schedule', '*/10 * * * *'),
                inventory_groups=playbook_schedule.get('inventory_groups', [first_play.get('hosts', 'all')]),
                systemd_service_name=self._derive_systemd_name(playbook_name),
                timeout=playbook_schedule.get('timeout', 300),
                enabled=playbook_schedule.get('enabled', False)
            )
            
        except yaml.YAMLError as e:
            self.logger.error(f"Failed to parse YAML in {playbook_path}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error parsing playbook config for {playbook_name}: {e}")
            return None
    
    def _inherit_from_roles(self, play: Dict) -> Dict:
        """
        Inherit scheduling configuration from roles used in the play
        
        Args:
            play: Ansible play dictionary
            
        Returns:
            Inherited scheduling configuration, empty if none found
        """
        tasks = play.get('tasks', [])
        
        for task in tasks:
            # Check for include_role tasks
            include_role = task.get('include_role', {})
            if isinstance(include_role, dict):
                role_name = include_role.get('name')
            elif isinstance(include_role, str):
                role_name = include_role
            else:
                continue
                
            if role_name:
                role_defaults = self._get_role_defaults(role_name)
                schedule_config = role_defaults.get('default_schedule_config', {})
                
                if schedule_config:
                    self.logger.info(f"Inheriting schedule from role {role_name}")
                    return {
                        'enabled': True,
                        'schedule': schedule_config.get('schedule', '*/10 * * * *'),
                        'description': f"Inherited from {role_name}: {schedule_config.get('description', 'monitoring')}",
                        'inventory_groups': schedule_config.get('inventory_groups', ['all']),
                        'timeout': schedule_config.get('timeout', 300),
                        'inherited_from_role': role_name
                    }
        
        return {}
    
    def get_playbook_summary(self, playbooks: List[ScheduledPlaybook]) -> Dict:
        """
        Generate summary information about discovered playbooks
        
        Args:
            playbooks: List of ScheduledPlaybook objects
            
        Returns:
            Dictionary containing playbook summary statistics
        """
        summary = {
            'total_playbooks': len(playbooks),
            'enabled_playbooks': len([p for p in playbooks if p.is_enabled]),
            'inventory_groups': set(),
            'schedules': {},
            'inherited_configs': 0
        }
        
        for playbook in playbooks:
            # Collect all inventory groups
            summary['inventory_groups'].update(playbook.inventory_groups)
            
            # Count schedule patterns
            schedule = playbook.schedule
            summary['schedules'][schedule] = summary['schedules'].get(schedule, 0) + 1
            
            # Count inherited configurations
            if 'inherited_from_role' in playbook.schedule_config:
                summary['inherited_configs'] += 1
            
        # Convert set to list for JSON serialization
        summary['inventory_groups'] = list(summary['inventory_groups'])
        
        return summary

if __name__ == "__main__":
    # Example usage for testing
    factory = SchedulerFactory()
    playbooks = factory.discover_schedulable_playbooks()
    
    print(f"Discovered {len(playbooks)} schedulable playbooks:")
    for playbook in playbooks:
        print(f"  - {playbook.name}: {playbook.description}")
        print(f"    Schedule: {playbook.schedule}")
        print(f"    Groups: {', '.join(playbook.inventory_groups)}")
        print(f"    Enabled: {playbook.is_enabled}")
        
        if 'inherited_from_role' in playbook.schedule_config:
            print(f"    📋 Inherited from role: {playbook.schedule_config['inherited_from_role']}")
        else:
            print(f"    📅 Playbook-defined schedule")
        print()
    
    # Print summary
    summary = factory.get_playbook_summary(playbooks)
    print("Summary:")
    print(json.dumps(summary, indent=2))