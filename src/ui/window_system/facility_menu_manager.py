"""
FacilityMenuManager クラス

施設メニューロジックと項目管理

Fowler式リファクタリング：Extract Class パターン
"""

from typing import Dict, List, Any, Optional
from src.ui.window_system.facility_menu_types import (
    FacilityType, FacilityMenuItem, MenuItemType, FacilityInteraction
)
from src.utils.logger import logger


class FacilityMenuManager:
    """
    施設メニュー管理クラス
    
    メニューロジック、項目管理、選択処理を担当
    """
    
    def __init__(self, facility_type: FacilityType, menu_items: List[FacilityMenuItem]):
        """
        メニューマネージャーを初期化
        
        Args:
            facility_type: 施設タイプ
            menu_items: メニュー項目リスト
        """
        self.facility_type = facility_type
        self.menu_items = menu_items
        self.selected_index = 0
        self.interactions: List[FacilityInteraction] = []
        
        logger.debug(f"FacilityMenuManagerを初期化: {facility_type}, 項目数: {len(menu_items)}")
    
    def get_selected_item(self) -> Optional[FacilityMenuItem]:
        """現在選択されている項目を取得"""
        if 0 <= self.selected_index < len(self.menu_items):
            return self.menu_items[self.selected_index]
        return None
    
    def move_selection_up(self) -> bool:
        """選択を上に移動"""
        if self.selected_index > 0:
            self.selected_index -= 1
        else:
            # ラップアラウンド
            self.selected_index = len(self.menu_items) - 1
        
        logger.debug(f"選択を上に移動: インデックス {self.selected_index}")
        return True
    
    def move_selection_down(self) -> bool:
        """選択を下に移動"""
        if self.selected_index < len(self.menu_items) - 1:
            self.selected_index += 1
        else:
            # ラップアラウンド
            self.selected_index = 0
        
        logger.debug(f"選択を下に移動: インデックス {self.selected_index}")
        return True
    
    def select_item_by_id(self, item_id: str) -> Optional[FacilityMenuItem]:
        """IDで項目を選択"""
        for item in self.menu_items:
            if item.item_id == item_id:
                return item
        
        logger.warning(f"メニュー項目が見つかりません: {item_id}")
        return None
    
    def is_exit_item(self, item: FacilityMenuItem) -> bool:
        """退場項目かどうかチェック"""
        return item.item_type == MenuItemType.EXIT
    
    def record_interaction(self, interaction_type: str, item_id: Optional[str] = None) -> FacilityInteraction:
        """インタラクションを記録"""
        interaction = FacilityInteraction(
            interaction_type=interaction_type,
            facility_type=self.facility_type,
            item_id=item_id
        )
        
        self.interactions.append(interaction)
        logger.debug(f"インタラクション記録: {interaction_type}, {item_id}")
        
        return interaction
    
    def get_interaction_history(self) -> List[FacilityInteraction]:
        """インタラクション履歴を取得"""
        return self.interactions.copy()
    
    def reset_selection(self) -> None:
        """選択状態をリセット"""
        self.selected_index = 0
        logger.debug("選択状態をリセット")
    
    def get_visible_items(self, party: Any) -> List[FacilityMenuItem]:
        """表示可能な項目を取得"""
        visible_items = []
        for item in self.menu_items:
            if item.visible and item.is_available(party):
                visible_items.append(item)
        
        logger.debug(f"表示可能項目数: {len(visible_items)}/{len(self.menu_items)}")
        return visible_items
    
    def validate_selection_index(self) -> bool:
        """選択インデックスの妥当性をチェック"""
        return 0 <= self.selected_index < len(self.menu_items)
    
    def get_menu_summary(self) -> Dict[str, Any]:
        """メニューサマリーを取得"""
        return {
            'facility_type': self.facility_type.value,
            'total_items': len(self.menu_items),
            'selected_index': self.selected_index,
            'selected_item_id': self.get_selected_item().item_id if self.get_selected_item() else None,
            'interaction_count': len(self.interactions)
        }