#!/usr/bin/env python3

import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import json
import os

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

# Fetch monitor info using hyprctl
def get_monitors():
    global original_monitors
    output = run_command("hyprctl monitors -j")
    if output.startswith("Error"):
        print(f"get_monitors error: {output}")
        return original_monitors if original_monitors else []
    monitors = json.loads(output)
    print(f"Detected {len(monitors)} monitors: {[m['name'] for m in monitors]}")
    if not original_monitors:  # Store initial state
        original_monitors = monitors.copy()
    return monitors

# Fetch available resolutions for a monitor
def get_resolutions(monitor_name):
    monitors = get_monitors()
    for mon in monitors:
        if mon["name"] == monitor_name:
            return mon.get("availableModes", ["1920x1080@60Hz"])
    return ["1920x1080@60Hz"]

# Apply resolution and refresh rate
def set_resolution(monitor, resolution):
    res, rate = resolution.split("@")
    cmd = f"hyprctl keyword monitor {monitor},{res}@{rate},auto,1"
    result = run_command(cmd)
    if "Error" in result:
        update_status(f"Failed to set {monitor} to {resolution}: {result}")
    else:
        update_status(f"Set {monitor} to {resolution}")
    refresh_monitors()

# Toggle monitor off (disable)
def toggle_monitor(monitor, enable=True):
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
    refresh_monitors()

# Set wallpaper by calling the script
def set_wallpaper(monitor):
    script_path = os.path.expanduser("~/.config/hypr/UserScripts/monitors/WallpaperSelectSimple.sh")
    if os.path.exists(script_path):
        result = run_command(f"bash {script_path}")
        if "Error" in result:
            update_status(f"Wallpaper script failed: {result}")
        else:
            update_status("Wallpaper selection triggered for focused monitor")
    else:
        update_status(f"Wallpaper script not found at {script_path}")

# Mirror or extend displays
def set_display_mode(mode="extend"):
    global original_monitors
    monitors = get_monitors()
    if not monitors:
        update_status("No monitors detected")
        return
    if len(monitors) < 2 and mode in ["mirror", "extend"] and not original_monitors:
        update_status("Need at least 2 monitors for mirror/extend")
        return

    if mode == "mirror":
        primary = next((m for m in monitors if m.get("primary", False)), None)
        if primary is None:
            primary = monitors[0]
        res = f"{primary['width']}x{primary['height']}@{primary['refreshRate']}"
        # Reset all monitors first
        for mon in original_monitors:
            cmd = f"hyprctl keyword monitor {mon['name']},{mon['width']}x{mon['height']}@{mon['refreshRate']},auto,1"
            run_command(cmd)
        # Set primary monitor
        cmd = f"hyprctl keyword monitor {primary['name']},{res},0x0,1"
        result = run_command(cmd)
        if "Error" in result:
            update_status(f"Failed to set primary {primary['name']}: {result}")
            return
        # Mirror others to primary
        for mon in original_monitors:
            if mon["name"] != primary["name"]:
                cmd = f"hyprctl keyword monitor {mon['name']},{res},0x0,1,mirror,{primary['name']}"
                result = run_command(cmd)
                if "Error" in result:
                    update_status(f"Failed to mirror {mon['name']} to {primary['name']}: {result}")
                    return
                run_command(f"hyprctl dispatch focusmonitor {mon['name']}")
        update_status(f"All displays mirrored to {primary['name']} at {res}")
    elif mode == "extend":
        # Reset mirroring before extending
        for mon in original_monitors:
            cmd = f"hyprctl keyword monitor {mon['name']},{mon['width']}x{mon['height']}@{mon['refreshRate']},auto,1"
            run_command(cmd)
        arrange_monitors()
    refresh_monitors()

