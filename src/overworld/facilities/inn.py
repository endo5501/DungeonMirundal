"""宿屋"""

from typing import Dict, List, Optional, Any
from src.overworld.base_facility import BaseFacility, FacilityType
from src.character.party import Party
from src.ui.base_ui import UIMenu, UIDialog, UIInputDialog, ui_manager
from src.core.config_manager import config_manager
from src.utils.logger import logger


class Inn(BaseFacility):
    """宿屋
    
    注意: このゲームでは地上部帰還時に自動回復するため、
    従来の宿屋での休息機能は提供しません。
    代わりに情報提供や雰囲気作りの場として機能します。
    """
    
    def __init__(self):
        super().__init__(
            facility_id="inn",
            facility_type=FacilityType.INN,
            name_key="facility.inn"
        )
    
    def _setup_menu_items(self, menu: UIMenu):
        """宿屋固有のメニュー項目を設定"""
        menu.add_menu_item(
            "宿屋の主人と話す",
            self._talk_to_innkeeper
        )
        
        menu.add_menu_item(
            "旅の情報を聞く",
            self._show_travel_info
        )
        
        menu.add_menu_item(
            "酒場の噂話",
            self._show_tavern_rumors
        )
        
        menu.add_menu_item(
            "パーティ名を変更",
            self._change_party_name
        )
    
    def _on_enter(self):
        """宿屋入場時の処理"""
        logger.info("宿屋に入りました")
        
        # 入場時のメッセージを表示
        welcome_message = (
            "「いらっしゃいませ！\n"
            "最近は皆さん、地上に戻るだけで\n"
            "すっかり元気になってしまうので、\n"
            "宿泊客が少なくて困っています。\n\n"
            "でも、旅の情報や噂話なら\n"
            "いくらでもお聞かせしますよ！」"
        )
        
        self._show_dialog(
            "inn_welcome_dialog",
            "宿屋の主人",
            welcome_message
        )
    
    def _on_exit(self):
        """宿屋退場時の処理"""
        logger.info("宿屋から出ました")
    
    def _talk_to_innkeeper(self):
        """宿屋の主人との会話"""
        messages = [
            (
                config_manager.get_text("inn.innkeeper.conversation.adventure_title"),
                config_manager.get_text("inn.innkeeper.conversation.adventure_message")
            ),
            (
                config_manager.get_text("inn.innkeeper.conversation.town_title"),
                config_manager.get_text("inn.innkeeper.conversation.town_message")
            ),
            (
                config_manager.get_text("inn.innkeeper.conversation.history_title"),
                config_manager.get_text("inn.innkeeper.conversation.history_message")
            )
        ]
        
        # ランダムにメッセージを選択
        import random
        title, message = random.choice(messages)
        
        self._show_dialog(
            "innkeeper_dialog",
            f"{config_manager.get_text('inn.innkeeper.title')} - {title}",
            message
        )
    
    def _show_travel_info(self):
        """旅の情報を表示"""
        travel_info = config_manager.get_text("inn.travel_info.content")
        
        self._show_dialog(
            "travel_info_dialog",
            config_manager.get_text("inn.travel_info.title"),
            travel_info
        )
    
    def _show_tavern_rumors(self):
        """酒場の噂話を表示"""
        rumors = [
            (
                config_manager.get_text("inn.rumors.dungeon_title"),
                config_manager.get_text("inn.rumors.dungeon_message")
            ),
            (
                config_manager.get_text("inn.rumors.monster_title"),
                config_manager.get_text("inn.rumors.monster_message")
            ),
            (
                config_manager.get_text("inn.rumors.legendary_title"),
                config_manager.get_text("inn.rumors.legendary_message")
            ),
            (
                config_manager.get_text("inn.rumors.adventurer_title"),
                config_manager.get_text("inn.rumors.adventurer_message")
            ),
            (
                config_manager.get_text("inn.rumors.merchant_title"),
                config_manager.get_text("inn.rumors.merchant_message")
            )
        ]
        
        # ランダムに噂を選択
        import random
        title, rumor = random.choice(rumors)
        
        self._show_dialog(
            "rumor_dialog",
            f"{config_manager.get_text('inn.rumors.title')} - {title}",
            rumor
        )
    
    def _change_party_name(self):
        """パーティ名変更機能"""
        if not self.current_party:
            self._show_dialog(
                "no_party_error_dialog",
                config_manager.get_text("inn.party_name.no_party_error_title"),
                config_manager.get_text("inn.party_name.no_party_error_message")
            )
            return
        
        # 現在のパーティ名を取得
        current_name = self.current_party.name if self.current_party.name else config_manager.get_text("inn.party_name.anonymous_party")
        
        # パーティ名変更ダイアログを表示
        name_input_dialog = UIInputDialog(
            "party_name_input_dialog",
            config_manager.get_text("inn.party_name.title"),
            f"{config_manager.get_text('inn.party_name.current_name_label').format(name=current_name)}\n\n"
            f"{config_manager.get_text('inn.party_name.input_prompt')}",
            initial_text=current_name,
            placeholder=config_manager.get_text("inn.party_name.placeholder"),
            on_confirm=self._on_party_name_confirmed,
            on_cancel=self._on_party_name_cancelled
        )
        
        ui_manager.register_element(name_input_dialog)
        ui_manager.show_element(name_input_dialog.element_id)
    
    def _on_party_name_confirmed(self, new_name: str):
        """パーティ名変更確認時の処理"""
        # 名前の検証と正規化
        validated_name = self._validate_party_name(new_name)
        
        if not validated_name:
            self._show_dialog(
                "invalid_name_dialog",
                config_manager.get_text("inn.party_name.invalid_name_title"),
                config_manager.get_text("inn.party_name.invalid_name_message")
            )
            return
        
        # パーティ名を更新
        old_name = self.current_party.name
        self.current_party.name = validated_name
        
        # 入力ダイアログを閉じる
        ui_manager.hide_element("party_name_input_dialog")
        ui_manager.unregister_element("party_name_input_dialog")
        
        # 成功メッセージを表示
        success_message = config_manager.get_text("inn.party_name.success_message").format(
            old_name=old_name,
            new_name=validated_name
        )
        
        self._show_dialog(
            "name_change_success_dialog",
            config_manager.get_text("inn.party_name.success_title"),
            success_message
        )
        
        logger.info(f"パーティ名を変更: {old_name} → {validated_name}")
    
    def _on_party_name_cancelled(self):
        """パーティ名変更キャンセル時の処理"""
        # 入力ダイアログを閉じる
        ui_manager.hide_element("party_name_input_dialog")
        ui_manager.unregister_element("party_name_input_dialog")
        
        logger.info("パーティ名変更がキャンセルされました")
    
    def _validate_party_name(self, name: str) -> str:
        """パーティ名のバリデーションと正規化"""
        if not name or not name.strip():
            return config_manager.get_text("inn.party_name.default_name")  # デフォルト名
        
        # 前後の空白を除去
        name = name.strip()
        
        # 長さ制限（30文字）
        if len(name) > 30:
            name = name[:30]
        
        # 危険な文字の除去（基本的なサニタイズ）
        dangerous_chars = ['<', '>', '&', '"', "'", '\n', '\r', '\t']
        for char in dangerous_chars:
            name = name.replace(char, '')
        
        # 空になった場合はデフォルト名
        if not name:
            return config_manager.get_text("inn.party_name.default_name")
        
        return name