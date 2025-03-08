#!/usr/bin/env python3

import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import json
import os
import atexit
import threading
import time

# Catppuccin Mocha Theme Colors
THEME = {
    "base": "#1E1E2E",      # Main background
    "mantle": "#181825",    # Darker background
    "crust": "#11111B",     # Darkest background
    "text": "#CDD6F4",      # Main text
    "subtext0": "#A6ADC8",  # Muted text
    "surface0": "#313244",  # Widget background
    "surface1": "#45475A",  # Hover/selected background
    "lavender": "#B4BEFE",  # Accent color
    "peach": "#FAB387",     # Secondary accent
    "red": "#F38BA8"        # Error/warning
}

# Create lock file path
LOCK_FILE = "/tmp/hyprland_monitor_manager.lock"

# Create lock file on startup
def create_lock_file():
    try:
        with open(LOCK_FILE, 'w') as f:
            f.write(str(os.getpid()))
        print(f"Created lock file at {LOCK_FILE}")
    except Exception as e:
        print(f"Error creating lock file: {str(e)}")

# Remove lock file on exit
def remove_lock_file():
    try:
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)
            print(f"Removed lock file at {LOCK_FILE}")
    except Exception as e:
        print(f"Error removing lock file: {str(e)}")

# Register cleanup function
atexit.register(remove_lock_file)

# Create lock file at startup
create_lock_file()

# Global to store original monitor states
original_monitors = []

# Run shell commands and return output
def run_command(command):
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.stderr:
            print(f"Command '{command}' stderr: {result.stderr.strip()}")
            return f"Error: {result.stderr.strip()}"
        print(f"Command '{command}' stdout: {result.stdout.strip()}")
        return result.stdout.strip()
    except Exception as e:
        print(f"Command '{command}' exception: {str(e)}")
        return f"Error: {str(e)}"

# Update status label - thread-safe
def update_status(message):
    if root and status_label:
        root.after(0, lambda: status_label.config(text=message))
    print(f"Status: {message}")

# Refresh monitor frame - thread-safe
def refresh_monitors_ui():
    if root:
        root.after(0, refresh_monitors)

# Fetch monitor info using hyprctl
def get_monitors():
    global original_monitors
    output = run_command("hyprctl monitors -j")
    if output.startswith("Error"):
        print(f"get_monitors error: {output}")
        return original_monitors if original_monitors else []
    try:
        monitors = json.loads(output)
        print(f"Detected {len(monitors)} monitors: {[m['name'] for m in monitors]}")
        if not original_monitors:  # Store initial state
            original_monitors = monitors.copy()
        return monitors
    except json.JSONDecodeError:
        print(f"Failed to parse JSON: {output}")
        return original_monitors if original_monitors else []

# Fetch available resolutions for a monitor
def get_resolutions(monitor_name):
    monitors = get_monitors()
    for mon in monitors:
        if mon["name"] == monitor_name:
            return mon.get("availableModes", ["1920x1080@60Hz"])
    return ["1920x1080@60Hz"]

# Apply resolution and refresh rate in a separate thread
def set_resolution_thread(monitor, resolution):
    def task():
        update_status(f"Setting {monitor} to {resolution}...")
        res, rate = resolution.split("@")
        cmd = f"hyprctl keyword monitor {monitor},{res}@{rate},auto,1"
        result = run_command(cmd)
        if "Error" in result:
            update_status(f"Failed to set {monitor} to {resolution}: {result}")
        else:
            update_status(f"Set {monitor} to {resolution}")
            time.sleep(0.5)
            refresh_wallpaper_thread()
        root.after(500, refresh_monitors)
    
    threading.Thread(target=task, daemon=True).start()

def set_resolution(monitor, resolution):
    set_resolution_thread(monitor, resolution)

# Toggle monitor off (disable) in a separate thread
def toggle_monitor_thread(monitor, enable=True):
    def task():
        update_status(f"{'Enabling' if enable else 'Disabling'} {monitor}...")
        monitors = get_monitors()
        mon_info = next((m for m in monitors if m["name"] == monitor), None)
        if not mon_info:
            update_status(f"Monitor {monitor} not found")
            return

        if mon_info.get("primary", False) and not enable:
            update_status(f"Cannot disable primary monitor {monitor}")
            return

        if not enable:
            cmd = f"hyprctl keyword monitor {monitor},disable"
            result = run_command(cmd)
            if "Error" in result:
                update_status(f"Failed to disable {monitor}: {result}")
            else:
                update_status(f"{monitor} disabled")
                time.sleep(0.5)
                reset_ui_elements_thread()
        root.after(500, refresh_monitors)
    
    threading.Thread(target=task, daemon=True).start()

