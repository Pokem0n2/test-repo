# 精灵图动画系统架构方案

## 1. 当前代码结构分析

### 1.1 核心类

| 类 | 职责 |
|---|------|
| `PetData` | 宠物数据模型（状态值、序列化） |
| `DesktopPetApp` | 主应用（UI、动画、事件、动作） |
| `SetupDialog` | 首次运行选择宠物对话框 |
| `StatsWindow` | 详细统计信息窗口 |

### 1.2 当前渲染方式

当前使用 **纯 Emoji 文本渲染**，通过 `tk.Canvas.create_text()` 绘制宠物形象：

```
# 核心渲染代码 (draw_pet)
c.create_text(cx, pet_y, text=emoji, font=("Segoe UI Emoji", 48), tags="pet_emoji")
```

- 浮动动画：正弦波 `bob_y = sin(anim_time * 2.0) * 6`
- 眨眼动画：随机切换 `blink_state` → 替换 alt_emoji
- 睡觉动画：显示 `😴` + 浮动 ZZZ 文字
- 气泡动画：`bubble_timer` 倒计时 + `draw_bubble()` 绘制
- 弹跳动画：`mood_bounce` 衰减位移

### 1.3 当前局限性

1. Emoji 渲染不一致 — 不同系统/字体下外观差异大
2. 无帧动画 — 无法表达连续动作（奔跑、跳跃等）
3. 状态视觉反馈弱 — 仅靠 emoji 切换，缺乏动画表现力
4. 无动画过渡 — 状态切换生硬

---

## 2. 精灵图动画系统设计

### 2.1 精灵图集规格（修正：直接使用原始图集）

```
sprites.png
├── Row 0: idle     (8帧)  — 待机呼吸动画
├── Row 1: running  (8帧)  — 奔跑循环
├── Row 2: jumping  (8帧)  — 跳跃动作
├── Row 3: waving   (8帧)  — 挥手打招呼
├── Row 4: sleeping (8帧)  — 睡觉呼吸
├── Row 5: dead     (8帧)  — 死亡状态
└── Row 6: eating   (8帧)  — 进食动作

单帧尺寸: 128×128 像素
**不再生成新图集。** 直接使用 krluagif 项目的原始图集 `go_hero_vesper-1.png`（2048×2048 RGBA）。
运行时通过 PIL.Image.crop() 按坐标裁剪各帧，保持原始尺寸不缩放。
```

### 2.2 sprites.json 配置格式

```json
{
  "meta": {
    "image": "sprites.png",
    "size": [512, 896],
    "frame_size": [128, 128]
  },
  "animations": {
    "idle": {
      "row": 0, "frames": 8,
      "fps": 8, "loop": true
    },
    "running": {
      "row": 1, "frames": 8,
      "fps": 12, "loop": true
    },
    "jumping": {
      "row": 2, "frames": 8,
      "fps": 10, "loop": false
    },
    "waving": {
      "row": 3, "frames": 8,
      "fps": 8, "loop": false
    },
    "sleeping": {
      "row": 4, "frames": 8,
      "fps": 4, "loop": true
    },
    "dead": {
      "row": 5, "frames": 8,
      "fps": 2, "loop": false
    },
    "eating": {
      "row": 6, "frames": 8,
      "fps": 10, "loop": false
    }
  }
}
```

### 2.3 核心模块设计

#### `SpriteSheet` 类 — 精灵图集加载器

```python
class SpriteSheet:
    """加载并切割精灵图集"""

    def __init__(self, image_path: str, config_path: str):
        self.image = None          # PIL.Image (RGBA)
        self.config = {}           # JSON 配置
        self.frames = {}           # {state: [PhotoImage, ...]}
        self.load(image_path, config_path)

    def load(self, image_path: str, config_path: str):
        """加载图片和配置"""
        from PIL import Image
        self.image = Image.open(image_path).convert("RGBA")
        with open(config_path, "r") as f:
            self.config = json.load(f)

    def cut_frames(self, state: str) -> list:
        """切割指定状态的所有帧，返回 tkinter PhotoImage 列表"""
        meta = self.config["meta"]
        anim = self.config["animations"][state]
        fw, fh = meta["frame_size"]
        row = anim["row"]

        frames = []
        for col in range(anim["frames"]):
            box = (col * fw, row * fh, (col + 1) * fw, (row + 1) * fh)
            crop = self.image.crop(box)
            # 转换为 tkinter 可用的 PhotoImage
            photo = ImageTk.PhotoImage(crop)
            frames.append(photo)
        return frames

    def get_animation(self, state: str) -> dict:
        """获取完整动画数据: {frames: [...], fps, loop}"""
        if state not in self.frames:
            self.frames[state] = self.cut_frames(state)
        anim = self.config["animations"][state]
        return {
            "frames": self.frames[state],
            "fps": anim["fps"],
            "loop": anim["loop"],
            "frame_count": len(self.frames[state]),
        }
```

