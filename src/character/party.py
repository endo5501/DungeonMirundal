"""パーティ管理システム"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
import uuid

from src.character.character import Character, CharacterStatus
from src.utils.constants import MAX_PARTY_SIZE, FRONT_ROW_SIZE, BACK_ROW_SIZE
from src.utils.logger import logger


class PartyPosition(Enum):
    """パーティ内位置"""
    FRONT_1 = "front_1"
    FRONT_2 = "front_2"
    FRONT_3 = "front_3"
    BACK_1 = "back_1"
    BACK_2 = "back_2"
    BACK_3 = "back_3"


@dataclass
class PartyFormation:
    """パーティ編成"""
    positions: Dict[PartyPosition, Optional[str]] = field(default_factory=dict)
    
    def __post_init__(self):
        """初期化時に全ポジションを設定"""
        for pos in PartyPosition:
            if pos not in self.positions:
                self.positions[pos] = None
    
    def add_character(self, character_id: str, position: PartyPosition) -> bool:
        """キャラクターを指定位置に配置"""
        if self.positions[position] is not None:
            logger.warning(f"位置 {position.value} は既に使用されています")
            return False
        
        self.positions[position] = character_id
        logger.info(f"キャラクター {character_id} を位置 {position.value} に配置")
        return True
    
    def remove_character(self, character_id: str) -> bool:
        """キャラクターをパーティから除去"""
        for position, char_id in self.positions.items():
            if char_id == character_id:
                self.positions[position] = None
                logger.info(f"キャラクター {character_id} を位置 {position.value} から除去")
                return True
        
        logger.warning(f"キャラクター {character_id} がパーティに見つかりません")
        return False
    
    def move_character(self, character_id: str, new_position: PartyPosition) -> bool:
        """キャラクターの位置を変更"""
        # 現在の位置を探す
        current_position = None
        for position, char_id in self.positions.items():
            if char_id == character_id:
                current_position = position
                break
        
        if current_position is None:
            logger.warning(f"キャラクター {character_id} がパーティに見つかりません")
            return False
        
        if self.positions[new_position] is not None:
            logger.warning(f"位置 {new_position.value} は既に使用されています")
            return False
        
        # 位置移動
        self.positions[current_position] = None
        self.positions[new_position] = character_id
        logger.info(f"キャラクター {character_id} を {current_position.value} から {new_position.value} に移動")
        return True
    
    def get_front_row(self) -> List[Optional[str]]:
        """前衛の取得"""
        return [
            self.positions[PartyPosition.FRONT_1],
            self.positions[PartyPosition.FRONT_2],
            self.positions[PartyPosition.FRONT_3]
        ]
    
    def get_back_row(self) -> List[Optional[str]]:
        """後衛の取得"""
        return [
            self.positions[PartyPosition.BACK_1],
            self.positions[PartyPosition.BACK_2],
            self.positions[PartyPosition.BACK_3]
        ]
    
    def get_character_position(self, character_id: str) -> Optional[PartyPosition]:
        """キャラクターの位置を取得"""
        for position, char_id in self.positions.items():
            if char_id == character_id:
                return position
        return None
    
    def is_front_row(self, character_id: str) -> bool:
        """前衛にいるかチェック"""
        position = self.get_character_position(character_id)
        return position in [PartyPosition.FRONT_1, PartyPosition.FRONT_2, PartyPosition.FRONT_3]
    
    def get_active_characters(self) -> List[str]:
        """アクティブなキャラクター一覧"""
        return [char_id for char_id in self.positions.values() if char_id is not None]
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式でシリアライズ"""
        return {pos.value: char_id for pos, char_id in self.positions.items()}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PartyFormation':
        """辞書からデシリアライズ"""
        formation = cls()
        for pos_str, char_id in data.items():
            try:
                position = PartyPosition(pos_str)
                formation.positions[position] = char_id
            except ValueError:
                logger.warning(f"無効な位置: {pos_str}")
        return formation


