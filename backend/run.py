#!/usr/bin/env python3
"""Entry point for the Flask application."""
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app

config_name = os.environ.get('FLASK_ENV', 'development')
app = create_app(config_name)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = config_name == 'development'
    print(f"\n{'='*60}")
    print(f"  Automated Attendance System for Rural Schools")
    print(f"  Running on http://localhost:{port}")
    print(f"  Environment: {config_name}")
    print(f"{'='*60}\n")
    app.run(host='0.0.0.0', port=port, debug=debug)
