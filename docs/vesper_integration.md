# Vesper 桌面宠物整合架构方案（修正版）

> **核心变更：** 不再生成新的精灵图集。直接使用原始 `go_hero_vesper-1.png`（2048×2048），在运行时按坐标裁剪帧。

---

## 1. 原始数据结构理解

### 1.1 krluagif 项目动画系统

原项目使用 Love2D 引擎，动画系统核心：

- **图集** `go_hero_vesper-1.png`：2048×2048 RGBA 大图，包含所有帧
- **Lua 配置** `go_hero_vesper.lua`：每帧定义为 `{x, y, w, h}` 裁剪坐标
- **main.lua 动画定义**：帧范围 + FPS

关键特性：
- **帧尺寸不统一**：各帧 w=45~58, h=27~60（保持原始比例）
- **帧号不连续**：159 帧分布在 1~298 号范围内，缺失帧通过 alias 跳过
- **运行时裁剪**：`love.graphics.newQuad(x, y, w, h, 2048, 2048)` 按需裁剪

### 1.2 已提取数据

`vesper_frames.json` 包含 159 帧，每帧结构：
```json
{"name": "vesper_0001", "x": 83, "y": 872, "w": 47, "h": 39}
```

---

## 2. 配置文件方案

### 2.1 vesper_config.json 结构

```json
{
  "meta": {
    "atlas": "go_hero_vesper-1.png",
    "atlas_size": [2048, 2048],
    "description": "Vesper hero animation from krluagif project"
  },
  "animations": {
    "idle": {
      "fps": 10, "loop": true,
      "frames": [
        {"name": "vesper_0001", "x": 83, "y": 872, "w": 47, "h": 39},
        {"name": "vesper_0002", "x": 83, "y": 917, "w": 47, "h": 39},
        ...
      ]
    },
    "running": { ... },
    "jumping": { ... },
    "waving": { ... },
    "sleeping": { ... },
    "dead": { ... },
    "eating": { ... }
  }
}
```

### 2.2 实际帧映射

| 状态 | 帧源 | 实际帧数 | 帧号范围 | FPS | Loop | 帧尺寸范围 |
|------|------|---------|---------|-----|------|-----------|
| idle | idle | 18 | 1~18 | 10 | ✅ | 47×39~41 |
| running | walk | 10 | 19,21~35 | 15 | ✅ | 46~50 × 36~44 |
| jumping | ricochet前半 | 17 | 145~162 (缺146) | 15 | ❌ | 45~58 × 44~51 |
| waving | ranged_attack | 9 | 91,93~107 | 15 | ❌ | 45~48 × 37~46 |
| sleeping | idle静止帧 | 9 | 1,3,5,7,9,11,13,15,17 | 5 | ✅ | 47×39~41 |
| dead | ricochet倒地 | 2 | 164,166 | 2 | ❌ | 45~47 × 37~40 |
| eating | 特殊动作 | 27 | 258~298 (缺8帧) | 10 | ❌ | 45~54 × 27~60 |

**总计：92 帧映射到 7 个状态**

### 2.3 dead 状态补充说明

dead 仅 2 帧，需要特殊处理：
- 方案 A：2 帧循环播放（缓慢呼吸/颤抖效果）
- 方案 B：播放完 2 帧后停在最后一帧（倒地不动）
- **推荐方案 B**：死亡后定格在最后一帧

### 2.4 sleeping 复用 idle 帧

sleeping 复用 idle 的奇数帧（1,3,5,7,...），视觉上是 idle 的慢速版本，适合睡觉的缓慢呼吸感。

---

## 3. 代码架构

### 3.1 新增类：`VesperSpriteSheet`

