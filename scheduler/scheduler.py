#!/usr/bin/env python3
"""
Purpose: Ansible ServiceNow Monitoring Scheduler Orchestrator
Design Pattern: Command Pattern with Factory and Template Engines
Complexity: O(n) for role processing, O(1) for service management operations
"""

import os
import sys
import argparse
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Optional
from jinja2 import Environment, FileSystemLoader
import logging

# Import our factory
from monitoring_role_factory import MonitoringRoleFactory, MonitoringRole

class SystemdServiceManager:
    """
    Manages systemd service and timer operations
    Handles service file generation, installation, and lifecycle management
    """
    
    def __init__(self, project_path: str, log_path: str = "/var/log/ansible-monitoring"):
        """
        Initialize systemd service manager
        
        Args:
            project_path: Path to Ansible project directory
            log_path: Path for service logs
        """
        self.project_path = Path(project_path)
        self.log_path = Path(log_path)
        self.systemd_path = Path("/etc/systemd/system")
        self.template_path = Path(__file__).parent / "templates"
        
        # Setup Jinja2 environment
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.template_path)),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        self.logger = logging.getLogger(__name__)
    
    def _cron_to_systemd_calendar(self, cron_schedule: str) -> str:
        """
        Convert cron schedule to systemd calendar format
        
        Args:
            cron_schedule: Cron format schedule (e.g., "*/5 * * * *")
            
        Returns:
            Systemd calendar format
        """
        # Basic conversion for common patterns
        # This is a simplified implementation - could be expanded
        if cron_schedule == "*/5 * * * *":
            return "*:0/5"  # Every 5 minutes
        elif cron_schedule == "*/10 * * * *":
            return "*:0/10"  # Every 10 minutes
        elif cron_schedule == "*/1 * * * *":
            return "*:*"  # Every minute
        elif cron_schedule == "0 * * * *":
            return "hourly"
        elif cron_schedule == "0 0 * * *":
            return "daily"
        else:
            # Default fallback - could be enhanced with more sophisticated parsing
            self.logger.warning(f"Unknown cron format: {cron_schedule}, using hourly")
            return "hourly"
    
    def generate_service_files(self, role: MonitoringRole, inventory_file: str) -> Dict[str, str]:
        """
        Generate systemd service and timer files for a monitoring role
        
        Args:
            role: MonitoringRole object
            inventory_file: Path to Ansible inventory file
            
        Returns:
            Dictionary with 'service' and 'timer' file contents
        """
        # Prepare template variables
        template_vars = {
            'role': role,
            'ansible_project_path': str(self.project_path),
            'inventory_file': inventory_file,
            'playbook_file': f"run_{role.name}.yml",  # Convention: run_<role_name>.yml
            'log_path': str(self.log_path),
            'systemd_calendar_format': self._cron_to_systemd_calendar(role.schedule),
            'randomized_delay': 30,  # Prevent thundering herd
            'accuracy_sec': 10
        }
        
        # Render service file
        service_template = self.jinja_env.get_template('systemd_service.j2')
        service_content = service_template.render(**template_vars)
        
        # Render timer file
        timer_template = self.jinja_env.get_template('systemd_timer.j2')
        timer_content = timer_template.render(**template_vars)
        
        return {
            'service': service_content,
            'timer': timer_content
        }
    
    def install_service(self, role: MonitoringRole, inventory_file: str, dry_run: bool = False) -> bool:
        """
        Install systemd service and timer files
        
        Args:
            role: MonitoringRole object
            inventory_file: Path to Ansible inventory file
            dry_run: If True, only show what would be done
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Generate service files
            files = self.generate_service_files(role, inventory_file)
            
            service_name = role.systemd_service_name
            service_file = self.systemd_path / f"{service_name}.service"
            timer_file = self.systemd_path / f"{service_name}.timer"
            
            if dry_run:
                self.logger.info(f"DRY RUN: Would create {service_file}")
                self.logger.info(f"DRY RUN: Would create {timer_file}")
                return True
            
            # Ensure log directory exists
            self.log_path.mkdir(parents=True, exist_ok=True)
            
            # Write service file
            with open(service_file, 'w') as f:
                f.write(files['service'])
            self.logger.info(f"Created service file: {service_file}")
            
            # Write timer file
            with open(timer_file, 'w') as f:
                f.write(files['timer'])
            self.logger.info(f"Created timer file: {timer_file}")
            
            # Reload systemd daemon
            subprocess.run(['systemctl', 'daemon-reload'], check=True)
            
            # Enable and start timer
            subprocess.run(['systemctl', 'enable', f"{service_name}.timer"], check=True)
            subprocess.run(['systemctl', 'start', f"{service_name}.timer"], check=True)
            
            self.logger.info(f"✅ Installed and started timer: {service_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to install service for {role.name}: {e}")
            return False
    
    def get_service_status(self, service_name: str) -> Dict:
        """
        Get status information for a systemd service
        
        Args:
            service_name: Name of the systemd service
            
        Returns:
            Dictionary containing status information
        """
        try:
            # Get service status
            result = subprocess.run(
                ['systemctl', 'status', f"{service_name}.service", '--no-pager'],
                capture_output=True,
                text=True
            )
            
            # Get timer status
            timer_result = subprocess.run(
                ['systemctl', 'status', f"{service_name}.timer", '--no-pager'],
                capture_output=True,
                text=True
            )
            
            return {
                'service_active': result.returncode == 0,
                'service_output': result.stdout,
                'timer_active': timer_result.returncode == 0,
                'timer_output': timer_result.stdout
            }
        except Exception as e:
            return {
                'error': str(e),
                'service_active': False,
                'timer_active': False
            }

class MonitoringScheduler:
    """
    Main orchestrator for Ansible ServiceNow monitoring scheduler
    Coordinates role discovery, service generation, and management
    """
    
    def __init__(self, project_path: str = "/home/gmorris/ansible-servicenow"):
        """
        Initialize the monitoring scheduler
        
        Args:
            project_path: Path to Ansible project directory
        """
        self.project_path = Path(project_path)
        self.factory = MonitoringRoleFactory(str(self.project_path / "roles"))
        self.service_manager = SystemdServiceManager(str(self.project_path))
        
        self.logger = self._setup_logging()
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
    
    def discover_roles(self) -> List[MonitoringRole]:
        """Discover all monitoring roles"""
        return self.factory.discover_monitoring_roles()
    
    def create_timers(self, inventory_file: str = "examples/inventory.yml", dry_run: bool = False):
        """
        Create systemd timers for all discovered monitoring roles
        
        Args:
            inventory_file: Path to Ansible inventory file
            dry_run: If True, only show what would be done
        """
        roles = self.discover_roles()
        
        if not roles:
            self.logger.warning("No monitoring roles discovered")
            return
        
        self.logger.info(f"Creating timers for {len(roles)} roles")
        
        success_count = 0
        for role in roles:
            self.logger.info(f"Processing role: {role.name}")
            
            # Validate role configuration
            errors = self.factory.validate_role(role)
            if errors:
                self.logger.error(f"Role {role.name} has validation errors: {', '.join(errors)}")
                continue
            
            # Install systemd service
            if self.service_manager.install_service(role, inventory_file, dry_run):
                success_count += 1
        
        self.logger.info(f"Successfully processed {success_count}/{len(roles)} roles")
    
    def show_status(self):
        """Show status of all monitoring services"""
        roles = self.discover_roles()
        
        print(f"\nMonitoring Services Status ({len(roles)} roles):")
        print("=" * 60)
        
        for role in roles:
            status = self.service_manager.get_service_status(role.systemd_service_name)
            
            service_status = "🟢 ACTIVE" if status.get('service_active') else "🔴 INACTIVE"
            timer_status = "🟢 ACTIVE" if status.get('timer_active') else "🔴 INACTIVE"
            
            print(f"\n📊 {role.name}")
            print(f"   Description: {role.description}")
            print(f"   Schedule: {role.schedule}")
            print(f"   Service: {service_status}")
            print(f"   Timer: {timer_status}")
            
            if status.get('error'):
                print(f"   ❌ Error: {status['error']}")
    
    def show_summary(self):
        """Show summary of discovered roles"""
        roles = self.discover_roles()
        summary = self.factory.get_role_summary(roles)
        
        print("\nMonitoring Roles Summary:")
        print("=" * 40)
        print(json.dumps(summary, indent=2))

def main():
    """Main entry point for the scheduler"""
    parser = argparse.ArgumentParser(description="Ansible ServiceNow Monitoring Scheduler")
    parser.add_argument('--project-path', default="/home/gmorris/ansible-servicenow",
                      help="Path to Ansible project directory")
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Discover command
    discover_parser = subparsers.add_parser('discover', help='Discover monitoring roles')
    
    # Create timers command
    create_parser = subparsers.add_parser('create-timers', help='Create systemd timers')
    create_parser.add_argument('--inventory', default="examples/inventory.yml",
                             help="Ansible inventory file")
    create_parser.add_argument('--dry-run', action='store_true',
                             help="Show what would be done without making changes")
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show service status')
    
    # Summary command
    summary_parser = subparsers.add_parser('summary', help='Show roles summary')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    scheduler = MonitoringScheduler(args.project_path)
    
    if args.command == 'discover':
        roles = scheduler.discover_roles()
        print(f"Discovered {len(roles)} monitoring roles:")
        for role in roles:
            print(f"  - {role.name}: {role.systemd_service_name}")
    
    elif args.command == 'create-timers':
        scheduler.create_timers(args.inventory, args.dry_run)
    
    elif args.command == 'status':
        scheduler.show_status()
    
    elif args.command == 'summary':
        scheduler.show_summary()

if __name__ == "__main__":
    main()