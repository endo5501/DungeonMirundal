"""施設サービスの基底クラスとメニュー項目定義"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from src.character.party import Party


@dataclass
class MenuItem:
    """メニュー項目"""
    id: str
    label: str
    icon: Optional[str] = None
    enabled: bool = True
    service_type: str = "action"  # action, wizard, list, panel
    description: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'id': self.id,
            'label': self.label,
            'icon': self.icon,
            'enabled': self.enabled,
            'service_type': self.service_type,
            'description': self.description
        }


class FacilityService(ABC):
    """施設サービスの基底クラス
    
    各施設のビジネスロジックを実装するための基底クラス。
    UIから完全に分離され、純粋なビジネスロジックのみを扱う。
    """
    
    def __init__(self, facility_id: str):
        """初期化
        
        Args:
            facility_id: 施設ID (例: 'guild', 'inn')
        """
        self.facility_id = facility_id
        self.party: Optional[Party] = None
        self._service_data: Dict[str, Any] = {}
    
    @abstractmethod
    def get_menu_items(self) -> List[MenuItem]:
        """利用可能なメニュー項目を取得
        
        Returns:
            メニュー項目のリスト
        """
        pass
    
    @abstractmethod
    def execute_action(self, action_id: str, params: Dict[str, Any]) -> 'ServiceResult':
        """アクションを実行
        
        Args:
            action_id: アクションID
            params: アクションパラメータ
            
        Returns:
            実行結果
        """
        pass
    
    @abstractmethod
    def can_execute(self, action_id: str) -> bool:
        """アクション実行可能かチェック
        
        Args:
            action_id: アクションID
            
        Returns:
            実行可能ならTrue
        """
        pass
    
    def set_party(self, party: Party) -> None:
        """パーティを設定
        
        Args:
            party: 現在のパーティ
        """
        self.party = party
    
    def get_party(self) -> Optional[Party]:
        """現在のパーティを取得
        
        Returns:
            現在のパーティ（未設定の場合None）
        """
        return self.party
    
    def has_party(self) -> bool:
        """パーティが設定されているかチェック
        
        Returns:
            パーティが設定されていればTrue
        """
        return self.party is not None
    
    def get_service_data(self, key: str, default: Any = None) -> Any:
        """サービスデータを取得
        
        Args:
            key: データキー
            default: デフォルト値
            
        Returns:
            保存されたデータ
        """
        return self._service_data.get(key, default)
    
    def set_service_data(self, key: str, value: Any) -> None:
        """サービスデータを設定
        
        Args:
            key: データキー
            value: 設定値
        """
        self._service_data[key] = value
    
    def clear_service_data(self) -> None:
        """サービスデータをクリア"""
        self._service_data.clear()
    
    def get_welcome_message(self) -> str:
        """施設の歓迎メッセージを取得
        
        Returns:
            歓迎メッセージ
        """
        return f"{self.facility_id}へようこそ！"
    
    def validate_action_params(self, action_id: str, params: Dict[str, Any]) -> bool:
        """アクションパラメータを検証
        
        Args:
            action_id: アクションID
            params: 検証するパラメータ
            
        Returns:
            有効ならTrue
        """
        # サブクラスでオーバーライド可能
        return True
    
    def get_action_cost(self, action_id: str) -> int:
        """アクションのコストを取得
        
        Args:
            action_id: アクションID
            
        Returns:
            コスト（ゴールド）
        """
        # サブクラスでオーバーライド可能
        return 0
    
    def can_afford_action(self, action_id: str) -> bool:
        """アクションの費用を支払えるかチェック
        
        Args:
            action_id: アクションID
            
        Returns:
            支払い可能ならTrue
        """
        if not self.has_party():
            return False
        
        cost = self.get_action_cost(action_id)
        return self.party.gold >= cost