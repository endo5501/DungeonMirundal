"""アイテム詳細パネル"""

import pygame
import pygame_gui
from typing import Dict, Any, Optional
import logging
from ..service_panel import ServicePanel

logger = logging.getLogger(__name__)


class ItemDetailPanel(ServicePanel):
    """アイテム詳細パネル
    
    アイテムの詳細情報を表示する共通パネル。
    """
    
    def __init__(self, rect: pygame.Rect, parent: pygame_gui.elements.UIPanel,
                 ui_manager: pygame_gui.UIManager):
        """初期化"""
        # ItemDetailPanel固有のUI要素（ServicePanel初期化前に定義）
        self.name_label: Optional[pygame_gui.elements.UILabel] = None
        self.icon_image: Optional[pygame_gui.elements.UIImage] = None
        self.description_box: Optional[pygame_gui.elements.UITextBox] = None
        self.stats_box: Optional[pygame_gui.elements.UITextBox] = None
        
        # ServicePanel初期化（表示専用なのでcontrollerは不要）
        super().__init__(rect, parent, None, "item_detail", ui_manager)
        
        logger.info("ItemDetailPanel initialized")
    
    def _create_ui(self) -> None:
        """UI要素を作成"""
        self._create_name_area()
        self._create_description_area()
        self._create_stats_area()
    
    def _create_name_area(self) -> None:
        """アイテム名エリアを作成"""
        name_rect = pygame.Rect(5, 5, self.rect.width - 10, 30)
        
        if self.ui_element_manager and not self.ui_element_manager.is_destroyed:
            self.name_label = self.ui_element_manager.create_label(
                "item_name_label", "", name_rect
            )
        else:
            # フォールバック
            self.name_label = pygame_gui.elements.UILabel(
                relative_rect=name_rect,
                text="",
                manager=self.ui_manager,
                container=self.container
            )
            self.ui_elements.append(self.name_label)
    
    def _create_description_area(self) -> None:
        """説明文エリアを作成"""
        desc_rect = pygame.Rect(5, 40, self.rect.width - 10, 100)
        
        if self.ui_element_manager and not self.ui_element_manager.is_destroyed:
            self.description_box = self.ui_element_manager.create_text_box(
                "item_description_box", "", desc_rect
            )
        else:
            # フォールバック
            self.description_box = pygame_gui.elements.UITextBox(
                html_text="",
                relative_rect=desc_rect,
                manager=self.ui_manager,
                container=self.container
            )
            self.ui_elements.append(self.description_box)
    
    def _create_stats_area(self) -> None:
        """ステータス/効果エリアを作成"""
        stats_rect = pygame.Rect(5, 145, self.rect.width - 10, 80)
        
        if self.ui_element_manager and not self.ui_element_manager.is_destroyed:
            self.stats_box = self.ui_element_manager.create_text_box(
                "item_stats_box", "", stats_rect
            )
        else:
            # フォールバック
            self.stats_box = pygame_gui.elements.UITextBox(
                html_text="",
                relative_rect=stats_rect,
                manager=self.ui_manager,
                container=self.container
            )
            self.ui_elements.append(self.stats_box)
    
    def set_item(self, item_data: Dict[str, Any]) -> None:
        """アイテムデータを設定"""
        if not item_data:
            self.clear()
            return
        
        # 名前
        if self.name_label:
            self.name_label.set_text(item_data.get("name", "???"))
        
        # 説明
        if self.description_box:
            description = item_data.get("description", "説明なし")
            self.description_box.html_text = description
            self.description_box.rebuild()
        
        # ステータス/効果
        if self.stats_box:
            stats_text = self._build_stats_text(item_data)
            self.stats_box.html_text = stats_text
            self.stats_box.rebuild()
    
    def _build_stats_text(self, item_data: Dict[str, Any]) -> str:
        """ステータステキストを構築"""
        text = "<b>効果:</b><br>"
        
        # ステータス修正
        if "stats" in item_data:
            for stat, value in item_data["stats"].items():
                stat_name = self._get_stat_name(stat)
                if value > 0:
                    text += f"・{stat_name}: +{value}<br>"
                else:
                    text += f"・{stat_name}: {value}<br>"
        
        # 効果
        if "effect" in item_data:
            for effect, value in item_data["effect"].items():
                effect_text = self._get_effect_text(effect, value)
                text += f"・{effect_text}<br>"
        
        # 価格情報
        if "price" in item_data:
            text += f"<br><b>価格:</b> {item_data['price']} G"
        
        if "sell_price" in item_data:
            text += f"<br><b>売却価格:</b> {item_data['sell_price']} G"
        
        return text
    
    def _get_stat_name(self, stat: str) -> str:
        """ステータス名を取得"""
        stat_names = {
            "attack": "攻撃力",
            "defense": "防御力",
            "magic": "魔力",
            "speed": "素早さ",
            "accuracy": "命中率",
            "evasion": "回避率",
            "critical": "クリティカル率"
        }
        return stat_names.get(stat, stat)
    
    def _get_effect_text(self, effect: str, value: Any) -> str:
        """効果テキストを取得"""
        effect_texts = {
            "hp_restore": lambda v: f"HPを{v}回復",
            "mp_restore": lambda v: f"MPを{v}回復",
            "cure_poison": lambda v: "毒を治療",
            "cure_paralysis": lambda v: "麻痺を治療",
            "cure_all": lambda v: "全ての状態異常を治療",
            "revive": lambda v: f"戦闘不能を回復（HP{v}%）"
        }
        
        if effect in effect_texts:
            return effect_texts[effect](value)
        else:
            return f"{effect}: {value}"
    
    def clear(self) -> None:
        """表示をクリア"""
        if self.name_label:
            self.name_label.set_text("")
        
        if self.description_box:
            self.description_box.html_text = ""
            self.description_box.rebuild()
        
        if self.stats_box:
            self.stats_box.html_text = ""
            self.stats_box.rebuild()
    
    def show(self) -> None:
        """パネルを表示"""
        if self.container:
            self.container.show()
    
    def hide(self) -> None:
        """パネルを非表示"""
        if self.container:
            self.container.hide()
    
    def destroy(self) -> None:
        """パネルを破棄"""
        # ItemDetailPanel固有のクリーンアップ
        self.name_label = None
        self.icon_image = None
        self.description_box = None
        self.stats_box = None
        
        # ServicePanelの基本破棄処理を呼び出し
        super().destroy()
        
        logger.info("ItemDetailPanel destroyed")