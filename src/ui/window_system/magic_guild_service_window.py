"""魔術協会サービス専用ウィンドウ"""

from typing import Dict, Any, List, Optional
import pygame
import pygame_gui
from src.ui.window_system.facility_sub_window import FacilitySubWindow
from src.core.config_manager import config_manager
from src.utils.logger import logger


class MagicGuildServiceWindow(FacilitySubWindow):
    """魔術協会サービス専用ウィンドウ
    
    魔術書店、魔法習得、アイテム鑑定、魔法分析、キャラクター分析を統合したWindow実装。
    レガシーメニューの6箇所（spellbook_category_menu, available_spells_menu, identification_menu, 
    analysis_menu, character_analysis_menu, spell_usage_menu）を代替。
    """
    
    def __init__(self, window_id: str, facility_config: Dict[str, Any]):
        """初期化
        
        Args:
            window_id: ウィンドウID（例: 'magic_guild_service'）
            facility_config: 魔術協会設定データ
                - parent_facility: 親魔術協会インスタンス
                - current_party: 現在のパーティ
                - service_types: ['spellbook_shop', 'spell_learning', 'identification', 'analysis']
                - selected_character: 選択されたキャラクター（オプション）
                - title: ウィンドウタイトル（オプション）
        """
        super().__init__(window_id, facility_config)
        
        # 魔術協会固有の設定
        self.title = facility_config.get('title', '魔術協会サービス')
        self.service_types = facility_config.get('service_types', ['spellbook_shop'])
        self.available_services = self._validate_service_types(self.service_types)
        self.selected_character = facility_config.get('selected_character')
        
        # UI要素
        self.service_buttons = {}
        self.spellbook_category_list = None
        self.available_spells_list = None
        self.identification_interface = None
        self.analysis_interface = None
        self.character_selector = None
        self.back_button = None
        
        # 選択状態
        self.selected_service = None
        self.selected_category = None
        self.selected_spell = None
        self.selected_item = None
        
    def _validate_service_types(self, service_types: List[str]) -> List[str]:
        """サービスタイプを検証
        
        Args:
            service_types: サービスタイプリスト
            
        Returns:
            有効なサービスタイプのリスト
        """
        valid_types = [
            'spellbook_shop',       # 魔術書店
            'spell_learning',       # 魔法習得
            'identification',       # アイテム鑑定
            'analysis',            # 魔法分析
            'character_analysis',   # キャラクター分析
            'spell_usage_check'     # 魔法使用回数確認
        ]
        return [t for t in service_types if t in valid_types]
    
    def get_spellbook_categories(self) -> List[str]:
        """魔術書カテゴリを取得
        
        Returns:
            利用可能な魔術書カテゴリのリスト
        """
        # 基本的な魔法カテゴリ
        base_categories = [
            'offensive',    # 攻撃魔法
            'defensive',    # 防御魔法
            'healing',      # 回復魔法
            'utility',      # 汎用魔法
            'prayer',       # 祈祷魔法
            'special'       # 特殊魔法
        ]
        
        # 親施設から利用可能なカテゴリを取得
        if hasattr(self.parent_facility, 'get_available_spell_categories'):
            try:
                categories = self.parent_facility.get_available_spell_categories()
                # 有効なリストが返された場合のみ使用
                if isinstance(categories, list) and len(categories) > 0:
                    return categories
            except Exception as e:
                logger.warning(f"魔術書カテゴリ取得エラー: {e}")
        
        return base_categories
    
    def get_available_spells_for_character(self, character) -> List:
        """キャラクターが習得可能な魔法を取得
        
        Args:
            character: 対象キャラクター
            
        Returns:
            習得可能な魔法のリスト
        """
        if not character:
            return []
        
        try:
            # キャラクターの職業とレベルに基づいて習得可能魔法を取得
            if hasattr(character, 'get_learnable_spells'):
                return character.get_learnable_spells()
            elif hasattr(self.parent_facility, 'get_learnable_spells_for_character'):
                return self.parent_facility.get_learnable_spells_for_character(character)
        except Exception as e:
            logger.warning(f"習得可能魔法取得エラー: {character.name} - {e}")
        
        return []
    
    def get_identifiable_items(self) -> List:
        """鑑定可能アイテムを取得
        
        Returns:
            鑑定可能なアイテムのリスト（パーティ所持品）
        """
        if not self.has_party():
            return []
        
        identifiable_items = []
        
        # パーティメンバーの所持アイテムから未鑑定アイテムを取得
        for character in self.get_party_members():
            if hasattr(character, 'get_personal_inventory'):
                try:
                    inventory = character.get_personal_inventory()
                    for item in inventory:
                        # 未鑑定フラグがあるアイテムを収集
                        if hasattr(item, 'is_identified') and not item.is_identified:
                            identifiable_items.append(item)
                except Exception as e:
                    logger.warning(f"キャラクターインベントリ取得エラー: {character.name} - {e}")
        
        return identifiable_items
    
    def get_analyzable_spells(self) -> List:
        """分析可能魔法を取得
        
        Returns:
            分析可能な魔法のリスト
        """
        analyzable_spells = []
        
        if not self.has_party():
            return analyzable_spells
        
        # パーティメンバーの習得済み魔法を取得
        for character in self.get_party_members():
            try:
                spellbook = character.get_spellbook() if hasattr(character, 'get_spellbook') else None
                if spellbook and hasattr(spellbook, 'learned_spells'):
                    analyzable_spells.extend(spellbook.learned_spells)
            except Exception as e:
                logger.warning(f"スペルブック取得エラー: {character.name} - {e}")
        
        # 重複除去
        return list(set(analyzable_spells))
    
    def get_character_spell_usage_data(self, character) -> Dict[str, Any]:
        """キャラクターの魔法使用状況データを取得
        
        Args:
            character: 対象キャラクター
            
        Returns:
            魔法使用状況データ辞書
        """
        if not character:
            return {}
        
        try:
            spellbook = character.get_spellbook() if hasattr(character, 'get_spellbook') else None
            if spellbook:
                return {
                    'equipped_spells': spellbook.get_equipped_spells() if hasattr(spellbook, 'get_equipped_spells') else {},
                    'spell_slots': spellbook.spell_slots if hasattr(spellbook, 'spell_slots') else {},
                    'remaining_uses': spellbook.get_remaining_uses() if hasattr(spellbook, 'get_remaining_uses') else {}
                }
        except Exception as e:
            logger.warning(f"魔法使用状況取得エラー: {character.name} - {e}")
        
        return {'equipped_spells': {}, 'spell_slots': {}, 'remaining_uses': {}}
    
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
        
        if service_type == 'spellbook_shop':
            return self._handle_spellbook_shop(**kwargs)
        elif service_type == 'spell_learning':
            return self._handle_spell_learning(**kwargs)
        elif service_type == 'identification':
            return self._handle_identification(**kwargs)
        elif service_type == 'analysis':
            return self._handle_spell_analysis(**kwargs)
        elif service_type == 'character_analysis':
            return self._handle_character_analysis(**kwargs)
        elif service_type == 'spell_usage_check':
            return self._handle_spell_usage_check(**kwargs)
        
        return False
    
    def _handle_spellbook_shop(self, **kwargs) -> bool:
        """魔術書店処理
        
        Returns:
            処理が成功したらTrue
        """
        category = kwargs.get('category', 'all')
        
        # 魔術書店処理
        # 実装時に詳細を追加
        logger.info(f"魔術書店サービス: カテゴリ '{category}'")
        return True
    
    def _handle_spell_learning(self, **kwargs) -> bool:
        """魔法習得処理
        
        Returns:
            処理が成功したらTrue
        """
        character = kwargs.get('character')
        spell_id = kwargs.get('spell_id')
        
        if not character:
            logger.warning("魔法習得: キャラクターが指定されていません")
            return False
        
        # 魔法習得処理
        # 実装時に詳細を追加
        logger.info(f"魔法習得サービス: {character.name} - {spell_id}")
        return True
    
    def _handle_identification(self, **kwargs) -> bool:
        """アイテム鑑定処理
        
        Returns:
            処理が成功したらTrue
        """
        item = kwargs.get('item')
        
        if not item:
            logger.warning("アイテム鑑定: 対象アイテムが指定されていません")
            return False
        
        # アイテム鑑定処理
        # 実装時に詳細を追加
        logger.info(f"アイテム鑑定サービス: {item}")
        return True
    
    def _handle_spell_analysis(self, **kwargs) -> bool:
        """魔法分析処理
        
        Returns:
            処理が成功したらTrue
        """
        spell_id = kwargs.get('spell_id')
        
        if not spell_id:
            logger.warning("魔法分析: 対象魔法が指定されていません")
            return False
        
        # 魔法分析処理
        # 実装時に詳細を追加
        logger.info(f"魔法分析サービス: {spell_id}")
        return True
    
    def _handle_character_analysis(self, **kwargs) -> bool:
        """キャラクター分析処理
        
        Returns:
            処理が成功したらTrue
        """
        character = kwargs.get('character')
        
        if not character:
            logger.warning("キャラクター分析: 対象キャラクターが指定されていません")
            return False
        
        # キャラクター分析処理
        # 実装時に詳細を追加
        logger.info(f"キャラクター分析サービス: {character.name}")
        return True
    
    def _handle_spell_usage_check(self, **kwargs) -> bool:
        """魔法使用回数確認処理
        
        Returns:
            処理が成功したらTrue
        """
        character = kwargs.get('character')
        
        if not character:
            logger.warning("魔法使用回数確認: 対象キャラクターが指定されていません")
            return False
        
        # 魔法使用回数確認処理
        # 実装時に詳細を追加
        logger.info(f"魔法使用回数確認サービス: {character.name}")
        return True
    
    def create_service_ui(self):
        """サービス用UIの作成
        
        魔術協会サービス選択、カテゴリ選択、魔法リスト、鑑定インターフェースなどのUI要素を作成。
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
        if message_type == 'service_selected':
            service_type = message_data.get('service')
            
            if service_type:
                self.selected_service = service_type
                return self.handle_service_request(service_type, **message_data)
                
        elif message_type == 'category_selected':
            category = message_data.get('category')
            if category:
                self.selected_category = category
                return self.handle_service_request('spellbook_shop', category=category)
        
        elif message_type == 'spell_selected':
            spell_id = message_data.get('spell_id')
            character = message_data.get('character')
            
            if spell_id and character:
                return self.handle_service_request('spell_learning', character=character, spell_id=spell_id)
        
        elif message_type == 'item_identification_requested':
            item = message_data.get('item')
            if item:
                return self.handle_service_request('identification', item=item)
        
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
        # 魔術協会サービス固有のイベント処理
        # 現在はプレースホルダー実装
        return False