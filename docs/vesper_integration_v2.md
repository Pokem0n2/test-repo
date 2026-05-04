# Vesper 桌面宠物整合架构方案 v2

> **直接使用原始图集 `go_hero_vesper-1.png`（2048×2048），运行时按坐标裁剪，保持帧原始尺寸。**

---

## 1. 数据分析

### 1.1 原始图集

| 属性 | 值 |
|------|-----|
| 文件 | `go_hero_vesper-1.png` |
| 尺寸 | 2048 × 2048 |
| 模式 | RGBA（已带透明通道） |
| 总帧数 | 159 帧 |
| 帧号范围 | vesper_0001 ~ vesper_0298（非连续） |

### 1.2 帧尺寸统计

| 指标 | 值 |
|------|-----|
| 最大帧 | 79 × 60 px |
| 最小帧 | 2 × 2 px（特效碎片，桌面宠物不会用到） |
| 平均帧 | 49.5 × 42.9 px |
| 最常见尺寸 | 47×41 (11帧), 47×39 (7帧), 46×58 (7帧) |

> 桌面宠物实际使用的帧大多在 45~50 × 37~45 范围内。最大帧 79×60 用于攻击特效。

### 1.3 最终状态映射

| 状态 | 帧数 | FPS | Loop | 帧号 |
|------|------|-----|------|------|
| idle | 18 | 10 | ✅ | 1~18 |
| running | 10 | 15 | ✅ | 19,21,22,24,26,28,30,31,33,35 |
| jumping | 17 | 15 | ❌ | 145~162 (缺146) |
| waving | 9 | 15 | ❌ | 91,93,95,97,99,101,103,105,107 |
| sleeping | 9 | 5 | ✅ | 1,3,5,7,9,11,13,15,17 |
| dead | 2 | 2 | ❌ | 164,166 |
| eating | 27 | 10 | ❌ | 258~298 (缺8帧) |

**共 92 帧映射到 7 个状态。**

---

## 2. VesperSpriteSheet 类设计

```python
class VesperSpriteSheet:
    """
    Vesper 精灵图集管理器

    直接加载原始 2048×2048 图集，按 vesper_config.json 中的
    f_quad 坐标运行时裁剪。帧保持原始尺寸，不缩放。
    """

    def __init__(self, config_path: str):
        self.config = {}          # vesper_config.json 全文
        self.atlas = None         # PIL.Image RGBA (2048×2048)
        self._pil_cache = {}      # {state: [PIL.Image, ...]}
        self._photo_cache = {}    # {state: [PhotoImage, ...]}
        self._load(config_path)

    def _load(self, config_path: str):
        """加载配置文件和原始图集"""
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = json.load(f)

        from PIL import Image
        atlas_name = self.config["source_image"]
        atlas_path = os.path.join(os.path.dirname(config_path), atlas_name)
        self.atlas = Image.open(atlas_path).convert("RGBA")

        expected = tuple(self.config["source_size"])
        assert self.atlas.size == expected, \
            f"图集尺寸不匹配: 期望{expected}, 实际{self.atlas.size}"

    def get_pil_frames(self, state: str) -> list:
        """
        获取指定状态的 PIL Image 帧列表。
        首次请求时按坐标裁剪并缓存，后续直接返回缓存。
        """
        if state in self._pil_cache:
            return self._pil_cache[state]

        anim = self.config["animations"][state]
        frames = []
        for f in anim["frames"]:
            x, y, w, h = f["x"], f["y"], f["w"], f["h"]
            crop = self.atlas.crop((x, y, x + w, y + h))
            frames.append(crop)
        self._pil_cache[state] = frames
        return frames

    def get_photo_frames(self, state: str) -> list:
        """
        获取 tkinter PhotoImage 帧列表。
        PhotoImage 必须保持引用防止 GC 回收。
        """
        key = f"{state}_photo"
        if key in self._photo_cache:
            return self._photo_cache[key]

        from PIL import ImageTk
        pil_frames = self.get_pil_frames(state)
        photos = [ImageTk.PhotoImage(img) for img in pil_frames]
        self._photo_cache[key] = photos
        return photos

    def get_frame_size(self, state: str, index: int) -> tuple:
        """获取指定帧的原始尺寸 (w, h)"""
        anim = self.config["animations"][state]
        f = anim["frames"][index]
        return (f["w"], f["h"])

    def get_meta(self, state: str) -> dict:
        """获取动画元数据 {fps, loop, frames}"""
        return self.config["animations"][state]

    def get_states(self) -> list:
        """返回所有可用动画状态名"""
        return list(self.config["animations"].keys())
```

