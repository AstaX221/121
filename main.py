#!/usr/bin/env python3
"""
Galaxy Nick Checker v2.1
Поиск свободных однословных ников на galaxy.mobstudio.ru
С отображением даты последнего онлайна
Автоматически создает .env при первом запуске
"""

import hashlib
import random
import requests
import time
import os
import sys
from typing import Dict, List
from pathlib import Path
from dotenv import load_dotenv

# ==================== РАБОТА С .ENV ====================
def get_env_path():
    """Возвращает путь к .env файлу (рядом с EXE или в папке скрипта)"""
    if getattr(sys, 'frozen', False):
        # Запущено как EXE
        base_path = Path(sys.executable).parent
    else:
        # Запущено как скрипт
        base_path = Path(__file__).parent
    return base_path / '.env'

def ensure_env_file():
    """
    Проверяет наличие .env и создает его при отсутствии.
    Возвращает True, если файл существует или был создан.
    """
    env_path = get_env_path()
    
    if env_path.exists():
        return True
    
    # Файла нет — создаем
    print("=" * 60)
    print("🔧 Файл .env не найден. Создаю новый...")
    print("=" * 60)
    
    try:
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write("# Galaxy Nick Checker - Настройки\n")
            f.write("# Получите свой userID через F12 -> Network на сайте galaxy.mobstudio.ru\n")
            f.write("# Или найдите параметр userID в любом запросе\n\n")
            f.write("GALAXY_USER_ID=\n")
            f.write("GALAXY_PASSWORD=\n")
        
        print(f"✅ Файл создан: {env_path}")
        print("\n📝 Теперь откройте этот файл Блокнотом и впишите свои данные:")
        print("   GALAXY_USER_ID=ваш_айди")
        print("   GALAXY_PASSWORD=ваш_пароль")
        print("\n💡 Подсказка:")
        print("   - userID — ваше ID в игре (число)")
        print("   - password — ваш пароль от аккаунта Galaxy")
        print("\n⚠️ ВНИМАНИЕ: Не показывайте этот файл никому!")
        print("=" * 60)
        
        input("Нажмите Enter, когда заполните файл .env...")
        
        # Проверяем, заполнил ли пользователь
        load_dotenv(env_path)
        test_id = os.getenv("GALAXY_USER_ID")
        test_pass = os.getenv("GALAXY_PASSWORD")
        
        if not test_id or not test_pass:
            print("\n❌ Вы не заполнили данные в .env!")
            print("   Откройте файл и впишите:")
            print("   GALAXY_USER_ID=ваш_айди")
            print("   GALAXY_PASSWORD=ваш_пароль")
            input("\nНажмите Enter, чтобы попробовать снова...")
            return ensure_env_file()  # Рекурсивно просим заполнить
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при создании .env: {e}")
        input("\nНажмите Enter для выхода...")
        sys.exit(1)

# ==================== ЧЕКЕР ====================
class GalaxyNickChecker:
    def __init__(self, user_id: int, password: str):
        self.user_id = user_id
        self.password_hash = hashlib.md5(password.encode('utf-8')).hexdigest()
        self.url = "https://galaxy.mobstudio.ru/services/"
        self.headers = {
            "accept": "*/*",
            "content-type": "multipart/form-data; boundary=----WebKitFormBoundary9B72nKAEd6UycZAA",
            "origin": "https://galaxy.mobstudio.ru",
            "referer": "https://galaxy.mobstudio.ru/web/assets/index.html",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "x-galaxy-client-ver": "9.5",
            "x-galaxy-platform": "web"
        }
        self.checked = 0
        self.found = 0
    
    def _build_form_data(self, nick: str, rand: float) -> str:
        return f"""------WebKitFormBoundary9B72nKAEd6UycZAA
Content-Disposition: form-data; name="userID"

{self.user_id}
------WebKitFormBoundary9B72nKAEd6UycZAA
Content-Disposition: form-data; name="password"

{self.password_hash}
------WebKitFormBoundary9B72nKAEd6UycZAA
Content-Disposition: form-data; name="query_rand"

{rand}
------WebKitFormBoundary9B72nKAEd6UycZAA
Content-Disposition: form-data; name="a"

search_ajax
------WebKitFormBoundary9B72nKAEd6UycZAA
Content-Disposition: form-data; name="type"

1
------WebKitFormBoundary9B72nKAEd6UycZAA
Content-Disposition: form-data; name="search_value"

{nick}
------WebKitFormBoundary9B72nKAEd6UycZAA
Content-Disposition: form-data; name="ajax"

1
------WebKitFormBoundary9B72nKAEd6UycZAA--
"""
    
    def check(self, nick: str, delay: float = 0.3) -> Dict:
        time.sleep(delay)
        rand = random.random()
        url = f"{self.url}?&userID={self.user_id}&password={self.password_hash}&query_rand={rand}"
        
        try:
            resp = requests.post(url, headers=self.headers, data=self._build_form_data(nick, rand), timeout=10)
            resp.raise_for_status()
            result = resp.json()
            search_result = result.get("searchResult", {})
            has_match = search_result.get("hasFullMatch", False)
            
            self.checked += 1
            if not has_match:
                self.found += 1
            
            user_info = None
            if has_match:
                initial_match = search_result.get("initialMatchList", [])
                for user in initial_match:
                    user_nick = user.get("userNickData", {}).get("nick", "").lower()
                    if user_nick == nick.lower():
                        user_info = {
                            "user_id": user.get("userId"),
                            "is_online": user.get("isOnline", False),
                            "last_online": user.get("lastOnline", "неизвестно"),
                            "is_male": user.get("isMale", True),
                            "user_pic": user.get("userPic", "")
                        }
                        break
            
            return {
                "nick": nick,
                "available": not has_match,
                "taken": has_match,
                "user_info": user_info
            }
        except Exception as e:
            return {"nick": nick, "available": False, "error": str(e)}

