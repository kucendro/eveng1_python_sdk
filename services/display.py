"""
Display service implementation for G1 glasses
"""

from bleak import BleakClient
from typing import List, Optional

from utils.constants import COMMANDS
from utils.logger import user_guidance

class DisplayService:
    """Handles text and image display"""
    def __init__(self):
        pass 