"""魔法管理UIシステム（WindowSystem統合版）"""

from typing import Optional, Callable
from enum import Enum

from src.ui.window_system import WindowManager
from src.ui.window_system.magic_window import MagicWindow
from src.magic.spells import SpellBook, Spell
from src.character.party import Party
from src.character.character import Character
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
        
        logger.debug("MagicUI（WindowSystem版）を初期化しました")
    
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
    
    def _show_magic_interface(self, interface_type: str, mode: MagicUIMode, log_message: str):
        """魔法インターフェース表示の共通実装"""
        try:
            magic_window = self._get_magic_window()
            
            # インターフェースタイプに応じた処理を実行
            interface_methods = {
                'spellbook': magic_window.show_spellbook_management,
                'slot': magic_window.show_slot_management,
                'learning': magic_window.show_spell_learning,
                'casting': magic_window.show_spell_casting,
                'overview': magic_window.show_party_overview
            }
            
            if interface_type in interface_methods:
                interface_methods[interface_type]()
                self.current_mode = mode
                logger.info(log_message)
            else:
                logger.error(f"未知のインターフェースタイプ: {interface_type}")
                
        except Exception as e:
            logger.error(f"{log_message}エラー: {e}")
    
    def show_spellbook_management(self):
        """魔法書管理を表示（WindowSystem版）"""
        self._show_magic_interface('spellbook', MagicUIMode.SPELLBOOK, "魔法書管理を表示")
    
    def show_slot_management(self):
        """スロット管理を表示（WindowSystem版）"""
        self._show_magic_interface('slot', MagicUIMode.SLOT_MANAGEMENT, "スロット管理を表示")
    
    def show_spell_learning(self):
        """魔法習得を表示（WindowSystem版）"""
        self._show_magic_interface('learning', MagicUIMode.SPELL_LEARNING, "魔法習得を表示")
    
    def show_spell_casting(self):
        """魔法詠唱を表示（WindowSystem版）"""
        self._show_magic_interface('casting', MagicUIMode.SPELL_CASTING, "魔法詠唱を表示")
    
    def show_party_magic_overview(self):
        """パーティ魔法概要を表示（WindowSystem版）"""
        self._show_magic_interface('overview', MagicUIMode.OVERVIEW, "パーティ魔法概要を表示")
    
    def show_character_magic_detail(self, character: Character):
        """キャラクター魔法詳細を表示（WindowSystem版）"""
        try:
            self.set_character(character)
            magic_window = self._get_magic_window()
            magic_window.show_character_detail(character)
            logger.info(f"キャラクター魔法詳細を表示: {character.name}")
        except Exception as e:
            logger.error(f"キャラクター魔法詳細表示エラー: {e}")
    
    def _execute_slot_operation(self, operation_type: str, slot_index: int, spell: Optional[Spell] = None) -> bool:
        """スロット操作の共通実装"""
        try:
            if not self.current_character:
                logger.warning("キャラクターが設定されていません")
                return False
            
            magic_window = self._get_magic_window()
            
            if operation_type == 'equip':
                if spell is None:
                    logger.error("装備操作には魔法が必要です")
                    return False
                success = magic_window.equip_spell_to_slot(spell, slot_index)
                if success:
                    logger.info(f"魔法をスロットに装備: {spell.name} -> スロット{slot_index}")
            elif operation_type == 'unequip':
                success = magic_window.unequip_spell_from_slot(slot_index)
                if success:
                    logger.info(f"スロットから魔法を外しました: スロット{slot_index}")
            else:
                logger.error(f"未知のスロット操作: {operation_type}")
                return False
                
            return success
            
        except Exception as e:
            logger.error(f"スロット操作エラー({operation_type}): {e}")
            return False
    
    def equip_spell_to_slot(self, spell: Spell, slot_index: int):
        """魔法をスロットに装備（WindowSystem版）"""
        return self._execute_slot_operation('equip', slot_index, spell)
    
    def unequip_spell_from_slot(self, slot_index: int):
        """スロットから魔法を外す（WindowSystem版）"""
        return self._execute_slot_operation('unequip', slot_index)
    
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