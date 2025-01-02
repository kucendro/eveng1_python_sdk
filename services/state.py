"""
State management for G1 glasses
"""
from enum import Enum, IntEnum
import asyncio
from ..utils.constants import StateEvent, ConnectionState, NOTIFICATIONS

class StateManager:
    """Manages state for G1 glasses"""
    
    def __init__(self, connector):
        self.connector = connector
        self.logger = connector.logger
        self._physical_state = None
        self._battery_state = None  # Add explicit battery state tracking
        self._connection_state = ConnectionState.DISCONNECTED
        self._last_interaction = None
        self._last_interaction_side = None
        self._state_callbacks = []
        self._raw_state_callbacks = []
        self._unrecognized_states = set()
        self._dashboard_mode = False
        self._last_known_state = None
        self._silent_mode = False
        self._shutting_down = False

    def shutdown(self):
        """Mark manager as shutting down"""
        self._shutting_down = True
        self._state_callbacks.clear()

    @property
    def battery_state(self) -> str:
        """Get current battery state display label"""
        if self._battery_state is None:
            return "Unknown"
        return StateEvent.get_battery_state(self._battery_state)[1]

    @property
    def physical_state(self) -> str:
        """Get current physical state display label"""
        if self._physical_state is None:
            return "Unknown"
        # Only return physical state if it's in PHYSICAL_STATES
        if self._physical_state in StateEvent.PHYSICAL_STATES:
            return StateEvent.get_physical_state(self._physical_state)[1]
        return "Unknown"

    @property
    def connection_state(self) -> str:
        """Get current connection state"""
        return str(self._connection_state.value)

    @connection_state.setter
    def connection_state(self, state: str):
        """Set connection state"""
        if self._shutting_down:
            return
            
        try:
            if isinstance(state, str):
                self._connection_state = ConnectionState(state)
            elif isinstance(state, ConnectionState):
                self._connection_state = state
            else:
                raise ValueError(f"Invalid state type: {type(state)}")
            
            # Only log if not in dashboard mode
            if not self._dashboard_mode:
                self.logger.info(f"Connection state changed to: {self.connection_state}")
            
            asyncio.create_task(self._notify_state_change())
        except ValueError as e:
            self.logger.error(f"Invalid connection state: {state}")

    def set_dashboard_mode(self, enabled: bool):
        """Toggle dashboard mode to suppress state change logging"""
        if not isinstance(enabled, bool):
            raise ValueError("Dashboard mode must be a boolean")
        self._dashboard_mode = enabled

    @property
    def last_interaction(self) -> str:
        """Get last interaction display label with side if applicable"""
        if self._last_interaction is None:
            return "None"
        _, label = StateEvent.get_interaction(self._last_interaction)
        if self._last_interaction_side:
            return f"{label} ({self._last_interaction_side})"
        return label

    async def handle_state_change(self, new_state: int, side: str = None):
        """Handle state change from glasses"""
        if self._shutting_down:
            return
            
        try:
            # Notify raw callbacks first
            for callback in self._raw_state_callbacks:
                try:
                    await callback(new_state, new_state in StateEvent.PHYSICAL_STATES, side)
                except Exception as e:
                    self.logger.error(f"Error in raw state callback: {e}")

            self.logger.debug(f"Raw state received: 0x{new_state:02x} ({new_state}) from {side} glass")
            
            # Check if it's a physical state
            if new_state in StateEvent.PHYSICAL_STATES:
                system_name, display_label = StateEvent.get_physical_state(new_state)
                self._physical_state = new_state
                self._last_known_state = new_state
                
                if not self._dashboard_mode:
                    self.logger.info(f"Physical state changed to: {display_label} (0x{new_state:02x}) from {side} glass")
            
            # Check if it's a device state
            elif new_state in StateEvent.DEVICE_STATES:
                system_name, display_label = StateEvent.get_device_state(new_state)
                # Update relevant state if needed
                if not self._dashboard_mode:
                    self.logger.info(f"Device state changed to: {display_label} (0x{new_state:02x}) from {side} glass")
            
            # Check if it's a battery state
            elif new_state in StateEvent.BATTERY_STATES:
                system_name, display_label = StateEvent.get_battery_state(new_state)
                self._battery_state = new_state
                
                if not self._dashboard_mode:
                    self.logger.info(f"Battery state changed to: {display_label} (0x{new_state:02x}) from {side} glass")
            
            # Handle interactions
            elif new_state in StateEvent.INTERACTIONS:
                system_name, display_label = StateEvent.get_interaction(new_state)
                self._last_interaction = display_label
                self._last_interaction_side = side
                
                if not self._dashboard_mode:
                    self.logger.info(f"Interaction detected: {display_label} (0x{new_state:02x}) from {side} glass")
            
            # Handle unknown states
            else:
                if new_state not in self._unrecognized_states:
                    self._unrecognized_states.add(new_state)
                    self.logger.debug(f"Unrecognized state: 0x{new_state:02x} ({new_state}) from {side} glass")
            
            await self._notify_state_change()
                
        except Exception as e:
            self.logger.error(f"Error handling state change: {e}")

    async def _notify_state_change(self):
        """Notify callbacks of state change"""
        if self._shutting_down:
            return
            
        try:
            for callback in self._state_callbacks:
                try:
                    # Include both physical state and last interaction
                    phys_state = str(self.physical_state)
                    conn_state = str(self.connection_state)
                    interaction = str(self.last_interaction)
                    await callback(phys_state, conn_state, interaction)
                except Exception as e:
                    self.logger.error(f"Error in state change callback: {e}", exc_info=True)
        except Exception as e:
            self.logger.error(f"Error notifying state change: {e}", exc_info=True)

    def add_state_callback(self, callback):
        """Add callback for state changes"""
        if callback not in self._state_callbacks:
            self._state_callbacks.append(callback)

    def remove_state_callback(self, callback):
        """Remove callback for state changes"""
        if callback in self._state_callbacks:
            self._state_callbacks.remove(callback)

    def add_raw_state_callback(self, callback):
        """Add callback for raw state changes"""
        if callback not in self._raw_state_callbacks:
            self._raw_state_callbacks.append(callback)

    def remove_raw_state_callback(self, callback):
        """Remove callback for raw state changes"""
        if callback in self._raw_state_callbacks:
            self._raw_state_callbacks.remove(callback) 
            self._state_callbacks.remove(callback) 

    @property
    def silent_mode(self) -> bool:
        """Get current silent mode state"""
        return self._silent_mode
        
    @silent_mode.setter
    def silent_mode(self, value: bool):
        """Set silent mode state"""
        self._silent_mode = value
        if not self._dashboard_mode:
            self.logger.info(f"Silent mode {'enabled' if value else 'disabled'}") 