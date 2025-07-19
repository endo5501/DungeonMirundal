"""Base interfaces for game components."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class GameComponent(ABC):
    """ゲームコンポーネントの基底インターフェース
    
    すべてのゲームコンポーネントはこのインターフェースを実装し、
    初期化とクリーンアップの責任を持つ。
    """
    
    @abstractmethod
    def initialize(self, context: Dict[str, Any]) -> bool:
        """コンポーネントの初期化
        
        Args:
            context: 初期化に必要なコンテキスト情報
            
        Returns:
            bool: 初期化が成功した場合True
        """
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """リソースのクリーンアップ
        
        コンポーネントが保持するリソースを適切に解放する。
        """
        pass


class EventAwareComponent(GameComponent):
    """イベント対応コンポーネント
    
    ゲームイベントを処理する能力を持つコンポーネントのインターフェース。
    """
    
    @abstractmethod
    def handle_game_event(self, event: Any) -> bool:
        """ゲームイベントの処理
        
        Args:
            event: 処理対象のゲームイベント
            
        Returns:
            bool: イベントが処理された場合True
        """
        pass


class ComponentState:
    """コンポーネントの状態を表す列挙型"""
    UNINITIALIZED = "uninitialized"
    INITIALIZED = "initialized"
    RUNNING = "running"
    ERROR = "error"
    CLEANUP = "cleanup"


class ManagedComponent(EventAwareComponent):
    """状態管理付きコンポーネント
    
    コンポーネントの状態を自動的に管理し、
    適切な初期化とクリーンアップを保証する。
    """
    
    def __init__(self):
        self._state: str = ComponentState.UNINITIALIZED
        self._context: Optional[Dict[str, Any]] = None
    
    @property
    def state(self) -> str:
        """現在の状態を取得"""
        return self._state
    
    @property
    def context(self) -> Optional[Dict[str, Any]]:
        """初期化コンテキストを取得"""
        return self._context
    
    def initialize(self, context: Dict[str, Any]) -> bool:
        """初期化の実行と状態管理"""
        try:
            self._context = context
            self._state = ComponentState.INITIALIZED
            result = self._do_initialize(context)
            if result:
                self._state = ComponentState.RUNNING
            else:
                self._state = ComponentState.ERROR
            return result
        except Exception as e:
            self._state = ComponentState.ERROR
            self._handle_initialization_error(e)
            return False
    
    def cleanup(self) -> None:
        """クリーンアップの実行と状態管理"""
        try:
            self._state = ComponentState.CLEANUP
            self._do_cleanup()
        except Exception as e:
            self._handle_cleanup_error(e)
        finally:
            self._state = ComponentState.UNINITIALIZED
            self._context = None
    
    @abstractmethod
    def _do_initialize(self, context: Dict[str, Any]) -> bool:
        """具体的な初期化処理
        
        サブクラスでオーバーライドして実装する。
        """
        pass
    
    @abstractmethod
    def _do_cleanup(self) -> None:
        """具体的なクリーンアップ処理
        
        サブクラスでオーバーライドして実装する。
        """
        pass
    
    def _handle_initialization_error(self, error: Exception) -> None:
        """初期化エラーの処理
        
        サブクラスでオーバーライド可能。
        デフォルトでは何もしない。
        """
        pass
    
    def _handle_cleanup_error(self, error: Exception) -> None:
        """クリーンアップエラーの処理
        
        サブクラスでオーバーライド可能。
        デフォルトでは何もしない。
        """
        pass