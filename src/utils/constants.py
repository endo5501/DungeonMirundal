"""ゲーム定数の定義"""

# ゲーム設定
GAME_TITLE = "Dungeon RPG"
WINDOW_WIDTH = 1024
WINDOW_HEIGHT = 768
FPS = 60

# パーティ設定
MAX_PARTY_SIZE = 6
FRONT_ROW_SIZE = 3
BACK_ROW_SIZE = 3

# インベントリ設定
MAX_INVENTORY_SIZE = 10

# ダンジョン設定
MIN_DUNGEON_FLOORS = 3
MAX_DUNGEON_FLOORS = 20

# 属性タイプ
ELEMENT_TYPES = {
    "PHYSICAL": "physical",
    "FIRE": "fire",
    "ICE": "ice",
    "LIGHTNING": "lightning"
}

# キャラクター設定
MAX_CHARACTER_LEVEL = 99
BASE_HP = 10
BASE_MP = 5

# 種族リスト
RACES = ["human", "elf", "dwarf", "hobbit"]

# 職業リスト
CLASSES = [
    "fighter", "mage", "priest", "thief", 
    "bishop", "samurai", "lord", "ninja"
]

# UI設定
UI_SCALE = 1.0
MENU_TRANSITION_TIME = 0.3

# パス設定
CONFIG_DIR = "config"
SAVE_DIR = "saves"
ASSET_DIR = "assets"
LOG_DIR = "logs"