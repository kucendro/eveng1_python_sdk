"""
Logging configuration for G1 SDK
"""

import os
import logging
import traceback
from rich.console import Console

def setup_logger(config):
    """Configure logging for the SDK"""
    logger = logging.getLogger("G1Connector")
    logger.setLevel(logging.DEBUG)
    
    # Clear existing handlers
    logger.handlers = []
    
    # Create formatters with file/line information
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s')
    console_formatter = logging.Formatter('%(message)s')
    
    # File handler - logs everything
    if config.log_file:
        os.makedirs(os.path.dirname(config.log_file), exist_ok=True)
        mode = 'w' if getattr(config, 'reset_logs', True) else 'a'
        file_handler = logging.FileHandler(config.log_file, mode=mode)
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(logging.DEBUG)
        logger.addHandler(file_handler)
    
    if config.console_log:
        console = Console()
        
        def console_handler(record):
            try:
                msg = record.getMessage()
                if record.exc_info:
                    msg += '\n' + ''.join(traceback.format_exception(*record.exc_info))
                
                if record.levelno == logging.ERROR:
                    console.print(f"[red]{msg}[/red]")
                elif hasattr(record, 'success'):
                    console.print(f"[green]{msg}[/green]")
                elif hasattr(record, 'user_message'):
                    console.print(f"[yellow]{msg}[/yellow]")
                else:
                    console.print(msg)
            except Exception as e:
                console.print(f"Logging error: {e}")
        
        handler = logging.Handler()
        handler.setLevel(logging.INFO)
        handler.emit = console_handler
        logger.addHandler(handler)
    
    # Add convenience methods for different message types
    def error(self, message: str, exc_info=True):
        """Log error with traceback"""
        self.error(message, exc_info=exc_info)
    
    def user(self, message: str):
        """Log user-friendly message in yellow"""
        record = self.makeRecord(
            self.name, logging.INFO, "", 0, message, (), None
        )
        record.user_message = True
        self.handle(record)
    
    def success(self, message: str):
        """Log success message in green"""
        record = self.makeRecord(
            self.name, logging.INFO, "", 0, message, (), None
        )
        record.success = True
        self.handle(record)
    
    logger.user = user.__get__(logger)
    logger.success = success.__get__(logger)
    
    return logger

def user_guidance(logger, message: str):
    """Display formatted message to user and log it"""
    console = Console()
    console.print(message)
    # Strip rich formatting for log file
    plain_message = message.replace("[yellow]", "").replace("[/yellow]", "")
    plain_message = plain_message.replace("[green]", "").replace("[/green]", "")
    plain_message = plain_message.replace("[red]", "").replace("[/red]", "")
    logger.info(plain_message)  # Use INFO level for user guidance 