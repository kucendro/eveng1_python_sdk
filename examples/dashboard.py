"""Dashboard example for G1 glasses"""
import asyncio
from rich.live import Live
from rich.table import Table
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.logging import RichHandler
from collections import deque
import logging
from connector import G1Connector
from services.state import ConnectionState
import time
from rich.box import ROUNDED
from utils.constants import StateEvent

class LogPanel:
    """Panel to display recent log messages"""
    def __init__(self, max_lines=10):
        self.logs = deque(maxlen=max_lines)
        # Create a custom handler that adds logs to our deque
        self.handler = logging.Handler()
        self.handler.emit = self.emit
        
    def emit(self, record):
        """Custom emit method to handle log records"""
        try:
            msg = record.getMessage()
            
            # Skip status data logs entirely
            if "Status data:" in msg:
                return
                
            # Handle disconnect messages as errors
            if "glass disconnected" in msg.lower():
                self.logs.append(f"[red]{msg}[/red]")
                return
                
            # Skip certain messages during initial connection
            if any(skip in msg for skip in [
                "Connection state changed to",
                "Physical state changed to",
                "Battery state changed to",
                "Glasses now in",
                "Verifying pairing",
                "Started notifications",
                "Status data:",
                "Connecting to G1"
            ]):
                return
                
            # Show interaction events in cyan
            if "Interaction detected:" in msg:
                self.logs.append(f"[cyan]{msg}[/cyan]")
                return
                
            # Show battery events in yellow
            if "Battery state changed to:" in msg:
                self.logs.append(f"[yellow]{msg}[/yellow]")
                return
                
            # Show physical state changes in blue
            if "Physical state changed to:" in msg:
                self.logs.append(f"[blue]{msg}[/blue]")
                return
                
            # Only show essential connection messages
            if "Connecting to G1" in msg:
                self.logs.append("[yellow]Connecting to G1, please wait...[/yellow]")
                return
                
            if "Connected successfully" in msg:
                self.logs.append("[green]Connected successfully[/green]")
                return
                
            if "Error connecting" in msg or "Connection failed" in msg:
                self.logs.append("[red]Error connecting, retrying...[/red]")
                return
            
            # Format other messages
            if record.levelno >= logging.ERROR:
                msg = f"[red]{msg}[/red]"
            elif record.levelno >= logging.WARNING:
                msg = f"[orange3]{msg}[/orange3]"
            elif "success" in msg.lower():
                msg = f"[green]{msg}[/green]"
            else:
                msg = f"[white]{msg}[/white]"
                
            self.logs.append(msg)
            
        except Exception as e:
            print(f"Error in log panel: {e}")
    
    def __rich__(self):
        return Panel(
            "\n".join(self.logs),
            title="Recent Logs",
            border_style="blue"
        )

def create_layout(glasses, log_panel) -> Layout:
    """Create dashboard layout with status and logs"""
    layout = Layout()
    
    # Create status panel
    status_panel = Panel(
        create_status_table(glasses),
        title="Status",
        border_style="blue"
    )
    
    # Use log_panel directly as it's already a Panel
    
    # Split into left (status) and right (logs) panels
    layout.split_row(
        Layout(status_panel, ratio=3),
        Layout(log_panel, ratio=2)  # log_panel is already a Panel
    )
    
    return layout

