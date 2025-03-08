import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox, QGroupBox, QFormLayout, QFrame, QTabWidget
from PyQt5.QtGui import QColor, QPalette
import subprocess
import json
import os

# Run shell commands and return output
def run_command(command):
    try:
        print(f"Running command: {command}")  # Debugging line
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        print(f"Command output: {result.stdout}")  # Debugging line
        return result.stdout.strip()
    except Exception as e:
        print(f"Error: {str(e)}")  # Debugging line
        return f"Error: {str(e)}"

# Fetch monitor info using hyprctl
def get_monitors():
    output = run_command("hyprctl monitors -j")
    if output.startswith("Error"):
        return []
    return json.loads(output)

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
    run_command(cmd)
    update_status(f"Set {monitor} to {resolution}")

# Toggle monitor on/off
def toggle_monitor(monitor, enable=True):
    state = "enable" if enable else "disable"
    cmd = f"hyprctl keyword monitor {monitor},{state}"
    run_command(cmd)
    update_status(f"{monitor} {'enabled' if enable else 'disabled'}")

# Set wallpaper by calling the script
def set_wallpaper(monitor):
    script_path = os.path.expanduser("~/.config/hypr/UserScripts/monitors/WallpaperSelectSimple.sh")
    if os.path.exists(script_path):
        run_command(f"bash {script_path}")
        update_status(f"Wallpaper selection triggered for focused monitor")
    else:
        update_status(f"Wallpaper script not found at {script_path}")

# Update status label
def update_status(message):
    status_label.setText(message)

# Refresh monitor list and UI
def refresh_monitors():
    print("Refreshing monitors...")  # Debugging line
    monitor_list_widget.clear()
    monitors = get_monitors()
    if monitors:
        for monitor in monitors:
            mon_name = monitor["name"]
            monitor_list_widget.addItem(mon_name)
    else:
        update_status("No monitors found")

# Main Window UI
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hyprland Manager")
        self.setGeometry(100, 100, 800, 500)

        # Set Cappuccino Mocha color palette
        self.setStyleSheet("""
            QWidget {
                background-color: #D2B48C;  /* Mocha */
                color: #4B3621;  /* Dark Brown Text */
            }
            QPushButton {
                background-color: #6F4F37;  /* Cappuccino */
                color: white;
                border: none;
                padding: 10px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #4B3621;
            }
            QComboBox {
                background-color: #6F4F37;
                color: white;
                border: none;
                padding: 5px;
            }
            QLabel {
                font-size: 16px;
                color: #4B3621;
            }
        """)

        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Create a tab widget
        tabs = QTabWidget(self)

        # Monitor Section
        monitor_tab = QWidget()
        monitor_layout = QVBoxLayout()
        monitor_group = QGroupBox("Monitors")
        monitor_form = QFormLayout()

        self.monitor_list_widget = QComboBox()
        monitor_layout.addWidget(self.monitor_list_widget)
        self.monitor_list_widget.addItem("Select Monitor")
        monitor_form.addRow("Available Monitors", self.monitor_list_widget)

        monitor_buttons_layout = QHBoxLayout()
        monitor_buttons_layout.addWidget(QPushButton("Refresh Monitors", self, clicked=self.refresh_monitors))
        monitor_buttons_layout.addWidget(QPushButton("Turn Off", self, clicked=self.toggle_monitor_off))
        monitor_buttons_layout.addWidget(QPushButton("Turn On", self, clicked=self.toggle_monitor_on))
        monitor_layout.addLayout(monitor_buttons_layout)

        monitor_group.setLayout(monitor_form)
        monitor_layout.addWidget(monitor_group)
        monitor_tab.setLayout(monitor_layout)

        # Wallpaper Section
        wallpaper_tab = QWidget()
        wallpaper_layout = QVBoxLayout()

        wallpaper_buttons_layout = QHBoxLayout()
        wallpaper_buttons_layout.addWidget(QPushButton("Set Wallpaper", self, clicked=self.set_wallpaper))
        wallpaper_layout.addLayout(wallpaper_buttons_layout)

        wallpaper_tab.setLayout(wallpaper_layout)

        # Hyprland Functions Section
        hyprland_tab = QWidget()
        hyprland_layout = QVBoxLayout()

        hyprland_buttons_layout = QHBoxLayout()
        hyprland_buttons_layout.addWidget(QPushButton("Set Display Mode", self))
        hyprland_buttons_layout.addWidget(QPushButton("Mouse Control", self))
        hyprland_layout.addLayout(hyprland_buttons_layout)

        hyprland_tab.setLayout(hyprland_layout)

        # Add tabs to the tab widget
        tabs.addTab(monitor_tab, "Monitor")
        tabs.addTab(wallpaper_tab, "Wallpaper")
        tabs.addTab(hyprland_tab, "Hyprland Functions")

        layout.addWidget(tabs)

        # Status Bar
        global status_label
        status_label = QLabel("Ready")
        layout.addWidget(status_label)

        self.setLayout(layout)

    def refresh_monitors(self):
        refresh_monitors()

    def toggle_monitor_on(self):
        monitor = self.monitor_list_widget.currentText()
        if monitor != "Select Monitor":
            toggle_monitor(monitor, True)

    def toggle_monitor_off(self):
        monitor = self.monitor_list_widget.currentText()
        if monitor != "Select Monitor":
            toggle_monitor(monitor, False)

    def set_wallpaper(self):
        monitor = self.monitor_list_widget.currentText()
        if monitor != "Select Monitor":
            set_wallpaper(monitor)

# Running the application
def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()

