import os
import subprocess
import tkinter as tk
from tkinter import filedialog

def get_video_info(filepath):
    cmd_duration = ['ffprobe', '-v', 'error', '-select_streams', 'v:0',
                    '-show_entries', 'format=duration',
                    '-of', 'default=noprint_wrappers=1:nokey=1', filepath]
    duration_str = subprocess.check_output(cmd_duration).decode().strip()
    duration = float(duration_str)

    cmd_fps = ['ffprobe', '-v', 'error', '-select_streams', 'v:0',
               '-show_entries', 'stream=r_frame_rate',
               '-of', 'default=noprint_wrappers=1:nokey=1', filepath]
    fps_str = subprocess.check_output(cmd_fps).decode().strip()
    num, den = fps_str.split('/')
    fps = float(num) / float(den)

    nb_frames = round(duration * fps)

    frames = nb_frames % round(fps)
    total_seconds = nb_frames // round(fps)
    seconds = total_seconds % 60
    minutes = total_seconds // 60
    timecode = f"{minutes:02d}:{seconds:02d}:{frames:02d}"

    return timecode, nb_frames

def main():
    root = tk.Tk()
    root.withdraw()

    folder_selected = filedialog.askdirectory(title="Vyber složku s MXF soubory")
    if not folder_selected:
        print("Nebyla vybrána žádná složka, skript končí.")
        return

    files = [f for f in os.listdir(folder_selected) if f.lower().endswith('.mxf')]
    files.sort()

    data = []
    for f in files:
        path = os.path.join(folder_selected, f)
        try:
            timecode, nb_frames = get_video_info(path)
        except Exception as e:
            timecode = "N/A"
            nb_frames = -1
        if timecode == "00:25:00":
            continue
        data.append((timecode, nb_frames, f))

    data = [x for x in data if x[1] != -1]
    data.sort(key=lambda x: x[1], reverse=True)

    output_file = os.path.join(folder_selected, "stopaze.txt")
    with open(output_file, "w", encoding="utf-8") as out:
        out.write(f"{'Stopáž (MM:SS:FF)':<12} {'Soubor'}\n")
        out.write("-" * 50 + "\n")
        for timecode, nb_frames, f in data:
            out.write(f"{timecode} {f}\n")

    print(f"Hotovo! Výpis uložen v: {output_file}")

if __name__ == "__main__":
    main()
