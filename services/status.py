"""Status display service for G1 glasses"""
import asyncio
from rich.table import Table
from rich.live import Live
from ..utils.constants import StateEvent

class StatusManager:
    """Manages status display and dashboard"""
    
    def __init__(self, connector):
        self.connector = connector
        self.logger = connector.logger
        self._live = None
        self._running = False
        
    def generate_table(self) -> Table:
        """Generate status table for display"""
        table = Table(title="G1 Glasses Status")
        
        # Add columns
        table.add_column("Device", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Signal", style="yellow")
        table.add_column("Errors", style="red")
        
        # Add left glass status
        left_rssi = self.connector._connection_quality['left']['rssi']
        left_errors = self.connector._connection_quality['left']['errors']
        table.add_row(
            f"Left Glass ({self.connector.config.left_name or 'Not Found'})",
            "Connected" if self.connector.left_client and self.connector.left_client.is_connected else "Disconnected",
            f"{left_rssi}dBm" if left_rssi else "N/A",
            str(left_errors)
        )
        
        # Add right glass status
        right_rssi = self.connector._connection_quality['right']['rssi']
        right_errors = self.connector._connection_quality['right']['errors']
        table.add_row(
            f"Right Glass ({self.connector.config.right_name or 'Not Found'})",
            "Connected" if self.connector.right_client and self.connector.right_client.is_connected else "Disconnected",
            f"{right_rssi}dBm" if right_rssi else "N/A",
            str(right_errors)
        )
        
        # Add state information
        table.add_row(
            "Physical State",
            self.connector.state_manager.physical_state,
            "",
            ""
        )
        
        # Add last interaction if any
        if self.connector.state_manager.last_interaction != "None":
            table.add_row(
                "Last Interaction",
                self.connector.state_manager.last_interaction,
                "",
                ""
            )
        
        table.add_row(
            "Connection",
            self.connector.state_manager.connection_state,
            "",
            ""
        )
        
        return table
        
    async def start(self) -> None:
        """Start live status display"""
        if self._running:
            return
            
        self._running = True
        self._live = Live(
            self.generate_table(),
            refresh_per_second=1,
            console=self.connector.console
        )
        self._live.start()
        
        while self._running:
            self._live.update(self.generate_table())
            await asyncio.sleep(1)
            
    async def stop(self) -> None:
        """Stop live status display"""
        self._running = False
        if self._live:
            self._live.stop()
            
    async def update(self) -> None:
        """Update status display"""
        if self._live:
            self._live.update(self.generate_table()) 