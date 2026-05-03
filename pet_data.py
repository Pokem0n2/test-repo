"""
宠物数据层 - 负责宠物数据的序列化和持久化
"""
import json
import os
import time
from datetime import datetime
from pathlib import Path

SAVE_FILE = Path(__file__).parent / "pets_data.json"

PET_TYPES = {
    "1": {"name": "猫咪", "emoji": "🐱", "desc": "傲娇又粘人的小可爱"},
    "2": {"name": "狗狗", "emoji": "🐶", "desc": "忠诚热情的伙伴"},
    "3": {"name": "兔子", "emoji": "🐰", "desc": "温顺害羞的小家伙"},
    "4": {"name": "龙", "emoji": "🐉", "desc": "神秘强大的存在"},
    "5": {"name": "狐狸", "emoji": "🦊", "desc": "聪明狡黠的精灵"},
}


class Pet:
    """宠物核心类"""

    def __init__(self, pet_type: str, name: str):
        self.pet_type = pet_type
        self.name = name
        self.hunger = 50
        self.happiness = 50
        self.energy = 50
        self.health = 100
        self.age = 0.0
        self.created_at = datetime.now().isoformat()
        self.last_interaction = time.time()
        self.is_alive = True

    def feed(self) -> str:
        if self.hunger >= 90:
            return f"{self.name} 已经吃得很饱了，不想再吃啦！"
        self.hunger = min(100, self.hunger + 30)
        self.health = min(100, self.health + 5)
        reactions = [
            f"{self.name} 开心地吃着食物，发出满足的叫声~",
            f"{self.name} 狼吞虎咽，看来饿坏了！",
            f"{self.name} 优雅地品尝着美食，尾巴摇来摇去。",
        ]
        return _random_choice(reactions)

    def play(self) -> str:
        if self.energy < 20:
            return f"{self.name} 太累了，需要先休息..."
        self.happiness = min(100, self.happiness + 25)
        self.energy = max(0, self.energy - 20)
        self.hunger = max(0, self.hunger - 10)
        reactions = [
            f"{self.name} 兴奋地跑来跑去，玩得不亦乐乎！",
            f"你和 {self.name} 一起玩游戏，它开心极了！",
            f"{self.name} 表演了一个后空翻，太厉害了！",
        ]
        return _random_choice(reactions)

    def sleep(self) -> str:
        self.energy = min(100, self.energy + 40)
        self.health = min(100, self.health + 10)
        self.hunger = max(0, self.hunger - 5)
        reactions = [
            f"{self.name} 蜷缩成一团，安静地睡着了... 💤",
            f"{self.name} 打着小呼噜，进入了甜蜜的梦乡。",
            f"{self.name} 在睡梦中还摇着尾巴，一定在做美梦！",
        ]
        return _random_choice(reactions)

    def pet_action(self) -> str:
        self.happiness = min(100, self.happiness + 15)
        self.energy = max(0, self.energy - 5)
        reactions = [
            f"{self.name} 舒服地眯起眼睛，发出咕噜咕噜的声音~",
            f"{self.name} 用头蹭了蹭你的手，好可爱！",
            f"{self.name} 翻了个身，示意你继续摸~",
        ]
        return _random_choice(reactions)

    def clean(self) -> str:
        self.health = min(100, self.health + 15)
        self.happiness = min(100, self.happiness + 10)
        reactions = [
            f"{self.name} 洗了个香喷喷的澡，毛发闪闪发亮！",
            f"{self.name} 虽然不太情愿，但洗完后感觉清爽多了。",
            f"{self.name} 在泡泡里玩耍，洗澡变成了游戏！",
        ]
        return _random_choice(reactions)

    def talk(self) -> str:
        self.happiness = min(100, self.happiness + 10)
        phrases = [
            f"{self.name} 用亮晶晶的眼睛看着你，好像在说'我爱你'~",
            f"{self.name} 叽叽喳喳地叫着，似乎在分享今天的见闻。",
            f"{self.name} 歪着头，一脸好奇地看着你。",
            f"{self.name} 发出撒娇的声音，想要更多关注~",
            f"{self.name} 突然跳了起来，好像发现了什么有趣的东西！",
        ]
        return _random_choice(phrases)

    def update_by_time(self) -> None:
        """根据时间流逝更新状态"""
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

        # 健康检测
        if self.health <= 0:
            self.is_alive = False

    def get_status(self) -> list:
        self.update_by_time()
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

    def to_dict(self) -> dict:
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
            "is_alive": self.is_alive,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Pet":
        pet = cls(data["pet_type"], data["name"])
        pet.hunger = data["hunger"]
        pet.happiness = data["happiness"]
        pet.energy = data["energy"]
        pet.health = data["health"]
        pet.age = data["age"]
        pet.created_at = data["created_at"]
        pet.last_interaction = data["last_interaction"]
        pet.is_alive = data.get("is_alive", True)
        return pet


def _random_choice(lst: list) -> str:
    import random
    return random.choice(lst)


def load_pets() -> dict:
    if SAVE_FILE.exists():
        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {name: Pet.from_dict(p) for name, p in data.items()}
        except (json.JSONDecodeError, KeyError):
            return {}
    return {}


def save_pets(pets: dict) -> None:
    data = {name: p.to_dict() for name, p in pets.items()}
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
