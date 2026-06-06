"""
Rehoboam Comprehensive Logging Configuration
==========================================

This module provides a standardized logging configuration for the entire Rehoboam system,
including structured logging, error handling, and audit trails.

Features:
- Structured JSON logging for better parsing and analysis
- Different log levels for different components
- Error context enrichment
- Performance monitoring
- Security audit logging
- Log rotation and retention
"""

import logging
import logging.handlers
import json
import os
import sys
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import traceback
import asyncio
from functools import wraps

# Log levels
LOG_LEVELS = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}

# Default configuration
DEFAULT_CONFIG = {
    'log_level': os.getenv('LOG_LEVEL', 'INFO'),
    'log_format': 'json',  # 'json' or 'text'
    'log_file': os.getenv('LOG_FILE', './logs/rehoboam.log'),
    'max_file_size': 10 * 1024 * 1024,  # 10MB
    'backup_count': 5,
    'enable_console': True,
    'enable_file': True,
    'audit_log_file': os.getenv('AUDIT_LOG_FILE', './logs/rehoboam_audit.log')
}

class StructuredLogger:
    """
    A structured logger that provides consistent logging across the Rehoboam system.
    """
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        self.name = name
        self.config = config or DEFAULT_CONFIG.copy()
        self.logger = logging.getLogger(name)
        self.logger.setLevel(LOG_LEVELS.get(self.config['log_level'], logging.INFO))
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Set up handlers
        self._setup_handlers()
        
    def _setup_handlers(self):
        """Set up logging handlers based on configuration."""
        formatter = self._get_formatter()
        
        # Console handler
        if self.config['enable_console']:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
        # File handler with rotation
        if self.config['enable_file']:
            # Ensure log directory exists
            log_dir = os.path.dirname(self.config['log_file'])
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)
                
            file_handler = logging.handlers.RotatingFileHandler(
                self.config['log_file'],
                maxBytes=self.config['max_file_size'],
                backupCount=self.config['backup_count']
            )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def _get_formatter(self):
        """Get appropriate formatter based on configuration."""
        if self.config['log_format'] == 'json':
            return JsonFormatter()
        else:
            return logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
    
    def _log(self, level: int, message: str, **kwargs):
        """Internal logging method with structured data."""
        extra_data = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'service': self.name,
            **kwargs
        }
        
        # Add stack trace for error levels
        if level >= logging.ERROR and 'stack_trace' not in extra_data:
            extra_data['stack_trace'] = traceback.format_exc() if sys.exc_info()[0] else None
        
        self.logger.log(level, message, extra={'structured_data': extra_data})
    
    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self._log(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message."""
        self._log(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self._log(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message."""
        self._log(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message."""
        self._log(logging.CRITICAL, message, **kwargs)
    
    def audit(self, action: str, user: Optional[str] = None, resource: Optional[str] = None,
              success: bool = True, details: Optional[Dict[str, Any]] = None):
        """Log security audit event."""
        audit_data = {
            'action': action,
            'user': user,
            'resource': resource,
            'success': success,
            'details': details or {},
            'audit_timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        # Log to audit file
        if self.config['audit_log_file']:
            try:
                audit_dir = os.path.dirname(self.config['audit_log_file'])
                if audit_dir and not os.path.exists(audit_dir):
                    os.makedirs(audit_dir, exist_ok=True)
                    
                with open(self.config['audit_log_file'], 'a') as f:
                    f.write(json.dumps(audit_data) + '\n')
            except Exception as e:
                self.error(f"Failed to write audit log: {e}")

class JsonFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record):
        """Format log record as JSON."""
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }
        
        # Add structured data from extra fields
        if hasattr(record, '__dict__'):
            # Check for structured_data in the record's extra attributes
            if 'structured_data' in record.__dict__:
                structured_data = record.__dict__['structured_data']
                if isinstance(structured_data, dict):
                    log_entry.update(structured_data)
            
            # Add any other extra fields that aren't standard
            for key, value in record.__dict__.items():
                if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                              'filename', 'module', 'lineno', 'funcName', 'created', 
                              'msecs', 'relativeCreated', 'thread', 'threadName', 
                              'processName', 'process', 'getMessage', 'exc_info', 
                              'exc_text', 'stack_info', 'structured_data']:
                    log_entry[key] = value
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        elif record.levelno >= logging.ERROR and hasattr(record, '__dict__'):
            # Try to get stack trace from record if not in exc_info
            if 'stack_trace' in record.__dict__ and record.__dict__['stack_trace']:
                log_entry['stack_trace'] = record.__dict__['stack_trace']
        
        return json.dumps(log_entry, default=str)

# Global logger instances
_system_logger = None
_audit_logger = None

def get_logger(name: Optional[str] = None) -> StructuredLogger:
    """
    Get a structured logger instance.
    
    Args:
        name: Logger name (typically __name__ from calling module)
        
    Returns:
        StructuredLogger instance
    """
    global _system_logger
    if _system_logger is None:
        _system_logger = StructuredLogger('rehoboam.system')
    return _system_logger if name is None else StructuredLogger(name)

def get_audit_logger() -> StructuredLogger:
    """
    Get the audit logger instance.
    
    Returns:
        StructuredLogger instance for audit logging
    """
    global _audit_logger
    if _audit_logger is None:
        audit_config = DEFAULT_CONFIG.copy()
        audit_config['log_file'] = audit_config['audit_log_file']
        _audit_logger = StructuredLogger('rehoboam.audit', audit_config)
    return _audit_logger

def log_execution_time(logger: StructuredLogger):
    """
    Decorator to log function execution time.
    
    Args:
        logger: Logger instance to use for logging
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = datetime.now(timezone.utc)
            try:
                result = await func(*args, **kwargs)
                execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
                logger.info(
                    f"Executed {func.__name__}",
                    function=func.__name__,
                    execution_time=execution_time,
                    status="success"
                )
                return result
            except Exception as e:
                execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
                logger.error(
                    f"Failed to execute {func.__name__}: {str(e)}",
                    function=func.__name__,
                    execution_time=execution_time,
                    status="error",
                    error=str(e)
                )
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = datetime.now(timezone.utc)
            try:
                result = func(*args, **kwargs)
                execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
                logger.info(
                    f"Executed {func.__name__}",
                    function=func.__name__,
                    execution_time=execution_time,
                    status="success"
                )
                return result
            except Exception as e:
                execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
                logger.error(
                    f"Failed to execute {func.__name__}: {str(e)}",
                    function=func.__name__,
                    execution_time=execution_time,
                    status="error",
                    error=str(e)
                )
                raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator

def handle_exceptions(logger: StructuredLogger, reraise: bool = True):
    """
    Decorator to handle exceptions with comprehensive logging.
    
    Args:
        logger: Logger instance to use for logging
        reraise: Whether to re-raise the exception after logging
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.error(
                    f"Exception in {func.__name__}: {str(e)}",
                    function=func.__name__,
                    error_type=type(e).__name__,
                    error_message=str(e),
                    args=str(args)[:200],  # Limit args length
                    kwargs=str(kwargs)[:200]  # Limit kwargs length
                )
                if reraise:
                    raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(
                    f"Exception in {func.__name__}: {str(e)}",
                    function=func.__name__,
                    error_type=type(e).__name__,
                    error_message=str(e),
                    args=str(args)[:200],  # Limit args length
                    kwargs=str(kwargs)[:200]  # Limit kwargs length
                )
                if reraise:
                    raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator

# Compatibility function for legacy code
def setup_logging(name: Optional[str] = None) -> StructuredLogger:
    """
    Compatibility function for legacy code.
    Returns a logger instance.

    Args:
        name: Optional logger name

    Returns:
        StructuredLogger instance
    """
    return get_logger(name)

# Initialize default loggers
def initialize_logging():
    """Initialize the logging system with default configuration."""
    global _system_logger, _audit_logger

    # System logger
    _system_logger = StructuredLogger('rehoboam.system')

    # Audit logger
    audit_config = DEFAULT_CONFIG.copy()
    audit_config['log_file'] = audit_config['audit_log_file']
    _audit_logger = StructuredLogger('rehoboam.audit', audit_config)

    _system_logger.info("Logging system initialized", config=DEFAULT_CONFIG)

# Initialize on module import
initialize_logging()