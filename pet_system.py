import json
import os
import time
import random
from datetime import datetime

SAVE_FILE = "pets.json"

PET_TYPES = {
    "1": {"name": "猫咪", "emoji": "🐱", "desc": "傲娇又粘人的小可爱"},
    "2": {"name": "狗狗", "emoji": "🐶", "desc": "忠诚热情的伙伴"},
    "3": {"name": "兔子", "emoji": "🐰", "desc": "温顺害羞的小家伙"},
    "4": {"name": "龙", "emoji": "🐉", "desc": "神秘强大的存在"},
    "5": {"name": "狐狸", "emoji": "🦊", "desc": "聪明狡黠的精灵"},
}

class Pet:
    def __init__(self, pet_type, name):
        self.pet_type = pet_type
        self.name = name
        self.hunger = 50      # 饥饿度 (0-100, 越高越饱)
        self.happiness = 50   # 心情 (0-100)
        self.energy = 50      # 精力 (0-100)
        self.health = 100     # 健康 (0-100)
        self.age = 0          # 年龄（天数）
        self.created_at = datetime.now().isoformat()
        self.last_interaction = time.time()
        self.status_effects = []

    def feed(self):
        if self.hunger >= 90:
            return f"{self.name} 已经吃得很饱了，不想再吃啦！"
        self.hunger = min(100, self.hunger + 30)
        self.health = min(100, self.health + 5)
        reactions = [
            f"{self.name} 开心地吃着食物，发出满足的叫声~",
            f"{self.name} 狼吞虎咽，看来饿坏了！",
            f"{self.name} 优雅地品尝着美食，尾巴摇来摇去。"
        ]
        return random.choice(reactions)

    def play(self):
        if self.energy < 20:
            return f"{self.name} 太累了，需要先休息..."
        self.happiness = min(100, self.happiness + 25)
        self.energy = max(0, self.energy - 20)
        self.hunger = max(0, self.hunger - 10)
        reactions = [
            f"{self.name} 兴奋地跑来跑去，玩得不亦乐乎！",
            f"你和 {self.name} 一起玩游戏，它开心极了！",
            f"{self.name} 表演了一个后空翻，太厉害了！"
        ]
        return random.choice(reactions)

    def sleep(self):
        self.energy = min(100, self.energy + 40)
        self.health = min(100, self.health + 10)
        self.hunger = max(0, self.hunger - 5)
        reactions = [
            f"{self.name} 蜷缩成一团，安静地睡着了... 💤",
            f"{self.name} 打着小呼噜，进入了甜蜜的梦乡。",
            f"{self.name} 在睡梦中还摇着尾巴，一定在做美梦！"
        ]
        return random.choice(reactions)

    def pet(self):
        self.happiness = min(100, self.happiness + 15)
        self.energy = max(0, self.energy - 5)
        reactions = [
            f"{self.name} 舒服地眯起眼睛，发出咕噜咕噜的声音~",
            f"{self.name} 用头蹭了蹭你的手，好可爱！",
            f"{self.name} 翻了个身，示意你继续摸~"
        ]
        return random.choice(reactions)

    def clean(self):
        self.health = min(100, self.health + 15)
        self.happiness = min(100, self.happiness + 10)
        reactions = [
            f"{self.name} 洗了个香喷喷的澡，毛发闪闪发亮！",
            f"{self.name} 虽然不太情愿，但洗完后感觉清爽多了。",
            f"{self.name} 在泡泡里玩耍，洗澡变成了游戏！"
        ]
        return random.choice(reactions)

    def talk(self):
        self.happiness = min(100, self.happiness + 10)
        phrases = [
            f"{self.name} 用亮晶晶的眼睛看着你，好像在说'我爱你'~",
            f"{self.name} 叽叽喳喳地叫着，似乎在分享今天的见闻。",
            f"{self.name} 歪着头，一脸好奇地看着你。",
            f"{self.name} 发出撒娇的声音，想要更多关注~",
            f"{self.name} 突然跳了起来，好像发现了什么有趣的东西！"
        ]
        return random.choice(phrases)

    def check_status(self):
        # 根据时间流逝更新状态
        now = time.time()
        elapsed = now - self.last_interaction
        hours_passed = elapsed / 3600
        
        if hours_passed > 0:
            self.hunger = max(0, self.hunger - hours_passed * 5)
            self.energy = min(100, self.energy + hours_passed * 2)
            self.happiness = max(0, self.happiness - hours_passed * 3)
            self.health = max(0, self.health - hours_passed * 2)
            self.age += hours_passed / 24
        
        self.last_interaction = now
        
        # 状态效果
        status = []
        if self.hunger < 20:
            status.append("🍽️ 饿扁了")
        elif self.hunger < 50:
            status.append("🍽️ 有点饿")
            
        if self.happiness < 20:
            status.append("😢 很伤心")
        elif self.happiness < 50:
            status.append("😐 闷闷不乐")
            
        if self.energy < 20:
            status.append("😴 精疲力尽")
        elif self.energy < 50:
            status.append("😪 有点困")
            
        if self.health < 30:
            status.append("🏥 生病了")
        elif self.health < 60:
            status.append("🤧 不太舒服")
            
        if not status:
            status.append("✨ 状态很棒")
            
        return status

    def to_dict(self):
        return {
            "pet_type": self.pet_type,
            "name": self.name,
            "hunger": self.hunger,
            "happiness": self.happiness,
            "energy": self.energy,
            "health": self.health,
            "age": self.age,
            "created_at": self.created_at,
            "last_interaction": self.last_interaction,
        }

    @classmethod
    def from_dict(cls, data):
        pet = cls(data["pet_type"], data["name"])
        pet.hunger = data["hunger"]
        pet.happiness = data["happiness"]
        pet.energy = data["energy"]
        pet.health = data["health"]
        pet.age = data["age"]
        pet.created_at = data["created_at"]
        pet.last_interaction = data["last_interaction"]
        return pet


