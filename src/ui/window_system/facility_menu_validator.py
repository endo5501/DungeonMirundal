"""
FacilityMenuValidator クラス

施設メニュー項目の利用可能性チェック

Fowler式リファクタリング：Extract Class パターン
"""

from typing import Dict, List, Any, Optional, Callable
from src.ui.window_system.facility_menu_types import FacilityMenuItem, FacilityType
from src.utils.logger import logger


class FacilityMenuValidator:
    """
    施設メニュー項目検証クラス
    
    メニュー項目の利用可能性チェック、条件評価を担当
    """
    
    def __init__(self, facility_type: FacilityType):
        """
        バリデーターを初期化
        
        Args:
            facility_type: 施設タイプ
        """
        self.facility_type = facility_type
        self.custom_validators: Dict[str, Callable[[Any], bool]] = {}
        
        logger.debug(f"FacilityMenuValidatorを初期化: {facility_type}")
    
    def validate_item_availability(self, item: FacilityMenuItem, party: Any) -> bool:
        """項目の利用可能性を検証"""
        if not item.visible:
            logger.debug(f"項目は非表示: {item.item_id}")
            return False
        
        if not item.enabled:
            logger.debug(f"項目は無効: {item.item_id}")
            return False
        
        # コスト条件チェック
        if not self._validate_cost_requirement(item, party):
            logger.debug(f"コスト条件未満: {item.item_id}")
            return False
        
        # カスタム条件チェック
        if not self._validate_custom_condition(item, party):
            logger.debug(f"カスタム条件未満: {item.item_id}")
            return False
        
        logger.debug(f"項目利用可能: {item.item_id}")
        return True
    
    def validate_multiple_items(self, items: List[FacilityMenuItem], party: Any) -> Dict[str, bool]:
        """複数項目の利用可能性を一括検証"""
        results = {}
        
        for item in items:
            results[item.item_id] = self.validate_item_availability(item, party)
        
        available_count = sum(1 for available in results.values() if available)
        logger.debug(f"一括検証結果: {available_count}/{len(items)} 項目が利用可能")
        
        return results
    
    def check_party_requirements(self, party: Any) -> Dict[str, Any]:
        """パーティの要件をチェック"""
        requirements = {
            'has_gold': False,
            'gold_amount': 0,
            'has_dead_members': False,
            'has_items': False,
            'is_full_hp': False,
            'member_count': 0
        }
        
        if party:
            # 所持金チェック
            if hasattr(party, 'get_gold'):
                requirements['gold_amount'] = party.get_gold()
                requirements['has_gold'] = requirements['gold_amount'] > 0
            
            # 死亡メンバーチェック
            if hasattr(party, 'has_dead_members'):
                requirements['has_dead_members'] = party.has_dead_members()
            
            # アイテム所持チェック
            if hasattr(party, 'has_items'):
                requirements['has_items'] = party.has_items()
            
            # 満HP状態チェック
            if hasattr(party, 'is_full_hp'):
                requirements['is_full_hp'] = party.is_full_hp()
            
            # メンバー数チェック
            if hasattr(party, 'get_member_count'):
                requirements['member_count'] = party.get_member_count()
        
        logger.debug(f"パーティ要件チェック完了: {requirements}")
        return requirements
    
    def add_custom_validator(self, condition_name: str, validator: Callable[[Any], bool]) -> None:
        """カスタムバリデーターを追加"""
        self.custom_validators[condition_name] = validator
        logger.debug(f"カスタムバリデーター追加: {condition_name}")
    
    def remove_custom_validator(self, condition_name: str) -> bool:
        """カスタムバリデーターを削除"""
        if condition_name in self.custom_validators:
            del self.custom_validators[condition_name]
            logger.debug(f"カスタムバリデーター削除: {condition_name}")
            return True
        
        logger.warning(f"カスタムバリデーターが見つかりません: {condition_name}")
        return False
    
    def validate_facility_specific_requirements(self, item: FacilityMenuItem, party: Any) -> bool:
        """施設固有の要件を検証"""
        # 施設タイプ別の固有ロジック
        if self.facility_type == FacilityType.TEMPLE:
            return self._validate_temple_requirements(item, party)
        elif self.facility_type == FacilityType.SHOP:
            return self._validate_shop_requirements(item, party)
        elif self.facility_type == FacilityType.INN:
            return self._validate_inn_requirements(item, party)
        elif self.facility_type == FacilityType.GUILD:
            return self._validate_guild_requirements(item, party)
        
        # デフォルトは常にTrue
        return True
    
    def _validate_cost_requirement(self, item: FacilityMenuItem, party: Any) -> bool:
        """コスト要件を検証"""
        if item.cost and hasattr(party, 'get_gold'):
            return party.get_gold() >= item.cost
        return True
    
    def _validate_custom_condition(self, item: FacilityMenuItem, party: Any) -> bool:
        """カスタム条件を検証"""
        if not item.condition:
            return True
        
        # カスタムバリデーターをチェック
        if item.condition in self.custom_validators:
            return self.custom_validators[item.condition](party)
        
        # 標準条件をチェック
        if item.condition == 'has_dead_members':
            return hasattr(party, 'has_dead_members') and party.has_dead_members()
        elif item.condition == 'has_items':
            return hasattr(party, 'has_items') and party.has_items()
        elif item.condition == 'is_full_hp':
            return hasattr(party, 'is_full_hp') and party.is_full_hp()
        
        # 未知の条件は常にTrue
        logger.warning(f"未知の条件: {item.condition}")
        return True
    
    def _validate_temple_requirements(self, item: FacilityMenuItem, party: Any) -> bool:
        """神殿固有の要件を検証"""
        # 蘇生サービスは死亡メンバーがいる場合のみ
        if item.item_id == 'resurrection':
            return hasattr(party, 'has_dead_members') and party.has_dead_members()
        
        # 回復は負傷者がいる場合のみ（簡略化でHP < 最大HPをチェック）
        if item.item_id == 'heal' or item.item_id == 'heal_party':
            if hasattr(party, 'is_full_hp'):
                return not party.is_full_hp()
        
        return True
    
    def _validate_shop_requirements(self, item: FacilityMenuItem, party: Any) -> bool:
        """商店固有の要件を検証"""
        # 購入は所持金が必要
        if item.item_id.startswith('buy'):
            return hasattr(party, 'get_gold') and party.get_gold() > 0
        
        # 売却はアイテムが必要
        if item.item_id.startswith('sell'):
            return hasattr(party, 'has_items') and party.has_items()
        
        return True
    
    def _validate_inn_requirements(self, item: FacilityMenuItem, party: Any) -> bool:
        """宿屋固有の要件を検証"""
        # 休息は通常常に利用可能
        if item.item_id == 'rest':
            return True
        
        # 倉庫はアイテムまたは空きスペースが必要
        if item.item_id == 'storage':
            return True  # 簡略化
        
        return True
    
    def _validate_guild_requirements(self, item: FacilityMenuItem, party: Any) -> bool:
        """ギルド固有の要件を検証"""
        # キャラクター作成は通常常に利用可能
        if item.item_id == 'create_character':
            return True
        
        # パーティ編成はメンバーがいる場合に利用可能
        if item.item_id == 'party_formation':
            if hasattr(party, 'get_member_count'):
                return party.get_member_count() > 0
        
        return True
    
    def get_validation_summary(self, items: List[FacilityMenuItem], party: Any) -> Dict[str, Any]:
        """検証サマリーを取得"""
        party_requirements = self.check_party_requirements(party)
        item_validations = self.validate_multiple_items(items, party)
        
        available_items = [item_id for item_id, available in item_validations.items() if available]
        unavailable_items = [item_id for item_id, available in item_validations.items() if not available]
        
        return {
            'facility_type': self.facility_type.value,
            'party_requirements': party_requirements,
            'total_items': len(items),
            'available_items': available_items,
            'unavailable_items': unavailable_items,
            'availability_rate': len(available_items) / len(items) if items else 0.0
        }