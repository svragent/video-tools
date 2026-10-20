#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scene Detector - automatická detekce střihů ve videu
Používá PySceneDetect pro pixel-based detekci
"""

import cv2
import numpy as np
from pathlib import Path

DEBUG = True

def debug_print(message):
    """Debug print - snadno vypnutelný"""
    if DEBUG:
        print(f"🔍 [SceneDetect] {message}")


class SceneDetector:
    """Detekuje střihy ve videu pomocí analýzy změn mezi framy"""
    
    def __init__(self):
        self.scenes = []
        
    def detect_scenes(self, video_path, threshold=27.0, min_scene_len=15, progress_callback=None):
        """
        Detekuje střihy ve videu
        
        Args:
            video_path: Cesta k video souboru
            threshold: Citlivost detekce (0-100, výchozí 27)
                      - Nižší = citlivější (více false positives)
                      - Vyšší = méně citlivé (může přehlédnout jemné střihy)
            min_scene_len: Minimální délka scény ve framech (výchozí 15)
            progress_callback: Funkce pro update progress (volitelné)
            
        Returns:
            List frame čísel kde jsou střihy [(frame_num, score), ...]
        """
        debug_print(f"🎬 Začínám detekci střihů: {Path(video_path).name}")
        debug_print(f"   Threshold: {threshold}, Min scene length: {min_scene_len}")
        
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            raise Exception(f"Nelze otevřít video: {video_path}")
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        debug_print(f"   Total frames: {total_frames}, FPS: {fps}")
        
        scenes = []
        prev_frame = None
        frame_num = 0
        last_cut_frame = -min_scene_len
        
        # Progress tracking
        progress_step = max(1, total_frames // 100)
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Convert to grayscale for comparison
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            if prev_frame is not None:
                # Počítáme rozdíl mezi framy (mean absolute difference)
                diff = cv2.absdiff(prev_frame, gray)
                score = np.mean(diff)
                
                # Detekce střihu pokud:
                # 1) Score překročí threshold
                # 2) Od posledního střihu uplynulo min_scene_len framů
                if score > threshold and (frame_num - last_cut_frame) >= min_scene_len:
                    scenes.append((frame_num, score))
                    last_cut_frame = frame_num
                    
                    debug_print(f"   ✂️ Střih detekován: Frame {frame_num} (score: {score:.2f})")
            
            prev_frame = gray
            frame_num += 1
            
            # Progress callback
            if progress_callback and frame_num % progress_step == 0:
                progress = (frame_num / total_frames) * 100
                progress_callback(progress)
        
        cap.release()
        
        debug_print(f"✅ Detekce dokončena: Nalezeno {len(scenes)} střihů")
        
        self.scenes = scenes
        return scenes
    
    def get_scene_list(self):
        """Vrátí seznam detekovaných střihů"""
        return self.scenes


def quick_detect_scenes(video_path, threshold=27.0, min_scene_len=15):
    """
    Jednoduchá wrapper funkce pro rychlou detekci
    
    Args:
        video_path: Cesta k videu
        threshold: Citlivost (0-100)
        min_scene_len: Min délka scény ve framech
        
    Returns:
        List frame čísel střihů
    """
    detector = SceneDetector()
    scenes = detector.detect_scenes(video_path, threshold, min_scene_len)
    return [frame_num for frame_num, score in scenes]


# Test funkce
if __name__ == "__main__":
    print("🎬 Scene Detector Test")
    print("=" * 60)
    
    # Test na ukázkovém videu
    test_video = "test_video.mp4"
    
    if Path(test_video).exists():
        detector = SceneDetector()
        scenes = detector.detect_scenes(test_video, threshold=27.0)
        
        print(f"\n✅ Nalezeno {len(scenes)} střihů:")
        for frame_num, score in scenes:
            print(f"   Frame {frame_num:5d} | Score: {score:.2f}")
    else:
        print(f"❌ Test video nenalezeno: {test_video}")
        print("   Pro test vytvoř video nebo použij existující soubor")