def load_pets():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return {name: Pet.from_dict(p) for name, p in data.items()}
    return {}


def save_pets(pets):
    data = {name: p.to_dict() for name, p in pets.items()}
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def print_header(title):
    print("\n" + "=" * 50)
    print(f"  {title}")
    print("=" * 50)


def print_pet_ascii(pet_type):
    arts = {
        "1": """
    /\_/\
   ( o.o )
    > ^ <
   /|   |\\
  (_|   |_)
        """,
        "2": """
     / \__
    (    @\___
    /         O
   /   (_____/
  /_____/   U
        """,
        "3": """
     (\_/)
    ( •.• )
    / >❤️< \\
        """,
        "4": """
       /\___/\
      /  o o  \\
     ( ==  ^  == )
      )         (
     (           )
    ( (  )   (  ) )
   (__(__)___(__)__)
        """,
        "5": """
    /\   /\
   /  \ /  \
  (  o   o  )
   \   Y   /
    \  |  /
     | | |
     (_|_)
        """,
    }
    print(arts.get(pet_type, arts["1"]))


def create_pet(pets):
    print_header("🌟 选择你的宠物")
    for key, info in PET_TYPES.items():
        print(f"  {key}. {info['emoji']} {info['name']} - {info['desc']}")
    
    choice = input("\n请输入数字选择宠物: ").strip()
    while choice not in PET_TYPES:
        choice = input("无效选择，请重新输入: ").strip()
    
    pet_info = PET_TYPES[choice]
    print_pet_ascii(choice)
    
    name = input(f"\n给你的 {pet_info['emoji']} {pet_info['name']} 起个名字: ").strip()
    while not name:
        name = input("名字不能为空，请重新输入: ").strip()
    
    if name in pets:
        print(f"\n⚠️ 已经有一个叫 '{name}' 的宠物了！")
        confirm = input("是否覆盖? (y/n): ").strip().lower()
        if confirm != 'y':
            return None
    
    pet = Pet(choice, name)
    pets[name] = pet
    save_pets(pets)
    
    print(f"\n🎉 恭喜！{pet_info['emoji']} {name} 成为了你的伙伴！")
    print(f"   {pet_info['desc']}")
    return pet


