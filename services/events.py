"""
Event handling service for G1 glasses
Provides high-level event orchestration and subscription management
"""
import asyncio
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional
from time import time

from utils.constants import StateEvent, NOTIFICATIONS, COMMANDS
from utils.logger import user_guidance

@dataclass
class EventContext:
    """Context information for events"""
    side: Optional[str]  # 'left' or 'right'
    timestamp: float
    raw_data: Optional[bytes] = None
    metadata: Dict[str, any] = None

class EventService:
    """Handles high-level event orchestration for G1 glasses"""
    
    def __init__(self, connector):
        self.connector = connector
        self.logger = connector.logger
        
        # Initialize handler dictionaries for each event category
        self._physical_handlers: Dict[int, List[Callable]] = {
            code: [] for code in StateEvent.PHYSICAL_STATES.keys()
        }
        self._interaction_handlers: Dict[int, List[Callable]] = {
            code: [] for code in StateEvent.INTERACTIONS.keys()
        }
        self._device_handlers: Dict[int, List[Callable]] = {
            code: [] for code in StateEvent.DEVICE_STATES.keys()
        }
        self._battery_handlers: Dict[int, List[Callable]] = {
            code: [] for code in StateEvent.BATTERY_STATES.keys()
        }
        
        self._raw_handlers: List[Callable] = []
        self._event_history: List[tuple[int, EventContext]] = []
        self._max_history = 100
        self._setup_listeners()

    def _setup_listeners(self):
        """Initialize listeners for various event sources"""
        # Subscribe to state manager events
        self.connector.state_manager.add_raw_state_callback(self._handle_state_event)
        
        # Add UART notification callback
        self.connector.uart_service.add_notification_callback(self._handle_uart_event)

    async def _handle_state_event(self, state: int, is_physical: bool, side: str):
        """Process state changes from state manager"""
        context = EventContext(
            side=side,
            timestamp=asyncio.get_event_loop().time()
        )
        
        # Dispatch to appropriate handlers based on state type
        if state in StateEvent.PHYSICAL_STATES:
            await self._dispatch_event(state, context, self._physical_handlers)
        elif state in StateEvent.INTERACTIONS:
            await self._dispatch_event(state, context, self._interaction_handlers)
        elif state in StateEvent.DEVICE_STATES:
            await self._dispatch_event(state, context, self._device_handlers)
        elif state in StateEvent.BATTERY_STATES:
            await self._dispatch_event(state, context, self._battery_handlers)

    async def _handle_uart_event(self, data: bytes, side: str):
        """Process raw UART notifications"""
        if not data:
            return
            
        context = EventContext(
            side=side,
            timestamp=asyncio.get_event_loop().time(),
            raw_data=data
        )
        
        # Handle different notification types
        notification_type = data[0]
        if notification_type == NOTIFICATIONS.STATE_CHANGE:
            await self._handle_state_event(data[1], True, side)
        
        # Dispatch to raw handlers
        for handler in self._raw_handlers:
            try:
                await handler(data, context)
            except Exception as e:
                self.logger.error(f"Error in raw event handler: {e}")

    def subscribe_physical(self, state_code: int, handler: Callable):
        """Subscribe to physical state changes"""
        if state_code in StateEvent.PHYSICAL_STATES:
            self._physical_handlers[state_code].append(handler)

    def subscribe_interaction(self, interaction_code: int, handler: Callable):
        """Subscribe to interaction events"""
        if interaction_code in StateEvent.INTERACTIONS:
            self._interaction_handlers[interaction_code].append(handler)

    def subscribe_device(self, state_code: int, handler: Callable):
        """Subscribe to device state changes"""
        if state_code in StateEvent.DEVICE_STATES:
            self._device_handlers[state_code].append(handler)

    def subscribe_battery(self, state_code: int, handler: Callable):
        """Subscribe to battery state changes"""
        if state_code in StateEvent.BATTERY_STATES:
            self._battery_handlers[state_code].append(handler)

    def subscribe_raw(self, handler: Callable):
        """Subscribe to raw events"""
        if handler not in self._raw_handlers:
            self._raw_handlers.append(handler)

    def unsubscribe(self, handler: Callable):
        """Unsubscribe handler from all events"""
        # Remove from all handler dictionaries
        for handlers in [self._physical_handlers, self._interaction_handlers, 
                        self._device_handlers, self._battery_handlers]:
            for event_handlers in handlers.values():
                if handler in event_handlers:
                    event_handlers.remove(handler)
        
        # Remove from raw handlers
        if handler in self._raw_handlers:
            self._raw_handlers.remove(handler)

    async def _dispatch_event(self, event_code: int, context: EventContext, 
                            handlers: Dict[int, List[Callable]]):
        """Dispatch event to registered handlers"""
        # Store in history
        self._event_history.append((event_code, context))
        if len(self._event_history) > self._max_history:
            self._event_history.pop(0)
            
        # Dispatch to handlers
        if event_code in handlers:
            for handler in handlers[event_code]:
                try:
                    await handler(event_code, context)
                except Exception as e:
                    self.logger.error(f"Error in event handler: {e}")

    def get_recent_events(self, limit: int = 10) -> List[tuple[int, EventContext]]:
        """Get recent events from history"""
        return self._event_history[-limit:]