def create_status_table(glasses: G1Connector) -> Table:
    """Create status table from G1 connector state"""
    try:
        table = Table(box=ROUNDED)
        
        # Add column headers with consistent styling
        table.add_column("[bold cyan]Item", style="cyan")
        table.add_column("[bold cyan]Status", style="white")
        
        # Connection status with more detail
        left_name = glasses.config.left_name or "Unknown"
        right_name = glasses.config.right_name or "Unknown"
        left_status = f"[green]Connected ({left_name})[/green]" if glasses.left_client and glasses.left_client.is_connected else "[red]Disconnected[/red]"
        right_status = f"[green]Connected ({right_name})[/green]" if glasses.right_client and glasses.right_client.is_connected else "[red]Disconnected[/red]"
        table.add_row("Left Glass", left_status)
        table.add_row("Right Glass", right_status)
        
        # Physical state with last known state
        state = glasses.state_manager.physical_state
        last_state = glasses.state_manager._last_known_state or "None"
        state_colors = {
            "Wearing": "green",
            "Transitioning": "yellow",
            "In the cradle": "blue",
            "None": "white"
        }
        color = state_colors.get(last_state, "yellow")
        table.add_row("State", f"[{color}]{last_state}[/{color}]")
        
        # Battery state
        battery = glasses.state_manager.battery_state
        battery_colors = {
            "Battery fully charged": "bright_green",
            "Battery charging?": "yellow",
            "Unknown": "yellow"
        }
        color = battery_colors.get(battery, "yellow")
        table.add_row("Battery", f"[{color}]{battery}[/{color}]")
        
        # Last heartbeat
        last_heartbeat = getattr(glasses.state_manager, '_last_heartbeat', None)
        if last_heartbeat:
            time_since = time.time() - last_heartbeat
            heartbeat_status = f"{time_since:.1f}s ago"
            color = "green" if time_since < 5 else "yellow"
        else:
            heartbeat_status = "None"
            color = "white"
        table.add_row("Last Heartbeat", f"[{color}]{heartbeat_status}[/{color}]")
        
        # Last interaction
        interaction = glasses.state_manager.last_interaction
        interaction_time = getattr(glasses.state_manager, '_last_interaction_time', None)
        if interaction and interaction != "None" and interaction_time:
            time_since = time.time() - interaction_time
            interaction_status = f"{interaction} ({time_since:.1f}s ago)"
            table.add_row("Last Interaction", f"[cyan]{interaction_status}[/cyan]")
        else:
            table.add_row("Last Interaction", "[white]None[/white]")
        
        # Last device state
        last_device_state = glasses.state_manager._last_device_state
        last_device_time = glasses.state_manager._last_device_state_time
        if last_device_state and last_device_time:
            time_since = time.time() - last_device_time
            label = glasses.state_manager.last_device_state_label
            device_status = f"{label} ({time_since:.1f}s ago)"
            table.add_row("Last Device State", f"[yellow]{device_status}[/yellow]")
        else:
            table.add_row("Last Device State", "[white]None[/white]")
        
        # Silent mode status
        silent_mode = glasses.state_manager.silent_mode
        color = "yellow" if silent_mode else "green"
        status = "On" if silent_mode else "Off"
        table.add_row("Silent Mode", f"[{color}]{status}[/{color}]")
        
        return table
    except Exception as e:
        glasses.logger.error(f"Error creating status table: {e}", exc_info=True)
        error_table = Table(box=ROUNDED)
        error_table.add_row("[red]Error creating status display[/red]")
        return error_table

async def main():
    """Run the dashboard example"""
    glasses = G1Connector()
    console = Console()
    log_panel = LogPanel(max_lines=15)
    
    try:
        console.clear()
        glasses.state_manager.set_dashboard_mode(True)
        
        success = await glasses.connect()
        
        if not success:
            console.print("[red]Failed to connect to glasses[/red]")
            return
            
        console.print("[green]Connected successfully[/green]")
        await asyncio.sleep(1)
        console.clear()
        
        glasses.logger.addHandler(log_panel.handler)
        
        with Live(create_layout(glasses, log_panel), console=console, refresh_per_second=4) as live:
            try:
                while True:
                    live.update(create_layout(glasses, log_panel))
                    await asyncio.sleep(0.25)
            except KeyboardInterrupt:
                # Handle the interrupt gracefully
                live.stop()
                console.clear()
                console.print("[yellow]Shutting down...[/yellow]")
                    
    except KeyboardInterrupt:
        console.print("[yellow]Shutting down...[/yellow]")
    except Exception as e:
        glasses.logger.error(f"Dashboard error: {e}", exc_info=True)
    finally:
        # Ensure clean shutdown
        glasses.logger.removeHandler(log_panel.handler)
        glasses.state_manager.set_dashboard_mode(False)
        glasses.state_manager.shutdown()
        await glasses.disconnect()
        console.print("[green]Dashboard exited[/green]")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExited by user")
    except Exception as e:
        print(f"\nError: {e}") 