**关键设计决策：**
- 使用 **PIL/Pillow** 加载 PNG（透明通道支持）
- 用 `ImageTk.PhotoImage` 转换为 tkinter 可用格式
- **惰性切割**：首次请求某状态时才切割，缓存结果
- PhotoImage 对象必须保持引用（避免 GC 回收）

#### `AnimationController` 类 — 动画播放控制器

```python
class AnimationController:
    """管理精灵图动画播放"""

    def __init__(self, canvas: tk.Canvas, sprite_sheet: SpriteSheet):
        self.canvas = canvas
        self.sheet = sprite_sheet

        self.current_state = "idle"
        self.current_frame_idx = 0
        self.anim_data = None       # 当前动画数据
        self.playing = False
        self.image_id = None        # canvas item id
        self.after_id = None        # tkinter after() id

        # 位置
        self.x = 0
        self.y = 0

    def play(self, state: str, x: int = None, y: int = None, on_complete=None):
        """播放指定状态的动画"""
        # 停止当前动画
        self.stop()

        self.current_state = state
        self.current_frame_idx = 0
        self.anim_data = self.sheet.get_animation(state)
        self.playing = True
        self.on_complete = on_complete  # 非循环动画完成回调

        if x is not None:
            self.x = x
        if y is not None:
            self.y = y

        # 显示第一帧并启动播放
        self._show_frame(0)
        self._schedule_next()

    def stop(self):
        """停止当前动画"""
        self.playing = False
        if self.after_id:
            self.canvas.after_cancel(self.after_id)
            self.after_id = None

    def set_position(self, x: int, y: int):
        """更新动画位置（用于浮动效果）"""
        self.x = x
        self.y = y
        if self.image_id:
            self.canvas.coords(self.image_id, x, y)

    def _show_frame(self, idx: int):
        """在画布上显示指定帧"""
        frames = self.anim_data["frames"]
        frame = frames[idx % len(frames)]

        if self.image_id:
            self.canvas.itemconfig(self.image_id, image=frame)
        else:
            self.image_id = self.canvas.create_image(
                self.x, self.y, image=frame, anchor="center"
            )
        # 保持引用！防止 GC 回收 PhotoImage
        self._current_photo = frame

    def _schedule_next(self):
        """调度下一帧"""
        if not self.playing:
            return

        fps = self.anim_data["fps"]
        interval = int(1000 / fps)

        self.after_id = self.canvas.after(interval, self._advance)

    def _advance(self):
        """前进到下一帧"""
        if not self.playing:
            return

        frames = self.anim_data["frames"]
        self.current_frame_idx += 1

        if self.current_frame_idx >= len(frames):
            if self.anim_data["loop"]:
                self.current_frame_idx = 0  # 循环回到开头
            else:
                # 非循环动画：停留在最后一帧
                self.current_frame_idx = len(frames) - 1
                self.playing = False
                if self.on_complete:
                    self.on_complete()
                return

        self._show_frame(self.current_frame_idx)
        self._schedule_next()
```

**关键设计决策：**
- 每帧间隔由 `fps` 配置控制，不同动画可有不同帧率
- 循环动画（idle/running/sleeping）自动循环
- 非循环动画（jumping/waving/eating/dead）播放一次后停止，触发 `on_complete` 回调
- `PhotoImage` 引用保存在 `self._current_photo`，防止被 GC

---

## 3. 动画状态机设计

### 3.1 状态定义

```
         ┌──────────────────────────────────────────┐
         │                                          │
         ▼                                          │
    ┌─────────┐   用户喂食   ┌─────────┐            │
    │  IDLE   │ ──────────→ │ EATING  │ ───────────┘
    │ (待机)  │              │ (进食)  │  on_complete
    └────┬────┘              └─────────┘
         │
         │ 用户玩耍
         ▼
    ┌─────────┐
    │ RUNNING │ (自动循环)
    │ (奔跑)  │ ──→ 能量耗尽 → IDLE
    └────┬────┘
         │ 用户抚摸/挥手
         ▼
    ┌─────────┐
    │ WAVING  │ ──→ on_complete → IDLE
    │ (挥手)  │
    └─────────┘

    ┌─────────┐              ┌─────────┐
    │ JUMPING │ ←── 用户交互  │ SLEEPING│ ←── 用户点击睡觉
    │ (跳跃)  │              │ (睡觉)  │ ──→ 精力满 → IDLE
    └─────────┘              └─────────┘

    ┌─────────┐
    │  DEAD   │ (终态，需手动复活)
    │ (死亡)  │
    └─────────┘
```

