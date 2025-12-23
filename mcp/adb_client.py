"""
ADB Client Wrapper

Provides a Python interface to execute ADB commands for Android device control.
"""

import subprocess
import tempfile
import os
from typing import Optional, Tuple, List


class ADBClient:
    """Wrapper for ADB (Android Debug Bridge) commands."""

    def __init__(self, device_serial: Optional[str] = None):
        """
        Initialize ADB client.
        
        Args:
            device_serial: Specific device serial to target. If None, uses first available.
        """
        self.device_serial = device_serial

    def _run_adb(self, args: List[str], capture_output: bool = True, binary: bool = False) -> Tuple[int, bytes, bytes]:
        """
        Execute an ADB command.
        
        Args:
            args: List of arguments to pass to adb.
            capture_output: Whether to capture stdout/stderr.
            binary: If True, return raw bytes instead of decoded string.
            
        Returns:
            Tuple of (return_code, stdout, stderr)
        """
        cmd = ["adb"]
        if self.device_serial:
            cmd.extend(["-s", self.device_serial])
        cmd.extend(args)
        
        result = subprocess.run(
            cmd,
            capture_output=capture_output,
            timeout=30
        )
        
        return result.returncode, result.stdout, result.stderr

    def get_devices(self) -> List[dict]:
        """
        Get list of connected devices.
        
        Returns:
            List of device dictionaries with 'serial' and 'state' keys.
        """
        code, stdout, _ = self._run_adb(["devices"])
        if code != 0:
            return []
        
        devices = []
        lines = stdout.decode("utf-8").strip().split("\n")
        for line in lines[1:]:  # Skip header line
            if line.strip():
                parts = line.split()
                if len(parts) >= 2:
                    devices.append({
                        "serial": parts[0],
                        "state": parts[1]
                    })
        return devices

    def get_device_info(self) -> dict:
        """
        Get detailed device information.
        
        Returns:
            Dictionary containing device properties.
        """
        info = {}
        
        # Get device model
        code, stdout, _ = self._run_adb(["shell", "getprop", "ro.product.model"])
        if code == 0:
            info["model"] = stdout.decode("utf-8").strip()
        
        # Get Android version
        code, stdout, _ = self._run_adb(["shell", "getprop", "ro.build.version.release"])
        if code == 0:
            info["android_version"] = stdout.decode("utf-8").strip()
        
        # Get SDK version
        code, stdout, _ = self._run_adb(["shell", "getprop", "ro.build.version.sdk"])
        if code == 0:
            info["sdk_version"] = stdout.decode("utf-8").strip()
        
        # Get screen resolution
        code, stdout, _ = self._run_adb(["shell", "wm", "size"])
        if code == 0:
            size_output = stdout.decode("utf-8").strip()
            # Format: "Physical size: 1080x1920"
            if ":" in size_output:
                info["screen_size"] = size_output.split(":")[-1].strip()
        
        # Get screen density
        code, stdout, _ = self._run_adb(["shell", "wm", "density"])
        if code == 0:
            density_output = stdout.decode("utf-8").strip()
            if ":" in density_output:
                info["screen_density"] = density_output.split(":")[-1].strip()
        
        # Get manufacturer
        code, stdout, _ = self._run_adb(["shell", "getprop", "ro.product.manufacturer"])
        if code == 0:
            info["manufacturer"] = stdout.decode("utf-8").strip()
        
        return info

    def screenshot(self) -> Optional[bytes]:
        """
        Capture a screenshot from the device.
        
        Returns:
            PNG image bytes, or None if failed.
        """
        # Use exec-out for direct binary output (faster than pull)
        code, stdout, stderr = self._run_adb(["exec-out", "screencap", "-p"], binary=True)
        if code == 0 and stdout:
            return stdout
        return None

    def get_ui_hierarchy(self) -> Optional[str]:
        """
        Dump the UI hierarchy as XML.
        
        Returns:
            XML string representing UI hierarchy, or None if failed.
        """
        # Dump UI to a file on device
        device_path = "/sdcard/window_dump.xml"
        code, _, _ = self._run_adb(["shell", "uiautomator", "dump", device_path])
        if code != 0:
            return None
        
        # Read the file content
        code, stdout, _ = self._run_adb(["shell", "cat", device_path])
        if code != 0:
            return None
        
        # Clean up
        self._run_adb(["shell", "rm", device_path])
        
        return stdout.decode("utf-8")

    def tap(self, x: int, y: int) -> bool:
        """
        Simulate a tap at the specified coordinates.
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            True if successful, False otherwise.
        """
        code, _, _ = self._run_adb(["shell", "input", "tap", str(x), str(y)])
        return code == 0

    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration_ms: int = 300) -> bool:
        """
        Simulate a swipe gesture.
        
        Args:
            x1: Start X coordinate
            y1: Start Y coordinate
            x2: End X coordinate
            y2: End Y coordinate
            duration_ms: Duration of swipe in milliseconds
            
        Returns:
            True if successful, False otherwise.
        """
        code, _, _ = self._run_adb([
            "shell", "input", "swipe",
            str(x1), str(y1), str(x2), str(y2), str(duration_ms)
        ])
        return code == 0

    def input_text(self, text: str) -> bool:
        """
        Input text on the device.
        
        Args:
            text: Text to input. Spaces will be escaped.
            
        Returns:
            True if successful, False otherwise.
        """
        # Replace spaces with %s for adb shell input
        escaped_text = text.replace(" ", "%s")
        code, _, _ = self._run_adb(["shell", "input", "text", escaped_text])
        return code == 0

    def press_key(self, keycode: str) -> bool:
        """
        Press a key by its keycode.
        
        Common keycodes:
            - KEYCODE_HOME (3)
            - KEYCODE_BACK (4)
            - KEYCODE_ENTER (66)
            - KEYCODE_MENU (82)
            - KEYCODE_POWER (26)
            
        Args:
            keycode: The keycode name or number (e.g., "KEYCODE_HOME" or "3")
            
        Returns:
            True if successful, False otherwise.
        """
        code, _, _ = self._run_adb(["shell", "input", "keyevent", keycode])
        return code == 0

    def start_app(self, package_name: str, activity: Optional[str] = None) -> bool:
        """
        Start an application.
        
        Args:
            package_name: The package name (e.g., "com.example.app")
            activity: Optional activity name. If None, launches main activity.
            
        Returns:
            True if successful, False otherwise.
        """
        if activity:
            component = f"{package_name}/{activity}"
            code, _, _ = self._run_adb(["shell", "am", "start", "-n", component])
        else:
            code, _, _ = self._run_adb([
                "shell", "monkey", "-p", package_name,
                "-c", "android.intent.category.LAUNCHER", "1"
            ])
        return code == 0

    def get_current_app(self) -> Optional[dict]:
        """
        Get information about the currently focused app.
        
        Returns:
            Dictionary with 'package' and 'activity' keys, or None if failed.
        """
        code, stdout, _ = self._run_adb([
            "shell", "dumpsys", "window", "windows",
        ])
        if code != 0:
            return None
        
        output = stdout.decode("utf-8")
        # Look for mCurrentFocus or mFocusedApp
        for line in output.split("\n"):
            if "mCurrentFocus" in line or "mFocusedApp" in line:
                # Extract package/activity
                if "/" in line:
                    # Format: "... com.example.app/com.example.app.MainActivity ..."
                    parts = line.split()
                    for part in parts:
                        if "/" in part and "." in part:
                            app_parts = part.rstrip("}").split("/")
                            if len(app_parts) >= 2:
                                return {
                                    "package": app_parts[0],
                                    "activity": app_parts[1]
                                }
        return None

    # ==================== APP MANAGEMENT ====================
    
    def stop_app(self, package_name: str) -> bool:
        """Force stop an application."""
        code, _, _ = self._run_adb(["shell", "am", "force-stop", package_name])
        return code == 0

    def clear_app_data(self, package_name: str) -> bool:
        """Clear app data and cache."""
        code, _, _ = self._run_adb(["shell", "pm", "clear", package_name])
        return code == 0

    def install_apk(self, apk_path: str, replace: bool = True) -> Tuple[bool, str]:
        """Install an APK file."""
        args = ["install"]
        if replace:
            args.append("-r")
        args.append(apk_path)
        code, stdout, stderr = self._run_adb(args)
        message = stdout.decode("utf-8") + stderr.decode("utf-8")
        return code == 0, message.strip()

    def uninstall_app(self, package_name: str) -> bool:
        """Uninstall an application."""
        code, _, _ = self._run_adb(["uninstall", package_name])
        return code == 0

    def list_packages(self, filter_type: str = "all") -> List[str]:
        """
        List installed packages.
        
        Args:
            filter_type: 'all', 'system', 'third_party', 'enabled', 'disabled'
        """
        args = ["shell", "pm", "list", "packages"]
        if filter_type == "system":
            args.append("-s")
        elif filter_type == "third_party":
            args.append("-3")
        elif filter_type == "enabled":
            args.append("-e")
        elif filter_type == "disabled":
            args.append("-d")
        
        code, stdout, _ = self._run_adb(args)
        if code != 0:
            return []
        
        packages = []
        for line in stdout.decode("utf-8").strip().split("\n"):
            if line.startswith("package:"):
                packages.append(line[8:])
        return packages

    def get_app_info(self, package_name: str) -> Optional[dict]:
        """Get detailed info about an app."""
        code, stdout, _ = self._run_adb(["shell", "dumpsys", "package", package_name])
        if code != 0:
            return None
        
        output = stdout.decode("utf-8")
        info = {"package": package_name}
        
        for line in output.split("\n"):
            line = line.strip()
            if line.startswith("versionName="):
                info["version_name"] = line.split("=")[1]
            elif line.startswith("versionCode="):
                info["version_code"] = line.split("=")[1].split()[0]
            elif line.startswith("firstInstallTime="):
                info["first_install"] = line.split("=")[1]
            elif line.startswith("lastUpdateTime="):
                info["last_update"] = line.split("=")[1]
        
        return info

    # ==================== FILE OPERATIONS ====================
    
    def push_file(self, local_path: str, device_path: str) -> bool:
        """Push a file to the device."""
        code, _, _ = self._run_adb(["push", local_path, device_path])
        return code == 0

    def pull_file(self, device_path: str, local_path: str) -> bool:
        """Pull a file from the device."""
        code, _, _ = self._run_adb(["pull", device_path, local_path])
        return code == 0

    def list_files(self, path: str = "/sdcard") -> List[dict]:
        """List files in a directory."""
        code, stdout, _ = self._run_adb(["shell", "ls", "-la", path])
        if code != 0:
            return []
        
        files = []
        for line in stdout.decode("utf-8").strip().split("\n"):
            parts = line.split()
            if len(parts) >= 8:
                files.append({
                    "permissions": parts[0],
                    "size": parts[4] if len(parts) > 4 else "0",
                    "date": f"{parts[5]} {parts[6]}" if len(parts) > 6 else "",
                    "name": " ".join(parts[7:]) if len(parts) > 7 else parts[-1],
                    "is_dir": parts[0].startswith("d")
                })
        return files

    def file_exists(self, device_path: str) -> bool:
        """Check if a file exists on device."""
        code, _, _ = self._run_adb(["shell", "test", "-e", device_path, "&&", "echo", "1"])
        return code == 0

    def delete_file(self, device_path: str) -> bool:
        """Delete a file on device."""
        code, _, _ = self._run_adb(["shell", "rm", "-f", device_path])
        return code == 0

    def read_file(self, device_path: str) -> Optional[str]:
        """Read text file content from device."""
        code, stdout, _ = self._run_adb(["shell", "cat", device_path])
        if code == 0:
            return stdout.decode("utf-8")
        return None

    # ==================== CLIPBOARD ====================
    
    def set_clipboard(self, text: str) -> bool:
        """Set clipboard text (requires Android 10+)."""
        # Escape special characters
        escaped = text.replace("'", "'\\''")
        code, _, _ = self._run_adb(["shell", "am", "broadcast", "-a", "clipper.set", "-e", "text", f"'{escaped}'"])
        return code == 0

    def get_clipboard(self) -> Optional[str]:
        """Get clipboard text (requires clipper service or root)."""
        code, stdout, _ = self._run_adb(["shell", "am", "broadcast", "-a", "clipper.get"])
        if code == 0:
            return stdout.decode("utf-8").strip()
        return None

    # ==================== NOTIFICATIONS ====================
    
    def get_notifications(self) -> List[dict]:
        """Get current notifications."""
        code, stdout, _ = self._run_adb(["shell", "dumpsys", "notification", "--noredact"])
        if code != 0:
            return []
        
        notifications = []
        output = stdout.decode("utf-8")
        current_notif = {}
        
        for line in output.split("\n"):
            if "pkg=" in line:
                if current_notif:
                    notifications.append(current_notif)
                current_notif = {}
                # Extract package
                for part in line.split():
                    if part.startswith("pkg="):
                        current_notif["package"] = part[4:]
            elif "android.title=" in line:
                current_notif["title"] = line.split("android.title=")[-1].strip()
            elif "android.text=" in line:
                current_notif["text"] = line.split("android.text=")[-1].strip()
        
        if current_notif:
            notifications.append(current_notif)
        
        return notifications[:20]  # Limit to 20

    def open_notification_panel(self) -> bool:
        """Open the notification panel."""
        code, _, _ = self._run_adb(["shell", "cmd", "statusbar", "expand-notifications"])
        return code == 0

    def close_notification_panel(self) -> bool:
        """Close the notification panel."""
        code, _, _ = self._run_adb(["shell", "cmd", "statusbar", "collapse"])
        return code == 0

    # ==================== SYSTEM INFO ====================
    
    def get_battery_info(self) -> dict:
        """Get battery information."""
        code, stdout, _ = self._run_adb(["shell", "dumpsys", "battery"])
        if code != 0:
            return {}
        
        info = {}
        for line in stdout.decode("utf-8").split("\n"):
            line = line.strip()
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip().lower().replace(" ", "_")
                info[key] = value.strip()
        return info

    def get_wifi_info(self) -> dict:
        """Get WiFi connection info."""
        code, stdout, _ = self._run_adb(["shell", "dumpsys", "wifi"])
        if code != 0:
            return {}
        
        info = {}
        output = stdout.decode("utf-8")
        
        for line in output.split("\n"):
            if "mWifiInfo" in line:
                # Extract SSID
                if "SSID:" in line:
                    ssid_part = line.split("SSID:")[1].split(",")[0].strip()
                    info["ssid"] = ssid_part
                if "RSSI:" in line:
                    rssi_part = line.split("RSSI:")[1].split(",")[0].strip()
                    info["rssi"] = rssi_part
                if "Link speed:" in line:
                    speed_part = line.split("Link speed:")[1].split(",")[0].strip()
                    info["link_speed"] = speed_part
        
        return info

    def get_ip_address(self) -> Optional[str]:
        """Get device IP address."""
        code, stdout, _ = self._run_adb(["shell", "ip", "route", "get", "1"])
        if code == 0:
            output = stdout.decode("utf-8")
            if "src" in output:
                parts = output.split("src")
                if len(parts) > 1:
                    return parts[1].strip().split()[0]
        return None

    def get_running_processes(self) -> List[dict]:
        """Get list of running processes."""
        code, stdout, _ = self._run_adb(["shell", "ps", "-A"])
        if code != 0:
            return []
        
        processes = []
        lines = stdout.decode("utf-8").strip().split("\n")
        
        for line in lines[1:]:  # Skip header
            parts = line.split()
            if len(parts) >= 9:
                processes.append({
                    "user": parts[0],
                    "pid": parts[1],
                    "name": parts[-1]
                })
        
        return processes[:50]  # Limit

    # ==================== INPUT ADVANCED ====================
    
    def long_press(self, x: int, y: int, duration_ms: int = 1000) -> bool:
        """Long press at coordinates."""
        return self.swipe(x, y, x, y, duration_ms)

    def double_tap(self, x: int, y: int) -> bool:
        """Double tap at coordinates."""
        self.tap(x, y)
        import time
        time.sleep(0.1)
        return self.tap(x, y)

    def pinch(self, center_x: int, center_y: int, start_distance: int, end_distance: int) -> bool:
        """Simulate pinch gesture (requires multi-touch via sendevent)."""
        # This is a simplified version - real pinch requires sendevent
        # For now, we use swipe as approximation
        if start_distance > end_distance:
            # Pinch in
            return self.swipe(center_x - start_distance//2, center_y, 
                            center_x - end_distance//2, center_y, 300)
        else:
            # Pinch out
            return self.swipe(center_x - start_distance//2, center_y,
                            center_x - end_distance//2, center_y, 300)

    def scroll_up(self, x: Optional[int] = None, distance: int = 500) -> bool:
        """Scroll up on screen."""
        if x is None:
            # Get screen center
            info = self.get_device_info()
            if "screen_size" in info:
                x = int(info["screen_size"].split("x")[0]) // 2
            else:
                x = 540
        center_y = 1200
        return self.swipe(x, center_y, x, center_y + distance, 300)

    def scroll_down(self, x: Optional[int] = None, distance: int = 500) -> bool:
        """Scroll down on screen."""
        if x is None:
            info = self.get_device_info()
            if "screen_size" in info:
                x = int(info["screen_size"].split("x")[0]) // 2
            else:
                x = 540
        center_y = 1200
        return self.swipe(x, center_y, x, center_y - distance, 300)

    # ==================== MEDIA ====================
    
    def take_photo(self, save_path: str = "/sdcard/DCIM/photo.jpg") -> bool:
        """Trigger camera to take a photo (opens camera app)."""
        code, _, _ = self._run_adb([
            "shell", "am", "start", "-a", "android.media.action.IMAGE_CAPTURE",
            "--ez", "android.intent.extra.quickCapture", "true"
        ])
        return code == 0

    def screen_record(self, output_path: str, duration_seconds: int = 10) -> bool:
        """Record screen video."""
        code, _, _ = self._run_adb([
            "shell", "screenrecord", "--time-limit", str(duration_seconds), output_path
        ])
        return code == 0

    def set_brightness(self, level: int) -> bool:
        """Set screen brightness (0-255)."""
        level = max(0, min(255, level))
        code, _, _ = self._run_adb(["shell", "settings", "put", "system", "screen_brightness", str(level)])
        return code == 0

    def set_volume(self, stream: str, level: int) -> bool:
        """
        Set volume level.
        
        Args:
            stream: 'music', 'ring', 'alarm', 'notification'
            level: Volume level (0-15 typically)
        """
        stream_map = {
            "music": "3",
            "ring": "2", 
            "alarm": "4",
            "notification": "5"
        }
        stream_id = stream_map.get(stream, "3")
        code, _, _ = self._run_adb(["shell", "media", "volume", "--stream", stream_id, "--set", str(level)])
        return code == 0

    # ==================== SHELL & MISC ====================
    
    def shell_command(self, command: str, as_root: bool = False) -> Tuple[bool, str]:
        """
        Execute arbitrary shell command.
        
        Args:
            command: The command to execute.
            as_root: Whether to run with root privileges (su).
        """
        if as_root:
            # Escape single quotes for the outer shell wrapper
            escaped_cmd = command.replace("'", "'\\''")
            full_cmd = f"su -c '{escaped_cmd}'"
            args = ["shell", full_cmd]
        else:
            args = ["shell", command]
            
        code, stdout, stderr = self._run_adb(args)
        output = stdout.decode("utf-8") + stderr.decode("utf-8")
        return code == 0, output.strip()

    def write_file(self, device_path: str, content: str, as_root: bool = False) -> bool:
        """
        Write string content to a file on device.
        Uses base64 decoding to avoid special character escaping issues.
        """
        import base64
        b64_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")
        
        # Command to decode base64 and write to file
        cmd = f"echo '{b64_content}' | base64 -d > '{device_path}'"
        
        success, _ = self.shell_command(cmd, as_root=as_root)
        return success

    def chmod(self, device_path: str, mode: str, recursive: bool = False, as_root: bool = False) -> bool:
        """Change file permissions (e.g., '755' or '+x')."""
        flags = "-R" if recursive else ""
        cmd = f"chmod {flags} {mode} '{device_path}'"
        success, _ = self.shell_command(cmd, as_root=as_root)
        return success

    def chown(self, device_path: str, owner: str, group: Optional[str] = None, recursive: bool = False, as_root: bool = False) -> bool:
        """Change file owner and group."""
        flags = "-R" if recursive else ""
        owner_group = f"{owner}:{group}" if group else owner
        cmd = f"chown {flags} {owner_group} '{device_path}'"
        success, _ = self.shell_command(cmd, as_root=as_root)
        return success

    def get_prop(self, prop_name: str) -> Optional[str]:
        """Get a system property."""
        code, stdout, _ = self._run_adb(["shell", "getprop", prop_name])
        if code == 0:
            return stdout.decode("utf-8").strip()
        return None

    def open_url(self, url: str) -> bool:
        """Open a URL in browser."""
        code, _, _ = self._run_adb([
            "shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", url
        ])
        return code == 0

    def open_settings(self, setting: str = "") -> bool:
        """
        Open settings app.
        
        Args:
            setting: Specific setting page (e.g., 'wifi', 'bluetooth', 'display', 'sound')
        """
        settings_map = {
            "": "android.settings.SETTINGS",
            "wifi": "android.settings.WIFI_SETTINGS",
            "bluetooth": "android.settings.BLUETOOTH_SETTINGS",
            "display": "android.settings.DISPLAY_SETTINGS",
            "sound": "android.settings.SOUND_SETTINGS",
            "apps": "android.settings.APPLICATION_SETTINGS",
            "battery": "android.intent.action.POWER_USAGE_SUMMARY",
            "location": "android.settings.LOCATION_SOURCE_SETTINGS",
            "security": "android.settings.SECURITY_SETTINGS",
            "date": "android.settings.DATE_SETTINGS",
            "developer": "android.settings.APPLICATION_DEVELOPMENT_SETTINGS",
        }
        action = settings_map.get(setting, "android.settings.SETTINGS")
        code, _, _ = self._run_adb(["shell", "am", "start", "-a", action])
        return code == 0

    def toggle_wifi(self, enable: bool) -> bool:
        """Enable or disable WiFi."""
        action = "enable" if enable else "disable"
        code, _, _ = self._run_adb(["shell", "svc", "wifi", action])
        return code == 0

    def toggle_airplane_mode(self, enable: bool) -> bool:
        """Toggle airplane mode."""
        value = "1" if enable else "0"
        self._run_adb(["shell", "settings", "put", "global", "airplane_mode_on", value])
        code, _, _ = self._run_adb([
            "shell", "am", "broadcast", "-a", "android.intent.action.AIRPLANE_MODE"
        ])
        return code == 0

    def reboot(self, mode: str = "") -> bool:
        """
        Reboot device.
        
        Args:
            mode: '', 'recovery', 'bootloader'
        """
        args = ["reboot"]
        if mode:
            args.append(mode)
        code, _, _ = self._run_adb(args)
        return code == 0

    def get_logcat(self, lines: int = 100, filter_tag: Optional[str] = None) -> str:
        """Get logcat output."""
        args = ["logcat", "-d", "-t", str(lines)]
        if filter_tag:
            args.extend(["-s", filter_tag])
        code, stdout, _ = self._run_adb(args)
        if code == 0:
            return stdout.decode("utf-8")
        return ""

    def clear_logcat(self) -> bool:
        """Clear logcat buffer."""
        code, _, _ = self._run_adb(["logcat", "-c"])
        return code == 0

    def wait_for_device(self, timeout: int = 30) -> bool:
        """Wait for device to be available."""
        try:
            result = subprocess.run(
                ["adb", "wait-for-device"],
                timeout=timeout,
                capture_output=True
            )
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            return False
