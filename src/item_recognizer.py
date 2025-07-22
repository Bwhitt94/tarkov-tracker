import cv2
import numpy as np
import os
from typing import Optional, Dict, List
import json

class ItemRecognizer:
    """Recognizes Tarkov items from inventory slot images."""
    
    def __init__(self, templates_path: str = "data/items"):
        self.templates_path = templates_path
        self.templates = {}
        self.item_data = {}
        self.load_templates()
        
    def load_templates(self):
        """
        Loads item icon templates from the data folder.
        Each item should have a .png icon and a .json data file.
        """
        if not os.path.exists(self.templates_path):
            print(f"Creating templates directory at {self.templates_path}")
            os.makedirs(self.templates_path)
            return
            
        for filename in os.listdir(self.templates_path):
            if filename.endswith('.png'):
                item_name = filename[:-4]  # Remove .png extension
                
                # Load the icon image
                icon_path = os.path.join(self.templates_path, filename)
                template = cv2.imread(icon_path)
                
                if template is not None:
                    self.templates[item_name] = template
                    
                    # Load corresponding data file if it exists
                    data_path = os.path.join(self.templates_path, f"{item_name}.json")
                    if os.path.exists(data_path):
                        with open(data_path, 'r') as f:
                            self.item_data[item_name] = json.load(f)
                    
                    print(f"Loaded template for {item_name}")
        
        print(f"Loaded {len(self.templates)} item templates")
    
    def recognize_item(self, slot_image: np.ndarray, confidence_threshold: float = 0.8) -> Optional[str]:
        """
        Attempts to recognize an item in the given slot image.
        Returns the item name or None if no match found.
        """
        if slot_image is None or slot_image.size == 0:
            return None
            
        best_match = None
        best_score = 0
        
        # Try to match against each template
        for item_name, template in self.templates.items():
            # Ensure template and slot image are the same size
            if template.shape[:2] != slot_image.shape[:2]:
                template_resized = cv2.resize(template, 
                                            (slot_image.shape[1], slot_image.shape[0]))
            else:
                template_resized = template
            
            # Perform template matching
            result = cv2.matchTemplate(slot_image, template_resized, cv2.TM_CCOEFF_NORMED)
            score = np.max(result)
            
            # Keep track of the best match
            if score > best_score:
                best_score = score
                best_match = item_name
        
        # Only return a match if we're confident enough
        if best_score >= confidence_threshold:
            print(f"Recognized {best_match} with confidence {best_score:.2f}")
            return best_match
        
        return None
    
    def get_item_info(self, item_name: str) -> Dict:
        """
        Gets stored information about an item.
        Returns item data or empty dict if not found.
        """
        return self.item_data.get(item_name, {})