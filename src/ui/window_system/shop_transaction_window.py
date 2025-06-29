"""商店取引専用ウィンドウ"""

from typing import Dict, Any, List, Optional
import pygame
import pygame_gui
from src.ui.window_system.facility_sub_window import FacilitySubWindow
from src.core.config_manager import config_manager
from src.utils.logger import logger


class ShopTransactionWindow(FacilitySubWindow):
    """商店取引専用ウィンドウ
    
    購入・売却・カテゴリ選択・数量選択を統合したWindow実装。
    UIMenuの4箇所（category_menu, character_sell_menu, storage_sell_menu, quantity_menu）を代替。
    """
    
    def __init__(self, window_id: str, facility_config: Dict[str, Any]):
        """初期化
        
        Args:
            window_id: ウィンドウID（例: 'shop_transaction'）
            facility_config: 商店設定データ
                - parent_facility: 親商店インスタンス
                - current_party: 現在のパーティ
                - transaction_types: ['purchase', 'sell']
                - available_items: 利用可能アイテムリスト（オプション）
                - title: ウィンドウタイトル（オプション）
        """
        super().__init__(window_id, facility_config)
        
        # 商店固有の設定
        self.title = facility_config.get('title', '商店取引')
        self.transaction_types = facility_config.get('transaction_types', ['purchase', 'sell'])
        self.available_services = self._validate_transaction_types(self.transaction_types)
        self.available_items = facility_config.get('available_items', [])
        
        # UI要素
        self.transaction_buttons = {}
        self.item_list = None
        self.category_selector = None
        self.quantity_selector = None
        self.cost_display = None
        self.confirm_button = None
        self.back_button = None
        
        # 選択状態
        self.selected_transaction = None
        self.selected_item = None
        self.selected_quantity = 1
        self.selected_category = None
        
    def _validate_transaction_types(self, transaction_types: List[str]) -> List[str]:
        """取引タイプを検証
        
        Args:
            transaction_types: 取引タイプリスト
            
        Returns:
            有効な取引タイプのリスト
        """
        valid_types = ['purchase', 'sell', 'category_filter', 'quantity_select']
        return [t for t in transaction_types if t in valid_types]
    
    def get_purchasable_items(self) -> List:
        """購入可能アイテムを取得
        
        Returns:
            購入可能なアイテムのリスト
        """
        if not self.has_party():
            return []
        
        purchasable_items = []
        
        # available_itemsが設定されている場合はそれを使用
        if self.available_items:
            purchasable_items = self.available_items
        # 親施設からインベントリを取得
        elif hasattr(self.parent_facility, 'inventory'):
            from src.items.item import item_manager
            for item_id in self.parent_facility.inventory:
                try:
                    item = item_manager.get_item(item_id)
                    if item:
                        purchasable_items.append(item)
                except Exception as e:
                    logger.warning(f"アイテム取得エラー: {item_id} - {e}")
        
        return purchasable_items
    
    def get_sellable_items(self) -> List:
        """売却可能アイテムを取得
        
        Returns:
            売却可能なアイテムのリスト（キャラクター所持品+倉庫）
        """
        if not self.has_party():
            return []
        
        sellable_items = []
        
        # パーティメンバーの所持アイテム
        for character in self.get_party_members():
            if hasattr(character, 'get_personal_inventory'):
                try:
                    inventory = character.get_personal_inventory()
                    sellable_items.extend(inventory)
                except Exception as e:
                    logger.warning(f"キャラクターインベントリ取得エラー: {character.name} - {e}")
        
        # TODO: 倉庫アイテムの取得（Phase 4で実装）
        
        return sellable_items
    
    def filter_items_by_category(self, category: str) -> List:
        """カテゴリでアイテムをフィルタリング
        
        Args:
            category: アイテムカテゴリ
            
        Returns:
            指定カテゴリのアイテムリスト
        """
        if category == 'ALL':
            return self.get_purchasable_items()
        
        filtered_items = []
        for item in self.get_purchasable_items():
            item_category = getattr(item, 'item_type', 'UNKNOWN')
            if isinstance(item_category, str):
                if item_category == category:
                    filtered_items.append(item)
            elif hasattr(item_category, 'value'):
                if item_category.value == category:
                    filtered_items.append(item)
        
        return filtered_items
    
    def calculate_purchase_cost(self, item, quantity: int) -> int:
        """購入コストを計算
        
        Args:
            item: 対象アイテム
            quantity: 数量
            
        Returns:
            購入コスト（ゴールド）
        """
        if not item or quantity <= 0:
            return 0
        
        item_price = getattr(item, 'price', 0)
        return item_price * quantity
    
    def calculate_sell_price(self, item, quantity: int) -> int:
        """売却価格を計算
        
        Args:
            item: 対象アイテム
            quantity: 数量
            
        Returns:
            売却価格（ゴールド）
        """
        if not item or quantity <= 0:
            return 0
        
        item_price = getattr(item, 'price', 0)
        # 売却価格は購入価格の半額
        sell_price = item_price // 2
        return sell_price * quantity
    
    def get_max_purchasable_quantity(self, item) -> int:
        """最大購入可能数量を取得
        
        Args:
            item: 対象アイテム
            
        Returns:
            最大購入可能数量
        """
        if not item or not self.has_party():
            return 0
        
        item_price = getattr(item, 'price', 0)
        if item_price <= 0:
            return 99  # 無料アイテムの場合の上限
        
        party_gold = getattr(self.current_party, 'gold', 0)
        return party_gold // item_price
    
    def handle_service_request(self, service_type: str, **kwargs) -> bool:
        """サービスリクエストの処理
        
        Args:
            service_type: サービスタイプ（'purchase' または 'sell'）
            **kwargs: サービス固有のパラメータ
                - item: 対象アイテム
                - quantity: 数量
                - category: カテゴリ（category_filter時）
                
        Returns:
            サービス処理が成功したらTrue
        """
        if not self.can_provide_service(service_type):
            logger.warning(f"提供できないサービスです: {service_type}")
            return False
        
        item = kwargs.get('item')
        quantity = kwargs.get('quantity', 1)
        
        if service_type == 'purchase':
            return self._perform_purchase(item, quantity)
        elif service_type == 'sell':
            return self._perform_sell(item, quantity)
        elif service_type == 'category_filter':
            category = kwargs.get('category', 'ALL')
            return self._apply_category_filter(category)
        elif service_type == 'quantity_select':
            return self._handle_quantity_selection(item, quantity)
        
        return False
    
    def _perform_purchase(self, item, quantity: int) -> bool:
        """購入処理を実行
        
        Args:
            item: 対象アイテム
            quantity: 数量
            
        Returns:
            購入が成功したらTrue
        """
        if not item or not self.has_party():
            logger.warning("購入処理に必要な情報が不足しています")
            return False
        
        cost = self.calculate_purchase_cost(item, quantity)
        party_gold = getattr(self.current_party, 'gold', 0)
        
        if party_gold < cost:
            logger.warning(f"ゴールドが不足しています: 必要{cost}G, 現在{party_gold}G")
            return False
        
        # 購入処理（実装時に詳細を追加）
        # TODO: パーティのゴールド減少
        # TODO: アイテムをインベントリに追加
        
        item_name = getattr(item, 'get_name', lambda: str(item))()
        logger.info(f"{item_name} x{quantity}を購入しました（コスト: {cost}G）")
        return True
    
    def _perform_sell(self, item, quantity: int) -> bool:
        """売却処理を実行
        
        Args:
            item: 対象アイテム
            quantity: 数量
            
        Returns:
            売却が成功したらTrue
        """
        if not item or not self.has_party():
            logger.warning("売却処理に必要な情報が不足しています")
            return False
        
        price = self.calculate_sell_price(item, quantity)
        
        # 売却処理（実装時に詳細を追加）
        # TODO: アイテムをインベントリから削除
        # TODO: パーティのゴールド増加
        
        item_name = getattr(item, 'get_name', lambda: str(item))()
        logger.info(f"{item_name} x{quantity}を売却しました（価格: {price}G）")
        return True
    
    def _apply_category_filter(self, category: str) -> bool:
        """カテゴリフィルターを適用
        
        Args:
            category: フィルターするカテゴリ
            
        Returns:
            フィルター適用が成功したらTrue
        """
        self.selected_category = category
        filtered_items = self.filter_items_by_category(category)
        
        logger.info(f"カテゴリ'{category}'でフィルタリング: {len(filtered_items)}個のアイテム")
        return True
    
    def _handle_quantity_selection(self, item, quantity: int) -> bool:
        """数量選択を処理
        
        Args:
            item: 対象アイテム
            quantity: 選択された数量
            
        Returns:
            数量選択が成功したらTrue
        """
        if quantity <= 0:
            logger.warning("無効な数量が選択されました")
            return False
        
        max_quantity = self.get_max_purchasable_quantity(item)
        if quantity > max_quantity:
            logger.warning(f"選択数量が上限を超えています: {quantity} > {max_quantity}")
            return False
        
        self.selected_quantity = quantity
        logger.info(f"数量 {quantity} が選択されました")
        return True
    
    def create_service_ui(self):
        """サービス用UIの作成
        
        商店取引選択、アイテム一覧、カテゴリ選択、数量選択などのUI要素を作成。
        """
        # 実装はPhase 2の具体的なUI実装時に追加
        # 現在はテスト用のプレースホルダー
        pass
    
    def handle_message(self, message_type: str, message_data: Dict[str, Any]) -> bool:
        """Windowメッセージの処理
        
        Args:
            message_type: メッセージタイプ
            message_data: メッセージデータ
            
        Returns:
            メッセージ処理が成功したらTrue
        """
        if message_type == 'transaction_selected':
            transaction_type = message_data.get('transaction')
            target_item = message_data.get('item')
            quantity = message_data.get('quantity', 1)
            
            if transaction_type and target_item:
                return self.handle_service_request(transaction_type, item=target_item, quantity=quantity)
        
        elif message_type == 'category_selected':
            category = message_data.get('category')
            if category:
                return self.handle_service_request('category_filter', category=category)
        
        # 親クラスのメッセージ処理にフォールバック
        return super().handle_message(message_type, message_data) if hasattr(super(), 'handle_message') else False
    
    def create(self) -> None:
        """ウィンドウの作成
        
        Windowクラスの抽象メソッド実装。
        実際のUI要素の作成はcreate_service_ui()で行う。
        """
        self.create_service_ui()
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """イベント処理
        
        Args:
            event: pygameイベント
            
        Returns:
            イベントを処理したらTrue
        """
        # 商店取引固有のイベント処理
        # 現在はプレースホルダー実装
        return False