import os
import subprocess
import sys

def create_icon():
    """Create a simple EFT-themed icon using PIL."""
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # Create a 256x256 icon
        size = 256
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Draw a simple EFT-style icon (black background with white text)
        draw.rectangle([0, 0, size-1, size-1], fill=(20, 20, 20, 255))
        draw.rectangle([10, 10, size-11, size-11], outline=(255, 255, 255, 255), width=3)
        
        # Add text "EFT" in the center
        try:
            # Try to use a system font
            font = ImageFont.truetype("arial.ttf", 60)
        except:
            # Fallback to default font
            font = ImageFont.load_default()
        
        text = "EFT"
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (size - text_width) // 2
        y = (size - text_height) // 2
        draw.text((x, y), text, fill=(255, 255, 255, 255), font=font)
        
        # Save as ICO
        img.save("icon.ico", format='ICO')
        print("Created icon.ico")
        return True
    except Exception as e:
        print(f"Could not create icon: {e}")
        return False

def build_executable():
    """Build the executable using PyInstaller."""
    try:
        # Create icon if it doesn't exist
        if not os.path.exists("icon.ico"):
            create_icon()
        
        # Build command
        cmd = [
            "pyinstaller",
            "--onefile",
            "--windowed",
            "--name=TarkovItemTracker",
            "--icon=icon.ico" if os.path.exists("icon.ico") else "",
            "gui.py"
        ]
        
        # Remove empty arguments
        cmd = [arg for arg in cmd if arg]
        
        print("Building executable...")
        print(f"Command: {' '.join(cmd)}")
        
        # Run PyInstaller
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("Build successful!")
            if os.path.exists("dist/TarkovItemTracker.exe"):
                print("Executable created: dist/TarkovItemTracker.exe")
                return True
            else:
                print("Executable not found in dist/")
                return False
        else:
            print("Build failed!")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False
            
    except Exception as e:
        print(f"Error building executable: {e}")
        return False

if __name__ == "__main__":
    success = build_executable()
    if success:
        print("\n✅ Executable built successfully!")
        print("You can find it in the 'dist' folder.")
    else:
        print("\n❌ Build failed!")
        sys.exit(1) 