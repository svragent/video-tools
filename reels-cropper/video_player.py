#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Video Player - načítání a zobrazování videa (OPTIMIZED)
"""

import cv2
import numpy as np
from collections import OrderedDict

# Debug flag
import sys
DEBUG_CACHE = False  # ✅ VYPNUTO - zapni pro diagnostiku

class VideoPlayer:
    """Handles video loading and frame rendering (OPTIMIZED)"""
    
    def __init__(self):
        self.cap = None
        self.video_path = None
        self.total_frames = 0
        self.fps = 0
        self.width = 0
        self.height = 0
        self.current_frame = 0
        self.duration = 0
        
        # Crop box dimensions (9:16 aspect ratio)
        self.crop_width = 0
        self.crop_height = 0
        self.crop_x = 0
        self.crop_y = 0
        
        # ✅ OPTIMIZATION 1: Frame cache (LRU)
        self.frame_cache = OrderedDict()
        self.cache_size = 30  # posledních 30 framů
        self.cache_hits = 0
        self.cache_misses = 0
        
        # Frame cache pro dragging (původní)
        self.cached_frame = None
    
    def load_video(self, video_path):
        """Load video file"""
        try:
            if self.cap is not None:
                self.cap.release()
            
            # Clear cache
            self.frame_cache.clear()
            self.cache_hits = 0
            self.cache_misses = 0
            
            self.video_path = video_path
            self.cap = cv2.VideoCapture(video_path)
            
            if not self.cap.isOpened():
                raise Exception("Failed to open video file")
            
            # Get video properties
            self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            self.fps = self.cap.get(cv2.CAP_PROP_FPS)
            self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            self.duration = self.total_frames / self.fps if self.fps > 0 else 0
            
            # Calculate crop box size (9:16)
            self.crop_height = self.height
            self.crop_width = int(self.crop_height * 9 / 16)
            
            # Center by default
            self.crop_x = (self.width - self.crop_width) // 2
            self.crop_y = 0
            
            # Go to first frame
            self.seek_frame(0)
            
            return True
            
        except Exception as e:
            print(f"Error loading video: {e}")
            return False
    
    def seek_frame(self, frame_num):
        """Jump to specific frame (OPTIMIZED - sequential read support)"""
        if self.cap is None:
            return False
        
        frame_num = max(0, min(frame_num, self.total_frames - 1))
        
        # ✅ RADICAL FIX: Pokud už jsme na správném framu, SKIP!
        if self.current_frame == frame_num:
            return True
        
        # ✅ RADICAL FIX: Sequential read (frame+1) = jen cap.read(), BEZ seek!
        if frame_num == self.current_frame + 1:
            # Sequential - update frame number, cap.read() proběhne v get_current_frame()
            self.current_frame = frame_num
            return True
        
        # Non-sequential - musíme seeknout
        self.current_frame = frame_num
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
        return True

    def get_current_frame(self, use_cache=False):
        """Get current frame as numpy array (OPTIMIZED - with cache)"""
        if self.cap is None:
            return None
        
        # ✅ FIX: Vždy zkontroluj cache NEJDŘÍV (i pro use_cache=True)
        if self.current_frame in self.frame_cache:
            self.cache_hits += 1
            if DEBUG_CACHE and self.cache_hits % 10 == 0:
                hit_rate = self.cache_hits / (self.cache_hits + self.cache_misses) * 100
                print(f"📊 Cache stats: {self.cache_hits} hits, {self.cache_misses} misses ({hit_rate:.1f}% hit rate)")
            
            # Move to end (LRU)
            self.frame_cache.move_to_end(self.current_frame)
            frame = self.frame_cache[self.current_frame]
            self.cached_frame = frame  # Update pro use_cache
            return frame
        
        # Cache miss - read from disk
        self.cache_misses += 1
        ret, frame = self.cap.read()
        
        if ret:
            # ✅ OPTIMIZATION: Pouze JEDNA BGR→RGB konverze
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Add to cache
            self.frame_cache[self.current_frame] = frame_rgb
            
            # Limit cache size (LRU eviction)
            if len(self.frame_cache) > self.cache_size:
                self.frame_cache.popitem(last=False)
            
            # Cache pro dragging
            self.cached_frame = frame_rgb
            return frame_rgb
        
        return None
    
    def get_frame_with_overlay(self, crop_x=None, crop_y=None, use_cache=False):
        """Get frame with crop box overlay"""
        frame = self.get_current_frame(use_cache=use_cache)
        if frame is None:
            return None
        
        # Use provided position or default
        x = crop_x if crop_x is not None else self.crop_x
        y = crop_y if crop_y is not None else self.crop_y
        
        # Draw crop box
        overlay = frame.copy()
        
        # Green rectangle
        cv2.rectangle(overlay, 
                     (x, y),
                     (x + self.crop_width, y + self.crop_height),
                     (0, 255, 0), 3)
        
        # Semi-transparent overlay outside crop box
        mask = np.zeros_like(frame, dtype=np.uint8)
        cv2.rectangle(mask, (x, y), 
                     (x + self.crop_width, y + self.crop_height),
                     (255, 255, 255), -1)
        
        darkened = cv2.addWeighted(frame, 0.3, np.zeros_like(frame), 0.7, 0)
        frame = np.where(mask > 0, frame, darkened)
        
        # Add overlay
        frame = cv2.addWeighted(frame, 0.9, overlay, 0.1, 0)
        
        return frame
    
    def get_video_info(self):
        """Return video info dict"""
        return {
            'path': self.video_path,
            'width': self.width,
            'height': self.height,
            'fps': self.fps,
            'total_frames': self.total_frames,
            'duration': self.duration,
            'crop_width': self.crop_width,
            'crop_height': self.crop_height
        }
    
    def release(self):
        """Release video capture"""
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        self.frame_cache.clear()
