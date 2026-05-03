#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
桌面宠物 (Desktop Pet) - 可爱的桌面伴侣
==========================================
一个使用 Python + tkinter 制作的桌面浮窗宠物应用。
支持喂食、玩耍、睡觉、抚摸、洗澡、聊天等互动。
宠物有实时状态条、闲置动画、语音气泡、死亡机制等。

用法: python desktop_pet.py
依赖: Python 3.8+ (标准库)
可选: pystray + Pillow (系统托盘支持)

作者: Hermes Agent
"""

import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
import json
import os
import time
import random
import math
import datetime
import threading
import sys

# ============================================================================
# 常量与配置
# ============================================================================

# 数据文件路径 - 保存在脚本同目录下
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(SCRIPT_DIR, "pets_gui.json")

# 窗口尺寸
WINDOW_W = 220
WINDOW_H = 260
STATUS_BAR_H = 12
STATUS_BAR_W = 100

# 动画间隔 (毫秒)
ANIM_INTERVAL = 50          # 主动画循环
DECAY_INTERVAL = 10000      # 状态衰减间隔 (10秒)
AUTOSAVE_INTERVAL = 60000   # 自动保存间隔 (60秒)

# 宠物类型定义
PET_TYPES = {
    "cat":    {"emoji": "🐱", "name": "猫咪", "alt_emojis": ["😺", "😸", "😻", "🙀", "😿", "😾", "😽"]},
    "dog":    {"emoji": "🐶", "name": "小狗", "alt_emojis": ["🐕", "🦮", "🐕‍🦺", "🐾"]},
    "rabbit": {"emoji": "🐰", "name": "兔子", "alt_emojis": ["🐇", "🥕"]},
    "dragon": {"emoji": "🐉", "name": "龙龙", "alt_emojis": ["🔥", "🐲", "✨", "💫"]},
    "fox":    {"emoji": "🦊", "name": "狐狸", "alt_emojis": ["🧡", "🍁"]},
}

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

# 状态衰减速率 (每次衰减减少的量)
DECAY_RATES = {
    "hunger":  3,    # 饥饿值下降 (饥饿感增加)
    "mood":    2,    # 心情下降
    "energy":  -1,   # 睡觉时恢复精力，清醒时缓慢消耗 (负数=恢复)
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
}

# ============================================================================
# 工具函数
# ============================================================================

def get_status_color(value: int) -> str:
    """根据状态值返回对应颜色"""
    if value >= 60:
        return COLORS["green"]
    elif value >= 30:
        return COLORS["yellow"]
    else:
        return COLORS["red"]


def clamp(value: int, lo: int = 0, hi: int = MAX_STAT) -> int:
    """将值限制在范围内"""
    return max(lo, min(hi, value))


def now_str() -> str:
    """返回当前时间字符串"""
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ============================================================================
# 宠物数据类
# ============================================================================

class PetData:
    """宠物数据存储类，负责管理宠物的所有状态"""

    def __init__(self):
        self.name: str = "宠物"
        self.pet_type: str = "cat"
        self.hunger: int = 50       # 饥饿值 (0=最饿, 100=最饱)
        self.mood: int = 80         # 心情 (0=最差, 100=最好)
        self.energy: int = 80       # 精力 (0=最困, 100=最精神)
        self.health: int = 100      # 健康 (0=死亡)
        self.is_alive: bool = True
        self.is_sleeping: bool = False
        self.created_at: str = now_str()
        self.last_saved: str = now_str()
        self.total_interactions: int = 0
        self.age_days: int = 0
        self.death_time: str = ""

    def to_dict(self) -> dict:
        """序列化为字典"""
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
        """从字典反序列化"""
        pet = cls()
        for key, val in d.items():
            if hasattr(pet, key):
                setattr(pet, key, val)
        return pet

    def get_emoji(self) -> str:
        """获取当前宠物的 emoji"""
        info = PET_TYPES.get(self.pet_type, PET_TYPES["cat"])
        return info["emoji"]

    def get_type_name(self) -> str:
        """获取宠物类型中文名"""
        info = PET_TYPES.get(self.pet_type, PET_TYPES["cat"])
        return info["name"]

    def get_alt_emoji(self) -> str:
        """获取一个随机的替代 emoji"""
        info = PET_TYPES.get(self.pet_type, PET_TYPES["cat"])
        return random.choice(info["alt_emojis"])

    def update_health(self):
        """根据其他状态更新健康值"""
        if not self.is_alive:
            return

        # 饥饿过低会扣健康
        if self.hunger <= 10:
            self.health = clamp(self.health - 2)
        elif self.hunger <= 20:
            self.health = clamp(self.health - 1)

        # 心情太差也会扣健康
        if self.mood <= 10:
            self.health = clamp(self.health - 1)

        # 良好状态会缓慢恢复健康
        if self.hunger > 50 and self.mood > 50 and self.energy > 30:
            self.health = clamp(self.health + 1)

        # 检查死亡
        if self.health <= 0:
            self.health = 0
            self.is_alive = False
            self.death_time = now_str()


# ============================================================================
# 存储管理
# ============================================================================

def save_pet_data(pet: PetData):
    """保存宠物数据到 JSON 文件"""
    try:
        data = pet.to_dict()
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[保存失败] {e}")


def load_pet_data() -> PetData | None:
    """从 JSON 文件加载宠物数据，不存在则返回 None"""
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
    """尝试设置系统托盘图标，如果 pystray/PIL 不可用则跳过"""
    try:
        import pystray
        from PIL import Image, ImageDraw

        # 创建一个简单的图标
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

        icon = pystray.Icon("desktop_pet", img, "桌面宠物", menu)
        tray_thread = threading.Thread(target=icon.run, daemon=True)
        tray_thread.start()
        print("[系统托盘] 已启用 (pystray)")
        return icon

    except ImportError:
        print("[系统托盘] pystray 或 PIL 未安装，跳过系统托盘支持")
        return None
    except Exception as e:
        print(f"[系统托盘] 初始化失败: {e}")
        return None


# ============================================================================
# 初始设置对话框
# ============================================================================

class SetupDialog:
    """首次运行时的宠物选择对话框"""

    def __init__(self, parent):
        self.result = None
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("🐾 选择你的宠物")
        self.dialog.geometry("400x450")
        self.dialog.resizable(False, False)
        self.dialog.configure(bg="#FFF8E7")
        self.dialog.grab_set()
        self.dialog.transient(parent)

        # 居中显示
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 400) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 450) // 2
        self.dialog.geometry(f"+{x}+{y}")

        # 标题
        tk.Label(
            self.dialog, text="✨ 欢迎来到桌面宠物！✨",
            font=("Microsoft YaHei UI", 16, "bold"),
            bg="#FFF8E7", fg="#E65100"
        ).pack(pady=(20, 5))

        tk.Label(
            self.dialog, text="选择你想要的宠物伙伴：",
            font=("Microsoft YaHei UI", 11),
            bg="#FFF8E7", fg="#555555"
        ).pack(pady=(0, 15))

        # 宠物选择区域
        self.selected_type = tk.StringVar(value="cat")
        btn_frame = tk.Frame(self.dialog, bg="#FFF8E7")
        btn_frame.pack(pady=5)

        self.pet_buttons = {}
        for i, (key, info) in enumerate(PET_TYPES.items()):
            frame = tk.Frame(btn_frame, bg="#FFF8E7", padx=8, pady=5)
            frame.grid(row=0, column=i)

            btn = tk.Label(
                frame, text=info["emoji"],
                font=("Segoe UI Emoji", 36),
                bg="#FFF8E7", cursor="hand2",
                padx=10, pady=5,
                relief="groove", bd=2
            )
            btn.pack()
            btn.bind("<Button-1>", lambda e, k=key: self.select_pet(k))

            tk.Label(
                frame, text=info["name"],
                font=("Microsoft YaHei UI", 10),
                bg="#FFF8E7"
            ).pack()

            self.pet_buttons[key] = btn

        # 高亮默认选择
        self.highlight_selected()

        # 名字输入
        tk.Label(
            self.dialog, text="给你的宠物起个名字：",
            font=("Microsoft YaHei UI", 11),
            bg="#FFF8E7", fg="#555555"
        ).pack(pady=(20, 5))

        self.name_entry = tk.Entry(
            self.dialog, font=("Microsoft YaHei UI", 13),
            justify="center", width=15,
            relief="solid", bd=1
        )
        self.name_entry.insert(0, "")
        self.name_entry.pack(pady=5)
        self.name_entry.focus_set()

        # 随机名字按钮
        random_names = ["小可爱", "团团", "圆圆", "皮蛋", "布丁", "奶茶",
                        "豆豆", "糯米", "芒果", "雪球", "元宝", "芝麻"]
        tk.Button(
            self.dialog, text="🎲 随机名字",
            font=("Microsoft YaHei UI", 9),
            command=lambda: self.name_entry.delete(0, tk.END) or
                            self.name_entry.insert(0, random.choice(random_names)),
            bg="#E3F2FD", relief="flat", padx=10
        ).pack(pady=3)

        # 确认按钮
        tk.Button(
            self.dialog, text="✨ 开始冒险！✨",
            font=("Microsoft YaHei UI", 14, "bold"),
            bg="#4CAF50", fg="white",
            activebackground="#388E3C", activeforeground="white",
            relief="flat", padx=30, pady=8,
            command=self.confirm
        ).pack(pady=(20, 15))

        # 绑定回车
        self.dialog.bind("<Return>", lambda e: self.confirm())

    def select_pet(self, pet_type: str):
        """选择宠物类型"""
        self.selected_type.set(pet_type)
        self.highlight_selected()

    def highlight_selected(self):
        """高亮当前选中的宠物"""
        selected = self.selected_type.get()
        for key, btn in self.pet_buttons.items():
            if key == selected:
                btn.configure(bg="#FFECB3", relief="solid", bd=3)
            else:
                btn.configure(bg="#FFF8E7", relief="groove", bd=2)

    def confirm(self):
        """确认选择"""
        name = self.name_entry.get().strip()
        if not name:
            # 给个默认名
            info = PET_TYPES[self.selected_type.get()]
            name = info["name"]

        self.result = (self.selected_type.get(), name)
        self.dialog.destroy()


# ============================================================================
# 统计详情窗口
# ============================================================================

class StatsWindow:
    """宠物详细统计信息窗口"""

    def __init__(self, parent, pet: PetData):
        self.pet = pet
        self.win = tk.Toplevel(parent)
        self.win.title(f"📊 {pet.name} 的详细信息")
        self.win.geometry("320x420")
        self.win.resizable(False, False)
        self.win.configure(bg="#FAFAFA")
        self.win.transient(parent)

        self.build_ui()

    def build_ui(self):
        """构建统计界面"""
        pet = self.pet

        # 宠物名和图标
        header = tk.Frame(self.win, bg="#E8F5E9", padx=15, pady=12)
        header.pack(fill="x")

        tk.Label(
            header, text=f"{pet.get_emoji()} {pet.name}",
            font=("Microsoft YaHei UI", 18, "bold"),
            bg="#E8F5E9", fg="#1B5E20"
        ).pack()

        tk.Label(
            header, text=f"类型: {pet.get_type_name()}  |  {'💤 睡觉中' if pet.is_sleeping else '🟢 活跃'}",
            font=("Microsoft YaHei UI", 10),
            bg="#E8F5E9", fg="#666"
        ).pack(pady=(2, 0))

        # 状态详情
        info_frame = tk.Frame(self.win, bg="#FAFAFA", padx=20, pady=10)
        info_frame.pack(fill="both", expand=True)

        stats = [
            ("🍖 饱食度", pet.hunger, "肚子饱饱的好开心"),
            ("😊 心情值", pet.mood, "开心的宠物更健康"),
            ("⚡ 精力值", pet.energy, "累了就休息一下"),
            ("❤️ 健康值", pet.health, "保持各项数值健康"),
        ]

        for i, (label, value, desc) in enumerate(stats):
            row = tk.Frame(info_frame, bg="#FAFAFA")
            row.pack(fill="x", pady=8)

            tk.Label(
                row, text=label,
                font=("Microsoft YaHei UI", 12, "bold"),
                bg="#FAFAFA", anchor="w"
            ).pack(fill="x")

            bar_frame = tk.Frame(row, bg="#FAFAFA")
            bar_frame.pack(fill="x", pady=2)

            # 状态条背景
            canvas = tk.Canvas(bar_frame, height=16, bg=COLORS["bar_bg"],
                              highlightthickness=0, bd=0)
            canvas.pack(fill="x", side="left", expand=True)

            color = get_status_color(value)
            canvas.create_rectangle(0, 0, value * 2, 16, fill=color, outline="")

            tk.Label(
                bar_frame, text=f"{value}/{MAX_STAT}",
                font=("Microsoft YaHei UI", 9, "bold"),
                bg="#FAFAFA", fg=color, width=7
            ).pack(side="right")

            tk.Label(
                row, text=desc,
                font=("Microsoft YaHei UI", 8),
                bg="#FAFAFA", fg="#999"
            ).pack(fill="x")

        # 底部信息
        footer = tk.Frame(self.win, bg="#E3F2FD", padx=15, pady=10)
        footer.pack(fill="x", side="bottom")

        info_text = (
            f"📅 创建时间: {pet.created_at}\n"
            f"🕐 最后保存: {pet.last_saved}\n"
            f"🤝 互动次数: {pet.total_interactions}\n"
            f"{'💀 已死亡 - ' + pet.death_time if not pet.is_alive else ''}"
        )
        tk.Label(
            footer, text=info_text,
            font=("Microsoft YaHei UI", 9),
            bg="#E3F2FD", fg="#555",
            justify="left", anchor="w"
        ).pack(fill="x")


# ============================================================================
# 主应用类
# ============================================================================

class DesktopPetApp:
    """桌面宠物主应用"""

    def __init__(self):
        # 创建主窗口
        self.root = tk.Tk()
        self.root.title("桌面宠物")
        self.root.overrideredirect(True)         # 无边框
        self.root.attributes("-topmost", True)   # 置顶
        self.root.attributes("-alpha", 0.92)     # 半透明
        self.root.configure(bg=COLORS["bg"])

        # 窗口尺寸和位置 (默认右下角)
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        x = screen_w - WINDOW_W - 30
        y = screen_h - WINDOW_H - 80  # 留出任务栏空间
        self.root.geometry(f"{WINDOW_W}x{WINDOW_H}+{x}+{y}")

        # 动画状态
        self.anim_time = 0.0
        self.blink_state = False
        self.blink_counter = 0
        self.bubble_text = ""
        self.bubble_timer = 0
        self.bubble_alpha = 1.0
        self.sleep_z_timer = 0
        self.is_dragging = False
        self.drag_offset = (0, 0)
        self.mood_bounce = 0

        # 统计窗口引用
        self.stats_window = None

        # 系统托盘
        self.tray_icon = None

        # 加载或创建宠物
        self.pet = self.init_pet()

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
            self.show_bubble(random.choice(ACTION_BUBBLES["idle"]))

        # 设置系统托盘 (在主线程窗口创建后)
        self.tray_icon = setup_tray(self)

    def init_pet(self) -> PetData:
        """初始化宠物 - 加载存档或显示选择对话框"""
        pet = load_pet_data()

        if pet is not None:
            # 已有存档
            if not pet.is_alive:
                # 宠物已死亡，询问是否重生
                self.root.after(100)  # 确保窗口已初始化
                answer = messagebox.askyesno(
                    "宠物状态",
                    f"😢 {pet.name} 已经不在了...\n"
                    f"死亡时间: {pet.death_time}\n\n"
                    f"是否要创建一个新伙伴？",
                    parent=self.root
                )
                if answer:
                    return self.create_new_pet()
                else:
                    return pet
            return pet
        else:
            # 首次运行 - 显示选择对话框
            return self.create_new_pet()

    def create_new_pet(self) -> PetData:
        """通过对话框创建新宠物"""
        dialog = SetupDialog(self.root)
        self.root.wait_window(dialog.dialog)

        if dialog.result:
            pet_type, name = dialog.result
            pet = PetData()
            pet.pet_type = pet_type
            pet.name = name
            save_pet_data(pet)
            return pet
        else:
            # 用户关闭了对话框，使用默认
            pet = PetData()
            save_pet_data(pet)
            return pet

    def build_ui(self):
        """构建宠物UI"""
        # 主画布
        self.canvas = tk.Canvas(
            self.root, width=WINDOW_W, height=WINDOW_H,
            bg=COLORS["bg"], highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)

        # 绘制所有元素
        self.draw_pet()

    def draw_pet(self):
        """绘制/更新宠物的所有视觉元素"""
        self.canvas.delete("all")
        c = self.canvas
        pet = self.pet

        cx = WINDOW_W // 2  # 水平中心

        # --- 背景装饰 (半透明圆角矩形效果) ---
        # 绘制一个淡淡的背景
        c.create_rectangle(5, 5, WINDOW_W - 5, WINDOW_H - 5,
                          fill="#FFFDE7", outline="#E0E0E0", width=1, stipple="gray25")

        # --- 宠物名字标签 ---
        name_display = f"{pet.name} {'💀' if not pet.is_alive else ''}"
        c.create_text(
            cx, 18, text=name_display,
            font=("Microsoft YaHei UI", 11, "bold"),
            fill="#333333", tags="name"
        )

        # --- 宠物 Emoji ---
        emoji = pet.get_emoji()
        if pet.is_sleeping:
            emoji = "😴"
        elif not pet.is_alive:
            emoji = "💀"
        elif self.blink_state:
            emoji = pet.get_alt_emoji()

        # 浮动动画 (正弦波上下飘动)
        bob_y = math.sin(self.anim_time * 2.0) * 6
        pet_y = 70 + bob_y + self.mood_bounce

        # 创建宠物 emoji 文字
        c.create_text(
            cx, pet_y, text=emoji,
            font=("Segoe UI Emoji", 48),
            tags="pet_emoji"
        )

        # --- 睡觉时的 ZZZ 动画 ---
        if pet.is_sleeping:
            self.sleep_z_timer += 1
            for i in range(3):
                z_offset = (self.sleep_z_timer * 0.5 + i * 25) % 80
                z_alpha = max(0, 1.0 - z_offset / 80.0)
                z_x = cx + 40 + z_offset * 0.3
                z_y = pet_y - 30 - z_offset
                if z_alpha > 0.2:
                    size = 10 + int(z_alpha * 8)
                    color_val = int(z_alpha * 200)
                    color = f"#{color_val:02x}{color_val:02x}{int(color_val * 0.7):02x}"
                    c.create_text(
                        z_x, z_y, text="Z",
                        font=("Arial", size, "bold"),
                        fill=COLORS["sleep_z"], tags="zzz"
                    )

        # --- 语音气泡 ---
        if self.bubble_text and self.bubble_timer > 0:
            self.draw_bubble(cx, pet_y - 55)

        # --- 状态条 ---
        if pet.is_alive:
            self.draw_status_bars(15, 130)

        # --- 死亡覆盖 ---
        if not pet.is_alive:
            c.create_text(
                cx, WINDOW_H - 60, text="😢 已永远离开...",
                font=("Microsoft YaHei UI", 11, "italic"),
                fill="#888888"
            )
            c.create_text(
                cx, WINDOW_H - 40, text="右键点击创建新伙伴",
                font=("Microsoft YaHei UI", 9),
                fill="#AAAAAA"
            )

    def draw_bubble(self, x: int, y: int):
        """绘制语音气泡"""
        c = self.canvas
        text = self.bubble_text

        # 计算气泡大小
        text_len = len(text)
        bw = max(80, text_len * 14 + 20)
        bh = 28

        bx1 = x - bw // 2
        by1 = y - bh // 2
        bx2 = x + bw // 2
        by2 = y + bh // 2

        # 确保不超出窗口
        if bx1 < 5:
            bx1, bx2 = 5, 5 + bw
        if bx2 > WINDOW_W - 5:
            bx2, bx1 = WINDOW_W - 5, WINDOW_W - 5 - bw
        if by1 < 5:
            by1, by2 = 5, 5 + bh

        # 气泡背景
        c.create_oval(
            bx1, by1, bx2, by2,
            fill=COLORS["bubble"], outline=COLORS["bubble_border"],
            width=1, tags="bubble"
        )

        # 小尾巴
        tail_x = x
        tail_y = by2
        c.create_polygon(
            tail_x - 5, tail_y - 2,
            tail_x + 5, tail_y - 2,
            tail_x, tail_y + 8,
            fill=COLORS["bubble"], outline=COLORS["bubble_border"],
            tags="bubble"
        )

        # 气泡文字
        c.create_text(
            x, (by1 + by2) // 2, text=text,
            font=("Microsoft YaHei UI", 10),
            fill="#333333", tags="bubble"
        )

    def draw_status_bars(self, x: int, y: int):
        """绘制状态条"""
        c = self.canvas
        pet = self.pet

        stats = [
            ("🍖", pet.hunger),
            ("😊", pet.mood),
            ("⚡", pet.energy),
            ("❤️", pet.health),
        ]

        bar_x = x + 30
        bar_w = STATUS_BAR_W

        for i, (icon, value) in enumerate(stats):
            row_y = y + i * 28

            # 图标
            c.create_text(
                x + 10, row_y + STATUS_BAR_H // 2,
                text=icon, font=("Segoe UI Emoji", 10),
                anchor="w", tags="status"
            )

            # 背景条
            c.create_rectangle(
                bar_x, row_y,
                bar_x + bar_w, row_y + STATUS_BAR_H,
                fill=COLORS["bar_bg"], outline="#CCCCCC", width=1,
                tags="status"
            )

            # 数值条
            color = get_status_color(value)
            fill_w = int(bar_w * value / MAX_STAT)
            if fill_w > 0:
                c.create_rectangle(
                    bar_x + 1, row_y + 1,
                    bar_x + fill_w - 1, row_y + STATUS_BAR_H - 1,
                    fill=color, outline="", tags="status"
                )

            # 数值文字
            c.create_text(
                bar_x + bar_w + 8, row_y + STATUS_BAR_H // 2,
                text=str(value), font=("Microsoft YaHei UI", 8, "bold"),
                fill=color, anchor="w", tags="status"
            )

    # =========================================================================
    # 动画系统
    # =========================================================================

    def animate(self):
        """主动画循环"""
        self.anim_time += 0.05

        # 眨眼动画
        self.blink_counter += 1
        if self.blink_counter >= random.randint(25, 50):
            self.blink_state = True
            self.blink_counter = 0
        elif self.blink_state and self.blink_counter >= 3:
            self.blink_state = False

        # 气泡计时
        if self.bubble_timer > 0:
            self.bubble_timer -= 1
            if self.bubble_timer <= 0:
                self.bubble_text = ""

        # 心情反弹动画
        if self.mood_bounce > 0:
            self.mood_bounce *= 0.85
            if self.mood_bounce < 0.5:
                self.mood_bounce = 0

        # 重新绘制
        self.draw_pet()

        # 下一帧
        self.root.after(ANIM_INTERVAL, self.animate)

    def show_bubble(self, text: str, duration: int = 40):
        """显示语音气泡"""
        self.bubble_text = text
        self.bubble_timer = duration

    def do_bounce(self, intensity: float = 15.0):
        """让宠物弹跳一下"""
        self.mood_bounce = -intensity

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

        # 双击查看详情
        self.canvas.bind("<Double-Button-1>", self.show_stats)

    def on_press(self, event):
        """鼠标按下 - 开始拖拽"""
        self.is_dragging = True
        self.drag_offset = (event.x, event.y)

    def on_drag(self, event):
        """鼠标拖拽 - 移动窗口"""
        if self.is_dragging:
            x = self.root.winfo_x() + (event.x - self.drag_offset[0])
            y = self.root.winfo_y() + (event.y - self.drag_offset[1])
            self.root.geometry(f"+{x}+{y}")

    def on_release(self, event):
        """鼠标释放"""
        self.is_dragging = False

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
        menu.add_command(label="详细统计 📊", command=self.show_stats)
        menu.add_separator()

        if not self.pet.is_alive:
            menu.add_command(label="创建新伙伴 🌟", command=self.revive_pet)

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
            self.do_bounce(10)

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
            self.do_bounce(20)

        elif action == "sleep":
            pet.is_sleeping = True
            self.show_bubble(random.choice(ACTION_BUBBLES["sleep"]))

        elif action == "wake":
            if pet.energy < 30:
                self.show_bubble("还想再睡一会儿...😴")
                return
            pet.is_sleeping = False
            self.show_bubble("早安！精神满满！✨")
            self.do_bounce(12)

        elif action == "pet":
            if pet.is_sleeping:
                self.show_bubble("呼噜呼噜...💕")
                pet.mood = clamp(pet.mood + 5)
            else:
                pet.mood = clamp(pet.mood + random.randint(8, 18))
                self.show_bubble(random.choice(ACTION_BUBBLES["pet"]))
            self.do_bounce(8)

        elif action == "clean":
            if pet.is_sleeping:
                self.show_bubble("我还在睡觉呢...💤")
                return
            pet.health = clamp(pet.health + random.randint(5, 10))
            pet.mood = clamp(pet.mood + random.randint(3, 8))
            self.show_bubble(random.choice(ACTION_BUBBLES["clean"]))
            self.do_bounce(5)

        elif action == "chat":
            bubble = random.choice(ACTION_BUBBLES["chat"])
            self.show_bubble(bubble, duration=60)
            pet.mood = clamp(pet.mood + random.randint(2, 6))
            self.do_bounce(3)

        # 保存数据
        save_pet_data(pet)

    # =========================================================================
    # 状态衰减系统
    # =========================================================================

    def decay_loop(self):
        """定期衰减宠物状态"""
        pet = self.pet

        if pet.is_alive:
            if not pet.is_sleeping:
                # 清醒状态
                pet.hunger = clamp(pet.hunger - DECAY_RATES["hunger"])
                pet.mood = clamp(pet.mood - DECAY_RATES["mood"])
                pet.energy = clamp(pet.energy - abs(DECAY_RATES["energy"]))
            else:
                # 睡觉状态 - 恢复精力
                pet.energy = clamp(pet.energy + 5)
                # 睡觉时也稍微饿一点
                pet.hunger = clamp(pet.hunger - 1)
                # 心情缓慢下降
                pet.mood = clamp(pet.mood - 1)

                # 精力满了自动醒来
                if pet.energy >= MAX_STAT:
                    pet.is_sleeping = False
                    self.show_bubble("精力充沛！☀️")

            # 更新健康
            pet.update_health()

            # 状态警告气泡
            self.check_warnings()

            # 检查死亡
            if not pet.is_alive:
                self.show_bubble(random.choice(ACTION_BUBBLES["death"]), duration=100)
                save_pet_data(pet)

        # 下次衰减
        self.root.after(DECAY_INTERVAL, self.decay_loop)

    def check_warnings(self):
        """检查并显示状态警告"""
        pet = self.pet

        if not pet.is_alive:
            return

        # 随机概率显示警告 (避免太频繁)
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
        """定期自动保存"""
        save_pet_data(self.pet)
        self.root.after(AUTOSAVE_INTERVAL, self.autosave_loop)

    # =========================================================================
    # 详细统计窗口
    # =========================================================================

    def show_stats(self, event=None):
        """显示详细统计窗口"""
        # 如果已有窗口，先关闭
        if self.stats_window is not None:
            try:
                self.stats_window.win.destroy()
            except Exception:
                pass

        self.stats_window = StatsWindow(self.root, self.pet)

    # =========================================================================
    # 复活 / 新建
    # =========================================================================

    def revive_pet(self):
        """创建新宠物"""
        # 先删除旧存档
        if os.path.exists(DATA_FILE):
            os.remove(DATA_FILE)

        self.pet = self.create_new_pet()
        if self.pet.is_alive:
            self.show_bubble(f"你好！我是{self.pet.name}~✨")
            self.do_bounce(15)

    # =========================================================================
    # 退出
    # =========================================================================

    def save_and_quit(self):
        """保存数据并退出"""
        save_pet_data(self.pet)
        print(f"[{now_str()}] 宠物数据已保存，再见！")

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
        """启动主循环"""
        # 窗口关闭协议
        self.root.protocol("WM_DELETE_WINDOW", self.save_and_quit)

        # 启动消息循环
        self.root.mainloop()


# ============================================================================
# 入口
# ============================================================================

def main():
    """主入口函数"""
    print("=" * 50)
    print("  🐾 桌面宠物 Desktop Pet")
    print("  按 Ctrl+C 或右键退出")
    print("=" * 50)

    app = DesktopPetApp()
    app.run()


if __name__ == "__main__":
    main()
