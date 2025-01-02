"""Example showing G1 glasses state changes and interactions"""
import asyncio
import logging
from datetime import datetime
from connector.base import G1Connector
from utils.constants import StateEvent
from utils.logger import setup_logger
from utils.config import Config
from rich.console import Console

class InteractionLogger:
    def __init__(self):
        from utils.logger import setup_logger
        from utils.config import Config
        from datetime import datetime
        from rich.console import Console
        
        config = Config.load()
        self.logger = setup_logger(config, "G1Interactions")
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
        
        # Get current timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Format side string - use actual side or "both" if None
        side_str = side if side else "both"
        
        # Check if this is an unknown state first
        if "unknown" in label.lower():
            base_color = "yellow"
        else:
            # Base color based on side for known states
            base_color = "grey74" if side == "left" else "white"
        
        # Format each column with exact spacing
        formatted_msg = (
            f"{timestamp}  "             # timestamp (19 chars) + 2 spaces
            f"{raw_code:02x}      "      # code (2 chars) + 6 spaces
            f"{event_type:<12}"          # type (12 chars)
            f"{side_str:<7} "            # side (7 chars + 1 space)
            f"{label}"                   # label (remaining space)
        )
        
        # Print with color, ensuring the entire line uses the same color
        self.console.print(f"[{base_color}]{formatted_msg}[/{base_color}]")

async def main():
    # Create connector with minimal logging
    glasses = G1Connector()
    logger = InteractionLogger()
    
    # Connect first, with normal logging
    await glasses.connect()
    
    # Clear the screen or add spacing before starting interaction monitoring
    print("\nMonitoring state changes (Ctrl+C to exit)...\n")
    
    # Track raw states
    async def raw_state_callback(state_code: int, is_physical: bool, side: str):
        """Handle raw state changes"""
        if state_code in StateEvent.BATTERY_STATES:
            _, label = StateEvent.get_battery_state(state_code)
            logger.log_event(state_code, "battery", side, label)
        elif state_code in StateEvent.PHYSICAL_STATES:
            _, label = StateEvent.get_physical_state(state_code)
            logger.log_event(state_code, "physical", side, label)
        elif state_code in StateEvent.DEVICE_STATES:
            _, label = StateEvent.get_device_state(state_code)
            logger.log_event(state_code, "device", side, label)
        elif state_code in StateEvent.INTERACTIONS:
            _, label = StateEvent.get_interaction(state_code)
            logger.log_event(state_code, "interaction", side, label)
        else:
            logger.log_event(state_code, "unknown", side, f"Unknown (0x{state_code:02x})")

    # Only register callback after successful connection
    if glasses.left_client and glasses.right_client:
        # Disable all console logging from glasses
        glasses.logger.handlers = [h for h in glasses.logger.handlers if not isinstance(h, logging.StreamHandler)]
        # Remove any state change callbacks
        glasses.state_manager._state_callbacks.clear()
        # Register only the raw state callback
        glasses.state_manager.add_raw_state_callback(raw_state_callback)
        
        try:
            # Keep the script running
            while True:
                await asyncio.sleep(0.1)
        except KeyboardInterrupt:
            print("\nExited by user")
    else:
        print("\nFailed to connect to glasses")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExited by user")
    except Exception as e:
        print(f"\nError: {e}") 