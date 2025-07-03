"""
InnFacilityHandler - Inn施設の統一ハンドラー

Inn施設クラスの90-99%重複を統合
BaseFacilityHandlerを継承して、Inn固有の操作を実装
"""

from typing import Dict, List, Optional, Any
from src.overworld.facilities.base_facility_handler import (
    BaseFacilityHandler, FacilityOperationResult, OperationType
)
from src.overworld.base_facility import FacilityType
from src.character.character import Character
from src.core.config_manager import config_manager
from src.utils.logger import logger


class InnFacilityHandler(BaseFacilityHandler):
    """Inn施設の統一ハンドラー"""
    
    def __init__(self):
        super().__init__(
            facility_id="inn",
            facility_type=FacilityType.INN,
            name_key="facility.inn"
        )
        
        # Inn固有の状態
        self.current_character: Optional[Character] = None
        
        logger.info("InnFacilityHandler初期化完了")
    
    def _execute_operation(self, operation: str, **kwargs) -> FacilityOperationResult:
        """
        Inn固有の操作実行
        
        Args:
            operation: 操作タイプ
            **kwargs: 操作パラメータ
            
        Returns:
            FacilityOperationResult: 実行結果
        """
        # Inn操作マップ（Strategy Pattern）
        operation_map = {
            'show_service': self._handle_show_service,
            'show_adventure_preparation': self._handle_adventure_preparation,
            'show_item_management': self._handle_item_management,
            'show_spell_management': self._handle_spell_management,
            'show_equipment_management': self._handle_equipment_management,
            'talk_to_innkeeper': self._handle_talk_to_innkeeper,
            'show_travel_info': self._handle_travel_info,
            'show_tavern_rumors': self._handle_tavern_rumors,
            'change_party_name': self._handle_change_party_name
        }
        
        if operation not in operation_map:
            return self.handle_error(
                'unknown_operation',
                f"未知のInn操作: {operation}"
            )
        
        try:
            return operation_map[operation](**kwargs)
        except Exception as e:
            return self.handle_error(
                'operation_execution_error',
                f"Inn操作実行エラー({operation}): {str(e)}"
            )
    
    def _handle_show_service(self, service_type: str, **kwargs) -> FacilityOperationResult:
        """
        Innサービス表示の統一ハンドラー
        
        Args:
            service_type: サービスタイプ
            **kwargs: サービスパラメータ
            
        Returns:
            FacilityOperationResult: 実行結果
        """
        # サービス設定を作成
        service_config = self._create_inn_service_config(service_type, **kwargs)
        
        # 統一されたウィンドウ表示メソッドを使用
        return self.show_facility_window('inn_service', service_config)
    
    def _create_inn_service_config(self, service_type: str, **kwargs) -> Dict[str, Any]:
        """
        Innサービス設定の統一作成メソッド
        
        Args:
            service_type: サービスタイプ
            **kwargs: 追加パラメータ
            
        Returns:
            Dict[str, Any]: サービス設定
        """
        base_config = {
            'service_type': service_type,
            'party': self.current_party,
            'character': kwargs.get('character', self.current_character)
        }
        
        # サービスタイプ別の設定
        service_specific_configs = {
            'rest': {
                'rest_type': kwargs.get('rest_type', 'basic'),
                'duration': kwargs.get('duration', 'full'),
                'cost': kwargs.get('cost', 10)
            },
            'item_management': {
                'action': kwargs.get('action', 'view'),
                'item_filter': kwargs.get('item_filter', 'all')
            },
            'spell_management': {
                'spell_type': kwargs.get('spell_type', 'wizard'),
                'action': kwargs.get('action', 'view')
            },
            'equipment_management': {
                'equipment_type': kwargs.get('equipment_type', 'all'),
                'action': kwargs.get('action', 'view')
            }
        }
        
        if service_type in service_specific_configs:
            base_config.update(service_specific_configs[service_type])
        
        return base_config
    
    def _handle_adventure_preparation(self, **kwargs) -> FacilityOperationResult:
        """冒険準備サービスの表示"""
        return self._handle_show_service('adventure_preparation', **kwargs)
    
    def _handle_item_management(self, **kwargs) -> FacilityOperationResult:
        """アイテム管理サービスの表示"""
        return self._handle_show_service('item_management', **kwargs)
    
    def _handle_spell_management(self, **kwargs) -> FacilityOperationResult:
        """魔法管理サービスの表示"""
        return self._handle_show_service('spell_management', **kwargs)
    
    def _handle_equipment_management(self, **kwargs) -> FacilityOperationResult:
        """装備管理サービスの表示"""
        return self._handle_show_service('equipment_management', **kwargs)
    
    def _handle_talk_to_innkeeper(self, **kwargs) -> FacilityOperationResult:
        """宿屋主人との会話"""
        try:
            # 宿屋主人との会話内容を取得
            innkeeper_messages = config_manager.get_text("inn.innkeeper_dialog")
            innkeeper_title = config_manager.get_text("inn.innkeeper_title")
            
            # innkeeper_messagesが辞書でない場合の対応
            if isinstance(innkeeper_messages, str):
                greeting_message = innkeeper_messages
            elif isinstance(innkeeper_messages, dict):
                greeting_message = innkeeper_messages.get('greeting', 'ようこそ、宿屋へ！')
            else:
                greeting_message = 'ようこそ、宿屋へ！'
            
            return self.show_dialog(
                'information',
                innkeeper_title,
                greeting_message
            )
            
        except Exception as e:
            return self.handle_error(
                'innkeeper_dialog_error',
                f"宿屋主人との会話でエラー: {str(e)}"
            )
    
    def _handle_travel_info(self, **kwargs) -> FacilityOperationResult:
        """旅の情報表示"""
        try:
            travel_info = config_manager.get_text("inn.travel_info")
            travel_info_title = config_manager.get_text("inn.travel_info_title")
            
            # travel_infoが辞書でない場合の対応
            if isinstance(travel_info, str):
                info_message = travel_info
            elif isinstance(travel_info, dict):
                info_message = travel_info.get('general', '冒険者への有用な情報をお伝えします。')
            else:
                info_message = '冒険者への有用な情報をお伝えします。'
            
            return self.show_dialog(
                'information',
                travel_info_title,
                info_message
            )
            
        except Exception as e:
            return self.handle_error(
                'travel_info_error',
                f"旅の情報表示でエラー: {str(e)}"
            )
    
    def _handle_tavern_rumors(self, **kwargs) -> FacilityOperationResult:
        """酒場の噂話表示"""
        try:
            rumors = config_manager.get_text("inn.tavern_rumors")
            rumors_title = config_manager.get_text("inn.tavern_rumors_title")
            
            # rumorsが辞書でない場合の対応
            if isinstance(rumors, str):
                rumor_message = rumors
            elif isinstance(rumors, dict):
                rumor_message = rumors.get('current', '最近は不思議な話をよく聞きますね...')
            else:
                rumor_message = '最近は不思議な話をよく聞きますね...'
            
            return self.show_dialog(
                'information',
                rumors_title,
                rumor_message
            )
            
        except Exception as e:
            return self.handle_error(
                'tavern_rumors_error',
                f"酒場の噂話表示でエラー: {str(e)}"
            )
    
    def _handle_change_party_name(self, new_name: Optional[str] = None, **kwargs) -> FacilityOperationResult:
        """パーティ名変更"""
        try:
            if not self.current_party:
                return self.handle_error(
                    'no_party',
                    "パーティが設定されていません"
                )
            
            if new_name:
                # 新しい名前が指定された場合は変更
                old_name = self.current_party.name
                self.current_party.name = new_name
                
                logger.info(f"パーティ名を変更: {old_name} -> {new_name}")
                
                return FacilityOperationResult(
                    success=True,
                    message=f"パーティ名を '{new_name}' に変更しました",
                    data={'old_name': old_name, 'new_name': new_name}
                )
            else:
                # 名前変更UIを表示
                return self.show_facility_window('party_name_change', {
                    'current_name': self.current_party.name,
                    'party': self.current_party
                })
                
        except Exception as e:
            return self.handle_error(
                'party_name_change_error',
                f"パーティ名変更でエラー: {str(e)}"
            )
    
    def _validate_specific_operation(self, operation: str, **kwargs) -> FacilityOperationResult:
        """Inn固有の操作検証"""
        # キャラクター要求操作の検証
        character_required_operations = [
            'show_spell_management',
            'show_equipment_management'
        ]
        
        if operation in character_required_operations:
            character = kwargs.get('character', self.current_character)
            if not character:
                return FacilityOperationResult(
                    success=False,
                    error_type='no_character',
                    message=f"操作 {operation} にはキャラクターが必要です"
                )
        
        # パーティ名変更の検証
        if operation == 'change_party_name':
            new_name = kwargs.get('new_name')
            if new_name and len(new_name.strip()) == 0:
                return FacilityOperationResult(
                    success=False,
                    error_type='invalid_party_name',
                    message="パーティ名を空にすることはできません"
                )
        
        return FacilityOperationResult(success=True)
    
    def _cleanup_specific_operation(self, operation: str, result: FacilityOperationResult) -> None:
        """Inn固有の操作後クリーンアップ"""
        # サービス表示操作後のクリーンアップ
        if operation.startswith('show_') and not result.success:
            # 失敗した場合は関連するUI要素をクリーンアップ
            self.cleanup_ui()
        
        # 特定の操作でのログ記録
        if operation == 'change_party_name' and result.success:
            logger.info(f"パーティ名変更完了: {result.data}")
    
    def set_character(self, character: Character) -> None:
        """現在のキャラクターを設定"""
        self.current_character = character
        logger.debug(f"Inn現在キャラクターを設定: {character.name if character else None}")
    
    # === レガシー互換性メソッド ===
    
    def _on_enter_specific(self):
        """Inn固有の入場処理"""
        logger.debug("Inn入場処理実行")
    
    def _on_exit_specific(self):
        """Inn固有の退場処理"""
        logger.debug("Inn退場処理実行")
    
    def get_inn_menu_config(self) -> Dict[str, Any]:
        """Inn用のメニュー設定を取得"""
        menu_items = [
            {
                'id': 'adventure_preparation',
                'label': config_manager.get_text("inn_menu.adventure_preparation"),
                'type': 'action',
                'enabled': True,
                'operation': 'show_adventure_preparation'
            },
            {
                'id': 'item_storage',
                'label': config_manager.get_text("inn_menu.item_storage"),
                'type': 'action',
                'enabled': True,
                'operation': 'show_item_management'
            },
            {
                'id': 'talk_innkeeper',
                'label': config_manager.get_text("inn_menu.talk_innkeeper"),
                'type': 'action',
                'enabled': True,
                'operation': 'talk_to_innkeeper'
            },
            {
                'id': 'travel_info',
                'label': config_manager.get_text("inn_menu.travel_info"),
                'type': 'action',
                'enabled': True,
                'operation': 'show_travel_info'
            },
            {
                'id': 'tavern_rumors',
                'label': config_manager.get_text("inn_menu.tavern_rumors"),
                'type': 'action',
                'enabled': True,
                'operation': 'show_tavern_rumors'
            },
            {
                'id': 'change_party_name',
                'label': config_manager.get_text("inn_menu.change_party_name"),
                'type': 'action',
                'enabled': self.current_party is not None,
                'operation': 'change_party_name'
            },
            {
                'id': 'exit',
                'label': config_manager.get_text("menu.exit"),
                'type': 'exit',
                'enabled': True
            }
        ]
        
        return {
            'facility_type': FacilityType.INN.value,
            'facility_name': config_manager.get_text("facility.inn"),
            'menu_items': menu_items,
            'party': self.current_party,
            'show_party_info': False,
            'show_gold': False
        }