# ==================== ГЕНЕРАТОР ====================
class NickGenerator:
    RUSSIAN = {
        "сила": ["мощь", "энергия", "крепость", "стойкость", "власть", "могущество", "твердыня", "воля", "дух"],
        "огонь": ["пламя", "феникс", "искра", "жар", "вулкан", "костер", "зарево"],
        "вода": ["океан", "волна", "поток", "река", "дождь", "родник", "пучина"],
        "ветер": ["буря", "ураган", "шторм", "порыв", "бриз", "тайфун"],
        "земля": ["камень", "скала", "песок", "гранит", "утёс", "валун"],
        "свет": ["луч", "сияние", "солнце", "звезда", "блик", "созвездие"],
        "тьма": ["мрак", "ночь", "тень", "сумерки", "чернота", "бездна"],
        "воин": ["солдат", "боец", "рыцарь", "гладиатор", "герой", "витязь"],
        "король": ["царь", "император", "властелин", "повелитель", "монарх", "князь"],
        "маг": ["волшебник", "чародей", "колдун", "шаман", "ведун", "кудесник"],
        "дракон": ["рептилия", "ящер", "хищник", "исполин", "грифон"],
        "волк": ["хищник", "зверь", "вожак", "свободный", "серый"],
        "орел": ["сокол", "ястреб", "беркут", "коршун", "орлан"],
        "скорость": ["быстрота", "стремительность", "порыв", "рывок", "мгновение"],
        "тишина": ["покой", "спокойствие", "тишь", "безмолвие", "шёпот"],
        "мудрость": ["знание", "опыт", "разум", "интеллект", "просветление"],
        "смелость": ["храбрость", "отвага", "мужество", "героизм", "дерзость"],
        "свобода": ["вольность", "независимость", "полет", "ветер", "простор"],
        "лес": ["дубрава", "тайга", "чаща", "бор", "роща"],
        "гора": ["вершина", "скала", "пик", "утес", "высь"],
        "радость": ["счастье", "восторг", "улыбка", "смех", "блаженство"],
        "грусть": ["печаль", "тоска", "дождь", "осень", "раздумье"],
        "гнев": ["ярость", "бешенство", "неистовство", "фурия"],
        "эльф": ["сильф", "фея", "дух", "легенда", "призрак"],
        "гном": ["дварф", "кузнец", "шахтер", "рудокоп"],
        "вампир": ["кровь", "граф", "бессмертие", "тень"],
        "оборотень": ["луна", "зверь", "охотник", "сталкер"],
        "меч": ["клинок", "сабля", "рапира", "катана", "палаш"],
        "щит": ["защита", "броня", "крепость", "стена", "доспех"],
        "хаос": ["бездна", "разрушение", "анархия", "неистовство"],
        "истина": ["правда", "честность", "чистота", "откровение"],
        "ангел": ["архангел", "хранитель", "небожитель", "светлый"],
        "демон": ["бес", "сатана", "люцифер", "падший"],
        "алый": ["огненный", "багряный", "червонный"],
        "белый": ["снежный", "серебряный", "сияющий"],
        "черный": ["ночной", "вороной", "темный"],
        "золотой": ["солнечный", "златый", "драгоценный"],
    }
    
    ENGLISH = {
        "power": ["might", "energy", "strength", "force", "vigor", "prowess"],
        "fire": ["flame", "phoenix", "spark", "blaze", "inferno", "ember"],
        "water": ["ocean", "wave", "stream", "river", "rain", "spring"],
        "wind": ["storm", "hurricane", "gale", "breeze", "typhoon"],
        "earth": ["stone", "rock", "clay", "granite", "cliff", "boulder"],
        "light": ["ray", "shine", "sun", "star", "glow", "radiance"],
        "dark": ["shadow", "night", "gloom", "twilight", "void", "abyss"],
        "warrior": ["knight", "fighter", "soldier", "gladiator", "hero", "champion"],
        "king": ["emperor", "ruler", "monarch", "sovereign", "prince", "lord"],
        "mage": ["wizard", "sorcerer", "warlock", "shaman", "enchanter"],
        "dragon": ["wyrm", "reptile", "serpent", "beast", "leviathan"],
        "wolf": ["predator", "hunter", "alpha", "feral", "howler"],
        "eagle": ["falcon", "hawk", "raven", "phoenix", "vulture"],
        "speed": ["velocity", "haste", "swiftness", "rapidity", "dash"],
        "silence": ["peace", "quiet", "stillness", "calm", "serenity"],
        "wisdom": ["knowledge", "insight", "intellect", "enlightenment"],
        "courage": ["bravery", "valor", "heroism", "daring", "audacity"],
        "freedom": ["liberty", "independence", "flight", "spirit"],
        "forest": ["grove", "woods", "jungle", "thicket", "wildwood"],
        "mountain": ["peak", "summit", "cliff", "ridge", "highland"],
        "star": ["moon", "sun", "sky", "cosmos", "galaxy"],
        "joy": ["happiness", "delight", "bliss", "ecstasy", "euphoria"],
        "sorrow": ["grief", "melancholy", "despair", "woe", "anguish"],
        "rage": ["fury", "wrath", "frenzy", "ferocity"],
        "elf": ["fairy", "sprite", "spirit", "phantom", "mirage"],
        "dwarf": ["smith", "miner", "crafter", "artisan", "forger"],
        "vampire": ["blood", "night", "count", "immortal", "shadow"],
        "sword": ["blade", "saber", "rapier", "katana", "claymore"],
        "shield": ["armor", "bulwark", "fortress", "guard", "aegis"],
        "chaos": ["void", "anarchy", "tumult", "pandemonium"],
        "truth": ["honesty", "purity", "clarity", "revelation"],
        "angel": ["archangel", "guardian", "celestial", "divine"],
        "demon": ["fiend", "devil", "satan", "infernal"],
        "storm": ["tempest", "blizzard", "cyclone", "monsoon"],
        "ice": ["frost", "glacier", "crystal", "winter", "polar"],
        "moon": ["lunar", "crescent", "eclipse", "nocturnal"],
        "sun": ["solar", "blaze", "dawn", "sunrise", "solstice"],
    }
    
    def __init__(self, checker):
        self.checker = checker
        self.found = []
        self.taken_with_info = []
    
    def get_words(self, base: str, lang: str = "both") -> List[str]:
        base = base.lower()
        words = []
        if lang in ["russian", "both"]:
            words.extend(self.RUSSIAN.get(base, []))
        if lang in ["english", "both"]:
            words.extend(self.ENGLISH.get(base, []))
        return list(set([base] + words))
    
    def cases(self, word: str) -> List[str]:
        return [word, word.capitalize(), word.upper(), word.lower()]
    
    def search(self, base: str, lang: str = "both", delay: float = 0.3) -> List[str]:
        print(f"🔍 Поиск: '{base}'")
        words = self.get_words(base, lang)
        random.shuffle(words)
        print(f"📝 Вариантов: {len(words)}")
        
        found = []
        self.taken_with_info = []
        
        for word in words[:20]:
            if not (3 <= len(word) <= 15):
                continue
            for nick in set(self.cases(word)):
                result = self.checker.check(nick, delay)
                if result.get("available"):
                    found.append(nick)
                    print(f"✅ {nick} — СВОБОДЕН!")
                else:
                    user_info = result.get("user_info")
                    if user_info:
                        status = "🟢 Онлайн" if user_info.get("is_online") else "🔴 Офлайн"
                        last_online = user_info.get("last_online", "неизвестно")
                        gender = "♂️" if user_info.get("is_male") else "♀️"
                        print(f"❌ {nick} — ЗАНЯТ {gender} {status}, последний раз: {last_online}")
                        self.taken_with_info.append({
                            "nick": nick,
                            "user_id": user_info.get("user_id"),
                            "last_online": last_online,
                            "is_online": user_info.get("is_online"),
                            "gender": "Мужской" if user_info.get("is_male") else "Женский"
                        })
                    else:
                        print(f"❌ {nick} — ЗАНЯТ")
        
        print(f"🎯 Найдено свободных: {len(found)}")
        if self.taken_with_info:
            print(f"📊 Занятых ников с информацией: {len(self.taken_with_info)}")
        print()
        return found

