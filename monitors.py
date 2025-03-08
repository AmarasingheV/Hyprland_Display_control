#!/usr/bin/env python3

import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import json

# Function to run shell commands and return output
def run_command(command):
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.stdout.strip()
    except Exception as e:
        return f"Error: {str(e)}"

# Fetch monitor info using hyprctl
def get_monitors():
    output = run_command("hyprctl monitors -j")  # -j for JSON output
    if output.startswith("Error"):
        return []
    return json.loads(output)

# Fetch available resolutions for a monitor
def get_resolutions(monitor_name):
    # Hyprland doesn't provide resolutions directly, so we might use wlr-randr
    output = run_command(f"wlr-randr --output {monitor_name}")
    if output.startswith("Error"):
        return []
    resolutions = []
    for line in output.splitlines():
        if "x" in line and "@" in line:  # Look for lines like "1920x1080@60Hz"
            resolutions.append(line.strip())
    return resolutions

# Apply resolution and refresh rate
def set_resolution(monitor, resolution):
    res, rate = resolution.split("@")
    cmd = f"hyprctl keyword monitor {monitor},{res}@{rate},auto,1"
    run_command(cmd)
    update_status(f"Set {monitor} to {resolution}")

# Toggle monitor on/off
def toggle_monitor(monitor, enable=True):
    state = "enable" if enable else "disable"
    cmd = f"hyprctl keyword monitor {monitor},{state}"
    run_command(cmd)
    update_status(f"{monitor} {'enabled' if enable else 'disabled'}")

# Set wallpaper using swww
def set_wallpaper(monitor, wallpaper_path="/path/to/default/wallpaper.jpg"):
    cmd = f"swww img {wallpaper_path} --output {monitor}"
    run_command(cmd)
    update_status(f"Wallpaper set for {monitor}")

# Mirror or extend displays
def set_display_mode(mode="extend"):
    monitors = get_monitors()
    if len(monitors) < 2:
        update_status("Need at least 2 monitors for mirror/extend")
        return
    if mode == "mirror":
        # Mirror: Set same resolution and position (0,0) for all
        res = "1920x1080@60"  # Default, could be dynamic
        for i, mon in enumerate(monitors):
            cmd = f"hyprctl keyword monitor {mon['name']},{res},0x0,1"
            run_command(cmd)
    elif mode == "extend":
        # Extend: Position monitors side by side
        x_offset = 0
        for mon in monitors:
            cmd = f"hyprctl keyword monitor {mon['name']},{mon['activeMode']['width']}x{mon['activeMode']['height']}@{mon['activeMode']['refreshRate']},{x_offset}x0,1"
            run_command(cmd)
            x_offset += mon['activeMode']['width']
    update_status(f"Display mode set to {mode}")

# Update status label
def update_status(message):
    status_label.config(text=message)

# Build GUI
root = tk.Tk()
root.title("Hyprland Monitor Manager")
root.geometry("600x400")

# Status label
status_label = tk.Label(root, text="Ready", anchor="w")
status_label.pack(fill="x", padx=5, pady=5)

# Monitor frame
monitor_frame = ttk.LabelFrame(root, text="Monitors")
monitor_frame.pack(fill="both", expand=True, padx=5, pady=5)

# Dynamically populate monitor controls
monitors = get_monitors()
for i, monitor in enumerate(monitors):
    mon_name = monitor["name"]
    
    # Monitor label
    ttk.Label(monitor_frame, text=f"Monitor: {mon_name}").grid(row=i, column=0, padx=5, pady=5)
    
    # Resolution dropdown
    resolutions = get_resolutions(mon_name) or ["1920x1080@60Hz", "1280x720@60Hz"]  # Fallback
    res_var = tk.StringVar(value=resolutions[0])
    res_menu = ttk.Combobox(monitor_frame, textvariable=res_var, values=resolutions)
    res_menu.grid(row=i, column=1, padx=5, pady=5)
    
    # Apply resolution button
    ttk.Button(monitor_frame, text="Set Resolution",
               command=lambda m=mon_name, r=res_var: set_resolution(m, r.get())).grid(row=i, column=2, padx=5, pady=5)
    
    # Toggle monitor button
    ttk.Button(monitor_frame, text="Turn Off",
               command=lambda m=mon_name: toggle_monitor(m, False)).grid(row=i, column=3, padx=5, pady=5)
    
    # Wallpaper button
    ttk.Button(monitor_frame, text="Set Wallpaper",
               command=lambda m=mon_name: set_wallpaper(m)).grid(row=i, column=4, padx=5, pady=5)

# Display mode controls
mode_frame = ttk.LabelFrame(root, text="Display Mode")
mode_frame.pack(fill="x", padx=5, pady=5)
ttk.Button(mode_frame, text="Mirror", command=lambda: set_display_mode("mirror")).pack(side="left", padx=5)
ttk.Button(mode_frame, text="Extend", command=lambda: set_display_mode("extend")).pack(side="left", padx=5)

# Start GUI
root.mainloop()
