"""
终端电子宠物 - ASCII 彩色动画版本
支持键盘快捷键互动
"""
import os
import sys
import time
import random
import threading
import shutil
from pathlib import Path

# 设置 UTF-8 输出
if sys.platform == "win32":
    os.system("chcp 65001 > nul 2>&1")

try:
    from pet_data import Pet, PET_TYPES, load_pets, save_pets
except ImportError:
    from .pet_data import Pet, PET_TYPES, load_pets, save_pets

# ANSI 颜色码
class Colors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"

    # 状态条颜色
    HUNGER = OKGREEN
    HAPPINESS = WARNING
    ENERGY = OKBLUE
    HEALTH = FAIL


def clear_screen():
    """清屏"""
    os.system("cls" if os.name == "nt" else "clear")


def print_centered(text: str, width: int = 60):
    """居中打印"""
    print(text.center(width))


def print_bar(value: float, max_val: float = 100, width: int = 20, color: str = "") -> str:
    """生成状态条"""
    filled = int((value / max_val) * width)
    bar = "█" * filled + "░" * (width - filled)
    return f"{color}{bar}{Colors.ENDC}"


class ASCIIPet:
    """ASCII 宠物渲染器"""

    @staticmethod
    def get_art(pet_type: str, mood: str = "normal") -> str:
        """获取宠物 ASCII 艺术"""
        arts = {
            "1": {  # 猫
                "happy": r"""
    /\_____/\
   /  o   o  \
  ( ==  ^  == )
   )         (
  (           )
 ( (  )   (  ) )
(__(__)___(__)__)
                """,
                "normal": r"""
    /\_____/\
   /  o . o  \
  ( ==  ^  == )
   )         (
  (    ___    )
 ( ( )____( ) )
(__(__)___(__)__)
                """,
                "sad": r"""
    /\_____/\
   /  x   x  \
  ( ==  ^  == )
   )         (
  (  ___  )
 ( (_____ ) )
(__(___)___(__)__)
                """,
            },
            "2": {  # 狗
                "happy": r"""
      /\____/\
     /  o  o  \
    ( ==  ^  == )
     \  ----  /
    __)____(__
   /  o    o  \
  /   (____)   \
 (    (    )    )
( ( ) )    ( ( ) )
                """,
                "normal": r"""
      /\____/\
     /  o  .  \
    ( ==  ^  == )
     \  ----  /
    __)____(__
   /  o    o  \
  /   (____)   \
                """,
                "sad": r"""
      /\____/\
     /  x  x  \
    ( ==  ^  == )
     \  ----  /
    __)____(__
   /  o    o  \
                """,
            },
            "3": {  # 兔子
                "happy": r"""
    (\(\\
    ( -.-)
    o_(")(")
                """,
                "normal": r"""
    (\(\\
    ( . .)
    o_(")(")
                """,
                "sad": r"""
    (\(\\
    ( x x)
    o_(")(")
                """,
            },
            "4": {  # 龙
                "happy": r"""
       /\___/\
      /  o o  \
     ( ==  ^  == )
      )       (
     (    ___    )
    ( ( )  |  ( ) )
   (__(__) | (__)__)
                """,
                "normal": r"""
       /\___/\
      /  o .  \
     ( ==  ^  == )
      )       (
     (    ___    )
                """,
                "sad": r"""
       /\___/\
      /  x x  \
     ( ==  ^  == )
      )       (
                """,
            },
            "5": {  # 狐狸
                "happy": r"""
    /\   /\
   /  \_/  \
  (  o   o  )
   \   Y   /
    \  |  /
     |_|_|
    (_| |_)
                """,
                "normal": r"""
    /\   /\
   /  \_/  \
  (  o   .  )
   \   Y   /
    \  |  /
                """,
                "sad": r"""
    /\   /\
   /  \_/  \
  (  x   x  )
   \   Y   /
                """,
            },
        }

        mood_arts = arts.get(pet_type, arts["1"])
        return mood_arts.get(mood, mood_arts["normal"])

    @staticmethod
    def get_mood(pet: Pet) -> str:
        """根据宠物状态获取心情"""
        if pet.happiness < 20 or pet.health < 30:
            return "sad"
        elif pet.happiness > 70 and pet.health > 60:
            return "happy"
        return "normal"


