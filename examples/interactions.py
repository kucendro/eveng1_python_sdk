"""Example showing G1 glasses state changes and interactions"""
import asyncio
import logging
from datetime import datetime
from connector import G1Connector
from utils.constants import (
    StateEvent, EventCategories, StateColors, 
    StateDisplay, ConnectionState
)
from utils.logger import setup_logger
from rich.console import Console

class InteractionLogger:
    def __init__(self):
        self.logger = setup_logger()
        self.log_count = 0
        self.console = Console()

    def print_header(self):
        """Print column headers"""
        self.console.print("\n[bold cyan]Timestamp            Code    Type        Side    Label[/bold cyan]")
        self.console.print("[cyan]" + "-" * 70 + "[/cyan]")

    def log_event(self, raw_code: int, event_type: str, side: str, label: str):
        """Log event in standardized format"""
        # Print header every 15 lines
        if self.log_count % 15 == 0:
            self.print_header()
        self.log_count += 1
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        side_str = side if side else "both"
        
        # Color logic based on event type
        base_color = {
            "physical": "blue",
            "battery": "yellow",
            "device": "green",
            "interaction": "cyan",
            "unknown": "red"
        }.get(event_type, "white")
        
        formatted_msg = (
            f"{timestamp}  "             # timestamp (19 chars) + 2 spaces
            f"{raw_code:02x}      "      # code (2 chars) + 6 spaces
            f"{event_type:<12}"          # type (12 chars)
            f"{side_str:<7} "            # side (7 chars + 1 space)
            f"{label}"                   # label (remaining space)
        )
        
        self.console.print(f"[{base_color}]{formatted_msg}[/{base_color}]")

class EventContext:
    """Context object for events"""
    def __init__(self, raw_data: bytes, side: str):
        self.raw_data = raw_data
        self.side = side

async def main():
    # Disable all console logging
    logging.getLogger().setLevel(logging.ERROR)
    
    glasses = G1Connector()
    logger = InteractionLogger()
    
    # Connect first
    print("Connecting to glasses...")
    success = await glasses.connect()
    if not success:
        print("\nFailed to connect to glasses")
        return
    
    # Clear console and show monitoring message
    print("\033[H\033[J")  # Clear screen
    print("Monitoring state changes (Ctrl+C to exit)...")
    await asyncio.sleep(0.5)
    
    # Now show the table headers
    logger.print_header()
    
    async def handle_state_change(raw_code: int, side: str, label: str):
        """Handle state changes from the state manager"""
        event_type = "unknown"
        if raw_code in StateEvent.BATTERY_STATES:
            event_type = "battery"
        elif raw_code in StateEvent.PHYSICAL_STATES:
            event_type = "physical"
        elif raw_code in StateEvent.DEVICE_STATES:
            event_type = "device"
        elif raw_code in StateEvent.INTERACTIONS:
            event_type = "interaction"
            
        logger.log_event(raw_code, event_type, side, label)
    
    # Register callback silently
    glasses.state_manager.add_raw_state_callback(handle_state_change)
    
    try:
        while True:
            await asyncio.sleep(0.1)
    except KeyboardInterrupt:
        print("\nExited by user")
    finally:
        glasses.state_manager.remove_raw_state_callback(handle_state_change)
        await glasses.disconnect()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExited by user")
    except Exception as e:
        print(f"\nError: {e}") 