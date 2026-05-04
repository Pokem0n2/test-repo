#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
桌面宠物 (Desktop Pet) - Vesper 版
==================================
使用 Python + tkinter + PIL 制作的桌面浮窗宠物应用。
宠物形象使用 krluagif 项目的 Vesper 英雄精灵图动画。

用法: python desktop_pet.py
依赖: Python 3.8+, Pillow
"""

import tkinter as tk
from tkinter import messagebox
import json
import os
import time
import random
import math
import datetime
import threading
import sys

# PIL 用于精灵图处理
try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    print("[警告] Pillow 未安装，将使用 emoji 回退模式")
    print("  安装: pip install Pillow")

# ============================================================================
# 常量与配置
# ============================================================================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(SCRIPT_DIR, "pets_gui.json")
ASSETS_DIR = os.path.join(SCRIPT_DIR, "assets")
CONFIG_FILE = os.path.join(ASSETS_DIR, "vesper_config.json")
SPRITE_FILE = os.path.join(ASSETS_DIR, "go_hero_vesper-1.png")

# 窗口尺寸 - 根据 Vesper 帧尺寸优化
WINDOW_W = 200
WINDOW_H = 220

# 动画间隔 (毫秒)
ANIM_INTERVAL = 50          # 主动画循环 20fps
DECAY_INTERVAL = 900000     # 状态衰减间隔 (15分钟 = 15*60*1000)
AUTOSAVE_INTERVAL = 60000   # 自动保存间隔 (60秒)

# 状态最大值
MAX_STAT = 100

# 动作反应气泡文字
ACTION_BUBBLES = {
    "feed":  ["好好吃~🤤", "美味！", "谢谢主人！", "还想吃...", "饱了饱了~"],
    "play":  ["好开心！🎉", "再来一次！", "哈哈哈~", "累死了...", "真好玩！"],
    "sleep": ["zzZ...💤", "好困...", "做了个好梦~", "晚安...", "精力充沛！"],
    "pet":   ["呼噜呼噜~💕", "好舒服！", "❤️", "再摸摸~", "嘻嘻~"],
    "clean": ["香喷喷！🛁", "好干净！", "闪闪发光~", "不喜欢水...", "焕然一新！"],
    "chat":  ["你好呀！", "今天开心吗？", "陪我玩吧！", "我爱你~💕", "汪汪！喵~"],
    "death": ["我...不行了...😢", "要记得我...", "再见了..."],
    "warn_hunger": ["肚子好饿...🥺", "好想吃东西...", "快饿扁了..."],
    "warn_mood":   ["好无聊...", "不开心...", "陪陪我吧...😢"],
    "warn_energy": ["好累...", "需要休息...", "眼睛快睁不开了..."],
    "warn_health": ["感觉不舒服...", "我生病了吗...", "需要照顾...🤒"],
    "idle":  ["~", "？", "！", "嘿嘿", "嗯...", "看看我！", "无聊~"],
}

# 状态衰减速率 (每15分钟衰减的量)
DECAY_RATES = {
    "hunger":  2,    # 饥饿值下降 (饥饿感增加)
    "mood":    3,    # 心情下降
    "energy":  -1.5, # 睡觉时恢复精力，清醒时缓慢消耗 (负数=恢复)
    "health":  0,    # 健康不会自动变化，由其他状态影响
}

# 颜色配置
COLORS = {
    "green":  "#4CAF50",
    "yellow": "#FF9800",
    "red":    "#F44336",
    "bg":     "#FFFEF0",
    "bubble": "#FFFFFF",
    "bubble_border": "#CCCCCC",
    "sleep_z": "#6B7DB3",
    "bar_bg": "#E0E0E0",
    "popup_bg": "#FFF8E7",
    "popup_border": "#E0D0B0",
}

# ============================================================================
# 工具函数
# ============================================================================

def get_status_color(value: int) -> str:
    if value >= 60:
        return COLORS["green"]
    elif value >= 30:
        return COLORS["yellow"]
    else:
        return COLORS["red"]


def clamp(value: int, lo: int = 0, hi: int = MAX_STAT) -> int:
    return max(lo, min(hi, value))


def now_str() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ============================================================================
# Vesper 精灵图系统
# ============================================================================

class VesperSpriteSheet:
    """Vesper 精灵图集 - 运行时从原始大图裁剪帧"""

    def __init__(self, config_path: str, image_path: str):
        self.config_path = config_path
        self.image_path = image_path
        self.config = None
        self.source_image = None
        self.frame_data = []
        self.loaded = False
        self.error_msg = ""

        self._load()

    def _load(self):
        """加载配置和源图"""
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                self.config = json.load(f)
        except Exception as e:
            self.error_msg = f"配置加载失败: {e}"
            return

        self.frame_data = self.config.get("frameData", [])
        if not self.frame_data:
            self.error_msg = "配置中无 frameData"
            return

        if not HAS_PIL:
            self.error_msg = "Pillow 未安装"
            return

        try:
            self.source_image = Image.open(self.image_path).convert("RGBA")
        except Exception as e:
            self.error_msg = f"图片加载失败: {e}"
            return

        self.loaded = True
        print(f"[VesperSpriteSheet] 加载成功: {len(self.frame_data)} 帧, 图片 {self.source_image.size}")

    def get_frame(self, index: int, scale: float = 2.0, flip: bool = False) -> ImageTk.PhotoImage | None:
        """获取指定索引的帧，裁剪、缩放、可选水平翻转"""
        if not self.loaded or index < 0 or index >= len(self.frame_data):
            return None

        frame = self.frame_data[index]
        crop = frame["crop"]
        x, y, w, h = crop["x"], crop["y"], crop["w"], crop["h"]

        # 裁剪原始帧
        cropped = self.source_image.crop((x, y, x + w, y + h))

        # 水平翻转
        if flip:
            cropped = cropped.transpose(Image.FLIP_LEFT_RIGHT)

        # 缩放（保持比例，使用 NEAREST 保持像素风锐利）
        if scale != 1.0:
            new_w = max(1, int(w * scale))
            new_h = max(1, int(h * scale))
            cropped = cropped.resize((new_w, new_h), Image.NEAREST)

        return ImageTk.PhotoImage(cropped)

    def get_frame_size(self, index: int, scale: float = 2.0) -> tuple[int, int]:
        """获取指定帧的显示尺寸"""
        if not self.loaded or index < 0 or index >= len(self.frame_data):
            return (64, 64)
        crop = self.frame_data[index]["crop"]
        return (max(1, int(crop["w"] * scale)), max(1, int(crop["h"] * scale)))


class VesperAnimationController:
    """Vesper 动画控制器 - 管理帧序列和播放状态"""

    def __init__(self, sprite_sheet: VesperSpriteSheet, config: dict):
        self.sprite_sheet = sprite_sheet
        self.config = config
        self.animations = config.get("animations", {})

        # 当前状态
        self.current_state = "idle"
        self.current_frame_idx = 0  # 在 sourceFrames 中的索引
        self.frame_timer = 0.0
        self.frame_cache = {}  # index -> PhotoImage 缓存
        self.scale = 2.0

        # 状态映射: 动作 -> 动画名
        self.action_map = {
            "feed": "eating",
            "play": "running",
            "sleep": "sleeping",
            "wake": "idle",
            "pet": "waving",
            "clean": "jumping",
            "chat": "idle",
            "death": "dead",
        }

    def get_animation(self, state: str) -> dict | None:
        return self.animations.get(state)

    def get_current_photo(self, flip: bool = False) -> ImageTk.PhotoImage | None:
        """获取当前帧的 PhotoImage，可选水平翻转"""
        anim = self.get_animation(self.current_state)
        if not anim:
            return None

        source_frames = anim.get("sourceFrames", [])
        if not source_frames:
            return None

        # 确保索引有效
        if self.current_frame_idx >= len(source_frames):
            self.current_frame_idx = 0

        frame_index = source_frames[self.current_frame_idx]

        # 缓存键包含翻转状态
        cache_key = (frame_index, flip)
        if cache_key not in self.frame_cache:
            photo = self.sprite_sheet.get_frame(frame_index, self.scale, flip)
            if photo:
                self.frame_cache[cache_key] = photo

        return self.frame_cache.get(cache_key)

    def get_current_size(self) -> tuple[int, int]:
        """获取当前帧尺寸"""
        anim = self.get_animation(self.current_state)
        if not anim:
            return (64, 64)
        source_frames = anim.get("sourceFrames", [])
        if not source_frames or self.current_frame_idx >= len(source_frames):
            return (64, 64)
        return self.sprite_sheet.get_frame_size(source_frames[self.current_frame_idx], self.scale)

    def update(self, dt: float):
        """更新动画状态，dt 为秒"""
        anim = self.get_animation(self.current_state)
        if not anim:
            return

        fps = anim.get("fps", 10)
        loop = anim.get("loop", True)
        source_frames = anim.get("sourceFrames", [])
        total = len(source_frames)

        if total == 0:
            return

        self.frame_timer += dt
        frame_duration = 1.0 / fps

        if self.frame_timer >= frame_duration:
            self.frame_timer -= frame_duration
            self.current_frame_idx += 1

            if self.current_frame_idx >= total:
                if loop:
                    self.current_frame_idx = 0
                else:
                    self.current_frame_idx = total - 1

    def force_state(self, state: str):
        """强制切换到指定状态，重置帧索引"""
        if state in self.animations and state != self.current_state:
            self.current_state = state
            self.current_frame_idx = 0
            self.frame_timer = 0.0

    def do_action(self, action: str) -> str:
        """执行动作，返回对应的动画状态"""
        state = self.action_map.get(action, "idle")
        self.force_state(state)
        return state

    def is_playing_one_shot(self) -> bool:
        """检查是否正在播放非循环动画且未结束"""
        anim = self.get_animation(self.current_state)
        if not anim:
            return False
        if anim.get("loop", True):
            return False
        source_frames = anim.get("sourceFrames", [])
        return self.current_frame_idx < len(source_frames) - 1

    def clear_cache(self):
        """清理帧缓存（释放内存）"""
        self.frame_cache.clear()


class VesperStateMachine:
    """Vesper 状态机 - 管理动画状态与游戏状态的联动"""

    def __init__(self, anim_controller: VesperAnimationController):
        self.anim = anim_controller
        self.is_sleeping = False
        self.is_alive = True
        self.pending_action = None  # 非循环动画结束后要切回的状态
        self.facing_left = False     # 朝向：False=右 True=左
        self.facing_timer = 0.0      # 随机换向计时器

    def update(self, dt: float, pet_data):
        """每帧更新，根据游戏状态管理动画"""
        self.is_sleeping = pet_data.is_sleeping
        self.is_alive = pet_data.is_alive

        # 死亡状态最高优先级
        if not self.is_alive and self.anim.current_state != "dead":
            self.anim.force_state("dead")
            return

        # 如果正在播放非循环动画且还没播完，继续播放
        if self.anim.is_playing_one_shot():
            self.anim.update(dt)
            return

        # 非循环动画播完了，检查是否有待处理的状态回切
        if self.pending_action:
            self.anim.force_state(self.pending_action)
            self.pending_action = None
            self.anim.update(dt)
            return

        # 根据游戏状态确定基础状态
        if self.is_sleeping:
            target = "sleeping"
        else:
            target = "idle"

        # 如果当前是非循环动画且已结束，切回基础状态
        anim = self.anim.get_animation(self.anim.current_state)
        if anim and not anim.get("loop", True):
            self.anim.force_state(target)
        elif self.anim.current_state not in ["idle", "sleeping", "running"]:
            # 其他状态也切回基础
            self.anim.force_state(target)

        # 随机换向：每5-15秒随机切换一次朝向（仅在idle/sleeping时）
        if self.anim.current_state in ["idle", "sleeping"]:
            self.facing_timer += dt
            if self.facing_timer >= random.uniform(5.0, 15.0):
                self.facing_timer = 0.0
                self.facing_left = not self.facing_left

        self.anim.update(dt)

    def on_action(self, action: str):
        """响应游戏动作"""
        if not self.is_alive and action != "revive":
            return

        state = self.anim.do_action(action)

        # 非循环动画播完后要回 idle
        anim = self.anim.get_animation(state)
        if anim and not anim.get("loop", True):
            self.pending_action = "idle"
        else:
            self.pending_action = None

    def on_drag_start(self, facing_left: bool):
        """开始拖拽时切换到跑动动画并固定朝向"""
        self.facing_left = facing_left
        self.anim.force_state("running")

    def on_drag_end(self):
        """拖拽结束时切回idle"""
        self.anim.force_state("idle")
    def on_sleep(self):
        self.is_sleeping = True
        self.anim.force_state("sleeping")

    def on_wake(self):
        self.is_sleeping = False
        self.anim.force_state("idle")

    def on_death(self):
        self.is_alive = False
        self.anim.force_state("dead")


# ============================================================================
# 宠物数据类
# ============================================================================

class PetData:
    """宠物数据存储类"""

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

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "pet_type": self.pet_type,
            "hunger": self.hunger,
            "mood": self.mood,
            "energy": self.energy,
            "health": self.health,
            "is_alive": self.is_alive,
            "is_sleeping": self.is_sleeping,
            "created_at": self.created_at,
            "last_saved": now_str(),
            "total_interactions": self.total_interactions,
            "age_days": self.age_days,
            "death_time": self.death_time,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "PetData":
        pet = cls()
        for key, val in d.items():
            if hasattr(pet, key):
                setattr(pet, key, val)
        # 确保名字是 Vesper
        pet.name = "Vesper"
        pet.pet_type = "vesper"
        return pet

    def update_health(self):
        if not self.is_alive:
            return

        # 健康值由其他状态加权计算
        self.health = clamp(int(self.hunger * 0.5 + self.mood * 0.1 + self.energy * 0.4))

        # 检查死亡
        if self.health <= 0:
            self.health = 0
            self.is_alive = False
            self.death_time = now_str()


# ============================================================================
# 存储管理
# ============================================================================

def save_pet_data(pet: PetData):
    try:
        data = pet.to_dict()
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[保存失败] {e}")


def load_pet_data() -> PetData | None:
    if not os.path.exists(DATA_FILE):
        return None
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return PetData.from_dict(data)
    except Exception as e:
        print(f"[加载失败] {e}")
        return None


# ============================================================================
# 系统托盘 (可选)
# ============================================================================

def setup_tray(pet_app):
    try:
        import pystray
        from PIL import Image, ImageDraw

        img = Image.new("RGBA", (64, 64), (255, 255, 200, 255))
        draw = ImageDraw.Draw(img)
        draw.ellipse([8, 8, 56, 56], fill=(255, 180, 50, 255))
        draw.ellipse([20, 22, 28, 30], fill=(60, 60, 60, 255))
        draw.ellipse([36, 22, 44, 30], fill=(60, 60, 60, 255))
        draw.arc([22, 34, 42, 46], 0, 180, fill=(60, 60, 60, 255), width=2)

        def on_show(icon, item):
            pet_app.root.after(0, pet_app.root.deiconify)

        def on_quit(icon, item):
            pet_app.save_and_quit()
            icon.stop()

        def on_feed(icon, item):
            pet_app.root.after(0, lambda: pet_app.do_action("feed"))

        def on_play(icon, item):
            pet_app.root.after(0, lambda: pet_app.do_action("play"))

        menu = pystray.Menu(
            pystray.MenuItem("显示宠物", on_show, default=True),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("喂食🍖", on_feed),
            pystray.MenuItem("玩耍🎾", on_play),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("退出🚪", on_quit),
        )

        icon = pystray.Icon("desktop_pet", img, "桌面宠物 Vesper", menu)
        tray_thread = threading.Thread(target=icon.run, daemon=True)
        tray_thread.start()
        print("[系统托盘] 已启用 (pystray)")
        return icon

    except ImportError:
        print("[系统托盘] pystray 未安装，跳过")
        return None
    except Exception as e:
        print(f"[系统托盘] 初始化失败: {e}")
        return None


# ============================================================================
# 悬停浮窗状态显示
# ============================================================================

class HoverPopup:
    """鼠标悬停时显示的宠物状态浮窗"""

    def __init__(self, parent, pet_data):
        self.parent = parent
        self.pet = pet_data
        self.popup = None
        self.visible = False
        self._hide_timer = None

    def show(self, x: int, y: int):
        """在指定位置显示浮窗 - 位于宠物上方，不重叠"""
        if self.visible:
            return

        self.popup = tk.Toplevel(self.parent)
        self.popup.overrideredirect(True)
        self.popup.attributes("-topmost", True)
        self.popup.attributes("-alpha", 0.95)
        self.popup.configure(bg=COLORS["popup_bg"])

        # 构建内容
        self._build_content()

        # 定位：在宠物上方，留出间距避免重叠
        pw = 200
        ph = 145
        px = x - pw // 2
        py = y - ph - 75  # 75像素间距，大幅上移避免与气泡重叠
        self.popup.geometry(f"{pw}x{ph}+{px}+{py}")

        self.visible = True

    def _build_content(self):
        """构建浮窗内容 - 加大尺寸确保显示完整"""
        p = self.popup
        pet = self.pet

        # 名字
        tk.Label(
            p, text=f"✨ {pet.name}",
            font=("Microsoft YaHei UI", 12, "bold"),
            bg=COLORS["popup_bg"], fg="#E65100"
        ).pack(pady=(8, 4))

        # 状态条
        stats = [
            ("🍖 饱食度", pet.hunger),
            ("😊 心情值", pet.mood),
            ("⚡ 精力值", pet.energy),
            ("❤️ 健康值", pet.health),
        ]

        for label, value in stats:
            row = tk.Frame(p, bg=COLORS["popup_bg"])
            row.pack(fill="x", padx=10, pady=1)

            tk.Label(
                row, text=label,
                font=("Microsoft YaHei UI", 9),
                bg=COLORS["popup_bg"], fg="#555",
                anchor="w"
            ).pack(side="left")

            # 进度条
            bar_w = 85
            bar_h = 10
            bar_canvas = tk.Canvas(row, width=bar_w, height=bar_h,
                                   bg=COLORS["bar_bg"], highlightthickness=0)
            bar_canvas.pack(side="left", padx=(4, 0))

            color = get_status_color(value)
            fill_w = int(bar_w * value / MAX_STAT)
            if fill_w > 0:
                bar_canvas.create_rectangle(0, 0, fill_w, bar_h, fill=color, outline="")

            tk.Label(
                row, text=str(value),
                font=("Microsoft YaHei UI", 9, "bold"),
                bg=COLORS["popup_bg"], fg=color,
            ).pack(side="left", padx=(3, 0))

    def hide(self):
        """隐藏浮窗"""
        if self.popup:
            try:
                self.popup.destroy()
            except Exception:
                pass
            self.popup = None
        self.visible = False

        if self._hide_timer:
            self.parent.after_cancel(self._hide_timer)
            self._hide_timer = None

    def schedule_hide(self, delay: int = 200):
        """延迟隐藏"""
        if self._hide_timer:
            self.parent.after_cancel(self._hide_timer)
        self._hide_timer = self.parent.after(delay, self.hide)


# ============================================================================
# 主应用类
# ============================================================================

class DesktopPetApp:
    """桌面宠物主应用 - Vesper 版"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("桌面宠物 Vesper")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.92)
        self.root.configure(bg=COLORS["bg"])
        # 设置透明色，使窗口背景完全透明（仅显示宠物，无矩形区域）
        self.root.attributes("-transparentcolor", COLORS["bg"])

        # 窗口尺寸和位置
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        x = screen_w - WINDOW_W - 30
        y = screen_h - WINDOW_H - 80
        self.root.geometry(f"{WINDOW_W}x{WINDOW_H}+{x}+{y}")

        # 动画状态
        self.anim_time = 0.0
        self.bubble_text = ""
        self.bubble_timer = 0
        self.is_dragging = False
        self.drag_offset = (0, 0)
        self.mouse_hover = False

        # Vesper 动画系统
        self.sprite_sheet = None
        self.anim_controller = None
        self.state_machine = None
        self.use_emoji_fallback = False
        self.current_photo = None
        self.pet_image_id = None

        # 悬停浮窗
        self.hover_popup = None

        # 系统托盘
        self.tray_icon = None

        # 加载或创建宠物
        self.pet = self.init_pet()

        # 初始化 Vesper 动画系统
        self._init_vesper_system()

        # 构建UI
        self.build_ui()

        # 绑定事件
        self.bind_events()

        # 启动动画
        self.animate()

        # 启动状态衰减
        self.decay_loop()

        # 启动自动保存
        self.autosave_loop()

        # 初始气泡
        if self.pet.is_alive:
            self.show_bubble("你好！我是 Vesper~✨")

        # 系统托盘
        self.tray_icon = setup_tray(self)

    def _init_vesper_system(self):
        """初始化 Vesper 精灵图和动画系统"""
        if not HAS_PIL:
            self.use_emoji_fallback = True
            print("[Vesper] Pillow 不可用，使用 emoji 回退")
            return

        # 检查文件
        if not os.path.exists(CONFIG_FILE):
            print(f"[Vesper] 配置文件不存在: {CONFIG_FILE}")
            self.use_emoji_fallback = True
            return
        if not os.path.exists(SPRITE_FILE):
            print(f"[Vesper] 精灵图不存在: {SPRITE_FILE}")
            self.use_emoji_fallback = True
            return

        # 加载精灵图
        self.sprite_sheet = VesperSpriteSheet(CONFIG_FILE, SPRITE_FILE)
        if not self.sprite_sheet.loaded:
            print(f"[Vesper] 精灵图加载失败: {self.sprite_sheet.error_msg}")
            self.use_emoji_fallback = True
            return

        # 加载动画配置
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
        except Exception as e:
            print(f"[Vesper] 配置读取失败: {e}")
            self.use_emoji_fallback = True
            return

        # 创建控制器和状态机
        self.anim_controller = VesperAnimationController(self.sprite_sheet, config)
        self.state_machine = VesperStateMachine(self.anim_controller)

        print("[Vesper] 动画系统初始化成功")

    def init_pet(self) -> PetData:
        """初始化宠物 - Vesper 固定为默认"""
        pet = load_pet_data()

        if pet is not None:
            # 强制设置为 Vesper
            pet.name = "Vesper"
            pet.pet_type = "vesper"

            if not pet.is_alive:
                self.root.after(100)
                answer = messagebox.askyesno(
                    "宠物状态",
                    f"😢 {pet.name} 已经不在了...\n"
                    f"死亡时间: {pet.death_time}\n\n"
                    f"是否要复活 Vesper？",
                    parent=self.root
                )
                if answer:
                    return self.create_new_pet()
                else:
                    return pet
            return pet
        else:
            return self.create_new_pet()

    def create_new_pet(self) -> PetData:
        """创建新宠物 - 固定为 Vesper"""
        pet = PetData()
        pet.name = "Vesper"
        pet.pet_type = "vesper"
        save_pet_data(pet)
        return pet

    def build_ui(self):
        """构建宠物UI - 只显示宠物，状态条移到悬停浮窗"""
        self.canvas = tk.Canvas(
            self.root, width=WINDOW_W, height=WINDOW_H,
            bg=COLORS["bg"], highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)

        # 绘制初始画面
        self.draw_pet()

    def draw_pet(self):
        """绘制/更新宠物视觉"""
        self.canvas.delete("all")
        c = self.canvas
        pet = self.pet

        cx = WINDOW_W // 2
        cy = WINDOW_H // 2 + 10

        if self.use_emoji_fallback:
            # Emoji 回退模式
            emoji = "🐱"
            if pet.is_sleeping:
                emoji = "😴"
            elif not pet.is_alive:
                emoji = "💀"

            bob_y = math.sin(self.anim_time * 2.0) * 6
            pet_y = cy + bob_y

            c.create_text(
                cx, pet_y, text=emoji,
                font=("Segoe UI Emoji", 48),
                tags="pet_emoji"
            )
        else:
            # Vesper 精灵图模式
            if self.anim_controller and self.state_machine:
                flip = self.state_machine.facing_left
                photo = self.anim_controller.get_current_photo(flip=flip)
                if photo:
                    self.current_photo = photo  # 保持引用防止GC
                    fw, fh = self.anim_controller.get_current_size()

                    # 浮动动画
                    bob_y = math.sin(self.anim_time * 2.0) * 4 if pet.is_alive else 0
                    img_y = cy + bob_y

                    self.pet_image_id = c.create_image(
                        cx, img_y,
                        image=photo,
                        anchor="center",
                        tags="pet_image"
                    )

        # 语音气泡 - 放在宠物上方较远位置，避免与浮窗重叠
        if self.bubble_text and self.bubble_timer > 0:
            self.draw_bubble(cx, cy - 70)

        # 死亡提示
        if not pet.is_alive:
            c.create_text(
                cx, WINDOW_H - 25, text="😢 已永远离开...",
                font=("Microsoft YaHei UI", 10, "italic"),
                fill="#888888"
            )
            c.create_text(
                cx, WINDOW_H - 10, text="右键点击复活",
                font=("Microsoft YaHei UI", 8),
                fill="#AAAAAA"
            )

    def draw_bubble(self, x: int, y: int):
        """绘制语音气泡"""
        c = self.canvas
        text = self.bubble_text

        # 气泡居中显示，宽度根据文本自适应
        text_len = len(text)
        bw = max(80, text_len * 16 + 30)
        bh = 32

        # 水平居中，确保不超出窗口边界
        bx1 = max(8, (WINDOW_W - bw) // 2)
        bx2 = bx1 + bw
        if bx2 > WINDOW_W - 8:
            bx2 = WINDOW_W - 8
            bx1 = max(8, bx2 - bw)

        # 垂直位置
        by1 = max(8, y - bh // 2)
        by2 = by1 + bh

        c.create_oval(
            bx1, by1, bx2, by2,
            fill=COLORS["bubble"], outline=COLORS["bubble_border"],
            width=1, tags="bubble"
        )

        tail_x = x
        tail_y = by2
        c.create_polygon(
            tail_x - 5, tail_y - 2,
            tail_x + 5, tail_y - 2,
            tail_x, tail_y + 8,
            fill=COLORS["bubble"], outline=COLORS["bubble_border"],
            tags="bubble"
        )

        c.create_text(
            x, (by1 + by2) // 2, text=text,
            font=("Microsoft YaHei UI", 10),
            fill="#333333", tags="bubble"
        )

    # =========================================================================
    # 动画系统
    # =========================================================================

    def animate(self):
        """主动画循环"""
        self.anim_time += 0.05
        dt = ANIM_INTERVAL / 1000.0  # 秒

        # 更新 Vesper 动画系统
        if self.state_machine and self.anim_controller:
            self.state_machine.update(dt, self.pet)

        # 气泡计时
        if self.bubble_timer > 0:
            self.bubble_timer -= 1
            if self.bubble_timer <= 0:
                self.bubble_text = ""

        # 重新绘制
        self.draw_pet()

        # 下一帧
        self.root.after(ANIM_INTERVAL, self.animate)

    def show_bubble(self, text: str, duration: int = 40):
        """显示语音气泡，同时关闭状态浮窗避免重叠"""
        self.bubble_text = text
        self.bubble_timer = duration
        # 有气泡时关闭浮窗
        if self.hover_popup and self.hover_popup.visible:
            self.hover_popup.hide()

    # =========================================================================
    # 事件绑定
    # =========================================================================

    def bind_events(self):
        """绑定所有事件"""
        # 拖拽
        self.canvas.bind("<Button-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

        # 右键菜单
        self.canvas.bind("<Button-3>", self.show_context_menu)

        # 悬停检测
        self.canvas.bind("<Enter>", self.on_hover_enter)
        self.canvas.bind("<Leave>", self.on_hover_leave)

    def on_press(self, event):
        """鼠标按下 - 开始拖拽，隐藏浮窗，记录拖拽起始X用于判断方向"""
        self.is_dragging = True
        self.drag_offset = (event.x, event.y)
        self.drag_start_x = event.x_root  # 记录屏幕X坐标用于判断方向
        if self.hover_popup:
            self.hover_popup.hide()

    def on_drag(self, event):
        """鼠标拖拽 - 移动窗口，根据方向播放跑动动画"""
        if self.is_dragging:
            x = self.root.winfo_x() + (event.x - self.drag_offset[0])
            y = self.root.winfo_y() + (event.y - self.drag_offset[1])
            self.root.geometry(f"+{x}+{y}")
            if self.hover_popup:
                self.hover_popup.hide()

            # 根据拖拽方向切换朝向和跑动动画
            if self.state_machine:
                dx = event.x_root - self.drag_start_x
                if dx != 0:
                    facing_left = dx < 0
                    if self.state_machine.facing_left != facing_left or self.state_machine.anim.current_state != "running":
                        self.state_machine.on_drag_start(facing_left)
                    self.drag_start_x = event.x_root

    def on_release(self, event):
        """鼠标释放 - 结束拖拽，切回idle"""
        self.is_dragging = False
        if self.state_machine:
            self.state_machine.on_drag_end()

    def on_hover_enter(self, event):
        """鼠标进入窗口 - 显示状态浮窗（如果不在拖拽中且没有气泡）"""
        if not self.is_dragging and self.pet.is_alive and not self.bubble_text:
            self.mouse_hover = True
            if not self.hover_popup:
                self.hover_popup = HoverPopup(self.root, self.pet)

            # 获取宠物中心位置用于浮窗定位
            cx = self.root.winfo_x() + WINDOW_W // 2
            cy = self.root.winfo_y() + WINDOW_H // 2
            self.hover_popup.show(cx, cy)

    def on_hover_leave(self, event):
        """鼠标离开窗口 - 隐藏浮窗"""
        self.mouse_hover = False
        if self.hover_popup:
            self.hover_popup.schedule_hide(delay=100)

    # =========================================================================
    # 右键菜单
    # =========================================================================

    def show_context_menu(self, event):
        """显示右键菜单"""
        menu = tk.Menu(self.root, tearoff=0, font=("Microsoft YaHei UI", 10))

        if self.pet.is_alive:
            if self.pet.is_sleeping:
                menu.add_command(label="起床！⏰", command=lambda: self.do_action("wake"))
            else:
                menu.add_command(label="喂食 🍖", command=lambda: self.do_action("feed"))
                menu.add_command(label="玩耍 🎾", command=lambda: self.do_action("play"))
                menu.add_command(label="睡觉 💤", command=lambda: self.do_action("sleep"))
                menu.add_command(label="抚摸 🖐️", command=lambda: self.do_action("pet"))
                menu.add_command(label="洗澡 🛁", command=lambda: self.do_action("clean"))

            menu.add_separator()
            menu.add_command(label="聊天 💬", command=lambda: self.do_action("chat"))

        menu.add_separator()

        if not self.pet.is_alive:
            menu.add_command(label="复活 Vesper 🌟", command=self.revive_pet)

        menu.add_command(label="退出 🚪", command=self.save_and_quit)

        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    # =========================================================================
    # 动作系统
    # =========================================================================

    def do_action(self, action: str):
        """执行宠物动作"""
        pet = self.pet

        if not pet.is_alive and action != "revive":
            self.show_bubble("我...已经不在了...😢")
            return

        pet.total_interactions += 1

        if action == "feed":
            if pet.is_sleeping:
                self.show_bubble("我还在睡觉呢...💤")
                return
            pet.hunger = clamp(pet.hunger + random.randint(15, 25))
            pet.mood = clamp(pet.mood + random.randint(3, 8))
            self.show_bubble(random.choice(ACTION_BUBBLES["feed"]))

        elif action == "play":
            if pet.is_sleeping:
                self.show_bubble("我还在睡觉呢...💤")
                return
            if pet.energy < 15:
                self.show_bubble("太累了，玩不动了...😫")
                return
            pet.mood = clamp(pet.mood + random.randint(12, 25))
            pet.energy = clamp(pet.energy - random.randint(10, 20))
            pet.hunger = clamp(pet.hunger - random.randint(5, 10))
            self.show_bubble(random.choice(ACTION_BUBBLES["play"]))

        elif action == "sleep":
            pet.is_sleeping = True
            if self.state_machine:
                self.state_machine.on_sleep()
            self.show_bubble(random.choice(ACTION_BUBBLES["sleep"]))

        elif action == "wake":
            if pet.energy < 30:
                self.show_bubble("还想再睡一会儿...😴")
                return
            pet.is_sleeping = False
            if self.state_machine:
                self.state_machine.on_wake()
            self.show_bubble("早安！精神满满！✨")

        elif action == "pet":
            if pet.is_sleeping:
                self.show_bubble("呼噜呼噜...💕")
                pet.mood = clamp(pet.mood + 5)
            else:
                pet.mood = clamp(pet.mood + random.randint(8, 18))
                self.show_bubble(random.choice(ACTION_BUBBLES["pet"]))

        elif action == "clean":
            if pet.is_sleeping:
                self.show_bubble("我还在睡觉呢...💤")
                return
            pet.health = clamp(pet.health + random.randint(5, 10))
            pet.mood = clamp(pet.mood + random.randint(3, 8))
            self.show_bubble(random.choice(ACTION_BUBBLES["clean"]))

        elif action == "chat":
            bubble = random.choice(ACTION_BUBBLES["chat"])
            self.show_bubble(bubble, duration=60)
            pet.mood = clamp(pet.mood + random.randint(2, 6))

        # 通知动画系统
        if self.state_machine:
            self.state_machine.on_action(action)

        # 保存数据
        save_pet_data(pet)

        # 刷新浮窗（如果显示中）
        if self.hover_popup and self.hover_popup.visible:
            self.hover_popup.hide()
            if not self.is_dragging:
                cx = self.root.winfo_x() + WINDOW_W // 2
                cy = self.root.winfo_y() + WINDOW_H // 2
                self.hover_popup = HoverPopup(self.root, self.pet)
                self.hover_popup.show(cx, cy)

    # =========================================================================
    # 状态衰减系统
    # =========================================================================

    def decay_loop(self):
        """定期衰减宠物状态"""
        pet = self.pet

        if pet.is_alive:
            if not pet.is_sleeping:
                pet.hunger = clamp(int(pet.hunger - DECAY_RATES["hunger"]))
                pet.mood = clamp(int(pet.mood - DECAY_RATES["mood"]))
                pet.energy = clamp(int(pet.energy - abs(DECAY_RATES["energy"])))
            else:
                pet.energy = clamp(int(pet.energy + abs(DECAY_RATES["energy"])))
                pet.hunger = clamp(int(pet.hunger - DECAY_RATES["hunger"]))
                pet.mood = clamp(int(pet.mood - DECAY_RATES["mood"]))

                if pet.energy >= MAX_STAT:
                    pet.is_sleeping = False
                    if self.state_machine:
                        self.state_machine.on_wake()
                    self.show_bubble("精力充沛！☀️")

            pet.update_health()
            self.check_warnings()

            if not pet.is_alive:
                if self.state_machine:
                    self.state_machine.on_death()
                self.show_bubble(random.choice(ACTION_BUBBLES["death"]), duration=100)
                save_pet_data(pet)

        self.root.after(DECAY_INTERVAL, self.decay_loop)

    def check_warnings(self):
        """检查并显示状态警告"""
        pet = self.pet
        if not pet.is_alive:
            return
        if random.random() > 0.3:
            return

        if pet.hunger <= 15:
            self.show_bubble(random.choice(ACTION_BUBBLES["warn_hunger"]))
        elif pet.mood <= 15:
            self.show_bubble(random.choice(ACTION_BUBBLES["warn_mood"]))
        elif pet.energy <= 15 and not pet.is_sleeping:
            self.show_bubble(random.choice(ACTION_BUBBLES["warn_energy"]))
        elif pet.health <= 25:
            self.show_bubble(random.choice(ACTION_BUBBLES["warn_health"]))

    # =========================================================================
    # 自动保存
    # =========================================================================

    def autosave_loop(self):
        save_pet_data(self.pet)
        self.root.after(AUTOSAVE_INTERVAL, self.autosave_loop)

    # =========================================================================
    # 复活
    # =========================================================================

    def revive_pet(self):
        """复活 Vesper"""
        if os.path.exists(DATA_FILE):
            os.remove(DATA_FILE)

        self.pet = self.create_new_pet()
        if self.state_machine:
            self.state_machine.is_alive = True
            self.state_machine.on_wake()

        if self.pet.is_alive:
            self.show_bubble(f"你好！我是{self.pet.name}~✨")

    # =========================================================================
    # 退出
    # =========================================================================

    def save_and_quit(self):
        save_pet_data(self.pet)
        print(f"[{now_str()}] 宠物数据已保存，再见！")

        if self.hover_popup:
            self.hover_popup.hide()

        if self.tray_icon is not None:
            try:
                self.tray_icon.stop()
            except Exception:
                pass

        self.root.destroy()

    # =========================================================================
    # 运行
    # =========================================================================

    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self.save_and_quit)
        self.root.mainloop()


# ============================================================================
# 入口
# ============================================================================

def main():
    print("=" * 50)
    print("  🐾 桌面宠物 Desktop Pet - Vesper 版")
    print("  按 Ctrl+C 或右键退出")
    print("=" * 50)

    app = DesktopPetApp()
    app.run()


if __name__ == "__main__":
    main()