**设计要点：**
- 图集一次性加载到内存（2048×2048×4 = 16MB，可接受）
- 帧按需裁剪：首次请求某状态时裁剪该状态全部帧，后续命中缓存
- PIL Image 和 PhotoImage 分开缓存（PhotoImage 引用必须持久持有）
- `get_frame_size()` 供控制器查询单帧尺寸

---

## 3. VesperAnimationController 类设计

```python
class VesperAnimationController:
    """
    帧动画播放控制器

    支持不同尺寸的帧。每帧按原始尺寸绘制在画布上，
    位置以帧中心点为锚点对齐。
    """

    def __init__(self, canvas: tk.Canvas, sheet: VesperSpriteSheet):
        self.canvas = canvas
        self.sheet = sheet
        self.state = "idle"
        self.frame_idx = 0
        self.playing = False
        self.image_id = None       # canvas item id
        self.after_id = None       # tkinter after() id
        self._photo_ref = None     # 防 GC 引用
        self.x = 0                 # 中心点 x
        self.y = 0                 # 中心点 y
        self.on_complete = None

    def play(self, state: str, x: int = None, y: int = None, on_complete=None):
        """播放指定状态的动画"""
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
        """停止当前动画"""
        self.playing = False
        if self.after_id:
            self.canvas.after_cancel(self.after_id)
            self.after_id = None

    def set_position(self, x: int, y: int):
        """更新绘制位置（浮动动画用）"""
        self.x, self.y = x, y
        if self.image_id:
            self.canvas.coords(self.image_id, x, y)

    def _draw(self, idx: int):
        """在画布上显示指定帧"""
        photos = self.sheet.get_photo_frames(self.state)
        frame = photos[idx % len(photos)]

        if self.image_id:
            self.canvas.itemconfig(self.image_id, image=frame)
        else:
            # anchor="center" 让帧以 (x,y) 为中心绘制
            # 不同尺寸的帧自动居中对齐
            self.image_id = self.canvas.create_image(
                self.x, self.y, image=frame, anchor="center"
            )
        self._photo_ref = frame  # 防 GC

    def _tick(self):
        """调度下一帧"""
        if not self.playing: return
        fps = self.sheet.get_meta(self.state)["fps"]
        self.after_id = self.canvas.after(int(1000 / fps), self._advance)

    def _advance(self):
        """前进到下一帧"""
        if not self.playing: return

        photos = self.sheet.get_photo_frames(self.state)
        self.frame_idx += 1

        if self.frame_idx >= len(photos):
            loop = self.sheet.get_meta(self.state).get("loop", False)
            if loop:
                self.frame_idx = 0  # 循环回到首帧
            else:
                self.frame_idx = len(photos) - 1  # 停在末帧
                self.playing = False
                if self.on_complete:
                    self.on_complete()
                return

        self._draw(self.frame_idx)
        self._tick()
```

**变尺寸帧处理：**
- 使用 `anchor="center"` 让所有帧以同一中心点对齐
- 帧尺寸变化时自动适应，无需额外计算
- 小帧（待机 ~47×39）和大帧（攻击 ~79×60）都以宠物中心位置锚定

---

## 4. VesperStateMachine 类设计

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
NON_LOOP = {"jumping", "waving", "eating", "dead"}


class VesperStateMachine:
    """动画状态机 — 管理状态切换合法性与锁定"""

    def __init__(self, controller: VesperAnimationController):
        self.ctrl = controller
        self.current = "idle"
        self.locked = False  # 非循环动画播放中锁定

    def request(self, state: str, on_complete=None):
        """
        请求切换动画状态。
        非循环动画播放完成后自动回 idle。
        """
        if self.current == "dead" and state != "revive":
            return
        if self.locked:
            return
        if state not in TRANSITIONS.get(self.current, []):
            return

        self.current = state

        def done():
            self.locked = False
            self.current = "idle"
            self.ctrl.play("idle")
            if on_complete:
                on_complete()

        if state in NON_LOOP:
            self.locked = True
            self.ctrl.play(state, on_complete=done)
        else:
            self.ctrl.play(state)

    def force(self, state: str):
        """强制切换（死亡/复活/唤醒）"""
        self.locked = False
        self.current = state
        self.ctrl.play(state)
