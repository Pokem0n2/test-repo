"""
桌面悬浮电子宠物 - tkinter 窗口版本
始终置顶、半透明、无边框、可拖拽
"""
import tkinter as tk
from tkinter import ttk
import threading
import time
import random
import sys
import os
from pathlib import Path

# 添加当前目录到路径以便导入 pet_data
sys.path.insert(0, str(Path(__file__).parent))
from pet_data import Pet, PET_TYPES, load_pets, save_pets


class FloatingPet:
    """悬浮宠物主类"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()  # 先隐藏，用于初始化

        # 窗口配置
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.9)
        self.root.configure(bg="systemTransparent")

        # 始终置顶
        self.root.lift()
        self.root.call("wm", "attributes", ".", "-topmost", "1")

        # 宠物数据
        self.pets = load_pets()
        self.active_pet = None
        self.drag_data = {"x": 0, "y": 0}

        # 动画状态
        self.float_offset = 0
        self.float_direction = 1
        self.is_animating = True

        # 初始化UI
        self._setup_ui()
        self._setup_tray()

        # 选择或创建宠物
        if self.pets:
            self._show_pet_selector()
        else:
            self._show_create_dialog()

        # 启动动画线程
        self.animating = True
        self.animation_thread = threading.Thread(target=self._float_animation, daemon=True)
        self.animation_thread.start()

        # 状态衰减线程
        self.decay_thread = threading.Thread(target=self._status_decay, daemon=True)
        self.decay_thread.start()

        # 协议处理
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self.root.mainloop()

    def _setup_ui(self):
        """设置UI组件"""
        # 主框架
        self.main_frame = tk.Frame(self.root, bg="#2d2d2d", bd=2, relief="ridge")
        self.main_frame.pack(fill="both", expand=True)

        # 宠物显示区域
        self.pet_label = tk.Label(
            self.main_frame,
            text="🐱",
            font=("Segoe UI Emoji", 48),
            bg="#2d2d2d",
            fg="white",
            cursor="fleur",
        )
        self.pet_label.pack(pady=(10, 5))

        # 名字标签
        self.name_label = tk.Label(
            self.main_frame,
            text="宠物",
            font=("Microsoft YaHei UI", 10, "bold"),
            bg="#2d2d2d",
            fg="white",
        )
        self.name_label.pack()

        # 状态条框架
        self.status_frame = tk.Frame(self.main_frame, bg="#2d2d2d")
        self.status_frame.pack(fill="x", padx=10, pady=5)

        # 状态条
        self.hunger_bar = self._create_bar("🍖 饱食", "#4CAF50")
        self.happiness_bar = self._create_bar("😊 心情", "#FFC107")
        self.energy_bar = self._create_bar("⚡ 精力", "#2196F3")
        self.health_bar = self._create_bar("❤️ 健康", "#f44336")

        # 状态提示
        self.status_label = tk.Label(
            self.main_frame,
            text="",
            font=("Microsoft YaHei UI", 8),
            bg="#2d2d2d",
            fg="#aaaaaa",
            wraplength=150,
        )
        self.status_label.pack(pady=2)

        # 按钮框架
        self.btn_frame = tk.Frame(self.main_frame, bg="#2d2d2d")
        self.btn_frame.pack(pady=5)

        self._create_buttons()

        # 右键菜单
        self.context_menu = tk.Menu(self.root, tearoff=0, bg="#2d2d2d", fg="white")
        self._setup_context_menu()

        # 绑定事件
        self.pet_label.bind("<Button-1>", self._on_drag_start)
        self.pet_label.bind("<B1-Motion>", self._on_drag_motion)
        self.main_frame.bind("<Button-3>", self._show_context_menu)

        # 拖拽整个窗口
        self.main_frame.bind("<Button-1>", self._on_drag_start)
        self.main_frame.bind("<B1-Motion>", self._on_drag_motion)

    def _create_bar(self, label: str, color: str) -> tuple:
        """创建状态条"""
        frame = tk.Frame(self.status_frame, bg="#2d2d2d")
        frame.pack(fill="x", pady=1)

        tk.Label(
            frame,
            text=label,
            font=("Microsoft YaHei UI", 7),
            bg="#2d2d2d",
            fg="white",
            width=8,
            anchor="w",
        ).pack(side="left")

        bar_frame = tk.Frame(frame, bg="#444444", height=8)
        bar_frame.pack(side="left", fill="x", expand=True, padx=(5, 0))
        bar_frame.pack_propagate(False)

        fill = tk.Frame(bar_frame, bg=color, width=0)
        fill.pack(fill="y", side="left")

        return fill

    def _create_buttons(self):
        """创建交互按钮"""
        buttons = [
            ("🍖", self._feed, "#4CAF50"),
            ("🎾", self._play, "#8BC34A"),
            ("💤", self._sleep, "#2196F3"),
            ("🖐️", self._pet, "#9C27B0"),
            ("🛁", self._clean, "#00BCD4"),
            ("💬", self._talk, "#FF9800"),
        ]

        for i, (emoji, cmd, color) in enumerate(buttons):
            btn = tk.Button(
                self.btn_frame,
                text=emoji,
                font=("Segoe UI Emoji", 12),
                bg=color,
                fg="white",
                width=3,
                height=1,
                bd=0,
                cursor="hand2",
                command=cmd,
            )
            btn.grid(row=0, column=i, padx=2)

    def _setup_context_menu(self):
        """设置右键菜单"""
        self.context_menu.add_command(label="🍖 喂食", command=self._feed)
        self.context_menu.add_command(label="🎾 玩耍", command=self._play)
        self.context_menu.add_command(label="💤 睡觉", command=self._sleep)
        self.context_menu.add_command(label="🖐️ 抚摸", command=self._pet)
        self.context_menu.add_command(label="🛁 清洁", command=self._clean)
        self.context_menu.add_command(label="💬 聊天", command=self._talk)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="📊 详细状态", command=self._show_status)
        self.context_menu.add_command(label="🔄 切换宠物", command=self._show_pet_selector)
        self.context_menu.add_command(label="➕ 新建宠物", command=self._show_create_dialog)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="❌ 关闭", command=self._on_close)

    def _setup_tray(self):
        """系统托盘支持 - 简化版最小化"""
        self.minimized = False

        # 双击标签最小化
        self.name_label.bind("<Double-Button-1>", lambda e: self._minimize_to_tray())

    def _minimize_to_tray(self):
        """最小化到托盘"""
        self.minimized = True
        self.root.withdraw()

        # 创建托盘窗口
        self.tray_window = tk.Toplevel()
        self.tray_window.overrideredirect(True)
        self.tray_window.attributes("-topmost", True)
        self.tray_window.configure(bg="#333333")

        # 托盘标签
        tray_label = tk.Label(
            self.tray_window,
            text=f"{PET_TYPES[self.active_pet.pet_type]['emoji']} {self.active_pet.name}",
            font=("Microsoft YaHei UI", 10),
            bg="#333333",
            fg="white",
            padx=10,
            pady=5,
            cursor="hand2",
        )
        tray_label.pack()

        # 托盘右键菜单
        tray_menu = tk.Menu(self.tray_window, tearoff=0, bg="#2d2d2d", fg="white")
        tray_menu.add_command(label="📦 恢复窗口", command=self._restore_from_tray)
        tray_menu.add_command(label="❌ 退出", command=self._on_close)

        tray_label.bind("<Button-3>", lambda e: tray_menu.post(e.x_root, e.y_root))
        tray_label.bind("<Double-Button-1>", lambda e: self._restore_from_tray())

        # 定位到右下角
        self.tray_window.update_idletasks()
        x = self.tray_window.winfo_screenwidth() - self.tray_window.winfo_reqwidth() - 20
        y = self.tray_window.winfo_screenheight() - self.tray_window.winfo_reqheight() - 60
        self.tray_window.geometry(f"+{x}+{y}")

    def _restore_from_tray(self):
        """从托盘恢复"""
        if hasattr(self, "tray_window"):
            self.tray_window.destroy()
        self.minimized = False
        self.root.deiconify()
        self.root.lift()

    def _on_drag_start(self, event):
        """开始拖拽"""
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y

    def _on_drag_motion(self, event):
        """拖拽移动"""
        delta_x = event.x - self.drag_data["x"]
        delta_y = event.y - self.drag_data["y"]
        x = self.root.winfo_x() + delta_x
        y = self.root.winfo_y() + delta_y
        self.root.geometry(f"+{x}+{y}")

    def _show_context_menu(self, event):
        """显示右键菜单"""
        if self.active_pet:
            self.context_menu.post(event.x_root, event.y_root)

    def _float_animation(self):
        """浮动动画线程"""
        while self.animating:
            if self.active_pet and not self.minimized:
                try:
                    self.root.after(50, self._update_float_position)
                except Exception:
                    pass
            time.sleep(0.05)

    def _update_float_position(self):
        """更新浮动位置"""
        self.float_offset += 0.3 * self.float_direction
        if abs(self.float_offset) > 5:
            self.float_direction *= -1

        x = self.root.winfo_x()
        y = self.root.winfo_y() + int(self.float_offset)
        self.root.geometry(f"+{x}+{y}")

    def _status_decay(self):
        """状态衰减线程"""
        while self.animating:
            time.sleep(60)  # 每分钟检查一次
            if self.active_pet:
                self.active_pet.update_by_time()
                save_pets(self.pets)
                self.root.after(0, self._update_ui)

    def _update_ui(self):
        """更新UI显示"""
        if not self.active_pet:
            return

        pet_info = PET_TYPES[self.active_pet.pet_type]
        self.pet_label.config(text=pet_info["emoji"])
        self.name_label.config(text=f"{self.active_pet.name}")

        # 更新状态条
        self._update_bar_width(self.hunger_bar, self.active_pet.hunger)
        self._update_bar_width(self.happiness_bar, self.active_pet.happiness)
        self._update_bar_width(self.energy_bar, self.active_pet.energy)
        self._update_bar_width(self.health_bar, self.active_pet.health)

        # 更新状态提示
        status = self.active_pet.get_status()
        self.status_label.config(text=" | ".join(status))

        # 死亡检测
        if not self.active_pet.is_alive:
            self._show_death_message()

    def _update_bar_width(self, bar, value: float):
        """更新状态条宽度"""
        bar.config(width=max(0, int(value * 0.5)))

    def _show_death_message(self):
        """显示死亡消息"""
        dialog = tk.Toplevel(self.root)
        dialog.title("💔")
        dialog.geometry("250x120")
        dialog.attributes("-topmost", True)
        dialog.grab_set()

        tk.Label(
            dialog,
            text=f"{self.active_pet.name} 离开了你...",
            font=("Microsoft YaHei UI", 12),
            pady=10,
        ).pack()
        tk.Label(
            dialog,
            text="它陪伴了你 {:.1f} 天".format(self.active_pet.age),
            font=("Microsoft YaHei UI", 10),
            fg="#888888",
        ).pack()

        def close_and_remove():
            del self.pets[self.active_pet.name]
            save_pets(self.pets)
            dialog.destroy()
            if self.pets:
                self._show_pet_selector()
            else:
                self._show_create_dialog()

        tk.Button(dialog, text="确定", command=close_and_remove, width=10).pack(pady=10)

    # ==================== 交互动作 ====================

    def _feed(self):
        if not self.active_pet:
            return
        msg = self.active_pet.feed()
        self._show_action_feedback(msg)

    def _play(self):
        if not self.active_pet:
            return
        msg = self.active_pet.play()
        self._show_action_feedback(msg)

    def _sleep(self):
        if not self.active_pet:
            return
        msg = self.active_pet.sleep()
        self._show_action_feedback(msg)

    def _pet(self):
        if not self.active_pet:
            return
        msg = self.active_pet.pet_action()
        self._show_action_feedback(msg)

    def _clean(self):
        if not self.active_pet:
            return
        msg = self.active_pet.clean()
        self._show_action_feedback(msg)

    def _talk(self):
        if not self.active_pet:
            return
        msg = self.active_pet.talk()
        self._show_action_feedback(msg)

    def _show_action_feedback(self, message: str):
        """显示动作反馈"""
        self.root.after(0, lambda: self.status_label.config(text=message))
        self.root.after(0, self._update_ui)
        save_pets(self.pets)

    def _show_status(self):
        """显示详细状态"""
        if not self.active_pet:
            return

        pet = self.active_pet
        info = PET_TYPES[pet.pet_type]

        dialog = tk.Toplevel(self.root)
        dialog.title("📊 宠物状态")
        dialog.geometry("280x220")
        dialog.attributes("-topmost", True)
        dialog.grab_set()

        tk.Label(dialog, text=f"{info['emoji']} {pet.name}", font=("Microsoft YaHei UI", 14, "bold")).pack(pady=5)
        tk.Label(dialog, text=f"类型: {info['name']}", font=("Microsoft YaHei UI", 10), fg="#888888").pack()

        status_text = f"""
