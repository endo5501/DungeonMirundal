"""宿屋サービス専用ウィンドウ"""

from typing import Dict, Any, List, Optional
import pygame
import pygame_gui
from src.ui.window_system.facility_sub_window import FacilitySubWindow
from src.core.config_manager import config_manager
from src.utils.logger import logger


class InnServiceWindow(FacilitySubWindow):
    """宿屋サービス専用ウィンドウ
    
    冒険準備、アイテム管理、魔術管理、装備管理を統合したタブベースWindow実装。
    レガシーメニューの12箇所を代替する最も複雑な統合Window。
    """
    
    def __init__(self, window_id: str, facility_config: Dict[str, Any]):
        """初期化
        
        Args:
            window_id: ウィンドウID（例: 'inn_service'）
            facility_config: 宿屋設定データ
                - parent_facility: 親宿屋インスタンス
                - current_party: 現在のパーティ
                - service_types: ['adventure_prep', 'item_management', 'magic_management', 'equipment_management']
                - selected_character: 選択されたキャラクター（オプション）
                - title: ウィンドウタイトル（オプション）
        """
        super().__init__(window_id, facility_config)
        
        # 宿屋固有の設定
        self.title = facility_config.get('title', '宿屋サービス')
        self.service_types = facility_config.get('service_types', ['adventure_prep'])
        self.available_services = self._validate_service_types(self.service_types)
        self.selected_character = facility_config.get('selected_character')
        
        # タブ管理
        self.current_tab = None
        self.tab_contents = {}
        
        # UI要素
        self.tab_container = None
        self.character_selector = None
        self.service_content_area = None
        self.action_buttons = {}
        self.back_button = None
        
        # 選択状態
        self.selected_service = None
        self.selected_item = None
        self.selected_spell = None
        self.selected_equipment_slot = None
        
    def _validate_service_types(self, service_types: List[str]) -> List[str]:
        """サービスタイプを検証
        
        Args:
            service_types: サービスタイプリスト
            
        Returns:
            有効なサービスタイプのリスト
        """
        valid_types = [
            'adventure_prep',      # 冒険準備
            'item_management',     # アイテム管理
            'magic_management',    # 魔術管理
            'equipment_management', # 装備管理
            'spell_slot_management', # 魔法スロット管理（高度）
            'party_status'         # パーティ状況確認
        ]
        return [t for t in service_types if t in valid_types]
    
    def get_adventure_prep_options(self) -> List[str]:
        """冒険準備オプションを取得
        
        Returns:
            利用可能な準備オプションのリスト
        """
        base_options = ['item_management', 'magic_management', 'equipment_management', 'party_status']
        return [option for option in base_options if self.can_provide_service(option)]
    
    def get_character_items(self, character) -> List:
        """キャラクターのアイテム一覧を取得
        
        Args:
            character: 対象キャラクター
            
        Returns:
            キャラクターの所持アイテムリスト
        """
        if not character:
            return []
        
        try:
            if hasattr(character, 'get_personal_inventory'):
                return character.get_personal_inventory()
            elif hasattr(character, 'get_inventory'):
                inventory = character.get_inventory()
                return inventory.get_all_items() if hasattr(inventory, 'get_all_items') else []
        except Exception as e:
            logger.warning(f"キャラクターアイテム取得エラー: {character.name} - {e}")
        
        return []
    
    def get_character_spell_slots(self, character) -> Dict[str, Any]:
        """キャラクターの魔術スロット情報を取得
        
        Args:
            character: 対象キャラクター
            
        Returns:
            魔術スロット情報辞書
        """
        if not character:
            return {}
        
        try:
            spellbook = character.get_spellbook() if hasattr(character, 'get_spellbook') else None
            if spellbook:
                return {
                    'available_spells': spellbook.get_available_spells() if hasattr(spellbook, 'get_available_spells') else [],
                    'equipped_spells': spellbook.get_equipped_spells() if hasattr(spellbook, 'get_equipped_spells') else {},
                    'max_slots': getattr(spellbook, 'max_slots', 0)
                }
        except Exception as e:
            logger.warning(f"魔術スロット取得エラー: {character.name} - {e}")
        
        return {'available_spells': [], 'equipped_spells': {}, 'max_slots': 0}
    
    def get_party_equipment_status(self) -> Dict[str, Any]:
        """パーティの装備状況を取得
        
        Returns:
            パーティ装備状況辞書
        """
        if not self.has_party():
            return {}
        
        equipment_status = {}
        for character in self.get_party_members():
            try:
                equipment = character.get_equipment() if hasattr(character, 'get_equipment') else None
                if equipment:
                    equipped_items = equipment.get_equipped_items() if hasattr(equipment, 'get_equipped_items') else {}
                    equipment_status[character.name] = equipped_items
                else:
                    equipment_status[character.name] = {}
            except Exception as e:
                logger.warning(f"装備状況取得エラー: {character.name} - {e}")
                equipment_status[character.name] = {}
        
        return equipment_status
    
    def get_selectable_characters(self) -> List:
        """選択可能キャラクター一覧を取得
        
        Returns:
            選択可能なキャラクターのリスト
        """
        return self.get_party_members()
    
    def get_available_tabs(self) -> List[str]:
        """利用可能タブ一覧を取得
        
        Returns:
            利用可能なタブのリスト
        """
        tab_mapping = {
            'adventure_prep': 'preparation',
            'item_management': 'items',
            'magic_management': 'magic',
            'equipment_management': 'equipment',
            'spell_slot_management': 'spell_slots',
            'party_status': 'status'
        }
        
        available_tabs = []
        for service_type in self.available_services:
            if service_type in tab_mapping:
                available_tabs.append(tab_mapping[service_type])
        
        return available_tabs
    
    def handle_spell_slot_operation(self, operation: str, **kwargs) -> bool:
        """魔法スロット操作を処理
        
        Args:
            operation: 操作タイプ（'assign', 'remove', 'swap'等）
            **kwargs: 操作固有のパラメータ
                - character: 対象キャラクター
                - spell_id: 魔法ID
                - slot_level: スロットレベル
                
        Returns:
            操作が成功したらTrue
        """
        character = kwargs.get('character')
        spell_id = kwargs.get('spell_id')
        slot_level = kwargs.get('slot_level')
        
        if not character:
            logger.warning("魔法スロット操作: キャラクターが指定されていません")
            return False
        
        try:
            spellbook = character.get_spellbook() if hasattr(character, 'get_spellbook') else None
            if not spellbook:
                logger.warning(f"魔法書が見つかりません: {character.name}")
                return False
            
            if operation == 'assign':
                # 魔法をスロットに装備
                if hasattr(spellbook, 'equip_spell'):
                    result = spellbook.equip_spell(spell_id, slot_level)
                    logger.info(f"魔法装備: {character.name} - {spell_id} (レベル{slot_level})")
                    return result
            elif operation == 'remove':
                # スロットから魔法を除去
                if hasattr(spellbook, 'unequip_spell'):
                    result = spellbook.unequip_spell(slot_level)
                    logger.info(f"魔法除去: {character.name} - レベル{slot_level}")
                    return result
            elif operation == 'swap':
                # スロット間で魔法を交換
                target_slot = kwargs.get('target_slot')
                if hasattr(spellbook, 'swap_spells'):
                    result = spellbook.swap_spells(slot_level, target_slot)
                    logger.info(f"魔法交換: {character.name} - {slot_level} <-> {target_slot}")
                    return result
            
        except Exception as e:
            logger.error(f"魔法スロット操作エラー: {operation} - {e}")
        
        return False
    
    def handle_service_request(self, service_type: str, **kwargs) -> bool:
        """サービスリクエストの処理
        
        Args:
            service_type: サービスタイプ
            **kwargs: サービス固有のパラメータ
                
        Returns:
            サービス処理が成功したらTrue
        """
        if not self.can_provide_service(service_type):
            logger.warning(f"提供できないサービスです: {service_type}")
            return False
        
        if service_type == 'adventure_prep':
            return self._handle_adventure_preparation(**kwargs)
        elif service_type == 'item_management':
            return self._handle_item_management(**kwargs)
        elif service_type == 'magic_management':
            return self._handle_magic_management(**kwargs)
        elif service_type == 'equipment_management':
            return self._handle_equipment_management(**kwargs)
        elif service_type == 'spell_slot_management':
            operation = kwargs.get('operation', 'view')
            return self.handle_spell_slot_operation(operation, **kwargs)
        elif service_type == 'party_status':
            return self._handle_party_status(**kwargs)
        
        return False
    
    def _handle_adventure_preparation(self, **kwargs) -> bool:
        """冒険準備処理
        
        Returns:
            処理が成功したらTrue
        """
        # 冒険準備の統合処理
        # 実装時に詳細を追加
        logger.info("冒険準備サービスを開始しました")
        return True
    
    def _handle_item_management(self, **kwargs) -> bool:
        """アイテム管理処理
        
        Returns:
            処理が成功したらTrue
        """
        character = kwargs.get('character')
        action = kwargs.get('action', 'view')
        
        if not character:
            logger.warning("アイテム管理: キャラクターが指定されていません")
            return False
        
        # アイテム管理処理
        # 実装時に詳細を追加
        logger.info(f"アイテム管理サービス: {character.name} - {action}")
        return True
    
    def _handle_magic_management(self, **kwargs) -> bool:
        """魔術管理処理
        
        Returns:
            処理が成功したらTrue
        """
        character = kwargs.get('character')
        magic_type = kwargs.get('magic_type', 'spell')  # 'spell' or 'prayer'
        
        if not character:
            logger.warning("魔術管理: キャラクターが指定されていません")
            return False
        
        # 魔術管理処理
        # 実装時に詳細を追加
        logger.info(f"魔術管理サービス: {character.name} - {magic_type}")
        return True
    
    def _handle_equipment_management(self, **kwargs) -> bool:
        """装備管理処理
        
        Returns:
            処理が成功したらTrue
        """
        scope = kwargs.get('scope', 'party')  # 'party' or 'character'
        
        # 装備管理処理
        # 実装時に詳細を追加
        logger.info(f"装備管理サービス: {scope}")
        return True
    
    def _handle_party_status(self, **kwargs) -> bool:
        """パーティ状況確認処理
        
        Returns:
            処理が成功したらTrue
        """
        if not self.has_party():
            logger.warning("パーティ状況確認: パーティが設定されていません")
            return False
        
        # パーティ状況確認処理
        # 実装時に詳細を追加
        logger.info("パーティ状況確認サービスを実行しました")
        return True
    
    def create_service_ui(self):
        """サービス用UIの作成
        
        タブベースの統合UI、キャラクター選択、各種サービス機能を作成。
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
        if message_type == 'tab_selected':
            tab = message_data.get('tab')
            character = message_data.get('character')
            
            if tab:
                self.current_tab = tab
                return self._switch_to_tab(tab, character)
                
        elif message_type == 'character_selected':
            character = message_data.get('character')
            if character:
                self.selected_character = character
                return True
                
        elif message_type == 'service_action':
            action = message_data.get('action')
            service_type = message_data.get('service_type')
            
            if action and service_type:
                return self.handle_service_request(service_type, **message_data)
        
        # 親クラスのメッセージ処理にフォールバック
        return super().handle_message(message_type, message_data) if hasattr(super(), 'handle_message') else False
    
    def _switch_to_tab(self, tab: str, character=None) -> bool:
        """タブを切り替える
        
        Args:
            tab: 切り替え先タブ
            character: 対象キャラクター（オプション）
            
        Returns:
            切り替えが成功したらTrue
        """
        tab_service_mapping = {
            'preparation': 'adventure_prep',
            'items': 'item_management',
            'magic': 'magic_management',
            'equipment': 'equipment_management',
            'spell_slots': 'spell_slot_management',
            'status': 'party_status'
        }
        
        service_type = tab_service_mapping.get(tab)
        if service_type and self.can_provide_service(service_type):
            self.current_tab = tab
            if character:
                self.selected_character = character
            
            logger.info(f"タブ切り替え: {tab} (サービス: {service_type})")
            return True
        
        return False
    
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
        # 宿屋サービス固有のイベント処理
        # 現在はプレースホルダー実装
        return False