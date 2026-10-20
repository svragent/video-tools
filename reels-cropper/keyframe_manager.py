#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Keyframe Manager - správa keyframů a interpolace
"""

import json
from pathlib import Path

# Auto-disable debug in EXE builds (detects missing console)
import sys
DEBUG = hasattr(sys, 'stdout') and sys.stdout is not None and not getattr(sys, 'frozen', False)

def debug_print(message, level="INFO"):
    """Debug print s úrovněmi"""
    if not DEBUG:
        return
    prefixes = {"INFO": "ℹ️", "KEYFRAME": "🔑", "INTERPOLATE": "📐"}
    prefix = prefixes.get(level, "•")
    print(f"{prefix} {message}")
def debug_keyframe_state(keyframe_manager, current_frame):
    """Vypíše aktuální stav keyframů"""
    if not DEBUG:
        return
    
    print("\n" + "="*60)
    print("🔍 DEBUG: Stav keyframů")
    print("="*60)
    print(f"Aktuální frame: {current_frame}")
    
    keyframes = keyframe_manager.get_all_keyframes()
    if keyframes:
        print(f"Počet keyframů: {len(keyframes)}")
        for frame_num, kf_data in keyframes:
            x, y, mode = kf_data
            marker = " <-- AKTUÁLNÍ" if frame_num == current_frame else ""
            mode_str = f"[{mode.upper()}]"
            print(f"  Frame {frame_num:5d}: X={x:4d}, Y={y:4d} {mode_str}{marker}")
    else:
        print("⚠️  ŽÁDNÉ KEYFRAMY")
    print("="*60 + "\n")


class KeyframeManager:
    """Manages keyframes and interpolation"""
    
    def __init__(self):
        self.keyframes = {}  # {frame_number: (x, y, mode)}  mode="step" nebo "linear"
    
    def add_keyframe(self, frame_num, x, y, mode="step"):
        """Add or update keyframe with interpolation mode"""
        self.keyframes[frame_num] = (x, y, mode)
        
        # 🔍 DEBUG
        if DEBUG:
            debug_print(f"Keyframe přidán: Frame {frame_num} -> X={x}, Y={y}, Mode={mode}", "KEYFRAME")
            debug_keyframe_state(self, frame_num)
        
        return True
    
    def remove_keyframe(self, frame_num):
        """Remove keyframe"""
        if frame_num in self.keyframes:
            del self.keyframes[frame_num]
            return True
        return False
    
    def get_position_at_frame(self, frame_num, default_pos):
        """Get interpolated position for given frame"""
        if not self.keyframes:
            return default_pos
        
        # If exact keyframe exists
        if frame_num in self.keyframes:
            x, y, mode = self.keyframes[frame_num]
            if DEBUG:
                debug_print(f"Frame {frame_num}: Exact keyframe -> X={x}, Y={y}, Mode={mode}", "INTERPOLATE")
            return (x, y)
        
        # Find surrounding keyframes
        frames = sorted(self.keyframes.keys())
        
        # Before first keyframe
        if frame_num < frames[0]:
            x, y, mode = self.keyframes[frames[0]]
            if DEBUG:
                debug_print(f"Frame {frame_num}: Před prvním keyframem ({frames[0]}) -> X={x}, Y={y}", "INTERPOLATE")
            return (x, y)
        
        # After last keyframe
        if frame_num > frames[-1]:
            x, y, mode = self.keyframes[frames[-1]]
            if DEBUG:
                debug_print(f"Frame {frame_num}: Po posledním keyframu ({frames[-1]}) -> X={x}, Y={y}", "INTERPOLATE")
            return (x, y)
        
        # Between two keyframes - MODE určuje PŘÍCHOD do KF2
        for i in range(len(frames) - 1):
            if frames[i] < frame_num < frames[i + 1]:
                f1, f2 = frames[i], frames[i + 1]
                x1, y1, mode1 = self.keyframes[f1]
                x2, y2, mode2 = self.keyframes[f2]
                
                # Mode KF2 určuje chování úseku PŘED ním
                if mode2 == "linear":
                    # LINEAR - interpolace od KF1 k KF2
                    t = (frame_num - f1) / (f2 - f1)
                    x = int(x1 + (x2 - x1) * t)
                    y = int(y1 + (y2 - y1) * t)
                    
                    if DEBUG:
                        debug_print(f"Frame {frame_num}: LINEAR interpolace {f1}→{f2} (t={t:.3f})", "INTERPOLATE")
                        debug_print(f"  KF1: X={x1}, Y={y1} | KF2: X={x2}, Y={y2}", "INTERPOLATE")
                        debug_print(f"  Výsledek: X={x}, Y={y}", "INTERPOLATE")
                else:
                    # STEP - drží hodnotu KF1 až do KF2
                    x, y = x1, y1
                    
                    if DEBUG:
                        debug_print(f"Frame {frame_num}: STEP mode - drží KF {f1} (další: {f2})", "INTERPOLATE")
                        debug_print(f"  Pozice: X={x}, Y={y}", "INTERPOLATE")
                
                return (x, y)
        
        return default_pos

    def get_all_keyframes(self):
        """Return sorted list of keyframes"""
        return sorted(self.keyframes.items())
    
    def clear_all(self):
        """Clear all keyframes"""
        self.keyframes.clear()
    
    def save_to_file(self, filepath):
        """Save keyframes to JSON"""
        try:
            with open(filepath, 'w') as f:
                json.dump(self.keyframes, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving keyframes: {e}")
            return False
    
    def load_from_file(self, filepath):
        """Load keyframes from JSON (zpětná kompatibilita)"""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                # Convert string keys back to int
                self.keyframes = {}
                for k, v in data.items():
                    # Zpětná kompatibilita: pokud je (x, y), přidej mode="step"
                    if len(v) == 2:
                        self.keyframes[int(k)] = (v[0], v[1], "step")
                    else:
                        self.keyframes[int(k)] = tuple(v)
            return True
        except Exception as e:
            print(f"Error loading keyframes: {e}")
            return False


