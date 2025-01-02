"""
Device management service for G1 glasses
if battery status is available, add that here too
"""

class DeviceManager:
    """Handles device-wide states and controls"""
    
    def __init__(self, connector):
        self.connector = connector
        self.logger = connector.logger
        self._silent_mode = False
    
    @property
    def silent_mode(self) -> bool:
        """Get current silent mode state"""
        return self._silent_mode
    
    async def set_silent_mode(self, enabled: bool) -> bool:
        """Set silent mode state (disables all functionality)"""
        try:
            if enabled == self._silent_mode:
                return True
                
            # Command structure for silent mode
            command = bytes([0x22, 0x01 if enabled else 0x00])
            
            result = await self.connector.command_manager.send_command(
                self.connector.right_client,
                command,
                expect_response=True
            )
            
            if result and result[1] == 0xC9:  # Success response
                self._silent_mode = enabled
                self.logger.info(f"Silent mode {'enabled' if enabled else 'disabled'}")
                await self.connector.update_status()
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error setting silent mode: {e}")
            return False 