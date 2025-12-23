# Android Control MCP Server

![License](https://img.shields.io/badge/license-MIT-blue.svg) ![Python](https://img.shields.io/badge/python-3.10%2B-green) ![Platform](https://img.shields.io/badge/platform-Android-orange)

这是一个基于 Model Context Protocol (MCP) 的 Android 控制服务器。它允许 AI Agent（如 Claude Desktop、Cursor 等）通过 ADB 协议直接控制 Android 设备，实现从“读取屏幕”到“Root 级文件操作”的全方位控制。

## ✨ 功能特性表

服务器目前支持 40+ 种工具操作，详细功能如下：

### 📱 核心与输入控制
| 工具名称 | 功能描述 | 参数示例 |
| :--- | :--- | :--- |
| `get_device_info` | 获取设备型号、版本、屏幕信息 | 无 |
| `get_screenshot` | 获取当前屏幕截图 (Base64) | 无 |
| `get_ui_hierarchy` | 获取当前界面 XML 结构 | 无 |
| `tap` | 点击屏幕指定坐标 | `x=500, y=1000` |
| `swipe` | 模拟滑动操作 | `x1=100, y1=500, x2=100, y2=100` |
| `input_text` | 在焦点输入框输入文本 | `text="Hello World"` |
| `press_key` | 模拟物理按键 | `keycode=3` (HOME), `4` (BACK) |
| `long_press` | 长按指定坐标 | `x=500, y=500` |

### 📦 应用与进程管理
| 工具名称 | 功能描述 | 参数示例 |
| :--- | :--- | :--- |
| `start_app` | 启动指定应用 | `package_name="com.android.settings"` |
| `stop_app` | 强制停止应用 | `package_name="..."` |
| `list_packages` | 列出已安装应用 | `filter_type="third_party"` |
| `install_apk` | 安装 APK 文件 | `apk_path="/path/to/app.apk"` |
| `uninstall_app` | 卸载应用 | `package_name="..."` |
| `clear_app_data` | 清除应用全部数据 | `package_name="..."` |
| `get_current_app` | 获取当前前台应用包名 | 无 |

### 📂 文件系统 (支持 Root)
| 工具名称 | 功能描述 | 权限说明 |
| :--- | :--- | :--- |
| `list_files` | 列出目录文件 | 普通/Root |
| `read_file` | 读取文件内容 | 支持 Root 读取系统文件 |
| `write_file` | 写入文件内容 | **支持 Root 写入** (如 `/data/data`) |
| `delete_file` | 删除文件 | 普通/Root |
| `push_file` | 本地文件推送到手机 | ADB 协议 |
| `pull_file` | 手机文件拉取到本地 | ADB 协议 |
| `chmod` | 修改文件权限 | 支持 Root (如 `777`) |
| `chown` | 修改文件所有者 | 支持 Root |

### ⚙️ 系统设置与监控
| 工具名称 | 功能描述 | 示例 |
| :--- | :--- | :--- |
| `open_settings` | 打开系统设置页 | `setting="wifi"` |
| `toggle_wifi` | 开关 WiFi | `enable=true` / `false` |
| `get_battery_info` | 获取电池电量与状态 | 无 |
| `shell_command` | 执行任意 ADB Shell 命令 | 可选 `as_root=true` 执行 `su` 命令 |

---

## 🚀 使用指南

### 第一步：准备工作
1. 确保电脑已安装 **Python 3.10** 或更高版本。
2. 确保电脑已安装 **ADB 工具**，并且 Android 设备已连接（开启 USB 调试）。
   - 在终端输入 `adb devices` 确认能看到设备。

### 第二步：安装与配置
本服务包含一个自启动脚本，会自动处理依赖安装。

**对于 Claude Desktop / Cursor 用户：**
找到你的 MCP 配置文件（通常位于 `~/Library/Application Support/Claude/claude_desktop_config.json` 或项目特定的 `mcp_config.json`），添加以下配置：

```json
{
  "mcpServers": {
    "android_control": {
      "command": "/你的项目路径/control_android_mcp/mcp/start_server.sh",
      "args": []
    }
  }
}
```
> ⚠️ **注意**：请务必然将 `/你的项目路径/...` 替换为 `start_server.sh` 脚本在您电脑上的**绝对路径**。

### 第三步：开始使用
配置生效后，重启 AI 客户端。你现在可以直接用自然语言控制手机了：

*   **"帮我截个图看看现在屏幕上显示什么。"** -> AI 会调用 `get_screenshot`
*   **"打开设置里的 WiFi 页面。"** -> AI 会调用 `open_settings`
*   **"把 /sdcard/test.txt 的权限改成 777。"** -> AI 会调用 `chmod`
*   **"帮我看看 Clash Meta 这种 VPN 软件有没有运行，没有的话启动它。"** -> AI 会组合使用 `list_packages`, `get_running_processes`, `start_app`。

---

## 🛠️ 常见问题

**Q: 报错 "externally-managed-environment" 怎么办？**
A: 我们的启动脚本 `start_server.sh` 已经内置了修复方案（使用 `--break-system-packages`），请确保配置的是该脚本的路径，而不是直接运行 python。

**Q: 如何使用 Root 权限？**
A: 只要你的手机已经 Root（安装了 Magisk 等），在让 AI 执行敏感操作时（如修改系统文件），只需告诉它“使用 Root 权限”或者 AI 判断需要 Root 时，它会自动设置 `as_root=True` 参数。

---
**项目维护**: 该项目旨在为大模型提供最完整的 Android 操作接口。如有建议，欢迎提交 Issue。
