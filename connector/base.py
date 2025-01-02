"""
Base connector class for G1 glasses
"""
from rich.console import Console
from rich.live import Live
from rich.table import Table
import os
import time
import logging
import asyncio
from dataclasses import dataclass
from typing import Optional

from connector.bluetooth import BLEManager
from connector.pairing import PairingManager
from connector.commands import CommandManager
from services.state import StateManager
from services.uart import UARTService
from utils.logger import setup_logger
from utils.config import Config
from utils.constants import UUIDS, COMMANDS, StateEvent

@dataclass
class G1Config:
    """Configuration for G1 glasses SDK"""
    CONFIG_FILE = "g1_config.json"
    
    # Logging configuration
    log_level: str = "INFO"
    log_file: str = "g1_connector.log"
    console_log: bool = True
    
    # Connection configuration
    heartbeat_interval: int = 8  # seconds
    reconnect_attempts: int = 3
    reconnect_delay: float = 1.0  # seconds
    
    # Device information (auto-populated)
    left_address: Optional[str] = None
    right_address: Optional[str] = None
    left_name: Optional[str] = None
    right_name: Optional[str] = None

class G1Connector:
    """Main connector class for G1 glasses"""
    
    def __init__(self):
        """Initialize the connector"""
        # Load or create config
        self.config = Config.load()
        
        # Set up logging
        self.logger = setup_logger(self.config)
        
        # Initialize Rich console for status display
        self.console = Console()
        
        # Initialize connection quality tracking
        self._connection_quality = {
            'left': {'rssi': None, 'errors': 0},
            'right': {'rssi': None, 'errors': 0}
        }
        
        # Initialize clients
        self.left_client = None
        self.right_client = None
        
        # Initialize managers and services in correct order
        self.state_manager = StateManager(self)  # Initialize state_manager first
        self.pairing_manager = PairingManager(self)
        self.ble_manager = BLEManager(self)
        self.command_manager = CommandManager(self)
        self.uart_service = UARTService(self)

    async def connect(self):
        """Connect to glasses"""
        try:
            # Only set state once at the beginning
            self.state_manager.connection_state = "Connecting..."
            
            # Attempt connection
            if not await self.ble_manager.connect_to_glasses():
                self.state_manager.connection_state = "Disconnected"
                return False
            
            self.state_manager.connection_state = "Connected"
            return True
                
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            self.state_manager.connection_state = "Disconnected"
            return False

    async def disconnect(self):
        """Disconnect from glasses"""
        try:
            await self.ble_manager.disconnect()
            self.state_manager.connection_state = "Disconnected"
        except Exception as e:
            self.logger.error(f"Error during disconnect: {e}")

    async def update_status(self):
        """Update and display current status"""
        try:
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Status", style="dim")
            table.add_column("Value")
            
            # Add status rows
            table.add_row(
                "Left Glass",
                "Connected" if self.left_client and self.left_client.is_connected else "Disconnected"
            )
            table.add_row(
                "Right Glass",
                "Connected" if self.right_client and self.right_client.is_connected else "Disconnected"
            )
            table.add_row(
                "State",
                self.state_manager.physical_state
            )
            
            # Add silent mode status if device manager exists
            if hasattr(self, 'device_manager'):
                table.add_row(
                    "Silent Mode",
                    "Enabled" if self.device_manager.silent_mode else "Disabled"
                )
            
            # Add error counts if any
            left_errors = self._connection_quality['left']['errors']
            right_errors = self._connection_quality['right']['errors']
            if left_errors > 0 or right_errors > 0:
                table.add_row(
                    "Errors",
                    f"Left: {left_errors}, Right: {right_errors}"
                )
            
            # Clear screen and display new status
            self.console.clear()
            self.console.print("\n[bold]G1 Glasses Status[/bold]")
            self.console.print(table)
            
        except Exception as e:
            self.logger.error(f"Error updating status: {e}") 