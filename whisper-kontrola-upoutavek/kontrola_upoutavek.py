#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hromadný speech-to-text přepis posledních 15 sekund videí
Používá Whisper s kontrolou času a dne v názvu souboru
"""

import subprocess
import os
from pathlib import Path
import json
import re

def get_video_duration(video_path):
    """Zjistí délku videa v sekundách"""
    cmd = [
        'ffprobe', '-v', 'quiet',
        '-print_format', 'json',
        '-show_format',
        str(video_path)
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    data = json.loads(result.stdout)
    duration = float(data['format']['duration'])
    return duration

def extract_last_15s_audio(video_path, output_audio):
    """Vytáhne posledních 15 sekund audio do WAV s filtrováním pro lepší rozpoznání řeči"""
    duration = get_video_duration(video_path)
    start_time = max(0, duration - 15)
    
    cmd = [
        'ffmpeg', '-y',
        '-ss', str(start_time),
        '-i', str(video_path),
        '-vn',
        # Audio filtry pro zvýraznění řeči a potlačení hudby
        '-af', 'highpass=f=200,lowpass=f=3000,volume=2.0,dialoguenhance',
        '-acodec', 'pcm_s16le',
        '-ar', '16000',
        '-ac', '1',
        str(output_audio)
    ]
    
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def extract_time_from_filename(filename):
    """Extrahuje čas z názvu souboru (např. 2005 -> 20:05)"""
    # Hledá 4 cifry které vypadají jako čas (s podtržítkem před a tečkou nebo podtržítkem za)
    match = re.search(r'_(\d{4})[\._]', filename)
    if match:
        time_str = match.group(1)
        hour = time_str[:2]
        minute = time_str[2:]
        return f"{hour}:{minute}"
    return None

def extract_day_from_filename(filename):
    """Extrahuje den z názvu souboru"""
    filename_lower = filename.lower()
    
    days = {
        'pondeli': 'PONDĚLÍ',
        'utery': 'ÚTERÝ',
        'streda': 'STŘEDA',
        'ctvrtek': 'ČTVRTEK',
        'patek': 'PÁTEK',
        'sobota': 'SOBOTA',
        'nedele': 'NEDĚLE',
        'dnes': 'DNES',
        'zitra': 'ZÍTRA',
    }
    
    for day_key, day_value in days.items():
        if day_key in filename_lower:
            return day_value
    
    return None

def check_time_in_text(text, expected_time):
    """Kontroluje, zda je očekávaný čas v textu"""
    if not expected_time:
        return None
    
    # Odstranit dvojtečku pro flexibilnější hledání
    time_variants = [
        expected_time,  # 20:05
        expected_time.replace(':', '.'),  # 20.05
        expected_time.replace(':', ' '),  # 20 05
        expected_time.replace(':', ''),   # 2005
    ]
    
    text_lower = text.lower()
    for variant in time_variants:
        if variant in text_lower:
            return True
    
    # Kontrola slovního vyjádření (např. "dvacet nula pět")
    hour, minute = expected_time.split(':')
    
    # Slovní vyjádření hodin
    hour_words = {
        '20': ['dvacet'],
        '21': ['dvacet jedna', 'dvacet jeden'],
        '22': ['dvacet dva', 'dvacet dvě'],
        '19': ['devatenáct'],
        '18': ['osmnáct'],
    }
    
    # Slovní vyjádření minut
    minute_words = {
        '00': ['hodin', 'nula nula'],
        '05': ['nula pět', 'ma pět', 'pět'],
        '10': ['deset'],
        '15': ['patnáct', 'čtvrt'],
        '30': ['třicet', 'půl'],
        '45': ['čtyřicet pět', 'tři čtvrtě'],
        '50': ['padesát'],
    }
    
    if hour in hour_words and minute in minute_words:
        for h_word in hour_words[hour]:
            for m_word in minute_words[minute]:
                # Kontrola různých kombinací
                patterns = [
                    f"{h_word} {m_word}",
                    f"ve {h_word} {m_word}",
                    f"v {h_word} {m_word}",
                ]
                for pattern in patterns:
                    if pattern in text_lower:
                        return True
    
    return False

def check_day_in_text(text, expected_day):
    """Kontroluje, zda je očekávaný den v textu"""
    if not expected_day:
        return None
    
    text_upper = text.upper()
    
    # Kontrola přesné shody
    if expected_day in text_upper:
        return True
    
    # Kontrola variant (např. STŘEDU místo STŘEDA)
    day_variants = {
        'PONDĚLÍ': ['PONDĚLÍ', 'PONDELI'],
        'ÚTERÝ': ['ÚTERÝ', 'UTERY'],
        'STŘEDA': ['STŘEDA', 'STREDA', 'STŘEDU', 'STREDU'],
        'ČTVRTEK': ['ČTVRTEK', 'CTVRTEK'],
        'PÁTEK': ['PÁTEK', 'PATEK'],
        'SOBOTA': ['SOBOTA', 'SOBOTU'],
        'NEDĚLE': ['NEDĚLE', 'NEDELE', 'NEDĚLI', 'NEDELI'],
        'DNES': ['DNES'],
        'ZÍTRA': ['ZÍTRA', 'ZITRA'],
    }
    
    if expected_day in day_variants:
        for variant in day_variants[expected_day]:
            if variant in text_upper:
                return True
    
    return False

def format_transcript(text):
    """Formátuje přepis - časy na HH:MM a velká písmena pro klíčová slova"""
    if not text:
        return text
    
    # Převod časů na HH:MM
    time_patterns = {
        r'dvacet jedna padesát': '21:50',
        r'dvacet jedna čtyřicet pět': '21:45',
        r'dvacet jedna deset': '21:10',
        r'dvacet dva nola pět': '22:05',
        r'dvacet dva nula pět': '22:05',
        r'dvacet nola pět': '20:05',
        r'dvacet nula pět': '20:05',
        r'dvacet ma pět': '20:05',
        r'dvacet pět': '20:05',
        r'dvacet jedna hodin': '21:00',
        r'dvacet jedna': '21:00',
        r'dvacet dva': '22:00',
        r'dvacet': '20:00',
    }
    
    for pattern, replacement in time_patterns.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    
    # Velká písmena pro dny
    day_patterns = {
        r'\bpondělí\b': 'PONDĚLÍ',
        r'\búterý\b': 'ÚTERÝ',
        r'\bstředa\b': 'STŘEDA',
        r'\bčtvrtek\b': 'ČTVRTEK',
        r'\bpátek\b': 'PÁTEK',
        r'\bsobota\b': 'SOBOTA',
        r'\bneděle\b': 'NEDĚLE',
        r'\bdnes\b': 'DNES',
        r'\bzítra\b': 'ZÍTRA',
        r'\bzitra\b': 'ZÍTRA',
    }
    
    for pattern, replacement in day_patterns.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    
    # Velká písmena pro kanály
    channel_patterns = {
        r'tv barrandov': 'TV BARRANDOV',
        r'barrandov kino': 'KINO BARRANDOV',
        r'kino barrandov': 'KINO BARRANDOV',
        r'barrandov krimi': 'KRIMI BARRANDOV',
        r'krimi barrandov': 'KRIMI BARRANDOV',
    }
    
    for pattern, replacement in channel_patterns.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    
    return text

def transcribe_audio(audio_path):
    """Přepíše audio pomocí Whisper"""
    try:
        import whisper
        
        # Načti MEDIUM model (přesnější než base)
        model = whisper.load_model("medium")
        
        # Přepiš
        result = model.transcribe(str(audio_path), language="cs")
        
        # Formátuj text
        formatted_text = format_transcript(result["text"])
        
        return formatted_text
        
    except Exception as e:
        print(f"❌ Chyba při přepisu: {e}")
        return None

def process_folder(folder_path):
    """Zpracuje všechny videa ve složce"""
    folder = Path(folder_path)
    
    if not folder.exists():
        print(f"❌ Složka nenalezena: {folder}")
        return
    
    # Najdi všechny video soubory
    video_extensions = ['.mov', '.mxf', '.mp4', '.avi', '.mkv']
    videos = []
    for ext in video_extensions:
        videos.extend(folder.glob(f'*{ext}'))
    
    if not videos:
        print(f"❌ Ve složce nejsou žádné video soubory")
        return
    
    print(f"\n📁 Složka: {folder}")
    print(f"📹 Nalezeno videí: {len(videos)}")
    print()
    
    # Výstupní soubor
    output_file = folder / "prepisy_vsech_upoutavek.txt"
    
    # Dočasné audio
    temp_audio = folder / "temp_audio.wav"
    
    # Zpracuj všechna videa - průběžný zápis
    for i, video in enumerate(videos, 1):
        print(f"[{i}/{len(videos)}] {video.name}")
        
        try:
            # Extrahuj očekávaný čas a den z názvu
            expected_time = extract_time_from_filename(video.name)
            expected_day = extract_day_from_filename(video.name)
            
            # Vytáhni audio
            print(f"   🎵 Vytahuji audio...")
            extract_last_15s_audio(video, temp_audio)
            
            # Přepiš
            print(f"   🎤 Přepisuji...")
            transcript = transcribe_audio(temp_audio)
            
            # Kontrola času a dne
            time_check = None
            day_check = None
            
            if transcript:
                if expected_time:
                    time_check = check_time_in_text(transcript, expected_time)
                if expected_day:
                    day_check = check_day_in_text(transcript, expected_day)
            
            # Průběžně zapisuj do souboru
            with open(output_file, 'a', encoding='utf-8') as f:
                f.write(f"{video.name}\n")
                
                if transcript:
                    f.write(f"{transcript}\n")
                    
                    # Kontrola času
                    if expected_time:
                        if time_check:
                            f.write(f"✅ ČAS: Sedí ({expected_time})\n")
                            print(f"   ✅ ČAS: Sedí ({expected_time})")
                        else:
                            f.write(f"❌ ČAS: Nesedí! (očekáván: {expected_time}, ale není v přepisu)\n")
                            print(f"   ❌ ČAS: Nesedí! (očekáván: {expected_time})")
                    
                    # Kontrola dne
                    if expected_day:
                        if day_check:
                            f.write(f"✅ DEN: Sedí ({expected_day})\n")
                            print(f"   ✅ DEN: Sedí ({expected_day})")
                        else:
                            f.write(f"❌ DEN: Nesedí! (očekáván: {expected_day}, ale není v přepisu)\n")
                            print(f"   ❌ DEN: Nesedí! (očekáván: {expected_day})")
                    
                    f.write(f"\n\n")
                    print(f"   ✅ Hotovo a uloženo")
                else:
                    f.write(f"(přepis se nezdařil)\n\n\n")
                    print(f"   ⚠️ Přepis selhal")
            
        except Exception as e:
            with open(output_file, 'a', encoding='utf-8') as f:
                f.write(f"{video.name}\n(chyba: {e})\n\n\n")
            print(f"   ❌ Chyba: {e}")
        
        print()
    
    # Smaž temp audio
    if temp_audio.exists():
        temp_audio.unlink()
    
    print("="*60)
    print(f"✅ VŠECHNY PŘEPISY DOKONČENY!")
    print(f"📄 Uloženo: {output_file.name}")
    print(f"📊 Zpracováno videí: {len(videos)}")
    print("="*60)

def main():
    # Složka s upoutávkami - výběr v okně
    import tkinter as tk
    from tkinter import filedialog
    root = tk.Tk()
    root.withdraw()
    folder_path = filedialog.askdirectory(title="Vyber složku s upoutávkami")
    root.destroy()
    if not folder_path:
        print("Nebyla vybrána žádná složka.")
        return

    print("\n" + "="*60)
    print("🎬 HROMADNÝ SPEECH-TO-TEXT S KONTROLOU")
    print("="*60)
    
    process_folder(folder_path)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Přerušeno")
    except Exception as e:
        print(f"\n❌ Chyba: {e}")
        import traceback
        traceback.print_exc()
    finally:
        input("\nStiskni Enter pro ukončení...")
