import os
import sys
import django
import pytest

# Add the project root to Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hotel_hms.settings')

# Setup Django
django.setup()

# Register pytest-django plugin
pytest_plugins = ['pytest_django']
