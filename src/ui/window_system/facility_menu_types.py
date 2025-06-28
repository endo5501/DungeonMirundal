"""
FacilityMenuWindow 型定義

施設メニューウィンドウに関する型定義
"""

from enum import Enum
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass


class FacilityType(Enum):
    """施設タイプ"""
    GUILD = "guild"
    INN = "inn"
    SHOP = "shop"
    TEMPLE = "temple"
    MAGIC_GUILD = "magic_guild"
    
    @property
    def display_name(self) -> str:
        """表示名を取得"""
        display_names = {
            FacilityType.GUILD: "冒険者ギルド",
            FacilityType.INN: "宿屋",
            FacilityType.SHOP: "商店",
            FacilityType.TEMPLE: "神殿",
            FacilityType.MAGIC_GUILD: "魔術師ギルド"
        }
        return display_names.get(self, str(self))


class MenuItemType(Enum):
    """メニュー項目タイプ"""
    ACTION = "action"
    SUBMENU = "submenu"
    DIALOG = "dialog"
    EXIT = "exit"


@dataclass
class FacilityMenuItem:
    """施設メニュー項目"""
    item_id: str
    label: str
    item_type: MenuItemType = MenuItemType.ACTION
    enabled: bool = True
    visible: bool = True
    condition: Optional[str] = None
    cost: Optional[int] = None
    description: Optional[str] = None
    callback: Optional[Callable] = None
    
    def is_available(self, party: Any) -> bool:
        """パーティの状態に基づいて利用可能かチェック"""
        if not self.visible:
            return False
        
        if not self.enabled:
            return False
        
        # コスト条件チェック
        if self.cost and hasattr(party, 'get_gold'):
            if party.get_gold() < self.cost:
                return False
        
        # カスタム条件チェック
        if self.condition:
            return self._check_condition(party)
        
        return True
    
    def _check_condition(self, party: Any) -> bool:
        """条件をチェック"""
        if self.condition == 'has_dead_members':
            return hasattr(party, 'has_dead_members') and party.has_dead_members()
        elif self.condition == 'has_items':
            return hasattr(party, 'has_items') and party.has_items()
        elif self.condition == 'is_full_hp':
            return hasattr(party, 'is_full_hp') and party.is_full_hp()
        # 他の条件も必要に応じて追加
        return True


@dataclass
class FacilityConfig:
    """施設設定"""
    facility_type: str
    facility_name: str
    party: Any
    menu_items: List[Dict[str, Any]]
    show_party_info: bool = True
    show_gold: bool = True
    background_music: Optional[str] = None
    welcome_message: Optional[str] = None
    
    def validate(self) -> None:
        """設定の妥当性をチェック"""
        if not self.facility_type:
            raise ValueError("Facility config must contain 'facility_type'")
        if not self.menu_items:
            raise ValueError("Facility config must contain 'menu_items'")
        if self.party is None:
            raise ValueError("Facility config must contain 'party'")
    
    def get_menu_items(self) -> List[FacilityMenuItem]:
        """メニュー項目をFacilityMenuItemオブジェクトに変換"""
        items = []
        for item_config in self.menu_items:
            item_type = MenuItemType.ACTION
            
            # タイプ判定
            if item_config.get('type') == 'submenu':
                item_type = MenuItemType.SUBMENU
            elif item_config.get('type') == 'dialog':
                item_type = MenuItemType.DIALOG
            elif item_config.get('id') == 'exit':
                item_type = MenuItemType.EXIT
            
            item = FacilityMenuItem(
                item_id=item_config['id'],
                label=item_config['label'],
                item_type=item_type,
                enabled=item_config.get('enabled', True),
                visible=item_config.get('visible', True),
                condition=item_config.get('condition'),
                cost=item_config.get('cost'),
                description=item_config.get('description'),
                callback=item_config.get('callback')
            )
            items.append(item)
        
        return items


@dataclass
class PartyInfo:
    """パーティ情報"""
    member_count: int
    gold: int
    max_hp: int
    current_hp: int
    location: str
    
    @property
    def hp_percentage(self) -> float:
        """HP割合を取得"""
        return (self.current_hp / max(self.max_hp, 1)) * 100.0
    
    @property
    def is_healthy(self) -> bool:
        """健康状態かどうか"""
        return self.hp_percentage >= 80.0


@dataclass
class FacilityInteraction:
    """施設インタラクション"""
    interaction_type: str  # 'enter', 'exit', 'menu_select', 'purchase', etc.
    facility_type: FacilityType
    item_id: Optional[str] = None
    cost: Optional[int] = None
    result: Optional[Any] = None
    timestamp: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'interaction_type': self.interaction_type,
            'facility_type': self.facility_type.value,
            'item_id': self.item_id,
            'cost': self.cost,
            'result': self.result,
            'timestamp': self.timestamp
        }


@dataclass
class MenuLayout:
    """メニューレイアウト"""
    window_width: int = 600
    window_height: int = 500
    menu_item_height: int = 40
    menu_spacing: int = 10
    title_height: int = 50
    party_info_height: int = 100
    padding: int = 20
    
    def calculate_menu_area_rect(self) -> Dict[str, int]:
        """メニューエリアのRectを計算"""
        y_offset = self.title_height + self.padding
        if self.party_info_height > 0:
            y_offset += self.party_info_height + self.padding
        
        height = self.window_height - y_offset - self.padding
        
        return {
            'x': self.padding,
            'y': y_offset,
            'width': self.window_width - (self.padding * 2),
            'height': height
        }
    
    def calculate_menu_item_positions(self, item_count: int) -> List[Dict[str, int]]:
        """メニュー項目の位置を計算"""
        menu_area = self.calculate_menu_area_rect()
        positions = []
        
        for i in range(item_count):
            y = menu_area['y'] + i * (self.menu_item_height + self.menu_spacing)
            
            positions.append({
                'x': menu_area['x'],
                'y': y,
                'width': menu_area['width'],
                'height': self.menu_item_height
            })
        
        return positions


# コールバック型定義
MenuItemCallback = Callable[[str, FacilityType], None]
ConditionChecker = Callable[[Any], bool]
PartyInfoProvider = Callable[[Any], PartyInfo]