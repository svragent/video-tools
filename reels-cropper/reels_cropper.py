#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reels Cropper v1.0 - Video Crop Tool for Social Media by Jan Cervenak 2026 (9:16)
Creates vertical videos from horizontal footage with keyframe animation

Requirements:
    pip install opencv-python numpy pillow

Usage:
    python reels_cropper.py
"""

import tkinter as tk
import sys

from reels_gui import ReelsCropperGUI

def main():
    """Main entry point"""
    # Check dependencies
    missing_deps = []
    
    try:
        import cv2
    except ImportError:
        missing_deps.append("opencv-python")
    
    try:
        import numpy
    except ImportError:
        missing_deps.append("numpy")
    
    try:
        from PIL import Image
    except ImportError:
        missing_deps.append("pillow")
    
    if missing_deps:
        print("❌ Missing dependencies!")
        print("\nPlease install:")
        print(f"   pip install {' '.join(missing_deps)}")
        print("\nNote: FFmpeg must also be installed separately")
        sys.exit(1)
    
    # Create GUI
    root = tk.Tk()
    app = ReelsCropperGUI(root)
    
    # Center window
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    print("✅ Reels Cropper v1.0 started!")
    print("\n📖 Quick Guide:")
    print("   1. Load Video - Select your horizontal video")
    print("   2. Drag green box - Position the 9:16 crop area")
    print("   3. Add Keyframe - Save position at current time")
    print("   4. Repeat steps 2-3 to create animation")
    print("   5. Export MP4 - Render final vertical video")
    print("\n💡 Tip: Use timeline slider to navigate through video")
    print("🎬 Crop box will animate smoothly between keyframes!\n")
    
    root.mainloop()

if __name__ == "__main__":
    main()
