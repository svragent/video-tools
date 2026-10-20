import os
import sys
from pydub import AudioSegment
import numpy as np
import requests, time, hmac, hashlib, base64
import threading
import json
from datetime import datetime, timedelta
try:
    import tkinter as tk
    from tkinter import filedialog, messagebox, scrolledtext, ttk
except ImportError:
    import Tkinter as tk
    from tkFileDialog import filedialog
    from tkMessageBox import messagebox
    from ScrolledText import ScrolledText as scrolledtext
    import ttk

# ----- ACRCloud klice (nacitaji se ze souboru config.json vedle programu) -----
def load_acr_config():
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(base_dir, "config.json")
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            cfg = json.load(f)
        return cfg["host"], cfg["access_key"], cfg["access_secret"]
    except Exception:
        print("CHYBA: Chybi nebo je spatne vyplneny config.json (viz config.example.json)")
        return "", "", ""

host, access_key, access_secret = load_acr_config()

# ----- Globalni promenne -----
stop_processing = False
INTERVAL_HOURS = 24
INTERVAL_MINUTES = 5
FILES_PER_BATCH = 3

# ----- Funkce pro vypocet energie stopy -----
def calculate_energy(file_path):
    try:
        audio = AudioSegment.from_file(file_path)
        samples = np.array(audio.get_array_of_samples(), dtype=float)
        energy = np.mean(samples**2) / (np.max(samples**2)+1e-10)
        return energy, len(audio)
    except Exception as e:
        return 0, 0

# ----- Funkce pro rozpoznani ACRCloud -----
def recognize_segment(segment_audio):
    temp_file = "temp_segment.wav"
    try:
        segment_audio.export(temp_file, format="wav")
    except Exception as e:
        return None, "Chyba exportu: " + str(e)

    http_method = "POST"
    http_uri = "/v1/identify"
    data_type = "audio"
    signature_version = "1"
    timestamp = str(int(time.time()))

    string_to_sign = "\n".join([http_method, http_uri, access_key, data_type, signature_version, timestamp])
    sign = base64.b64encode(
        hmac.new(access_secret.encode('utf-8'),
                 string_to_sign.encode('utf-8'),
                 digestmod=hashlib.sha1).digest()
    ).decode('utf-8')

    data = {
        "access_key": access_key,
        "data_type": data_type,
        "signature_version": signature_version,
        "signature": sign,
        "timestamp": timestamp
    }

    try:
        files = {"sample": open(temp_file, "rb")}
        url = "https://" + host + "/v1/identify"
        response = requests.post(url, files=files, data=data, timeout=10)
        result = response.json()

        status_msg = result.get("status", {}).get("msg", "Neznama odpoved")

        if "metadata" in result and "music" in result["metadata"]:
            track = result["metadata"]["music"][0]
            title = track.get("title", "Unknown")
            artists = ", ".join([a.get("name", "Unknown") for a in track.get("artists", [])])
            label = track.get("label", "Unknown")
            release_date = track.get("release_date", "Unknown")
            return (title, artists, label, release_date), status_msg
        else:
            return None, status_msg
    except Exception as e:
        return None, "Chyba API: " + str(e)