# Arrange monitors based on position dropdowns
def arrange_monitors():
    global original_monitors
    monitors = get_monitors()
    if not monitors and not original_monitors:
        update_status("No monitors to arrange")
        return
    # Use original_monitors if current list is incomplete
    working_monitors = original_monitors if len(monitors) < len(original_monitors) else monitors
    if len(working_monitors) == 1:
        cmd = f"hyprctl keyword monitor {working_monitors[0]['name']},{working_monitors[0]['width']}x{working_monitors[0]['height']}@{working_monitors[0]['refreshRate']},0x0,1"
        run_command(cmd)
        update_status("Single monitor arranged at 0x0")
        return

    # Map position labels to indices
    pos_map = {"Left": 0, "Right": 1} if len(working_monitors) == 2 else {f"Pos {i}": i for i in range(len(working_monitors))}
    positions = {mon["name"]: pos_map[pos_vars[mon["name"]].get()] for mon in working_monitors}
    
    # Sort monitors by position number
    sorted_monitors = sorted(working_monitors, key=lambda m: positions[m["name"]])
    
    # Check for duplicate positions
    pos_list = [positions[mon["name"]] for mon in working_monitors]
    if len(pos_list) != len(set(pos_list)):
        update_status("Error: Duplicate position selections detected")
        return

    # Assign x offsets
    x_offset = 0
    for mon in sorted_monitors:
        cmd = f"hyprctl keyword monitor {mon['name']},{mon['width']}x{mon['height']}@{mon['refreshRate']},{x_offset}x0,1"
        result = run_command(cmd)
        if "Error" in result:
            update_status(f"Failed to position {mon['name']}: {result}")
            return
        x_offset += mon["width"]
    update_status("Monitors extended successfully")

# Update other monitor's position when one changes (for 2 monitors)
def update_position(changed_monitor):
    monitors = get_monitors()
    if len(monitors) == 2:
        other_monitor = next(m["name"] for m in monitors if m["name"] != changed_monitor)
        current_pos = pos_vars[changed_monitor].get()
        other_pos = "Right" if current_pos == "Left" else "Left"
        pos_vars[other_monitor].set(other_pos)

# Reload Hyprland configuration
def reload_hyprland():
    global original_monitors
    result = run_command("hyprctl reload")
    if "Error" in result:
        update_status(f"Failed to reload Hyprland: {result}")
    else:
        update_status("Hyprland configuration reloaded")
        original_monitors = []  # Reset cached monitors on reload
    refresh_monitors()

# Update status label
def update_status(message):
    status_label.config(text=message)

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
        
        # Position dropdown
        pos_options = ["Left", "Right"] if len(working_monitors) == 2 else [f"Pos {x}" for x in range(len(working_monitors))]
        pos_vars[mon_name] = tk.StringVar(value=pos_options[i])
        pos_menu = ttk.Combobox(monitor_frame, textvariable=pos_vars[mon_name], values=pos_options, width=8)
        pos_menu.grid(row=i, column=4, padx=5, pady=5)
        pos_menu.bind("<<ComboboxSelected>>", lambda event, m=mon_name: update_position(m))
        ttk.Button(monitor_frame, text="Apply Position",
                   command=arrange_monitors).grid(row=i, column=5, padx=5, pady=5)

# Build GUI
root = tk.Tk()
root.title("Hyprland Monitor Manager")
root.geometry("900x500")
root.resizable(True, True)

# Style
style = ttk.Style()
style.configure("TButton", padding=5)
style.configure("TLabel", padding=5)

# Status label
status_label = ttk.Label(root, text="Ready", anchor="w")
status_label.pack(fill="x", padx=10, pady=5)

# Monitor frame
monitor_frame = ttk.LabelFrame(root, text="Monitors", padding=10)
monitor_frame.pack(fill="both", expand=True, padx=10, pady=5)

# Wallpaper frame
wallpaper_frame = ttk.LabelFrame(root, text="Wallpaper", padding=10)
wallpaper_frame.pack(fill="x", padx=10, pady=5)
ttk.Button(wallpaper_frame, text="Select Wallpaper", command=lambda: set_wallpaper("focused")).pack(side="left", padx=5)

# Display mode frame
mode_frame = ttk.LabelFrame(root, text="Display Mode", padding=10)
mode_frame.pack(fill="x", padx=10, pady=5)
ttk.Button(mode_frame, text="Mirror", command=lambda: set_display_mode("mirror")).pack(side="left", padx=5)
ttk.Button(mode_frame, text="Extend", command=lambda: set_display_mode("extend")).pack(side="left", padx=5)
ttk.Button(mode_frame, text="Refresh", command=reload_hyprland).pack(side="right", padx=5)

# Initial population
pos_vars = {}
refresh_monitors()

# Start GUI
root.mainloop()