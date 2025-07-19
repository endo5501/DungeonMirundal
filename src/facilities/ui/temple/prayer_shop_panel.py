"""祈祷書購入パネル"""

import logging
from typing import Dict, Any, List, Optional
import pygame
import pygame_gui
from pygame_gui.elements import UIWindow, UIButton, UILabel, UIScrollingContainer
from ..service_panel import ServicePanel

logger = logging.getLogger(__name__)


class PrayerShopPanel(ServicePanel):
    """祈祷書購入パネル
    
    神聖魔法の祈祷書を購入するためのUI。
    """
    
    def __init__(self, rect: pygame.Rect, parent: pygame_gui.elements.UIPanel,
                 controller, ui_manager: pygame_gui.UIManager):
        """初期化"""
        super().__init__(rect, parent, controller, "prayer_shop", ui_manager)
        
        # データ
        self.available_spells: List[Dict[str, Any]] = []
        self.categories: List[str] = []
        self.party_gold: int = 0
        
        # UI要素
        self.title_label: Optional[pygame_gui.elements.UILabel] = None
        self.spell_container: Optional[pygame_gui.elements.UIScrollingContainer] = None
        self.spell_buttons: Dict[str, pygame_gui.elements.UIButton] = {}
        self.detail_panel: Optional[pygame_gui.elements.UIPanel] = None
        self.spell_name_label: Optional[pygame_gui.elements.UILabel] = None
        self.spell_desc_label: Optional[pygame_gui.elements.UILabel] = None
        self.spell_cost_label: Optional[pygame_gui.elements.UILabel] = None
        self.purchase_button: Optional[pygame_gui.elements.UIButton] = None
        self.gold_label: Optional[pygame_gui.elements.UILabel] = None
        
        # 状態
        self.selected_spell: Optional[Dict[str, Any]] = None
        
        logger.info("PrayerShopPanel initialized")
    
    def _create_ui(self) -> None:
        """UI要素を作成"""
        self._create_header()
        self._create_spell_list()
        self._create_detail_area()
        self._create_action_controls()
        
        # 初期データを読み込み
        self._load_prayer_data()
    
    def _create_header(self) -> None:
        """ヘッダーを作成"""
        # タイトル
        title_rect = pygame.Rect(20, 20, 360, 30)
        if self.ui_element_manager and not self.ui_element_manager.is_destroyed:
            self.title_label = self.ui_element_manager.create_label(
                "title_label", "神聖魔法の祈祷書", title_rect
            )
        else:
            # フォールバック
            self.title_label = pygame_gui.elements.UILabel(
                relative_rect=title_rect,
                text="神聖魔法の祈祷書",
                manager=self.ui_manager,
                container=self.container
            )
            self.ui_elements.append(self.title_label)
        
        # 所持金表示
        gold_rect = pygame.Rect(20, 60, 200, 25)
        if self.ui_element_manager and not self.ui_element_manager.is_destroyed:
            self.gold_label = self.ui_element_manager.create_label(
                "gold_label", f"所持金: {self.party_gold} G", gold_rect
            )
        else:
            # フォールバック
            self.gold_label = pygame_gui.elements.UILabel(
                relative_rect=gold_rect,
                text=f"所持金: {self.party_gold} G",
                manager=self.ui_manager,
                container=self.container
            )
            self.ui_elements.append(self.gold_label)
    
    def _create_spell_list(self) -> None:
        """祈祷書リストを作成"""
        # 祈祷書リスト（スクロール可能）
        scroll_rect = pygame.Rect(20, 100, 360, 200)
        if self.ui_element_manager and not self.ui_element_manager.is_destroyed:
            # UIElementManagerでScrollingContainerは未対応のため、フォールバックを使用
            self.spell_container = pygame_gui.elements.UIScrollingContainer(
                relative_rect=scroll_rect,
                manager=self.ui_manager,
                container=self.container
            )
            self.ui_elements.append(self.spell_container)
        else:
            # フォールバック
            self.spell_container = pygame_gui.elements.UIScrollingContainer(
                relative_rect=scroll_rect,
                manager=self.ui_manager,
                container=self.container
            )
            self.ui_elements.append(self.spell_container)
    
    def _create_detail_area(self) -> None:
        """詳細表示エリアを作成"""
        # 詳細表示エリア
        detail_rect = pygame.Rect(20, 320, 360, 80)
        if self.ui_element_manager and not self.ui_element_manager.is_destroyed:
            self.spell_desc_label = self.ui_element_manager.create_label(
                "spell_desc_label", "祈祷書を選択してください", detail_rect
            )
        else:
            # フォールバック
            self.spell_desc_label = pygame_gui.elements.UILabel(
                relative_rect=detail_rect,
                text="祈祷書を選択してください",
                manager=self.ui_manager,
                container=self.container
            )
            self.ui_elements.append(self.spell_desc_label)
    
    def _create_action_controls(self) -> None:
        """アクションコントロールを作成"""
        # 購入ボタン
        button_rect = pygame.Rect(20, 420, 120, 40)
        if self.ui_element_manager and not self.ui_element_manager.is_destroyed:
            self.purchase_button = self.ui_element_manager.create_button(
                "purchase_button", "購入", button_rect
            )
        else:
            # フォールバック
            self.purchase_button = pygame_gui.elements.UIButton(
                relative_rect=button_rect,
                text="購入",
                manager=self.ui_manager,
                container=self.container
            )
            self.ui_elements.append(self.purchase_button)
        
        self.purchase_button.disable()
    
    def _load_prayer_data(self) -> None:
        """祈祷書データを読み込み"""
        result = self._execute_service_action("prayer_shop", {})
        
        if result.success and result.data:
            self.available_spells = result.data.get("available_spells", [])
            self.categories = result.data.get("categories", [])
            self.party_gold = result.data.get("party_gold", 0)
            
            # 所持金表示を更新
            self.gold_label.set_text(f"所持金: {self.party_gold} G")
            
            # 祈祷書ボタンを作成
            self._create_spell_buttons()
        else:
            self.spell_desc_label.set_text(result.message if result.message else "祈祷書データの読み込みに失敗しました")
    
    def _create_spell_buttons(self) -> None:
        """祈祷書ボタンを作成"""
        # 既存のボタンをクリア
        for button in self.spell_buttons.values():
            button.kill()
        self.spell_buttons.clear()
        
        y_offset = 10
        for i, spell in enumerate(self.available_spells):
            button_rect = pygame.Rect(10, y_offset, 340, 40)
            
            # 祈祷書情報を表示
            button_text = f"{spell['name']} - {spell['cost']} G"
            
            button = pygame_gui.elements.UIButton(
                relative_rect=button_rect,
                text=button_text,
                manager=self.ui_manager,
                container=self.spell_container,
                object_id=f"#spell_button_{i}"
            )
            
            self.spell_buttons[spell['id']] = button
            y_offset += 45
    
    def handle_button_click(self, button: pygame_gui.elements.UIButton) -> bool:
        """ボタンクリックを処理"""
        # 購入ボタン
        if button == self.purchase_button:
            self._perform_purchase()
            return True
        
        # 祈祷書選択ボタン
        for spell_id, spell_button in self.spell_buttons.items():
            if button == spell_button:
                self._select_spell(spell_id)
                return True
        
        return False
    
    def _select_spell(self, spell_id: str) -> None:
        """祈祷書を選択"""
        for spell in self.available_spells:
            if spell['id'] == spell_id:
                self.selected_spell = spell
                
                # 詳細情報を表示
                desc_text = f"{spell['name']}\n{spell['description']}\n費用: {spell['cost']} G"
                self.spell_desc_label.set_text(desc_text)
                
                # 購入ボタンの有効/無効を切り替え
                if self.party_gold >= spell['cost']:
                    self.purchase_button.enable()
                else:
                    self.purchase_button.disable()
                break
    
    def _perform_purchase(self) -> None:
        """購入を実行"""
        if not self.selected_spell:
            return
        
        result = self._execute_service_action("prayer_shop", {
            "action": "purchase",
            "spell_id": self.selected_spell['id']
        })
        
        # 結果を表示
        self.spell_desc_label.set_text(result.message)
        
        if result.success:
            # 成功時はデータを再読み込み
            self._load_prayer_data()
            self.selected_spell = None
            self.purchase_button.disable()
    
    def refresh(self) -> None:
        """パネルをリフレッシュ"""
        self._load_prayer_data()
        self.selected_spell = None
        self.purchase_button.disable()
        self.spell_desc_label.set_text("祈祷書を選択してください")