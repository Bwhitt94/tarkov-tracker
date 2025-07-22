#!/usr/bin/env python3
"""
Simple test script to verify the overlay is working correctly.
This will create a test overlay with sample items to ensure the display is functional.
"""

import tkinter as tk
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from overlay import PriceOverlay
import time

def test_overlay():
    """Test the overlay with sample data."""
    print("Creating test overlay...")
    
    # Create the overlay
    overlay = PriceOverlay()
    
    # Show the overlay
    overlay.show()
    
    # Test data - sample items that might be found in inventory
    test_items = [
        {
            'name': 'Graphics Card',
            'price': 285000,
            'trader': 'Mechanic',
            'position': (0, 0)
        },
        {
            'name': 'Bitcoin',
            'price': 445000,
            'trader': 'Therapist',
            'position': (0, 1)
        },
        {
            'name': 'LEDX',
            'price': 890000,
            'trader': 'Therapist',
            'position': (1, 0)
        },
        {
            'name': 'Red Rebel Ice Pick',
            'price': 2800000,
            'trader': 'Jaeger',
            'position': (1, 1)
        }
    ]
    
    print("Updating overlay with test items...")
    overlay.update_items(test_items)
    
    print("Overlay should now show test items.")
    print("Press Ctrl+C to exit the test.")
    
    try:
        # Run the overlay
        overlay.run()
    except KeyboardInterrupt:
        print("\nTest completed.")
        overlay.close()

if __name__ == "__main__":
    test_overlay() 