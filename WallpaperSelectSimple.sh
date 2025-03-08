#!/bin/bash

# Wallpaper directory
wallDIR="$HOME/Pictures/wallpapers"

# Get available monitors
monitors=($(hyprctl monitors | awk '/^Monitor/{print $2}'))

# Allow selecting a monitor
selected_monitor=$(printf "%s\n" "${monitors[@]}" | rofi -dmenu -i -p "Select Monitor")

if [[ -z "$selected_monitor" ]]; then
    exit 1
fi

# Initiate swww if not running
swww query || swww-daemon --format xrgb

# Select wallpaper with preview
choice=$(find "${wallDIR}" -type f \( -iname \*.jpg -o -iname \*.jpeg -o -iname \*.png -o -iname \*.gif \) \
    | rofi -dmenu -i -p "Select Wallpaper" \
    -theme-str 'window {width: 50%; height: 60%;}')

# Apply wallpaper if selected
if [[ -n "$choice" ]]; then
    swww img -o "$selected_monitor" "$choice" --transition-fps 30 --transition-type simple --transition-duration 5
    notify-send "Wallpaper set on $selected_monitor"
fi

