# 鼠标悬停浮窗状态显示设计方案

## 1. 需求概述

当用户将鼠标移动到桌面宠物身上时，以浮窗形式显示宠物的名字和状态条（饱食度、心情、精力、健康）。鼠标移开后浮窗自动消失。当鼠标有点击或拖拽动作时，浮窗也应该消失。

---

## 2. 浮窗视觉设计

### 2.1 整体样式

```
    ╭──────────────────────────╮
    │  🐱 小可爱               │  ← 宠物名字（粗体）
    │                          │
    │  🍖 饱食度  ████████░░ 72│  ← 状态条 + 数值
    │  😊 心情    ██████░░░░ 58│
    │  ⚡ 精力    ██████████ 95│
    │  ❤️ 健康    ███████░░░ 68│
    ╰──────────────────────────╯
           ▼ (小三角指向宠物)
```

### 2.2 样式参数

| 属性 | 值 | 说明 |
|------|-----|------|
| 背景色 | `#FFFFFF` (alpha=0.92) | 白色半透明 |
| 边框色 | `#E0E0E0` | 浅灰细边框 |
| 圆角半径 | 12px | 柔和圆角 |
| 阴影 | `2px 4px 8px rgba(0,0,0,0.15)` | 轻微投影 |
| 内边距 | 12px (上下), 16px (左右) | 舒适间距 |
| 字体 | `Microsoft YaHei UI, 10pt` | 主要文字 |
| 标题字体 | `Microsoft YaHei UI, 11pt, bold` | 宠物名字 |
| 状态条宽度 | 100px | 短于主窗口的状态条 |
| 状态条高度 | 10px | 比主窗口状态条稍矮 |
| 动画 | 淡入 200ms, 淡出 150ms | 平滑过渡 |
| 触发延迟 | 300ms | 防止快速划过时闪烁 |

### 2.3 颜色方案

```python
HOVER_POPUP_COLORS = {
    "bg":           "#FFFFFF",
    "border":       "#E0E0E0",
    "shadow":       "#00000026",     # rgba(0,0,0,0.15)
    "title_fg":     "#333333",
    "label_fg":     "#666666",
    "bar_bg":       "#F0F0F0",
    "bar_green":    "#4CAF50",
    "bar_yellow":   "#FF9800",
    "bar_red":      "#F44336",
    "value_fg":     "#555555",
}
```

---

## 3. 技术实现方案

### 3.1 方案选择：Toplevel 窗口

**选定方案：使用 `tk.Toplevel` 窗口** 作为浮窗载体。

| 方案 | 优点 | 缺点 |
|------|------|------|
| **Toplevel 窗口** ✅ | 独立窗口、支持圆角裁剪、可跨窗口区域、不干扰主画布 | 需要管理窗口生命周期 |
| Canvas 叠加层 | 实现简单、无窗口管理开销 | 受主窗口边界限制、圆角实现复杂 |
| Tooltip 库 | 开箱即用 | 样式定制困难、不支持状态条 |

**选择理由：** 宠物窗口较小（220×260），浮窗内容较多，如果用 Canvas 叠加，浮窗会被主窗口裁剪。Toplevel 可以自由定位在宠物旁边，不受主窗口限制。

### 3.2 圆角窗口实现

tkinter 原生不支持窗口圆角。两种方案：

**方案 A：`overrideredirect` + Canvas 绘制（推荐）**

```python
class HoverPopup(tk.Toplevel):
    """鼠标悬停浮窗"""

    def __init__(self, parent, pet_data: PetData):
        super().__init__(parent)
        self.pet = pet_data

        # 无边框 + 置顶
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.92)

        # 透明背景（Windows 用 bg 标记）
        self.configure(bg="#FFFFFF")
        self.wm_attributes("-transparentcolor", "#FFFFFF")  # Windows 专属

        # 使用 Canvas 绘制圆角矩形内容
        self.canvas = tk.Canvas(
            self, highlightthickness=0, bg="#FFFFFF"
        )
        self.canvas.pack()

        self._draw_content()
```