def toggle_monitor(monitor, enable=True):
    toggle_monitor_thread(monitor, enable)

# Refresh wallpaper for all monitors in a separate thread
def refresh_wallpaper_thread():
    def task():
        update_status("Refreshing wallpapers...")
        script_path = os.path.expanduser("~/.config/hypr/UserScripts/monitors/WallpaperSelectSimple.sh")
        if os.path.exists(script_path):
            swaybg_cmd = "pkill swaybg; systemctl --user restart hyprpaper.service"
            run_command(swaybg_cmd)
            update_status("Wallpapers refreshed")
        else:
            update_status(f"Wallpaper script not found at {script_path}")
    
    threading.Thread(target=task, daemon=True).start()

def refresh_wallpaper():
    refresh_wallpaper_thread()

# Set wallpaper by calling the script in a separate thread
def set_wallpaper_thread(monitor):
    def task():
        update_status("Setting wallpaper...")
        script_path = os.path.expanduser("~/.config/hypr/UserScripts/monitors/WallpaperSelectSimple.sh")
        if os.path.exists(script_path):
            result = run_command(f"bash {script_path}")
            if "Error" in result:
                update_status(f"Wallpaper script failed: {result}")
            else:
                update_status("Wallpaper selection triggered for focused monitor")
        else:
            update_status(f"Wallpaper script not found at {script_path}")
    
    threading.Thread(target=task, daemon=True).start()

def set_wallpaper(monitor):
    set_wallpaper_thread(monitor)

# Reset UI elements like waybar in a separate thread
def reset_ui_elements_thread():
    def task():
        update_status("Resetting UI elements...")
        run_command("pkill waybar; sleep 0.5; waybar &")
        run_command("systemctl --user restart hyprpaper.service")
        update_status("UI elements reset")
    
    threading.Thread(target=task, daemon=True).start()

def reset_ui_elements():
    reset_ui_elements_thread()

# Move all windows to primary monitor in a separate thread
def move_windows_to_primary_thread():
    def task():
        update_status("Moving windows to primary monitor...")
        monitors = get_monitors()
        primary = next((m for m in monitors if m.get("primary", False) or m["name"] == "eDP-1"), monitors[0] if monitors else None)
        
        if not primary:
            update_status("No primary monitor found to move windows to")
            return
            
        window_list = run_command("hyprctl clients -j")
        try:
            windows = json.loads(window_list)
            moved_count = 0
            for window in windows:
                if "address" in window:
                    move_cmd = f"hyprctl dispatch movewindow mon:{primary['name']} address:{window['address']}"
                    run_command(move_cmd)
                    moved_count += 1
            update_status(f"Moved {moved_count} windows to {primary['name']}")
        except json.JSONDecodeError:
            update_status("Failed to parse window list")
    
    threading.Thread(target=task, daemon=True).start()

def move_windows_to_primary():
    move_windows_to_primary_thread()