# ----- Hlavni funkce pro zpracovani souboru -----
def process_file(input_file, temp_folder, log_callback, segment_length_s=7.0, step_s=3.5):
    global stop_processing

    segment_length_ms = int(segment_length_s * 1000)
    step_ms = int(step_s * 1000)
    min_segment_ms = 5000

    log_callback("Zpracovavam: " + os.path.basename(input_file))
    log_callback("  Vzorek: " + str(segment_length_s) + " s  |  Krok: " + str(step_s) + " s")

    file_ext = input_file.lower()
    is_wav = file_ext.endswith('.wav') or file_ext.endswith('.mp3')
    is_mxf = file_ext.endswith('.mxf')

    if not is_wav and not is_mxf:
        log_callback("  CHYBA: Nepodporovany format")
        return {"status": "error", "message": "Nepodporovany format"}

    if stop_processing:
        log_callback("  PRERUSENO uzivatelem")
        return {"status": "stopped", "message": "Preruseno uzivatelem"}

    if is_wav:
        track_files = [input_file]
    else:
        num_stops = 8
        track_files = []
        for i in range(num_stops):
            if stop_processing:
                return {"status": "stopped", "message": "Preruseno pri extrakci"}
            out_file = os.path.join(temp_folder, "track" + str(i) + ".wav")
            track_files.append(out_file)
            cmd = 'ffmpeg -y -i "' + input_file + '" -map 0:a:' + str(i) + ' "' + out_file + '" 2>NUL'
            os.system(cmd)

    track_energies = []
    for i, track_file in enumerate(track_files):
        if stop_processing:
            break
        if os.path.exists(track_file):
            file_size = os.path.getsize(track_file)
            if file_size > 1000:
                energy, duration = calculate_energy(track_file)
                track_energies.append((i, track_file, energy, duration))

    if len(track_energies) == 0:
        log_callback("  Zadne audio stopy")
        return {"status": "no_audio", "message": "Zadne audio stopy"}

    energy_threshold = 0.005
    selected_tracks = []
    for i, track_file, energy, duration in track_energies:
        if energy > energy_threshold:
            selected_tracks.append((i, track_file, energy, duration))

    if len(selected_tracks) == 0:
        log_callback("  Zadne stopy s hudbou")
        return {"status": "no_music", "message": "Zadne stopy s hudbou"}

    track_timeline = {}
    track_details = {}
    track_durations = {}

    for track_idx, track_file, track_energy, duration in selected_tracks:
        if stop_processing:
            break

        track_durations[track_idx] = duration
        track_timeline[track_idx] = []

        try:
            audio = AudioSegment.from_file(track_file)
        except Exception as e:
            continue

        half_seg = segment_length_ms // 2
        test_positions = [
            (0, min(segment_length_ms, len(audio))),
            (len(audio) // 2 - half_seg, len(audio) // 2 + half_seg),
            (max(0, len(audio) - segment_length_ms), len(audio))
        ]

        has_music = False
        for test_start, test_end in test_positions:
            if stop_processing:
                break
            if test_end - test_start < min_segment_ms:
                continue
            test_segment = audio[test_start:test_end]
            track_info, status = recognize_segment(test_segment)
            if track_info:
                has_music = True
                break
            time.sleep(0.2)

        if not has_music:
            continue

        pos = 0

        while pos < len(audio):
            if stop_processing:
                break

            start_ms = pos
            end_ms = min(pos + segment_length_ms, len(audio))
            segment_duration = end_ms - start_ms

            if segment_duration < min_segment_ms:
                break

            segment = audio[start_ms:end_ms]
            track_info, status = recognize_segment(segment)

            if track_info:
                title, artists, label, release_date = track_info
                track_timeline[track_idx].append((start_ms, end_ms, title))

                if title not in track_details:
                    track_details[title] = {
                        'artists': artists,
                        'label': label,
                        'release_date': release_date
                    }

            pos += step_ms
            time.sleep(0.2)

    all_segments = []
    for track_idx, segments in track_timeline.items():
        for start_ms, end_ms, title in segments:
            all_segments.append((track_idx, start_ms, end_ms, title))

    if len(all_segments) == 0:
        log_callback("  Zadne skladby rozpoznany")
        if stop_processing:
            return {"status": "stopped", "message": "Preruseno - zadne vysledky"}
        else:
            return {"status": "no_recognition", "message": "Zadne skladby rozpoznany"}

    songs_by_title = {}
    for track_idx, start_ms, end_ms, title in all_segments:
        if title not in songs_by_title:
            songs_by_title[title] = []
        songs_by_title[title].append((track_idx, start_ms, end_ms))

    results = []
    for title, segments in songs_by_title.items():
        if stop_processing:
            break

        tracks_used = list(set([s[0] for s in segments]))

        parallel = False
        if len(tracks_used) > 1:
            track_lengths = [track_durations[t] for t in tracks_used]
            min_len = min(track_lengths)
            max_len = max(track_lengths)
            if max_len - min_len < 1000:
                parallel = True

        if parallel:
            total_track_ms = max([track_durations[t] for t in tracks_used])
        else:
            total_track_ms = sum([track_durations[t] for t in tracks_used])

        if parallel:
            all_intervals = []
            for track_idx, start_ms, end_ms in segments:
                all_intervals.append((start_ms, end_ms))

            all_intervals.sort()
            if len(all_intervals) > 0:
                merged = []
                current_start, current_end = all_intervals[0]

                for start, end in all_intervals[1:]:
                    if start <= current_end:
                        current_end = max(current_end, end)
                    else:
                        merged.append((current_start, current_end))
                        current_start, current_end = start, end

                merged.append((current_start, current_end))
                recognized_ms = sum([end - start for start, end in merged])
            else:
                recognized_ms = 0
        else:
            sorted_segments = sorted(segments, key=lambda x: (x[0], x[1]))
            merged_time = 0
            current_track_segments = {}

            for track_idx, start_ms, end_ms in sorted_segments:
                if track_idx not in current_track_segments:
                    current_track_segments[track_idx] = []
                current_track_segments[track_idx].append((start_ms, end_ms))

            for track_idx, track_segs in current_track_segments.items():
                track_segs.sort()
                if len(track_segs) == 0:
                    continue

                merged = []
                current_start, current_end = track_segs[0]

                for start, end in track_segs[1:]:
                    if start <= current_end:
                        current_end = max(current_end, end)
                    else:
                        merged.append((current_start, current_end))
                        current_start, current_end = start, end

                merged.append((current_start, current_end))

                for start, end in merged:
                    merged_time += (end - start)

            recognized_ms = merged_time

        if parallel and recognized_ms < total_track_ms * 0.7:
            recommended_length = total_track_ms
        else:
            recommended_length = recognized_ms

        details = track_details[title]
        seconds = recommended_length / 1000

        results.append({
            'title': title,
            'artists': details['artists'],
            'label': details['label'],
            'release_date': details['release_date'],
            'length_seconds': seconds
        })

        log_callback("  Rozpoznano: " + title + " (" + str(round(seconds, 1)) + " s)")

    if stop_processing and len(results) > 0:
        return {"status": "partial", "results": results, "message": "Castecne zpracovano"}
    elif len(results) > 0:
        return {"status": "success", "results": results}
    else:
        return {"status": "no_recognition", "message": "Zadne skladby"}

# ----- Funkce pro zapis vysledku do souboru -----
def write_result_to_file(output_file, filename, result_data):
    try:
        with open(output_file, 'a', encoding='utf-8') as f:
            status = result_data.get("status", "unknown")

            if status == "success" or status == "partial":
                results = result_data.get("results", [])
                if len(results) > 0:
                    line = filename
                    for i, r in enumerate(results):
                        if i > 0:
                            line += " ||| "
                        else:
                            line += " | "

                        line += r['title']
                        line += " | " + r['artists']
                        line += " | " + r['label']

                        release_year = r['release_date'][:4] if len(r['release_date']) >= 4 else r['release_date']
                        line += " | " + release_year

                        line += " | " + str(round(r['length_seconds'], 1)) + " s"

                    if status == "partial":
                        line += " | [CASTECNE - PRERUSENO]"

                    f.write(line + "\n")
                else:
                    f.write(filename + " | [ZADNE VYSLEDKY]\n")

            elif status == "stopped":
                message = result_data.get("message", "Preruseno")
                f.write(filename + " | [PRERUSENO: " + message + "]\n")

            elif status == "error":
                message = result_data.get("message", "Chyba")
                f.write(filename + " | [CHYBA: " + message + "]\n")

            elif status == "no_audio":
                f.write(filename + " | [ZADNE AUDIO STOPY]\n")

            elif status == "no_music":
                f.write(filename + " | [ZADNA HUDBA DETEKOVANA]\n")

            elif status == "no_recognition":
                f.write(filename + " | [SKLADBY NEROZPOZNANY]\n")

            else:
                f.write(filename + " | [NEZNAMY STAV]\n")

            f.flush()
        return True
    except Exception as e:
        return False

# ----- Sprava fronty souboru -----
class QueueManager:
    def __init__(self, queue_file, config_file):
        self.queue_file = queue_file
        self.config_file = config_file
        self.queue = []
        self.config = {
            'files_per_batch': 3,
            'interval_hours': 24,
            'interval_minutes': 5,
            'segment_length_s': 7.0,
            'step_s': 3.5
        }
        self.load_queue()
        self.load_config()

    def load_queue(self):
        if os.path.exists(self.queue_file):
            try:
                with open(self.queue_file, 'r', encoding='utf-8') as f:
                    self.queue = json.load(f)
            except:
                self.queue = []
        else:
            self.queue = []

    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                if 'segment_length_s' not in self.config:
                    self.config['segment_length_s'] = 7.0
                if 'step_s' not in self.config:
                    self.config['step_s'] = 3.5
            except:
                self.config = {
                    'files_per_batch': 3,
                    'interval_hours': 24,
                    'interval_minutes': 5,
                    'segment_length_s': 7.0,
                    'step_s': 3.5
                }
        else:
            self.config = {
                'files_per_batch': 3,
                'interval_hours': 24,
                'interval_minutes': 5,
                'segment_length_s': 7.0,
                'step_s': 3.5
            }

    def save_config(self):
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            return True
        except:
            return False

    def get_files_per_batch(self):
        return self.config.get('files_per_batch', 3)

    def set_files_per_batch(self, count):
        self.config['files_per_batch'] = count
        self.save_config()

    def get_interval_hours(self):
        return self.config.get('interval_hours', 24)

    def get_interval_minutes(self):
        return self.config.get('interval_minutes', 5)

    def set_interval(self, hours, minutes):
        self.config['interval_hours'] = hours
        self.config['interval_minutes'] = minutes
        self.save_config()

    def get_segment_length_s(self):
        return self.config.get('segment_length_s', 7.0)

    def set_segment_length_s(self, value):
        self.config['segment_length_s'] = value
        self.save_config()

    def get_step_s(self):
        return self.config.get('step_s', 3.5)

    def set_step_s(self, value):
        self.config['step_s'] = value
        self.save_config()

    def save_queue(self):
        try:
            with open(self.queue_file, 'w', encoding='utf-8') as f:
                json.dump(self.queue, f, indent=2, ensure_ascii=False)
            return True
        except:
            return False

    def add_files(self, file_paths):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for file_path in file_paths:
            already_exists = False
            for item in self.queue:
                if item['file_path'] == file_path:
                    already_exists = True
                    break

            if not already_exists:
                self.queue.append({
                    'file_path': file_path,
                    'file_name': os.path.basename(file_path),
                    'status': 'waiting',
                    'added_time': current_time,
                    'processed_time': None,
                    'result': None
                })

        self.save_queue()

    def get_waiting_files(self, count):
        waiting = []
        for item in self.queue:
            if item['status'] == 'waiting':
                waiting.append(item)
                if len(waiting) >= count:
                    break
        return waiting

    def update_status(self, file_path, status, result=None):
        for item in self.queue:
            if item['file_path'] == file_path:
                item['status'] = status
                if status in ['completed', 'error', 'no_audio', 'no_music', 'no_recognition']:
                    item['processed_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                if result:
                    item['result'] = result
                break
        self.save_queue()

    def reset_file_status(self, file_path):
        for item in self.queue:
            if item['file_path'] == file_path:
                item['status'] = 'waiting'
                item['processed_time'] = None
                item['result'] = None
                break
        self.save_queue()

    def get_statistics(self):
        waiting = 0
        processing = 0
        completed = 0
        error = 0

        for item in self.queue:
            if item['status'] == 'waiting':
                waiting += 1
            elif item['status'] == 'processing':
                processing += 1
            elif item['status'] == 'completed':
                completed += 1
            elif item['status'] in ['error', 'no_audio', 'no_music', 'no_recognition']:
                error += 1

        return {
            'waiting': waiting,
            'processing': processing,
            'completed': completed,
            'error': error,
            'total': len(self.queue)
        }

# ----- GUI Aplikace -----
class MusicRecognitionGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Rozpoznavani hudby - AUTOMATICKA FRONTA (24h 5min)")
        self.root.geometry("920x700")
        self.root.minsize(600, 400)

        if getattr(sys, 'frozen', False):
            # Bezi jako EXE (PyInstaller)
            program_dir = os.path.dirname(sys.executable)
        else:
            # Bezi jako skript
            program_dir = os.path.dirname(os.path.abspath(__file__))

        self.temp_folder = os.path.join(os.path.expanduser("~"), "Desktop", "temp_audio")
        self.output_file = None
        self.queue_file = os.path.join(program_dir, "music_queue.json")
        self.config_file = os.path.join(program_dir, "music_config.json")

        self.queue_manager = QueueManager(self.queue_file, self.config_file)

        self.processing_thread = None
        self.timer_thread = None
        self.next_processing_time = None
        self.timer_running = False

        # ----- Rolovatelna oblast -----
        outer_frame = tk.Frame(root)
        outer_frame.pack(fill=tk.BOTH, expand=True)

        self._scrollbar = tk.Scrollbar(outer_frame, orient=tk.VERTICAL)
        self._scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self._canvas = tk.Canvas(outer_frame, yscrollcommand=self._scrollbar.set)
        self._canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._scrollbar.config(command=self._canvas.yview)

        self._inner_frame = tk.Frame(self._canvas)
        self._canvas_window = self._canvas.create_window(
            (0, 0),
            window=self._inner_frame,
            anchor=tk.NW
        )

        self._inner_frame.bind("<Configure>", self._on_inner_frame_configure)
        self._canvas.bind("<Configure>", self._on_canvas_configure)
        self._canvas.bind("<MouseWheel>", self._on_mousewheel)
        self._inner_frame.bind("<MouseWheel>", self._on_mousewheel)

        main_frame = tk.Frame(self._inner_frame, padx=10, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # ----- Statistiky -----
        stats_frame = tk.Frame(main_frame, relief=tk.RIDGE, borderwidth=2, padx=5, pady=5)
        stats_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Label(stats_frame, text="STATISTIKY FRONTY", font=("Arial", 10, "bold")).pack()

        stats_info_frame = tk.Frame(stats_frame)
        stats_info_frame.pack(fill=tk.X, pady=5)

        self.stats_waiting_label = tk.Label(stats_info_frame, text="Ceka: 0", font=("Arial", 9))
        self.stats_waiting_label.pack(side=tk.LEFT, padx=10)

        self.stats_processing_label = tk.Label(stats_info_frame, text="Zpracovava se: 0", font=("Arial", 9))
        self.stats_processing_label.pack(side=tk.LEFT, padx=10)

        self.stats_completed_label = tk.Label(stats_info_frame, text="Hotovo: 0", font=("Arial", 9))
        self.stats_completed_label.pack(side=tk.LEFT, padx=10)

        self.stats_error_label = tk.Label(stats_info_frame, text="Chyby: 0", font=("Arial", 9))
        self.stats_error_label.pack(side=tk.LEFT, padx=10)

        # ----- Casovac -----
        timer_frame = tk.Frame(main_frame, relief=tk.RIDGE, borderwidth=2, padx=5, pady=5)
        timer_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Label(timer_frame, text="AUTOMATICKE ZPRACOVANI", font=("Arial", 10, "bold")).pack()

        files_count_frame = tk.Frame(timer_frame)
        files_count_frame.pack(pady=5)

        tk.Label(files_count_frame, text="Pocet souboru na davku:", font=("Arial", 9)).pack(side=tk.LEFT, padx=5)

        self.files_per_batch_var = tk.IntVar(value=self.queue_manager.get_files_per_batch())
        self.files_per_batch_spinbox = tk.Spinbox(
            files_count_frame, from_=1, to=9999,
            textvariable=self.files_per_batch_var,
            width=6, font=("Arial", 10),
            command=self.on_files_per_batch_change
        )
        self.files_per_batch_spinbox.pack(side=tk.LEFT, padx=5)
        # Zachyceni rucniho zadani
        self.files_per_batch_spinbox.bind("<FocusOut>", lambda e: self.on_files_per_batch_change())
        self.files_per_batch_spinbox.bind("<Return>", lambda e: self.on_files_per_batch_change())

        tk.Label(files_count_frame, text="(1-9999 souboru)", font=("Arial", 8), fg="gray").pack(side=tk.LEFT)

        interval_frame = tk.Frame(timer_frame)
        interval_frame.pack(pady=5)

        tk.Label(interval_frame, text="Interval zpracovani:", font=("Arial", 9)).pack(side=tk.LEFT, padx=5)

        self.interval_hours_var = tk.IntVar(value=self.queue_manager.get_interval_hours())
        self.interval_hours_spinbox = tk.Spinbox(
            interval_frame, from_=0, to=168,
            textvariable=self.interval_hours_var,
            width=4, font=("Arial", 10),
            command=self.on_interval_change
        )
        self.interval_hours_spinbox.pack(side=tk.LEFT, padx=2)
        # Zachyceni rucniho zadani
        self.interval_hours_spinbox.bind("<FocusOut>", lambda e: self.on_interval_change())
        self.interval_hours_spinbox.bind("<Return>", lambda e: self.on_interval_change())

        tk.Label(interval_frame, text="hodin", font=("Arial", 9)).pack(side=tk.LEFT, padx=2)

        self.interval_minutes_var = tk.IntVar(value=self.queue_manager.get_interval_minutes())
        self.interval_minutes_spinbox = tk.Spinbox(
            interval_frame, from_=0, to=59,
            textvariable=self.interval_minutes_var,
            width=4, font=("Arial", 10),
            command=self.on_interval_change
        )
        self.interval_minutes_spinbox.pack(side=tk.LEFT, padx=2)
        # Zachyceni rucniho zadani
        self.interval_minutes_spinbox.bind("<FocusOut>", lambda e: self.on_interval_change())
        self.interval_minutes_spinbox.bind("<Return>", lambda e: self.on_interval_change())

        tk.Label(interval_frame, text="minut", font=("Arial", 9)).pack(side=tk.LEFT, padx=2)
        tk.Label(interval_frame, text="(0-168h, 0-59min)", font=("Arial", 8), fg="gray").pack(side=tk.LEFT, padx=5)

        self.timer_status_label = tk.Label(timer_frame, text="Casovac VYPNUTY", font=("Arial", 9), fg="red")
        self.timer_status_label.pack(pady=2)

        self.timer_countdown_label = tk.Label(timer_frame, text="Dalsi zpracovani za: --:--:--", font=("Arial", 9))
        self.timer_countdown_label.pack(pady=2)

        timer_btn_frame = tk.Frame(timer_frame)
        timer_btn_frame.pack(pady=5)

        self.start_timer_btn = tk.Button(
            timer_btn_frame, text="SPUSTIT CASOVAC", command=self.start_timer,
            bg="#4CAF50", fg="white", font=("Arial", 10, "bold"), width=18
        )
        self.start_timer_btn.pack(side=tk.LEFT, padx=5)

        self.stop_timer_btn = tk.Button(
            timer_btn_frame, text="ZASTAVIT CASOVAC", command=self.stop_timer,
            bg="#f44336", fg="white", font=("Arial", 10, "bold"), width=18, state=tk.DISABLED
        )
        self.stop_timer_btn.pack(side=tk.LEFT, padx=5)

        timer_btn_frame2 = tk.Frame(timer_frame)
        timer_btn_frame2.pack(pady=5)

        self.process_now_btn = tk.Button(
            timer_btn_frame2, text="ZPRACOVAT HNED", command=self.process_now,
            bg="#2196F3", fg="white", font=("Arial", 10, "bold"), width=18
        )
        self.process_now_btn.pack(side=tk.LEFT, padx=5)

        self.stop_processing_btn = tk.Button(
            timer_btn_frame2, text="ZASTAVIT ZPRACOVANI", command=self.stop_processing_cmd,
            bg="#FF9800", fg="white", font=("Arial", 10, "bold"), width=18, state=tk.DISABLED
        )
        self.stop_processing_btn.pack(side=tk.LEFT, padx=5)

        # ----- Pridani souboru do fronty -----
        add_frame = tk.Frame(main_frame, relief=tk.RIDGE, borderwidth=2, padx=5, pady=5)
        add_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Label(add_frame, text="PRIDANI SOUBORU DO FRONTY", font=("Arial", 10, "bold")).pack()

        tk.Button(
            add_frame, text="Pridat soubory do fronty", command=self.add_files_to_queue,
            font=("Arial", 10), width=25
        ).pack(pady=5)

        # ----- Fronta souboru -----
        tk.Label(main_frame, text="FRONTA SOUBORU:", font=("Arial", 10, "bold")).pack(anchor=tk.W)

        queue_frame = tk.Frame(main_frame)
        queue_frame.pack(fill=tk.X, pady=5)

        columns = ('Soubor', 'Stav', 'Pridan', 'Zpracovan')
        self.queue_tree = ttk.Treeview(queue_frame, columns=columns, show='headings', height=8)

        self.queue_tree.heading('Soubor', text='Soubor')
        self.queue_tree.heading('Stav', text='Stav')
        self.queue_tree.heading('Pridan', text='Pridan')
        self.queue_tree.heading('Zpracovan', text='Zpracovan')

        self.queue_tree.column('Soubor', width=300)
        self.queue_tree.column('Stav', width=120)
        self.queue_tree.column('Pridan', width=150)
        self.queue_tree.column('Zpracovan', width=150)

        tree_scrollbar = tk.Scrollbar(queue_frame, orient=tk.VERTICAL, command=self.queue_tree.yview)
        self.queue_tree.configure(yscrollcommand=tree_scrollbar.set)

        self.queue_tree.pack(side=tk.LEFT, fill=tk.X, expand=True)
        tree_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.queue_tree.bind("<MouseWheel>", self._on_mousewheel)

        self.context_menu = tk.Menu(self.queue_tree, tearoff=0)
        self.context_menu.add_command(label="Zpracovat znovu", command=self.reprocess_selected_file)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Zrusit", command=lambda: None)

        self.queue_tree.bind("<Button-3>", self.show_context_menu)

        queue_btn_frame = tk.Frame(main_frame)
        queue_btn_frame.pack(fill=tk.X, pady=5)

        tk.Button(queue_btn_frame, text="Obnovit zobrazeni", command=self.refresh_queue_display, width=18).pack(side=tk.LEFT, padx=5)
        tk.Button(queue_btn_frame, text="Vymazat dokoncene", command=self.clear_completed, width=18).pack(side=tk.LEFT, padx=5)
        tk.Button(queue_btn_frame, text="Vymazat vse", command=self.clear_all_queue, width=18).pack(side=tk.LEFT, padx=5)

        # ----- Nastaveni -----
        settings_frame = tk.Frame(main_frame, relief=tk.RIDGE, borderwidth=2, padx=5, pady=5)
        settings_frame.pack(fill=tk.X, pady=(10, 0))

        tk.Label(settings_frame, text="NASTAVENI", font=("Arial", 10, "bold")).pack(anchor=tk.W)

        temp_frame = tk.Frame(settings_frame)
        temp_frame.pack(fill=tk.X, pady=2)
        tk.Label(temp_frame, text="Temp slozka:", width=20, anchor=tk.W).pack(side=tk.LEFT)
        self.temp_entry = tk.Entry(temp_frame)
        self.temp_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.temp_entry.insert(0, self.temp_folder)
        tk.Button(temp_frame, text="Vybrat", command=self.select_temp_folder, width=8).pack(side=tk.LEFT)

        output_frame = tk.Frame(settings_frame)
        output_frame.pack(fill=tk.X, pady=2)
        tk.Label(output_frame, text="Vystup TXT:", width=20, anchor=tk.W).pack(side=tk.LEFT)
        self.output_entry = tk.Entry(output_frame)
        self.output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        tk.Button(output_frame, text="Vybrat", command=self.select_output_file, width=8).pack(side=tk.LEFT)

        sample_frame = tk.Frame(settings_frame)
        sample_frame.pack(fill=tk.X, pady=4)
        tk.Label(sample_frame, text="Delka vzorku (s):", width=20, anchor=tk.W).pack(side=tk.LEFT)

        self.segment_length_var = tk.DoubleVar(value=self.queue_manager.get_segment_length_s())
        self.segment_length_spinbox = tk.Spinbox(
            sample_frame, from_=1, to=1000,
            textvariable=self.segment_length_var,
            width=6, font=("Arial", 10), increment=0.5,
            format="%.1f",
            command=self.on_segment_length_change
        )
        self.segment_length_spinbox.pack(side=tk.LEFT, padx=5)
        # Zachyceni rucniho zadani
        self.segment_length_spinbox.bind("<FocusOut>", lambda e: self.on_segment_length_change())
        self.segment_length_spinbox.bind("<Return>", lambda e: self.on_segment_length_change())

        tk.Label(sample_frame, text="(1-1000 s, vychozi 7 s)", font=("Arial", 8), fg="gray").pack(side=tk.LEFT, padx=5)

        step_frame = tk.Frame(settings_frame)
        step_frame.pack(fill=tk.X, pady=4)
        tk.Label(step_frame, text="Krok mezi vzorky (s):", width=20, anchor=tk.W).pack(side=tk.LEFT)

        self.step_var = tk.DoubleVar(value=self.queue_manager.get_step_s())
        self.step_spinbox = tk.Spinbox(
            step_frame, from_=1, to=1000,
            textvariable=self.step_var,
            width=6, font=("Arial", 10), increment=0.5,
            format="%.1f",
            command=self.on_step_change
        )
        self.step_spinbox.pack(side=tk.LEFT, padx=5)
        # Zachyceni rucniho zadani
        self.step_spinbox.bind("<FocusOut>", lambda e: self.on_step_change())
        self.step_spinbox.bind("<Return>", lambda e: self.on_step_change())

        tk.Label(step_frame, text="(1-1000 s, vychozi 3.5 s)", font=("Arial", 8), fg="gray").pack(side=tk.LEFT, padx=5)

        # ----- Log -----
        tk.Label(main_frame, text="LOG:", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(10, 0))

        self.log_text = scrolledtext.ScrolledText(main_frame, height=8)
        self.log_text.pack(fill=tk.X, pady=5)

        self.log_text.bind("<MouseWheel>", self._on_mousewheel)

        # Inicializace
        self.refresh_queue_display()
        self.update_statistics()
        self.start_countdown_update()

    # ----- Metody pro rolovatelny canvas -----
    def _on_inner_frame_configure(self, event):
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self._canvas.itemconfig(self._canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        self._canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    # ----- Pomocna metoda pro bezpecne nacteni int hodnoty ze Spinboxu -----
    def _read_int_spinbox(self, var, default, min_val, max_val):
        try:
            val = int(var.get())
            if val < min_val:
                val = min_val
            if val > max_val:
                val = max_val
            var.set(val)
            return val
        except (ValueError, tk.TclError):
            var.set(default)
            return default

    # ----- Pomocna metoda pro bezpecne nacteni float hodnoty ze Spinboxu -----
    def _read_float_spinbox(self, var, default, min_val, max_val):
        try:
            val = round(float(var.get()), 1)
            if val < min_val:
                val = min_val
            if val > max_val:
                val = max_val
            var.set(val)
            return val
        except (ValueError, tk.TclError):
            var.set(default)
            return default

    # ----- Ostatni metody -----
    def log(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update()

    def on_files_per_batch_change(self):
        new_count = self._read_int_spinbox(self.files_per_batch_var, 3, 1, 9999)
        self.queue_manager.set_files_per_batch(new_count)
        self.log("Pocet souboru na davku zmenen na: " + str(new_count))

    def on_interval_change(self):
        new_hours = self._read_int_spinbox(self.interval_hours_var, 24, 0, 168)
        new_minutes = self._read_int_spinbox(self.interval_minutes_var, 5, 0, 59)
        self.queue_manager.set_interval(new_hours, new_minutes)
        self.log("Casovy interval zmenen na: " + str(new_hours) + "h " + str(new_minutes) + "min")
        if self.timer_running:
            self.log("  (Zmena se projevi az pri dalsim spusteni casovace)")

    def on_segment_length_change(self):
        new_val = self._read_float_spinbox(self.segment_length_var, 7.0, 1.0, 1000.0)
        self.queue_manager.set_segment_length_s(new_val)
        self.log("Delka vzorku zmenena na: " + str(new_val) + " s")

    def on_step_change(self):
        new_val = self._read_float_spinbox(self.step_var, 3.5, 1.0, 1000.0)
        self.queue_manager.set_step_s(new_val)
        self.log("Krok mezi vzorky zmenen na: " + str(new_val) + " s")

    def add_files_to_queue(self):
        files = filedialog.askopenfilenames(
            title="Vyberte soubory pro pridani do fronty",
            filetypes=[("Audio soubory", "*.mxf *.wav *.mp3"), ("Vsechny soubory", "*.*")]
        )
        if files:
            self.queue_manager.add_files(files)
            self.refresh_queue_display()
            self.update_statistics()
            self.log("Pridano " + str(len(files)) + " souboru do fronty")

    def refresh_queue_display(self):
        for item in self.queue_tree.get_children():
            self.queue_tree.delete(item)

        for item in self.queue_manager.queue:
            status_text = {
                'waiting': 'Ceka',
                'processing': 'Zpracovava se',
                'completed': 'Hotovo',
                'error': 'Chyba',
                'no_audio': 'Bez audia',
                'no_music': 'Bez hudby',
                'no_recognition': 'Nerozpoznano'
            }.get(item['status'], item['status'])

            processed = item['processed_time'] if item['processed_time'] else '--'

            self.queue_tree.insert('', tk.END, values=(
                item['file_name'],
                status_text,
                item['added_time'],
                processed
            ))

    def update_statistics(self):
        stats = self.queue_manager.get_statistics()
        self.stats_waiting_label.config(text="Ceka: " + str(stats['waiting']))
        self.stats_processing_label.config(text="Zpracovava se: " + str(stats['processing']))
        self.stats_completed_label.config(text="Hotovo: " + str(stats['completed']))
        self.stats_error_label.config(text="Chyby: " + str(stats['error']))

    def clear_completed(self):
        if messagebox.askyesno("Vymazat dokoncene", "Opravdu chcete vymazat vsechny dokoncene soubory z fronty?"):
            new_queue = []
            for item in self.queue_manager.queue:
                if item['status'] not in ['completed', 'error', 'no_audio', 'no_music', 'no_recognition']:
                    new_queue.append(item)

            self.queue_manager.queue = new_queue
            self.queue_manager.save_queue()
            self.refresh_queue_display()
            self.update_statistics()
            self.log("Dokoncene polozky vymazany z fronty")

    def clear_all_queue(self):
        if messagebox.askyesno("Vymazat vse", "Opravdu chcete vymazat CELOU frontu?"):
            self.queue_manager.queue = []
            self.queue_manager.save_queue()
            self.refresh_queue_display()
            self.update_statistics()
            self.log("Fronta zcela vymazana")

    def show_context_menu(self, event):
        item = self.queue_tree.identify_row(event.y)
        if item:
            self.queue_tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def reprocess_selected_file(self):
        selection = self.queue_tree.selection()
        if not selection:
            return

        item_index = self.queue_tree.index(selection[0])

        if item_index < len(self.queue_manager.queue):
            file_item = self.queue_manager.queue[item_index]
            file_path = file_item['file_path']
            file_name = file_item['file_name']

            if messagebox.askyesno("Zpracovat znovu",
                                   "Chcete znovu zpracovat soubor:\n\n" + file_name + "\n\nSoubor bude vracen do fronty."):
                self.queue_manager.reset_file_status(file_path)
                self.refresh_queue_display()
                self.update_statistics()
                self.log("Soubor vracen do fronty: " + file_name)

    def stop_processing_cmd(self):
        global stop_processing
        if messagebox.askyesno("Zastavit zpracovani",
                               "Opravdu chcete zastavit zpracovani?\n\nAktualni soubor bude dokoncen a pak se zpracovani zastavi.\nVsechna dosud zpracovana data jsou ulozena."):
            stop_processing = True
            self.stop_processing_btn.config(state=tk.DISABLED)
            self.log("")
            self.log("!!! ZASTAVENI POZADOVANO !!!")
            self.log("Cekam na dokonceni aktualniho souboru...")

    def select_temp_folder(self):
        folder = filedialog.askdirectory(title="Vyberte slozku pro docasne WAV")
        if folder:
            self.temp_folder = folder
            self.temp_entry.delete(0, tk.END)
            self.temp_entry.insert(0, folder)

    def select_output_file(self):
        output_file = filedialog.asksaveasfilename(
            title="Ulozit vysledky",
            defaultextension=".txt",
            filetypes=[("Textovy soubor", "*.txt")]
        )
        if output_file:
            self.output_file = output_file
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, output_file)

    def start_timer(self):
        if not self.output_file:
            messagebox.showwarning("Chyba", "Nejprve nastavte vystupni TXT soubor!")
            return

        # Vynucene ulozeni vsech hodnot ze Spinboxu pred spustenim
        self.on_interval_change()
        self.on_files_per_batch_change()
        self.on_segment_length_change()
        self.on_step_change()

        self.timer_running = True
        self.timer_status_label.config(text="Casovac ZAPNUTY", fg="green")
        self.start_timer_btn.config(state=tk.DISABLED)
        self.stop_timer_btn.config(state=tk.NORMAL)

        # Nacteni hodnot primo ze Spinboxu (uz ulozene vyse)
        interval_hours = self._read_int_spinbox(self.interval_hours_var, 24, 0, 168)
        interval_minutes = self._read_int_spinbox(self.interval_minutes_var, 5, 0, 59)

        self.next_processing_time = datetime.now() + timedelta(hours=interval_hours, minutes=interval_minutes)

        self.log("=== CASOVAC SPUSTEN ===")
        self.log("Interval: " + str(interval_hours) + "h " + str(interval_minutes) + "min")
        self.log("Dalsi zpracovani: " + self.next_processing_time.strftime("%Y-%m-%d %H:%M:%S"))

        self.timer_thread = threading.Thread(target=self.timer_loop)
        self.timer_thread.daemon = True
        self.timer_thread.start()

    def stop_timer(self):
        if messagebox.askyesno("Zastavit casovac", "Opravdu chcete zastavit automaticky casovac?"):
            self.timer_running = False
            self.timer_status_label.config(text="Casovac VYPNUTY", fg="red")
            self.start_timer_btn.config(state=tk.NORMAL)
            self.stop_timer_btn.config(state=tk.DISABLED)
            self.next_processing_time = None
            self.log("=== CASOVAC ZASTAVEN ===")

    def timer_loop(self):
        while self.timer_running:
            if datetime.now() >= self.next_processing_time:
                self.execute_batch_processing()

                interval_hours = self.queue_manager.get_interval_hours()
                interval_minutes = self.queue_manager.get_interval_minutes()

                self.next_processing_time = datetime.now() + timedelta(hours=interval_hours, minutes=interval_minutes)
                self.log("Dalsi zpracovani naplanovano na: " + self.next_processing_time.strftime("%Y-%m-%d %H:%M:%S"))
                self.log("Interval: " + str(interval_hours) + "h " + str(interval_minutes) + "min")

            time.sleep(1)

    def start_countdown_update(self):
        def update():
            if self.timer_running and self.next_processing_time:
                remaining = self.next_processing_time - datetime.now()
                if remaining.total_seconds() > 0:
                    hours = int(remaining.total_seconds() // 3600)
                    minutes = int((remaining.total_seconds() % 3600) // 60)
                    seconds = int(remaining.total_seconds() % 60)
                    self.timer_countdown_label.config(
                        text="Dalsi zpracovani za: " + str(hours).zfill(2) + ":" + str(minutes).zfill(2) + ":" + str(seconds).zfill(2)
                    )
                else:
                    self.timer_countdown_label.config(text="Zpracovavam...")
            else:
                self.timer_countdown_label.config(text="Dalsi zpracovani za: --:--:--")

            self.root.after(1000, update)

        update()

    def process_now(self):
        if not self.output_file:
            messagebox.showwarning("Chyba", "Nejprve nastavte vystupni TXT soubor!")
            return

        # Vynucene ulozeni vsech hodnot ze Spinboxu pred spustenim
        self.on_files_per_batch_change()
        self.on_segment_length_change()
        self.on_step_change()

        files_count = self._read_int_spinbox(self.files_per_batch_var, 3, 1, 9999)
        if messagebox.askyesno("Zpracovat hned", "Chcete zpracovat " + str(files_count) + " soubory z fronty hned?"):
            self.execute_batch_processing()

    def execute_batch_processing(self):
        global stop_processing
        stop_processing = False

        files_count = self.queue_manager.get_files_per_batch()
        waiting_files = self.queue_manager.get_waiting_files(files_count)

        if len(waiting_files) == 0:
            self.log("=== FRONTA PRAZDNA ===")
            self.log("Zadne soubory k zpracovani. Pridejte soubory do fronty.")
            messagebox.showinfo("Fronta prazdna", "Nejsou zadne soubory k zpracovani.\n\nPridejte soubory do fronty.")
            return

        self.temp_folder = self.temp_entry.get()
        if not os.path.exists(self.temp_folder):
            os.makedirs(self.temp_folder)

        if not os.path.exists(self.output_file):
            with open(self.output_file, 'w', encoding='utf-8') as f:
                pass

        self.processing_thread = threading.Thread(target=self.process_batch_thread, args=(waiting_files,))
        self.processing_thread.daemon = True
        self.processing_thread.start()

    def process_batch_thread(self, files_to_process):
        global stop_processing

        self.stop_processing_btn.config(state=tk.NORMAL)
        self.process_now_btn.config(state=tk.DISABLED)

        seg_len = self.queue_manager.get_segment_length_s()
        step = self.queue_manager.get_step_s()

        self.log("")
        self.log("=== START DAVKOVEHO ZPRACOVANI ===")
        self.log("Zpracovavam " + str(len(files_to_process)) + " soubory")
        self.log("Vzorek: " + str(seg_len) + " s  |  Krok: " + str(step) + " s")
        self.log("")

        for file_item in files_to_process:
            if stop_processing:
                self.log("=== ZPRACOVANI PRERUSENO ===")
                break

            input_file = file_item['file_path']

            self.queue_manager.update_status(input_file, 'processing')
            self.refresh_queue_display()
            self.update_statistics()

            result_data = process_file(
                input_file,
                self.temp_folder,
                self.log,
                segment_length_s=seg_len,
                step_s=step
            )

            if result_data:
                status = result_data.get("status", "unknown")

                if status == "success":
                    self.queue_manager.update_status(input_file, 'completed', result_data)
                elif status in ["error", "no_audio", "no_music", "no_recognition"]:
                    self.queue_manager.update_status(input_file, status, result_data)
                else:
                    self.queue_manager.update_status(input_file, 'error', result_data)

                if write_result_to_file(self.output_file, os.path.basename(input_file), result_data):
                    self.log("  -> Ulozeno do TXT")
                else:
                    self.log("  -> CHYBA pri zapisu do TXT!")

            self.refresh_queue_display()
            self.update_statistics()
            self.log("")

        self.log("=== DAVKOVE ZPRACOVANI DOKONCENO ===")
        stats = self.queue_manager.get_statistics()
        self.log("Celkem ve fronte: " + str(stats['total']))
        self.log("Ceka: " + str(stats['waiting']) + " | Hotovo: " + str(stats['completed']) + " | Chyby: " + str(stats['error']))

        self.stop_processing_btn.config(state=tk.DISABLED)
        self.process_now_btn.config(state=tk.NORMAL)

# ----- Spusteni GUI -----
if __name__ == "__main__":
    root = tk.Tk()
    app = MusicRecognitionGUI(root)
    root.mainloop()
