"""
施設サービスProtocol定義

施設（宿屋、商店、神殿、ギルド等）で使用される型安全なインターフェースを定義します。
hasattr(controller, 'service'), hasattr(service, 'set_controller') パターンを型安全な呼び出しに置き換えます。
"""

from typing import Protocol, Any, Dict, Optional, TYPE_CHECKING, runtime_checkable
from .core_protocols import Cleanupable
from .ui_lifecycle_protocols import ServicePanel

if TYPE_CHECKING:
    from typing import Any as pygame
    from typing import Any as pygame_gui
    from typing import Any as ServiceResult


@runtime_checkable
class FacilityController(Protocol):
    """施設コントローラーのインターフェース"""
    
    def get_party(self) -> Optional[Any]:
        """パーティ情報を取得"""
        ...
    
    def get_service(self) -> "FacilityService":
        """施設サービスを取得"""
        ...
    
    def execute_service_action(self, action: str, params: Dict[str, Any]) -> "ServiceResult":
        """サービスアクション実行"""
        ...


@runtime_checkable
class FacilityService(Protocol):
    """施設サービスのインターフェース"""
    
    def set_controller(self, controller: FacilityController) -> None:
        """コントローラー参照を設定"""
        ...
    
    def create_service_panel(self, rect: "pygame.Rect", parent: "pygame_gui.elements.UIPanel") -> ServicePanel:
        """専用サービスパネルを作成"""
        ...
    
    def get_service_id(self) -> str:
        """サービスIDを取得"""
        ...


@runtime_checkable
class StorageService(FacilityService, Protocol):
    """ストレージサービスのインターフェース（宿屋等）"""
    
    @property
    def storage_manager(self) -> Any:
        """ストレージマネージャーを取得"""
        ...


@runtime_checkable
class GuildService(FacilityService, Protocol):
    """ギルドサービスのインターフェース"""
    
    def register_character(self, character_data: Dict[str, Any]) -> "ServiceResult":
        """キャラクター登録"""
        ...
    
    def create_party(self, party_name: str, character_ids: list) -> "ServiceResult":
        """パーティ作成"""
        ...


@runtime_checkable
class InnService(FacilityService, Protocol):
    """宿屋サービスのインターフェース"""
    
    def rest_party(self, rest_type: str) -> "ServiceResult":
        """パーティ休息"""
        ...
    
    def manage_storage(self, action: str, params: Dict[str, Any]) -> "ServiceResult":
        """ストレージ管理"""
        ...


@runtime_checkable
class ShopService(FacilityService, Protocol):
    """商店サービスのインターフェース"""
    
    def buy_item(self, item_id: str, quantity: int) -> "ServiceResult":
        """アイテム購入"""
        ...
    
    def sell_item(self, item_id: str, quantity: int) -> "ServiceResult":
        """アイテム売却"""
        ...
    
    def identify_item(self, item_id: str) -> "ServiceResult":
        """アイテム鑑定"""
        ...


@runtime_checkable
class TempleService(FacilityService, Protocol):
    """神殿サービスのインターフェース"""
    
    def heal_character(self, character_id: str, heal_type: str) -> "ServiceResult":
        """キャラクター治療"""
        ...
    
    def resurrect_character(self, character_id: str) -> "ServiceResult":
        """キャラクター蘇生"""
        ...
    
    def cure_status(self, character_id: str, status_type: str) -> "ServiceResult":
        """状態異常治療"""
        ...


# 複合Protocol（サービスの組み合わせ）

class FullServiceFacility(StorageService, Protocol):
    """フルサービス施設のインターフェース（宿屋等）"""
    pass


class TradingFacility(ShopService, Protocol):
    """取引施設のインターフェース（商店等）"""
    pass


class HealingFacility(TempleService, Protocol):
    """治療施設のインターフェース（神殿等）"""
    pass