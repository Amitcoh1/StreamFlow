#!/usr/bin/env python3
"""Debug script to test configuration loading"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Print environment variables
print("Environment variables:")
for key, value in os.environ.items():
    if any(x in key for x in ['JWT', 'DATABASE', 'RABBITMQ', 'REDIS']):
        print(f"{key}={value}")

# Test SecuritySettings directly
from shared.config import SecuritySettings

try:
    security = SecuritySettings()
    print(f"SecuritySettings loaded successfully: {security}")
except Exception as e:
    print(f"Error loading SecuritySettings: {e}")
    
# Test main Settings
from shared.config import Settings

try:
    settings = Settings()
    print(f"Settings loaded successfully: {settings}")
except Exception as e:
    print(f"Error loading Settings: {e}")
