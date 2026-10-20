#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reels Cropper GUI - hlavní aplikační rozhraní
"""

import tkinter as tk
import time
from tkinter import filedialog, messagebox, ttk
import cv2
from PIL import Image, ImageTk
import numpy as np
from pathlib import Path

from keyframe_manager import KeyframeManager
from video_player import VideoPlayer
from export_manager import ExportManager
from scene_detector import SceneDetector
from face_detector import FaceDetector

# Auto-disable debug in EXE builds (detects missing console)
import sys
DEBUG = False  # ✅ VYPNUTO and sys.stdout is not None and not getattr(sys, 'frozen', False)
DEBUG_RIGHT_CLICK = True  # Debug pravého tlačítka

class ReelsCropperGUI:
    def on_mouse_wheel(self, event):
        """Scroll kolečkem myši po 4 framech, se Shift = 10 frameů"""
        if self.video_player.cap is None:
            return

        # Posun: 10 frameů pokud je Shift drženej, jinak 4
        shift_pressed = (event.state & 0x0001) != 0  # Shift maska na Windows
        step = 10 if shift_pressed else 1

        delta = step if getattr(event, 'delta', 1) > 0 else -step
        new_frame = min(max(0, self.video_player.current_frame + delta),
                        self.video_player.total_frames - 1)

        self.time_slider.set(new_frame)
        self.video_player.seek_frame(new_frame)
        self.update_frame_display()

    def show_random_joke(self):
        """Easter egg - náhodný vtip"""
        import random
        jokes = [
            "Proč programátoři pletou Halloween a Vánoce?\nProtože Oct 31 == Dec 25! ",
            "Jak programátor opraví rozbité světlo?\nNevypíná, vypne a zapne celý dům! ",
            "Proč Python programátoři nosí brýle?\nProtože nevidí C#! ",
            "Co dělá keyframe když je smutný?\nInterpoluje se do lepší nálady! 🎬",
            "Jak se říká videu, které běží pozpátku?\nOediv! "
        ]
        joke = random.choice(jokes)
        messagebox.showinfo("🎉 Easter Egg!", joke)

    """Main GUI application"""

    
    def show_random_joke(self):
        """Easter egg - náhodný vtip"""
        import random
        jokes = [
			"Co dělá klávesnice, když se bojí? Tlačí na Escape.",
			"Jak programátor opraví světlo? Vypne a zapne celý dům.",
			"Proč si programátoři pletou Vánoce a Halloween? Oct 31 = Dec 25.",
			"Jaký je oblíbený hudební nástroj programátora? Klávesnice.",
			"Co dělá keyframe, když je smutný? Interpoluje do lepší nálady.",
			"Jak programátor pozná, že je zima? Celý den debugguje.",
			"Proč programátoři nemohou lhát? Vždy vrací True.",
			"Co řekl bit 0 bitu 1? \"Máš bit pravdu.\"",
			"Jak se programátor učí angličtinu? Překládá error messages.",
			"Proč programátor nenosí hodinky? Čas je relativní.",
			"Co řekl nula osmičce? Hezký pásek!",
			"Proč si počítač nemůže dát čaj? Protože se bojí virů.",
			"Proč kuře přešlo silnici? Aby se dostalo na druhou stranu.",
			"Proč nemůže hvězda jít na diskotéku? Protože příliš září.",
			"Co řekla jedna zeď druhé? Uvidíme se na rohu.",
			"Jak se jmenuje pes kouzelníka? Labracadabrador.",
			"Proč banán šel k doktorovi? Protože nebyl dobře oloupaný.",
			"Jak se říká kočce na internetu? Memeow.",
			"Co řekla hvězda, když byla ohromena? Ty mě gravituj!"
			"Proč nemaj programátoři rádi přirodu? Protože má mnoho much.",
			"What do you call a programmer who swims? Python in the pool.",
			"What does a keyboard do when it's scared? It presses Escape.",
			"How does a programmer fix the light? Turns the whole house off and on.",
			"Why do programmers confuse Christmas and Halloween? Because Oct 31 == Dec 25.",
			"Why does the Pythonista go fishing? Looking for import fish.",
			"What's a programmer's favorite musical instrument? The keyboard.",
			"What did the HTML tag say to CSS? 'Leave me alone, I have my own style.'",
			"Why can't databases dance? They don't have a JOIN.",
			"What's a programmer's favorite sport? Sprinting in a for-loop.",
			"Why do programmers like fishing? Catching pointers.",
			"What does a keyframe do when it's sad? Interpolates to a better mood.",
			"How does a programmer know it's cold? Debugging all day.",
			"Why can't programmers lie? They always return True.",
			"How does a Pythonista apologize? Sorry, it was badly indented.",
			"What did bit 0 say to bit 1? 'You're right.'",
			"Why is JavaScript sad? Because it has many undefineds.",
			"How does a programmer learn English? By translating error messages.",
			"Why don't programmers wear watches? Time is relative.",
			"Why can't a skeleton play piano? It has no nerves.",
			"What do you call a blind dinosaur? Do-you-think-he-saurus.",
			"What did zero say to eight? Nice belt!",
			"Why can't a computer have tea? It’s afraid of viruses.",
			"What's a ghost's favorite sport? Baseball, because they haunt the bases.",
			"What does a fish do in the library? Reads water stories.",
			"Why was the school desk having a sad day? Overloaded with homework.",
			"What's a mathematician's favorite drink? Piña colada.",
			"Why did the chicken cross the road? To get to the other side.",
			"What do you call a sloth on the internet? Slow-fi.",
			"Why can't a star go to a disco? Because it's too bright.",
			"What did one wall say to the other? See you at the corner.",
			"What do you call a magician's dog? Labracadabrador.",
			"What is invisible and insanely fast? Ghost runner.",
			"Why did the banana go to the doctor? Because it wasn't peeled properly.",
			"What do you call a bear that plays piano? Beary Jackson.",
			"What does an ant do when it falls into tea? Ant-icipation.",
			"Why does a spider make websites? It's their job.",
			"What do you call a cat online? Memeow.",
			"What did the star say when it was attracted? You gravitate me!"
        ]
        joke = random.choice(jokes)
        messagebox.showinfo("🎉 Easter Egg!", joke)
    
    def __init__(self, root):
        self.root = root
        self.root.title("16:9 to 9:16 Video Crop for Shorts, Reels, Tik Tok By Jan Cervenak 2025")
        self.root.geometry("1070x650")  # ✅ OPRAVENO: Menší okno pro 1366x768
        
        # DEBUG flag pro auto-edit
        self.debug_auto_edit = True
        
        # Components
        self.video_player = VideoPlayer()
        self.keyframe_manager = KeyframeManager()
        
        # GUI state
        self.canvas_width = 480   # ✅ OPRAVENO: 50% menší (bylo 960)
        self.canvas_height = 270  # ✅ OPRAVENO: 50% menší (bylo 540)
        self.scale_factor = 1.0
        self.dragging = False
        
        # DEBUG: Pravé tlačítko pro timeline scrubbing
        self.time_dragging = False
        self.time_drag_start_x = 0
        self.time_drag_start_frame = 0
        self.time_drag_sensitivity = 3  # pixelů na 1 frame
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.crop_start_x = 0
        self.crop_start_y = 0
        
        self.current_image = None
        
        # Undo/Redo system
        self.undo_stack = []  # [(keyframes_copy, description), ...]
        self.redo_stack = []
        self.max_undo_steps = 50
        
        
        # Playback state
        self.playing = False
        self.play_timer = None
        
        # Selection control flag
        self.user_manual_selection = False  # True = user ručně vybral KF, neměnit!
        
        # Timing pro realtime playback
        self.frame_times = []  # měření rychlosti
        self.target_delay = 40  # ms mezi framy (25fps)
        
        self._build_gui()
        
    def _build_gui(self):
        """Build GUI layout"""
        
        # Top toolbar
        toolbar = tk.Frame(self.root, relief=tk.RAISED, borderwidth=2)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        # POŘADÍ ZLEVA: Load, Export, Play, Add KF, Add Animated, Debug, Clear All, Easter Egg
        tk.Button(toolbar, text="Load Video", command=self.load_video, 
                 width=9, bg="#FF9800", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Button(toolbar, text="Export MP4", command=self.export_video,
                 width=9, bg="#4CAF50", fg="white").pack(side=tk.LEFT, padx=5)
        
        # Playback controls
        self.play_button = tk.Button(toolbar, text="Play", command=self.toggle_play,
                                      width=6, bg="#2196F3", fg="white", font=("Arial", 10, "bold"))
        self.play_button.pack(side=tk.LEFT, padx=5)
        
        tk.Button(toolbar, text="Add KF", command=self.add_keyframe,
                 width=6).pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar, text="Add Animated KF", command=self.add_animated_keyframe,
                 width=14).pack(side=tk.LEFT, padx=2)
        
        # Checkbox pro automatické animované KF
        self.auto_animated_var = tk.BooleanVar(value=False)
        auto_anim_check = tk.Checkbutton(toolbar, text="Add Animated KF", 
                                         variable=self.auto_animated_var,
                                         font=("Arial", 9))
        auto_anim_check.pack(side=tk.LEFT, padx=5)
        
        # Tooltip (simulace - zobrazí se ve status baru při hover)
        def show_tooltip(e):
            self.status_label.config(text="Auto Animated: Drag vytvari/upravi LINEAR keyframes (plynule animace)")
        def hide_tooltip(e):
            self.status_label.config(text="Ready")
        
        auto_anim_check.bind("<Enter>", show_tooltip)
        auto_anim_check.bind("<Leave>", hide_tooltip)
        tk.Button(toolbar, text="Debug", command=self.export_video_debug,
                 width=3).pack(side=tk.LEFT, padx=5)
        tk.Button(toolbar, text="Clear All KF", command=self.clear_keyframes,
                 width=8, bg="#f44336", fg="white").pack(side=tk.LEFT, padx=5)
        
        # Easter Egg - vtipek!
        tk.Button(toolbar, text="Vtip za stovku!", command=self.show_random_joke,
                 width=12, bg="#FFC107").pack(side=tk.LEFT, padx=2)

        # Auto Detect Cuts
        tk.Label(toolbar, text="Citlivost:", font=("Arial", 9)).pack(side=tk.LEFT, padx=(10, 2))
        
        self.threshold_var = tk.StringVar(value="15")
        threshold_entry = tk.Entry(toolbar, textvariable=self.threshold_var, width=5, font=("Arial", 10))
        threshold_entry.pack(side=tk.LEFT, padx=2)
        
        tk.Button(toolbar, text="Auto Detect Cuts", command=self.auto_detect_cuts,
                 width=12, bg="#9C27B0", fg="white").pack(side=tk.LEFT, padx=2)
        
        # Checkbox pro centrování na obličej
        self.center_face_var = tk.BooleanVar(value=True)
        tk.Checkbutton(toolbar, text="HAAR Face detect", 
                      variable=self.center_face_var).pack(side=tk.LEFT, padx=2)
        
        # Checkbox pro DNN detekci (přesnější, pomalejší)
        self.use_dnn_var = tk.BooleanVar(value=True)
        tk.Checkbutton(toolbar, text="DNN Face detect", 
                      variable=self.use_dnn_var).pack(side=tk.LEFT, padx=2)
        
        # Info label
        self.info_label = tk.Label(toolbar, text="No video loaded", 
                                   fg="gray")
        self.info_label.pack(side=tk.RIGHT, padx=10)
        
        # Main content area
        content = tk.Frame(self.root)
        content.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left side - Video canvas
        left_frame = tk.Frame(content)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        tk.Label(left_frame, text="Video Preview (tažení rámečku hned ukládá pozici)",
                font=("Arial", 10, "bold")).pack(pady=5)
        
        # Canvas for video
        self.canvas = tk.Canvas(left_frame, width=self.canvas_width, 
                               height=self.canvas_height, bg='black')
        self.canvas.pack(padx=5, pady=5)
        
        # Bind mouse events
        self.canvas.bind('<Button-1>', self.on_canvas_click)
        self.canvas.bind('<Double-Button-1>', self.on_canvas_double_click)
        self.canvas.bind('<B1-Motion>', self.on_canvas_drag)
        self.canvas.bind('<ButtonRelease-1>', self.on_canvas_release)
        self.canvas.bind('<MouseWheel>', self.on_mouse_wheel)
        self.canvas.bind('<Double-Button-3>', self.on_canvas_double_click_right)  # RIGHT DOUBLE CLICK -> Add Animated KF
        self.canvas.bind('<Button-4>', self.on_mouse_wheel)
        self.canvas.bind('<Button-5>', self.on_mouse_wheel)        
        # DEBUG: Pravé tlačítko pro timeline scrubbing
        self.canvas.bind('<Button-3>', self.on_right_click_debug)
        self.canvas.bind('<B3-Motion>', self.on_right_drag_debug)
        self.canvas.bind('<ButtonRelease-3>', self.on_right_release_debug)

        
        # Bind keyboard events (sipky pro navigaci)
        self.root.bind('<Left>', self.on_key_left)
        self.root.bind('<Right>', self.on_key_right)
        self.root.bind('<Shift-Left>', self.on_key_shift_left)
        self.root.bind('<Shift-Right>', self.on_key_shift_right)
        
        # Klávesové zkratky (nové)
        self.root.bind_all('<space>', lambda e: self.toggle_play())
        self.root.bind_all('<p>', lambda e: self.toggle_play())
        self.root.bind('<k>', lambda e: self.add_keyframe())
        self.root.bind('<K>', lambda e: self.add_keyframe())
        self.root.bind('<l>', lambda e: self.add_animated_keyframe())
        self.root.bind('<L>', lambda e: self.add_animated_keyframe())
        self.root.bind('<BackSpace>', lambda e: self.delete_keyframe())
        self.root.bind('<Home>', lambda e: self.jump_to_start())
        self.root.bind('<End>', lambda e: self.jump_to_end())
        self.root.bind('<Control-z>', lambda e: self.undo())
        self.root.bind('<Control-y>', lambda e: self.redo())
        self.root.bind('<Control-Z>', lambda e: self.redo())  # Shift+Ctrl+Z
        
        
        # Position display
        pos_frame = tk.Frame(left_frame)
        pos_frame.pack(pady=5)
        tk.Label(pos_frame, text="Crop Position:").pack(side=tk.LEFT, padx=5)
        self.pos_label = tk.Label(pos_frame, text="X: 0, Y: 0", 
                                 font=("Courier", 10))
        self.pos_label.pack(side=tk.LEFT, padx=5)
        
        # Timeline
        timeline_frame = tk.Frame(left_frame)
        timeline_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(timeline_frame, text="Timeline:").pack(anchor=tk.W)
        
        slider_frame = tk.Frame(timeline_frame)
        slider_frame.pack(fill=tk.X, pady=5)
        
        self.time_slider = tk.Scale(slider_frame, from_=0, to=100,
                                    orient=tk.HORIZONTAL,
                                    command=self.on_slider_change,
                                    showvalue=0)
        self.time_slider.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Timeline markers canvas (POD sliderem)
        markers_frame = tk.Frame(timeline_frame)
        markers_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.timeline_canvas = tk.Canvas(markers_frame, height=25, bg='#f0f0f0', highlightthickness=0)
        self.timeline_canvas.pack(fill=tk.X, expand=True)
        self.timeline_canvas.bind('<Button-1>', self.on_timeline_marker_click)
        

        # --- Help text pod timeline ---
        self.help_label = tk.Label(left_frame, text='''Ovládání:
- Po "Load Video" klikni na "Auto Detect Cuts" program do tabulky KF rozstříhá většinu záběrů a detekuje většinu obličejů.
- Posuvník // šipky vpravo / vlevo // PRAVÉ tlačítko myši tažení po obraze vpravo / vlevo: přesun v čase vpřed / vzad
- Pomocí šipek nahoru / dolů // klikání v seznamu procházej střihy a upravuj kompozici.
- Shift + šipky: přesun o 10 framů /// Kolečko myši: posun o 1 frame /// Shift + kolečko: přesun o 10 framů
- LEVÝ Dvojklik na video / Tlačítko "Add KF" : přidání STEP keyframe (modrá tečka na timeline)
- PRAVÝ Dvojklik  na video / Tlačítko "Add Animated KF": přidání animovaného keyframe (zelená tečka na timeline)
  Jak na ANIMACE: První je přidání klasického (STEP) KF na začátku obrazu. 
  Na konci pohybu (objektu) člověka v rámci stejného obrazu přidej ANIMATED KF.'''
,
                                   justify=tk.LEFT, font=("Arial", 9), fg="gray")
        self.help_label.pack(pady=5, anchor="w")
        
        # Časový label pod timeline vpravo
        time_display_frame = tk.Frame(timeline_frame)
        time_display_frame.pack(fill=tk.X, pady=2)
        
        tk.Label(time_display_frame, text="Čas (MM:SS:FF):", 
                font=("Arial", 9)).pack(side=tk.LEFT, padx=5)
        
        self.time_label = tk.Label(time_display_frame, text="00:00:00 / 00:00:00",
                                   font=("Courier", 10, "bold"), fg="#2196F3")
        self.time_label.pack(side=tk.RIGHT, padx=5)
        
        # Right side - Keyframes list
        right_frame = tk.Frame(content, width=500)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=5)
        
        tk.Label(right_frame, text="Keyframes", 
                font=("Arial", 12, "bold")).pack(pady=5)
        
        # Keyframes listbox
        listbox_frame = tk.Frame(right_frame)
        listbox_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(listbox_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.keyframe_listbox = tk.Listbox(listbox_frame, width=60, 
                                           yscrollcommand=scrollbar.set,
                                           font=("Courier", 9),
                                           selectmode=tk.EXTENDED)  # SHIFT/CTRL multi-select
        self.keyframe_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        # Auto-goto keyframe on click
        self.keyframe_listbox.bind('<ButtonRelease-1>', lambda e: self.goto_keyframe())
        # Arrow keys navigation with auto-preview
        self.keyframe_listbox.bind('<Up>', lambda e: self.root.after(10, self.goto_keyframe))
        self.keyframe_listbox.bind('<Down>', lambda e: self.root.after(10, self.goto_keyframe))
        self.keyframe_listbox.bind('<Delete>', lambda e: self.delete_keyframe())  # DELETE key support
        scrollbar.config(command=self.keyframe_listbox.yview)
        
        # Keyframe controls
        kf_controls = tk.Frame(right_frame)
        kf_controls.pack(fill=tk.X, pady=5)
        
        tk.Button(kf_controls, text="Go To", 
                 command=self.goto_keyframe).pack(fill=tk.X, pady=2)
        tk.Button(kf_controls, text="Delete", 
                 command=self.delete_keyframe).pack(fill=tk.X, pady=2)
        
        # Status bar
        self.status_label = tk.Label(self.root, text="Ready", 
                                     relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)
    
    def load_video(self):
        """Load video file"""
        filepath = filedialog.askopenfilename(
            title="Select Video File",
            filetypes=[
                ("Video files", "*.mp4 *.mov *.avi *.mkv *.mxf"),
                ("All files", "*.*")
            ]
        )
        
        if not filepath:
            return
        
        self.status_label.config(text="Loading video...")
        self.root.update()
        
        if self.video_player.load_video(filepath):
            info = self.video_player.get_video_info()
            
            # Update info
            self.info_label.config(
                text=f"{info['width']}x{info['height']} | {info['fps']:.1f}fps | {info['duration']:.1f}s"
            )
            
            # Update timeline
            self.time_slider.config(to=info['total_frames'] - 1)
            self.time_slider.set(0)
            
            # Calculate scale factor for canvas
            self.scale_factor = min(
                self.canvas_width / info['width'],
                self.canvas_height / info['height']
            )
            
            # Update display
            self.update_frame_display()
            self.update_keyframe_list()
            
            # 🔍 DEBUG: Slider check po load_video
            print("\n" + "="*60)
            print("🔍 DEBUG: load_video() DONE")
            print("="*60)
            print(f"   Slider value: {self.time_slider.get()}")
            print(f"   Current frame: {self.video_player.current_frame}")
            print(f"   Total frames: {self.video_player.total_frames}")
            print("="*60 + "\n")
            
            self.status_label.config(
                text=f"Loaded: {Path(filepath).name}"
            )
        else:
            messagebox.showerror("Error", "Failed to load video")
            self.status_label.config(text="Error loading video")
    
    def on_slider_change(self, value):
        """Handle timeline slider change (OPTIMIZED)"""
        if self.video_player.cap is None:
            return
        
        frame_num = int(float(value))
        
        # ✅ OPTIMIZATION: Ignoruj změny při draggingu NEBO playbacku
        if self.dragging or self.playing:
            return
        
        # Reset selection lock
        self.user_manual_selection = False
        
        self.video_player.seek_frame(frame_num)
        self.update_frame_display()
    
    def update_frame_display(self):
        """Update video canvas with current frame (OPTIMIZED for playback)"""
        if self.video_player.cap is None:
            return
        
        # ✅ OPTIMIZATION: Při playbacku skip interpolaci (použij cached pozici)
        if self.playing:
            crop_x = self.video_player.crop_x
            crop_y = self.video_player.crop_y
        elif self.dragging:
            # Při draggingu použij aktuální pozici přímo
            crop_x = self.video_player.crop_x
            crop_y = self.video_player.crop_y
        else:
            # Normální režim - použij interpolaci z keyframes
            default_pos = (self.video_player.crop_x, self.video_player.crop_y)
            crop_x, crop_y = self.keyframe_manager.get_position_at_frame(
                self.video_player.current_frame, default_pos
            )
            
            # Update current position
            self.video_player.crop_x = crop_x
            self.video_player.crop_y = crop_y
        
        # Get frame with overlay
        frame = self.video_player.get_frame_with_overlay(crop_x, crop_y)
        
        if frame is None:
            return
        
        # Resize for canvas
        scaled_width = int(self.video_player.width * self.scale_factor)
        scaled_height = int(self.video_player.height * self.scale_factor)
        
        frame_resized = cv2.resize(frame, (scaled_width, scaled_height))
        
        # Convert to PIL Image
        img = Image.fromarray(frame_resized)
        self.current_image = ImageTk.PhotoImage(image=img)
        
        # Display on canvas
        self.canvas.delete("all")
        self.canvas.create_image(
            self.canvas_width // 2, 
            self.canvas_height // 2,
            image=self.current_image
        )
        
        # Update labels
        self.update_position_label()
        self.update_time_label()
        
        # Auto-highlight nejbližší keyframe v tabulce (jen pokud NENÍ playback)
        if not self.playing:
            self._highlight_nearest_keyframe(self.video_player.current_frame)

    def update_frame_display_static(self):
        """Update frame display without seeking video (for dragging)"""
        if self.video_player.cap is None:
            return
        
        # ✅ NOVÁ FUNKCE: Jen překreslí overlay, NESEEKUJE video
        crop_x = self.video_player.crop_x
        crop_y = self.video_player.crop_y
        
        # Get frame with overlay (používá CACHED frame)
        frame = self.video_player.get_frame_with_overlay(crop_x, crop_y)
        
        if frame is None:
            return
        
        # Resize for canvas
        scaled_width = int(self.video_player.width * self.scale_factor)
        scaled_height = int(self.video_player.height * self.scale_factor)
        
        frame_resized = cv2.resize(frame, (scaled_width, scaled_height))
        
        # Convert to PIL Image
        img = Image.fromarray(frame_resized)
        self.current_image = ImageTk.PhotoImage(image=img)
        
        # Display on canvas
        self.canvas.delete("all")
        self.canvas.create_image(
            self.canvas_width // 2, 
            self.canvas_height // 2,
            image=self.current_image
        )
        
        # Update labels
        self.update_position_label()
        # ✅ NEPŘEKRESLUJEME čas - zůstává stejný
    
    def update_position_label(self):
        """Update crop position label with KF info"""
        base_text = f"X: {self.video_player.crop_x}, Y: {self.video_player.crop_y}"
        
        # Pridej info o aktivnim KF
        if self.video_player.cap is not None:
            active_kf = self._get_active_keyframe()
            if active_kf:
                kf_frame, _, _, mode = active_kf
                mode_label = "STEP" if mode == "step" else "ANIM"
                base_text += f"  |  [KF #{kf_frame} {mode_label}]"
            else:
                base_text += f"  |  [Pred prvnim KF]"
        
        self.pos_label.config(text=base_text)
    
    def update_time_label(self):
        """Update time label with frame numbers"""
        if self.video_player.cap is None:
            return
        
        current_time = self.video_player.current_frame / self.video_player.fps
        total_time = self.video_player.duration
        current_frame = self.video_player.current_frame
        total_frames = self.video_player.total_frames
        
        self.time_label.config(
            text=f"{self._format_time(current_time)} / {self._format_time(total_time)}  |  Frame: {current_frame} / {total_frames}"
        )
    
    def update_frame_display_cached(self):
        """FIX V2: Update display při draggingu - používá cached frame"""
        if self.video_player.cap is None:
            return
        
        # Použij cached frame (NESEEKUJ video!)
        frame = self.video_player.get_frame_with_overlay(
            self.video_player.crop_x, 
            self.video_player.crop_y,
            use_cache=True  # <-- KLÍČOVÁ ZMĚNA
        )
        
        if frame is None:
            return
        
        # Resize for canvas
        scaled_width = int(self.video_player.width * self.scale_factor)
        scaled_height = int(self.video_player.height * self.scale_factor)
        
        frame_resized = cv2.resize(frame, (scaled_width, scaled_height))
        
        # Convert to PIL Image
        img = Image.fromarray(frame_resized)
        self.current_image = ImageTk.PhotoImage(image=img)
        
        # Display on canvas
        self.canvas.delete("all")
        self.canvas.create_image(
            self.canvas_width // 2, 
            self.canvas_height // 2,
            image=self.current_image
        )
        
        # Update position label only
        self.update_position_label()
        
        # ✅ FIX: Update highlight i při cached display (eliminuje blikání)
        if self.video_player.cap is not None:
            self._highlight_nearest_keyframe(self.video_player.current_frame)
    
    def _format_time(self, seconds):
        """Format seconds to MM:SS:FF"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        frames = int((seconds % 1) * self.video_player.fps) if self.video_player.fps > 0 else 0
        return f"{minutes:02d}:{secs:02d}:{frames:02d}"
    

    def debug_right_click(self, event, action):
        """DEBUG: Výpis info o pravém tlačítku"""
        if not DEBUG_RIGHT_CLICK:
            return
        
        print("\n" + "="*60)
        print(f"🖱️  DEBUG RIGHT CLICK: {action}")
        print("="*60)
        print(f"   Event X: {event.x}, Y: {event.y}")
        
        if self.video_player.cap:
            print(f"   Frame: {self.video_player.current_frame}/{self.video_player.total_frames}")
        
        if action == "DRAG":
            delta_x = event.x - self.time_drag_start_x
            frames_delta = int(delta_x / self.time_drag_sensitivity)
            new_frame = self.time_drag_start_frame + frames_delta
            
            print(f"   Delta X: {delta_x} px → {frames_delta} frames")
            print(f"   Sensitivity: {self.time_drag_sensitivity} px/frame")
            print(f"   New frame: {new_frame}")
        
        print("="*60)

    def on_canvas_click(self, event):
        """Handle canvas click"""
        if self.video_player.cap is None:
            return
        
        # Convert canvas coords to video coords
        video_x = event.x / self.scale_factor
        video_y = event.y / self.scale_factor
        
        # Check if click is inside crop box
        crop_x = self.video_player.crop_x
        crop_y = self.video_player.crop_y
        crop_w = self.video_player.crop_width
        crop_h = self.video_player.crop_height
        
        if (crop_x <= video_x <= crop_x + crop_w and
            crop_y <= video_y <= crop_y + crop_h):
            # ✅ OPRAVENO: Nastavíme dragging flag PŘED jakýmkoli update
            self.dragging = True
            self.drag_start_x = video_x
            self.drag_start_y = video_y
            self.crop_start_x = crop_x
            self.crop_start_y = crop_y
    
    def on_canvas_drag(self, event):
        """Handle canvas drag"""
        if not self.dragging:
            return
        
        
        # Calculate new position
        video_x = event.x / self.scale_factor
        video_y = event.y / self.scale_factor
        
        delta_x = video_x - self.drag_start_x
        delta_y = video_y - self.drag_start_y
        
        new_x = self.crop_start_x + delta_x
        new_y = self.crop_start_y + delta_y
        
        # Clamp to video bounds
        new_x = max(0, min(new_x, 
                          self.video_player.width - self.video_player.crop_width))
        new_y = max(0, min(new_y,
                          self.video_player.height - self.video_player.crop_height))
        
        # Update position
        self.video_player.crop_x = int(new_x)
        self.video_player.crop_y = int(new_y)
        
        # ✅ OPRAVENO: Aktualizuj jen frame display, NE seek videa
        self.update_frame_display_cached()
    
    def on_canvas_release(self, event):
        """Handle canvas release - AUTO-EDIT keyframes (PATCHED V4 - SELECT FIX)"""
        print("\n" + "="*60)
        print("🖱️ DEBUG: on_canvas_release() START")
        print("="*60)
        
        if not self.dragging:
            print("   ⏭️ SKIP: not dragging")
            print("="*60 + "\n")
            return
        
        self.dragging = False
        
        if self.video_player.cap is None:
            print("   ⏭️ SKIP: no video")
            print("="*60 + "\n")
            return
        
        current_frame = self.video_player.current_frame
        new_x = self.video_player.crop_x
        new_y = self.video_player.crop_y
        
        # DEBUG
        if self.debug_auto_edit:
            print("\n" + "="*60)
            print("[AUTO-EDIT] DRAG RELEASE CHECK (PATCHED V4)")
            print("="*60)
            print(f"   Current frame: {current_frame}")
            print(f"   Crop position: X={new_x}, Y={new_y}")
            print(f"   Existující KF: {list(self.keyframe_manager.keyframes.keys())}")
            print(f"   Auto Animated checkbox: {self.auto_animated_var.get()}")
        
        # 🆕 KONTROLA: Jsem PŘESNĚ na existujícím KF?
        if current_frame in self.keyframe_manager.keyframes:
            self._save_undo_state(f"Update KF #{current_frame}")
            # ✅ ÚPRAVA existujícího KF (vždy!)
            old_data = self.keyframe_manager.keyframes[current_frame]
            old_x, old_y, old_mode = old_data
            
            # Zjisti nový mode podle checkboxu (nebo zachovej původní)
            new_mode = "linear" if self.auto_animated_var.get() else old_mode
            
            # Aktualizuj KF
            self.keyframe_manager.add_keyframe(current_frame, new_x, new_y, mode=new_mode)
            self.update_keyframe_list()
            
            # 🆕 ZACHOVEJ VÝBĚR v tabulce
            self._select_keyframe_by_frame(current_frame)
            
            # Status feedback
            mode_label = "LINEAR" if new_mode == "linear" else "STEP"
            self.status_label.config(
                text=f"[UPRAVA] KF #{current_frame} [{mode_label}] upraven: X {old_x}→{new_x}, Y {old_y}→{new_y}"
            )
            
            if self.debug_auto_edit:
                print(f"   ✅ [UPRAVA] KF #{current_frame} upraven")
                print(f"      X: {old_x} → {new_x}")
                print(f"      Y: {old_y} → {new_y}")
                print(f"      Mode: {old_mode} → {new_mode}")
        
        else:
            # Mezi KF - záleží na checkboxu
            if self.auto_animated_var.get():
                # ☑ CHECKBOX ZAPNUTÝ → VYTVOŘ nový LINEAR KF (animace!)
                mode = "linear"
                
                self._save_undo_state(f"New LINEAR KF #{current_frame}")
                
                self.keyframe_manager.add_keyframe(current_frame, new_x, new_y, mode=mode)
                self.update_keyframe_list()
                
                # Auto-select nově přidaný keyframe
                self._select_keyframe_by_frame(current_frame)
                
                # Status feedback
                self.status_label.config(
                    text=f"[NOVY LINEAR] KF #{current_frame} vytvořen: X={new_x}, Y={new_y} (animace!)"
                )
                
                if self.debug_auto_edit:
                    print(f"   ✅ [NOVY LINEAR] KF #{current_frame} vytvořen (animace)")
                    print(f"      X={new_x}, Y={new_y}")
                    print(f"      Mode: linear")
            
            else:
                # ☐ CHECKBOX VYPNUTÝ → UPRAV předchozí KF (STEP zóna)
                active_kf = self._get_active_keyframe()
                
                if active_kf:
                    # Existuje předchozí KF → uprav ho
                    kf_frame, old_x, old_y, old_mode = active_kf
                    
                    # Zachovej původní mode (STEP zóna)
                    self.keyframe_manager.add_keyframe(kf_frame, new_x, new_y, mode=old_mode)
                    self.update_keyframe_list()
                    
                    # 🆕 ZACHOVEJ VÝBĚR upraveného KF
                    self._select_keyframe_by_frame(kf_frame)
                    
                    # Status feedback
                    mode_label = "LINEAR" if old_mode == "linear" else "STEP"
                    self.status_label.config(
                        text=f"[UPRAVA ZÓNY] KF #{kf_frame} [{mode_label}] upraven: X {old_x}→{new_x}, Y {old_y}→{new_y}"
                    )
                    
                    if self.debug_auto_edit:
                        print(f"   ✅ [UPRAVA ZÓNY] KF #{kf_frame} upraven (STEP zóna)")
                        print(f"      Current frame: {current_frame} → upravuje KF #{kf_frame}")
                        print(f"      X: {old_x} → {new_x}")
                        print(f"      Y: {old_y} → {new_y}")
                        print(f"      Mode zachován: {old_mode}")
                
                else:
                    # Žádný předchozí KF → vytvoř KF #0
                    mode = "step"
                    
                    self.keyframe_manager.add_keyframe(0, new_x, new_y, mode=mode)
                    self.update_keyframe_list()
                    
                    # Auto-select nově přidaný keyframe
                    self._select_keyframe_by_frame(0)
                    
                    # Status feedback
                    self.status_label.config(
                        text=f"[NOVY] KF #0 [STEP] vytvořen (začátek videa): X={new_x}, Y={new_y}"
                    )
                    
                    if self.debug_auto_edit:
                        print(f"   ✅ [NOVY] KF #0 vytvořen (před prvním KF)")
                        print(f"      X={new_x}, Y={new_y}")
                        print(f"      Mode: step")
        
        if self.debug_auto_edit:
            print("="*60 + "\n")
    
    def add_keyframe(self):
        """Add STEP keyframe at current position"""
        if self.video_player.cap is None:
            messagebox.showwarning("Warning", "No video loaded")
            return
        
        frame_num = self.video_player.current_frame
        self._save_undo_state(f"Add STEP KF #{frame_num}")
        x = self.video_player.crop_x
        y = self.video_player.crop_y
        
        self.keyframe_manager.add_keyframe(frame_num, x, y, mode="step")
        self.update_keyframe_list()
        
        # Auto-select nově přidaný keyframe
        self._select_keyframe_by_frame(frame_num)
        
        self.status_label.config(
            text=f"Keyframe [STEP] added at frame {frame_num}"
        )
    
    def add_animated_keyframe(self):
        """Add LINEAR (animated) keyframe at current position"""
        if self.video_player.cap is None:
            messagebox.showwarning("Warning", "No video loaded")
            return
        
        frame_num = self.video_player.current_frame
        self._save_undo_state(f"Add LINEAR KF #{frame_num}")
        x = self.video_player.crop_x
        y = self.video_player.crop_y
        
        self.keyframe_manager.add_keyframe(frame_num, x, y, mode="linear")
        self.update_keyframe_list()
        
        # Auto-select nově přidaný keyframe
        self._select_keyframe_by_frame(frame_num)
        
        self.status_label.config(
            text=f"Keyframe [LINEAR] added at frame {frame_num}"
        )
    
    def update_keyframe_list(self):
        """Update keyframes listbox"""
        self.keyframe_listbox.delete(0, tk.END)
        
        for frame_num, kf_data in self.keyframe_manager.get_all_keyframes():
            x, y, mode = kf_data
            time = frame_num / self.video_player.fps if self.video_player.fps > 0 else 0
            time_str = self._format_time(time)
            mode_label = "STEP" if mode == "step" else "ANIM"
            self.keyframe_listbox.insert(
                tk.END,
                f"F{frame_num:5d} | {time_str} | X:{x:4d} Y:{y:4d} | {mode_label}"
            )
    

        self._draw_timeline_markers()
    def _select_keyframe_by_frame(self, frame_num):
        """Vybere keyframe v listboxu podle frame čísla"""
        keyframes = self.keyframe_manager.get_all_keyframes()
        for idx, (kf_frame, _) in enumerate(keyframes):
            if kf_frame == frame_num:
                self.keyframe_listbox.selection_clear(0, tk.END)
                self.keyframe_listbox.selection_set(idx)
                self.keyframe_listbox.activate(idx)  # FIX: Nastav focus pro šipky
                self.keyframe_listbox.see(idx)  # scroll to visible
                self.keyframe_listbox.focus_set()  # FIX: Nastaví focus pro šipky
                
                # ✅ FIX: Toto je manuální výběr, zamkni auto-highlight
                self.user_manual_selection = True
                break
    
    def _get_active_keyframe(self):
        """
        Najde aktivni KF pro aktualni frame
        Returns: (frame_num, x, y, mode) nebo None
        """
        if not self.keyframe_manager.keyframes:
            return None
        
        current_frame = self.video_player.current_frame
        keyframes = self.keyframe_manager.get_all_keyframes()
        
        # Najdi nejvetsí KF <= current_frame
        active_kf = None
        for kf_frame, kf_data in keyframes:
            if kf_frame <= current_frame:
                active_kf = (kf_frame, kf_data)
            else:
                break
        
        if active_kf:
            kf_frame, (x, y, mode) = active_kf
            return (kf_frame, x, y, mode)
        
        return None
    
    def _highlight_nearest_keyframe(self, frame_num):
        """
        Automaticky označí předchozí/aktuální keyframe v tabulce
        """

        # DEBUG disabled

        """
        Označení zůstává až do dalšího KF (trvalé)
        """
        # ✅ FIX: Pokud user ručně vybral KF, neměň selection!
        if self.user_manual_selection:
            # print(f"🔒 DEBUG: Auto-highlight LOCKED (user selection active)")
            return
        
        if not self.keyframe_manager.keyframes:
            return
        
        keyframes = self.keyframe_manager.get_all_keyframes()
        
        # Najdi předchozí nebo přesný KF (největší KF <= current_frame)
        selected_idx = None
        
        for idx, (kf_frame, _) in enumerate(keyframes):
            if kf_frame <= frame_num:
                selected_idx = idx
            else:
                break  # Už jsme za aktuálním framen
        
        # 🔍 DEBUG: Auto-highlight
        current_selection = self.keyframe_listbox.curselection()
        # print(f"🎯 DEBUG: _highlight_nearest_keyframe(frame={frame_num})")
        print(f"   Current selection: {current_selection}")
        print(f"   Want to select: {selected_idx}")
        if selected_idx is not None:
            print(f"   KF frame: {keyframes[selected_idx][0]}")
        

        # 🔍 DEBUG: Selection made
        if DEBUG:
            if selected_idx is not None:
                print(f"   ✅ Selecting KF index {selected_idx} (frame {keyframes[selected_idx][0]})")
            else:
                print(f"   ⚠️ Before first KF - clearing selection")
            print(f"{'='*60}\n")

        # Označ nalezený KF (nebo zruš selection pokud jsme před prvním KF)
        self.keyframe_listbox.selection_clear(0, tk.END)
        
        if selected_idx is not None:
            self.keyframe_listbox.selection_set(selected_idx)
            self.keyframe_listbox.see(selected_idx)
    
    def goto_keyframe(self):
        """Go to selected keyframe"""
        selection = self.keyframe_listbox.curselection()
        if not selection:
            return
        
        idx = selection[0]
        keyframes = self.keyframe_manager.get_all_keyframes()
        
        if idx < len(keyframes):
            frame_num, kf_data = keyframes[idx]
            
            # ✅ FIX: User ručně vybrал KF v tabulce, zamkni auto-highlight
            self.user_manual_selection = True
            
            self.time_slider.set(frame_num)
            self.video_player.seek_frame(frame_num)
            self.update_frame_display()
    
    def delete_keyframe(self):
        """Delete selected keyframe(s) - podporuje multi-select (SHIFT/CTRL)"""
        selection = self.keyframe_listbox.curselection()
        if not selection:
            return
        
        keyframes = self.keyframe_manager.get_all_keyframes()
        
        # Smazat všechny vybrané keyframy
        self._save_undo_state("Delete keyframes")
        
        deleted_frames = []
        for idx in selection:
            if idx < len(keyframes):
                frame_num, kf_data = keyframes[idx]
                deleted_frames.append(frame_num)
        
        # Odstranit z manageru
        for frame_num in deleted_frames:
            self.keyframe_manager.remove_keyframe(frame_num)
        
        # Update GUI
        self.update_keyframe_list()
        
        # ✅ FIX: Po delete KF resetuj lock (struktura se změnila)
        self.user_manual_selection = False
        
        self.update_frame_display()
        
        # Status zpráva
        if len(deleted_frames) == 1:
            self.status_label.config(
                text=f"Keyframe at frame {deleted_frames[0]} deleted"
            )
        else:
            self.status_label.config(
                text=f"Deleted {len(deleted_frames)} keyframes"
            )
    
    def clear_keyframes(self):
        """Clear all keyframes"""
        if not self.keyframe_manager.keyframes:
            return
        
        if messagebox.askyesno("Confirm", "Clear all keyframes?"):
            self._save_undo_state("Clear all keyframes")
            self.keyframe_manager.clear_all()
            self.update_keyframe_list()
            self.update_frame_display()
            
            self.status_label.config(text="All keyframes cleared")
    
    def toggle_play(self):
	    # Zruší výběr v listboxu, aby mezerník nespustil návrat na vybraný KF
        self.keyframe_listbox.selection_clear(0, tk.END)
        """Toggle playback"""
        if self.video_player.cap is None:
            return
        
        if self.playing:
            self.stop_playback()
        else:
            self.start_playback()
    
    def start_playback(self):
        """Start video playback"""
        self.playing = True
        self.play_button.config(text="⏸ Stop", bg="#f44336")
        self.user_manual_selection = False  # FIX: Reset lock při playbacku

        
        # Reset timing measurements
        self.frame_times = []
        
        if DEBUG:
            print("▶️ Playback started - měření rychlosti aktivní")
        
        self.play_next_frame()
    
    def stop_playback(self):
        """Stop video playback"""
        self.playing = False
        self.play_button.config(text="▶ Play", bg="#2196F3")
        if self.play_timer is not None:
            self.root.after_cancel(self.play_timer)
            self.play_timer = None
        
        # ✅ FIX: Explicitně aktualizuj highlight při stop
        if self.video_player.cap is not None:
            self._highlight_nearest_keyframe(self.video_player.current_frame)
        
        # Timing pro realtime playback
        self.frame_times = []  # měření rychlosti
        self.target_delay = 40  # ms mezi framy (25fps)
        if DEBUG:
            print("⏸ Playback stopped")
    

    def start_playback(self):
        """Start video playback (immediate Stop support)"""
        if self.video_player.cap is None:
            return

        self.playing = True
        self.play_button.config(text="⏸ Stop", bg="#f44336")
        self.play_next_frame_immediate()

    def stop_playback(self):
        """Stop video playback immediately"""

        # 🔍 DEBUG: Selection Loss Investigation
        if DEBUG:
            print(f"\n{'='*60}")
            print(f"🛑 STOP_PLAYBACK DEBUG")
            print(f"{'='*60}")
            print(f"   Current frame: {self.video_player.current_frame}")
            print(f"   Lock before: {self.user_manual_selection}")
            
            # Zkontroluj aktuální selection
            selection = self.keyframe_listbox.curselection()
            if selection:
                idx = selection[0]
                keyframes = self.keyframe_manager.get_all_keyframes()
                if idx < len(keyframes):
                    sel_frame, _ = keyframes[idx]
                    print(f"   Selected KF BEFORE: #{sel_frame}")
            else:
                print(f"   ❌ NO SELECTION BEFORE")
            print(f"{'='*60}\n")

        self.playing = False
        self.play_button.config(text="▶ Play", bg="#2196F3")
        if self.play_timer is not None:
            self.root.after_cancel(self.play_timer)
            self.play_timer = None
        
        # ✅ FIX: Explicitně aktualizuj highlight při stop
        if self.video_player.cap is not None:
            self._highlight_nearest_keyframe(self.video_player.current_frame)

    def play_next_frame_immediate(self):
        """Play next frame - OPTIMIZED (no diagnostics)"""
        if not self.playing or self.video_player.cap is None:
            return

        # Next frame
        next_frame = self.video_player.current_frame + 1
        if next_frame >= self.video_player.total_frames:
            self.stop_playback()
            self.time_slider.set(self.video_player.total_frames - 1)
            return

        # ✅ OPTIMIZED: Sequential read (seek_frame detekuje +1 a skipuje cap.set)
        self.video_player.seek_frame(next_frame)
        self.update_frame_display()
        self.time_slider.set(next_frame)

        # Schedule next (40ms = 25fps)
        self.play_timer = self.root.after(40, self.play_next_frame_immediate)

    def on_right_click_debug(self, event):
        """DEBUG: Pravé tlačítko stisknuto"""
        self.debug_right_click(event, "CLICK")
        
        if self.video_player.cap is None:
            return
        
        self.time_dragging = True
        self.time_drag_start_x = event.x
        self.time_drag_start_frame = self.video_player.current_frame
        print("⏱️  TIME DRAG STARTED")
    
    def on_right_drag_debug(self, event):
        """DEBUG: Tažení s pravým tlačítkem"""
        if not self.time_dragging:
            return
        
        self.debug_right_click(event, "DRAG")
        
        delta_x = event.x - self.time_drag_start_x
        frames_delta = int(delta_x / self.time_drag_sensitivity)
        new_frame = self.time_drag_start_frame + frames_delta
        
        new_frame = max(0, min(new_frame, self.video_player.total_frames - 1))
        
        self.time_slider.set(new_frame)
        self.video_player.seek_frame(new_frame)
        self.update_frame_display()
    
    def on_right_release_debug(self, event):
        """DEBUG: Pravé tlačítko uvolněno"""
        self.debug_right_click(event, "RELEASE")
        self.time_dragging = False
        print("⏱️  TIME DRAG STOPPED\n")

    def on_key_left(self, event):
        """Sipka vlevo: -1 frame"""
        if self.video_player.cap is None:
            return
        new_frame = max(0, self.video_player.current_frame - 1)
        self.time_slider.set(new_frame)
        self.video_player.seek_frame(new_frame)
        self.update_frame_display()
    
    def on_key_right(self, event):
        """Sipka vpravo: +1 frame"""
        if self.video_player.cap is None:
            return
        new_frame = min(self.video_player.total_frames - 1, 
                       self.video_player.current_frame + 1)
        self.time_slider.set(new_frame)
        self.video_player.seek_frame(new_frame)
        self.update_frame_display()
    
    def on_key_shift_left(self, event):
        """Shift + sipka vlevo: -10 frames"""
        if self.video_player.cap is None:
            return
        new_frame = max(0, self.video_player.current_frame - 10)
        self.time_slider.set(new_frame)
        self.video_player.seek_frame(new_frame)
        self.update_frame_display()
    
    def on_key_shift_right(self, event):
        """Shift + sipka vpravo: +10 frames"""
        if self.video_player.cap is None:
            return
        new_frame = min(self.video_player.total_frames - 1,
                       self.video_player.current_frame + 10)
        self.time_slider.set(new_frame)
        self.video_player.seek_frame(new_frame)
        self.update_frame_display()
    


    def auto_detect_cuts(self):
        """Automatická detekce střihů a přidání keyframů"""
        if self.video_player.cap is None:
            messagebox.showwarning("Varování", "Nejdřív nahraj video!")
            return
        
        # Získej citlivost z kolonky
        try:
            threshold = float(self.threshold_var.get())
            if threshold < 0 or threshold > 100:
                raise ValueError
        except ValueError:
            messagebox.showerror("Chyba", "Citlivost musí být číslo 0-100!")
            return
        
        # Vytvoř progress okno
        progress_window = tk.Toplevel(self.root)
        progress_window.title("Detekuji střihy...")
        progress_window.geometry("400x120")
        progress_window.transient(self.root)
        progress_window.grab_set()
        
        tk.Label(progress_window, text="Analyzuji video...", 
                font=("Arial", 12)).pack(pady=20)
        
        progress_label = tk.Label(progress_window, text="0%", fg="gray")
        progress_label.pack(pady=10)
        
        self.root.update()
        
        # Detekce střihů
        try:
            detector = SceneDetector()
            
            def update_progress(percent):
                progress_label.config(text=f"{percent:.0f}%")
                self.root.update()
            
            scenes = detector.detect_scenes(
                self.video_player.video_path,
                threshold=threshold,
                min_scene_len=15,
                progress_callback=update_progress
            )
            
            progress_window.destroy()
            
            if not scenes:
                messagebox.showinfo("Detekce dokončena", "Žádné střihy nenalezeny!")
                return
            
            # Přidej keyframy na střihy
            current_x = self.video_player.crop_x
            current_y = self.video_player.crop_y
            
            added_count = 0
            
            # Vždy přidej první frame (začátek videa)
            self.keyframe_manager.add_keyframe(0, current_x, current_y, mode="step")
            added_count += 1
            
            # Přidej detekované střihy
            face_detector = FaceDetector() if self.center_face_var.get() else None
            
            for frame_num, score in scenes:
                # Pokud je zapnuta detekce obličeje
                if face_detector:
                    # Seek na frame
                    self.video_player.seek_frame(frame_num)
                    frame = self.video_player.get_current_frame()
                    
                    if frame is not None:
                        # BGR -> RGB (OpenCV používá BGR)
                        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                        
                        # Detekuj obličej (s DNN pokud je zaškrtnuto)
                        use_dnn = self.use_dnn_var.get()
                        result = face_detector.get_crop_position(
                            frame_bgr,
                            self.video_player.crop_width,
                            self.video_player.crop_height,
                            self.video_player.width,
                            self.video_player.height,
                            use_dnn=use_dnn
                        )
                        
                        if result:
                            current_x, current_y = result
                        else:
                            # Fallback na střed
                            current_x = self.video_player.crop_x
                            current_y = self.video_player.crop_y
                
                self.keyframe_manager.add_keyframe(frame_num, current_x, current_y, mode="step")
                added_count += 1
            
            self.update_keyframe_list()
            
            # ✅ FIX: Reset video na frame 0 po detekci (jinak zůstane na posledním cutu)
            self.video_player.seek_frame(0)
            self.time_slider.set(0)
            self.update_frame_display()
            
            self.status_label.config(text=f"Přidáno {added_count} keyframů (včetně frame 0)")
            
        except Exception as e:
            progress_window.destroy()
            messagebox.showerror("Chyba", f"Detekce selhala: {e}")
            self.status_label.config(text="Detekce selhala")
    

    def export_video_debug(self):
        """Export video s DEBUG informacemi"""
        
        # Stop playback if running
        if self.playing:
            self.stop_playback()
        
        if self.video_player.cap is None:
            messagebox.showwarning("Warning", "No video loaded")
            return
        
        # Předvyplnit originální název + _DEBUG
        original_name = Path(self.video_player.video_path).stem
        
        output_path = filedialog.asksaveasfilename(
            title="Save DEBUG Video",
            defaultextension=".mp4",
            initialfile=f"{original_name}_DEBUG.mp4",
            filetypes=[("MP4 files", "*.mp4"), ("All files", "*.*")]
        )
        
        if not output_path:
            return
        
        # Check FFmpeg
        if not ExportManager.check_ffmpeg():
            messagebox.showerror(
                "FFmpeg Not Found",
                "FFmpeg is required for export.\n\n"
                "Please install FFmpeg:\n"
                "- Windows: Download from ffmpeg.org\n"
                "- Mac: brew install ffmpeg\n"
                "- Linux: sudo apt install ffmpeg"
            )
            return
        
        # Show progress dialog
        progress_window = tk.Toplevel(self.root)
        progress_window.title("Exporting DEBUG...")
        progress_window.geometry("400x150")
        progress_window.transient(self.root)
        progress_window.grab_set()
        
        tk.Label(progress_window, text="Exporting DEBUG video...", 
                font=("Arial", 12)).pack(pady=20)
        
        progress_label = tk.Label(progress_window, text="Processing with debug overlay...", 
                                 fg="gray")
        progress_label.pack(pady=10)
        
        self.status_label.config(text="Exporting DEBUG video...")
        self.root.update()
        
        try:
            ExportManager.export_video_debug(
                self.video_player.video_path,
                output_path,
                self.keyframe_manager,
                self.video_player
            )
            
            progress_window.destroy()
            
            messagebox.showinfo(
                "Success",
                f"DEBUG video exported successfully!\n\n{Path(output_path).name}\n\n"
                "Video obsahuje:\n"
                "- Číslo framu (nahoře)\n"
                "- X a Y pozici cropu\n"
            )
            
            self.status_label.config(text=f"DEBUG Exported: {Path(output_path).name}")
            
        except Exception as e:
            progress_window.destroy()
            messagebox.showerror("Export Error", str(e))
            self.status_label.config(text="DEBUG export failed")

    def export_video(self):
        """Export video with crop animation"""
        
        # Stop playback if running
        if self.playing:
            self.stop_playback()
        
        if DEBUG:
            print('🎬 Export started')
        if self.video_player.cap is None:
            messagebox.showwarning("Warning", "No video loaded")
            return
        
        # Předvyplnit originální název
        original_name = Path(self.video_player.video_path).stem
        
        output_path = filedialog.asksaveasfilename(
            title="Save Cropped Video",
            defaultextension=".mp4",
            initialfile=f"{original_name}.mp4",
            filetypes=[("MP4 files", "*.mp4"), ("All files", "*.*")]
        )
        
        if not output_path:
            return
        
        # Check FFmpeg
        if not ExportManager.check_ffmpeg():
            messagebox.showerror(
                "FFmpeg Not Found",
                "FFmpeg is required for export.\n\n"
                "Please install FFmpeg:\n"
                "- Windows: Download from ffmpeg.org\n"
                "- Mac: brew install ffmpeg\n"
                "- Linux: sudo apt install ffmpeg"
            )
            return
        
        # Show progress dialog
        progress_window = tk.Toplevel(self.root)
        progress_window.title("Exporting...")
        progress_window.geometry("400x150")
        progress_window.transient(self.root)
        progress_window.grab_set()
        
        tk.Label(progress_window, text="Exporting video...", 
                font=("Arial", 12)).pack(pady=20)
        
        progress_label = tk.Label(progress_window, text="Processing...", 
                                 fg="gray")
        progress_label.pack(pady=10)
        
        self.status_label.config(text="Exporting video...")
        self.root.update()
        
        try:
            # Export in separate thread would be better, but for V1 blocking is OK
            ExportManager.export_video(
                self.video_player.video_path,
                output_path,
                self.keyframe_manager,
                self.video_player
            )
            
            progress_window.destroy()
            
            messagebox.showinfo(
                "Success",
                f"Video exported successfully!\n\n{Path(output_path).name}"
            )
            
            self.status_label.config(text=f"Exported: {Path(output_path).name}")
            
        except Exception as e:
            progress_window.destroy()
            messagebox.showerror("Export Error", str(e))
            self.status_label.config(text="Export failed")



    def on_canvas_double_click(self, event):
        """Add keyframe via double click on canvas"""
        if self.video_player.cap is None:
            return

        frame_num = self.video_player.current_frame
        x = self.video_player.crop_x
        y = self.video_player.crop_y

        self.keyframe_manager.add_keyframe(frame_num, x, y, mode='step')
        self.update_keyframe_list()
        
        # Auto-select nově přidaný keyframe
        self._select_keyframe_by_frame(frame_num)

        self.status_label.config(
            text=f"Keyframe [STEP] added at frame {frame_num} via DOUBLE CLICK"
        )

    def on_canvas_double_click_right(self, event):
        """Add ANIMATED keyframe via RIGHT double click on canvas"""
        if self.video_player.cap is None:
            return

        frame_num = self.video_player.current_frame
        x = self.video_player.crop_x
        y = self.video_player.crop_y

        self.keyframe_manager.add_keyframe(frame_num, x, y, mode='linear')
        self.update_keyframe_list()
        
        # Auto-select nově přidaný keyframe
        self._select_keyframe_by_frame(frame_num)

        self.status_label.config(
            text=f"Keyframe [LINEAR] added at frame {frame_num} via RIGHT DOUBLE CLICK"
        )
    # ========== NOVÉ METODY: Undo/Redo ==========
    
    def _save_undo_state(self, description="Change"):
        """Uloží aktuální stav keyframů do undo stacku"""
        state = dict(self.keyframe_manager.keyframes)  # deep copy
        self.undo_stack.append((state, description))
        
        # Omez velikost stacku
        if len(self.undo_stack) > self.max_undo_steps:
            self.undo_stack.pop(0)
        
        # Vyčisti redo stack (nová akce = nemůžeš už redo)
        self.redo_stack.clear()
    
    def undo(self):
        """CTRL+Z - vrátí poslední změnu"""
        if not self.undo_stack:
            self.status_label.config(text="⚠️ Nic k vrácení (undo stack prázdný)")
            return
        
        # Ulož současný stav do redo
        current_state = dict(self.keyframe_manager.keyframes)
        self.redo_stack.append((current_state, "Current state"))
        
        # Obnov předchozí stav
        prev_state, description = self.undo_stack.pop()
        self.keyframe_manager.keyframes = prev_state
        
        self.update_keyframe_list()
        self.update_frame_display()
        
        self.status_label.config(text=f"↩️ Undo: {description} (zbývá {len(self.undo_stack)} kroků)")
    
    def redo(self):
        """CTRL+Y - znovu aplikuje vrácenou změnu"""
        if not self.redo_stack:
            self.status_label.config(text="⚠️ Nic k opakování (redo stack prázdný)")
            return
        
        # Ulož současný stav do undo
        current_state = dict(self.keyframe_manager.keyframes)
        self.undo_stack.append((current_state, "Before redo"))
        
        # Obnov redo stav
        redo_state, description = self.redo_stack.pop()
        self.keyframe_manager.keyframes = redo_state
        
        self.update_keyframe_list()
        self.update_frame_display()
        
        self.status_label.config(text=f"↪️ Redo: {description}")
    
    # ========== NOVÉ METODY: Timeline značky ==========
    
    def _draw_timeline_markers(self):
        """Vykreslí barevné značky keyframů na timeline canvas"""
        if not hasattr(self, 'timeline_canvas'):
            return
        
        self.timeline_canvas.delete("all")
        
        if self.video_player.cap is None or not self.keyframe_manager.keyframes:
            return
        
        canvas_width = self.timeline_canvas.winfo_width()
        if canvas_width <= 1:
            canvas_width = 400  # fallback
        
        canvas_height = 20
        total_frames = self.video_player.total_frames
        
        # Vykreslení značek
        for frame_num, kf_data in self.keyframe_manager.get_all_keyframes():
            x, y, mode = kf_data
            
            # Pozice na canvasu
            marker_x = (frame_num / total_frames) * canvas_width
            
            # Barva podle módu
            color = "#4CAF50" if mode == "linear" else "#2196F3"  # zelená=LINEAR, modrá=STEP
            
            # Vykreslení značky (kolečko)
            r = 4
            self.timeline_canvas.create_oval(
                marker_x - r, canvas_height // 2 - r,
                marker_x + r, canvas_height // 2 + r,
                fill=color, outline="white", width=1,
                tags=f"marker_{frame_num}"
            )
    
    def on_timeline_marker_click(self, event):
        """Kliknutí na timeline canvas - skok na nejbližší keyframe"""
        if self.video_player.cap is None:
            return
        
        canvas_width = self.timeline_canvas.winfo_width()
        total_frames = self.video_player.total_frames
        
        # Přepočítej pozici kliknutí na frame number
        clicked_frame = int((event.x / canvas_width) * total_frames)
        
        # Najdi nejbližší keyframe (max 5% tolerance)
        tolerance = total_frames * 0.05
        closest_kf = None
        closest_dist = float('inf')
        
        for frame_num, kf_data in self.keyframe_manager.get_all_keyframes():
            dist = abs(frame_num - clicked_frame)
            if dist < closest_dist and dist < tolerance:
                closest_dist = dist
                closest_kf = frame_num
        
        if closest_kf is not None:
            # Skoč na keyframe
            self.time_slider.set(closest_kf)
            self.video_player.seek_frame(closest_kf)
            self.update_frame_display()
            
            # Zvýrazni v tabulce
            self._select_keyframe_by_frame(closest_kf)
    
    # ========== NOVÉ METODY: Klávesové zkratky ==========
    
    def jump_to_start(self):
        """Home - skok na začátek"""
        if self.video_player.cap is None:
            return
        self.time_slider.set(0)
        self.video_player.seek_frame(0)
        self.update_frame_display()
    
    def jump_to_end(self):
        """End - skok na konec"""
        if self.video_player.cap is None:
            return
        last_frame = self.video_player.total_frames - 1
        self.time_slider.set(last_frame)
        self.video_player.seek_frame(last_frame)
        self.update_frame_display()