# Set display mode - EXTEND with reload buttons after setting mode
def set_display_mode_thread(mode="extend"):
    def task():
        update_status(f"Setting display mode to {mode}...")
        global original_monitors
        monitors = get_monitors()
        
        working_monitors = original_monitors if len(original_monitors) > len(monitors) else monitors
        
        if not working_monitors:
            update_status("No monitors detected")
            return
        
        if len(working_monitors) < 2 and mode in ["mirror", "extend"]:
            update_status("Need at least 2 monitors for mirror/extend")
            return

        run_command("pkill waybar")
        
        if mode == "mirror":
            primary = next((m for m in working_monitors if m.get("primary", False) or m["name"] == "eDP-1"), working_monitors[0])
            secondary_monitors = [m for m in working_monitors if m["name"] != primary["name"]]
            res = f"{primary['width']}x{primary['height']}@{primary['refreshRate']}"
            
            for mon in secondary_monitors:
                cmd = f"hyprctl keyword monitor {mon['name']},disable"
                run_command(cmd)
                time.sleep(0.5)
            
            cmd = f"hyprctl keyword monitor {primary['name']},{res},0x0,1"
            result = run_command(cmd)
            time.sleep(0.5)
            
            if "Error" in result:
                update_status(f"Failed to set primary {primary['name']}: {result}")
                reset_ui_elements_thread()
                return
            
            for mon in secondary_monitors:
                cmd = f"hyprctl keyword monitor {mon['name']},{res},0x0,1,mirror,{primary['name']}"
                result = run_command(cmd)
                time.sleep(0.5)
                
                if "Error" in result:
                    update_status(f"Failed to mirror {mon['name']} to {primary['name']}: {result}")
                else:
                    update_status(f"Mirrored {mon['name']} to {primary['name']}")
            
            move_windows_to_primary()
            update_status(f"All displays mirrored to {primary['name']} at {res}")
            time.sleep(0.5)
            reset_ui_elements_thread()
            
        elif mode == "extend":
            primary = next((m for m in working_monitors if m.get("primary", False) or m["name"] == "eDP-1"), working_monitors[0])
            secondary_monitors = [m for m in working_monitors if m["name"] != primary["name"]]
            
            is_mirroring = False
            for mon in working_monitors:
                if mon.get("mirror", "") != "":
                    is_mirroring = True
                    break
            
            if is_mirroring:
                for mon in secondary_monitors:
                    cmd = f"hyprctl keyword monitor {mon['name']},disable"
                    run_command(cmd)
                    time.sleep(0.5)
                cmd = f"hyprctl keyword monitor {primary['name']},{primary['width']}x{primary['height']}@{primary['refreshRate']},0x0,1"
                run_command(cmd)
                time.sleep(0.7)
            else:
                for mon in secondary_monitors:
                    cmd = f"hyprctl keyword monitor {mon['name']},disable"
                    run_command(cmd)
                    time.sleep(0.3)
            
            time.sleep(0.5)
            
            cmd = f"hyprctl keyword monitor {primary['name']},{primary['width']}x{primary['height']}@{primary['refreshRate']},0x0,1"
            run_command(cmd)
            time.sleep(0.5)
            
            x_offset = primary["width"]
            for mon in secondary_monitors:
                cmd = f"hyprctl keyword monitor {mon['name']},{mon['width']}x{mon['height']}@{mon['refreshRate']},{x_offset}x0,1"
                result = run_command(cmd)
                
                if "Error" in result:
                    update_status(f"Failed to extend {mon['name']}: {result}")
                else:
                    update_status(f"Extended {mon['name']} at position {x_offset}x0")
                
                x_offset += mon["width"]
                time.sleep(0.5)
            
            run_command("hyprctl dispatch workspace 1")
            time.sleep(0.5)
            reset_ui_elements_thread()
            update_status("Reloading Hyprland buttons...")
            run_command("hyprctl dispatch reload-buttons")

        root.after(1000, refresh_monitors)
    
    threading.Thread(target=task, daemon=True).start()

def set_display_mode(mode="extend"):
    set_display_mode_thread(mode)

