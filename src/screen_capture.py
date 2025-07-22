import mss
import numpy as np
import cv2
from typing import Optional, Tuple
import threading
import time

# Fallback imports
try:
    from PIL import ImageGrab
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

class ScreenCapture:
    """Handles capturing screenshots of the game screen."""
    
    def __init__(self):
        # We'll create mss instances per thread to avoid threading issues
        self._local = threading.local()
        # We'll store the game window position once we find it
        self.game_window = None
        
    def _get_mss_instance(self):
        """Get or create an mss instance for the current thread."""
        if not hasattr(self._local, 'sct'):
            self._local.sct = mss.mss()
        return self._local.sct
    
    def find_game_window(self) -> Optional[dict]:
        """
        Finds the Escape from Tarkov window.
        Returns the window coordinates or None if not found.
        """
        # For now, we'll use the primary monitor
        # In a full implementation, you'd use win32gui to find the actual game window
        sct = self._get_mss_instance()
        monitor = sct.monitors[1]  # Primary monitor
        
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
            
        # Try mss first
        try:
            # Get thread-local mss instance
            sct = self._get_mss_instance()
            
            # Capture the screen
            screenshot = sct.grab(self.game_window)
            
            # Convert to numpy array (this is how OpenCV likes images)
            img = np.array(screenshot)
            
            # Convert from BGRA to BGR color format
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            
            return img
            
        except Exception as e:
            print(f"MSS screenshot failed: {e}")
            
            # Fallback to PIL if available
            if PIL_AVAILABLE:
                try:
                    print("Trying PIL fallback...")
                    # PIL captures the entire screen, so we need to crop to our region
                    pil_img = ImageGrab.grab()
                    pil_img = pil_img.crop((
                        self.game_window["left"],
                        self.game_window["top"],
                        self.game_window["left"] + self.game_window["width"],
                        self.game_window["top"] + self.game_window["height"]
                    ))
                    
                    # Convert PIL image to numpy array
                    img = np.array(pil_img)
                    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
                    
                    print("PIL fallback successful")
                    return img
                    
                except Exception as pil_error:
                    print(f"PIL fallback also failed: {pil_error}")
            
            return None
    
    def save_screenshot(self, image: np.ndarray, filename: str):
        """Saves a screenshot to file for debugging."""
        cv2.imwrite(filename, image)
        print(f"Screenshot saved to {filename}")
    
    def cleanup(self):
        """Clean up mss instances."""
        if hasattr(self._local, 'sct'):
            self._local.sct.close()
            delattr(self._local, 'sct')