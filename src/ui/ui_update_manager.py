"""
UI更新処理の共通管理クラス

このモジュールは、ゲーム全体のUI更新処理を統一的に管理し、
重複コードの排除とパフォーマンスの向上を目的としています。
"""

import logging
from typing import Optional, Any, Dict, List, Callable
from abc import ABC, abstractmethod

from src.character.party import Party
from src.core.event_bus import EventBus, EventHandler, EventType, GameEvent

logger = logging.getLogger(__name__)


class UIUpdateable(ABC):
    """UI更新可能なコンポーネントのインターフェース"""
    
    @abstractmethod
    def set_party(self, party: Optional[Party]) -> None:
        """パーティ情報を設定する"""
        pass
    
    @abstractmethod
    def update_display(self) -> None:
        """表示を更新する"""
        pass


class UIUpdateManager(EventHandler):
    """UI更新処理の統一管理クラス（EventBus統合版）
    
    このクラスは以下の責務を持ちます：
    - WindowManager経由の安全なUI更新
    - パーティ変更時の一括UI更新
    - EventBus経由でのイベント駆動UI更新
    - エラーハンドリングとログの統一
    - 更新対象コンポーネントの管理
    """
    
    def __init__(self, window_manager=None):
        """初期化
        
        Args:
            window_manager: WindowManagerインスタンス
        """
        self.window_manager = window_manager
        self._registered_components: Dict[str, Any] = {}
        self._update_callbacks: List[Callable] = []
        self._auto_discovery_enabled = True
        
        # EventBus統合
        self.event_bus = EventBus()
        self._setup_event_subscriptions()
    
    def _setup_event_subscriptions(self) -> None:
        """EventBus購読の設定"""
        # パーティ関連イベントを購読
        party_events = [
            EventType.PARTY_CREATED,
            EventType.PARTY_MEMBER_ADDED,
            EventType.PARTY_MEMBER_REMOVED,
            EventType.PARTY_GOLD_CHANGED
        ]
        
        for event_type in party_events:
            self.event_bus.subscribe(event_type, self)
        
        # キャラクター関連イベントも購読
        character_events = [
            EventType.CHARACTER_HP_CHANGED,
            EventType.CHARACTER_STATUS_CHANGED,
            EventType.CHARACTER_LEVEL_UP
        ]
        
        for event_type in character_events:
            self.event_bus.subscribe(event_type, self)
        
        logger.debug("UIUpdateManager: EventBus購読を設定しました")
    
    def handle_event(self, event: GameEvent) -> bool:
        """EventBusからのイベント処理（EventHandlerインターフェース実装）"""
        try:
            if event.event_type in [EventType.PARTY_CREATED, EventType.PARTY_MEMBER_ADDED, 
                                   EventType.PARTY_MEMBER_REMOVED, EventType.PARTY_GOLD_CHANGED]:
                # パーティ関連イベントの場合、関連UIを更新
                party = event.data.get('party') if event.data else None
                if party:
                    self.update_party_across_ui(party)
                    logger.debug(f"UIUpdateManager: パーティイベント処理完了 - {event.event_type.value}")
                else:
                    # パーティ情報なしの場合は強制リフレッシュ
                    self.force_ui_refresh()
                    logger.debug(f"UIUpdateManager: UI強制リフレッシュ - {event.event_type.value}")
                
            elif event.event_type in [EventType.CHARACTER_HP_CHANGED, EventType.CHARACTER_STATUS_CHANGED, 
                                     EventType.CHARACTER_LEVEL_UP]:
                # キャラクター関連イベントの場合、キャラクター表示を更新
                self._update_character_displays(event)
                logger.debug(f"UIUpdateManager: キャラクターイベント処理完了 - {event.event_type.value}")
            
            return False  # 他のハンドラーにも処理を委ねる
            
        except Exception as e:
            logger.error(f"UIUpdateManager: イベント処理エラー - {event.event_type.value}: {e}")
            return False
    
    def get_handled_event_types(self) -> List[EventType]:
        """処理するイベントタイプのリスト"""
        return [
            EventType.PARTY_CREATED,
            EventType.PARTY_MEMBER_ADDED,
            EventType.PARTY_MEMBER_REMOVED,
            EventType.PARTY_GOLD_CHANGED,
            EventType.CHARACTER_HP_CHANGED,
            EventType.CHARACTER_STATUS_CHANGED,
            EventType.CHARACTER_LEVEL_UP
        ]
    
    def _update_character_displays(self, event: GameEvent) -> None:
        """キャラクター関連イベントでの表示更新"""
        character = event.data.get('character') if event.data else None
        if not character:
            return
        
        # 登録されたコンポーネントのうち、キャラクター更新をサポートするものを更新
        for name, component in self._registered_components.items():
            try:
                if hasattr(component, 'update_character'):
                    component.update_character(character)
                elif hasattr(component, 'refresh_character'):
                    component.refresh_character(character)
                elif hasattr(component, 'mark_dirty'):
                    component.mark_dirty()
            except Exception as e:
                logger.error(f"UIUpdateManager: {name} のキャラクター更新エラー: {e}")
        
        # WindowManager経由でも更新
        if self.window_manager:
            try:
                current_window = self.window_manager.get_active_window()
                if current_window and hasattr(current_window, 'update_character_display'):
                    current_window.update_character_display(character)
            except Exception as e:
                logger.error(f"UIUpdateManager: ウィンドウキャラクター更新エラー: {e}")

    def set_window_manager(self, window_manager) -> None:
        """WindowManagerを設定する
        
        Args:
            window_manager: WindowManagerインスタンス
        """
        self.window_manager = window_manager
        logger.debug("UIUpdateManager: WindowManagerが設定されました")
    
    def register_component(self, name: str, component: Any) -> None:
        """UI更新対象のコンポーネントを登録する
        
        Args:
            name: コンポーネント名
            component: UIUpdateableインターフェースを実装するコンポーネント
        """
        if not hasattr(component, 'set_party'):
            logger.warning(f"UIUpdateManager: コンポーネント '{name}' はset_partyメソッドを持っていません")
        
        self._registered_components[name] = component
        logger.debug(f"UIUpdateManager: コンポーネント '{name}' を登録しました")
    
    def unregister_component(self, name: str) -> None:
        """コンポーネントの登録を解除する
        
        Args:
            name: コンポーネント名
        """
        if name in self._registered_components:
            del self._registered_components[name]
            logger.debug(f"UIUpdateManager: コンポーネント '{name}' の登録を解除しました")
    
    def add_update_callback(self, callback: Callable) -> None:
        """更新時のコールバック関数を追加する
        
        Args:
            callback: 更新時に呼び出される関数
        """
        self._update_callbacks.append(callback)
        logger.debug("UIUpdateManager: 更新コールバックを追加しました")
    
    def auto_discover_components(self) -> int:
        """WindowManager内のコンポーネントを自動検出して登録する
        
        Returns:
            int: 検出・登録されたコンポーネント数
        """
        if not self._auto_discovery_enabled or not self.window_manager:
            return 0
        
        discovered_count = 0
        
        try:
            # アクティブなウィンドウから検出
            current_window = self.window_manager.get_active_window()
            if current_window:
                discovered_count += self._discover_from_window(current_window, "active_window")
            
            # 全ウィンドウから検出
            all_windows = getattr(self.window_manager, 'windows', {})
            for window_name, window in all_windows.items():
                if window != current_window:  # アクティブウィンドウは既に処理済み
                    discovered_count += self._discover_from_window(window, f"window_{window_name}")
            
            logger.info(f"UIUpdateManager: 自動検出で {discovered_count} 個のコンポーネントを登録しました")
            return discovered_count
            
        except Exception as e:
            logger.error(f"UIUpdateManager: 自動検出中にエラー: {e}")
            return 0
    
    def _discover_from_window(self, window, prefix: str) -> int:
        """ウィンドウからUIコンポーネントを検出する
        
        Args:
            window: 検出対象のウィンドウ
            prefix: コンポーネント名のプレフィックス
            
        Returns:
            int: 検出されたコンポーネント数
        """
        count = 0
        
        # よく使われるUI要素の属性名
        ui_attributes = [
            'character_status_bar', 'status_bar', 'party_status',
            'magic_ui', 'inventory_ui', 'equipment_ui',
            'character_display', 'party_display'
        ]
        
        for attr_name in ui_attributes:
            if hasattr(window, attr_name):
                component = getattr(window, attr_name)
                if component and hasattr(component, 'set_party'):
                    component_name = f"{prefix}_{attr_name}"
                    if component_name not in self._registered_components:
                        self.register_component(component_name, component)
                        count += 1
        
        return count
    
    def update_party_across_ui(self, party: Optional[Party]) -> bool:
        """パーティ情報をすべてのUI要素に更新する
        
        Args:
            party: 新しいパーティ情報
            
        Returns:
            bool: 更新が成功したかどうか
        """
        if not party:
            logger.warning("UIUpdateManager: パーティ情報がNullです")
            return False
        
        success_count = 0
        total_count = 0
        
        try:
            # 自動検出実行（必要に応じて）
            if self._auto_discovery_enabled:
                self.auto_discover_components()
            
            # WindowManager経由でのメインウィンドウ更新
            if self.window_manager:
                success = self._update_main_window_party(party)
                if success:
                    success_count += 1
                total_count += 1
            
            # 登録されたコンポーネントの更新
            for name, component in self._registered_components.items():
                try:
                    if hasattr(component, 'set_party'):
                        component.set_party(party)
                        logger.debug(f"UIUpdateManager: {name} のパーティ情報を更新しました")
                        success_count += 1
                    else:
                        logger.warning(f"UIUpdateManager: {name} は set_party メソッドを持っていません")
                except Exception as e:
                    logger.error(f"UIUpdateManager: {name} の更新中にエラー: {e}")
                finally:
                    total_count += 1
            
            # コールバック関数の実行
            for callback in self._update_callbacks:
                try:
                    callback()
                except Exception as e:
                    logger.error(f"UIUpdateManager: コールバック実行中にエラー: {e}")
            
            logger.info(f"UIUpdateManager: パーティ更新完了 ({success_count}/{total_count} 成功)")
            return success_count == total_count
            
        except Exception as e:
            logger.error(f"UIUpdateManager: パーティ更新処理でエラー: {e}")
            return False
    
    def _update_main_window_party(self, party: Party) -> bool:
        """メインウィンドウのパーティ情報を更新する
        
        Args:
            party: パーティ情報
            
        Returns:
            bool: 更新が成功したかどうか
        """
        try:
            if not self.window_manager:
                logger.warning("UIUpdateManager: WindowManagerが利用できません")
                return False
            
            current_window = self.window_manager.get_active_window()
            if not current_window:
                logger.warning("UIUpdateManager: アクティブなウィンドウが見つかりません")
                return False
            
            updated_components = []
            
            # CharacterStatusBarの更新
            if hasattr(current_window, 'character_status_bar') and current_window.character_status_bar:
                current_window.character_status_bar.set_party(party)
                updated_components.append("CharacterStatusBar")
            
            # パーティステータス更新
            if hasattr(current_window, 'update_party_status'):
                current_window.update_party_status()
                updated_components.append("PartyStatus")
            
            # その他のパーティ関連UI要素の更新
            party_ui_methods = ['update_party_display', 'refresh_party_info', 'set_current_party']
            for method_name in party_ui_methods:
                if hasattr(current_window, method_name):
                    method = getattr(current_window, method_name)
                    if callable(method):
                        try:
                            method(party)
                            updated_components.append(method_name)
                        except TypeError:
                            # 引数なしのメソッドの場合
                            method()
                            updated_components.append(method_name)
                        except Exception as e:
                            logger.warning(f"UIUpdateManager: {method_name} 実行中にエラー: {e}")
            
            if updated_components:
                logger.info(f"UIUpdateManager: メインウィンドウ更新完了 - {', '.join(updated_components)}")
                logger.info(f"UIUpdateManager: パーティ '{party.name}' ({len(party.characters)}人) を設定")
                return True
            else:
                logger.warning("UIUpdateManager: 更新可能なUI要素が見つかりませんでした")
                return False
                
        except Exception as e:
            logger.error(f"UIUpdateManager: メインウィンドウ更新エラー: {e}")
            return False
    
    def force_ui_refresh(self) -> None:
        """すべてのUI要素の強制再描画"""
        try:
            # 登録されたコンポーネントの更新
            for name, component in self._registered_components.items():
                try:
                    if hasattr(component, 'update_display'):
                        component.update_display()
                    elif hasattr(component, 'refresh'):
                        component.refresh()
                    elif hasattr(component, 'update'):
                        component.update()
                    logger.debug(f"UIUpdateManager: {name} を強制更新しました")
                except Exception as e:
                    logger.error(f"UIUpdateManager: {name} の強制更新中にエラー: {e}")
            
            # WindowManager経由での更新
            if self.window_manager:
                try:
                    current_window = self.window_manager.get_active_window()
                    if current_window and hasattr(current_window, 'refresh'):
                        current_window.refresh()
                        logger.debug("UIUpdateManager: メインウィンドウを強制更新しました")
                except Exception as e:
                    logger.error(f"UIUpdateManager: メインウィンドウ強制更新エラー: {e}")
            
            logger.info("UIUpdateManager: UI強制更新が完了しました")
            
        except Exception as e:
            logger.error(f"UIUpdateManager: UI強制更新処理でエラー: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """UIUpdateManagerの状態を取得する
        
        Returns:
            Dict[str, Any]: 状態情報
        """
        return {
            'window_manager_available': self.window_manager is not None,
            'registered_components': list(self._registered_components.keys()),
            'callback_count': len(self._update_callbacks),
            'active_window': str(self.window_manager.get_active_window()) if self.window_manager else None
        }


# シングルトンインスタンス（オプション）
_ui_update_manager_instance: Optional[UIUpdateManager] = None


def get_ui_update_manager() -> UIUpdateManager:
    """UIUpdateManagerのシングルトンインスタンスを取得する
    
    Returns:
        UIUpdateManager: シングルトンインスタンス
    """
    global _ui_update_manager_instance
    if _ui_update_manager_instance is None:
        _ui_update_manager_instance = UIUpdateManager()
        logger.debug("UIUpdateManager: シングルトンインスタンスを作成しました")
    return _ui_update_manager_instance


def set_global_window_manager(window_manager) -> None:
    """グローバルUIUpdateManagerにWindowManagerを設定する
    
    Args:
        window_manager: WindowManagerインスタンス
    """
    manager = get_ui_update_manager()
    manager.set_window_manager(window_manager)