# Arrange monitors based on position dropdowns in a separate thread
def arrange_monitors_thread():
    def task():
        update_status("Arranging monitors...")
        global original_monitors
        monitors = get_monitors()
        if not monitors and not original_monitors:
            update_status("No monitors to arrange")
            return
        
        working_monitors = original_monitors if len(monitors) < len(original_monitors) else monitors
        if len(working_monitors) == 1:
            cmd = f"hyprctl keyword monitor {working_monitors[0]['name']},{working_monitors[0]['width']}x{working_monitors[0]['height']}@{working_monitors[0]['refreshRate']},0x0,1"
            run_command(cmd)
            update_status("Single monitor arranged at 0x0")
            time.sleep(0.5)
            reset_ui_elements_thread()
            return

        pos_map = {"Left": 0, "Right": 1} if len(working_monitors) == 2 else {f"Pos {i}": i for i in range(len(working_monitors))}
        positions = {mon["name"]: pos_map[pos_vars[mon["name"]].get()] for mon in working_monitors}
        
        sorted_monitors = sorted(working_monitors, key=lambda m: positions[m["name"]])
        
        pos_list = [positions[mon["name"]] for mon in working_monitors]
        if len(pos_list) != len(set(pos_list)):
            update_status("Error: Duplicate position selections detected")
            return

        primary = next((m for m in sorted_monitors if m.get("primary", False) or m["name"] == "eDP-1"), sorted_monitors[0])
        secondary_monitors = [m for m in sorted_monitors if m["name"] != primary["name"]]
        
        for mon in secondary_monitors:
            cmd = f"hyprctl keyword monitor {mon['name']},disable"
            run_command(cmd)
            time.sleep(0.2)
        
        time.sleep(0.5)
        
        left_offset = 0
        for i in range(sorted_monitors.index(primary) - 1, -1, -1):
            mon = sorted_monitors[i]
            left_offset -= mon["width"]
            cmd = f"hyprctl keyword monitor {mon['name']},{mon['width']}x{mon['height']}@{mon['refreshRate']},{left_offset}x0,1"
            run_command(cmd)
            time.sleep(0.5)
        
        cmd = f"hyprctl keyword monitor {primary['name']},{primary['width']}x{primary['height']}@{primary['refreshRate']},0x0,1"
        run_command(cmd)
        time.sleep(0.5)
        
        right_offset = primary["width"]
        for i in range(sorted_monitors.index(primary) + 1, len(sorted_monitors)):
            mon = sorted_monitors[i]
            cmd = f"hyprctl keyword monitor {mon['name']},{mon['width']}x{mon['height']}@{mon['refreshRate']},{right_offset}x0,1"
            run_command(cmd)
            right_offset += mon["width"]
            time.sleep(0.5)
        
        update_status("Monitors arranged successfully")
        time.sleep(0.5)
        reset_ui_elements_thread()
        
        root.after(1000, refresh_monitors)
    
    threading.Thread(target=task, daemon=True).start()

def arrange_monitors():
    arrange_monitors_thread()

# Update other monitor's position when one changes (for 2 monitors)
def update_position(changed_monitor):
    monitors = get_monitors()
    if len(monitors) == 2:
        other_monitor = next(m["name"] for m in monitors if m["name"] != changed_monitor)
        current_pos = pos_vars[changed_monitor].get()
        other_pos = "Right" if current_pos == "Left" else "Left"
        pos_vars[other_monitor].set(other_pos)

# Reload Hyprland configuration in a separate thread
def reload_hyprland_thread():
    def task():
        update_status("Reloading Hyprland...")
        global original_monitors
        result = run_command("hyprctl reload")
        if "Error" in result:
            update_status(f"Failed to reload Hyprland: {result}")
        else:
            update_status("Hyprland configuration reloaded")
            original_monitors = []
            time.sleep(1)
            reset_ui_elements_thread()
        root.after(1000, refresh_monitors)
    
    threading.Thread(target=task, daemon=True).start()

def reload_hyprland():
    reload_hyprland_thread()

# Refresh monitor list and UI
def refresh_monitors():
    global original_monitors
    for widget in monitor_frame.winfo_children():
        widget.destroy()
    monitors = get_monitors()
    working_monitors = original_monitors if len(monitors) < len(original_monitors) else monitors
    global pos_vars
    pos_vars = {}

    for i, monitor in enumerate(working_monitors):
        mon_name = monitor["name"]
        is_primary = monitor.get("primary", False) or mon_name == "eDP-1"
        
        label_text = f"{mon_name} (Primary)" if is_primary else f"{mon_name}"
        ttk.Label(monitor_frame, text=label_text).grid(row=i, column=0, padx=5, pady=5, sticky="w")
        
        resolutions = get_resolutions(mon_name)
        res_var = tk.StringVar(value=f"{monitor['width']}x{monitor['height']}@{monitor['refreshRate']}Hz")
        res_menu = ttk.Combobox(monitor_frame, textvariable=res_var, values=resolutions, width=20)
        res_menu.grid(row=i, column=1, padx=5, pady=5)
        
        ttk.Button(monitor_frame, text="Set Resolution",
                   command=lambda m=mon_name, r=res_var: set_resolution(m, r.get())).grid(row=i, column=2, padx=5, pady=5)
        
        if not is_primary:
            ttk.Button(monitor_frame, text="Turn Off",
                       command=lambda m=mon_name: toggle_monitor(m, False)).grid(row=i, column=3, padx=5, pady=5)
        
        pos_options = ["Left", "Right"] if len(working_monitors) == 2 else [f"Pos {i}" for i in range(len(working_monitors))]
        pos_vars[mon_name] = tk.StringVar(value=pos_options[i])
        pos_menu = ttk.Combobox(monitor_frame, textvariable=pos_vars[mon_name], values=pos_options, width=8)
        pos_menu.grid(row=i, column=4, padx=5, pady=5)
        pos_menu.bind("<<ComboboxSelected>>", lambda event, m=mon_name: update_position(m))
        ttk.Button(monitor_frame, text="Apply Position",
                   command=arrange_monitors).grid(row=i, column=5, padx=5, pady=5)