### 3.2 状态切换规则

```python
ANIMATION_TRANSITIONS = {
    # 当前状态 → 可切换到的状态
    "idle":     ["running", "jumping", "waving", "eating", "sleeping", "dead"],
    "running":  ["idle", "jumping", "dead"],
    "jumping":  ["idle"],                   # 跳跃播放完才能切换
    "waving":   ["idle"],                   # 挥手播放完才能切换
    "sleeping": ["idle", "dead"],           # 只能醒来或死亡
    "eating":   ["idle"],                   # 吃完才能切换
    "dead":     [],                         # 终态
}
```

### 3.3 状态映射逻辑

将用户动作映射到动画状态：

| 用户动作 | 动画状态 | 触发条件 |
|---------|---------|---------|
| `feed` | `eating` | 宠物存活且未睡觉 |
| `play` | `running` | 宠物存活、未睡觉、精力>15 |
| `sleep` | `sleeping` | 宠物存活 |
| `wake` | `idle` | 精力≥30 |
| `pet` | `waving` | 宠物存活 |
| `clean` | `jumping` | 宠物存活且未睡觉 |
| 死亡 | `dead` | health ≤ 0 |
| 无操作 | `idle` | 默认 |

### 3.4 AnimationStateMachine 集成

```python
class AnimationStateMachine:
    """动画状态机 — 管理状态切换逻辑"""

    def __init__(self, controller: AnimationController):
        self.controller = controller
        self.current = "idle"
        self.locked = False       # 非循环动画播放中，锁定状态

    def request_state(self, new_state: str, on_complete=None):
        """请求切换到新状态"""
        # 死亡是终态
        if self.current == "dead" and new_state != "revive":
            return

        # 非循环动画播放中，不允许切换
        if self.locked:
            return

        # 检查合法性
        allowed = ANIMATION_TRANSITIONS.get(self.current, [])
        if new_state not in allowed:
            return

        self.current = new_state

        def unlock_and_callback():
            self.locked = False
            self.current = "idle"  # 非循环动画完成后回到 idle
            if on_complete:
                on_complete()

        # 非循环动画需要锁定
        non_looped = ["jumping", "waving", "eating"]
        if new_state in non_looped:
            self.locked = True
            self.controller.play(new_state, on_complete=unlock_and_callback)
        else:
            self.controller.play(new_state)

    def force_state(self, state: str):
        """强制切换状态（用于死亡等特殊情况）"""
        self.locked = False
        self.current = state
        self.controller.play(state)
```

---

## 4. 与现有 tkinter Canvas 集成方案

### 4.1 修改点清单

| 组件 | 现有实现 | 改造方案 |
|------|---------|---------|
| `build_ui()` | 创建 `tk.Canvas` | 增加 `SpriteSheet` + `AnimationController` 初始化 |
| `draw_pet()` | 用 `create_text` 画 emoji | 替换为精灵图渲染，保留状态条绘制 |
| `animate()` | 驱动眨眼+浮动 | 浮动效果改为 `controller.set_position()`，眨眼由精灵图帧替代 |
| `do_action()` | 改数据+气泡 | 增加 `state_machine.request_state()` 调用 |
| 依赖 | 仅标准库 | **需新增 `Pillow` 依赖**（`pip install Pillow`） |

### 4.2 新的 `DesktopPetApp.__init__` 结构

```python
def __init__(self):
    self.root = tk.Tk()
    # ... (现有窗口配置不变) ...

    # 【新增】精灵图系统
    assets_dir = os.path.join(SCRIPT_DIR, "assets")
    self.sprite_sheet = SpriteSheet(
        os.path.join(assets_dir, "sprites.png"),
        os.path.join(assets_dir, "sprites.json"),
    )
    self.anim_controller = AnimationController(self.canvas, self.sprite_sheet)
    self.state_machine = AnimationStateMachine(self.anim_controller)

    # 加载或创建宠物
    self.pet = self.init_pet()
    self.build_ui()
    self.bind_events()

    # 【修改】启动时播放 idle 动画
    self.state_machine.request_state("idle")

    self.animate()
    self.decay_loop()
    self.autosave_loop()
```

