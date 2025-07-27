"""
UI コンポーネントの基底クラスとインターフェース

このモジュールは、パーティ情報を扱うUIコンポーネントの
共通インターフェースと基底実装を提供します。
"""

from abc import ABC, abstractmethod
from typing import Optional
from src.character.party import Party
from src.ui.ui_update_manager import UIUpdateable


class PartyAwareUIComponent(UIUpdateable):
    """パーティ情報を扱うUIコンポーネントの基底クラス
    
    このクラスは以下の責務を持ちます：
    - パーティ情報の統一的な管理
    - UIUpdateableインターフェースの基本実装
    - パーティ変更時の標準的な更新フロー
    """
    
    def __init__(self):
        self._party: Optional[Party] = None
        self._is_dirty = True  # 変更フラグ
    
    @property
    def party(self) -> Optional[Party]:
        """現在のパーティを取得"""
        return self._party
    
    def set_party(self, party: Optional[Party]) -> None:
        """パーティ情報を設定する（UIUpdateableインターフェース実装）
        
        Args:
            party: 新しいパーティ情報
        """
        if self._party != party:
            self._party = party
            self._is_dirty = True
            self.on_party_changed(party)
    
    def update_display(self) -> None:
        """表示を更新する（UIUpdateableインターフェース実装）"""
        if self._is_dirty or self.needs_refresh():
            self.refresh_ui()
            self._is_dirty = False
    
    @abstractmethod
    def on_party_changed(self, party: Optional[Party]) -> None:
        """パーティ変更時のコールバック（継承クラスで実装）
        
        Args:
            party: 新しいパーティ情報
        """
        pass
    
    @abstractmethod
    def refresh_ui(self) -> None:
        """UIの再描画処理（継承クラスで実装）"""
        pass
    
    def needs_refresh(self) -> bool:
        """追加の更新が必要かチェック（オーバーライド可能）
        
        Returns:
            bool: 更新が必要な場合True
        """
        return False
    
    def mark_dirty(self) -> None:
        """変更フラグを設定（手動で再描画をトリガー）"""
        self._is_dirty = True
    
    def is_dirty(self) -> bool:
        """変更フラグの状態を取得
        
        Returns:
            bool: 変更がある場合True
        """
        return self._is_dirty


class SimplePartyUIComponent(PartyAwareUIComponent):
    """シンプルなパーティUIコンポーネントの基本実装
    
    基本的なパーティ情報表示を行うコンポーネント用の
    デフォルト実装を提供します。
    """
    
    def __init__(self, update_callback=None):
        """初期化
        
        Args:
            update_callback: パーティ変更時に呼び出されるコールバック関数
        """
        super().__init__()
        self._update_callback = update_callback
    
    def on_party_changed(self, party: Optional[Party]) -> None:
        """パーティ変更時のデフォルト処理"""
        if self._update_callback:
            try:
                self._update_callback(party)
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"パーティ変更コールバック実行エラー: {e}")
    
    def refresh_ui(self) -> None:
        """デフォルトのUI更新処理（具体的な実装は継承クラスで）"""
        pass
    
    def set_update_callback(self, callback) -> None:
        """更新コールバックを設定
        
        Args:
            callback: パーティ変更時に呼び出される関数
        """
        self._update_callback = callback


class DummyPartyUIComponent(SimplePartyUIComponent):
    """テスト・デバッグ用のダミーUIコンポーネント"""
    
    def __init__(self):
        super().__init__()
        self.refresh_count = 0
        self.last_party_name = None
    
    def on_party_changed(self, party: Optional[Party]) -> None:
        """パーティ変更をログに記録"""
        import logging
        logger = logging.getLogger(__name__)
        
        self.last_party_name = party.name if party else None
        logger.debug(f"DummyPartyUIComponent: パーティ変更 -> {self.last_party_name}")
        super().on_party_changed(party)
    
    def refresh_ui(self) -> None:
        """更新回数をカウント"""
        self.refresh_count += 1
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"DummyPartyUIComponent: UI更新 #{self.refresh_count}")
    
    def get_stats(self) -> dict:
        """統計情報を取得（デバッグ用）"""
        return {
            'refresh_count': self.refresh_count,
            'last_party_name': self.last_party_name,
            'is_dirty': self.is_dirty(),
            'has_party': self.party is not None
        }