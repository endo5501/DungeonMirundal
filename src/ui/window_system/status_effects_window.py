"""ステータス効果管理用ウィンドウ

Window Systemのステータス効果管理ウィンドウクラス。
旧StatusEffectsUIシステムからWindow Systemアーキテクチャへの移行。

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
from src.ui.window_system.status_effect_manager import StatusEffectManager
from src.ui.window_system.status_display_manager import StatusDisplayManager, DisplayMode
from src.ui.window_system.effect_action_manager import EffectActionManager, ActionType
from src.utils.logger import logger


class StatusEffectsWindow(Window):
    """ステータス効果管理ウィンドウ
    
    Window Systemベースのステータス効果管理UI。
    パーティ効果表示、個別キャラクター効果、効果詳細、効果解除を統括。
    """
    
    def __init__(self, window_manager, rect: pygame.Rect, window_id: str = "status_effects_window", **kwargs):
        """StatusEffectsWindow初期化
        
        Args:
            window_manager: ウィンドウマネージャー
            rect: ウィンドウの矩形
            window_id: ウィンドウID
            **kwargs: その他のオプション
        """
        super().__init__(window_id, **kwargs)
        self.window_manager = window_manager
        self.rect = rect
        
        # ステータス効果システム状態
        self.party_effects: Dict[str, Any] = {}
        self.current_character: Optional[Any] = None
        self.current_effect: Optional[Dict[str, Any]] = None
        
        # コールバック
        self.on_close_callback: Optional[Callable] = None
        
        # Fowler Extract Classパターン: 責任の分離
        self.effect_manager = StatusEffectManager()
        self.display_manager = StatusDisplayManager()
        self.action_manager = EffectActionManager()
        
        # アクションコールバックの設定
        self._setup_action_callbacks()
        
        logger.info("StatusEffectsWindowを初期化しました（リファクタリング済み）")
    
    def create(self) -> None:
        """UI要素を作成（Window抽象メソッドの実装）"""
        # 最小限の実装でテストを通す
        logger.debug("StatusEffectsWindow UI要素を作成しました")
    
    def _setup_action_callbacks(self) -> None:
        """アクションコールバックを設定"""
        # 効果除去時のコールバック
        self.action_manager.add_action_callback(
            ActionType.REMOVE_EFFECT,
            self._on_effect_removed
        )
        
        # 一括除去時のコールバック
        self.action_manager.add_action_callback(
            ActionType.CLEANSE_DEBUFFS,
            self._on_effects_cleansed
        )
    
    def _on_effect_removed(self, callback_data: Dict[str, Any]) -> None:
        """効果除去時のコールバック"""
        character = callback_data.get('character')
        effect = callback_data.get('effect')
        char_name = getattr(character, 'name', 'Unknown') if character else 'Unknown'
        effect_name = effect.get('name', 'Unknown') if effect else 'Unknown'
        logger.info(f"効果除去完了: {effect_name} from {char_name}")
    
    def _on_effects_cleansed(self, callback_data: Dict[str, Any]) -> None:
        """一括除去時のコールバック"""
        character = callback_data.get('character')
        removed_effects = callback_data.get('removed_effects', [])
        char_name = getattr(character, 'name', 'Unknown') if character else 'Unknown'
        logger.info(f"デバフ一括除去完了: {len(removed_effects)}個 from {char_name}")
    
    def show_party_effects(self, party) -> None:
        """パーティ効果を表示
        
        Args:
            party: パーティオブジェクト
        """
        if party is None:
            logger.warning("パーティがNoneです")
            return
        
        # ウィンドウマネージャーでウィンドウを表示
        if self.window_manager:
            self.window_manager.show_window(self)
        
        logger.info("パーティ効果を表示しました")
    
    def show_character_effects(self, character) -> None:
        """キャラクター効果を表示
        
        Args:
            character: キャラクターオブジェクト
        """
        self.current_character = character
        logger.info(f"キャラクター効果を表示: {getattr(character, 'name', 'Unknown') if character else 'None'}")
    
    def show_effect_details(self, effect: Optional[Dict[str, Any]]) -> None:
        """効果詳細を表示
        
        Args:
            effect: 効果データ
        """
        if effect is None:
            logger.warning("効果データがNoneです")
            return
        
        self.current_effect = effect
        logger.info(f"効果詳細を表示: {effect.get('name', 'Unknown')}")
    
    def remove_effect(self, character, effect: Dict[str, Any]) -> bool:
        """効果を除去（リファクタリング済み）
        
        Args:
            character: キャラクターオブジェクト
            effect: 除去する効果
            
        Returns:
            bool: 除去成功の場合True
        """
        # アクション管理に委譲
        result = self.action_manager.remove_effect(character, effect)
        return result.success
    
    def get_party_effect_summary(self, party) -> Dict[str, Any]:
        """パーティ効果サマリーを取得（リファクタリング済み）
        
        Args:
            party: パーティオブジェクト
            
        Returns:
            Dict: 効果サマリー
        """
        # 効果管理に委譲
        return self.effect_manager.get_party_effect_summary(party)
    
    def get_effect_statistics(self, party) -> Dict[str, Any]:
        """効果統計を取得（リファクタリング済み）
        
        Args:
            party: パーティオブジェクト
            
        Returns:
            Dict: 効果統計
        """
        # 効果管理に委譲
        return self.effect_manager.get_effect_statistics(party)
    
    def filter_removable_effects(self, effects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """除去可能な効果をフィルタリング（リファクタリング済み）
        
        Args:
            effects: 効果リスト
            
        Returns:
            List: 除去可能な効果リスト
        """
        # アクション管理に委譲
        return self.action_manager.filter_removable_effects(effects)
    
    def show_effect_details_dialog(self, effect: Dict[str, Any]) -> None:
        """効果詳細ダイアログを表示
        
        Args:
            effect: 効果データ
        """
        # DialogWindowを使用して詳細を表示
        # 実装は段階的に追加
        logger.info(f"効果詳細ダイアログを表示: {effect.get('name', 'Unknown')}")
    
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
        
        # ステータス効果ウィンドウ固有のイベント処理
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.close()
                return True
            elif event.key == pygame.K_v:
                # Vキーでステータス効果を切り替え
                logger.info("ステータス効果ビューを切り替え")
                return True
        
        return False
    
    def update(self, delta_time: float) -> None:
        """ウィンドウ更新
        
        Args:
            delta_time: 前フレームからの経過時間
        """
        super().update(delta_time)
        
        # ステータス効果ウィンドウ固有の更新処理
        # 実装は段階的に追加
    
    def render(self, surface: pygame.Surface) -> None:
        """ウィンドウ描画
        
        Args:
            surface: 描画対象サーフェス
        """
        super().render(surface)
        
        # ステータス効果ウィンドウ固有の描画処理
        # 実装は段階的に追加
        
        # デバッグ情報を表示
        font = pygame.font.Font(None, 24)
        text = font.render("ステータス効果システム", True, (255, 255, 255))
        surface.blit(text, (self.rect.x + 10, self.rect.y + 10))
        
        if self.current_character:
            char_name = getattr(self.current_character, 'name', 'Unknown')
            char_text = font.render(f"キャラクター: {char_name}", True, (200, 200, 200))
            surface.blit(char_text, (self.rect.x + 10, self.rect.y + 40))
        
        if self.current_effect:
            effect_text = font.render(f"効果: {self.current_effect.get('name', 'Unknown')}", True, (200, 200, 200))
            surface.blit(effect_text, (self.rect.x + 10, self.rect.y + 70))
    
    def close(self) -> None:
        """ウィンドウを閉じる"""
        if self.on_close_callback:
            self.on_close_callback()
        
        if self.window_manager:
            self.window_manager.hide_window(self)
        
        logger.info("StatusEffectsWindowを閉じました")
    
    # リファクタリング後のメソッド（テスト用）
    def format_effect_list(self, effects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """効果リストをフォーマット（リファクタリング済み）
        
        Args:
            effects: 効果リスト
            
        Returns:
            List: フォーマット済み効果リスト
        """
        # 表示管理に委譲
        return self.display_manager.format_effect_list(effects, DisplayMode.LIST)
    
    def get_effect_menu_items(self, party) -> List[Dict[str, Any]]:
        """効果メニューアイテムを取得（リファクタリング済み）
        
        Args:
            party: パーティオブジェクト
            
        Returns:
            List: メニューアイテムリスト
        """
        # 表示管理に委譲
        return self.display_manager.get_effect_menu_items(party)