class TerminalPet:
    """终端宠物主类"""

    def __init__(self):
        self.pets = load_pets()
        self.active_pet = None
        self.running = True
        self.animation_frame = 0
        self.message = ""
        self.message_time = 0

        # 终端尺寸
        self.width = shutil.get_terminal_size().columns or 80
        self.height = shutil.get_terminal_size().lines or 24

        # 选择或创建宠物
        if self.pets:
            # 找到活着的宠物
            alive_pets = {k: v for k, v in self.pets.items() if v.is_alive}
            if alive_pets:
                self.active_pet = list(alive_pets.values())[0]
            else:
                self._show_create_screen()
        else:
            self._show_create_screen()

        # 启动动画线程
        self.animating = True
        self.anim_thread = threading.Thread(target=self._animation_loop, daemon=True)
        self.anim_thread.start()

        # 状态衰减线程
        self.decay_thread = threading.Thread(target=self._decay_loop, daemon=True)
        self.decay_thread.start()

    def _animation_loop(self):
        """动画循环"""
        while self.animating:
            self.animation_frame = (self.animation_frame + 1) % 4
            time.sleep(0.3)

    def _decay_loop(self):
        """状态衰减循环"""
        while self.animating:
            time.sleep(60)
            if self.active_pet:
                self.active_pet.update_by_time()
                save_pets(self.pets)

    def _show_create_screen(self):
        """显示创建宠物界面"""
        clear_screen()

        print()
        print_centered(f"{Colors.HEADER}{Colors.BOLD}🎮 电子宠物系统 v1.0{Colors.ENDC}")
        print_centered(f"{Colors.DIM}=" * 50)
        print()
        print_centered(f"{Colors.OKCYAN}🌟 选择你的宠物{Colors.ENDC}")
        print()

        for key, info in PET_TYPES.items():
            print_centered(f"  {key}. {info['emoji']} {info['name']} - {info['desc']}")

        print()
        print_centered(f"{Colors.DIM}输入数字选择宠物，或输入 q 退出{Colors.ENDC}")

        choice = input(f"\n{Colors.WARNING}> {Colors.ENDC}").strip()

        if choice.lower() == "q":
            self.running = False
            return

        if choice not in PET_TYPES:
            input(f"\n{Colors.FAIL}无效选择，按回车重试...{Colors.ENDC}")
            self._show_create_screen()
            return

        pet_info = PET_TYPES[choice]
        print(f"\n{Colors.OKGREEN}")
        print_centered(ASCIIPet.get_art(choice, "happy"))
        print(f"{Colors.ENDC}")

        name = input(f"\n{Colors.WARNING}给你的 {pet_info['emoji']} {pet_info['name']} 起个名字: {Colors.ENDC}").strip()

        if not name:
            input(f"\n{Colors.FAIL}名字不能为空，按回车重试...{Colors.ENDC}")
            self._show_create_screen()
            return

        # 检查重名
        if name in self.pets:
            confirm = input(f"\n{Colors.WARNING}已经存在叫 '{name}' 的宠物，是否覆盖? (y/n): {Colors.ENDC}").strip().lower()
            if confirm != "y":
                self._show_create_screen()
                return

        pet = Pet(choice, name)
        self.pets[name] = pet
        save_pets(self.pets)
        self.active_pet = pet

        print(f"\n{Colors.OKGREEN}🎉 恭喜！{pet_info['emoji']} {name} 成为了你的伙伴！{Colors.ENDC}")
        time.sleep(1)

    def _show_interaction_menu(self):
        """显示互动菜单"""
        clear_screen()

        if not self.active_pet:
            print(f"{Colors.FAIL}没有活跃的宠物！{Colors.ENDC}")
            return

        pet = self.active_pet
        info = PET_TYPES[pet.pet_type]
        mood = ASCIIPet.get_mood(pet)
        status = pet.get_status()

        # 动画帧
        frames = ["🐾", "🐾 ", " 🐾", " 🐾"]
        paw = frames[self.animation_frame]

        # 打印头部
        print()
        print_centered(f"{Colors.HEADER}{Colors.BOLD}{paw} {info['emoji']} {pet.name} 的互动菜单 {paw}{Colors.ENDC}")
        print_centered(f"{Colors.DIM}{'─' * 50}{Colors.ENDC}")

        # ASCII 艺术
        art = ASCIIPet.get_art(pet.pet_type, mood)
        print(f"{Colors.OKCYAN}{art}{Colors.ENDC}")

        # 状态条
        print(f"{Colors.DIM}{'─' * 50}{Colors.ENDC}")
        print(f"  {Colors.BOLD}📊 基础状态{Colors.ENDC}")
        print(
            f"  🍖 饱食度: {print_bar(pet.hunger, 100, 15, Colors.HUNGER)} {pet.hunger:5.1f}/100"
        )
        print(
            f"  😊 心情值: {print_bar(pet.happiness, 100, 15, Colors.HAPPINESS)} {pet.happiness:5.1f}/100"
        )
        print(
            f"  ⚡ 精力值: {print_bar(pet.energy, 100, 15, Colors.ENERGY)} {pet.energy:5.1f}/100"
        )
        print(
            f"  ❤️ 健康值: {print_bar(pet.health, 100, 15, Colors.HEALTH)} {pet.health:5.1f}/100"
        )
        print(f"  📅 年龄: {pet.age:.2f} 天")
        print()
        print(f"  {Colors.BOLD}当前状态:{Colors.ENDC} {', '.join(status)}")

        # 消息提示
        if self.message and time.time() - self.message_time < 3:
            print(f"\n  {Colors.WARNING}{self.message}{Colors.ENDC}")

        # 操作菜单
        print()
        print_centered(f"{Colors.DIM}{'─' * 50}{Colors.ENDC}")
        print_centered(f"{Colors.BOLD}🎮 互动操作{Colors.ENDC}")
        print()
        print_centered("1. 🍖 喂食    2. 🎾 玩耍    3. 💤 睡觉")
        print_centered("4. 🖐️ 抚摸    5. 🛁 清洁    6. 💬 聊天")
        print_centered("7. 📊 详细    8. 🔄 切换    0. 🚪 退出")
        print()
        print_centered(f"{Colors.DIM}[提示] 直接输入数字选择操作{Colors.ENDC}")

    def _handle_action(self, choice: str):
        """处理动作"""
        if not self.active_pet:
            return

        pet = self.active_pet

        actions = {
            "1": ("🍖 喂食", pet.feed),
            "2": ("🎾 玩耍", pet.play),
            "3": ("💤 睡觉", pet.sleep),
            "4": ("🖐️ 抚摸", pet.pet_action),
            "5": ("🛁 清洁", pet.clean),
            "6": ("💬 聊天", pet.talk),
        }

        if choice in actions:
            label, action_fn = actions[choice]
            result = action_fn()
            self.message = f"{label}: {result}"
            self.message_time = time.time()
            save_pets(self.pets)

            # 检查死亡
            if not pet.is_alive:
                self._show_death_screen()

        elif choice == "7":
            self._show_detailed_status()
        elif choice == "8":
            self._show_switch_pet()
        elif choice == "0":
            self._save_and_exit()

    def _show_death_screen(self):
        """显示死亡画面"""
        clear_screen()
        print()
        print_centered(f"{Colors.FAIL}{Colors.BOLD}💔 宠物离开了{Colors.ENDC}")
        print()
        print_centered(f"{Colors.DIM}你的 {self.active_pet.name} 离开了这个世界...{Colors.ENDC}")
        print_centered(f"{Colors.DIM}它陪伴了你 {self.active_pet.age:.1f} 天{Colors.ENDC}")
        print()
        print_centered(f"{Colors.WARNING}按回车继续...{Colors.ENDC}")

        # 删除死亡的宠物
        del self.pets[self.active_pet.name]
        save_pets(self.pets)

        input()

        # 选择其他宠物或创建新宠物
        alive_pets = {k: v for k, v in self.pets.items() if v.is_alive}
        if alive_pets:
            self.active_pet = list(alive_pets.values())[0]
        else:
            self._show_create_screen()

    def _show_detailed_status(self):
        """显示详细状态"""
        clear_screen()

        pet = self.active_pet
        info = PET_TYPES[pet.pet_type]

        print()
        print_centered(f"{Colors.HEADER}{Colors.BOLD}📊 {pet.name} 的详细报告{Colors.ENDC}")
        print_centered(f"{Colors.DIM}{'─' * 50}{Colors.ENDC}")
        print()
        print(f"  {Colors.BOLD}基本信息:{Colors.ENDC}")
        print(f"  类型: {info['emoji']} {info['name']}")
        print(f"  名字: {pet.name}")
        print(f"  创建时间: {pet.created_at}")
        print(f"  存活天数: {pet.age:.2f} 天")
        print()
        print(f"  {Colors.BOLD}属性状态:{Colors.ENDC}")
        print(f"  🍖 饱食度: {pet.hunger:.1f}/100")
        print(f"  😊 心情值: {pet.happiness:.1f}/100")
        print(f"  ⚡ 精力值: {pet.energy:.1f}/100")
        print(f"  ❤️ 健康值: {pet.health:.1f}/100")
        print()
        print(f"  当前状态: {', '.join(pet.get_status())}")
        print()
        print_centered(f"{Colors.DIM}按回车返回...{Colors.ENDC}")
        input()

    def _show_switch_pet(self):
        """显示切换宠物"""
        clear_screen()

        print()
        print_centered(f"{Colors.HEADER}{Colors.BOLD}🔄 切换宠物{Colors.ENDC}")
        print_centered(f"{Colors.DIM}{'─' * 50}{Colors.ENDC}")
        print()

        alive_pets = {k: v for k, v in self.pets.items() if v.is_alive}

        if not alive_pets:
            print_centered(f"{Colors.WARNING}没有存活的宠物{Colors.ENDC}")
            print_centered(f"{Colors.DIM}按回车创建新宠物...{Colors.ENDC}")
            input()
            self._show_create_screen()
            return

        for i, (name, p) in enumerate(alive_pets.items(), 1):
            info = PET_TYPES[p.pet_type]
            print_centered(f"{i}. {info['emoji']} {name} ({info['name']})")

        print()
        print_centered(f"{Colors.DIM}输入编号切换，输入 q 返回{Colors.ENDC}")

        choice = input(f"\n{Colors.WARNING}> {Colors.ENDC}").strip()

        if choice.lower() == "q":
            return

        try:
            idx = int(choice) - 1
            pet_list = list(alive_pets.values())
            if 0 <= idx < len(pet_list):
                self.active_pet = pet_list[idx]
                self.message = f"切换到 {self.active_pet.name}"
                self.message_time = time.time()
            else:
                self.message = "无效编号"
                self.message_time = time.time()
        except ValueError:
            self.message = "请输入数字"
            self.message_time = time.time()

    def _save_and_exit(self):
        """保存并退出"""
        self.animating = False
        if self.active_pet:
            self.active_pet.update_by_time()
        save_pets(self.pets)
        clear_screen()
        print()
        print_centered(f"{Colors.OKGREEN}👋 再见！{Colors.ENDC}")
        print_centered(f"{Colors.DIM}你的宠物会想念你的~{Colors.ENDC}")
        print()
        self.running = False

    def run(self):
        """运行主循环"""
        # 初始渲染
        self._show_interaction_menu()

        while self.running:
            # 显示界面
            self._show_interaction_menu()

            # 读取输入
            try:
                choice = input(f"\n{Colors.WARNING}> {Colors.ENDC}").strip()
            except (EOFError, KeyboardInterrupt):
                choice = "0"

            self._handle_action(choice)

            # 短暂延迟避免过度刷新
            time.sleep(0.1)


def main():
    """主入口"""
    try:
        terminal_pet = TerminalPet()
        if terminal_pet.running:
            terminal_pet.run()
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}已退出{Colors.ENDC}")
    except Exception as e:
        print(f"{Colors.FAIL}错误: {e}{Colors.ENDC}")
        import traceback

        traceback.print_exc()
        input("按回车退出...")


if __name__ == "__main__":
    main()
