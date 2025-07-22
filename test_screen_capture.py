#!/usr/bin/env python3
"""
Simple test script to verify screen capture is working correctly.
This will test the screen capture functionality without running the full scanner.
"""

import sys
import os
import time

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from screen_capture import ScreenCapture

def test_screen_capture():
    """Test the screen capture functionality."""
    print("Testing screen capture...")
    
    # Create screen capture instance
    screen_capture = ScreenCapture()
    
    try:
        # Find game window (monitor)
        print("Finding game window...")
        game_window = screen_capture.find_game_window()
        
        if game_window:
            print(f"Found game window: {game_window}")
        else:
            print("Could not find game window!")
            return
        
        # Test screenshot capture
        print("Capturing screenshot...")
        screenshot = screen_capture.capture_screenshot()
        
        if screenshot is not None:
            print(f"Screenshot captured successfully! Size: {screenshot.shape}")
            
            # Save the screenshot for inspection
            screen_capture.save_screenshot(screenshot, "test_screenshot.png")
            print("Test screenshot saved to test_screenshot.png")
            
            # Test multiple captures to ensure threading works
            print("Testing multiple captures...")
            for i in range(5):
                screenshot = screen_capture.capture_screenshot()
                if screenshot is not None:
                    print(f"Capture {i+1} successful")
                else:
                    print(f"Capture {i+1} failed")
                time.sleep(0.5)
            
        else:
            print("Failed to capture screenshot!")
            
    except Exception as e:
        print(f"Error during screen capture test: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up
        screen_capture.cleanup()
        print("Screen capture test completed.")

if __name__ == "__main__":
    test_screen_capture() 