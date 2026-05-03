# 🏗️ 系统架构设计文档

## 桌面电子宠物系统 (Desktop Pet System)

**版本**: 1.0.0  
**最后更新**: 2026-05-04

---

## 📑 目录

- [系统概述](#系统概述)
- [模块结构](#模块结构)
- [类图](#类图)
- [状态机设计](#状态机设计)
- [数据流图](#数据流图)
- [宠物属性系统](#宠物属性系统)
- [互动系统设计](#互动系统设计)
- [时间衰减算法](#时间衰减算法)
- [存档系统](#存档系统)
- [动画系统](#动画系统)
- [事件系统](#事件系统)
- [GUI vs 终端对比](#gui-vs-终端对比)

---

## 系统概述

本系统提供两种独立的电子宠物体验模式：

```
┌─────────────────────────────────────────────────────────┐
│                   桌面电子宠物系统                         │
├──────────────────────┬──────────────────────────────────┤
│                      │                                  │
│   GUI 模式            │   终端模式                        │
│   (desktop_pet.py)    │   (pet_system.py / pet_ascii.py) │
│                      │                                  │
│  ┌──────────────┐    │  ┌──────────────────┐            │
│  │ tkinter 窗口  │    │  │ ANSI 彩色终端     │            │
│  │ ┌──────────┐ │    │  │ ┌──────────────┐ │            │
│  │ │ 🐱 宠物   │ │    │  │ │  /\_/\  ASCII │ │            │
│  │ │ 浮动动画  │ │    │  │ │ ( o.o ) Art   │ │            │
│  │ │ 状态条    │ │    │  │ │  > ^ <        │ │            │
│  │ │ 语音气泡  │ │    │  │ │ 状态条+菜单   │ │            │
│  │ └──────────┘ │    │  │ └──────────────┘ │            │
│  │ [右键菜单]   │    │  │ [键盘快捷键]     │            │
│  └──────────────┘    │  └──────────────────┘            │
│                      │                                  │
├──────────────────────┴──────────────────────────────────┤
│                    共享数据层 (pet_data.py)                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │ Pet 类    │  │ 存档管理  │  │ 宠物类型  │              │
│  │ 状态计算  │  │ JSON I/O  │  │ 配置表   │              │
│  └──────────┘  └──────────┘  └──────────┘              │
└─────────────────────────────────────────────────────────┘
```

### 设计原则

1. **关注点分离**: 数据层 (pet_data.py) 与表现层 (GUI/终端) 解耦
2. **零外部依赖**: 核心功能仅使用 Python 标准库
3. **渐进增强**: 可选依赖 (pystray/Pillow) 提供额外功能，缺失时优雅降级
4. **数据持久化**: JSON 文件存档，支持损坏恢复

---

## 模块结构

```
test-repo/
├── desktop_pet.py      # GUI 版本（独立单文件，~1150行）
├── pet_data.py         # 共享数据层（Pet 类 + 存档管理）
├── pet_desktop.py      # GUI 版本（模块化，依赖 pet_data）
├── pet_ascii.py        # 终端版本（模块化，依赖 pet_data）
├── pet_system.py       # 终端版本（独立单文件，~410行）
├── pets_gui.json       # GUI 版存档文件
├── pets_data.json      # 模块化版本存档文件
├── pets.json           # 终端版存档文件
├── README.md           # 项目文档
├── ARCHITECTURE.md     # 本文件
└── TEST_PLAN.md        # 测试计划
```

### 模块依赖关系

```
desktop_pet.py ──(独立)──→ pets_gui.json
pet_desktop.py ──(import)─→ pet_data.py ──→ pets_data.json
pet_ascii.py   ──(import)─→ pet_data.py ──→ pets_data.json
pet_system.py  ──(独立)──→ pets.json
```

---

## 类图

### 核心类设计

```
┌─────────────────────────────────────────────┐
│              PetData (desktop_pet.py)        │
├─────────────────────────────────────────────┤
│ - name: str                                  │
│ - pet_type: str                              │
│ - hunger: int        (0-100)                 │
│ - mood: int          (0-100)                 │
│ - energy: int        (0-100)                 │
│ - health: int        (0-100)                 │
│ - is_alive: bool                              │
│ - is_sleeping: bool                           │
│ - created_at: str                             │
│ - total_interactions: int                     │
│ - age_days: int                               │
│ - death_time: str                             │
├─────────────────────────────────────────────┤
│ + to_dict() → dict                           │
│ + from_dict(d: dict) → PetData               │
│ + get_emoji() → str                          │
│ + get_type_name() → str                      │
│ + get_alt_emoji() → str                      │
│ + update_health()                            │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│              Pet (pet_data.py)               │
├─────────────────────────────────────────────┤
│ - pet_type: str                              │
│ - name: str                                  │
│ - hunger: float      (0-100)                 │
│ - happiness: float   (0-100)                 │
│ - energy: float      (0-100)                 │
│ - health: float      (0-100)                 │
│ - age: float         (天数)                   │
│ - created_at: str                             │
│ - last_interaction: float (timestamp)         │
│ - is_alive: bool                              │
├─────────────────────────────────────────────┤
│ + feed() → str                               │
│ + play() → str                               │
│ + sleep() → str                              │
│ + pet_action() → str                         │
│ + clean() → str                              │
│ + talk() → str                               │
│ + update_by_time()                           │
│ + get_status() → list[str]                   │
│ + to_dict() → dict                           │
│ + from_dict(data) → Pet                      │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│           DesktopPetApp (desktop_pet.py)     │
├─────────────────────────────────────────────┤
│ - root: tk.Tk                                │
│ - pet: PetData                               │
│ - canvas: tk.Canvas                          │
│ - bubble_id: int                             │
│ - float_phase: float                         │
│ - blink_timer: int                           │
│ - is_sleeping_anim: bool                     │
├─────────────────────────────────────────────┤
│ + run()                                      │
│ - _create_widgets()                          │
│ - _setup_context_menu()                      │
│ - _animation_loop()                          │
│ - _decay_tick()                              │
│ - _auto_save()                               │
│ - _feed/_play/_sleep/_pet/_clean/_chat()     │
│ - _show_bubble(text, duration)               │
│ - _show_stats_window()                       │
│ - _drag_start/_drag_motion()                 │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│           FloatingPet (pet_desktop.py)       │
├─────────────────────────────────────────────┤
│ - root: tk.Tk                                │
│ - pets: dict                                 │
│ - active_pet: Pet                            │
│ - drag_data: dict                            │
│ - float_offset: int                          │
├─────────────────────────────────────────────┤
│ - _setup_ui()                                │
│ - _float_animation()                         │
│ - _status_decay()                            │
│ - _feed/_play/_sleep/_pet/_clean/_talk()     │
│ - _show_status()                             │
│ - _minimize_to_tray()                        │
│ - _show_context_menu()                       │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│           TerminalPet (pet_ascii.py)         │
├─────────────────────────────────────────────┤
│ - pets: dict                                 │
│ - active_pet: Pet                            │
│ - animation_frame: int                       │
│ - running: bool                              │
├─────────────────────────────────────────────┤
│ - _animation_loop()                          │
│ - _decay_loop()                              │
│ - _show_create_screen()                      │
│ - _main_loop()                               │
│ - _render()                                  │
│ - _handle_input()                            │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│           ASCIIPet (pet_ascii.py)            │
├─────────────────────────────────────────────┤
│ (静态工具类)                                   │
├─────────────────────────────────────────────┤
│ + get_art(pet_type, mood) → str              │
│ + get_mood(pet) → str                        │
└─────────────────────────────────────────────┘
```

---

## 状态机设计

### 宠物状态转换

```
                    ┌──────────────┐
                    │   🌟 诞生     │
                    │  (创建宠物)   │
                    └──────┬───────┘
                           │
                           ▼
              ┌───→ ┌──────────────┐
              │     │   😊 快乐     │
              │     │ happiness>70  │
              │     │ health>60     │
              │     └──────┬───────┘
              │            │ happiness↓ 或 health↓
              │            ▼
              │     ┌──────────────┐
              │     │   😐 正常     │    hunger<20
              │     │ 默认状态      │ ──────────→ 🍖 饥饿警告
              │     └──────┬───────┘
              │            │
              │     ┌──────┴────────────────┐
              │     │                       │
              │     ▼ energy<20             ▼ health<30
              │ ┌──────────────┐    ┌──────────────┐
              │ │   😴 困倦     │    │   🤒 生病     │
              │ │ 需要休息      │    │ 需要治疗      │
              │ └──────┬───────┘    └──────┬───────┘
              │        │ sleep()           │ clean()/feed()
              │        └───────┬───────────┘
              │                │
              │                ▼
              │     ┌──────────────┐
              │     │   ✨ 状态良好  │ ←── 所有属性>50
              │     │ 全属性健康    │
              │     └──────────────┘
              │
              │ health>30 && hunger>20 && energy>20
              └──────────────────────────────────┘

                    健康 ≤ 0
              ┌──────────────────┐
              │    💀 死亡        │
              │ is_alive = False  │
              │ 可创建新宠物      │
              └──────────────────┘
```

### 状态判定规则

| 状态 | 触发条件 | 图标 |
|------|---------|------|
| 快乐 | happiness > 70 且 health > 60 | 😊 |
| 正常 | 默认状态 | 😐 |
| 饥饿 | hunger < 20 | 🍖 |
| 饥饿(轻) | hunger < 50 | 🍽️ |
| 伤心 | happiness < 20 | 😢 |
| 伤心(轻) | happiness < 50 | 😐 |
| 困倦 | energy < 20 | 😴 |
| 困倦(轻) | energy < 50 | 😪 |
| 生病 | health < 30 | 🏥 |
| 不适(轻) | health < 60 | 🤧 |
| 死亡 | health ≤ 0 | 💀 |

---

## 数据流图

### 用户交互流程

```
用户操作              状态更新               持久化            UI 刷新
─────────           ─────────            ─────────         ─────────

  右键点击      ┌─→ feed() ─→ hunger+30 ─┐
  "喂食"       │              health+5   │
               │                          │
  右键点击      ├─→ play() ─→ happy+25  ─┤
  "玩耍"       │              energy-20  │    save_pets()    update_bars()
               │              hunger-10  │ ──→ JSON 文件 ──→ 重绘状态条
  右键点击      ├─→ sleep() → energy+40 ─┤    (auto 60s)    显示气泡
  "睡觉"       │              health+10  │                  动画切换
               │                          │
  时间流逝      └─→ decay() → hunger-3/h  ┘
  (自动)                   mood-2/h
                           health 受惩罚
```

### 存档读写流程

```
启动程序                    运行中                      退出
────────                   ────────                   ────────

load_pet_data()           auto_save()                save_pet_data()
    │                         │                          │
    ▼                         ▼                          ▼
读取 JSON 文件            每 60 秒触发               写入 JSON 文件
    │                         │                          │
    ▼                         ▼                          ▼
PetData.from_dict()       pet.to_dict()             pet.to_dict()
    │                         │                          │
    ▼                         ▼                          ▼
恢复所有属性              序列化当前状态              json.dump()
恢复时间差衰减            json.dump()                 保存到磁盘
```

---

## 宠物属性系统

### 属性定义

| 属性 | 英文 | 范围 | 初始值 | 说明 |
|------|------|------|--------|------|
| 饥饿值 | hunger | 0-100 | 50 | 0=最饿, 100=最饱 |
| 心情值 | happiness/mood | 0-100 | 50/80 | 0=最差, 100=最好 |
| 精力值 | energy | 0-100 | 50/80 | 0=最困, 100=最精神 |
| 健康值 | health | 0-100 | 100 | 0=死亡 |
| 年龄 | age | 0-∞ | 0 | 单位: 天 |

> 注: PetData (desktop_pet.py) 初始 mood=80, energy=80; Pet (pet_data.py) 初始 hunger=50, happiness=50, energy=50

### 属性间影响关系

```
饥饿值(hunger) ──很低时──→ 健康值(health) 减少
心情值(mood/happiness) ──很低时──→ 健康值(health) 减少
精力值(energy) ──很低时──→ 无法玩耍(play)
健康值(health) ──归零──→ 宠物死亡(is_alive=False)

良好状态(hunger>50, mood>50, energy>30) ──→ 健康值缓慢恢复
```

### 属性溢出保护

所有属性修改均使用 `clamp()` 函数：
```python
def clamp(value, lo=0, hi=100):
    return max(lo, min(hi, value))
```

---

## 互动系统设计

### 互动效果表

| 操作 | 饥饿 | 心情 | 精力 | 健康 | 条件限制 |
|------|------|------|------|------|---------|
| 🍖 喂食 | +30 | +5 | 0 | +5 | hunger < 90 |
| 🎾 玩耍 | -10 | +25 | -20 | 0/+5 | energy ≥ 20 |
| 💤 睡觉 | -5 | +5 | +40 | +10 | 无 |
| 🖐️ 抚摸 | 0 | +15 | -5 | 0 | 无 |
| 🛁 清洁 | 0 | +10 | 0 | +15 | 无 |
| 💬 聊天 | 0 | +10 | 0 | 0 | 无 |

### 平衡性分析

```
喂食 → 饱腹 + 心情 + 健康    (全能型，但有上限90)
玩耍 → 心情大幅提升           (高收益但消耗精力和饥饿)
睡觉 → 精力 + 健康恢复        (核心恢复手段)
抚摸 → 心情小幅提升           (低成本，频繁可用)
清洁 → 健康 + 心情            (健康恢复辅助)
聊天 → 心情小幅提升           (最低成本互动)

设计意图:
- 玩家需要在 喂食-玩耍-睡觉 之间平衡
- 抚摸和聊天是低成本互动，保持宠物心情
- 清洁是唯一的健康恢复手段(除睡觉外)
- 避免单一操作无限刷属性
```

---

## 时间衰减算法

### 核心衰减公式 (pet_data.py)

```python
def update_by_time(self):
    elapsed = time.time() - self.last_interaction  # 秒
    hours = elapsed / 3600

    self.hunger    = max(0, self.hunger - hours * 5)       # 每小时 -5
    self.energy    = min(100, self.energy + hours * 2)     # 每小时 +2 (自然恢复)
    self.happiness = max(0, self.happiness - hours * 3)    # 每小时 -3
    self.health    = max(0, self.health - hours * 2)       # 每小时 -2
    self.age      += hours / 24                            # 累加天数
```

### GUI 版衰减 (desktop_pet.py)

```python
# 每 10 秒触发一次
DECAY_RATES = {
    "hunger":  3,    # 每次 -3
    "mood":    2,    # 每次 -2
    "energy": -1,    # 每次 +1 (自然恢复)
    "health":  0,    # 基础不衰减，由 update_health() 计算
}

def update_health(self):
    if self.hunger <= 10:   self.health -= 2
    elif self.hunger <= 20: self.health -= 1
    if self.mood <= 10:     self.health -= 1
    # 良好状态恢复
    if self.hunger > 50 and self.mood > 50 and self.energy > 30:
        self.health += 1
```

### 长时间未登录衰减预测

| 未登录时长 | hunger | happiness | energy | health | 存活? |
|-----------|--------|-----------|--------|--------|------|
| 1 小时 | -5 | -3 | +2 | -2 | ✅ |
| 6 小时 | -30 | -18 | +12 | -12 | ✅ 大概率 |
| 24 小时 | -100→0 | -72→0 | +48→100 | -48→52 | ⚠️ 危险 |
| 3 天 | 0 | 0 | 100 | 0→💀 | ❌ 死亡 |
| 7 天 | 0 | 0 | 100 | 0→💀 | ❌ 死亡 |

> 约 **2.5 天** 不登录，宠物将因健康归零而死亡 (初始 health=100, 每小时-2)

---

## 存档系统

### 存档格式

**GUI 版 (pets_gui.json)**:
```json
{
  "name": "小花",
  "pet_type": "cat",
  "hunger": 65,
  "mood": 72,
  "energy": 45,
  "health": 88,
  "is_alive": true,
  "is_sleeping": false,
  "created_at": "2026-05-04 02:30:00",
  "last_saved": "2026-05-04 03:15:00",
  "total_interactions": 12,
  "age_days": 0.02,
  "death_time": ""
}
```

**模块化版 (pets_data.json)**:
```json
{
  "小花": {
    "pet_type": "1",
    "name": "小花",
    "hunger": 65.0,
    "happiness": 72.0,
    "energy": 45.0,
    "health": 88.0,
    "age": 0.02,
    "created_at": "2026-05-04T02:30:00",
    "last_interaction": 1746337800.0,
    "is_alive": true
  }
}
```

### 存档策略

| 触发时机 | GUI 版 | 模块化版 | 终端版 |
|---------|--------|---------|--------|
| 每次互动后 | ✅ | ✅ | ✅ |
| 自动保存 | 每 60 秒 | 每 60 秒 | 每次互动 |
| 窗口关闭 | ✅ | ✅ | ✅ |
| 宠物死亡 | ✅ | ✅ | ✅ |

### 损坏恢复

```python
# pet_data.py 的 load_pets 包含异常处理
try:
    data = json.load(f)
    return {name: Pet.from_dict(p) for name, p in data.items()}
except (json.JSONDecodeError, KeyError):
    return {}  # 返回空字典，不崩溃
```

---

## 动画系统

### GUI 浮动动画

```python
# 正弦波浮动 (desktop_pet.py)
float_phase += 0.05
offset = math.sin(float_phase) * 5  # 上下浮动 5 像素
canvas.move(pet_emoji, 0, offset)
```

### 眨眼动画

```python
# 每 3-8 秒随机眨眼
blink_timer -= 1
if blink_timer <= 0:
    # 切换为闭眼 emoji (如 😻 → 😽)
    show_blink_emoji()
    # 200ms 后恢复
    root.after(200, show_normal_emoji)
    blink_timer = random.randint(60, 160)
```

### 睡眠动画

```python
# 睡眠时显示 ZZZ 漂浮
if is_sleeping:
    z_offset = (z_offset + 1) % 3
    z_text = "z" * (z_offset + 1)
    # 在宠物上方漂浮显示
```

### 终端动画

```python
# pet_ascii.py 的动画循环
def _animation_loop(self):
    while self.animating:
        self.animation_frame = (self.animation_frame + 1) % 4
        time.sleep(0.3)
        # 帧 0-3: 不同的 ASCII 姿态
```

---

## 事件系统

### 状态警告阈值

| 事件 | 触发条件 | 提示文字 |
|------|---------|---------|
| 饥饿警告 | hunger < 20 | "肚子好饿...🥺" |
| 饥饿提醒 | hunger < 50 | "有点饿了~" |
| 心情警告 | mood < 20 | "好无聊...不开心..." |
| 精力警告 | energy < 20 | "好累...需要休息..." |
| 健康警告 | health < 30 | "感觉不舒服...🤒" |
| 宠物死亡 | health ≤ 0 | "我...不行了...😢" |
| 全满状态 | 所有 > 70 | "今天真开心！" |

### 气泡显示机制

```
触发事件 → 从反应文字池随机选取 → 显示气泡(3秒) → 淡出消失

气泡优先级:
1. 死亡气泡 (永久显示)
2. 健康警告 (每 30 秒)
3. 饥饿/心情/精力警告 (每 60 秒)
4. 互动反应 (即时，3 秒)
5. 闲置随机气泡 (每 30-60 秒)
```

---

## GUI vs 终端对比

| 特性 | GUI 版 | 终端版 |
|------|--------|--------|
| **界面** | tkinter 窗口 | 命令行文本 |
| **宠物显示** | Emoji + Canvas | ASCII Art |
| **动画** | 正弦浮动 + 眨眼 | 帧切换动画 |
| **交互方式** | 右键菜单 + 按钮 | 键盘输入 |
| **状态展示** | 彩色进度条 | ANSI 色块条 |
| **系统托盘** | ✅ (可选) | ❌ |
| **拖拽** | ✅ | ❌ |
| **语音气泡** | ✅ | ❌ (用文字代替) |
| **多宠物** | 单宠物切换 | 多宠物管理 |
| **外部依赖** | 可选 pystray | 无 |
| **适用场景** | 日常桌面伴侣 | SSH/远程/无 GUI |

---

*文档结束 - 桌面电子宠物系统 v1.0.0*