# Add a function to handle window close event
def on_closing():
    remove_lock_file()
    root.destroy()

# Build GUI with Catppuccin Mocha Theme
root = tk.Tk()
root.title("Hyprland Monitor Manager")
root.geometry("900x500")
root.resizable(True, True)
root.configure(bg=THEME["base"])  # Set window background
root.protocol("WM_DELETE_WINDOW", on_closing)

# Style configuration
style = ttk.Style()
style.theme_use("default")  # Use default theme as base

# Configure styles
style.configure("TLabel", background=THEME["base"], foreground=THEME["text"], font=("Helvetica", 10))
style.configure("TButton", background=THEME["surface0"], foreground=THEME["text"], padding=5)
style.map("TButton", background=[("active", THEME["surface1"]), ("!active", THEME["surface0"])])
style.configure("TFrame", background=THEME["mantle"])
style.configure("TLabelframe", background=THEME["mantle"], foreground=THEME["lavender"])
style.configure("TLabelframe.Label", background=THEME["mantle"], foreground=THEME["lavender"])
style.configure("TCombobox", fieldbackground=THEME["surface0"], background=THEME["surface0"], foreground=THEME["text"])
style.map("TCombobox", fieldbackground=[("readonly", THEME["surface0"])], selectbackground=[("readonly", THEME["surface1"])])

# Status label
status_label = ttk.Label(root, text="Ready", anchor="w", style="TLabel")
status_label.pack(fill="x", padx=10, pady=5)

# Monitor frame
monitor_frame = ttk.LabelFrame(root, text="Monitors", padding=10)
monitor_frame.pack(fill="both", expand=True, padx=10, pady=5)

# Wallpaper frame
wallpaper_frame = ttk.LabelFrame(root, text="Wallpaper", padding=10)
wallpaper_frame.pack(fill="x", padx=10, pady=5)
ttk.Button(wallpaper_frame, text="Select Wallpaper", command=lambda: set_wallpaper("focused")).pack(side="left", padx=5)
ttk.Button(wallpaper_frame, text="Refresh All Wallpapers", command=refresh_wallpaper).pack(side="left", padx=5)

# Display mode frame
mode_frame = ttk.LabelFrame(root, text="Display Mode", padding=10)
mode_frame.pack(fill="x", padx=10, pady=5)
ttk.Button(mode_frame, text="Mirror", command=lambda: set_display_mode("mirror")).pack(side="left", padx=5)
ttk.Button(mode_frame, text="Extend", command=lambda: set_display_mode("extend")).pack(side="left", padx=5)
ttk.Button(mode_frame, text="Move Windows to Primary", command=move_windows_to_primary).pack(side="left", padx=5)
ttk.Button(mode_frame, text="Refresh UI", command=reset_ui_elements).pack(side="left", padx=5)
ttk.Button(mode_frame, text="Reload Hyprland", command=reload_hyprland).pack(side="right", padx=5)

# Display logs in a scrolled text widget
log_frame = ttk.LabelFrame(root, text="Logs", padding=10)
log_frame.pack(fill="x", padx=10, pady=5)
log_text = tk.Text(log_frame, height=5, width=80, bg=THEME["crust"], fg=THEME["subtext0"], insertbackground=THEME["lavender"])
log_text.pack(side="left", fill="both", expand=True)
log_scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=log_text.yview)
log_scrollbar.pack(side="right", fill="y")
log_text.config(yscrollcommand=log_scrollbar.set)

# Override print to also show in the log widget
original_print = print
def custom_print(*args, **kwargs):
    original_print(*args, **kwargs)
    message = " ".join(str(arg) for arg in args)
    if root and log_text:
        root.after(0, lambda m=message: log_text.insert(tk.END, m + "\n") or log_text.see(tk.END))
print = custom_print

# Initial population
pos_vars = {}
refresh_monitors()

# Start GUI
root.mainloop()