🍖 饱食度: {pet.hunger:.0f}/100
😊 心情值: {pet.happiness:.0f}/100
⚡ 精力值: {pet.energy:.0f}/100
❤️ 健康值: {pet.health:.0f}/100

📅 年龄: {pet.age:.2f} 天
        """

        tk.Label(dialog, text=status_text, font=("Consolas", 10), justify="left").pack(pady=10)
        tk.Button(dialog, text="关闭", command=dialog.destroy, width=10).pack(pady=5)

    def _show_pet_selector(self):
        """显示宠物选择对话框"""
        if not self.pets:
            self._show_create_dialog()
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("选择宠物")
        dialog.geometry("250x200")
        dialog.attributes("-topmost", True)
        dialog.grab_set()

        tk.Label(dialog, text="选择要互动的宠物:", font=("Microsoft YaHei UI", 11)).pack(pady=10)

        for name, pet in self.pets.items():
            if pet.is_alive:
                info = PET_TYPES[pet.pet_type]
                btn = tk.Button(
                    dialog,
                    text=f"{info['emoji']} {name}",
                    font=("Microsoft YaHei UI", 11),
                    command=lambda p=pet: self._select_pet(p, dialog),
                    width=20,
                )
                btn.pack(pady=3)

        tk.Button(dialog, text="取消", command=dialog.destroy, width=10).pack(pady=10)

    def _select_pet(self, pet: Pet, dialog):
        """选择宠物"""
        self.active_pet = pet
        self._update_ui()
        dialog.destroy()

    def _show_create_dialog(self):
        """显示创建宠物对话框"""
        dialog = tk.Toplevel(self.root)
        dialog.title("创建宠物")
        dialog.geometry("300x350")
        dialog.attributes("-topmost", True)
        dialog.grab_set()

        tk.Label(dialog, text="🐾 选择你的宠物", font=("Microsoft YaHei UI", 14, "bold")).pack(pady=10)

        selected_type = {"value": "1"}

        for key, info in PET_TYPES.items():
            btn = tk.Button(
                dialog,
                text=f"{info['emoji']} {info['name']}\n{info['desc']}",
                font=("Microsoft YaHei UI", 10),
                command=lambda k=key: selected_type.update({"value": k}) or self._preview_pet(k),
                width=25,
                height=2,
            )
            btn.pack(pady=3)

        # 名字输入
        tk.Label(dialog, text="给宠物起个名字:", font=("Microsoft YaHei UI", 10)).pack(pady=(15, 5))
        name_entry = tk.Entry(dialog, font=("Microsoft YaHei UI", 12), width=20, justify="center")
        name_entry.pack(pady=5)

        def create_and_close():
            name = name_entry.get().strip()
            if not name:
                tk.messagebox.showwarning("提示", "请输入宠物名字")
                return

            pet = Pet(selected_type["value"], name)
            self.pets[name] = pet
            save_pets(self.pets)
            self.active_pet = pet
            self._update_ui()
            dialog.destroy()

        tk.Button(dialog, text="创建", command=create_and_close, width=10, bg="#4CAF50", fg="white").pack(pady=15)

    def _preview_pet(self, pet_type: str):
        """预览宠物"""
        info = PET_TYPES[pet_type]
        self.pet_label.config(text=info["emoji"])

    def _on_close(self):
        """关闭窗口"""
        self.animating = False
        if self.active_pet:
            self.active_pet.update_by_time()
        save_pets(self.pets)
        self.root.destroy()
        sys.exit()


def main():
    try:
        FloatingPet()
    except Exception as e:
        print(f"启动失败: {e}")
        import traceback
        traceback.print_exc()
        input("按回车退出...")


if __name__ == "__main__":
    main()