### 4.3 新的 `draw_pet()` 流程

```python
def draw_pet(self):
    self.canvas.delete("all")
    c = self.canvas
    cx = WINDOW_W // 2

    # 背景 (保留)
    c.create_rectangle(5, 5, WINDOW_W-5, WINDOW_H-5, ...)

    # 名字标签 (保留)
    c.create_text(cx, 18, text=pet.name, ...)

    # 【修改】精灵图动画 — 位置由浮动动画驱动
    bob_y = math.sin(self.anim_time * 2.0) * 6
    pet_y = 96 + bob_y + self.mood_bounce  # 调整Y偏移适配128px精灵
    self.anim_controller.set_position(cx, pet_y)

    # 气泡 (保留，但位置调整到精灵上方)
    if self.bubble_text and self.bubble_timer > 0:
        self.draw_bubble(cx, pet_y - 80)

    # 状态条 (保留，位置下移适配精灵尺寸)
    if pet.is_alive:
        self.draw_status_bars(15, 190)

    # 死亡覆盖 (保留)
    if not pet.is_alive:
        c.create_text(cx, WINDOW_H-60, text="😢 已永远离开...", ...)
```

### 4.4 新的 `do_action()` 改造

```python
def do_action(self, action: str):
    pet = self.pet
    if not pet.is_alive and action != "revive":
        self.show_bubble("我...已经不在了...😢")
        return

    pet.total_interactions += 1

    if action == "feed":
        # ... 数值修改不变 ...
        self.state_machine.request_state("eating",
            on_complete=lambda: self.state_machine.request_state("idle"))

    elif action == "play":
        # ... 数值修改不变 ...
        self.state_machine.request_state("running")

    elif action == "sleep":
        pet.is_sleeping = True
        self.state_machine.request_state("sleeping")

    elif action == "pet":
        # ... 数值修改不变 ...
        self.state_machine.request_state("waving",
            on_complete=lambda: self.state_machine.request_state("idle"))

    # ... 其他动作 ...
    save_pet_data(pet)
```

### 4.5 回退兼容方案

如果精灵图加载失败，自动回退到 Emoji 渲染模式：

```python
def build_ui(self):
    self.canvas = tk.Canvas(...)
    self.canvas.pack(fill="both", expand=True)

    # 尝试加载精灵图
    self.use_sprite = False
    try:
        assets_dir = os.path.join(SCRIPT_DIR, "assets")
        self.sprite_sheet = SpriteSheet(
            os.path.join(assets_dir, "sprites.png"),
            os.path.join(assets_dir, "sprites.json"),
        )
        self.anim_controller = AnimationController(self.canvas, self.sprite_sheet)
        self.state_machine = AnimationStateMachine(self.anim_controller)
        self.use_sprite = True
        print("[动画] 已加载精灵图")
    except Exception as e:
        print(f"[动画] 精灵图加载失败，使用 Emoji 模式: {e}")
        self.sprite_sheet = None
        self.anim_controller = None
        self.state_machine = None

    self.draw_pet()
```

---

## 5. 实施路线图

### Phase 1: 基础框架（最小可运行版本）
1. 安装 Pillow：`pip install Pillow`
2. 生成精灵图集和配置 JSON
3. 实现 `SpriteSheet` 类
4. 实现 `AnimationController` 类
5. 修改 `build_ui()` 加载精灵图
6. 修改 `draw_pet()` 使用精灵图渲染

### Phase 2: 状态机集成
1. 实现 `AnimationStateMachine` 类
2. 修改 `do_action()` 接入状态机
3. 处理状态衰减触发的动画切换（如精力耗尽 → 自动走路变 idle）

### Phase 3: 完善与优化
1. 添加动画过渡效果（淡入淡出）
2. 窗口尺寸自适应（根据精灵图尺寸调整 WINDOW_W/H）
3. 精灵图预加载优化（启动时一次性切割所有帧）
4. 单元测试

---

## 6. 技术约束

| 约束 | 说明 |
|------|------|
| 新增依赖 | `Pillow` (PIL Fork)，用于 PNG 透明通道处理和裁剪 |
| 窗口尺寸 | 需从 220×260 调整为至少 220×300（128px精灵+状态条） |
| 内存 | 7状态×8帧×128×128×4字节 ≈ 3.5MB（可接受） |
| Python 版本 | 3.8+（现有要求不变） |
| 平台 | Windows（主要），需测试 DPI 缩放对精灵图的影响 |
