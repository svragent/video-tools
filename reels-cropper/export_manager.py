#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Export Manager - export videa pomocí FFmpeg (s portable FFmpeg support)
"""

import subprocess
from pathlib import Path

# Auto-disable debug in EXE builds (detects missing console)
import sys
DEBUG = hasattr(sys, 'stdout') and sys.stdout is not None and not getattr(sys, 'frozen', False)

# --- START PATCH: portable FFmpeg ---
LOCAL_FFMPEG_DIR = Path(__file__).parent / "ffmpeg" / "bin"
LOCAL_FFMPEG_EXE = LOCAL_FFMPEG_DIR / "ffmpeg.exe"

def get_ffmpeg_executable():
    """
    Vrátí cestu k FFmpeg:
    1) pokud existuje v lokální složce ./ffmpeg/bin/ffmpeg.exe, použije ho
    2) jinak fallback na systémový PATH
    """
    if LOCAL_FFMPEG_EXE.exists():
        return str(LOCAL_FFMPEG_EXE)
    else:
        return "ffmpeg"  # fallback na systémový PATH
# --- END PATCH ---


class ExportManager:
    """Handles video export with FFmpeg"""
    
    # ✅ OPTIMIZATION: Threading support
    export_thread = None
    cancel_export = False

    
    # ✅ OPTIMIZATION: Threading support
    export_thread = None
    cancel_export = False

    
    # ✅ OPTIMIZATION: Threading support
    export_thread = None
    cancel_export = False

    
    # ✅ OPTIMIZATION: Threading support
    export_thread = None
    cancel_export = False

    
    @staticmethod
    def check_ffmpeg():
        """Check if FFmpeg is available"""
        try:
            subprocess.run([get_ffmpeg_executable(), '-version'], 
                         stdout=subprocess.PIPE, 
                         stderr=subprocess.PIPE,
                         check=True)
            return True
        except:
            return False
    
    @staticmethod
    def export_video(input_path, output_path, keyframe_manager, video_player, progress_callback=None):
        print('🔹 DEBUG: export_video started')
        """Export video with crop animation"""
        
        if not ExportManager.check_ffmpeg():
            raise Exception("FFmpeg not found. Please install FFmpeg.")
        
        info = video_player.get_video_info()
        total_frames = info['total_frames']
        fps = info['fps']
        
        
        # 🔍 DEBUG: Zobraz keyframy před exportem
        print("\n" + "="*60)
        print("🔍 DEBUG: Export video - keyframy:")
        print("="*60)
        keyframes_list = keyframe_manager.get_all_keyframes()
        if keyframes_list:
            print(f"📍 Počet keyframů: {len(keyframes_list)}")
            for frame_num, kf_data in keyframes_list:
                x, y, mode = kf_data
                print(f"   Frame {frame_num}: X={x}, Y={y}, Mode={mode}")
        else:
            print("⚠️  ŽÁDNÉ KEYFRAMY!")
        print(f"🎬 Celkový počet framů videa: {total_frames}")
        print(f"📦 Default pozice: X={video_player.crop_x}, Y={video_player.crop_y}")
        print("="*60 + "\n")

        # 🔍 DEBUG: Preview interpolace pro export
        if DEBUG:
            print("\n" + "="*60)
            print("🎬 DEBUG: Preview interpolace pro export")
            print("="*60)
            
            # Ukázka každých 10% videa
            sample_frames = [int(total_frames * i / 10) for i in range(11)]
            
            for frame_num in sample_frames:
                default_pos = (video_player.crop_x, video_player.crop_y)
                x, y = keyframe_manager.get_position_at_frame(frame_num, default_pos)
                progress = (frame_num / total_frames) * 100
                print(f"  Frame {frame_num:5d} ({progress:5.1f}%): X={x:4d}, Y={y:4d}")
            
            print("="*60 + "\n")
        
        # Generate crop filter for FFmpeg
        crop_commands = []
        
        for frame_num in range(total_frames):
            default_pos = (video_player.crop_x, video_player.crop_y)
            x, y = keyframe_manager.get_position_at_frame(frame_num, default_pos)
            
            if frame_num % 30 == 0:
                print(f"🎯 Frame {frame_num}/{total_frames}: interpolovaná pozice X={x}, Y={y}")

            x = max(0, min(x, info['width'] - info['crop_width']))
            y = max(0, min(y, info['height'] - info['crop_height']))
            
            crop_commands.append(f"crop={info['crop_width']}:{info['crop_height']}:{x}:{y}")
        
        try:
            temp_crop_file = output_path + '.crop.txt'
            
            # Detekce formátu pro správný audio filtr
            is_mxf = input_path.lower().endswith(('.mxf', '.MXF'))
            
            if not keyframe_manager.keyframes:
                x, y = video_player.crop_x, video_player.crop_y
                
                if is_mxf:
                    # MXF - 8 kanálů (původní chování)
                    cmd = [
                        get_ffmpeg_executable(), '-y',
                        '-i', input_path,
                        '-vf', f'yadif=1:-1:0,crop={info["crop_width"]}:{info["crop_height"]}:{x}:{y},scale=1080:1920',
                        '-c:v', 'libx264',
                        '-profile:v', 'high',
                        '-level', '4.1',
                        '-b:v', '8M',
                        '-maxrate', '8M',
                        '-bufsize', '16M',
                        '-preset', 'medium',
                        '-r', '25',
                        '-pix_fmt', 'yuv420p',
                        '-filter_complex',
                        '[0:a:0][0:a:1][0:a:2][0:a:3][0:a:4][0:a:5][0:a:6][0:a:7]amerge=inputs=8[amerged];[amerged]pan=stereo|c0=c0+c2+c4+c6|c1=c1+c3+c5+c7[aout]',
                        '-map', '0:v',
                        '-map', '[aout]',
                        '-c:a', 'aac',
                        '-b:a', '320k',
                        '-ar', '48000',
                        '-movflags', '+faststart',
                        output_path
                    ]
                else:
                    # MOV/MP4/AVI - jednoduchý stereo mix
                    cmd = [
                        get_ffmpeg_executable(), '-y',
                        '-i', input_path,
                        '-vf', f'yadif=1:-1:0,crop={info["crop_width"]}:{info["crop_height"]}:{x}:{y},scale=1080:1920',
                        '-c:v', 'libx264',
                        '-profile:v', 'high',
                        '-level', '4.1',
                        '-b:v', '8M',
                        '-maxrate', '8M',
                        '-bufsize', '16M',
                        '-preset', 'medium',
                        '-r', '25',
                        '-pix_fmt', 'yuv420p',
                        '-map', '0:v',
                        '-map', '0:a',
                        '-c:a', 'aac',
                        '-b:a', '320k',
                        '-ar', '48000',
                        '-ac', '2',
                        '-movflags', '+faststart',
                        output_path
                    ]
            else:
                crop_expr_x = ExportManager._build_crop_expression(
                    keyframe_manager, video_player, 'x', info)
                crop_expr_y = ExportManager._build_crop_expression(
                    keyframe_manager, video_player, 'y', info)
                
                if is_mxf:
                    # MXF - 8 kanálů (původní chování)
                    cmd = [
                        get_ffmpeg_executable(), '-y',
                        '-i', input_path,
                        '-vf', f'yadif=1:-1:0,crop={info["crop_width"]}:{info["crop_height"]}:{crop_expr_x}:{crop_expr_y},scale=1080:1920',
                        '-c:v', 'libx264',
                        '-profile:v', 'high',
                        '-level', '4.1',
                        '-b:v', '8M',
                        '-maxrate', '8M',
                        '-bufsize', '16M',
                        '-preset', 'medium',
                        '-r', '25',
                        '-pix_fmt', 'yuv420p',
                        '-filter_complex',
                        '[0:a:0][0:a:1][0:a:2][0:a:3][0:a:4][0:a:5][0:a:6][0:a:7]amerge=inputs=8,pan=stereo|c0<c0+c2+c4+c6|c1<c1+c3+c5+c7[aout]',
                        '-map', '0:v',
                        '-map', '[aout]',
                        '-ac', '2',
                        '-c:a', 'aac',
                        '-b:a', '320k',
                        '-ar', '48000',
                        '-movflags', '+faststart',
                        output_path
                    ]
                else:
                    # MOV/MP4/AVI - jednoduchý stereo mix
                    cmd = [
                        get_ffmpeg_executable(), '-y',
                        '-i', input_path,
                        '-vf', f'yadif=1:-1:0,crop={info["crop_width"]}:{info["crop_height"]}:{crop_expr_x}:{crop_expr_y},scale=1080:1920',
                        '-c:v', 'libx264',
                        '-profile:v', 'high',
                        '-level', '4.1',
                        '-b:v', '8M',
                        '-maxrate', '8M',
                        '-bufsize', '16M',
                        '-preset', 'medium',
                        '-r', '25',
                        '-pix_fmt', 'yuv420p',
                        '-map', '0:v',
                        '-map', '0:a',
                        '-c:a', 'aac',
                        '-b:a', '320k',
                        '-ar', '48000',
                        '-ac', '2',
                        '-movflags', '+faststart',
                        output_path
                    ]
            
            print("\n🔹 DEBUG: FFmpeg příkaz sestaven\n")
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                raise Exception(f"FFmpeg error: {stderr}")
            
            return True
            
        except Exception as e:
            raise Exception(f"Export failed: {e}")
    

    @staticmethod
    def _build_crop_expression(keyframe_manager, video_player, axis, info):
        """Build FFmpeg crop expression s interpolací - POUŽÍVÁ TIME místo FRAME NUMBER"""
        keyframes = keyframe_manager.get_all_keyframes()
        
        if DEBUG:
            print(f"\n🔧 DEBUG _build_crop_expression(axis='{axis}'):")
            print(f"   Počet keyframů: {len(keyframes)}")
        
        if not keyframes:
            default_x = video_player.crop_x
            default_y = video_player.crop_y
            return str(default_x if axis == 'x' else default_y)
        
        fps = info['fps']
        
        if len(keyframes) == 1:
            frame_num, kf_data = keyframes[0]
            x, y, mode = kf_data
            value = x if axis == 'x' else y
            return str(value)
        
        expressions = []
        for i in range(len(keyframes)):
            frame_num, kf_data = keyframes[i]
            x, y, mode = kf_data
            value = x if axis == 'x' else y
            time = frame_num / fps
            
            if i == 0:
                expr = f"if(lt(t\,{time})\,{value}\,"
                expressions.append(expr)
                if len(keyframes) > 1:
                    next_frame, next_kf_data = keyframes[i + 1]
                    next_x, next_y, next_mode = next_kf_data
                    next_value = next_x if axis == 'x' else next_y
                    next_time = next_frame / fps
                    
                    if next_mode == "linear":
                        slope = (next_value - value) / (next_time - time)
                        expr = f"if(lt(t\,{next_time})\,{value}+({slope}*(t-{time}))\,"
                    else:
                        expr = f"if(lt(t\,{next_time})\,{value}\,"
                    expressions.append(expr)
            elif i == len(keyframes) - 1:
                expr = f"{value}"
                expressions.append(expr)
            else:
                next_frame, next_kf_data = keyframes[i + 1]
                next_x, next_y, next_mode = next_kf_data
                next_value = next_x if axis == 'x' else next_y
                next_time = next_frame / fps
                
                if next_mode == "linear":
                    slope = (next_value - value) / (next_time - time)
                    expr = f"if(lt(t\,{next_time})\,{value}+({slope}*(t-{time}))\,"
                else:
                    expr = f"if(lt(t\,{next_time})\,{value}\,"
                expressions.append(expr)
        
        result = "".join(expressions) + ")" * (len(expressions) - 1)
        if DEBUG:
            print(f"🔧 DEBUG: Crop expression pro '{axis}' vytvořen")
        return result