# ==================== ОСНОВНАЯ ПРОГРАММА ====================
def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def banner():
    print("""
╔══════════════════════════════════════════════════════════╗
║     🚀 GALAXY NICK CHECKER v2.1                        ║
║     Поиск свободных ников + дата последнего онлайна    ║
╚══════════════════════════════════════════════════════════╝
    """)

def main():
    # ===== АВТОМАТИЧЕСКОЕ СОЗДАНИЕ .env =====
    if not ensure_env_file():
        return
    
    # Загружаем .env
    env_path = get_env_path()
    load_dotenv(env_path)
    
    user_id = os.getenv("GALAXY_USER_ID")
    password = os.getenv("GALAXY_PASSWORD")
    
    if not user_id or not password:
        print("❌ Ошибка! В .env не хватает данных.")
        print("   Проверьте, что указаны:")
        print("   GALAXY_USER_ID=ваш_айди")
        print("   GALAXY_PASSWORD=ваш_пароль")
        input("\nНажмите Enter для выхода...")
        sys.exit(1)
    
    try:
        user_id = int(user_id)
    except:
        print("❌ Ошибка! ID должен быть числом")
        input("\nНажмите Enter для выхода...")
        sys.exit(1)
    
    os.makedirs("nicks", exist_ok=True)
    
    checker = GalaxyNickChecker(user_id, password)
    generator = NickGenerator(checker)
    
    while True:
        clear()
        banner()
        print("МЕНЮ:")
        print("  1. Поиск (русский)")
        print("  2. Поиск (английский)")
        print("  3. Поиск (оба языка)")
        print("  4. Поиск по списку")
        print("  5. Статистика")
        print("  6. Показать занятые ники с датами")
        print("  7. Выход")
        print("="*50)
        
        choice = input("\n👉 Выбор: ").strip()
        
        if choice == "1":
            word = input("Введите слово: ").strip().lower()
            if word:
                found = generator.search(word, "russian")
                if found:
                    with open("nicks/found.txt", "a", encoding="utf-8") as f:
                        for nick in found:
                            f.write(f"{nick}\n")
        
        elif choice == "2":
            word = input("Введите слово: ").strip().lower()
            if word:
                found = generator.search(word, "english")
                if found:
                    with open("nicks/found.txt", "a", encoding="utf-8") as f:
                        for nick in found:
                            f.write(f"{nick}\n")
        
        elif choice == "3":
            word = input("Введите слово: ").strip().lower()
            if word:
                found = generator.search(word, "both")
                if found:
                    with open("nicks/found.txt", "a", encoding="utf-8") as f:
                        for nick in found:
                            f.write(f"{nick}\n")
        
        elif choice == "4":
            words = input("Слова через запятую: ").strip()
            words = [w.strip().lower() for w in words.split(",") if w.strip()]
            if words:
                lang = input("Язык (russian/english/both): ").strip().lower()
                if lang not in ["russian", "english", "both"]:
                    lang = "both"
                all_found = []
                all_taken = []
                for word in words:
                    found = generator.search(word, lang)
                    all_found.extend(found)
                    all_taken.extend(generator.taken_with_info)
                    time.sleep(1)
                if all_found:
                    with open("nicks/found.txt", "a", encoding="utf-8") as f:
                        for nick in set(all_found):
                            f.write(f"{nick}\n")
                    print(f"✅ Сохранено {len(set(all_found))} свободных ников")
                if all_taken:
                    with open("nicks/taken_info.txt", "a", encoding="utf-8") as f:
                        for item in all_taken:
                            f.write(f"{item['nick']} | ID: {item['user_id']} | {item['last_online']} | {'Онлайн' if item['is_online'] else 'Офлайн'}\n")
        
        elif choice == "5":
            stats = checker
            print(f"\n📊 Статистика:")
            print(f"   Проверено ников: {stats.checked}")
            print(f"   Найдено свободных: {stats.found}")
        
        elif choice == "6":
            if generator.taken_with_info:
                print("\n📋 Занятые ники с информацией:")
                print("-" * 60)
                for item in generator.taken_with_info:
                    status = "🟢 Онлайн" if item["is_online"] else "🔴 Офлайн"
                    print(f"  {item['nick']} | {item['gender']} | {status} | Последний раз: {item['last_online']}")
                print("-" * 60)
            else:
                print("\n📭 Нет данных о занятых никах. Сначала выполните поиск.")
        
        elif choice == "7":
            print("👋 До свидания!")
            break
        
        else:
            print("❌ Неверный выбор")
        
        input("\nНажмите Enter...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Остановлено")
        sys.exit(0)