**方案 B：Win32 API 圆角裁剪（更美观但平台限定）**

```python
import ctypes
from ctypes import wintypes

def set_rounded_corners(hwnd, radius=12):
    """通过 Win32 API 设置窗口圆角"""
    dwmapi = ctypes.windll.dwmapi
    # DWM_WINDOW_CORNER_PREFERENCE
    DWMWCP_ROUND = 2
    attr = 33  # DWMWA_WINDOW_CORNER_PREFERENCE
    preference = ctypes.c_uint(DWMWCP_ROUND)
    dwmapi.DwmSetWindowAttribute(
        hwnd, attr, ctypes.byref(preference), ctypes.sizeof(preference)
    )
```

> **推荐方案 A**，因为：
> - 跨平台（未来可移植）
> - 不依赖 Win32 API
> - `wm_attributes("-transparentcolor")` 在 Windows 上即可实现透明背景
> - Canvas 绘制圆角矩形效果足够好

### 3.3 完整 HoverPopup 类实现

```python
class HoverPopup:
    """鼠标悬停状态浮窗"""

    # 常量
    POPUP_W = 200
    POPUP_H = 140
    PADDING = 12
    BAR_W = 90
    BAR_H = 8
    RADIUS = 12
    SHOW_DELAY = 300      # ms，鼠标悬停后延迟显示
    FADE_IN = 200          # ms，淡入时间
    FADE_OUT = 150         # ms，淡出时间

    def __init__(self, parent_root: tk.Tk, pet: PetData):
        self.parent = parent_root
        self.pet = pet
        self.popup = None
        self.show_timer = None     # 延迟显示定时器
        self.fade_timer = None     # 淡入/淡出定时器
        self.is_visible = False
        self.target_alpha = 0.0
        self.current_alpha = 0.0

    def schedule_show(self):
        """鼠标进入宠物区域 → 延迟显示浮窗"""
        # 如果正在拖拽或点击，不显示
        if self._is_interacting():
            return

        # 清除之前的隐藏定时器
        self.cancel_hide()

        # 如果已经在显示，不重复
        if self.is_visible:
            return

        # 设置延迟显示
        self.show_timer = self.parent.after(self.SHOW_DELAY, self._show)

    def schedule_hide(self):
        """鼠标离开宠物区域 → 延迟隐藏浮窗"""
        # 取消未触发的显示
        if self.show_timer:
            self.parent.after_cancel(self.show_timer)
            self.show_timer = None

        # 开始淡出
        if self.is_visible:
            self._fade_out()

    def hide_immediately(self):
        """立即隐藏（点击、拖拽时调用）"""
        self.cancel_show()
        if self.popup:
            self.popup.destroy()
            self.popup = None
        self.is_visible = False
        self.current_alpha = 0.0

    def cancel_show(self):
        """取消待触发的显示"""
        if self.show_timer:
            self.parent.after_cancel(self.show_timer)
            self.show_timer = None

    def cancel_hide(self):
        """取消淡出动画"""
        if self.fade_timer:
            self.parent.after_cancel(self.fade_timer)
            self.fade_timer = None

    # ------------------------------------------------------------------
    # 内部实现
    # ------------------------------------------------------------------

    def _is_interacting(self) -> bool:
        """检查是否正在进行交互（拖拽/点击）"""
        # 通过访问主应用的 is_dragging 状态判断
        # 这里需要传入 app 引用或使用回调
        return getattr(self.parent, '_pet_is_dragging', False)

    def _show(self):
        """创建并显示浮窗"""
        if self.popup:
            self.popup.destroy()

        self.popup = tk.Toplevel(self.parent)
        self.popup.overrideredirect(True)
        self.popup.attributes("-topmost", True)
        self.popup.configure(bg="#FFFFFF")

        # Windows: 设置透明色
        try:
            self.popup.wm_attributes("-transparentcolor", "#FEFEFE")
        except Exception:
            pass  # 非 Windows 平台跳过

        canvas = tk.Canvas(
            self.popup,
            width=self.POPUP_W,
            height=self.POPUP_H,
            bg="#FEFEFE",
            highlightthickness=0
        )
        canvas.pack()

        # 绘制圆角矩形背景
        self._draw_rounded_rect(canvas)

        # 绘制内容
        self._draw_content(canvas)

        # 定位浮窗（在宠物窗口上方）
        self._position_popup()

        # 淡入动画
        self.popup.attributes("-alpha", 0.0)
        self.is_visible = True
        self._fade_in()

    def _draw_rounded_rect(self, canvas: tk.Canvas):
        """绘制圆角矩形背景 + 阴影"""
        w, h = self.POPUP_W, self.POPUP_H
        r = self.RADIUS

        # 阴影（偏移 2px 的半透明矩形 — 简化版）
        canvas.create_rectangle(
            4, 4, w - 2, h - 2,
            fill="#D0D0D0", outline=""
        )

        # 圆角矩形主体
        # tkinter 没有原生圆角矩形，用 create_polygon 模拟
        points = [
            r, 2,
            w - r, 2,
            w - 2, 2,
            w - 2, r,
            w - 2, h - r,
            w - 2, h - 2,
            w - r, h - 2,
            r, h - 2,
            2, h - 2,
            2, h - r,
            2, r,
            2, 2,
        ]
        # 使用 create_oval + create_rectangle 组合实现圆角
        # 左上角圆弧
        canvas.create_oval(2, 2, 2 + r * 2, 2 + r * 2,
                          fill="#FFFFFF", outline="#E0E0E0")
        # 右上角圆弧
        canvas.create_oval(w - 2 - r * 2, 2, w - 2, 2 + r * 2,
                          fill="#FFFFFF", outline="#E0E0E0")
        # 左下角圆弧
        canvas.create_oval(2, h - 2 - r * 2, 2 + r * 2, h - 2,
                          fill="#FFFFFF", outline="#E0E0E0")
        # 右下角圆弧
        canvas.create_oval(w - 2 - r * 2, h - 2 - r * 2, w - 2, h - 2,
                          fill="#FFFFFF", outline="#E0E0E0")
        # 中心填充（覆盖圆弧之间的空白）
        canvas.create_rectangle(2 + r, 2, w - 2 - r, h - 2,
                              fill="#FFFFFF", outline="")
        canvas.create_rectangle(2, 2 + r, w - 2, h - 2 - r,
                              fill="#FFFFFF", outline="")
        # 边框线（上下左右四条直线段）
        canvas.create_line(2 + r, 2, w - 2 - r, 2, fill="#E0E0E0")
        canvas.create_line(2 + r, h - 2, w - 2 - r, h - 2, fill="#E0E0E0")
        canvas.create_line(2, 2 + r, 2, h - 2 - r, fill="#E0E0E0")
        canvas.create_line(w - 2, 2 + r, w - 2, h - 2 - r, fill="#E0E0E0")

    def _draw_content(self, canvas: tk.Canvas):
        """绘制浮窗内容"""
        p = self.PADDING
        pet = self.pet

        # 宠物名字
        canvas.create_text(
            p, p,
            text=f"{pet.get_emoji()} {pet.name}",
            font=("Microsoft YaHei UI", 11, "bold"),
            fill="#333333", anchor="nw"
        )

        # 状态条
        stats = [
            ("🍖 饱食度", pet.hunger),
            ("😊 心情",   pet.mood),
            ("⚡ 精力",   pet.energy),
            ("❤️ 健康",   pet.health),
        ]

        bar_x = p + 60
        start_y = p + 30

        for i, (label, value) in enumerate(stats):
            y = start_y + i * 24

            # 标签
            canvas.create_text(
                p, y + self.BAR_H // 2,
                text=label, font=("Microsoft YaHei UI", 9),
                fill="#666666", anchor="w"
            )

            # 状态条背景
            canvas.create_rectangle(
                bar_x, y,
                bar_x + self.BAR_W, y + self.BAR_H,
                fill="#F0F0F0", outline="#E0E0E0", width=1
            )

            # 状态条填充
            color = get_status_color(value)
            fill_w = int(self.BAR_W * value / MAX_STAT)
            if fill_w > 0:
                canvas.create_rectangle(
                    bar_x + 1, y + 1,
                    bar_x + fill_w - 1, y + self.BAR_H - 1,
                    fill=color, outline=""
                )

            # 数值
            canvas.create_text(
                bar_x + self.BAR_W + 5, y + self.BAR_H // 2,
                text=str(value),
                font=("Microsoft YaHei UI", 8, "bold"),
                fill="#555555", anchor="w"
            )

    def _position_popup(self):
        """将浮窗定位在宠物窗口上方"""
        # 获取主窗口位置
        self.parent.update_idletasks()
        px = self.parent.winfo_x()
        py = self.parent.winfo_y()
        pw = self.parent.winfo_width()

        # 浮窗位置：主窗口正上方，留 8px 间距
        popup_x = px + (pw - self.POPUP_W) // 2
        popup_y = py - self.POPUP_H - 8

        # 确保不超出屏幕顶部
        screen_h = self.parent.winfo_screenheight()
        if popup_y < 10:
            # 改为显示在主窗口下方
            popup_y = py + self.parent.winfo_height() + 8

        self.popup.geometry(f"{self.POPUP_W}x{self.POPUP_H}+{popup_x}+{popup_y}")

    def _fade_in(self):
        """淡入动画"""
        self.current_alpha += 0.1
        if self.current_alpha >= 0.92:
            self.current_alpha = 0.92
            if self.popup:
                self.popup.attributes("-alpha", self.current_alpha)
            return

        if self.popup:
            self.popup.attributes("-alpha", self.current_alpha)
            self.fade_timer = self.parent.after(
                self.FADE_IN // 6, self._fade_in
            )

    def _fade_out(self):
        """淡出动画"""
        self.current_alpha -= 0.1
        if self.current_alpha <= 0:
            self.current_alpha = 0
            if self.popup:
                self.popup.destroy()
                self.popup = None
            self.is_visible = False
            return

        if self.popup:
            self.popup.attributes("-alpha", self.current_alpha)
            self.fade_timer = self.parent.after(
                self.FADE_OUT // 6, self._fade_out
            )
```