```python
class VesperSpriteSheet:
    """Vesper 精灵图集管理器 — 运行时裁剪模式"""

    def __init__(self, config_path: str):
        self.config = {}
        self.atlas = None          # PIL.Image RGBA (2048×2048)
        self.pil_cache = {}        # {state: [PIL.Image, ...]}
        self.photo_cache = {}      # {state: [PhotoImage, ...]}
        self._load(config_path)

    def _load(self, config_path: str):
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = json.load(f)

        meta = self.config["meta"]
        atlas_path = os.path.join(os.path.dirname(config_path), meta["atlas"])
        from PIL import Image
        self.atlas = Image.open(atlas_path).convert("RGBA")
        assert self.atlas.size == tuple(meta["atlas_size"])
        print(f"[VesperSpriteSheet] 图集加载: {atlas_path} ({self.atlas.size})")

    def get_pil_frames(self, state: str) -> list:
        """获取指定状态的 PIL Image 帧列表（惰性裁剪+缓存）"""
        if state in self.pil_cache:
            return self.pil_cache[state]

        anim = self.config["animations"][state]
        frames = []
        for f in anim["frames"]:
            crop = self.atlas.crop((f["x"], f["y"], f["x"] + f["w"], f["y"] + f["h"]))
            frames.append(crop)
        self.pil_cache[state] = frames
        return frames

    def get_photo_frames(self, state: str) -> list:
        """获取 tkinter PhotoImage 帧列表"""
        key = f"{state}_photo"
        if key in self.photo_cache:
            return self.photo_cache[key]

        from PIL import ImageTk
        pil_frames = self.get_pil_frames(state)
        photos = [ImageTk.PhotoImage(f) for f in pil_frames]
        self.photo_cache[key] = photos
        return photos

    def get_meta(self, state: str) -> dict:
        return self.config["animations"][state]

    def get_states(self) -> list:
        return list(self.config["animations"].keys())
```

**设计要点：**
- 图集只加载一次（2048×2048 RGBA ≈ 16MB 内存，可接受）
- 帧按需裁剪，首次请求某状态时裁剪全部帧并缓存
- PIL Image 和 PhotoImage 分开缓存（PhotoImage 需保持引用防 GC）

### 3.2 `VesperAnimationController`

```python
class VesperAnimationController:
    """帧动画播放控制器"""

    def __init__(self, canvas: tk.Canvas, sheet: VesperSpriteSheet):
        self.canvas = canvas
        self.sheet = sheet
        self.state = "idle"
        self.frame_idx = 0
        self.playing = False
        self.image_id = None
        self.after_id = None
        self._photo_ref = None   # 防 GC
        self.x = 0
        self.y = 0
        self.on_complete = None

    def play(self, state, x=None, y=None, on_complete=None):
        self.stop()
        self.state = state
        self.frame_idx = 0
        self.playing = True
        self.on_complete = on_complete
        if x is not None: self.x = x
        if y is not None: self.y = y
        self._draw(0)
        self._tick()

    def stop(self):
        self.playing = False
        if self.after_id:
            self.canvas.after_cancel(self.after_id)
            self.after_id = None

    def set_position(self, x, y):
        self.x, self.y = x, y
        if self.image_id:
            self.canvas.coords(self.image_id, x, y)

    def _draw(self, idx):
        photos = self.sheet.get_photo_frames(self.state)
        frame = photos[idx % len(photos)]
        if self.image_id:
            self.canvas.itemconfig(self.image_id, image=frame)
        else:
            self.image_id = self.canvas.create_image(
                self.x, self.y, image=frame, anchor="center"
            )
        self._photo_ref = frame

    def _tick(self):
        if not self.playing: return
        fps = self.sheet.get_meta(self.state)["fps"]
        self.after_id = self.canvas.after(int(1000 / fps), self._advance)

    def _advance(self):
        if not self.playing: return
        photos = self.sheet.get_photo_frames(self.state)
        self.frame_idx += 1
        if self.frame_idx >= len(photos):
            loop = self.sheet.get_meta(self.state).get("loop", False)
            if loop:
                self.frame_idx = 0
            else:
                self.frame_idx = len(photos) - 1
                self.playing = False
                if self.on_complete: self.on_complete()
                return
        self._draw(self.frame_idx)
        self._tick()
```

### 3.3 `VesperStateMachine`

```python
TRANSITIONS = {
    "idle":     ["running", "jumping", "waving", "eating", "sleeping", "dead"],
    "running":  ["idle", "jumping", "dead"],
    "jumping":  ["idle"],
    "waving":   ["idle"],
    "sleeping": ["idle", "dead"],
    "eating":   ["idle"],
    "dead":     [],
}
NON_LOOP = ["jumping", "waving", "eating", "dead"]

class VesperStateMachine:
    def __init__(self, controller):
        self.ctrl = controller
        self.current = "idle"
        self.locked = False

    def request(self, state, on_complete=None):
        if self.current == "dead" and state != "revive": return
        if self.locked: return
        if state not in TRANSITIONS.get(self.current, []): return
        self.current = state

        def done():
            self.locked = False
            self.current = "idle"
            self.ctrl.play("idle")
            if on_complete: on_complete()

        if state in NON_LOOP:
            self.locked = True
            self.ctrl.play(state, on_complete=done)
        else:
            self.ctrl.play(state)

    def force(self, state):
        self.locked = False
        self.current = state
        self.ctrl.play(state)
```

