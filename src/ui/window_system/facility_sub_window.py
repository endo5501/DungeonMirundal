"""施設サブメニュー専用基底クラス"""

from typing import Dict, Any, Optional, List
from src.ui.window_system.window import Window


class FacilitySubWindow(Window):
    """施設サブメニュー専用基底クラス
    
    レガシーメニューの代替として、施設内のサブメニュー機能を提供するWindowの基底クラス。
    共通の戻り処理、コンテキスト管理、設定データ管理を提供。
    """
    
    def __init__(self, window_id: str, facility_config: Dict[str, Any]):
        """初期化
        
        Args:
            window_id: ウィンドウID
            facility_config: 施設設定データ
                - parent_facility: 親施設インスタンス
                - current_party: 現在のパーティ
                - service_types: 利用可能なサービスタイプ
                - context: 追加コンテキストデータ
        """
        super().__init__(window_id)
        self.facility_config = facility_config
        self.parent_facility = facility_config.get('parent_facility')
        self.current_party = facility_config.get('current_party')
        self.service_types = facility_config.get('service_types', [])
        self.context_data = facility_config.get('context', {})
        
        # Window固有の設定
        self.window_type = "facility_sub"
        self.can_be_minimized = True
        self.can_be_closed = True
        
    def handle_back_navigation(self):
        """共通の戻り処理
        
        親施設のメインメニューに戻るか、ウィンドウを閉じる。
        レガシーメニューの戻り機能の代替実装。
        """
        if self.parent_facility and hasattr(self.parent_facility, '_show_main_menu'):
            self.parent_facility._show_main_menu()
        else:
            self.close()
    
    def get_available_services(self) -> List[str]:
        """利用可能なサービス一覧を取得
        
        Returns:
            利用可能なサービスタイプのリスト
        """
        return self.service_types.copy()
    
    def update_context(self, key: str, value: Any):
        """コンテキストデータを更新
        
        Args:
            key: コンテキストキー
            value: 設定値
        """
        self.context_data[key] = value
    
    def get_context(self, key: str, default: Any = None) -> Any:
        """コンテキストデータを取得
        
        Args:
            key: コンテキストキー
            default: デフォルト値
            
        Returns:
            コンテキスト値
        """
        return self.context_data.get(key, default)
    
    def has_party(self) -> bool:
        """パーティが設定されているかチェック
        
        Returns:
            パーティが設定されていればTrue
        """
        return self.current_party is not None
    
    def get_party_members(self) -> List:
        """パーティメンバーを取得
        
        Returns:
            パーティメンバーのリスト
        """
        if self.current_party and hasattr(self.current_party, 'characters'):
            return self.current_party.characters
        return []
    
    def can_provide_service(self, service_type: str) -> bool:
        """指定されたサービスが提供可能かチェック
        
        Args:
            service_type: サービスタイプ
            
        Returns:
            サービス提供可能であればTrue
        """
        return service_type in self.service_types
    
    def handle_service_request(self, service_type: str, **kwargs) -> bool:
        """サービスリクエストの処理
        
        サブクラスでオーバーライドして具体的なサービス処理を実装。
        
        Args:
            service_type: サービスタイプ
            **kwargs: サービス固有のパラメータ
            
        Returns:
            サービス処理が成功したらTrue
        """
        raise NotImplementedError("Subclasses must implement handle_service_request")
    
    def create_service_ui(self):
        """サービス用UIの作成
        
        サブクラスでオーバーライドして具体的なUI作成を実装。
        """
        raise NotImplementedError("Subclasses must implement create_service_ui")
    
    def on_show(self):
        """表示時の処理
        
        ウィンドウが表示される際に呼び出される。
        サービス用UIの作成などを行う。
        """
        super().on_show()
        self.create_service_ui()
    
    def on_hide(self):
        """非表示時の処理
        
        ウィンドウが非表示になる際に呼び出される。
        """
        super().on_hide()
        # 必要に応じてリソースの解放等を行う