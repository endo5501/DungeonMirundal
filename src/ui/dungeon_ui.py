"""ダンジョン内UIシステム"""

from typing import Dict, List, Optional, Callable, Any
from enum import Enum
from direct.gui.DirectGui import *
from direct.gui.OnscreenText import OnscreenText
from panda3d.core import TextNode, Vec3

from src.ui.base_ui import UIElement, UIButton, UIText, UIMenu, UIState
from src.ui.inventory_ui import InventoryUI
from src.ui.equipment_ui import EquipmentUI
from src.ui.magic_ui import MagicUI
from src.ui.status_effects_ui import StatusEffectsUI
from src.character.party import Party
from src.core.config_manager import config_manager
from src.utils.logger import logger


class DungeonMenuType(Enum):
    """ダンジョンメニュータイプ"""
    MAIN = "main"           # メインメニュー
    INVENTORY = "inventory" # インベントリ
    MAGIC = "magic"         # 魔法
    EQUIPMENT = "equipment" # 装備
    CAMP = "camp"           # キャンプ
    STATUS = "status"       # ステータス
    STATUS_EFFECTS = "status_effects" # 状態効果


class DungeonMainMenu(UIElement):
    """ダンジョンメインメニュー"""
    
    def __init__(self, element_id: str = "dungeon_main_menu"):
        super().__init__(element_id)
        
        # メニュー項目
        self.menu_items = [
            {"text": "インベントリ", "action": "inventory"},
            {"text": "魔法", "action": "magic"},
            {"text": "装備", "action": "equipment"},
            {"text": "キャンプ", "action": "camp"},
            {"text": "ステータス", "action": "status"},
            {"text": "状態効果", "action": "status_effects"},
            {"text": "地上部に戻る", "action": "return_overworld"},
            {"text": "閉じる", "action": "close"}
        ]
        
        # コールバック
        self.callbacks: Dict[str, Callable] = {}
        
        # UI要素
        self.background = None
        self.title_text = None
        self.menu_buttons: List[UIButton] = []
        
        self._create_ui()
    
    def _create_ui(self):
        """UI要素を作成"""
        # 半透明背景
        self.background = DirectFrame(
            frameColor=(0, 0, 0, 0.7),
            frameSize=(-1.5, 1.5, -1, 1),
            pos=(0, 0, 0)
        )
        
        # タイトル
        self.title_text = OnscreenText(
            text=config_manager.get_text("dungeon.menu.title"),
            pos=(0, 0.7),
            scale=0.08,
            fg=(1, 1, 1, 1),
            align=TextNode.ACenter
        )
        
        # メニューボタン作成
        self._create_menu_buttons()
        
        # 初期状態は非表示
        self.hide()
    
    def _create_menu_buttons(self):
        """メニューボタンを作成"""
        start_y = 0.5
        button_height = 0.12
        
        for i, item in enumerate(self.menu_items):
            y_pos = start_y - i * button_height
            
            button = UIButton(
                f"{self.element_id}_btn_{item['action']}",
                item['text'],
                pos=(0, y_pos),
                scale=(0.25, 0.05),
                command=self._on_menu_item_click,
                extraArgs=[item['action']]
            )
            
            self.menu_buttons.append(button)
    
    def _on_menu_item_click(self, action: str):
        """メニュー項目クリック処理"""
        logger.info(f"ダンジョンメニュー選択: {action}")
        
        if action in self.callbacks:
            self.callbacks[action]()
        elif action == "close":
            self.hide()
    
    def set_callback(self, action: str, callback: Callable):
        """コールバックを設定"""
        self.callbacks[action] = callback
    
    def show(self):
        """メニューを表示"""
        super().show()
        self.state = UIState.MODAL
        self.background.show()
        self.title_text.show()
        for button in self.menu_buttons:
            button.show()
        
        logger.debug("ダンジョンメインメニューを表示")
    
    def hide(self):
        """メニューを非表示"""
        super().hide()
        self.background.hide()
        self.title_text.hide()
        for button in self.menu_buttons:
            button.hide()
        
        logger.debug("ダンジョンメインメニューを非表示")
    
    def destroy(self):
        """メニューを破棄"""
        if self.background:
            self.background.destroy()
        if self.title_text:
            self.title_text.destroy()
        for button in self.menu_buttons:
            button.destroy()
        
        super().destroy()


