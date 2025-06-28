"""魔法システム用ウィンドウ

Window Systemの魔法管理ウィンドウクラス。
旧MagicUIシステムからWindow Systemアーキテクチャへの移行。

t-wada式TDD実装：
1. 最小限の実装でテストを通す（Green段階）
2. 段階的に機能を追加
3. Fowlerリファクタリングパターンで改善
"""

from typing import Optional, Dict, List, Any, Callable
import pygame
from enum import Enum

from src.ui.window_system.window import Window
from src.ui.window_system.menu_window import MenuWindow
from src.ui.window_system.dialog_window import DialogWindow
from src.ui.window_system.magic_display_manager import MagicDisplayManager
from src.ui.window_system.spell_slot_manager import SpellSlotManager, SlotOperationResult
from src.character.party import Party
from src.character.character import Character
from src.magic.spells import SpellBook, Spell
from src.utils.logger import logger


class MagicWindowMode(Enum):
    """魔法ウィンドウ表示モード"""
    PARTY_OVERVIEW = "party_overview"
    CHARACTER_MAGIC = "character_magic"
    SPELL_SLOTS = "spell_slots"
    SPELL_USAGE = "spell_usage"
    LEARNED_SPELLS = "learned_spells"


class MagicWindow(Window):
    """魔法システム管理ウィンドウ
    
    Window Systemベースの魔法システムUI。
    パーティの魔法管理、スロット管理、魔法使用を統括。
    """
    
    def __init__(self, window_manager, rect: pygame.Rect, window_id: str = "magic_window", **kwargs):
        """MagicWindow初期化
        
        Args:
            window_manager: ウィンドウマネージャー
            rect: ウィンドウの矩形
            window_id: ウィンドウID
            **kwargs: その他のオプション
        """
        super().__init__(window_id, **kwargs)
        self.window_manager = window_manager
        self.rect = rect
        
        # 魔法システム状態
        self.party: Optional[Party] = None
        self.current_character: Optional[Character] = None
        self.current_spellbook: Optional[SpellBook] = None
        self.current_mode = MagicWindowMode.PARTY_OVERVIEW
        
        # 選択状態
        self.selected_level: Optional[int] = None
        self.selected_slot_index: Optional[int] = None
        
        # コールバック
        self.on_close_callback: Optional[Callable] = None
        
        # Fowler Extract Classパターン: 責任の分離
        self.display_manager = MagicDisplayManager()
        self.slot_manager = SpellSlotManager()
        
        # スロット操作のコールバック設定
        self._setup_slot_callbacks()
        
        logger.info("MagicWindowを初期化しました（リファクタリング済み）")
    
    def create(self) -> None:
        """UI要素を作成（Window抽象メソッドの実装）"""
        # 最小限の実装でテストを通す
        logger.debug("MagicWindow UI要素を作成しました")
    
    def _setup_slot_callbacks(self) -> None:
        """スロット操作のコールバックを設定"""
        from src.ui.window_system.spell_slot_manager import SlotOperation
        
        # 各スロット操作にコールバックを設定
        self.slot_manager.add_operation_callback(
            SlotOperation.EQUIP, 
            self._on_spell_equipped
        )
        self.slot_manager.add_operation_callback(
            SlotOperation.UNEQUIP, 
            self._on_spell_unequipped
        )
        self.slot_manager.add_operation_callback(
            SlotOperation.USE, 
            self._on_spell_used
        )
    
    def _on_spell_equipped(self, data: Dict[str, Any]) -> None:
        """魔法装備時のコールバック"""
        logger.info(f"魔法が装備されました: {data}")
    
    def _on_spell_unequipped(self, data: Dict[str, Any]) -> None:
        """魔法装備解除時のコールバック"""
        logger.info(f"魔法の装備が解除されました: {data}")
    
    def _on_spell_used(self, data: Dict[str, Any]) -> None:
        """魔法使用時のコールバック"""
        logger.info(f"魔法が使用されました: {data}")
    
    def set_party(self, party: Party) -> None:
        """パーティを設定
        
        Args:
            party: 設定するパーティ
        """
        self.party = party
        logger.debug(f"MagicWindowにパーティを設定: {party.name if party else None}")
    
    def show_party_magic_menu(self, party: Party) -> None:
        """パーティ魔法メニューを表示
        
        Args:
            party: 表示対象のパーティ
        """
        if party is None:
            logger.warning("パーティがNoneのため、魔法メニューを表示できません")
            return
        
        self.set_party(party)
        self.current_mode = MagicWindowMode.PARTY_OVERVIEW
        
        # ウィンドウマネージャーでウィンドウを表示
        if self.window_manager:
            self.window_manager.show_window(self)
        
        logger.info("パーティ魔法メニューを表示しました")
    
    def show_character_magic(self, character: Character) -> None:
        """キャラクター魔法画面を表示
        
        Args:
            character: 表示対象のキャラクター
        """
        if character is None:
            logger.warning("キャラクターがNoneのため、魔法画面を表示できません")
            return
        
        self.current_character = character
        self.current_spellbook = character.get_spellbook()
        self.current_mode = MagicWindowMode.CHARACTER_MAGIC
        
        logger.info(f"{character.name}の魔法画面を表示しました")
    
    def show_spell_slots(self, character: Character) -> None:
        """魔法スロット管理画面を表示
        
        Args:
            character: 対象キャラクター
        """
        if character is None:
            logger.warning("キャラクターがNoneのため、スロット画面を表示できません")
            return
        
        self.current_character = character
        self.current_spellbook = character.get_spellbook()
        self.current_mode = MagicWindowMode.SPELL_SLOTS
        
        # 魔法書の取得を確認
        if self.current_spellbook:
            logger.info(f"{character.name}の魔法スロット管理画面を表示しました")
        else:
            logger.warning(f"{character.name}の魔法書が取得できませんでした")
    
    def show_confirmation_dialog(self, message: str, on_confirm: Optional[Callable] = None,
                               on_cancel: Optional[Callable] = None) -> None:
        """確認ダイアログを表示
        
        Args:
            message: 確認メッセージ
            on_confirm: 確認時のコールバック
            on_cancel: キャンセル時のコールバック
        """
        # DialogWindowを使用して確認ダイアログを表示
        # 実装は段階的に追加
        logger.info(f"確認ダイアログを表示: {message}")
    
    def get_party_magic_summary(self) -> List[Dict[str, Any]]:
        """パーティ魔法サマリーを取得（リファクタリング済み）
        
        Extract Classにより、表示フォーマット処理をMagicDisplayManagerに委譲。
        
        Returns:
            List[Dict]: フォーマット済みサマリー
        """
        if not self.party:
            return []
        
        return self.display_manager.format_party_magic_summary(self.party)
    
    def get_character_spell_slots(self, character: Character) -> Dict[int, List[Dict[str, Any]]]:
        """キャラクターの魔法スロット情報を取得（リファクタリング済み）
        
        Args:
            character: 対象キャラクター
            
        Returns:
            Dict: レベル別スロット情報
        """
        return self.display_manager.format_character_spell_slots(character)
    
    def equip_spell_to_slot(self, character: Character, spell_id: str, 
                           level: int, slot_index: int) -> SlotOperationResult:
        """魔法をスロットに装備（リファクタリング済み）
        
        Extract Classにより、スロット操作をSpellSlotManagerに委譲。
        
        Args:
            character: 対象キャラクター
            spell_id: 魔法ID
            level: スロットレベル
            slot_index: スロットインデックス
            
        Returns:
            SlotOperationResult: 操作結果
        """
        return self.slot_manager.equip_spell_to_slot(character, spell_id, level, slot_index)
    
    def unequip_spell_from_slot(self, character: Character, 
                              level: int, slot_index: int) -> SlotOperationResult:
        """スロットから魔法を装備解除（リファクタリング済み）
        
        Args:
            character: 対象キャラクター
            level: スロットレベル
            slot_index: スロットインデックス
            
        Returns:
            SlotOperationResult: 操作結果
        """
        return self.slot_manager.unequip_spell_from_slot(character, level, slot_index)
    
    def get_party_magic_statistics(self) -> Dict[str, Any]:
        """パーティ魔法統計を取得（リファクタリング済み）
        
        Returns:
            Dict: 統計情報
        """
        if not self.party:
            return {}
        
        return self.display_manager.format_party_magic_statistics(self.party)
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """イベント処理
        
        Args:
            event: Pygameイベント
            
        Returns:
            bool: イベントが処理された場合True
        """
        # 基本的なイベント処理
        handled = super().handle_event(event)
        
        if handled:
            return True
        
        # 魔法ウィンドウ固有のイベント処理
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.close()
                return True
        
        return False
    
    def update(self, delta_time: float) -> None:
        """ウィンドウ更新
        
        Args:
            delta_time: 前フレームからの経過時間
        """
        super().update(delta_time)
        
        # 魔法ウィンドウ固有の更新処理
        # 実装は段階的に追加
    
    def render(self, surface: pygame.Surface) -> None:
        """ウィンドウ描画
        
        Args:
            surface: 描画対象サーフェス
        """
        super().render(surface)
        
        # 魔法ウィンドウ固有の描画処理
        # 実装は段階的に追加
        
        # デバッグ情報を表示
        if self.party:
            font = pygame.font.Font(None, 24)
            text = font.render(f"魔法システム - {self.current_mode.value}", True, (255, 255, 255))
            surface.blit(text, (self.rect.x + 10, self.rect.y + 10))
    
    def close(self) -> None:
        """ウィンドウを閉じる"""
        if self.on_close_callback:
            self.on_close_callback()
        
        if self.window_manager:
            self.window_manager.hide_window(self)
        
        logger.info("MagicWindowを閉じました")