"""メニュースタック管理システム

統一されたメニュー階層管理とナビゲーション処理を提供します。
"""

from typing import List, Optional, Dict, Any, Callable
from enum import Enum
import pygame
from src.ui.base_ui_pygame import UIMenu, UIElement, UIState
from src.utils.logger import logger


class MenuType(Enum):
    """メニュータイプ"""
    ROOT = "root"                    # 地上マップ（最上位）
    FACILITY_MAIN = "facility_main"  # 施設メインメニュー
    SUBMENU = "submenu"             # サブメニュー
    DIALOG = "dialog"               # ダイアログ
    SETTINGS = "settings"           # 設定画面


class MenuStackEntry:
    """メニュースタックエントリ"""
    
    def __init__(self, menu: UIMenu, menu_type: MenuType, context: Dict[str, Any] = None):
        self.menu = menu
        self.menu_type = menu_type
        self.context = context or {}
        self.timestamp = pygame.time.get_ticks()
        self.parent_entry: Optional['MenuStackEntry'] = None
        
    def __repr__(self):
        return f"MenuStackEntry({self.menu.menu_id}, {self.menu_type.value})"


class MenuStackManager:
    """メニュースタック管理クラス
    
    メニュー階層の管理、戻る処理の統一、ESCキー処理を担当。
    """
    
    def __init__(self, ui_manager):
        self.ui_manager = ui_manager
        self.stack: List[MenuStackEntry] = []
        self.current_entry: Optional[MenuStackEntry] = None
        
        # コールバック
        self.on_menu_changed: Optional[Callable] = None
        self.on_escape_pressed: Optional[Callable] = None
        
        # 状態管理
        self.is_transition_in_progress = False
        self.max_stack_size = 20  # スタックサイズ制限
        
        logger.info("MenuStackManagerを初期化しました")
    
    def push_menu(self, menu: UIMenu, menu_type: MenuType, context: Dict[str, Any] = None) -> bool:
        """メニューをスタックにプッシュして表示
        
        Args:
            menu: 表示するメニュー
            menu_type: メニューのタイプ
            context: メニューに関連するコンテキスト情報
            
        Returns:
            bool: 成功した場合True
        """
        try:
            if self.is_transition_in_progress:
                logger.warning("メニュー遷移中のため、プッシュ操作をスキップしました")
                return False
            
            self.is_transition_in_progress = True
            
            # スタックサイズ制限チェック
            if len(self.stack) >= self.max_stack_size:
                logger.warning(f"メニュースタックサイズが上限に達しました: {self.max_stack_size}")
                # 古いエントリを削除
                old_entry = self.stack.pop(0)
                self._cleanup_menu_entry(old_entry)
            
            # 現在のメニューを隠す
            if self.current_entry:
                self._hide_current_menu()
                # 親子関係を設定
                entry = MenuStackEntry(menu, menu_type, context)
                entry.parent_entry = self.current_entry
                self.stack.append(self.current_entry)
            else:
                # 最初のメニュー（ROOT）
                entry = MenuStackEntry(menu, menu_type, context)
            
            # 新しいメニューを表示
            self.current_entry = entry
            self._show_current_menu()
            
            logger.info(f"メニューをプッシュしました: {menu.menu_id} ({menu_type.value})")
            logger.debug(f"スタックサイズ: {len(self.stack)}")
            
            # コールバック実行
            if self.on_menu_changed:
                self.on_menu_changed(self.current_entry)
            
            return True
            
        except Exception as e:
            logger.error(f"メニュープッシュエラー: {e}")
            return False
        finally:
            self.is_transition_in_progress = False
    
    def pop_menu(self) -> Optional[MenuStackEntry]:
        """メニューをスタックからポップして前のメニューに戻る
        
        Returns:
            MenuStackEntry: ポップされたエントリ（なければNone）
        """
        try:
            if self.is_transition_in_progress:
                logger.warning("メニュー遷移中のため、ポップ操作をスキップしました")
                return None
            
            if not self.current_entry:
                logger.warning("現在のメニューがありません")
                return None
            
            self.is_transition_in_progress = True
            
            # 現在のメニューをクリーンアップ
            popped_entry = self.current_entry
            self._hide_current_menu()
            self._cleanup_menu_entry(popped_entry)
            
            # 前のメニューに戻る
            if self.stack:
                self.current_entry = self.stack.pop()
                self._show_current_menu()
                logger.info(f"メニューを戻りました: {self.current_entry.menu.menu_id}")
            else:
                # スタックが空の場合
                self.current_entry = None
                logger.info("メニュースタックが空になりました")
            
            logger.debug(f"スタックサイズ: {len(self.stack)}")
            
            # コールバック実行
            if self.on_menu_changed:
                self.on_menu_changed(self.current_entry)
            
            return popped_entry
            
        except Exception as e:
            logger.error(f"メニューポップエラー: {e}")
            return None
        finally:
            self.is_transition_in_progress = False
    
    def peek_current_menu(self) -> Optional[MenuStackEntry]:
        """現在のメニューエントリを取得（スタックは変更しない）
        
        Returns:
            MenuStackEntry: 現在のメニューエントリ
        """
        return self.current_entry
    
    def back_to_previous(self) -> bool:
        """一つ前のメニューに戻る
        
        Returns:
            bool: 成功した場合True
        """
        if self.current_entry:
            popped = self.pop_menu()
            return popped is not None
        return False
    
    def back_to_root(self) -> bool:
        """ルートメニュー（地上マップ）まで戻る
        
        Returns:
            bool: 成功した場合True
        """
        try:
            if not self.current_entry:
                return False
            
            # ROOTタイプが見つかるまでポップ
            while self.stack:
                entry = self.stack[-1]
                if entry.menu_type == MenuType.ROOT:
                    break
                self.pop_menu()
            
            # 最後にもう一度ポップしてROOTを表示
            if self.stack:
                self.pop_menu()
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"ルートメニューへの復帰エラー: {e}")
            return False
    
    def back_to_facility_main(self) -> bool:
        """施設メインメニューまで戻る
        
        Returns:
            bool: 成功した場合True
        """
        try:
            if not self.current_entry:
                return False
            
            # FACILITY_MAINタイプが見つかるまでポップ
            while self.stack:
                entry = self.stack[-1]
                if entry.menu_type == MenuType.FACILITY_MAIN:
                    break
                self.pop_menu()
            
            # 最後にもう一度ポップしてFACILITY_MAINを表示
            if self.stack:
                self.pop_menu()
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"施設メインメニューへの復帰エラー: {e}")
            return False
    
    def clear_stack(self) -> None:
        """スタックをクリア（緊急時用）"""
        try:
            logger.info("メニュースタックをクリアします")
            
            # 現在のメニューをクリーンアップ
            if self.current_entry:
                self._hide_current_menu()
                self._cleanup_menu_entry(self.current_entry)
                self.current_entry = None
            
            # スタック内の全エントリをクリーンアップ
            for entry in self.stack:
                self._cleanup_menu_entry(entry)
            
            self.stack.clear()
            self.is_transition_in_progress = False
            
            logger.info("メニュースタックをクリアしました")
            
        except Exception as e:
            logger.error(f"メニュースタッククリアエラー: {e}")
    
    def handle_escape_key(self) -> bool:
        """ESCキー処理
        
        Returns:
            bool: 処理した場合True
        """
        try:
            if self.is_transition_in_progress:
                return False
            
            logger.debug("ESCキーが押されました")
            
            # コールバックがある場合は最初にコールバックを実行
            if self.on_escape_pressed:
                if self.on_escape_pressed():
                    return True
            
            # 現在のメニュータイプに応じた処理
            if not self.current_entry:
                return False
            
            menu_type = self.current_entry.menu_type
            
            if menu_type == MenuType.ROOT:
                # 地上マップの場合は設定画面へ
                logger.info("地上マップから設定画面へ遷移")
                # 設定画面表示は呼び出し元で処理
                return True
                
            elif menu_type == MenuType.SETTINGS:
                # 設定画面の場合は地上マップへ
                self.back_to_root()
                return True
                
            elif menu_type in [MenuType.FACILITY_MAIN, MenuType.SUBMENU, MenuType.DIALOG]:
                # その他の場合は一つ前に戻る
                self.back_to_previous()
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"ESCキー処理エラー: {e}")
            return False
    
    def get_current_context(self) -> Dict[str, Any]:
        """現在のメニューのコンテキストを取得
        
        Returns:
            Dict[str, Any]: コンテキスト情報
        """
        if self.current_entry:
            return self.current_entry.context.copy()
        return {}
    
    def update_current_context(self, context: Dict[str, Any]) -> bool:
        """現在のメニューのコンテキストを更新
        
        Args:
            context: 更新するコンテキスト情報
            
        Returns:
            bool: 成功した場合True
        """
        if self.current_entry:
            self.current_entry.context.update(context)
            return True
        return False
    
    def get_menu_path(self) -> List[str]:
        """現在のメニューパスを取得（デバッグ用）
        
        Returns:
            List[str]: メニューIDのパス
        """
        path = []
        for entry in self.stack:
            path.append(entry.menu.menu_id)
        if self.current_entry:
            path.append(self.current_entry.menu.menu_id)
        return path
    
    def _show_current_menu(self) -> None:
        """現在のメニューを表示"""
        if not self.current_entry:
            return
        
        try:
            menu = self.current_entry.menu
            self.ui_manager.add_menu(menu)
            self.ui_manager.show_menu(menu.menu_id, modal=True)
            logger.debug(f"メニューを表示: {menu.menu_id}")
            
        except Exception as e:
            logger.error(f"メニュー表示エラー: {e}")
    
    def _hide_current_menu(self) -> None:
        """現在のメニューを隠す"""
        if not self.current_entry:
            return
        
        try:
            menu = self.current_entry.menu
            self.ui_manager.hide_menu(menu.menu_id)
            logger.debug(f"メニューを隠す: {menu.menu_id}")
            
        except Exception as e:
            logger.error(f"メニュー非表示エラー: {e}")
    
    def _cleanup_menu_entry(self, entry: MenuStackEntry) -> None:
        """メニューエントリのクリーンアップ"""
        try:
            menu = entry.menu
            # UI要素の状態をリセット
            if hasattr(menu, 'state'):
                menu.state = UIState.HIDDEN
            
            logger.debug(f"メニューエントリをクリーンアップ: {menu.menu_id}")
            
        except Exception as e:
            logger.error(f"メニューエントリクリーンアップエラー: {e}")
    
    def get_debug_info(self) -> Dict[str, Any]:
        """デバッグ情報を取得"""
        return {
            'current_menu': self.current_entry.menu.menu_id if self.current_entry else None,
            'current_type': self.current_entry.menu_type.value if self.current_entry else None,
            'stack_size': len(self.stack),
            'menu_path': self.get_menu_path(),
            'is_transition_in_progress': self.is_transition_in_progress,
            'stack_entries': [entry.menu.menu_id for entry in self.stack]
        }