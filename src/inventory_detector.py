import cv2
import numpy as np
from typing import List, Tuple, Optional

class InventoryDetector:
    """Detects and extracts the inventory grid from screenshots."""
    
    def __init__(self):
        # Tarkov's standard inventory slot size (you'll need to measure this)
        self.slot_size = (63, 63)
        
        # The color of empty inventory slots (grayish)
        # We'll use this to find the inventory area
        self.empty_slot_color_range = {
            'lower': np.array([40, 40, 40]),
            'upper': np.array([80, 80, 80])
        }
        
    def find_inventory_region(self, screenshot: np.ndarray) -> Optional[Tuple[int, int, int, int]]:
        """
        Finds the inventory area in the screenshot.
        Returns (x, y, width, height) or None if not found.
        """
        # Convert to grayscale for easier processing
        gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
        
        # Look for the characteristic pattern of the inventory grid
        # This is simplified - in reality, you'd use template matching
        # with an image of the inventory border
        
        # Apply threshold to find dark regions (inventory background)
        _, thresh = cv2.threshold(gray, 50, 255, cv2.THRESH_BINARY_INV)
        
        # Find contours (connected regions)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Look for large rectangular regions
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            
            # Check if this could be the inventory
            # Inventory is typically a large rectangle
            if w > 400 and h > 400:  # Minimum expected size
                # Verify it's somewhat square-ish (inventory proportions)
                aspect_ratio = w / h
                if 0.8 < aspect_ratio < 1.5:
                    print(f"Found potential inventory at ({x}, {y}), size: {w}x{h}")
                    return (x, y, w, h)
        
        return None
    
    def extract_inventory_slots(self, screenshot: np.ndarray, 
                              inventory_region: Tuple[int, int, int, int]) -> List[dict]:
        """
        Extracts individual inventory slots from the inventory region.
        Returns a list of slot information including position and image.
        """
        x, y, w, h = inventory_region
        slots = []
        
        # Calculate how many slots fit in the inventory
        cols = w // self.slot_size[0]
        rows = h // self.slot_size[1]
        
        print(f"Extracting {rows}x{cols} grid of slots")
        
        for row in range(rows):
            for col in range(cols):
                # Calculate this slot's position
                slot_x = x + (col * self.slot_size[0])
                slot_y = y + (row * self.slot_size[1])
                
                # Extract the slot image
                slot_image = screenshot[
                    slot_y:slot_y + self.slot_size[1],
                    slot_x:slot_x + self.slot_size[0]
                ]
                
                # Store slot information
                slot_info = {
                    'position': (row, col),
                    'coordinates': (slot_x, slot_y),
                    'image': slot_image,
                    'is_empty': self.is_slot_empty(slot_image)
                }
                
                slots.append(slot_info)
        
        return slots
    
    def is_slot_empty(self, slot_image: np.ndarray) -> bool:
        """
        Determines if a slot is empty by checking its color.
        Empty slots have a characteristic gray color.
        """
        # Calculate the average color of the slot
        avg_color = np.mean(slot_image, axis=(0, 1))
        
        # Check if it matches empty slot color
        # Empty slots are usually uniform gray
        color_variance = np.var(slot_image, axis=(0, 1))
        
        # Low variance + gray color = probably empty
        is_gray = all(40 < c < 80 for c in avg_color)
        is_uniform = all(v < 100 for v in color_variance)
        
        return is_gray and is_uniform