---

## 4. 事件绑定与触发逻辑

### 4.1 鼠标事件绑定

```python
# 在 DesktopPetApp.bind_events() 中新增：

def bind_events(self):
    """绑定所有事件"""
    # --- 现有事件 ---
    self.canvas.bind("<Button-1>", self.on_press)
    self.canvas.bind("<B1-Motion>", self.on_drag)
    self.canvas.bind("<ButtonRelease-1>", self.on_release)
    self.canvas.bind("<Button-3>", self.show_context_menu)
    self.canvas.bind("<Double-Button-1>", self.show_stats)

    # --- 【新增】悬停浮窗事件 ---
    self.hover_popup = HoverPopup(self.root, self.pet)

    # 鼠标进入宠物区域
    self.canvas.bind("<Enter>", self._on_mouse_enter)
    # 鼠标离开宠物区域
    self.canvas.bind("<Leave>", self._on_mouse_leave)

def _on_mouse_enter(self, event):
    """鼠标进入宠物窗口"""
    self.hover_popup.schedule_show()

def _on_mouse_leave(self, event):
    """鼠标离开宠物窗口"""
    self.hover_popup.schedule_hide()
```

### 4.2 点击/拖拽时隐藏浮窗

```python
def on_press(self, event):
    """鼠标按下 - 开始拖拽 + 隐藏浮窗"""
    self.is_dragging = True
    self.drag_offset = (event.x, event.y)
    # 【新增】立即隐藏浮窗
    self.hover_popup.hide_immediately()

def on_drag(self, event):
    """鼠标拖拽 - 移动窗口"""
    if self.is_dragging:
        x = self.root.winfo_x() + (event.x - self.drag_offset[0])
        y = self.root.winfo_y() + (event.y - self.drag_offset[1])
        self.root.geometry(f"+{x}+{y}")

def on_release(self, event):
    """鼠标释放"""
    self.is_dragging = False
```