class DungeonStatusBar(UIElement):
    """ダンジョン内ステータス表示バー"""
    
    def __init__(self, element_id: str = "dungeon_status_bar"):
        super().__init__(element_id)
        
        # パーティ参照
        self.party: Optional[Party] = None
        
        # UI要素
        self.background = None
        self.character_status_texts: List[OnscreenText] = []
        self.location_text = None
        
        self._create_ui()
    
    def _create_ui(self):
        """UI要素を作成"""
        # 背景
        self.background = DirectFrame(
            frameColor=(0, 0, 0, 0.5),
            frameSize=(-1, 1, 0.8, 1),
            pos=(0, 0, 0)
        )
        
        # 位置情報表示
        self.location_text = OnscreenText(
            text="位置: 不明",
            pos=(-0.9, 0.9),
            scale=0.04,
            fg=(1, 1, 1, 1),
            align=TextNode.ALeft
        )
        
        # 初期状態は非表示
        self.hide()
    
    def set_party(self, party: Party):
        """パーティを設定"""
        self.party = party
        self._update_character_status()
    
    def _update_character_status(self):
        """キャラクターステータス表示を更新"""
        # 既存のテキストを削除
        for text in self.character_status_texts:
            text.destroy()
        self.character_status_texts.clear()
        
        if not self.party:
            return
        
        # キャラクター情報を表示
        living_chars = self.party.get_living_characters()
        for i, character in enumerate(living_chars[:6]):  # 最大6人
            x_pos = -0.9 + (i * 0.3)
            
            status_text = f"{character.name}\nHP:{character.derived_stats.current_hp}/{character.derived_stats.max_hp}\nMP:{character.derived_stats.current_mp}/{character.derived_stats.max_mp}"
            
            char_text = OnscreenText(
                text=status_text,
                pos=(x_pos, 0.85),
                scale=0.03,
                fg=(1, 1, 1, 1),
                align=TextNode.ALeft
            )
            
            self.character_status_texts.append(char_text)
    
    def update_location(self, location_info: str):
        """位置情報を更新"""
        if self.location_text:
            self.location_text.setText(f"位置: {location_info}")
    
    def update_status(self):
        """ステータス表示を更新"""
        self._update_character_status()
    
    def show(self):
        """ステータスバーを表示"""
        super().show()
        self.background.show()
        self.location_text.show()
        for text in self.character_status_texts:
            text.show()
    
    def hide(self):
        """ステータスバーを非表示"""
        super().hide()
        self.background.hide()
        self.location_text.hide()
        for text in self.character_status_texts:
            text.hide()
    
    def destroy(self):
        """ステータスバーを破棄"""
        if self.background:
            self.background.destroy()
        if self.location_text:
            self.location_text.destroy()
        for text in self.character_status_texts:
            text.destroy()
        
        super().destroy()


