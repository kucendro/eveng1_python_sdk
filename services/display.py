"""
Display service implementation for G1 glasses
"""
import asyncio
from bleak import BleakClient
from typing import List, Optional
from utils.logger import setup_logger

class DisplayService:
    """Handles text and image display"""
    
    # Constants from documentation
    MAX_WIDTH_PIXELS = 488
    FONT_SIZE = 21
    LINES_PER_SCREEN = 5
    CHARS_PER_LINE = MAX_WIDTH_PIXELS // FONT_SIZE  # Approximate, needs testing
    MAX_TEXT_LENGTH = CHARS_PER_LINE * LINES_PER_SCREEN
    
    def __init__(self, connector):
        self.connector = connector
        self.logger = setup_logger()
        self._current_text = None  # Track currently displayed text
        
    def _split_text_into_chunks(self, text: str) -> List[str]:
        """Split text into screen-sized chunks, breaking at word boundaries"""
        chunks = []
        words = text.split()
        current_chunk = []
        current_length = 0
        
        for word in words:
            # Check if word itself is too long
            if len(word) > self.CHARS_PER_LINE:
                if current_chunk:
                    chunks.append(' '.join(current_chunk))
                    current_chunk = []
                    current_length = 0
                
                # Split long word
                for i in range(0, len(word), self.CHARS_PER_LINE):
                    chunks.append(word[i:i + self.CHARS_PER_LINE])
                continue
            
            # Check if adding this word exceeds the chunk size
            if current_length + len(word) + 1 > self.MAX_TEXT_LENGTH:
                chunks.append(' '.join(current_chunk))
                current_chunk = [word]
                current_length = len(word)
            else:
                current_chunk.append(word)
                current_length += len(word) + 1
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
            
        return chunks

    def validate_text(self, text: str) -> bool:
        """Validate text length and content"""
        if not text:
            raise ValueError("Text cannot be empty")
        return True

    async def send_text_sequential(self, text: str, hold_time: Optional[int] = None, show_exit: bool = True):
        """Send text to both glasses in sequence with acknowledgment"""
        # Check connection status first
        if not self.connector.left_client or not self.connector.right_client:
            self.logger.error("Glasses not connected. Please connect first.")
            return False
        
        if not self.connector.left_client.is_connected or not self.connector.right_client.is_connected:
            self.logger.error("One or both glasses disconnected. Please reconnect.")
            return False

        command = bytearray([
            0x4E,       # Text command
            0x00,       # Sequence number
            0x01,       # Total packages
            0x00,       # Current package
            0x71,       # Screen status (0x70 Text Show + 0x01 New Content)
            0x00, 0x00, # Character position
            0x00,       # Current page
            0x01,       # Max pages
        ])
        
        command.extend(text.encode('utf-8'))
        self._current_text = text
        
        try:
            # Send to left and wait for acknowledgment
            self.logger.info(f"Sending to left glass: '{text}'")
            if not await self.connector.uart_service.send_command_with_retry(self.connector.left_client, command):
                self.logger.error("Failed to send to left glass")
                return False
            
            await asyncio.sleep(1)  # Wait for acknowledgment
            
            # Send to right
            self.logger.info("Left glass acknowledged, sending to right...")
            if not await self.connector.uart_service.send_command_with_retry(self.connector.right_client, command):
                self.logger.error("Failed to send to right glass")
                return False
            
            # Hold for specified time if provided
            if hold_time is not None:
                self.logger.info(f"Holding text for {hold_time} seconds...")
                await asyncio.sleep(hold_time)
                if show_exit:  # Only show exit if requested
                    await self.show_exit_message()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending text: {e}")
            return False

    async def display_text(self, text: str, hold_time: Optional[int] = None):
        """Display a single text with optional hold time"""
        self.validate_text(text)
        
        if len(text) <= self.MAX_TEXT_LENGTH:
            return await self.send_text_sequential(text, hold_time)
        else:
            self.logger.info("Text exceeds screen size, splitting into chunks...")
            chunks = self._split_text_into_chunks(text)
            return await self.display_text_sequence(chunks, hold_time)

    async def display_text_sequence(self, texts: List[str], hold_time: Optional[int] = 5):
        """Display a sequence of texts with specified hold time"""
        if not texts:
            raise ValueError("Text sequence cannot be empty")
            
        # Validate all texts first
        for text in texts:
            self.validate_text(text)
            if len(text) > self.MAX_TEXT_LENGTH:
                raise ValueError(f"Text exceeds maximum length of {self.MAX_TEXT_LENGTH} characters: {text[:50]}...")
        
        # Display each text in sequence
        for i, text in enumerate(texts, 1):
            self.logger.info(f"Displaying text {i} of {len(texts)}")
            show_exit = (i == len(texts))  # Only show exit on last text
            if not await self.send_text_sequential(text, hold_time, show_exit=show_exit):
                return False
                
        return True

    async def show_exit_message(self):
        """Display exit message and wait for user action"""
        if self._current_text != "Activity completed, double-tap to exit":
            await self.send_text_sequential("Activity completed, double-tap to exit", hold_time=3) 