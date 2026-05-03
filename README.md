# 🐾 桌面电子宠物系统 (Desktop Pet System)

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8%2B-blue?logo=python" alt="Python 3.8+">
  <img src="https://img.shields.io/badge/Platform-Windows%2010%2F11-blue?logo=windows" alt="Windows">
  <img src="https://img.shields.io/badge/License-MIT-green" alt="MIT License">
  <img src="https://img.shields.io/badge/Version-1.0.0-orange" alt="Version">
</p>

> 🎮 一款跨平台桌面电子宠物养成系统，支持 **GUI 图形界面** 和 **终端命令行** 两种模式。领养你的专属宠物，喂食、玩耍、睡觉，见证它从幼崽成长为忠实伙伴！

---

## 📑 目录

- [✨ 功能特性](#-功能特性)
- [📸 截图](#-截图)
- [💻 系统要求](#-系统要求)
- [🚀 安装指南](#-安装指南)
- [📖 使用教程](#-使用教程)
- [📊 宠物属性说明](#-宠物属性说明)
- [⚔️ 互动效果表](#️-互动效果表)
- [⏰ 时间衰减机制](#-时间衰减机制)
- [❓ 常见问题 (FAQ)](#-常见问题-faq)
- [🏗️ 开发架构](#️-开发架构)
- [🧪 测试](#-测试)
- [📄 许可证](#-许可证)

---

## ✨ 功能特性

### 🖥️ GUI 图形界面版本 (`desktop_pet.py`)

| # | 功能 | 说明 |
|---|------|------|
| 1 | 🪟 **浮动桌面窗口** | 始终置顶 (Always-on-Top)，宠物常驻桌面不被遮挡 |
| 2 | 🖱️ **拖拽移动** | 鼠标左键拖拽宠物自由移动到屏幕任意位置 |
| 3 | 🐾 **五种可爱宠物** | 猫🐱 / 狗🐶 / 兔子🐰 / 龙🐉 / 狐🦊，各有独特动画 |
| 4 | 🎭 **表情动画系统** | 宠物拥有待机、开心、饥饿、困倦等多种表情状态 |
| 5 | 💬 **语音气泡** | 宠物会通过气泡对话框表达心情和需求 |
| 6 | 📊 **状态栏显示** | 实时显示饥饿、快乐、能量、健康、年龄等属性 |
| 7 | 📋 **右键菜单** | 喂食🍖、玩耍🎾、睡觉💤、查看状态、设置等选项 |
| 8 | 💾 **自动存档** | 宠物数据自动保存至 `pets_gui.json`，关闭后不丢失 |
| 9 | 🔔 **系统托盘** | 可选最小化到系统托盘（需安装 `pystray` 和 `Pillow`） |
| 10 | 🎨 **主题切换** | 支持浅色/深色主题，适配不同桌面风格 |

### 💻 终端命令行版本 (`pet_system.py`)

| # | 功能 | 说明 |
|---|------|------|
| 1 | 🎨 **ASCII 艺术** | 终端中以 ASCII 字符绘制宠物图案 |
| 2 | 📝 **菜单驱动** | 清晰的数字菜单界面，操作简单直观 |
| 3 | 🐾 **五种宠物可选** | 与 GUI 版本相同的宠物类型 |
| 4 | 📊 **详细状态面板** | 以进度条形式展示各项属性值 |
| 5 | 🍖 **互动操作** | 喂食、玩耍、睡觉、治疗等多种操作 |
| 6 | 📜 **日志记录** | 查看宠物的成长日志和互动历史 |
| 7 | 💾 **存档管理** | 支持多宠物存档，数据保存至 `pets.json` |
| 8 | ⚡ **快捷键操作** | 单键快捷操作，提升使用效率 |
| 9 | 📈 **成长系统** | 宠物随时间成长，外观和行为发生变化 |
| 10 | 🔔 **提醒通知** | 属性过低时主动提醒，避免宠物不开心 |

---

## 📸 截图

### GUI 版本

<!-- TODO: 替换为实际截图 -->
<!-- ![GUI 主界面](screenshots/gui_main.png) -->
<!-- ![GUI 右键菜单](screenshots/gui_menu.png) -->
<!-- ![GUI 语音气泡](screenshots/gui_bubble.png) -->

```
┌─────────────────────────────────────┐
│  GUI 版本截图占位符                   │
│  请在 screenshots/ 目录下添加截图后   │
│  取消上方的注释以显示图片              │
└─────────────────────────────────────┘
```

### 终端版本

<!-- TODO: 替换为实际截图 -->
<!-- ![终端主界面](screenshots/terminal_main.png) -->
<!-- ![终端状态面板](screenshots/terminal_status.png) -->

```
┌─────────────────────────────────────┐
│  终端版本截图占位符                   │
│  请在 screenshots/ 目录下添加截图后   │
│  取消上方的注释以显示图片              │
└─────────────────────────────────────┘
```

---

## 💻 系统要求

| 项目 | 最低要求 | 推荐配置 |
|------|---------|---------|
| **Python** | 3.8+ | 3.10+ |
| **操作系统** | Windows 10 | Windows 11 |
| **屏幕分辨率** | 1280×720 | 1920×1080+ |
| **磁盘空间** | 10 MB | 50 MB |

### 📦 可选依赖

| 包名 | 用途 | 是否必须 |
|------|------|---------|
| `pystray` | 系统托盘图标支持 | ❌ 可选 |
| `Pillow` | 托盘图标图像处理 | ❌ 可选 |

> 💡 **提示**：核心功能仅需 Python 标准库即可运行，无需额外安装第三方包。

---

## 🚀 安装指南

### 1. 克隆仓库

```bash
git clone https://github.com/your-username/desktop-pet-system.git
cd desktop-pet-system
```

### 2. （可选）安装可选依赖

如需系统托盘功能，安装额外依赖：

```bash
pip install pystray Pillow
```

### 3. 运行程序

**GUI 图形界面版本：**

```bash
python desktop_pet.py
```

**终端命令行版本：**

```bash
python pet_system.py
```

### 4. （推荐）创建虚拟环境

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate

pip install pystray Pillow  # 可选
```

---

## 📖 使用教程

### 🐾 GUI 版本操作指南

#### 创建宠物

1. 运行 `python desktop_pet.py`
2. 在宠物选择界面选择你喜欢的宠物类型
3. 为宠物取一个名字
4. 点击确认，宠物就会出现在你的桌面上！

#### 日常互动

| 操作 | 方法 |
|------|------|
| 🍖 喂食 | 右键菜单 → **喂食** |
| 🎾 玩耍 | 右键菜单 → **玩耍** |
| 💤 睡觉 | 右键菜单 → **睡觉** |
| 💊 治疗 | 右键菜单 → **治疗** |
| 📊 查看状态 | 右键菜单 → **查看状态** |
| 🚶 移动宠物 | 鼠标左键拖拽 |
| ⚙️ 设置 | 右键菜单 → **设置** |
| ❌ 退出 | 右键菜单 → **退出** |

#### 语音气泡

宠物会在以下情况主动显示语音气泡：
- 📢 饥饿值过低："我好饿啊...能给我吃点东西吗？"
- 😢 快乐值过低："好无聊啊...陪我玩一会儿吧！"
- 😴 能量值过低："好困...让我休息一下..."
- ⚠️ 健康值过低："我不太舒服...能照顾一下我吗？"
- 🎉 状态全满："今天真开心！谢谢你照顾我！"

---

### 💻 终端版本操作指南

#### 主菜单

```
╔══════════════════════════════════════╗
║     🐾 桌面电子宠物系统 v1.0.0      ║
╠══════════════════════════════════════╣
║  1. 🏠 领养新宠物                    ║
║  2. 📂 加载已有宠物                  ║
║  3. 📊 查看宠物状态                  ║
║  4. 🍖 喂食                          ║
║  5. 🎾 玩耍                          ║
║  6. 💤 让宠物睡觉                    ║
║  7. 💊 治疗宠物                      ║
║  8. 📜 查看日志                      ║
║  9. 💾 保存并退出                    ║
╚══════════════════════════════════════╝
```

#### 快捷键

| 按键 | 功能 |
|------|------|
| `1` - `9` | 菜单选项 |
| `f` | 快速喂食 |
| `p` | 快速玩耍 |
| `s` | 快速睡觉 |
| `h` | 快速治疗 |
| `q` | 保存并退出 |

---

## 📊 宠物属性说明

| 属性 | 图标 | 范围 | 说明 |
|------|------|------|------|
| **饥饿值** (Hunger) | 🍖 | 0 ~ 100 | 宠物的饱腹程度。低于 20 时宠物会请求喂食 |
| **快乐值** (Happiness) | 😊 | 0 ~ 100 | 宠物的心情指数。通过玩耍和互动提升 |
| **能量值** (Energy) | ⚡ | 0 ~ 100 | 宠物的精力水平。活动会消耗能量，睡觉可恢复 |
| **健康值** (Health) | ❤️ | 0 ~ 100 | 宠物的健康状况。受其他属性综合影响 |
| **年龄** (Age) | 🎂 | 0 ~ ∞ | 宠物的年龄（天数），随时间自然增长 |

### 属性影响关系

```
饥饿值过低 ──→ 健康值下降 ──→ 宠物可能生病
快乐值过低 ──→ 健康值下降 ──→ 宠物状态变差
能量值过低 ──→ 无法玩耍   ──→ 宠物需要休息
```

> ⚠️ **注意**：当健康值低于 10 时，宠物会进入危险状态，请及时照顾！

---

## ⚔️ 互动效果表

| 互动操作 | 🍖 饥饿 | 😊 快乐 | ⚡ 能量 | ❤️ 健康 | 冷却时间 |
|----------|---------|---------|---------|---------|---------|
| 🍖 **喂食** | +30 | +5 | 0 | +5 | 5 分钟 |
| 🎾 **玩耍** | -10 | +25 | -20 | +5 | 3 分钟 |
| 💤 **睡觉** | -5 | +5 | +50 | +10 | 10 分钟 |
| 💊 **治疗** | 0 | +10 | -5 | +40 | 15 分钟 |
| 🎁 **赠送礼物** | 0 | +40 | 0 | +5 | 8 分钟 |
| 🗣️ **聊天** | 0 | +15 | -5 | 0 | 1 分钟 |

> 💡 **小贴士**：过度喂食会导致快乐值下降 5 点，请合理安排宠物的饮食！

---

## ⏰ 时间衰减机制

宠物的属性会随时间自然衰减，模拟真实的成长过程。

### 衰减公式

每 **60 秒**（游戏内 1 分钟）触发一次属性衰减：

```
饥饿值  = max(0, 饥饿值 - 0.8)
快乐值  = max(0, 快乐值 - 0.5)
能量值  = max(0, 能量值 - 0.3)
健康值  = max(0, 健康值 - 健康衰减率)
```

### 健康值特殊衰减

健康值的衰减受其他属性影响：

```
健康衰减率 = 基础衰减(0.1) + 惩罚值

惩罚值计算：
  若 饥饿值 < 20: 惩罚值 += 0.5
  若 快乐值 < 20: 惩罚值 += 0.3
  若 能量值 < 20: 惩罚值 += 0.2
```

### 时间流速

| 版本 | 时间流速 | 说明 |
|------|---------|------|
| GUI 版本 | 1:1 | 游戏时间与现实时间同步 |
| 终端版本 | 1:1 | 同上 |

---

## ❓ 常见问题 (FAQ)

### 1. 🖱️ 宠物窗口被其他窗口遮挡了怎么办？

宠物窗口默认设置为 `topmost`（始终置顶），如果仍然被遮挡，请尝试：
- 右键任务栏 → 选择"层叠窗口"
- 检查是否有其他置顶窗口（如游戏全屏）

### 2. 💾 存档文件在哪里？

- GUI 版本存档：`pets_gui.json`
- 终端版本存档：`pets.json`

存档文件位于程序运行的同一目录下。

### 3. 🔔 系统托盘功能不工作？

系统托盘功能需要安装可选依赖：

```bash
pip install pystray Pillow
```

安装后重启程序即可启用托盘功能。

### 4. 📉 宠物状态下降太快怎么办？

属性衰减是游戏核心机制。如果觉得太快，可以：
- 更频繁地与宠物互动
- 在设置中调整衰减速率（如支持）
- 参考 [互动效果表](#️-互动效果表) 优化操作频率

### 5. 🐾 可以同时养多只宠物吗？

- **GUI 版本**：支持多实例运行，启动多个 `desktop_pet.py` 实例即可
- **终端版本**：支持多存档管理，但同一时间只能操作一只

### 6. 🔄 如何重置/删除宠物数据？

直接删除对应的存档文件即可：

```bash
# 删除 GUI 版本存档
rm pets_gui.json

# 删除终端版本存档
rm pets.json
```

重新启动程序后即可创建新宠物。

---

## 🏗️ 开发架构

本项目采用简洁的模块化设计：

```
desktop-pet-system/
├── desktop_pet.py      # GUI 版本主程序（tkinter）
├── pet_system.py       # 终端版本主程序
├── pets_gui.json       # GUI 版本存档数据
├── pets.json           # 终端版本存档数据
├── README.md           # 项目说明文档（本文件）
├── ARCHITECTURE.md     # 详细架构设计文档
├── TEST_PLAN.md        # 测试计划文档
└── screenshots/        # 截图目录（可选）
```

### 技术栈

| 组件 | 技术 |
|------|------|
| GUI 框架 | `tkinter`（Python 标准库） |
| 系统托盘 | `pystray`（可选） |
| 图像处理 | `Pillow`（可选） |
| 数据存储 | JSON 文件 |
| 终端渲染 | ASCII Art + ANSI 颜色代码 |

> 📄 详细的架构设计请参阅 [ARCHITECTURE.md](./ARCHITECTURE.md)

---

## 🧪 测试

本项目包含完整的测试计划，覆盖以下方面：

- ✅ 宠物创建与初始化
- ✅ 属性衰减机制
- ✅ 互动操作效果
- ✅ 存档与读档功能
- ✅ GUI 事件响应
- ✅ 边界条件与异常处理

> 📄 详细的测试计划请参阅 [TEST_PLAN.md](./TEST_PLAN.md)

运行测试：

```bash
python -m pytest tests/
```

---

## 📄 许可证

本项目基于 **MIT 许可证** 开源。

```
MIT License

Copyright (c) 2026 Desktop Pet System

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

<p align="center">
  Made with ❤️ by Desktop Pet Team<br>
  🐱 猫 · 🐶 狗 · 🐰 兔 · 🐉 龙 · 🦊 狐
</p>
