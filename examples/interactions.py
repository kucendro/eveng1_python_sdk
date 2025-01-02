"""Example showing G1 glasses state changes and interactions"""
import asyncio
import logging
from datetime import datetime
from connector.base import G1Connector
from utils.constants import StateEvent

class InteractionLogger:
    def __init__(self):
        self.logger = logging.getLogger("G1Interactions")
        self.logger.setLevel(logging.INFO)
        self.log_count = 0
        
        # Console handler with custom formatting
        ch = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s  %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)

    def print_header(self):
        """Print column headers"""
        print("\ntimestamp            code  type         side   label")
        print("-" * 70)

    def log_event(self, raw_code: int, event_type: str, side: str, label: str):
        """Log event in standardized format"""
        # Print header every 15 lines
        if self.log_count % 15 == 0:
            self.print_header()
        self.log_count += 1
        
        # Format side string - use actual side or "both" if None
        side_str = side if side else "both"
        
        # Format each column with fixed width
        formatted_msg = f"{raw_code:02x}    {event_type:<12} {side_str:<6} {label}"
        self.logger.info(formatted_msg)

async def main():
    # Create connector with minimal logging
    glasses = G1Connector()
    logger = InteractionLogger()
    
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

    # Register the raw state callback
    glasses.state_manager.add_raw_state_callback(raw_state_callback)
    
    # Track paired events for dashboard open/close
    last_event = None
    last_side = None
    
    async def state_callback(phys_state: str, conn_state: str, interaction: str):
        """Handle state changes and interactions"""
        nonlocal last_event, last_side
        
        # For now, we can just pass as the dashboard events are handled by raw_state_callback
        # If you want to add additional processing for the formatted state strings, you can add it here
        pass

    try:
        # Set dashboard mode before connection to suppress all state change logs
        glasses.state_manager.set_dashboard_mode(True)
        
        # Connect (retry logic handled by SDK)
        if not await glasses.connect():
            print("Failed to connect to glasses")
            return
            
        # After connection, modify all handlers
        for handler in glasses.logger.handlers:
            if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
                handler.setLevel(logging.CRITICAL)  # Only show critical errors on console
        
        # Register our callbacks correctly
        glasses.state_manager.add_raw_state_callback(raw_state_callback)  # For basic state logging
        glasses.state_manager.add_state_callback(state_callback)  # For dashboard sequence detection
        
        print("\nMonitoring state changes (Ctrl+C to exit)...")
        logger.print_header()
        
        # Wait for Ctrl+C
        try:
            while True:
                await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            pass
            
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        # Clean shutdown
        await glasses.disconnect()
        # Cancel any pending tasks
        for task in asyncio.all_tasks():
            if task is not asyncio.current_task():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExited by user")
    except Exception as e:
        print(f"\nError: {e}") 