### 4.3 右键菜单时隐藏浮窗

```python
def show_context_menu(self, event):
    """显示右键菜单 + 隐藏浮窗"""
    self.hover_popup.hide_immediately()
    # ... 现有菜单代码 ...
```

### 4.4 交互状态检查

`HoverPopup._is_interacting()` 需要知道主应用的拖拽状态：

```python
def _is_interacting(self) -> bool:
    """检查是否正在进行交互"""
    # 通过 parent 的属性获取
    try:
        app = self.parent._pet_app_ref  # 在主应用中设置
        return app.is_dragging
    except AttributeError:
        return False
```

在 `DesktopPetApp.__init__` 中添加引用：

```python
self.root._pet_app_ref = self  # 供 HoverPopup 访问拖拽状态
```

---

## 5. 数据同步

### 5.1 浮窗数据实时更新

浮窗显示的状态值需要是最新的。两种方案：

**方案 A：每次显示时重新读取（推荐）**

```python
def _show(self):
    """创建浮窗时读取最新数据"""
    # 使用当前 pet 数据的快照
    self._snapshot = {
        "name": self.pet.name,
        "emoji": self.pet.get_emoji(),
        "hunger": self.pet.hunger,
        "mood": self.pet.mood,
        "energy": self.pet.energy,
        "health": self.pet.health,
    }
    # ... 创建浮窗并绘制 ...
```

