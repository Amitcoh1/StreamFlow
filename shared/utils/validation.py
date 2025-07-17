"""Validation utilities for StreamFlow."""

import re
from typing import Any, Dict, List, Optional
from datetime import datetime

from .logging import get_logger

logger = get_logger(__name__)


def validate_event_data(data: Dict[str, Any]) -> bool:
    """Validate event data structure and content."""
    try:
        # Check if data is a dictionary
        if not isinstance(data, dict):
            return False
        
        # Check for dangerous keys that could cause issues
        dangerous_keys = ['__class__', '__module__', 'eval', 'exec', 'import']
        if any(key in data for key in dangerous_keys):
            logger.warning("Event data contains dangerous keys", data=data)
            return False
        
        # Validate data size (prevent oversized payloads)
        if len(str(data)) > 100000:  # 100KB limit
            logger.warning("Event data exceeds size limit", size=len(str(data)))
            return False
        
        return True
        
    except Exception as e:
        logger.error("Error validating event data", error=str(e))
        return False


def validate_alert_condition(condition: str) -> bool:
    """Validate alert condition syntax."""
    try:
        if not condition or not condition.strip():
            return False
        
        # Check for basic operators and patterns
        allowed_operators = [
            '>', '<', '>=', '<=', '==', '!=', 
            'and', 'or', 'not', '(', ')', 
            '+', '-', '*', '/', '%'
        ]
        
        allowed_functions = [
            'abs', 'min', 'max', 'sum', 'avg', 'count',
            'rate', 'increase', 'delta'
        ]
        
        # Remove allowed operators and functions
        test_condition = condition.lower()
        for op in allowed_operators:
            test_condition = test_condition.replace(op, ' ')
        
        for func in allowed_functions:
            test_condition = re.sub(rf'{func}\s*\(', ' ', test_condition)
        
        # Check remaining tokens (should be identifiers, numbers, or whitespace)
        tokens = test_condition.split()
        for token in tokens:
            if token and not (token.isidentifier() or is_number(token)):
                logger.warning("Invalid token in alert condition", token=token)
                return False
        
        return True
        
    except Exception as e:
        logger.error("Error validating alert condition", error=str(e))
        return False


def is_number(value: str) -> bool:
    """Check if a string represents a valid number."""
    try:
        float(value)
        return True
    except ValueError:
        return False


def validate_email(email: str) -> bool:
    """Validate email address format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_username(username: str) -> bool:
    """Validate username format."""
    # Username should be 3-50 characters, alphanumeric with underscores and hyphens
    pattern = r'^[a-zA-Z0-9_-]{3,50}$'
    return bool(re.match(pattern, username))


def validate_metric_name(name: str) -> bool:
    """Validate metric name follows Prometheus naming conventions."""
    # Metric names should start with letter or underscore, contain only alphanumeric, underscore, colon
    pattern = r'^[a-zA-Z_:][a-zA-Z0-9_:]*$'
    return bool(re.match(pattern, name))


def validate_time_window(window: str) -> bool:
    """Validate time window format (e.g., '5m', '1h', '2d')."""
    pattern = r'^\d+[smhd]$'
    return bool(re.match(pattern, window))


def validate_json_structure(data: Any, schema: Dict[str, Any]) -> bool:
    """Validate JSON data against a simple schema."""
    try:
        if not isinstance(data, dict):
            return False
        
        # Check required fields
        required_fields = schema.get('required', [])
        for field in required_fields:
            if field not in data:
                logger.warning("Missing required field", field=field)
                return False
        
        # Check field types
        field_types = schema.get('types', {})
        for field, expected_type in field_types.items():
            if field in data:
                if expected_type == 'string' and not isinstance(data[field], str):
                    return False
                elif expected_type == 'number' and not isinstance(data[field], (int, float)):
                    return False
                elif expected_type == 'boolean' and not isinstance(data[field], bool):
                    return False
                elif expected_type == 'array' and not isinstance(data[field], list):
                    return False
                elif expected_type == 'object' and not isinstance(data[field], dict):
                    return False
        
        return True
        
    except Exception as e:
        logger.error("Error validating JSON structure", error=str(e))
        return False


def sanitize_string(value: str, max_length: int = 1000) -> str:
    """Sanitize string input by removing dangerous characters."""
    if not isinstance(value, str):
        return str(value)
    
    # Remove null bytes and control characters
    sanitized = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', value)
    
    # Trim to maximum length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized.strip()


def validate_ip_address(ip: str) -> bool:
    """Validate IP address format (IPv4 or IPv6)."""
    import ipaddress
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False


def validate_url(url: str) -> bool:
    """Validate URL format."""
    pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    return bool(re.match(pattern, url))


def validate_phone_number(phone: str) -> bool:
    """Validate phone number format."""
    # Simple international phone number validation
    pattern = r'^\+?[1-9]\d{1,14}$'
    cleaned_phone = re.sub(r'[\s\-\(\)]', '', phone)
    return bool(re.match(pattern, cleaned_phone))


def validate_password_strength(password: str) -> Dict[str, Any]:
    """Validate password strength and return detailed feedback."""
    result = {
        'is_valid': True,
        'errors': [],
        'score': 0,
        'suggestions': []
    }
    
    if len(password) < 8:
        result['is_valid'] = False
        result['errors'].append('Password must be at least 8 characters long')
    else:
        result['score'] += 1
    
    if not re.search(r'[a-z]', password):
        result['is_valid'] = False
        result['errors'].append('Password must contain at least one lowercase letter')
    else:
        result['score'] += 1
    
    if not re.search(r'[A-Z]', password):
        result['is_valid'] = False
        result['errors'].append('Password must contain at least one uppercase letter')
    else:
        result['score'] += 1
    
    if not re.search(r'\d', password):
        result['is_valid'] = False
        result['errors'].append('Password must contain at least one digit')
    else:
        result['score'] += 1
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        result['suggestions'].append('Consider adding special characters for stronger security')
    else:
        result['score'] += 1
    
    if len(password) >= 12:
        result['score'] += 1
    
    # Common password check
    common_passwords = [
        'password', '123456', 'password123', 'admin', 'qwerty',
        'letmein', 'welcome', 'monkey', '123456789', 'password1'
    ]
    
    if password.lower() in common_passwords:
        result['is_valid'] = False
        result['errors'].append('Password is too common')
        result['score'] = 0
    
    return result


def validate_rate_limit(requests: int, window_seconds: int) -> bool:
    """Validate rate limit configuration."""
    return (
        isinstance(requests, int) and 
        isinstance(window_seconds, int) and
        requests > 0 and 
        window_seconds > 0 and
        requests <= 10000 and  # Reasonable upper limit
        window_seconds <= 3600  # Max 1 hour window
    )


def validate_cron_expression(expression: str) -> bool:
    """Validate cron expression format."""
    try:
        # Basic cron validation (5 or 6 fields)
        fields = expression.split()
        if len(fields) not in [5, 6]:
            return False
        
        # Each field should contain valid characters
        valid_chars = set('0123456789,-*/')
        for field in fields:
            if not all(c in valid_chars or c.isalpha() for c in field):
                return False
        
        return True
        
    except Exception:
        return False