"""祈祷書購入パネル"""

import logging
from typing import Dict, Any, List, Optional
import pygame
import pygame_gui
from pygame_gui.elements import UIWindow, UIButton, UILabel, UIScrollingContainer

logger = logging.getLogger(__name__)


class PrayerShopPanel:
    """祈祷書購入パネル
    
    神聖魔法の祈祷書を購入するためのUI。
    """
    
    def __init__(self, rect: pygame.Rect, parent: pygame_gui.elements.UIPanel,
                 ui_manager: pygame_gui.UIManager, controller, service, data: Dict[str, Any]):
        """初期化
        
        Args:
            rect: パネルの矩形
            parent: 親要素
            ui_manager: UIManager
            controller: コントローラ
            service: サービス
            data: 祈祷書データ
        """
        self.rect = rect
        self.parent = parent
        self.manager = ui_manager
        self.controller = controller
        self.service = service
        self.container = None
        
        self.available_spells = data.get("available_spells", [])
        self.categories = data.get("categories", [])
        self.party_gold = data.get("party_gold", 0)
        
        self.selected_spell = None
        self.spell_buttons = {}
        
        logger.info(f"PrayerShopPanel initialized with {len(self.available_spells)} spells")
    
    def _create_ui(self):
        """UI要素を作成"""
        
        # タイトル
        self.title_label = UILabel(
            relative_rect=pygame.Rect(20, 20, 360, 30),
            text="神聖魔法の祈祷書",
            manager=self.manager,
            container=self.parent
        )
        
        # 所持金表示
        self.gold_label = UILabel(
            relative_rect=pygame.Rect(20, 60, 200, 25),
            text=f"所持金: {self.party_gold} G",
            manager=self.manager,
            container=self.parent
        )
        
        # 祈祷書リスト（スクロール可能）
        self.scroll_container = UIScrollingContainer(
            relative_rect=pygame.Rect(20, 100, 360, 200),
            manager=self.manager,
            container=self.parent
        )
        
        # 祈祷書ボタンを作成
        self._create_spell_buttons()
        
        # 詳細表示エリア
        self.detail_label = UILabel(
            relative_rect=pygame.Rect(20, 320, 360, 80),
            text="祈祷書を選択してください",
            manager=self.manager,
            container=self.parent
        )
        
        # 購入ボタン
        self.buy_button = UIButton(
            relative_rect=pygame.Rect(20, 420, 120, 40),
            text="購入",
            manager=self.manager,
            container=self.parent
        )
        self.buy_button.disable()
        
        # 戻るボタン
        self.back_button = UIButton(
            relative_rect=pygame.Rect(260, 420, 120, 40),
            text="戻る",
            manager=self.manager,
            container=self.parent
        )
    
    def _create_spell_buttons(self):
        """祈祷書ボタンを作成"""
        y_offset = 0
        
        # カテゴリ別に分類
        categorized_spells = {}
        for spell in self.available_spells:
            category = spell.get("category", "other")
            if category not in categorized_spells:
                categorized_spells[category] = []
            categorized_spells[category].append(spell)
        
        # カテゴリごとに表示
        for category in self.categories:
            if category in categorized_spells:
                # カテゴリヘッダー
                category_names = {
                    "healing": "治癒系",
                    "blessing": "祝福系", 
                    "resurrection": "蘇生系",
                    "purification": "浄化系"
                }
                
                category_label = UILabel(
                    relative_rect=pygame.Rect(10, y_offset, 340, 25),
                    text=f"--- {category_names.get(category, category)} ---",
                    manager=self.manager,
                    container=self.scroll_container
                )
                y_offset += 35
                
                # スペルボタン
                for spell in categorized_spells[category]:
                    spell_button = UIButton(
                        relative_rect=pygame.Rect(10, y_offset, 320, 40),
                        text=f"{spell['name']} (Lv.{spell['level']}) - {spell['cost']} G",
                        manager=self.manager,
                        container=self.scroll_container
                    )
                    
                    # 購入可能かチェック
                    if spell['cost'] > self.party_gold:
                        spell_button.disable()
                    
                    self.spell_buttons[spell_button] = spell
                    y_offset += 50
                
                y_offset += 10  # カテゴリ間のスペース
        
        # スクロールエリアのサイズを調整
        self.scroll_container.set_scrollable_area_dimensions((340, y_offset))
    
    def handle_event(self, event) -> Optional[Dict[str, Any]]:
        """イベント処理"""
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            
            # 祈祷書選択ボタン
            for button, spell in self.spell_buttons.items():
                if event.ui_element == button:
                    self._select_spell(spell)
                    return None
            
            # 購入ボタン
            if event.ui_element == self.buy_button:
                if self.selected_spell:
                    return {
                        "action": "buy_spell",
                        "spell_id": self.selected_spell["id"],
                        "cost": self.selected_spell["cost"]
                    }
            
            # 戻るボタン
            elif event.ui_element == self.back_button:
                return {"action": "back"}
        
        return None
    
    def _select_spell(self, spell: Dict[str, Any]):
        """祈祷書を選択"""
        self.selected_spell = spell
        
        # 詳細表示を更新
        detail_text = (
            f"名前: {spell['name']}\n"
            f"レベル: {spell['level']}\n"
            f"費用: {spell['cost']} G\n"
            f"説明: {spell['description']}"
        )
        
        self.detail_label.set_text(detail_text)
        
        # 購入ボタンの状態更新
        if spell['cost'] <= self.party_gold:
            self.buy_button.enable()
        else:
            self.buy_button.disable()
        
        logger.info(f"Selected spell: {spell['name']}")
    
    def update_gold(self, new_gold: int):
        """所持金を更新"""
        self.party_gold = new_gold
        self.gold_label.set_text(f"所持金: {self.party_gold} G")
        
        # ボタンの有効/無効状態を更新
        for button, spell in self.spell_buttons.items():
            if spell['cost'] <= self.party_gold:
                button.enable()
            else:
                button.disable()
        
        # 購入ボタンの状態も更新
        if self.selected_spell and self.selected_spell['cost'] > self.party_gold:
            self.buy_button.disable()
    
    def destroy(self):
        """パネルを破棄"""
        # 作成したUI要素を削除
        elements_to_kill = [
            'title_label',
            'gold_label', 
            'scroll_container',
            'detail_label',
            'buy_button',
            'back_button'
        ]
        
        for element_name in elements_to_kill:
            if hasattr(self, element_name):
                element = getattr(self, element_name)
                if element and element.alive():
                    element.kill()
        
        # スペルボタンも削除
        for button in self.spell_buttons.keys():
            if button and button.alive():
                button.kill()
        
        self.spell_buttons.clear()
        
        logger.info("PrayerShopPanel destroyed")
    
    def show(self):
        """パネルを表示"""
        self._create_ui()
        
    def hide(self):
        """パネルを非表示"""
        self.destroy()