"""
Android Control MCP Server

An MCP server that exposes Android device control capabilities via ADB.
Allows AI models to see the screen and interact with Android devices.
"""

import asyncio
import base64
import json
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, ImageContent

from adb_client import ADBClient


# Initialize ADB client
adb = ADBClient()

# Create MCP server
server = Server("android-control")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List all available Android control tools."""
    return [
        # ==================== DEVICE INFO ====================
        Tool(
            name="get_device_info",
            description="Get information about the connected Android device including model, Android version, screen size, etc.",
            inputSchema={"type": "object", "properties": {}, "required": []}
        ),
        Tool(
            name="get_screenshot",
            description="Capture a screenshot of the current screen. Returns the image as base64 encoded PNG.",
            inputSchema={"type": "object", "properties": {}, "required": []}
        ),
        Tool(
            name="get_ui_hierarchy",
            description="Get the UI hierarchy of the current screen as XML. This provides semantic information about UI elements including their text, content descriptions, bounds, and clickability.",
            inputSchema={"type": "object", "properties": {}, "required": []}
        ),
        Tool(
            name="get_current_app",
            description="Get information about the currently focused/foreground application.",
            inputSchema={"type": "object", "properties": {}, "required": []}
        ),
        
        # ==================== INPUT BASIC ====================
        Tool(
            name="tap",
            description="Simulate a tap/click at the specified screen coordinates.",
            inputSchema={
                "type": "object",
                "properties": {
                    "x": {"type": "integer", "description": "X coordinate to tap"},
                    "y": {"type": "integer", "description": "Y coordinate to tap"}
                },
                "required": ["x", "y"]
            }
        ),
        Tool(
            name="swipe",
            description="Simulate a swipe gesture from one point to another.",
            inputSchema={
                "type": "object",
                "properties": {
                    "x1": {"type": "integer", "description": "Start X coordinate"},
                    "y1": {"type": "integer", "description": "Start Y coordinate"},
                    "x2": {"type": "integer", "description": "End X coordinate"},
                    "y2": {"type": "integer", "description": "End Y coordinate"},
                    "duration_ms": {"type": "integer", "description": "Duration of swipe in milliseconds", "default": 300}
                },
                "required": ["x1", "y1", "x2", "y2"]
            }
        ),
        Tool(
            name="input_text",
            description="Input text into the currently focused text field.",
            inputSchema={
                "type": "object",
                "properties": {"text": {"type": "string", "description": "Text to input"}},
                "required": ["text"]
            }
        ),
        Tool(
            name="press_key",
            description="Press a hardware key. Common keys: KEYCODE_HOME (3), KEYCODE_BACK (4), KEYCODE_ENTER (66), KEYCODE_MENU (82), KEYCODE_POWER (26), KEYCODE_VOLUME_UP (24), KEYCODE_VOLUME_DOWN (25).",
            inputSchema={
                "type": "object",
                "properties": {"keycode": {"type": "string", "description": "The keycode to press"}},
                "required": ["keycode"]
            }
        ),
        
        # ==================== INPUT ADVANCED ====================
        Tool(
            name="long_press",
            description="Long press at the specified coordinates.",
            inputSchema={
                "type": "object",
                "properties": {
                    "x": {"type": "integer", "description": "X coordinate"},
                    "y": {"type": "integer", "description": "Y coordinate"},
                    "duration_ms": {"type": "integer", "description": "Duration in milliseconds", "default": 1000}
                },
                "required": ["x", "y"]
            }
        ),
        Tool(
            name="double_tap",
            description="Double tap at the specified coordinates.",
            inputSchema={
                "type": "object",
                "properties": {
                    "x": {"type": "integer", "description": "X coordinate"},
                    "y": {"type": "integer", "description": "Y coordinate"}
                },
                "required": ["x", "y"]
            }
        ),
        Tool(
            name="scroll_up",
            description="Scroll up on the screen.",
            inputSchema={
                "type": "object",
                "properties": {
                    "distance": {"type": "integer", "description": "Scroll distance in pixels", "default": 500}
                },
                "required": []
            }
        ),
        Tool(
            name="scroll_down",
            description="Scroll down on the screen.",
            inputSchema={
                "type": "object",
                "properties": {
                    "distance": {"type": "integer", "description": "Scroll distance in pixels", "default": 500}
                },
                "required": []
            }
        ),
        
        # ==================== APP MANAGEMENT ====================
        Tool(
            name="start_app",
            description="Launch an application by its package name.",
            inputSchema={
                "type": "object",
                "properties": {
                    "package_name": {"type": "string", "description": "The package name (e.g., 'com.android.settings')"},
                    "activity": {"type": "string", "description": "Optional: specific activity to start"}
                },
                "required": ["package_name"]
            }
        ),
        Tool(
            name="stop_app",
            description="Force stop an application.",
            inputSchema={
                "type": "object",
                "properties": {"package_name": {"type": "string", "description": "The package name"}},
                "required": ["package_name"]
            }
        ),
        Tool(
            name="clear_app_data",
            description="Clear app data and cache.",
            inputSchema={
                "type": "object",
                "properties": {"package_name": {"type": "string", "description": "The package name"}},
                "required": ["package_name"]
            }
        ),
        Tool(
            name="install_apk",
            description="Install an APK file on the device.",
            inputSchema={
                "type": "object",
                "properties": {
                    "apk_path": {"type": "string", "description": "Path to the APK file"},
                    "replace": {"type": "boolean", "description": "Replace existing app", "default": True}
                },
                "required": ["apk_path"]
            }
        ),
        Tool(
            name="uninstall_app",
            description="Uninstall an application.",
            inputSchema={
                "type": "object",
                "properties": {"package_name": {"type": "string", "description": "The package name"}},
                "required": ["package_name"]
            }
        ),
        Tool(
            name="list_packages",
            description="List installed packages on the device.",
            inputSchema={
                "type": "object",
                "properties": {
                    "filter_type": {"type": "string", "description": "'all', 'system', 'third_party', 'enabled', 'disabled'", "default": "all"}
                },
                "required": []
            }
        ),
        Tool(
            name="get_app_info",
            description="Get detailed information about an installed app.",
            inputSchema={
                "type": "object",
                "properties": {"package_name": {"type": "string", "description": "The package name"}},
                "required": ["package_name"]
            }
        ),
        
        # ==================== FILE OPERATIONS ====================
        Tool(
            name="list_files",
            description="List files in a directory on the device.",
            inputSchema={
                "type": "object",
                "properties": {"path": {"type": "string", "description": "Directory path", "default": "/sdcard"}},
                "required": []
            }
        ),
        Tool(
            name="read_file",
            description="Read text file content from the device.",
            inputSchema={
                "type": "object",
                "properties": {"device_path": {"type": "string", "description": "Path to the file on device"}},
                "required": ["device_path"]
            }
        ),
        Tool(
            name="write_file",
            description="Write text content to a file on the device. Supports ROOT permission.",
            inputSchema={
                "type": "object",
                "properties": {
                    "device_path": {"type": "string", "description": "Path to the file on device"},
                    "content": {"type": "string", "description": "Content to write"},
                    "as_root": {"type": "boolean", "description": "Execute as root (required for system/protected paths)", "default": False}
                },
                "required": ["device_path", "content"]
            }
        ),
        Tool(
            name="chmod",
            description="Change file permissions.",
            inputSchema={
                "type": "object",
                "properties": {
                    "device_path": {"type": "string", "description": "Path to the file/directory"},
                    "mode": {"type": "string", "description": "Permission mode (e.g., '755', '+x')"},
                    "recursive": {"type": "boolean", "description": "Recursive info subdirectories", "default": False},
                    "as_root": {"type": "boolean", "description": "Execute as root", "default": False}
                },
                "required": ["device_path", "mode"]
            }
        ),
        Tool(
            name="chown",
            description="Change file owner/group.",
            inputSchema={
                "type": "object",
                "properties": {
                    "device_path": {"type": "string", "description": "Path to the file/directory"},
                    "owner": {"type": "string", "description": "New owner (user)"},
                    "group": {"type": "string", "description": "New group (optional)"},
                    "recursive": {"type": "boolean", "description": "Recursive info subdirectories", "default": False},
                    "as_root": {"type": "boolean", "description": "Execute as root", "default": False}
                },
                "required": ["device_path", "owner"]
            }
        ),
        Tool(
            name="push_file",
            description="Push a file from local to device.",
            inputSchema={
                "type": "object",
                "properties": {
                    "local_path": {"type": "string", "description": "Local file path"},
                    "device_path": {"type": "string", "description": "Destination path on device"}
                },
                "required": ["local_path", "device_path"]
            }
        ),
        Tool(
            name="pull_file",
            description="Pull a file from device to local.",
            inputSchema={
                "type": "object",
                "properties": {
                    "device_path": {"type": "string", "description": "File path on device"},
                    "local_path": {"type": "string", "description": "Local destination path"}
                },
                "required": ["device_path", "local_path"]
            }
        ),
        Tool(
            name="delete_file",
            description="Delete a file on the device.",
            inputSchema={
                "type": "object",
                "properties": {"device_path": {"type": "string", "description": "Path to the file"}},
                "required": ["device_path"]
            }
        ),
        
        # ==================== SYSTEM INFO ====================
        Tool(
            name="get_battery_info",
            description="Get battery information (level, status, temperature, etc.).",
            inputSchema={"type": "object", "properties": {}, "required": []}
        ),
        Tool(
            name="get_wifi_info",
            description="Get WiFi connection information.",
            inputSchema={"type": "object", "properties": {}, "required": []}
        ),
        Tool(
            name="get_ip_address",
            description="Get the device's IP address.",
            inputSchema={"type": "object", "properties": {}, "required": []}
        ),
        Tool(
            name="get_running_processes",
            description="Get list of running processes.",
            inputSchema={"type": "object", "properties": {}, "required": []}
        ),
        
        # ==================== NOTIFICATIONS ====================
        Tool(
            name="get_notifications",
            description="Get current notifications on the device.",
            inputSchema={"type": "object", "properties": {}, "required": []}
        ),
        Tool(
            name="open_notification_panel",
            description="Open the notification panel.",
            inputSchema={"type": "object", "properties": {}, "required": []}
        ),
        Tool(
            name="close_notification_panel",
            description="Close the notification panel.",
            inputSchema={"type": "object", "properties": {}, "required": []}
        ),
        
        # ==================== SETTINGS & SYSTEM ====================
        Tool(
            name="open_settings",
            description="Open settings app. Options: '', 'wifi', 'bluetooth', 'display', 'sound', 'apps', 'battery', 'location', 'security', 'date', 'developer'.",
            inputSchema={
                "type": "object",
                "properties": {"setting": {"type": "string", "description": "Specific setting page", "default": ""}},
                "required": []
            }
        ),
        Tool(
            name="open_url",
            description="Open a URL in the browser.",
            inputSchema={
                "type": "object",
                "properties": {"url": {"type": "string", "description": "The URL to open"}},
                "required": ["url"]
            }
        ),
        Tool(
            name="toggle_wifi",
            description="Enable or disable WiFi.",
            inputSchema={
                "type": "object",
                "properties": {"enable": {"type": "boolean", "description": "True to enable, False to disable"}},
                "required": ["enable"]
            }
        ),
        Tool(
            name="toggle_airplane_mode",
            description="Toggle airplane mode.",
            inputSchema={
                "type": "object",
                "properties": {"enable": {"type": "boolean", "description": "True to enable, False to disable"}},
                "required": ["enable"]
            }
        ),
        Tool(
            name="set_brightness",
            description="Set screen brightness level.",
            inputSchema={
                "type": "object",
                "properties": {"level": {"type": "integer", "description": "Brightness level (0-255)"}},
                "required": ["level"]
            }
        ),
        Tool(
            name="set_volume",
            description="Set volume level for a stream.",
            inputSchema={
                "type": "object",
                "properties": {
                    "stream": {"type": "string", "description": "'music', 'ring', 'alarm', 'notification'"},
                    "level": {"type": "integer", "description": "Volume level (0-15)"}
                },
                "required": ["stream", "level"]
            }
        ),
        
        # ==================== SHELL & LOGS ====================
        Tool(
            name="shell_command",
            description="Execute an arbitrary shell command on the device. Supports ROOT permission.",
            inputSchema={
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "The shell command to execute"},
                    "as_root": {"type": "boolean", "description": "Execute as root", "default": False}
                },
                "required": ["command"]
            }
        ),
        Tool(
            name="get_logcat",
            description="Get logcat output.",
            inputSchema={
                "type": "object",
                "properties": {
                    "lines": {"type": "integer", "description": "Number of lines to retrieve", "default": 100},
                    "filter_tag": {"type": "string", "description": "Optional tag filter"}
                },
                "required": []
            }
        ),
        Tool(
            name="clear_logcat",
            description="Clear the logcat buffer.",
            inputSchema={"type": "object", "properties": {}, "required": []}
        ),
        Tool(
            name="get_prop",
            description="Get a system property value.",
            inputSchema={
                "type": "object",
                "properties": {"prop_name": {"type": "string", "description": "Property name (e.g., 'ro.product.model')"}},
                "required": ["prop_name"]
            }
        ),
        
        # ==================== DEVICE CONTROL ====================
        Tool(
            name="reboot",
            description="Reboot the device. Use with caution!",
            inputSchema={
                "type": "object",
                "properties": {"mode": {"type": "string", "description": "'', 'recovery', 'bootloader'", "default": ""}},
                "required": []
            }
        ),
        Tool(
            name="screen_record",
            description="Record the screen to a video file.",
            inputSchema={
                "type": "object",
                "properties": {
                    "output_path": {"type": "string", "description": "Output path on device"},
                    "duration_seconds": {"type": "integer", "description": "Recording duration", "default": 10}
                },
                "required": ["output_path"]
            }
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent | ImageContent]:
    """Execute an Android control tool."""
    
    def text_result(msg: str) -> list[TextContent]:
        return [TextContent(type="text", text=msg)]
    
    def json_result(data: Any) -> list[TextContent]:
        return [TextContent(type="text", text=json.dumps(data, indent=2, ensure_ascii=False))]
    
    def success_result(action: str, success: bool) -> list[TextContent]:
        return text_result(f"{action}: {'Success' if success else 'Failed'}")

    # ==================== DEVICE INFO ====================
    if name == "get_device_info":
        return json_result(adb.get_device_info())
    
    elif name == "get_screenshot":
        screenshot_bytes = adb.screenshot()
        if screenshot_bytes:
            return [ImageContent(type="image", data=base64.b64encode(screenshot_bytes).decode("utf-8"), mimeType="image/png")]
        return text_result("Error: Failed to capture screenshot")
    
    elif name == "get_ui_hierarchy":
        hierarchy = adb.get_ui_hierarchy()
        return text_result(hierarchy if hierarchy else "Error: Failed to get UI hierarchy")
    
    elif name == "get_current_app":
        app_info = adb.get_current_app()
        return json_result(app_info) if app_info else text_result("Error: Could not determine current app")

    # ==================== INPUT BASIC ====================
    elif name == "tap":
        return success_result(f"Tap at ({arguments['x']}, {arguments['y']})", adb.tap(arguments["x"], arguments["y"]))
    
    elif name == "swipe":
        return success_result(
            f"Swipe from ({arguments['x1']}, {arguments['y1']}) to ({arguments['x2']}, {arguments['y2']})",
            adb.swipe(arguments["x1"], arguments["y1"], arguments["x2"], arguments["y2"], arguments.get("duration_ms", 300))
        )
    
    elif name == "input_text":
        return success_result(f"Input text '{arguments['text']}'", adb.input_text(arguments["text"]))
    
    elif name == "press_key":
        return success_result(f"Press key {arguments['keycode']}", adb.press_key(arguments["keycode"]))

    # ==================== INPUT ADVANCED ====================
    elif name == "long_press":
        return success_result(f"Long press at ({arguments['x']}, {arguments['y']})", adb.long_press(arguments["x"], arguments["y"], arguments.get("duration_ms", 1000)))
    
    elif name == "double_tap":
        return success_result(f"Double tap at ({arguments['x']}, {arguments['y']})", adb.double_tap(arguments["x"], arguments["y"]))
    
    elif name == "scroll_up":
        return success_result("Scroll up", adb.scroll_up(distance=arguments.get("distance", 500)))
    
    elif name == "scroll_down":
        return success_result("Scroll down", adb.scroll_down(distance=arguments.get("distance", 500)))

    # ==================== APP MANAGEMENT ====================
    elif name == "start_app":
        return success_result(f"Start app {arguments['package_name']}", adb.start_app(arguments["package_name"], arguments.get("activity")))
    
    elif name == "stop_app":
        return success_result(f"Stop app {arguments['package_name']}", adb.stop_app(arguments["package_name"]))
    
    elif name == "clear_app_data":
        return success_result(f"Clear data for {arguments['package_name']}", adb.clear_app_data(arguments["package_name"]))
    
    elif name == "install_apk":
        success, msg = adb.install_apk(arguments["apk_path"], arguments.get("replace", True))
        return text_result(f"Install APK: {'Success' if success else 'Failed'} - {msg}")
    
    elif name == "uninstall_app":
        return success_result(f"Uninstall {arguments['package_name']}", adb.uninstall_app(arguments["package_name"]))
    
    elif name == "list_packages":
        packages = adb.list_packages(arguments.get("filter_type", "all"))
        return json_result({"count": len(packages), "packages": packages})
    
    elif name == "get_app_info":
        info = adb.get_app_info(arguments["package_name"])
        return json_result(info) if info else text_result("Error: App not found")

    # ==================== FILE OPERATIONS ====================
    elif name == "list_files":
        return json_result(adb.list_files(arguments.get("path", "/sdcard")))
    
    elif name == "read_file":
        content = adb.read_file(arguments["device_path"])
        return text_result(content if content else "Error: Failed to read file")
    
    elif name == "write_file":
        return success_result(f"Write file {arguments['device_path']}", adb.write_file(arguments["device_path"], arguments["content"], arguments.get("as_root", False)))
        
    elif name == "chmod":
        return success_result(f"Chmod {arguments['mode']} {arguments['device_path']}", adb.chmod(arguments["device_path"], arguments["mode"], arguments.get("recursive", False), arguments.get("as_root", False)))
        
    elif name == "chown":
        return success_result(f"Chown {arguments['owner']} {arguments['device_path']}", adb.chown(arguments["device_path"], arguments["owner"], arguments.get("group"), arguments.get("recursive", False), arguments.get("as_root", False)))
    
    elif name == "push_file":
        return success_result(f"Push {arguments['local_path']} -> {arguments['device_path']}", adb.push_file(arguments["local_path"], arguments["device_path"]))
    
    elif name == "pull_file":
        return success_result(f"Pull {arguments['device_path']} -> {arguments['local_path']}", adb.pull_file(arguments["device_path"], arguments["local_path"]))
    
    elif name == "delete_file":
        return success_result(f"Delete {arguments['device_path']}", adb.delete_file(arguments["device_path"]))

    # ==================== SYSTEM INFO ====================
    elif name == "get_battery_info":
        return json_result(adb.get_battery_info())
    
    elif name == "get_wifi_info":
        return json_result(adb.get_wifi_info())
    
    elif name == "get_ip_address":
        ip = adb.get_ip_address()
        return text_result(ip if ip else "Error: Could not get IP")
    
    elif name == "get_running_processes":
        return json_result(adb.get_running_processes())

    # ==================== NOTIFICATIONS ====================
    elif name == "get_notifications":
        return json_result(adb.get_notifications())
    
    elif name == "open_notification_panel":
        return success_result("Open notification panel", adb.open_notification_panel())
    
    elif name == "close_notification_panel":
        return success_result("Close notification panel", adb.close_notification_panel())

    # ==================== SETTINGS & SYSTEM ====================
    elif name == "open_settings":
        return success_result(f"Open settings '{arguments.get('setting', '')}'", adb.open_settings(arguments.get("setting", "")))
    
    elif name == "open_url":
        return success_result(f"Open URL {arguments['url']}", adb.open_url(arguments["url"]))
    
    elif name == "toggle_wifi":
        return success_result(f"WiFi {'enabled' if arguments['enable'] else 'disabled'}", adb.toggle_wifi(arguments["enable"]))
    
    elif name == "toggle_airplane_mode":
        return success_result(f"Airplane mode {'enabled' if arguments['enable'] else 'disabled'}", adb.toggle_airplane_mode(arguments["enable"]))
    
    elif name == "set_brightness":
        return success_result(f"Set brightness to {arguments['level']}", adb.set_brightness(arguments["level"]))
    
    elif name == "set_volume":
        return success_result(f"Set {arguments['stream']} volume to {arguments['level']}", adb.set_volume(arguments["stream"], arguments["level"]))

    # ==================== SHELL & LOGS ====================
    elif name == "shell_command":
        success, output = adb.shell_command(arguments["command"], arguments.get("as_root", False))
        return text_result(f"{'Success' if success else 'Failed'}:\n{output}")
    
    elif name == "get_logcat":
        output = adb.get_logcat(arguments.get("lines", 100), arguments.get("filter_tag"))
        return text_result(output if output else "Error: Failed to get logcat")
    
    elif name == "clear_logcat":
        return success_result("Clear logcat", adb.clear_logcat())
    
    elif name == "get_prop":
        value = adb.get_prop(arguments["prop_name"])
        return text_result(f"{arguments['prop_name']} = {value}" if value else "Error: Property not found")

    # ==================== DEVICE CONTROL ====================
    elif name == "reboot":
        return success_result(f"Reboot {arguments.get('mode', '')}", adb.reboot(arguments.get("mode", "")))
    
    elif name == "screen_record":
        return success_result(f"Screen record to {arguments['output_path']}", adb.screen_record(arguments["output_path"], arguments.get("duration_seconds", 10)))

    else:
        return text_result(f"Unknown tool: {name}")


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
