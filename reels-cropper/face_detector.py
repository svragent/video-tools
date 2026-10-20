#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Face Detector - detekce obličeje pro automatické centrování
Podporuje Haar Cascade (rychlé) a DNN (přesnější) s automatickým fallbackem
"""

import cv2
import numpy as np
from pathlib import Path

# Auto-disable debug in EXE builds (detects missing console)
import sys
DEBUG = hasattr(sys, 'stdout') and sys.stdout is not None and not getattr(sys, 'frozen', False)

def debug_print(message):
    """Debug print - snadno vypnutelný"""
    if DEBUG:
        print(f"🎭 [FaceDetect] {message}")


class FaceDetector:
    """Detekuje obličeje pomocí Haar Cascade nebo DNN"""
    
    def __init__(self):
        """Inicializace detektorů"""
        # Haar Cascade (výchozí, vždy dostupný)
        try:
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            self.face_cascade = cv2.CascadeClassifier(cascade_path)
            
            if self.face_cascade.empty():
                raise Exception("Nepodařilo se načíst Haar Cascade")
            
            debug_print("✅ Haar Cascade inicializován")
            
        except Exception as e:
            debug_print(f"❌ Chyba při inicializaci Haar: {e}")
            self.face_cascade = None
        
        # DNN Model (volitelný, přesnější)
        self.dnn_net = None
        try:
            model_dir = Path(__file__).parent / "models"
            prototxt = model_dir / "deploy.prototxt"
            caffemodel = model_dir / "res10_300x300_ssd_iter_140000.caffemodel"
            
            if prototxt.exists() and caffemodel.exists():
                self.dnn_net = cv2.dnn.readNetFromCaffe(str(prototxt), str(caffemodel))
                debug_print("✅ DNN model načten (Caffe ResNet-SSD)")
            else:
                debug_print("⚠️ DNN model soubory nenalezeny (models/deploy.prototxt + .caffemodel)")
                
        except Exception as e:
            debug_print(f"⚠️ DNN model se nepodařilo načíst: {e}")
            self.dnn_net = None
    
    def detect_face_haar(self, frame):
        """
        Detekuje největší obličej pomocí Haar Cascade
        
        Args:
            frame: OpenCV frame (BGR nebo RGB)
            
        Returns:
            (center_x, center_y, width, height) nebo None pokud není obličej
        """
        if self.face_cascade is None:
            return None
        
        # Převeď na grayscale pro detekci
        if len(frame.shape) == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray = frame
        
        # Detekce obličejů
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )
        
        if len(faces) == 0:
            debug_print("⚠️ Haar: Žádný obličej nenalezen")
            return None
        
        # Najdi největší obličej
        largest_face = max(faces, key=lambda face: face[2] * face[3])
        x, y, w, h = largest_face
        
        center_x = x + w // 2
        center_y = y + h // 2
        
        debug_print(f"✅ Haar: Největší obličej: centrum ({center_x}, {center_y}), velikost {w}x{h}")
        
        if len(faces) > 1:
            debug_print(f"ℹ️ Haar: Nalezeno {len(faces)} obličejů, použit největší")
        
        return (center_x, center_y, w, h)
    
    def detect_face_dnn(self, frame, confidence_threshold=0.5):
        """
        Detekuje největší obličej pomocí DNN (ResNet-SSD)
        
        Args:
            frame: OpenCV frame (BGR)
            confidence_threshold: Minimální spolehlivost (0.0-1.0)
            
        Returns:
            (center_x, center_y, width, height) nebo None pokud není obličej
        """
        if self.dnn_net is None:
            debug_print("❌ DNN: Model není dostupný")
            return None
        
        h, w = frame.shape[:2]
        
        # Připrav blob pro DNN (300x300, normalized)
        blob = cv2.dnn.blobFromImage(
            cv2.resize(frame, (300, 300)), 
            1.0, 
            (300, 300), 
            (104.0, 177.0, 123.0)
        )
        
        self.dnn_net.setInput(blob)
        detections = self.dnn_net.forward()
        
        # Najdi největší detekci s dostatečnou confidence
        best_detection = None
        best_area = 0
        
        for i in range(detections.shape[2]):
            confidence = detections[0, 0, i, 2]
            
            if confidence > confidence_threshold:
                box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                (startX, startY, endX, endY) = box.astype("int")
                
                # Ořez do hranic framu
                startX = max(0, startX)
                startY = max(0, startY)
                endX = min(w, endX)
                endY = min(h, endY)
                
                face_w = endX - startX
                face_h = endY - startY
                area = face_w * face_h
                
                if area > best_area:
                    best_area = area
                    best_detection = (startX, startY, face_w, face_h, confidence)
        
        if best_detection is None:
            debug_print(f"⚠️ DNN: Žádný obličej (confidence > {confidence_threshold})")
            return None
        
        x, y, face_w, face_h, conf = best_detection
        center_x = x + face_w // 2
        center_y = y + face_h // 2
        
        debug_print(f"✅ DNN: Obličej nalezen: centrum ({center_x}, {center_y}), velikost {face_w}x{face_h}, confidence {conf:.2f}")
        
        return (center_x, center_y, face_w, face_h)
    
    def detect_face(self, frame, use_dnn=False):
        """
        Detekuje největší obličej na framu (s automatickým fallbackem)
        
        Args:
            frame: OpenCV frame (BGR nebo RGB)
            use_dnn: Pokud True, zkusí DNN, pak fallback na Haar
            
        Returns:
            (center_x, center_y, width, height) nebo None pokud není obličej
        """
        if use_dnn and self.dnn_net is not None:
            debug_print("🔍 Zkouším DNN detekci...")
            
            try:
                # Ujisti se že je BGR (DNN očekává BGR)
                if len(frame.shape) == 3 and frame.shape[2] == 3:
                    # Předpokládáme BGR od OpenCV
                    result = self.detect_face_dnn(frame)
                    
                    if result is not None:
                        debug_print("✅ DNN: Úspěch!")
                        return result
                    else:
                        debug_print("⚠️ DNN: Obličej nenalezen → fallback Haar")
                        return self.detect_face_haar(frame)
                        
            except Exception as e:
                debug_print(f"❌ DNN: Chyba {e} → fallback Haar")
                return self.detect_face_haar(frame)
        else:
            # Přímo Haar (rychlejší)
            debug_print("🔍 Použit Haar Cascade")
            return self.detect_face_haar(frame)
    
    def get_crop_position(self, frame, crop_width, crop_height, video_width, video_height, use_dnn=False):
        """
        Detekuje obličej a vrátí optimální pozici crop boxu
        
        Args:
            frame: OpenCV frame
            crop_width: Šířka crop boxu (9:16 format)
            crop_height: Výška crop boxu
            video_width: Šířka videa
            video_height: Výška videa
            use_dnn: Pokud True, použije DNN s fallbackem na Haar
            
        Returns:
            (crop_x, crop_y) - levý horní roh crop boxu
            Nebo None pokud není obličej (použij fallback na střed)
        """
        face_data = self.detect_face(frame, use_dnn=use_dnn)
        
        if face_data is None:
            debug_print("⚠️ Fallback na střed videa")
            return None
        
        center_x, center_y, face_w, face_h = face_data
        
        # Vycentruj crop box na obličej
        crop_x = center_x - crop_width // 2
        crop_y = center_y - crop_height // 2
        
        # Clamp do hranic videa
        crop_x = max(0, min(crop_x, video_width - crop_width))
        crop_y = max(0, min(crop_y, video_height - crop_height))
        
        debug_print(f"📍 Crop box vycentrován: X={crop_x}, Y={crop_y}")
        
        return (crop_x, crop_y)


def quick_detect_face(frame, crop_width, crop_height, video_width, video_height, use_dnn=False):
    """
    Jednoduchá wrapper funkce pro rychlou detekci
    
    Args:
        frame: OpenCV frame
        crop_width, crop_height: Rozměry crop boxu
        video_width, video_height: Rozměry videa
        use_dnn: Použít DNN místo Haar
        
    Returns:
        (crop_x, crop_y) nebo None
    """
    detector = FaceDetector()
    return detector.get_crop_position(frame, crop_width, crop_height, video_width, video_height, use_dnn=use_dnn)
