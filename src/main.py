import time
import threading
from datetime import datetime
import keyboard
import sys
import os
import queue

# Add src directory to path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from screen_capture import ScreenCapture
from inventory_detector import InventoryDetector
from item_recognizer import ItemRecognizer
from price_tracker import PriceTracker
from overlay import PriceOverlay

class TarkovScanner:
    """Main application class that coordinates all components."""
    
    def __init__(self):
        print("Initializing Tarkov Inventory Scanner...")
        
        # Initialize all components
        self.screen_capture = ScreenCapture()
        self.inventory_detector = InventoryDetector()
        self.item_recognizer = ItemRecognizer()
        self.price_tracker = PriceTracker()
        
        # We'll initialize the overlay later in the main thread
        self.overlay = None
        
        # Control flags
        self.scanning = False
        self.running = True
        self.scan_thread = None
        
        # Communication queue between threads
        # This is like a mailbox where the scanning thread can send updates to the GUI thread
        self.update_queue = queue.Queue()
        
        # Scan settings
        self.scan_interval = 1.0  # seconds between scans
        self.confidence_threshold = 0.8
        
        print("Scanner initialized. Press F9 to start/stop scanning.")
        
    def setup_hotkeys(self):
        """Sets up keyboard shortcuts for controlling the scanner."""
        # F9 to toggle scanning
        keyboard.add_hotkey('f9', self.toggle_scanning)
        
        # F10 to show/hide overlay
        keyboard.add_hotkey('f10', self.toggle_overlay)
        
        # ESC to exit
        keyboard.add_hotkey('escape', self.shutdown)
        
    def toggle_scanning(self):
        """Starts or stops the scanning process."""
        if not self.scanning:
            print("Starting scanner...")
            self.scanning = True
            
            # Start the scanning thread if it's not already running
            if not self.scan_thread or not self.scan_thread.is_alive():
                self.scan_thread = threading.Thread(target=self.scan_loop)
                self.scan_thread.daemon = True
                self.scan_thread.start()
                
            # Show the overlay
            if self.overlay:
                self.overlay.show()
        else:
            print("Stopping scanner...")
            self.scanning = False
            
    def toggle_overlay(self):
        """Shows or hides the overlay window."""
        if self.overlay:
            if self.overlay.root.winfo_viewable():
                self.overlay.hide()
            else:
                self.overlay.show()
            
    def scan_loop(self):
        """Main scanning loop that runs in a separate thread."""
        # First, find the game window
        game_window = self.screen_capture.find_game_window()
        if not game_window:
            print("Could not find game window!")
            self.update_queue.put({"error": "Could not find game window"})
            return
            
        while self.scanning and self.running:
            try:
                # Capture the screen
                screenshot = self.screen_capture.capture_screenshot()
                if screenshot is None:
                    print("Failed to capture screenshot")
                    time.sleep(self.scan_interval)
                    continue
                
                # Find inventory region
                inventory_region = self.inventory_detector.find_inventory_region(screenshot)
                if not inventory_region:
                    # Don't spam the console - inventory might just be closed
                    time.sleep(self.scan_interval)
                    continue
                    
                print(f"Found inventory at {inventory_region}")
                
                # Extract inventory slots
                slots = self.inventory_detector.extract_inventory_slots(screenshot, inventory_region)
                
                # Process each slot
                detected_items = []
                for slot in slots:
                    if slot['is_empty']:
                        continue
                        
                    # Try to recognize the item
                    item_name = self.item_recognizer.recognize_item(
                        slot['image'], 
                        self.confidence_threshold
                    )
                    
                    if item_name:
                        # Get price information
                        price_info = self.price_tracker.get_item_price(item_name)
                        if price_info:
                            detected_items.append({
                                'name': item_name,
                                'price': price_info.get('price', 0),
                                'trader': price_info.get('trader', 'Unknown'),
                                'position': slot['position']
                            })
                
                # Send update to the main thread via queue
                if detected_items:
                    print(f"Detected {len(detected_items)} items")
                    self.update_queue.put({"items": detected_items})
                
            except Exception as e:
                print(f"Error in scan loop: {e}")
                self.update_queue.put({"error": str(e)})
                
            # Wait before next scan
            time.sleep(self.scan_interval)
            
        print("Scan loop ended")
    
    def process_updates(self):
        """
        Processes updates from the scanning thread.
        This method runs in the main thread and updates the GUI.
        """
        try:
            # Check for updates without blocking
            while not self.update_queue.empty():
                update = self.update_queue.get_nowait()
                
                if "items" in update:
                    # Update the overlay with new items
                    self.overlay.update_items(update["items"])
                elif "error" in update:
                    # Handle errors
                    print(f"Scanner error: {update['error']}")
                    
        except queue.Empty:
            pass
            
        # Schedule the next update check if we're still running
        if self.running and self.overlay:
            # Check for updates every 100ms
            self.overlay.root.after(100, self.process_updates)
    
    def shutdown(self):
        """Gracefully shuts down the scanner."""
        print("\nShutting down scanner...")
        self.running = False
        self.scanning = False
        
        # Wait for scan thread to finish
        if self.scan_thread and self.scan_thread.is_alive():
            self.scan_thread.join(timeout=2)
            
        # Close the overlay
        if self.overlay:
            self.overlay.close()
            
        print("Scanner shut down. Goodbye!")
        os._exit(0)
        
    def run(self):
        """Starts the scanner application."""
        print("\n" + "="*50)
        print("TARKOV INVENTORY SCANNER")
        print("="*50)
        print("\nControls:")
        print("  F9  - Start/Stop scanning")
        print("  F10 - Show/Hide overlay")
        print("  ESC - Exit application")
        print("\nMake sure Escape from Tarkov is running and")
        print("your inventory is visible before scanning.")
        print("="*50 + "\n")
        
        # Setup hotkeys
        self.setup_hotkeys()
        
        # Create the overlay in the main thread
        self.overlay = PriceOverlay()
        
        # Start processing updates from the scanning thread
        self.process_updates()
        
        # Run the overlay's main loop in the main thread
        # This blocks until the window is closed
        try:
            self.overlay.run()
        except Exception as e:
            print(f"Overlay error: {e}")
        finally:
            self.shutdown()


def main():
    """Entry point of the application."""
    # Check if we're running as administrator (recommended for keyboard hooks)
    try:
        import ctypes
        if not ctypes.windll.shell32.IsUserAnAdmin():
            print("Warning: Running without administrator privileges.")
            print("Some features might not work properly.")
            print("Consider running as administrator for best results.\n")
    except:
        pass  # Not on Windows or can't check
    
    # Create and run the scanner
    scanner = TarkovScanner()
    scanner.run()


if __name__ == "__main__":
    main()