class DungeonUIManager:
    """ダンジョンUI統合管理"""
    
    def __init__(self):
        # UI要素
        self.main_menu: Optional[DungeonMainMenu] = None
        self.status_bar: Optional[DungeonStatusBar] = None
        self.inventory_ui: Optional[InventoryUI] = None
        self.equipment_ui: Optional[EquipmentUI] = None
        self.magic_ui: Optional[MagicUI] = None
        self.status_effects_ui: Optional[StatusEffectsUI] = None
        
        # 状態管理
        self.current_menu: Optional[DungeonMenuType] = None
        self.is_menu_open = False
        
        # 外部参照
        self.party: Optional[Party] = None
        self.dungeon_manager = None
        self.game_manager = None
        
        # コールバック
        self.callbacks: Dict[str, Callable] = {}
        
        self._initialize_ui()
        
        logger.info("DungeonUIManagerを初期化しました")
    
    def _initialize_ui(self):
        """UI要素を初期化"""
        # メインメニュー
        self.main_menu = DungeonMainMenu()
        self._setup_main_menu_callbacks()
        
        # ステータスバー
        self.status_bar = DungeonStatusBar()
    
    def _setup_main_menu_callbacks(self):
        """メインメニューのコールバックを設定"""
        if not self.main_menu:
            return
        
        self.main_menu.set_callback("inventory", self._open_inventory)
        self.main_menu.set_callback("magic", self._open_magic)
        self.main_menu.set_callback("equipment", self._open_equipment)
        self.main_menu.set_callback("camp", self._open_camp)
        self.main_menu.set_callback("status", self._open_status)
        self.main_menu.set_callback("status_effects", self._open_status_effects)
        self.main_menu.set_callback("return_overworld", self._return_to_overworld)
    
    def set_party(self, party: Party):
        """パーティを設定"""
        self.party = party
        if self.status_bar:
            self.status_bar.set_party(party)
    
    def set_managers(self, dungeon_manager, game_manager):
        """マネージャーを設定"""
        self.dungeon_manager = dungeon_manager
        self.game_manager = game_manager
    
    def set_callback(self, action: str, callback: Callable):
        """外部コールバックを設定"""
        self.callbacks[action] = callback
    
    def toggle_main_menu(self):
        """メインメニューの表示/非表示を切り替え"""
        if self.is_menu_open:
            self.close_all_menus()
        else:
            self.open_main_menu()
    
    def open_main_menu(self):
        """メインメニューを開く"""
        if self.main_menu:
            self.close_all_menus()
            self.main_menu.show()
            self.current_menu = DungeonMenuType.MAIN
            self.is_menu_open = True
            
            logger.info("ダンジョンメインメニューを開きました")
    
    def close_all_menus(self):
        """すべてのメニューを閉じる"""
        if self.main_menu:
            self.main_menu.hide()
        
        if self.inventory_ui:
            self.inventory_ui.hide()
        
        if self.equipment_ui:
            self.equipment_ui.hide()
        
        if self.magic_ui:
            self.magic_ui.hide()
        
        if self.status_effects_ui:
            self.status_effects_ui.hide()
        
        self.current_menu = None
        self.is_menu_open = False
        
        logger.info("ダンジョンメニューを閉じました")
    
    def show_status_bar(self):
        """ステータスバーを表示"""
        if self.status_bar:
            self.status_bar.show()
    
    def hide_status_bar(self):
        """ステータスバーを非表示"""
        if self.status_bar:
            self.status_bar.hide()
    
    def update_location(self, location_info: str):
        """位置情報を更新"""
        if self.status_bar:
            self.status_bar.update_location(location_info)
    
    def update_party_status(self):
        """パーティステータスを更新"""
        if self.status_bar:
            self.status_bar.update_status()
    
    def _open_inventory(self):
        """インベントリを開く"""
        logger.info("インベントリメニューを開きます")
        
        if not self.inventory_ui and self.party:
            self.inventory_ui = InventoryUI()
            self.inventory_ui.set_party(self.party)
        
        if self.inventory_ui:
            self.main_menu.hide()
            self.inventory_ui.show()
            self.current_menu = DungeonMenuType.INVENTORY
    
    def _open_magic(self):
        """魔法メニューを開く"""
        logger.info("魔法メニューを開きます")
        
        if not self.magic_ui and self.party:
            self.magic_ui = MagicUI()
            self.magic_ui.set_party(self.party)
        
        if self.magic_ui:
            self.main_menu.hide()
            self.magic_ui.show()
            self.current_menu = DungeonMenuType.MAGIC
    
    def _open_equipment(self):
        """装備メニューを開く"""
        logger.info("装備メニューを開きます")
        
        if not self.equipment_ui and self.party:
            self.equipment_ui = EquipmentUI()
            self.equipment_ui.set_party(self.party)
        
        if self.equipment_ui:
            self.main_menu.hide()
            self.equipment_ui.show()
            self.current_menu = DungeonMenuType.EQUIPMENT
    
    def _open_camp(self):
        """キャンプメニューを開く"""
        logger.info("キャンプメニューを開きます")
        # TODO: キャンプメニューの実装
    
    def _open_status(self):
        """ステータスメニューを開く"""
        logger.info("ステータスメニューを開きます")
        # TODO: ステータスメニューの実装
    
    def _open_status_effects(self):
        """状態効果メニューを開く"""
        logger.info("状態効果メニューを開きます")
        
        if not self.status_effects_ui and self.party:
            self.status_effects_ui = StatusEffectsUI()
            self.status_effects_ui.set_party(self.party)
        
        if self.status_effects_ui:
            self.main_menu.hide()
            self.status_effects_ui.show()
            self.current_menu = DungeonMenuType.STATUS_EFFECTS
    
    def _return_to_overworld(self):
        """地上部に戻る"""
        logger.info("地上部への帰還を実行します")
        
        if "return_overworld" in self.callbacks:
            self.callbacks["return_overworld"]()
        elif self.game_manager and hasattr(self.game_manager, 'transition_to_overworld'):
            self.close_all_menus()
            self.game_manager.transition_to_overworld()
    
    def cleanup(self):
        """リソースをクリーンアップ"""
        if self.main_menu:
            self.main_menu.destroy()
        if self.status_bar:
            self.status_bar.destroy()
        if self.inventory_ui:
            self.inventory_ui.destroy()
        if self.equipment_ui:
            self.equipment_ui.destroy()
        if self.magic_ui:
            self.magic_ui.destroy()
        if self.status_effects_ui:
            self.status_effects_ui.destroy()
        
        logger.info("DungeonUIManagerをクリーンアップしました")