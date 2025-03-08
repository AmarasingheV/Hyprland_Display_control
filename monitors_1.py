#!/usr/bin/env python3

import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import json

# Run shell commands and return output
def run_command(command):
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.stdout.strip()
    except Exception as e:
        return f"Error: {str(e)}"

# Fetch monitor info using hyprctl
def get_monitors():
    output = run_command("hyprctl monitors -j")
    if output.startswith("Error"):
        return []
    return json.loads(output)

# Fetch available resolutions for a monitor from hyprctl
def get_resolutions(monitor_name):
    monitors = get_monitors()
    for mon in monitors:
        if mon["name"] == monitor_name:
            return mon.get("availableModes", ["1920x1080@60Hz"])  # Fallback if no modes
    return ["1920x1080@60Hz"]  # Default fallback

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
        for mon in monitors:
            cmd = f"hyprctl keyword monitor {mon['name']},{res},0x0,1"
            run_command(cmd)
    elif mode == "extend":
        # Extend: Position monitors side by side
        x_offset = 0
        for mon in monitors:
            cmd = f"hyprctl keyword monitor {mon['name']},{mon['width']}x{mon['height']}@{mon['refreshRate']},{x_offset}x0,1"
            run_command(cmd)
            x_offset += mon['width']
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
    resolutions = get_resolutions(mon_name)
    res_var = tk.StringVar(value=f"{monitor['width']}x{monitor['height']}@{monitor['refreshRate']}Hz")
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
