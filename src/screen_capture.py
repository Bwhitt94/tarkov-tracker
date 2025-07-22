import mss
import numpy as np
import cv2
from typing import Optional, Tuple

class ScreenCapture:
    """Handles capturing screenshots of the game screen."""
    
    def __init__(self):
        # mss is our screenshot tool
        self.sct = mss.mss()
        # We'll store the game window position once we find it
        self.game_window = None
        
    def find_game_window(self) -> Optional[dict]:
        """
        Finds the Escape from Tarkov window.
        Returns the window coordinates or None if not found.
        """
        # For now, we'll use the primary monitor
        # In a full implementation, you'd use win32gui to find the actual game window
        monitor = self.sct.monitors[1]  # Primary monitor
        
        # Store the window coordinates
        self.game_window = {
            "top": monitor["top"],
            "left": monitor["left"],
            "width": monitor["width"],
            "height": monitor["height"]
        }
        
        print(f"Using monitor: {monitor['width']}x{monitor['height']}")
        return self.game_window
    
    def capture_screenshot(self) -> Optional[np.ndarray]:
        """
        Captures a screenshot of the game window.
        Returns the image as a numpy array or None if failed.
        """
        if not self.game_window:
            print("Game window not found. Run find_game_window first.")
            return None
            
        try:
            # Capture the screen
            screenshot = self.sct.grab(self.game_window)
            
            # Convert to numpy array (this is how OpenCV likes images)
            img = np.array(screenshot)
            
            # Convert from BGRA to BGR color format
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            
            return img
            
        except Exception as e:
            print(f"Error capturing screenshot: {e}")
            return None
    
    def save_screenshot(self, image: np.ndarray, filename: str):
        """Saves a screenshot to file for debugging."""
        cv2.imwrite(filename, image)
        print(f"Screenshot saved to {filename}")