---

## 4. `DesktopPetApp` 改造

### 4.1 删除项

| 删除 | 原因 |
|------|------|
| `SetupDialog` 类 | 固定为 Vesper |
| `PET_TYPES` 字典 | 不再有多种宠物 |
| `PetData.get_emoji()` / `get_alt_emoji()` | 不用 emoji 渲染 |
| `animate()` 中的 blink_state | 帧动画自带表情变化 |

### 4.2 `PetData` 默认值修改

```python
class PetData:
    def __init__(self):
        self.name: str = "Vesper"
        self.pet_type: str = "vesper"
        # ... 其余不变 ...
```

### 4.3 `__init__` 改造

```python
def __init__(self):
    self.root = tk.Tk()
    # ... 窗口配置 ...

    self.canvas = tk.Canvas(self.root, width=WINDOW_W, height=WINDOW_H,
                            bg=COLORS["bg"], highlightthickness=0)
    self.canvas.pack(fill="both", expand=True)

    # 加载 Vesper 精灵图
    assets = os.path.join(SCRIPT_DIR, "assets")
    cfg = os.path.join(assets, "vesper_config.json")
    self.use_sprite = False
    try:
        self.sheet = VesperSpriteSheet(cfg)
        self.controller = VesperAnimationController(self.canvas, self.sheet)
        self.state_machine = VesperStateMachine(self.controller)
        self.use_sprite = True
    except Exception as e:
        print(f"[Vesper] 精灵图不可用，回退 Emoji: {e}")

    self.pet = self.init_pet()  # 跳过选择对话框
    self.build_ui()
    self.bind_events()

    if self.use_sprite:
        self.controller.play("idle", WINDOW_W // 2, 96)

    self.animate()
    self.decay_loop()
    self.autosave_loop()
    self.tray_icon = setup_tray(self)
```

### 4.4 `init_pet` 改造

```python
def init_pet(self):
    pet = load_pet_data()
    if pet is not None:
        if not pet.is_alive:
            if messagebox.askyesno("宠物状态", f"😢 {pet.name} 已不在...\n复活 Vesper？"):
                return self._new_pet()
        return pet
    return self._new_pet()

def _new_pet(self):
    pet = PetData()  # 默认 name="Vesper", pet_type="vesper"
    save_pet_data(pet)
    return pet
```

### 4.5 `draw_pet` 改造

```python
def draw_pet(self):
    self.canvas.delete("all")
    c = self.canvas
    cx = WINDOW_W // 2

    # 背景
    c.create_rectangle(5, 5, WINDOW_W-5, WINDOW_H-5, fill="#FFFDE7", outline="#E0E0E0")

    # 名字
    c.create_text(cx, 18, text=f"{self.pet.name} {'💀' if not self.pet.is_alive else ''}",
                  font=("Microsoft YaHei UI", 11, "bold"), fill="#333")

    # 精灵图（浮动动画驱动位置）
    bob_y = math.sin(self.anim_time * 2.0) * 6
    pet_y = 96 + bob_y + self.mood_bounce
    if self.use_sprite:
        self.controller.set_position(cx, pet_y)
    else:
        emoji = "💀" if not self.pet.is_alive else ("😴" if self.pet.is_sleeping else "🐱")
        c.create_text(cx, pet_y, text=emoji, font=("Segoe UI Emoji", 48))

    # 气泡、状态条、死亡覆盖（位置微调）
    if self.bubble_text and self.bubble_timer > 0:
        self.draw_bubble(cx, pet_y - 50)
    if self.pet.is_alive:
        self.draw_status_bars(15, 160)
    if not self.pet.is_alive:
        c.create_text(cx, WINDOW_H-50, text="😢 已永远离开...", fill="#888", font=("Microsoft YaHei UI", 11, "italic"))
```

### 4.6 `do_action` 改造

