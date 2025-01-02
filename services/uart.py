"""
UART service implementation for G1 glasses
"""
import asyncio
from typing import Optional, Callable, Dict, Any
from bleak import BleakClient
from utils.constants import UUIDS, COMMANDS, NOTIFICATIONS
import time

class UARTService:
    """Handles UART service notifications from G1 glasses"""
    
    def __init__(self, connector):
        self.connector = connector
        self.logger = connector.logger
        self._notification_handlers = {}
        self._shutting_down = False

    async def send_command_with_retry(self, client: BleakClient, data: bytes, retries: int = 3) -> bool:
        """Send command with retry logic similar to official app"""
        for attempt in range(retries):
            try:
                await client.write_gatt_char(self.connector.UART_TX_CHAR_UUID, data, response=True)
                self.logger.debug(f"Command sent successfully on attempt {attempt + 1}")
                return True
            except Exception as e:
                self.logger.warning(f"Command failed on attempt {attempt + 1}: {e}")
                if attempt < retries - 1:
                    await asyncio.sleep(0.5)  # Wait before retry
        return False

    async def start_notifications(self, client: BleakClient, side: str):
        """Start UART notifications for a glass"""
        try:
            await client.start_notify(
                UUIDS.UART_RX,
                lambda sender, data: asyncio.create_task(
                    self._handle_notification(data, side)
                )
            )
            self.logger.debug(f"Started UART notifications for {side} glass")
        except Exception as e:
            self.logger.error(f"Failed to start UART notifications for {side} glass: {e}")
            raise

    async def _handle_notification(self, data: bytes, side: str):
        """Handle UART notification from glasses"""
        if self._shutting_down:
            return
            
        try:
            if not data:
                return
                
            # Log raw UART data
            self.logger.debug(f"Raw UART data from {side}: {data.hex()} ({len(data)} bytes)")
            
            notification_type = data[0]
            
            # Handle state changes (0xF5)
            if notification_type == NOTIFICATIONS.STATE_CHANGE:
                await self.connector.state_manager.handle_state_change(data[1], side)
            elif notification_type == NOTIFICATIONS.MIC_DATA:
                self.logger.debug(f"Microphone data received from {side}")
            elif notification_type == NOTIFICATIONS.HEARTBEAT_RESPONSE:
                self.logger.debug(f"Heartbeat response from {side}")
            elif notification_type == NOTIFICATIONS.COMMAND_RESPONSE:
                self.logger.debug(f"Command success response from {side}")
            elif notification_type == NOTIFICATIONS.ERROR_RESPONSE:
                self.logger.debug(f"Command error response from {side}")
            else:
                # Log unhandled notification types
                self.logger.debug(f"Unhandled notification type: 0x{notification_type:02x} from {side}")
                
        except Exception as e:
            self.logger.error(f"Error handling UART notification: {e}")

    def add_notification_callback(self, callback):
        """Add callback for notifications"""
        if callback not in self._notification_callbacks:
            self._notification_callbacks.append(callback)

    def remove_notification_callback(self, callback):
        """Remove callback for notifications"""
        if callback in self._notification_callbacks:
            self._notification_callbacks.remove(callback)

    async def stop_notifications(self, client: BleakClient) -> None:
        """Stop notifications for UART service"""
        try:
            await client.stop_notify(UUIDS.UART_RX)
            self.logger.debug("Stopped UART notifications")
        except Exception as e:
            if "17" not in str(e):  # Ignore error code 17 during disconnect
                self.logger.error(f"Error stopping notifications: {e}") 