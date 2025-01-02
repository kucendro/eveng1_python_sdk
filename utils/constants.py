"""
Constants used throughout the G1 SDK
"""

from enum import IntEnum, Enum
from typing import Dict, Tuple

class ConnectionState(str, Enum):
    """Connection states for G1 glasses"""
    DISCONNECTED = "Disconnected"
    CONNECTING = "Connecting..."
    CONNECTED = "Connected"
    SCANNING = "Scanning..."

class UUIDS:
    """Bluetooth UUIDs used by G1 glasses"""
    UART_SERVICE = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
    UART_TX = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"
    UART_RX = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"

class COMMANDS:
    """Command codes for G1 glasses"""
    # Command structures
    HEARTBEAT_CMD = bytes([0x25, 0x06, 0x00, 0x01, 0x04, 0x01])
    IMAGE_END_CMD = bytes([0x20, 0x0D, 0x0E])
    
    # event categories
    HEARTBEAT = 0x25
    STATE_CHANGE = 0xF5
    DASHBOARD = 0x22
    
    #TEXT_DISPLAY = 0x4E
    #IMAGE_DATA = 0x15
    #IMAGE_END = 0x20
    #IMAGE_CRC = 0x16
    #MIC_CONTROL = 0x0E
    #MIC_DATA = 0xF1
    #EVEN_AI = 
    
    # Response codes
    SUCCESS = 0xC9
    FAILURE = 0xCA
    
    @classmethod
    def get_heartbeat_cmd(cls) -> bytes:
        """Get heartbeat command"""
        return cls.HEARTBEAT_CMD
    
    @classmethod
    def get_image_end_cmd(cls) -> bytes:
        """Get image end command"""
        return cls.IMAGE_END_CMD


class NOTIFICATIONS:
    """Notification types from glasses"""
    STATE_CHANGE = 0xF5
    MIC_DATA = 0xF1
    HEARTBEAT_RESPONSE = 0x25
    COMMAND_RESPONSE = 0xC9
    ERROR_RESPONSE = 0xCA
    
    # Screen status bits
    SCREEN_NEW_CONTENT = 0x01
    SCREEN_EVEN_AI = 0x30
    SCREEN_AI_COMPLETE = 0x40
    SCREEN_MANUAL_MODE = 0x50
    SCREEN_ERROR = 0x60 


class StateEvent:
    """State and interaction events for G1 glasses"""
        
    # Physical States - (code, system_name, display_label)
    PHYSICAL_STATES: Dict[int, Tuple[str, str]] = {
        0x06: ("WEARING", "Wearing"),
        0x07: ("TRANSITIONING", "Transitioning"),
        0x08: ("CRADLE", "In the cradle")
        
    }
    
    # Device States, including connectivity - (code, system_name, display_label)
    DEVICE_STATES: Dict[int, Tuple[str, str]] = {
        0x09: ("DEVICE_UNKNOWN_09", "Device unknown 09"),
        0x0a: ("DEVICE_UNKNOWN_0a", "Device unknown 0a"), # this one started appearing after the firmware update on 2025-01-02 (left and right)
        0x0f: ("DEVICE_UNKNOWN_0F", "Device unknown 0f"), # seen at regular intervals while device was connect out and in cradle over 8 hours
        0x11: ("CONNECTED", "Successfully connected"), # assumed because its usualy at the start of the connection
        0x12: ("DEVICE_UNKNOWN_12", "Device unknown 12"), # seen, unclear purpose
        0x14: ("DEVICE_UNKNOWN_15", "Device unknown 14"), # seen, unclear purpose
        0x15: ("DEVICE_UNKNOWN_16", "Device unknown 15") # seen, unclear purpose
    }

    # Battery States - (code, system_name, display_label)
    BATTERY_STATES: Dict[int, Tuple[str, str]] = {
        0x09: ("BATTERY_CHARGED", "Battery fully charged"),
        0x0e: ("BATTERY_CHARGING", "Battery charging?"),
    }
    
    # Interaction Events - (code, system_name, display_label)
    INTERACTIONS: Dict[int, Tuple[str, str]] = {
        0x00: ("DOUBLE_TAP", "Double tap"), # works left and right
        0x01: ("SINGLE_TAP", "Single tap"), # does not trigger an event, internal use only?
        0x02: ("OPEN_DASHBOARD_START", "Open dashboard start"),  # followed by 0x1e, this seems to indicate open dashboard
        0x03: ("CLOSE_DASHBOARD_START", "Close dashboard start"),  # followed by 0x1f, this seems to indicate close dashboard
        0x04: ("SILENT_MODE_ON", "Silent mode enabled"), # works left and right
        0x05: ("SILENT_MODE_OFF", "Silent mode disabled"), # works left and right
        0x17: ("LONG_PRESS", "Long press"), # left enables ai, right does not trigger an event, internal use only?
        0x1e: ("OPEN_DASHBOARD", "Open dashboard confirmed"), # preceded by 0x02, this seems to indicate open dashboard
        0x1f: ("CLOSE_DASHBOARD", "Close dashboard confirmed"), # preceded by 0x03, this seems to indicate close dashboard
    }

    # Unknown or unused events - (code, system_name, display_label)
    UNKNOWN: Dict[int, Tuple[str, str]] = {
        0x0b: ("UNKNOWN0B", "Unknown (0x0b)"),
        0x0c: ("UNKNOWN0C", "Unknown (0x0c)"),
        0x0d: ("UNKNOWN0D", "Unknown (0x0d)"),
        0x10: ("UNKNOWN10", "Unknown (0x10)"),
        0x13: ("UNKNOWN13", "Unknown (0x13)"),
        0x16: ("UNKNOWN16", "Unknown (0x16)"),
        0x18: ("UNKNOWN18", "Unknown (0x18)"),
        0x19: ("UNKNOWN19", "Unknown (0x19)"),
        0x1a: ("UNKNOWN1A", "Unknown (0x1a)"),
        0x1b: ("UNKNOWN1B", "Unknown (0x1b)"),
        0x1c: ("UNKNOWN1C", "Unknown (0x1c)"),
        0x1d: ("UNKNOWN1D", "Unknown (0x1d)")
    }
    
    @classmethod
    def get_battery_state(cls, code: int) -> Tuple[str, str]:
        """Get (system_name, display_label) for a battery state code"""
        return cls.BATTERY_STATES.get(code, ("UNKNOWN", f"Unknown battery state (0x{code:02x})"))

    @classmethod
    def get_physical_state(cls, code: int) -> Tuple[str, str]:
        """Get (system_name, display_label) for a physical state code"""
        if code in cls.PHYSICAL_STATES:
            return cls.PHYSICAL_STATES[code]
        return ("UNKNOWN", f"Unknown state (0x{code:02x})")
        
    @classmethod
    def get_interaction(cls, code: int) -> Tuple[str, str]:
        """Get (system_name, display_label) for an interaction code"""
        return cls.INTERACTIONS.get(code, ("UNKNOWN", f"Unknown interaction (0x{code:02x})"))

    @classmethod
    def get_device_state(cls, code: int) -> Tuple[str, str]:
        """Get (system_name, display_label) for a device state code"""
        return cls.DEVICE_STATES.get(code, ("UNKNOWN", f"Unknown device state (0x{code:02x})"))


