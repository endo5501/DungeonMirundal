"""魔法管理UIシステム（WindowSystem統合版）"""

from typing import Dict, List, Optional, Any, Tuple, Callable
from enum import Enum
import pygame

from src.ui.window_system import WindowManager
from src.ui.window_system.magic_window import MagicWindow
from src.magic.spells import SpellBook, SpellSlot, Spell, SpellManager, spell_manager, SpellSchool, SpellType
from src.character.party import Party
from src.character.character import Character
from src.core.config_manager import config_manager
from src.utils.logger import logger


class MagicUIMode(Enum):
    """魔法UI表示モード"""
    OVERVIEW = "overview"               # 魔法概要
    SPELLBOOK = "spellbook"            # 魔法書管理
    SLOT_MANAGEMENT = "slot_management" # スロット管理
    SPELL_LEARNING = "spell_learning"   # 魔法習得
    SPELL_CASTING = "spell_casting"     # 魔法詠唱


class MagicUI:
    """魔法UI管理クラス（WindowSystem統合版）"""
    
    def __init__(self):
        self.current_party: Optional[Party] = None
        self.current_character: Optional[Character] = None
        self.current_spellbook: Optional[SpellBook] = None
        self.current_mode = MagicUIMode.OVERVIEW
        
        # UI状態
        self.is_open = False
        self.callback_on_close: Optional[Callable] = None
        
        # WindowSystem統合
        self.window_manager = WindowManager.get_instance()
        self.magic_window: Optional[MagicWindow] = None
        
        logger.info("MagicUI（WindowSystem版）を初期化しました")
    
    def _get_magic_window(self) -> MagicWindow:
        """MagicWindowインスタンスを取得または作成"""
        if self.magic_window is None:
            # MagicWindowの初期化
            self.magic_window = MagicWindow(
                window_id="magic_main",
                title="魔法管理"
            )
        return self.magic_window
    
    def set_party(self, party: Party):
        """パーティを設定"""
        self.current_party = party
        if self.magic_window:
            self.magic_window.set_party(party)
        logger.debug(f"パーティを設定: {party.name if party else None}")
    
    def set_character(self, character: Character):
        """キャラクターを設定"""
        self.current_character = character
        if self.magic_window:
            self.magic_window.set_character(character)
        logger.debug(f"キャラクターを設定: {character.name if character else None}")
    
    def show_magic_menu(self):
        """魔法メインメニューを表示（WindowSystem版）"""
        try:
            magic_window = self._get_magic_window()
            if self.current_party:
                magic_window.set_party(self.current_party)
            if self.current_character:
                magic_window.set_character(self.current_character)
            
            magic_window.show_main_menu()
            self.is_open = True
            logger.info("魔法メニューを表示（WindowSystem版）")
        except Exception as e:
            logger.error(f"魔法メニュー表示エラー: {e}")
    
    def show_spellbook_management(self):
        """魔法書管理を表示（WindowSystem版）"""
        try:
            magic_window = self._get_magic_window()
            magic_window.show_spellbook_management()
            self.current_mode = MagicUIMode.SPELLBOOK
            logger.info("魔法書管理を表示")
        except Exception as e:
            logger.error(f"魔法書管理表示エラー: {e}")
    
    def show_slot_management(self):
        """スロット管理を表示（WindowSystem版）"""
        try:
            magic_window = self._get_magic_window()
            magic_window.show_slot_management()
            self.current_mode = MagicUIMode.SLOT_MANAGEMENT
            logger.info("スロット管理を表示")
        except Exception as e:
            logger.error(f"スロット管理表示エラー: {e}")
    
    def show_spell_learning(self):
        """魔法習得を表示（WindowSystem版）"""
        try:
            magic_window = self._get_magic_window()
            magic_window.show_spell_learning()
            self.current_mode = MagicUIMode.SPELL_LEARNING
            logger.info("魔法習得を表示")
        except Exception as e:
            logger.error(f"魔法習得表示エラー: {e}")
    
    def show_spell_casting(self):
        """魔法詠唱を表示（WindowSystem版）"""
        try:
            magic_window = self._get_magic_window()
            magic_window.show_spell_casting()
            self.current_mode = MagicUIMode.SPELL_CASTING
            logger.info("魔法詠唱を表示")
        except Exception as e:
            logger.error(f"魔法詠唱表示エラー: {e}")
    
    def show_party_magic_overview(self):
        """パーティ魔法概要を表示（WindowSystem版）"""
        try:
            magic_window = self._get_magic_window()
            magic_window.show_party_overview()
            self.current_mode = MagicUIMode.OVERVIEW
            logger.info("パーティ魔法概要を表示")
        except Exception as e:
            logger.error(f"パーティ魔法概要表示エラー: {e}")
    
    def show_character_magic_detail(self, character: Character):
        """キャラクター魔法詳細を表示（WindowSystem版）"""
        try:
            self.set_character(character)
            magic_window = self._get_magic_window()
            magic_window.show_character_detail(character)
            logger.info(f"キャラクター魔法詳細を表示: {character.name}")
        except Exception as e:
            logger.error(f"キャラクター魔法詳細表示エラー: {e}")
    
    def equip_spell_to_slot(self, spell: Spell, slot_index: int):
        """魔法をスロットに装備（WindowSystem版）"""
        try:
            if not self.current_character:
                logger.warning("キャラクターが設定されていません")
                return False
            
            magic_window = self._get_magic_window()
            success = magic_window.equip_spell_to_slot(spell, slot_index)
            if success:
                logger.info(f"魔法をスロットに装備: {spell.name} -> スロット{slot_index}")
            return success
        except Exception as e:
            logger.error(f"魔法装備エラー: {e}")
            return False
    
    def unequip_spell_from_slot(self, slot_index: int):
        """スロットから魔法を外す（WindowSystem版）"""
        try:
            if not self.current_character:
                logger.warning("キャラクターが設定されていません")
                return False
            
            magic_window = self._get_magic_window()
            success = magic_window.unequip_spell_from_slot(slot_index)
            if success:
                logger.info(f"スロットから魔法を外しました: スロット{slot_index}")
            return success
        except Exception as e:
            logger.error(f"魔法装備解除エラー: {e}")
            return False
    
    def hide(self):
        """魔法UIを非表示（WindowSystem版）"""
        try:
            if self.magic_window:
                self.magic_window.close()
            self.is_open = False
            logger.info("魔法UIを非表示")
        except Exception as e:
            logger.error(f"魔法UI非表示エラー: {e}")
    
    def show(self):
        """魔法UIを表示（メインメニュー）"""
        self.show_magic_menu()
    
    def set_callback_on_close(self, callback: Callable):
        """クローズ時コールバックを設定"""
        self.callback_on_close = callback
    
    def cleanup(self):
        """リソースクリーンアップ"""
        if self.magic_window:
            self.magic_window.cleanup()
            self.magic_window = None
        self.is_open = False
        self.current_party = None
        self.current_character = None
        self.current_spellbook = None
        logger.info("MagicUIリソースをクリーンアップしました")


# グローバルインスタンス（互換性のため）
magic_ui = MagicUI()