**方案 B：浮窗存在期间定时刷新（过度设计，不推荐）**

> 推荐方案 A。浮窗显示时间短（几秒），数据变化慢（10秒才衰减一次），没有必要实时刷新。

### 5.2 宠物状态变化时更新引用

```python
# 在 revive_pet() 和 create_new_pet() 中：
self.hover_popup.pet = self.pet  # 更新浮窗的数据引用
```

---

## 6. 边界情况处理

| 情况 | 处理方式 |
|------|---------|
| 宠物死亡 | 浮窗仍然显示，健康值显示为红色 0 |
| 宠物在屏幕顶部 | 浮窗改为显示在宠物窗口下方 |
| 宠物在屏幕边缘 | 水平方向做 clamp 确保不超出屏幕 |
| 快速鼠标划过 | 300ms 延迟过滤，不触发浮窗 |
| 拖拽中鼠标进入 | 检查 `is_dragging`，不显示浮窗 |
| 宠物被隐藏（托盘） | 窗口 `deiconify` 时重置浮窗状态 |
| 浮窗打开时宠物复活/死亡 | 关闭旧浮窗，下次悬停显示新数据 |

---

## 7. 性能考量

| 指标 | 目标值 | 说明 |
|------|-------|------|
| 内存开销 | < 1MB | 仅一个 Toplevel + Canvas |
| CPU 开销 | 近零 | 淡入淡出用 `after()` 定时器，非忙等 |
| 创建耗时 | < 50ms | Canvas 绘制是同步的，一次性完成 |
| 触发频率 | 受限于 300ms 延迟 | 防止频繁创建/销毁 |

---

## 8. 实施步骤

### Step 1: 基础浮窗
1. 实现 `HoverPopup` 类骨架
2. 实现圆角矩形绘制
3. 实现文字和状态条渲染

### Step 2: 事件集成
1. 在 `DesktopPetApp` 中创建 `HoverPopup` 实例
2. 绑定 `<Enter>` / `<Leave>` 事件
3. 在 `on_press` / `show_context_menu` 中调用 `hide_immediately()`

### Step 3: 动画与边界
1. 实现淡入/淡出动画
2. 处理屏幕边界（上方/左右溢出）
3. 测试拖拽期间浮窗行为

### Step 4: 数据同步与兼容
1. 确保宠物复活/死亡后浮窗数据正确
2. 测试 Emoji 模式和精灵图模式下浮窗的兼容性
3. 测试高 DPI 屏幕下的显示效果
