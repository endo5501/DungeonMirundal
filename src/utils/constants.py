"""ゲーム定数の定義"""

# デフォルト値定数
DEFAULT_LOGGER_NAME = "dungeon"
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_ENCODING = "utf-8"
DEFAULT_LOG_FILE = "game.log"

# ログフォーマット定数
LOG_FORMAT_TIMESTAMP = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_FORMAT_DATE = '%Y-%m-%d %H:%M:%S'

# パーティ構成定数
EMPTY_PARTY_SIZE = 0
SINGLE_MEMBER_PARTY = 1
MIN_PARTY_SIZE = 1

# レベル範囲定数
MIN_CHARACTER_LEVEL = 1
EXPERIENCE_START_VALUE = 0

# インベントリ制限定数
MIN_INVENTORY_SIZE = 0
SINGLE_ITEM_QUANTITY = 1

# UI動作定数
MIN_UI_SCALE = 0.5
MAX_UI_SCALE = 2.0
INSTANT_TRANSITION = 0.0

# ファイルシステム定数
DIRECTORY_CREATE_MODE = 0o755
LOG_FILE_MODE = "a"

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

# 属性タイプ（Replace Type Code with Class向けの基盤）
ELEMENT_TYPES = {
    "PHYSICAL": "physical",
    "FIRE": "fire",
    "ICE": "ice",
    "LIGHTNING": "lightning"
}

# 属性効果倍率
ELEMENT_DAMAGE_MULTIPLIERS = {
    "weak": 1.5,
    "normal": 1.0,
    "resistant": 0.5,
    "immune": 0.0
}

# キャラクター設定
MAX_CHARACTER_LEVEL = 99
BASE_HP = 10
BASE_MP = 5

# 種族設定
RACES = ["human", "elf", "dwarf", "hobbit"]
DEFAULT_RACE = "human"
RANDOM_RACE_CHOICE = "random"

# 職業設定
CLASSES = [
    "fighter", "mage", "priest", "thief", 
    "bishop", "samurai", "lord", "ninja"
]
DEFAULT_CLASS = "fighter"
NO_CLASS_RESTRICTION = "any"

# 基本職業グループ
BASIC_CLASSES = ["fighter", "mage", "priest", "thief"]
ELITE_CLASSES = ["bishop", "samurai", "lord", "ninja"]

# UI設定
UI_SCALE = 1.0
MENU_TRANSITION_TIME = 0.3

# パス設定
CONFIG_DIR = "config"
SAVE_DIR = "saves"
ASSET_DIR = "assets"
LOG_DIR = "logs"

# ゲームロケーション定義
class GameLocation:
    """ゲーム内の場所を表す定数"""
    OVERWORLD = "overworld"
    DUNGEON = "dungeon"