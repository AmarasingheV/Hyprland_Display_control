
# Hyprland Monitor Manager

A Python-based GUI tool for managing monitors in the Hyprland window manager. Built with Tkinter and themed with Catppuccin Mocha, this script provides an intuitive interface to configure monitor resolutions, positions, display modes, and wallpapers.

![Hyprland Monitor Manager]

![image](https://github.com/user-attachments/assets/f265d155-fab5-4c8a-9383-2d3677d7193f)


## Features

- **Monitor Configuration**:
  - Set resolutions and refresh rates for each monitor.
  - Enable/disable individual monitors (except the primary one).
  - Arrange monitors with position dropdowns (e.g., Left/Right).

- **Display Modes**:
  - Switch between **Mirror** and **Extend** modes for multi-monitor setups.
  - Move all windows to the primary monitor with one click.

- **Wallpaper Management**:
  - Refresh wallpapers across all monitors.
  - Trigger wallpaper selection for the focused monitor (requires `WallpaperSelectSimple.sh`).

- **UI Utilities**:
  - Refresh UI elements (e.g., Waybar) after changes.
  - Reload Hyprland configuration on demand.
  - Real-time logs displayed in the GUI.

- **Theming**:
  - Styled with the elegant **Catppuccin Mocha** dark theme for a modern look.

- **Thread-Safe**:
  - Operations run in background threads to keep the GUI responsive.

## Prerequisites

- **Operating System**: Linux (tested on systems with Hyprland).
- **Hyprland**: Installed and running as your window manager.
- **Python**: Version 3.6+ with the following modules:
  - `tkinter` (usually included with Python).
- **Dependencies**: 
  - `hyprctl` (part of Hyprland) for monitor control.
  - Optional: `waybar`, `hyprpaper`, or `swaybg` for UI and wallpaper features.

## Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/AmarasingheV/hyprland-monitor-manager.git
   cd hyprland-monitor-manager
   ```

2. **Ensure Dependencies**:
   - Verify Hyprland is installed: `hyprctl -v`.
   - Check Python: `python3 --version`.
   - Install Tkinter if missing (e.g., on Ubuntu: `sudo apt install python3-tk`).

3. **Run the Script**:
   ```bash
   python3 monitor_8_final.py
   ```

   Alternatively, make it executable:
   ```bash
   chmod +x monitor_8_final.py
   ./monitor_8_final.py
   ```

## Usage

1. **Launch the Application**:
   - Run the script to open the GUI.

2. **Monitor Management**:
   - Select a monitor from the "Monitors" section.
   - Choose a resolution from the dropdown and click **Set Resolution**.
   - Use **Turn Off** to disable secondary monitors.
   - Adjust positions with the dropdown and click **Apply Position**.

3. **Display Modes**:
   - Click **Mirror** to mirror all displays to the primary monitor.
   - Click **Extend** to arrange monitors side-by-side.
   - Use **Move Windows to Primary** to consolidate windows.

4. **Wallpaper**:
   - **Select Wallpaper**: Triggers wallpaper selection for the focused monitor (requires script at `~/.config/hypr/UserScripts/monitors/WallpaperSelectSimple.sh`).
   - **Refresh All Wallpapers**: Updates wallpapers across all monitors.

5. **Utilities**:
   - **Refresh UI**: Restarts Waybar and refreshes wallpapers.
   - **Reload Hyprland**: Reloads the Hyprland configuration.

6. **Logs**:
   - View real-time logs in the bottom panel for status updates and errors.


## Configuration

- **Wallpaper Script**: Place `WallpaperSelectSimple.sh` in `~/.config/hypr/UserScripts/monitors/` for wallpaper selection to work. Example script:
  ```bash
  #!/bin/bash
  # Replace with your wallpaper selection logic, e.g., using hyprpaper
  hyprpaper --set-wallpaper "$(zenity --file-selection)"
  ```

- **Lock File**: The script creates a lock file at `/tmp/hyprland_monitor_manager.lock` to prevent multiple instances. It’s automatically removed on exit.

## Known Issues

- Disabling the primary monitor is prevented to avoid breaking the session.
- Some operations may require a short delay for Hyprland to apply changes.
- Wallpaper features depend on external tools (`hyprpaper` or `swaybg`).


- *Full settings GUI in the future to manage all Hyprland configurations in one place.*

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [Hyprland](https://hyprland.org/), [Tkinter](https://docs.python.org/3/library/tkinter.html), and [Catppuccin](https://github.com/catppuccin/catppuccin).
- Thanks to the open-source community for inspiration and tools!
