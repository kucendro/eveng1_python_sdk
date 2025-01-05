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
import re

class InteractionLogger:
    def __init__(self):
        self.logger = setup_logger()
        self.log_count = 0
        self.console = Console()

    def print_header(self):
        """Print column headers"""
        self.console.print("\n[white]Timestamp            Category              Code      Type          Side      Label[/white]")
        self.console.print("[white]" + "-" * 120 + "[/white]")

    def log_event(self, raw_code: int, category: str, event_type: str, side: str, label: str):
        """Log event in standardized format"""
        if self.log_count % 15 == 0:
            self.print_header()
        self.log_count += 1
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        side_str = side if side else "both"
        
        # Strip any existing color tags using regex
        label = re.sub(r'\[.*?\]', '', label)
        category = re.sub(r'\[.*?\]', '', category)
        event_type = re.sub(r'\[.*?\]', '', event_type)
        side_str = re.sub(r'\[.*?\]', '', side_str)
        
        # Determine if state is defined and if label contains "unknown"
        is_defined = raw_code in (
            StateEvent.BATTERY_STATES | 
            StateEvent.PHYSICAL_STATES | 
            StateEvent.DEVICE_STATES | 
            StateEvent.INTERACTIONS
        )
        has_unknown_label = "unknown" in label.lower()
        
        # Use StateColors constants for consistent coloring
        row_color = (
            StateColors.WARNING if (is_defined and has_unknown_label)
            else StateColors.ERROR if not is_defined
            else StateColors.SUCCESS
        )
        
        # Format the entire row as one string
        row = (
            f"{timestamp}  "             # timestamp (19 chars) + 2 spaces
            f"{category:<20}  "            # category (20 chars)
            f"0x{raw_code:02x}      "    # code (6 chars) + 6 spaces
            f"{event_type:<12}  "          # type (12 chars)
            f"{side_str:<10}"            # side (10 chars)
            f"{label}"                   # label (remaining space)
        )
        
        # Apply color to the entire row
        self.console.print(f"[{row_color}]{row}[/{row_color}]")

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
        
        # Get category from state manager's raw data
        category = "state (0xf5)"  # All state changes are 0xF5 category
        state_code = raw_code
        event_type = "unknown"
        
        # Determine type from the state code
        if state_code in StateEvent.BATTERY_STATES:
            event_type = "battery"
        elif state_code in StateEvent.PHYSICAL_STATES:
            event_type = "physical"
        elif state_code in StateEvent.DEVICE_STATES:
            event_type = "device"
        elif state_code in StateEvent.INTERACTIONS:
            event_type = "interaction"
            
        logger.log_event(state_code, category, event_type, side, label)
    
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