@dataclass
class Party:
    """パーティクラス"""
    party_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "New Party"
    characters: Dict[str, Character] = field(default_factory=dict)
    formation: PartyFormation = field(default_factory=PartyFormation)
    gold: int = 0
    
    def add_character(self, character: Character, position: Optional[PartyPosition] = None) -> bool:
        """キャラクターをパーティに追加"""
        if len(self.characters) >= MAX_PARTY_SIZE:
            logger.warning(f"パーティが満員です (最大 {MAX_PARTY_SIZE} 人)")
            return False
        
        if character.character_id in self.characters:
            logger.warning(f"キャラクター {character.name} は既にパーティにいます")
            return False
        
        # キャラクターを追加
        self.characters[character.character_id] = character
        
        # 位置を設定
        if position is None:
            position = self._find_empty_position()
        
        if position is not None:
            self.formation.add_character(character.character_id, position)
            logger.info(f"キャラクター {character.name} をパーティに追加しました")
            return True
        else:
            # 位置が見つからない場合はキャラクターも削除
            del self.characters[character.character_id]
            logger.error("パーティに空きがありません")
            return False
    
    def remove_character(self, character_id: str) -> bool:
        """キャラクターをパーティから削除"""
        if character_id not in self.characters:
            logger.warning(f"キャラクター {character_id} がパーティに見つかりません")
            return False
        
        character = self.characters[character_id]
        del self.characters[character_id]
        self.formation.remove_character(character_id)
        
        logger.info(f"キャラクター {character.name} をパーティから削除しました")
        return True
    
    def get_character(self, character_id: str) -> Optional[Character]:
        """キャラクターを取得"""
        return self.characters.get(character_id)
    
    def get_all_characters(self) -> List[Character]:
        """全キャラクターのリストを取得"""
        return list(self.characters.values())
    
    def get_living_characters(self) -> List[Character]:
        """生存しているキャラクターのリストを取得"""
        return [char for char in self.characters.values() if char.is_alive()]
    
    def get_conscious_characters(self) -> List[Character]:
        """意識のあるキャラクターのリストを取得"""
        return [char for char in self.characters.values() if char.is_conscious()]
    
    def get_front_row_characters(self) -> List[Character]:
        """前衛キャラクターを取得"""
        front_ids = self.formation.get_front_row()
        return [self.characters[char_id] for char_id in front_ids if char_id and char_id in self.characters]
    
    def get_back_row_characters(self) -> List[Character]:
        """後衛キャラクターを取得"""
        back_ids = self.formation.get_back_row()
        return [self.characters[char_id] for char_id in back_ids if char_id and char_id in self.characters]
    
    def move_character(self, character_id: str, new_position: PartyPosition) -> bool:
        """キャラクターの位置を変更"""
        if character_id not in self.characters:
            logger.warning(f"キャラクター {character_id} がパーティに見つかりません")
            return False
        
        return self.formation.move_character(character_id, new_position)
    
    def _find_empty_position(self) -> Optional[PartyPosition]:
        """空いている位置を探す"""
        for position in PartyPosition:
            if self.formation.positions[position] is None:
                return position
        return None
    
    def is_defeated(self) -> bool:
        """パーティが全滅しているかチェック"""
        living_chars = self.get_living_characters()
        return len(living_chars) == 0
    
    def has_conscious_members(self) -> bool:
        """意識のあるメンバーがいるかチェック"""
        conscious_chars = self.get_conscious_characters()
        return len(conscious_chars) > 0
    
    def rest(self):
        """休息処理（地上でのHP/MP全回復）"""
        for character in self.characters.values():
            if character.status in [CharacterStatus.GOOD, CharacterStatus.INJURED]:
                character.derived_stats.current_hp = character.derived_stats.max_hp
                character.derived_stats.current_mp = character.derived_stats.max_mp
                character.status = CharacterStatus.GOOD
        
        logger.info(f"パーティ {self.name} が休息しました")
    
    def add_gold(self, amount: int):
        """ゴールドを追加"""
        old_gold = self.gold
        self.gold += amount
        logger.info(f"パーティのゴールド変化: {old_gold} -> {self.gold} (+{amount})")
    
    def spend_gold(self, amount: int) -> bool:
        """ゴールドを消費"""
        if self.gold < amount:
            logger.warning(f"ゴールドが不足しています: 必要 {amount}, 現在 {self.gold}")
            return False
        
        old_gold = self.gold
        self.gold -= amount
        logger.info(f"パーティのゴールド変化: {old_gold} -> {self.gold} (-{amount})")
        return True
    
    def get_total_level(self) -> int:
        """パーティの合計レベル"""
        return sum(char.experience.level for char in self.characters.values())
    
    def get_average_level(self) -> float:
        """パーティの平均レベル"""
        if not self.characters:
            return 0.0
        return self.get_total_level() / len(self.characters)
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式でシリアライズ"""
        return {
            'party_id': self.party_id,
            'name': self.name,
            'characters': {char_id: char.to_dict() for char_id, char in self.characters.items()},
            'formation': self.formation.to_dict(),
            'gold': self.gold
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Party':
        """辞書からデシリアライズ"""
        characters = {}
        for char_id, char_data in data.get('characters', {}).items():
            characters[char_id] = Character.from_dict(char_data)
        
        party = cls(
            party_id=data.get('party_id', str(uuid.uuid4())),
            name=data.get('name', 'New Party'),
            characters=characters,
            formation=PartyFormation.from_dict(data.get('formation', {})),
            gold=data.get('gold', 0)
        )
        return party