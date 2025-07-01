"""
WindowPool クラス

Window オブジェクトの再利用によるメモリ効率向上
"""

from typing import Dict, List, Type, Optional, Any
import weakref
import threading
from collections import defaultdict

from src.utils.logger import logger
from .window import Window


class WindowPool:
    """
    Windowプールマネージャー
    
    Windowオブジェクトの再利用により以下の効果を実現する：
    - メモリアロケーション削減
    - オブジェクト作成コストの削減
    - ガベージコレクション負荷の軽減
    - 長期安定性の向上
    """
    
    def __init__(self, max_pool_size: int = 50):
        """
        Windowプールを初期化
        
        Args:
            max_pool_size: プール最大サイズ
        """
        self.max_pool_size = max_pool_size
        
        # クラス別のWindowプール
        self.pools: Dict[Type[Window], List[Window]] = defaultdict(list)
        
        # プール統計
        self.stats = {
            'total_created': 0,
            'total_reused': 0,
            'total_returned': 0,
            'current_pool_size': 0,
            'max_pool_size_reached': 0
        }
        
        # スレッドセーフティ
        self._lock = threading.Lock()
        
        logger.debug(f"WindowPoolを初期化（最大プールサイズ: {max_pool_size}）")
    
    def get_window(self, window_class: Type[Window], window_id: str, **kwargs) -> Window:
        """
        Windowをプールから取得または新規作成
        
        Args:
            window_class: Windowクラス
            window_id: WindowID
            **kwargs: Window作成引数
            
        Returns:
            Window: 再利用または新規作成されたWindow
        """
        with self._lock:
            # プールから再利用可能なWindowを検索
            pool = self.pools[window_class]
            
            if pool:
                # プールから取得
                window = pool.pop()
                self._reset_window(window, window_id, **kwargs)
                self.stats['total_reused'] += 1
                self.stats['current_pool_size'] -= 1
                
                logger.debug(f"Windowをプールから再利用: {window_id} ({window_class.__name__})")
                return window
            else:
                # 新規作成
                window = window_class(window_id, **kwargs)
                self.stats['total_created'] += 1
                
                logger.debug(f"新規Windowを作成: {window_id} ({window_class.__name__})")
                return window
    
    def return_window(self, window: Window) -> bool:
        """
        Windowをプールに返却
        
        Args:
            window: 返却するWindow
            
        Returns:
            bool: 返却成功時True
        """
        logger.debug(f"WindowPool.return_window() 開始: {window.window_id}")
        with self._lock:
            window_class = type(window)
            pool = self.pools[window_class]
            
            # プールサイズ制限チェック
            if len(pool) >= self.max_pool_size:
                logger.debug(f"プールサイズ上限のためWindow破棄: {window.window_id}")
                self.stats['max_pool_size_reached'] += 1
                return False
            
            # Windowをクリーンアップしてプールに返却
            logger.debug(f"WindowPool._cleanup_window() 呼び出し: {window.window_id}")
            if self._cleanup_window(window):
                pool.append(window)
                self.stats['total_returned'] += 1
                self.stats['current_pool_size'] += 1
                
                logger.debug(f"Windowをプールに返却: {window.window_id} ({window_class.__name__})")
                return True
            else:
                logger.warning(f"Windowクリーンアップ失敗のため破棄: {window.window_id}")
                return False
    
    def _reset_window(self, window: Window, new_window_id: str, **kwargs) -> None:
        """
        再利用Window用のリセット処理
        
        Args:
            window: リセット対象Window
            new_window_id: 新しいWindowID
            **kwargs: リセット用引数
        """
        # 基本プロパティのリセット
        window.window_id = new_window_id
        window.state = window.state.__class__.CREATED  # WindowState.CREATED
        window.visible = False
        window.focused = False
        
        # 子Window関係のクリア
        if hasattr(window, 'children'):
            window.children.clear()
        if hasattr(window, 'parent'):
            window.parent = None
        
        # イベントハンドラのクリア
        if hasattr(window, 'event_handlers'):
            window.event_handlers.clear()
        
        # カスタムリセット処理
        if hasattr(window, 'reset_for_reuse'):
            window.reset_for_reuse(**kwargs)
    
    def _cleanup_window(self, window: Window) -> bool:
        """
        Window返却前のクリーンアップ
        
        Args:
            window: クリーンアップ対象Window
            
        Returns:
            bool: クリーンアップ成功時True
        """
        try:
            # 表示状態のクリア（属性が存在する場合のみ）
            if hasattr(window, 'visible') and window.visible:
                window.hide()
            
            # フォーカス状態のクリア（属性が存在する場合のみ）
            if hasattr(window, 'focused'):
                window.focused = False
            
            # イベントリスナーのクリア
            if hasattr(window, 'clear_event_listeners'):
                window.clear_event_listeners()
            
            # カスタムクリーンアップ処理
            if hasattr(window, 'cleanup_for_pool'):
                logger.debug(f"WindowPool: cleanup_for_pool() を呼び出し: {window.window_id}")
                window.cleanup_for_pool()
            else:
                logger.debug(f"WindowPool: cleanup_for_pool() メソッドがありません: {window.window_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Windowクリーンアップエラー: {e}")
            return False
    
    def clear_pool(self, window_class: Optional[Type[Window]] = None) -> int:
        """
        プールをクリア
        
        Args:
            window_class: 特定クラスのみクリア（Noneで全クリア）
            
        Returns:
            int: クリアしたWindow数
        """
        with self._lock:
            cleared_count = 0
            
            if window_class:
                # 特定クラスのみクリア
                pool = self.pools[window_class]
                cleared_count = len(pool)
                pool.clear()
            else:
                # 全プールクリア
                for pool in self.pools.values():
                    cleared_count += len(pool)
                    pool.clear()
                self.pools.clear()
            
            self.stats['current_pool_size'] -= cleared_count
            logger.info(f"Windowプールをクリア: {cleared_count}個")
            return cleared_count
    
    def get_stats(self) -> Dict[str, Any]:
        """
        プール統計情報を取得
        
        Returns:
            Dict[str, Any]: 統計情報
        """
        with self._lock:
            # 現在のプールサイズを再計算
            current_size = sum(len(pool) for pool in self.pools.values())
            self.stats['current_pool_size'] = current_size
            
            # 効率性指標を計算
            total_requests = self.stats['total_created'] + self.stats['total_reused']
            reuse_ratio = (self.stats['total_reused'] / total_requests) if total_requests > 0 else 0.0
            
            return {
                **self.stats,
                'reuse_ratio': reuse_ratio,
                'pool_classes': list(self.pools.keys()),
                'pool_sizes_by_class': {
                    cls.__name__: len(pool) for cls, pool in self.pools.items()
                }
            }
    
    def optimize_pools(self) -> None:
        """
        プールの最適化処理
        
        使用頻度の低いWindowを除去し、メモリ効率を向上
        """
        with self._lock:
            optimized_count = 0
            
            for window_class, pool in list(self.pools.items()):
                if not pool:
                    # 空のプールを除去
                    del self.pools[window_class]
                    continue
                
                # プールサイズが過大な場合は削減
                max_size = max(1, self.max_pool_size // 4)  # 各クラスの最大サイズを制限
                if len(pool) > max_size:
                    removed = pool[max_size:]
                    pool[:] = pool[:max_size]
                    optimized_count += len(removed)
            
            self.stats['current_pool_size'] -= optimized_count
            
            if optimized_count > 0:
                logger.info(f"Windowプールを最適化: {optimized_count}個を除去")


# グローバルWindowPoolインスタンス
_window_pool: Optional[WindowPool] = None


def get_window_pool() -> WindowPool:
    """
    グローバルWindowPoolインスタンスを取得
    
    Returns:
        WindowPool: グローバルインスタンス
    """
    global _window_pool
    if _window_pool is None:
        _window_pool = WindowPool()
    return _window_pool


def set_window_pool(pool: WindowPool) -> None:
    """
    グローバルWindowPoolインスタンスを設定
    
    Args:
        pool: 設定するWindowPool
    """
    global _window_pool
    _window_pool = pool