```

---

## 5. DesktopPetApp 改造方案

### 5.1 窗口尺寸

根据 Vesper 帧尺寸分析：
- 待机帧约 47×39 → 中等显示需要放大
- 攻击帧最大 79×60 → 需要足够空间
- 状态条 + 名字 + 气泡需要额外垂直空间

**建议窗口尺寸：**

```python
WINDOW_W = 200    # 比原来的 220 略窄（Vesper 帧较纤细）
WINDOW_H = 220    # 60px精灵 + 顶部名字 + 底部状态条 + 间距
```

### 5.2 删除项

| 删除 | 说明 |
|------|------|
| `SetupDialog` 类 | 不再需要宠物选择 |
| `PET_TYPES` 字典 | 固定为 Vesper |
| `PetData.get_emoji()` | 不用 emoji 渲染 |
| `PetData.get_alt_emoji()` | 不用眨眼变体 |
| `animate()` 中 `blink_state` | 帧动画自带表情变化 |
| `draw_pet()` 中 emoji 文字绘制 | 替换为精灵图 |

### 5.3 `PetData` 修改

```python
class PetData:
    def __init__(self):
        self.name: str = "Vesper"
        self.pet_type: str = "vesper"
        self.hunger: int = 50
        self.mood: int = 80
        self.energy: int = 80
        self.health: int = 100
        self.is_alive: bool = True
        self.is_sleeping: bool = False
        self.created_at: str = now_str()
        self.last_saved: str = now_str()
        self.total_interactions: int = 0
        self.age_days: int = 0
        self.death_time: str = ""