```python
def do_action(self, action):
    pet = self.pet
    if not pet.is_alive and action != "revive":
        self.show_bubble("我...已经不在了...😢")
        return
    pet.total_interactions += 1

    if action == "feed":
        if pet.is_sleeping:
            self.show_bubble("还在睡觉呢...💤"); return
        pet.hunger = clamp(pet.hunger + random.randint(15, 25))
        pet.mood = clamp(pet.mood + random.randint(3, 8))
        self.show_bubble(random.choice(ACTION_BUBBLES["feed"]))
        self.do_bounce(10)
        if self.use_sprite: self.state_machine.request("eating")

    elif action == "play":
        if pet.is_sleeping: self.show_bubble("还在睡觉呢...💤"); return
        if pet.energy < 15: self.show_bubble("太累了...😫"); return
        pet.mood = clamp(pet.mood + random.randint(12, 25))
        pet.energy = clamp(pet.energy - random.randint(10, 20))
        pet.hunger = clamp(pet.hunger - random.randint(5, 10))
        self.show_bubble(random.choice(ACTION_BUBBLES["play"]))
        self.do_bounce(20)
        if self.use_sprite: self.state_machine.request("running")

    elif action == "sleep":
        pet.is_sleeping = True
        self.show_bubble(random.choice(ACTION_BUBBLES["sleep"]))
        if self.use_sprite: self.state_machine.request("sleeping")

    elif action == "wake":
        if pet.energy < 30: self.show_bubble("还想睡...😴"); return
        pet.is_sleeping = False
        self.show_bubble("早安！✨")
        self.do_bounce(12)
        if self.use_sprite: self.state_machine.force("idle")

    elif action == "pet":
        pet.mood = clamp(pet.mood + (5 if pet.is_sleeping else random.randint(8, 18)))
        self.show_bubble(random.choice(ACTION_BUBBLES["pet"]))
        self.do_bounce(8)
        if self.use_sprite and not pet.is_sleeping: self.state_machine.request("waving")

    elif action == "clean":
        if pet.is_sleeping: self.show_bubble("还在睡觉呢...💤"); return
        pet.health = clamp(pet.health + random.randint(5, 10))
        pet.mood = clamp(pet.mood + random.randint(3, 8))
        self.show_bubble(random.choice(ACTION_BUBBLES["clean"]))
        self.do_bounce(5)
        if self.use_sprite: self.state_machine.request("jumping")

    elif action == "chat":
        self.show_bubble(random.choice(ACTION_BUBBLES["chat"]), duration=60)
        pet.mood = clamp(pet.mood + random.randint(2, 6))
        self.do_bounce(3)

    save_pet_data(pet)
```

---

## 5. 文件结构

```
test-repo/
├── desktop_pet.py                          # 主程序（修改）
├── pets_gui.json                           # 存档（不变）
├── assets/
│   ├── go_hero_vesper-1.png               # 【直接使用】原始图集 2048×2048
│   └── vesper_config.json                  # 【新增】动画配置（帧坐标+元数据）
├── docs/
│   ├── animation_architecture.md
│   ├── hover_popup_design.md
│   └── vesper_integration.md              # 本文档
└── requirements.txt                        # Pillow>=9.0
```

> **不生成 vesper_sprites.png。** 直接使用原始图集。

---

## 6. HoverPopup 整合

浮窗方案与 `hover_popup_design.md` 兼容，仅修改标题行：

```python
# 原: text=f"{pet.get_emoji()} {pet.name}"
# 改: text=f"⚔️ {pet.name}"    # Vesper 固定图标
```

其余状态条、淡入淡出、事件绑定逻辑完全不变。

---

## 7. 存档兼容

旧存档自动迁移：
```python
def migrate_pet_data(pet):
    if pet.pet_type != "vesper":
        pet.pet_type = "vesper"
    if pet.name == "宠物":
        pet.name = "Vesper"
    return pet
```

---

## 8. 内存与性能

| 指标 | 值 |
|------|-----|
| 图集内存 | 2048×2048×4 = 16MB（一次性加载） |
| 单状态帧缓存 | 9~18帧 × ~50×40×4 ≈ 7~14KB（可忽略） |
| PhotoImage 缓存 | 92帧总计 ≈ 2MB |
| 裁剪耗时 | 首次请求某状态 ~1ms（PIL crop 极快） |
| 帧率 | 5~15 FPS（各状态不同） |

---

## 9. 实施顺序

1. **mini 生成 `vesper_config.json`** — 读取 `vesper_frames.json`，按映射表分组，输出配置
2. **复制 `go_hero_vesper-1.png` 到 `assets/`** — 直接复制原始图集
3. **修改 `desktop_pet.py`** — 实现三个新类 + 改造主应用
4. **测试** — 各状态动画、状态切换、回退兼容