def interact_with_pet(pet, pets):
    while True:
        status = pet.check_status()
        pet_info = PET_TYPES[pet.pet_type]
        
        print_header(f"{pet_info['emoji']} {pet.name} 的互动菜单")
        print_pet_ascii(pet.pet_type)
        print(f"\n  年龄: {pet.age:.1f} 天")
        print(f"  饱食度: {'█' * int(pet.hunger/10)}{'░' * (10-int(pet.hunger/10))} {pet.hunger:.0f}/100")
        print(f"  心情值: {'█' * int(pet.happiness/10)}{'░' * (10-int(pet.happiness/10))} {pet.happiness:.0f}/100")
        print(f"  精力值: {'█' * int(pet.energy/10)}{'░' * (10-int(pet.energy/10))} {pet.energy:.0f}/100")
        print(f"  健康值: {'█' * int(pet.health/10)}{'░' * (10-int(pet.health/10))} {pet.health:.0f}/100")
        print(f"  状态: {', '.join(status)}")
        
        print("\n  1. 🍖 喂食")
        print("  2. 🎾 玩耍")
        print("  3. 💤 睡觉")
        print("  4. 🖐️ 抚摸")
        print("  5. 🛁 清洁")
        print("  6. 💬 聊天")
        print("  7. 📊 查看详细状态")
        print("  0. 🔙 返回主菜单")
        
        choice = input("\n请选择操作: ").strip()
        
        if choice == "1":
            print(f"\n🍖 {pet.feed()}")
        elif choice == "2":
            print(f"\n🎾 {pet.play()}")
        elif choice == "3":
            print(f"\n💤 {pet.sleep()}")
        elif choice == "4":
            print(f"\n🖐️ {pet.pet()}")
        elif choice == "5":
            print(f"\n🛁 {pet.clean()}")
        elif choice == "6":
            print(f"\n💬 {pet.talk()}")
        elif choice == "7":
            print(f"\n📊 {pet.name} 的详细报告:")
            print(f"   类型: {pet_info['name']} {pet_info['emoji']}")
            print(f"   创建时间: {pet.created_at}")
            print(f"   存活天数: {pet.age:.2f} 天")
            print(f"   累计互动: {int((time.time() - pet.last_interaction) / 60)} 分钟前")
        elif choice == "0":
            save_pets(pets)
            print(f"\n💾 已保存 {pet.name} 的状态！")
            break
        else:
            print("\n⚠️ 无效选择")
        
        # 检查宠物是否死亡
        if pet.health <= 0:
            print(f"\n💔 {pet.name} 因为健康恶化离开了你...")
            del pets[pet.name]
            save_pets(pets)
            input("按回车继续...")
            break
        
        save_pets(pets)
        input("\n按回车继续...")


def main():
    pets = load_pets()
    
    print_header("🎮 电子宠物系统 v1.0")
    print("""
    欢迎来到电子宠物世界！
    你可以选择并养育一只可爱的虚拟宠物，
    给它起名、喂食、玩耍、陪伴它成长...
    """)
    
    while True:
        print_header("🏠 主菜单")
        print(f"  当前拥有宠物: {len(pets)} 只")
        if pets:
            print("  " + ", ".join([f"{PET_TYPES[p.pet_type]['emoji']} {name}" for name, p in pets.items()]))
        
        print("\n  1. ➕ 新建宠物")
        print("  2. 🎮 与宠物互动")
        print("  3. 🗑️ 放生宠物")
        print("  0. 🚪 退出")
        
        choice = input("\n请选择: ").strip()
        
        if choice == "1":
            create_pet(pets)
            input("\n按回车继续...")
            
        elif choice == "2":
            if not pets:
                print("\n⚠️ 你还没有宠物，先创建一个吧！")
                input("按回车继续...")
                continue
            
            print_header("🎮 选择要互动的宠物")
            pet_list = list(pets.items())
            for i, (name, pet) in enumerate(pet_list, 1):
                info = PET_TYPES[pet.pet_type]
                print(f"  {i}. {info['emoji']} {name} ({info['name']})")
            
            try:
                idx = int(input("\n请输入编号: ").strip()) - 1
                if 0 <= idx < len(pet_list):
                    interact_with_pet(pet_list[idx][1], pets)
                else:
                    print("\n⚠️ 无效编号")
                    input("按回车继续...")
            except ValueError:
                print("\n⚠️ 请输入数字")
                input("按回车继续...")
                
        elif choice == "3":
            if not pets:
                print("\n⚠️ 没有宠物可以放生")
                input("按回车继续...")
                continue
            
            print_header("🗑️ 选择要放生的宠物")
            pet_list = list(pets.items())
            for i, (name, pet) in enumerate(pet_list, 1):
                info = PET_TYPES[pet.pet_type]
                print(f"  {i}. {info['emoji']} {name}")
            
            try:
                idx = int(input("\n请输入编号 (0取消): ").strip()) - 1
                if idx == -1:
                    continue
                if 0 <= idx < len(pet_list):
                    name = pet_list[idx][0]
                    confirm = input(f"\n确定要放生 {name} 吗? (y/n): ").strip().lower()
                    if confirm == 'y':
                        del pets[name]
                        save_pets(pets)
                        print(f"\n😢 {name} 含着泪离开了...")
                    else:
                        print("\n✨ 太好了，继续陪伴它吧！")
                else:
                    print("\n⚠️ 无效编号")
            except ValueError:
                print("\n⚠️ 请输入数字")
            input("按回车继续...")
            
        elif choice == "0":
            save_pets(pets)
            print_header("👋 再见")
            print("感谢使用电子宠物系统！你的宠物会想念你的~")
            break
        else:
            print("\n⚠️ 无效选择")
            input("按回车继续...")


if __name__ == "__main__":
    main()