```

### 5.4 `__init__` 初始化流程

```python
def __init__(self):
    self.root = tk.Tk()
    self.root.title("桌面宠物")
    self.root.overrideredirect(True)
    self.root.attributes("-topmost", True)
    self.root.attributes("-alpha", 0.92)
    self.root.configure(bg=COLORS["bg"])

    screen_w = self.root.winfo_screenwidth()
    screen_h = self.root.winfo_screenheight()
    x = screen_w - WINDOW_W - 30
    y = screen_h - WINDOW_H - 80
    self.root.geometry(f"{WINDOW_W}x{WINDOW_H}+{x}+{y}")

    # 动画状态变量
    self.anim_time = 0.0
    self.bubble_text = ""
    self.bubble_timer = 0
    self.is_dragging = False
    self.drag_offset = (0, 0)
    self.mood_bounce = 0
    self.stats_window = None
    self.tray_icon = None

    # 画布
    self.canvas = tk.Canvas(self.root, width=WINDOW_W, height=WINDOW_H,
                            bg=COLORS["bg"], highlightthickness=0)
    self.canvas.pack(fill="both", expand=True)

    # 加载 Vesper 精灵图
    assets_dir = os.path.join(SCRIPT_DIR, "assets")
    cfg_path = os.path.join(assets_dir, "vesper_config.json")
    self.use_sprite = False
    try:
        self.sheet = VesperSpriteSheet(cfg_path)
        self.controller = VesperAnimationController(self.canvas, self.sheet)
        self.state_machine = VesperStateMachine(self.controller)
        self.use_sprite = True
        print("[Vesper] 精灵图加载成功")
    except Exception as e:
        print(f"[Vesper] 精灵图不可用，回退 Emoji: {e}")

    # 加载宠物数据（跳过选择对话框）
    self.pet = self._init_pet()
    self._bind_events()

    # 启动 idle 动画
    if self.use_sprite:
        self.controller.play("idle", WINDOW_W // 2, 80)

    self.animate()
    self.decay_loop()
    self.autosave_loop()
    self.tray_icon = setup_tray(self)
```

### 5.5 `_init_pet` 改造

```python
def _init_pet(self) -> PetData:
    pet = load_pet_data()
    if pet is not None:
        if not pet.is_alive:
            if messagebox.askyesno("宠物状态",
                                   f"😢 {pet.name} 已不在...\n复活 Vesper？"):
                return self._new_pet()
        return pet
    return self._new_pet()

def _new_pet(self) -> PetData:
    pet = PetData()  # 默认 Vesper
    save_pet_data(pet)
    return pet
```

### 5.6 `draw_pet` 改造

```python
def draw_pet(self):
    self.canvas.delete("all")
    c = self.canvas
    cx = WINDOW_W // 2

    # 背景装饰
    c.create_rectangle(5, 5, WINDOW_W - 5, WINDOW_H - 5,
                       fill="#FFFDE7", outline="#E0E0E0", width=1)

    # 名字标签
    name = f"{self.pet.name} {'💀' if not self.pet.is_alive else ''}"
    c.create_text(cx, 16, text=name,
                  font=("Microsoft YaHei UI", 11, "bold"), fill="#333")

    # 精灵图绘制（中心对齐，浮动驱动位置）
    bob_y = math.sin(self.anim_time * 2.0) * 5
    pet_y = 80 + bob_y + self.mood_bounce

    if self.use_sprite:
        self.controller.set_position(cx, pet_y)
    else:
        # 回退 Emoji 模式
        if not self.pet.is_alive:
            emoji = "💀"
        elif self.pet.is_sleeping:
            emoji = "😴"
        else:
            emoji = "🐱"
        c.create_text(cx, pet_y, text=emoji, font=("Segoe UI Emoji", 48))

    # 语音气泡（在精灵上方）
    if self.bubble_text and self.bubble_timer > 0:
        self.draw_bubble(cx, pet_y - 45)

    # 状态条（精灵下方）
    if self.pet.is_alive:
        self.draw_status_bars(15, 140)

    # 死亡文字
    if not self.pet.is_alive:
        c.create_text(cx, WINDOW_H - 40, text="😢 已永远离开...",
                      font=("Microsoft YaHei UI", 10, "italic"), fill="#888")
        c.create_text(cx, WINDOW_H - 22, text="右键点击复活",
                      font=("Microsoft YaHei UI", 8), fill="#AAA")
```

### 5.7 `do_action` 改造

```python
def do_action(self, action: str):
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
        if self.use_sprite:
            self.state_machine.request("eating")

    elif action == "play":
        if pet.is_sleeping:
            self.show_bubble("还在睡觉呢...💤"); return
        if pet.energy < 15:
            self.show_bubble("太累了...😫"); return
        pet.mood = clamp(pet.mood + random.randint(12, 25))
        pet.energy = clamp(pet.energy - random.randint(10, 20))
        pet.hunger = clamp(pet.hunger - random.randint(5, 10))
        self.show_bubble(random.choice(ACTION_BUBBLES["play"]))
        self.do_bounce(20)
        if self.use_sprite:
            self.state_machine.request("running")

    elif action == "sleep":
        pet.is_sleeping = True
        self.show_bubble(random.choice(ACTION_BUBBLES["sleep"]))
        if self.use_sprite:
            self.state_machine.request("sleeping")

    elif action == "wake":
        if pet.energy < 30:
            self.show_bubble("还想睡...😴"); return
        pet.is_sleeping = False
        self.show_bubble("早安！✨")
        self.do_bounce(12)
        if self.use_sprite:
            self.state_machine.force("idle")

    elif action == "pet":
        if pet.is_sleeping:
            pet.mood = clamp(pet.mood + 5)
            self.show_bubble("呼噜呼噜...💕")
        else:
            pet.mood = clamp(pet.mood + random.randint(8, 18))
            self.show_bubble(random.choice(ACTION_BUBBLES["pet"]))
        self.do_bounce(8)
        if self.use_sprite and not pet.is_sleeping:
            self.state_machine.request("waving")

    elif action == "clean":
        if pet.is_sleeping:
            self.show_bubble("还在睡觉呢...💤"); return
        pet.health = clamp(pet.health + random.randint(5, 10))
        pet.mood = clamp(pet.mood + random.randint(3, 8))
        self.show_bubble(random.choice(ACTION_BUBBLES["clean"]))
        self.do_bounce(5)
        if self.use_sprite:
            self.state_machine.request("jumping")

    elif action == "chat":
        self.show_bubble(random.choice(ACTION_BUBBLES["chat"]), duration=60)
        pet.mood = clamp(pet.mood + random.randint(2, 6))
        self.do_bounce(3)

    save_pet_data(pet)
```

### 5.8 状态衰减中的动画联动

```python
def decay_loop(self):
    pet = self.pet
    if pet.is_alive:
        if not pet.is_sleeping:
            pet.hunger = clamp(pet.hunger - DECAY_RATES["hunger"])
            pet.mood = clamp(pet.mood - DECAY_RATES["mood"])
            pet.energy = clamp(pet.energy - abs(DECAY_RATES["energy"]))
        else:
            pet.energy = clamp(pet.energy + 5)
            pet.hunger = clamp(pet.hunger - 1)
            pet.mood = clamp(pet.mood - 1)
            if pet.energy >= MAX_STAT:
                pet.is_sleeping = False
                self.show_bubble("精力充沛！☀️")
                if self.use_sprite:
                    self.state_machine.force("idle")

        pet.update_health()
        self.check_warnings()

        if not pet.is_alive:
            self.show_bubble(random.choice(ACTION_BUBBLES["death"]), duration=100)
            if self.use_sprite:
                self.state_machine.force("dead")
            save_pet_data(pet)

    self.root.after(DECAY_INTERVAL, self.decay_loop)
```

---

## 6. 事件绑定

### 6.1 拖拽 + 悬停浮窗

```python
def _bind_events(self):
    # 拖拽
    self.canvas.bind("<Button-1>", self._on_press)
    self.canvas.bind("<B1-Motion>", self._on_drag)
    self.canvas.bind("<ButtonRelease-1>", self._on_release)
    # 右键菜单
    self.canvas.bind("<Button-3>", self.show_context_menu)
    # 双击详情
    self.canvas.bind("<Double-Button-1>", self.show_stats)
    # 悬停浮窗（见 hover_popup_design.md）
    self.hover_popup = HoverPopup(self.root, self.pet)
    self.canvas.bind("<Enter>", lambda e: self.hover_popup.schedule_show())
    self.canvas.bind("<Leave>", lambda e: self.hover_popup.schedule_hide())

def _on_press(self, event):
    self.is_dragging = True
    self.drag_offset = (event.x, event.y)
    self.hover_popup.hide_immediately()

def _on_drag(self, event):
    if self.is_dragging:
        x = self.root.winfo_x() + (event.x - self.drag_offset[0])
        y = self.root.winfo_y() + (event.y - self.drag_offset[1])
        self.root.geometry(f"+{x}+{y}")

def _on_release(self, event):
    self.is_dragging = False
```

---

## 7. HoverPopup 整合

浮窗方案与 `hover_popup_design.md` 完全兼容。唯一修改：

```python
# HoverPopup._draw_content() 中
# 原: text=f"{pet.get_emoji()} {pet.name}"
# 改:
canvas.create_text(p, p, text=f"⚔️ {pet.name}",
                   font=("Microsoft YaHei UI", 11, "bold"),
                   fill="#333", anchor="nw")
```

---

## 8. 存档兼容

```python
# init_pet 中自动迁移
if pet.pet_type != "vesper":
    pet.pet_type = "vesper"
save_pet_data(pet)
```

旧存档的状态值（hunger/mood/energy/health）完全保留。

---

## 9. 回退兼容

当 Pillow 未安装或图集文件缺失时，自动回退 Emoji 模式：

```python
try:
    self.sheet = VesperSpriteSheet(cfg_path)
    self.controller = VesperAnimationController(self.canvas, self.sheet)
    self.state_machine = VesperStateMachine(self.controller)
    self.use_sprite = True
except Exception:
    self.use_sprite = False
```

回退模式下 `draw_pet()` 使用 emoji 渲染，`do_action()` 跳过状态机调用。

---

## 10. 文件结构

```
test-repo/
├── desktop_pet.py                   # 主程序（修改）
├── pets_gui.json                    # 存档（不变）
├── assets/
│   ├── go_hero_vesper-1.png        # 【直接复制】原始图集 2048×2048
│   └── vesper_config.json           # 【mini 生成】动画配置
├── docs/
│   ├── animation_architecture.md    # 通用动画架构（已更新）
│   ├── hover_popup_design.md        # 悬停浮窗设计
│   ├── vesper_integration.md        # v1（已被本文件取代）
│   └── vesper_integration_v2.md     # 本文档
└── requirements.txt                 # Pillow>=9.0
```

---

## 11. 新增依赖

```
Pillow>=9.0
```

安装：`pip install Pillow`
用途：`Image.open()`, `.crop()`, `ImageTk.PhotoImage()`

---

## 12. 实施顺序

| 步骤 | 负责 | 内容 |
|------|------|------|
| 1 | mini | 生成 `vesper_config.json`（从 vesper_frames.json 按映射表提取） |
| 2 | mini | 复制 `go_hero_vesper-1.png` 到 `assets/` |
| 3 | mimo | 实现 `VesperSpriteSheet` + `VesperAnimationController` + `VesperStateMachine` |
| 4 | mimo | 改造 `DesktopPetApp`（删除选择对话框、接入状态机、回退兼容） |
| 5 | mimo | 集成 `HoverPopup`（修改标题图标） |
| 6 | 测试 | 各状态动画播放、状态切换、死亡/复活、拖拽、回退模式 |
