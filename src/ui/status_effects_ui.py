"""ステータス効果表示UI（WindowSystem統合版）"""

from typing import Dict, List, Optional, Any, Callable
from enum import Enum
import pygame

from src.ui.window_system import WindowManager
from src.ui.window_system.status_effects_window import StatusEffectsWindow
from src.effects.status_effects import StatusEffectType, status_effect_manager
from src.character.party import Party
from src.character.character import Character
from src.core.config_manager import config_manager
from src.utils.logger import logger


class StatusEffectsUI:
    """ステータス効果表示UI管理クラス（WindowSystem統合版）"""
    
    def __init__(self):
        self.current_party: Optional[Party] = None
        self.current_character: Optional[Character] = None
        
        # UI状態
        self.is_open = False
        self.callback_on_close: Optional[Callable] = None
        
        # WindowSystem統合
        self.window_manager = WindowManager.get_instance()
        self.status_effects_window: Optional[StatusEffectsWindow] = None
        
        logger.info("StatusEffectsUI（WindowSystem版）を初期化しました")
    
    def _get_status_effects_window(self) -> StatusEffectsWindow:
        """StatusEffectsWindowインスタンスを取得または作成"""
        if self.status_effects_window is None:
            # StatusEffectsWindowの初期化
            self.status_effects_window = StatusEffectsWindow(
                window_id="status_effects_main",
                title="ステータス効果"
            )
        return self.status_effects_window
    
    def set_party(self, party: Party):
        """パーティを設定"""
        self.current_party = party
        if self.status_effects_window:
            self.status_effects_window.set_party(party)
        logger.debug(f"パーティを設定: {party.name if party else None}")
    
    def set_character(self, character: Character):
        """キャラクターを設定"""
        self.current_character = character
        if self.status_effects_window:
            self.status_effects_window.set_character(character)
        logger.debug(f"キャラクターを設定: {character.name if character else None}")
    
    def show_party_status_effects(self):
        """パーティ全体のステータス効果を表示（WindowSystem版）"""
        try:
            status_window = self._get_status_effects_window()
            if self.current_party:
                status_window.set_party(self.current_party)
            
            status_window.show_party_status_effects()
            self.is_open = True
            logger.info("パーティステータス効果を表示（WindowSystem版）")
        except Exception as e:
            logger.error(f"パーティステータス効果表示エラー: {e}")
    
    def show_character_status_effects(self, character: Character):
        """キャラクター個別のステータス効果を表示（WindowSystem版）"""
        try:
            self.set_character(character)
            status_window = self._get_status_effects_window()
            status_window.show_character_status_effects(character)
            self.is_open = True
            logger.info(f"キャラクターステータス効果を表示: {character.name}")
        except Exception as e:
            logger.error(f"キャラクターステータス効果表示エラー: {e}")
    
    def show_status_effect_detail(self, effect_type: StatusEffectType, character: Character):
        """ステータス効果詳細を表示（WindowSystem版）"""
        try:
            status_window = self._get_status_effects_window()
            status_window.show_status_effect_detail(effect_type, character)
            logger.info(f"ステータス効果詳細を表示: {effect_type.value} - {character.name}")
        except Exception as e:
            logger.error(f"ステータス効果詳細表示エラー: {e}")
    
    def show_active_effects_summary(self):
        """アクティブ効果概要を表示（WindowSystem版）"""
        try:
            status_window = self._get_status_effects_window()
            if self.current_party:
                status_window.set_party(self.current_party)
            
            status_window.show_active_effects_summary()
            self.is_open = True
            logger.info("アクティブ効果概要を表示")
        except Exception as e:
            logger.error(f"アクティブ効果概要表示エラー: {e}")
    
    def show_status_management_menu(self):
        """ステータス効果管理メニューを表示（WindowSystem版）"""
        try:
            status_window = self._get_status_effects_window()
            if self.current_party:
                status_window.set_party(self.current_party)
            
            status_window.show_management_menu()
            self.is_open = True
            logger.info("ステータス効果管理メニューを表示")
        except Exception as e:
            logger.error(f"ステータス効果管理メニュー表示エラー: {e}")
    
    def apply_status_effect(self, effect_type: StatusEffectType, character: Character):
        """ステータス効果を適用（WindowSystem版）"""
        try:
            status_window = self._get_status_effects_window()
            success = status_window.apply_status_effect(effect_type, character)
            if success:
                logger.info(f"ステータス効果を適用: {effect_type.value} -> {character.name}")
            return success
        except Exception as e:
            logger.error(f"ステータス効果適用エラー: {e}")
            return False
    
    def remove_status_effect(self, effect_type: StatusEffectType, character: Character):
        """ステータス効果を除去（WindowSystem版）"""
        try:
            status_window = self._get_status_effects_window()
            success = status_window.remove_status_effect(effect_type, character)
            if success:
                logger.info(f"ステータス効果を除去: {effect_type.value} -> {character.name}")
            return success
        except Exception as e:
            logger.error(f"ステータス効果除去エラー: {e}")
            return False
    
    def get_character_active_effects(self, character: Character) -> List[StatusEffectType]:
        """キャラクターのアクティブ効果を取得"""
        try:
            if hasattr(character, 'get_status_effects'):
                status_effects = character.get_status_effects()
                return list(status_effects.active_effects.keys())
            return []
        except Exception as e:
            logger.error(f"アクティブ効果取得エラー: {e}")
            return []
    
    def get_party_effects_summary(self) -> Dict[str, List[StatusEffectType]]:
        """パーティ全体の効果概要を取得"""
        try:
            if not self.current_party:
                return {}
            
            summary = {}
            for character in self.current_party.get_all_characters():
                summary[character.name] = self.get_character_active_effects(character)
            return summary
        except Exception as e:
            logger.error(f"パーティ効果概要取得エラー: {e}")
            return {}
    
    def hide(self):
        """ステータス効果UIを非表示（WindowSystem版）"""
        try:
            if self.status_effects_window:
                self.status_effects_window.close()
            self.is_open = False
            logger.info("ステータス効果UIを非表示")
        except Exception as e:
            logger.error(f"ステータス効果UI非表示エラー: {e}")
    
    def show(self):
        """ステータス効果UIを表示（パーティ概要）"""
        self.show_party_status_effects()
    
    def set_callback_on_close(self, callback: Callable):
        """クローズ時コールバックを設定"""
        self.callback_on_close = callback
    
    def cleanup(self):
        """リソースクリーンアップ"""
        if self.status_effects_window:
            self.status_effects_window.cleanup()
            self.status_effects_window = None
        self.is_open = False
        self.current_party = None
        self.current_character = None
        logger.info("StatusEffectsUIリソースをクリーンアップしました")


# グローバルインスタンス（互換性のため）
status_effects_ui = StatusEffectsUI()