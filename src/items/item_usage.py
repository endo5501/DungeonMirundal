"""アイテム使用システム"""

from typing import Dict, List, Optional, Any, Tuple
from enum import Enum

from src.items.item import Item, ItemInstance, ItemType, item_manager
from src.character.character import Character, CharacterStatus
from src.character.party import Party
from src.utils.logger import logger

# アイテム使用システム定数
CONSUME_QUANTITY = 1
MINIMUM_REVIVE_HP = 1
PERCENT_DIVISOR = 100
ZERO_QUANTITY = 0


class UsageResult(Enum):
    """使用結果"""
    SUCCESS = "success"
    FAILED = "failed"
    INVALID_TARGET = "invalid_target"
    INVALID_ITEM = "invalid_item"
    INSUFFICIENT_QUANTITY = "insufficient_quantity"
    CANNOT_USE = "cannot_use"


class ItemUsageManager:
    """アイテム使用管理システム"""
    
    def __init__(self):
        # アイテム効果ハンドラーを登録
        self.effect_handlers = {
            'heal_hp': self._handle_hp_healing,
            'heal_mp': self._handle_mp_healing,
            'restore_mp': self._handle_mp_healing,  # restore_mpもheal_mpと同じ処理
            'cure_poison': self._handle_cure_poison,
            'cure_paralysis': self._handle_cure_paralysis,
            'cure_sleep': self._handle_cure_sleep,
            'cure_all_status': self._handle_cure_all_status,
            'revive': self._handle_revive,
            'resurrect': self._handle_revive,  # resurrectもreviveと同じ処理
            'teleport': self._handle_teleport,
            'light': self._handle_light,
            'buff_attack': self._handle_buff_attack,
            'buff_defense': self._handle_buff_defense,
            'buff_all_stats': self._handle_buff_all_stats
        }
        
        logger.info("ItemUsageManagerを初期化しました")
    
    def can_use_item(self, item: Item, user: Character, target: Optional[Character] = None) -> Tuple[bool, str]:
        """アイテムが使用可能かチェック"""
        # アイテムが存在するかチェック
        if not item:
            return False, "アイテムが存在しません"
        
        # 消耗品以外は使用不可
        if not item.is_consumable():
            return False, "このアイテムは使用できません"
        
        # 鑑定済みかチェック
        # TODO: ItemInstanceの鑑定状態をチェックする場合は、引数を調整する必要がある
        
        # クラス制限チェック
        if item.usable_classes and user.character_class not in item.usable_classes:
            return False, f"{user.character_class}は{item.get_name()}を使用できません"
        
        # 対象が必要な場合のチェック
        effect_type = item.get_effect_type()
        if effect_type in ['heal_hp', 'heal_mp', 'restore_mp', 'revive', 'resurrect'] and not target:
            return False, "対象を指定してください"
        
        # 蘇生アイテムの場合、対象が死亡しているかチェック
        if effect_type in ['revive', 'resurrect']:
            if target and target.status != CharacterStatus.DEAD:
                return False, "対象は死亡していません"
        
        # 回復アイテムの場合、対象が生存または意識不明状態かチェック
        if effect_type in ['heal_hp', 'heal_mp', 'restore_mp']:
            if target and target.status == CharacterStatus.DEAD:
                return False, "対象は死亡しているため使用できません"
        
        return True, ""
    
    def use_item(self, item_instance: ItemInstance, user: Character, target: Optional[Character] = None, party: Optional[Party] = None) -> Tuple[UsageResult, str, Dict[str, Any]]:
        """アイテムを使用"""
        # アイテム情報を取得
        item = item_manager.get_item(item_instance.item_id)
        if not item:
            return UsageResult.INVALID_ITEM, "アイテムが見つかりません", {}
        
        # 鑑定済みかチェック
        if not item_instance.identified:
            return UsageResult.CANNOT_USE, "未鑑定のアイテムは使用できません", {}
        
        # 数量チェック
        if item_instance.quantity <= ZERO_QUANTITY:
            return UsageResult.INSUFFICIENT_QUANTITY, "アイテムがありません", {}
        
        # 使用可能性チェック
        can_use, reason = self.can_use_item(item, user, target)
        if not can_use:
            return UsageResult.CANNOT_USE, reason, {}
        
        # 効果実行
        effect_type = item.get_effect_type()
        effect_value = item.get_effect_value()
        
        if effect_type not in self.effect_handlers:
            return UsageResult.FAILED, f"未対応の効果: {effect_type}", {}
        
        # 効果ハンドラーを実行
        try:
            success, message, results = self.effect_handlers[effect_type](
                item, item_instance, user, target, party, effect_value
            )
            
            if success:
                # アイテム消費
                item_instance.quantity -= CONSUME_QUANTITY
                logger.info(f"アイテム使用: {user.name} が {item.get_name()} を使用")
                return UsageResult.SUCCESS, message, results
            else:
                return UsageResult.FAILED, message, results
                
        except Exception as e:
            logger.error(f"アイテム使用エラー: {e}")
            return UsageResult.FAILED, f"アイテム使用中にエラーが発生しました: {e}", {}
    
    def _handle_hp_healing(self, item: Item, item_instance: ItemInstance, user: Character, target: Character, party: Optional[Party], effect_value: int) -> Tuple[bool, str, Dict[str, Any]]:
        """HP回復処理"""
        if not target:
            return False, "対象が指定されていません", {}
        
        if target.status == CharacterStatus.DEAD:
            return False, f"{target.name}は死亡しているため使用できません", {}
        
        old_hp = target.derived_stats.current_hp
        target.heal(effect_value)
        healed = target.derived_stats.current_hp - old_hp
        
        # 意識不明状態から回復する可能性をチェック
        if target.status == CharacterStatus.UNCONSCIOUS and target.derived_stats.current_hp > ZERO_QUANTITY:
            target.status = CharacterStatus.GOOD
        
        message = f"{target.name}のHPが{healed}回復しました"
        results = {
            'target': target.name,
            'healed_amount': healed,
            'current_hp': target.derived_stats.current_hp,
            'max_hp': target.derived_stats.max_hp
        }
        
        return True, message, results
    
    def _handle_mp_healing(self, item: Item, item_instance: ItemInstance, user: Character, target: Character, party: Optional[Party], effect_value: int) -> Tuple[bool, str, Dict[str, Any]]:
        """MP回復処理"""
        if not target:
            return False, "対象が指定されていません", {}
        
        if target.status == CharacterStatus.DEAD:
            return False, f"{target.name}は死亡しているため使用できません", {}
        
        old_mp = target.derived_stats.current_mp
        target.restore_mp(effect_value)
        restored = target.derived_stats.current_mp - old_mp
        
        message = f"{target.name}のMPが{restored}回復しました"
        results = {
            'target': target.name,
            'restored_amount': restored,
            'current_mp': target.derived_stats.current_mp,
            'max_mp': target.derived_stats.max_mp
        }
        
        return True, message, results
    
    def _handle_cure_poison(self, item: Item, item_instance: ItemInstance, user: Character, target: Character, party: Optional[Party], effect_value: int) -> Tuple[bool, str, Dict[str, Any]]:
        """毒治療処理"""
        target_char = target if target else user
        status_effects = target_char.get_status_effects()
        
        from src.effects.status_effects import StatusEffectType
        if status_effects.has_effect(StatusEffectType.POISON):
            success, result = status_effects.remove_effect(StatusEffectType.POISON, target_char)
            if success:
                message = result.get('message', f"{target_char.name}の毒が治療されました")
                results = {'target': target_char.name, 'cured': 'poison', 'effective': True}
                return True, message, results
        
        # 毒状態でない場合
        message = f"{target_char.name}は毒状態ではありません"
        results = {'target': target_char.name, 'cured': 'poison', 'effective': False}
        return True, message, results
    
    def _handle_cure_paralysis(self, item: Item, item_instance: ItemInstance, user: Character, target: Character, party: Optional[Party], effect_value: int) -> Tuple[bool, str, Dict[str, Any]]:
        """麻痺治療処理"""
        target_char = target if target else user
        status_effects = target_char.get_status_effects()
        
        from src.effects.status_effects import StatusEffectType
        if status_effects.has_effect(StatusEffectType.PARALYSIS):
            success, result = status_effects.remove_effect(StatusEffectType.PARALYSIS, target_char)
            if success:
                message = result.get('message', f"{target_char.name}の麻痺が治療されました")
                results = {'target': target_char.name, 'cured': 'paralysis', 'effective': True}
                return True, message, results
        
        # 麻痺状態でない場合
        message = f"{target_char.name}は麻痺状態ではありません"
        results = {'target': target_char.name, 'cured': 'paralysis', 'effective': False}
        return True, message, results
    
    def _handle_cure_sleep(self, item: Item, item_instance: ItemInstance, user: Character, target: Character, party: Optional[Party], effect_value: int) -> Tuple[bool, str, Dict[str, Any]]:
        """睡眠治療処理"""
        target_char = target if target else user
        status_effects = target_char.get_status_effects()
        
        from src.effects.status_effects import StatusEffectType
        if status_effects.has_effect(StatusEffectType.SLEEP):
            success, result = status_effects.remove_effect(StatusEffectType.SLEEP, target_char)
            if success:
                message = result.get('message', f"{target_char.name}の睡眠が治療されました")
                results = {'target': target_char.name, 'cured': 'sleep', 'effective': True}
                return True, message, results
        
        # 睡眠状態でない場合
        message = f"{target_char.name}は睡眠状態ではありません"
        results = {'target': target_char.name, 'cured': 'sleep', 'effective': False}
        return True, message, results
    
    def _handle_cure_all_status(self, item: Item, item_instance: ItemInstance, user: Character, target: Character, party: Optional[Party], effect_value: int) -> Tuple[bool, str, Dict[str, Any]]:
        """全状態異常治療処理"""
        target_char = target if target else user
        status_effects = target_char.get_status_effects()
        
        cured_effects = status_effects.cure_negative_effects(target_char)
        
        if cured_effects:
            cured_names = [result.get('message', '') for result in cured_effects]
            message = f"{target_char.name}の全ての状態異常が治療されました"
            results = {'target': target_char.name, 'cured': 'all_status', 'cured_effects': cured_names, 'effective': True}
        else:
            message = f"{target_char.name}には治療すべき状態異常がありません"
            results = {'target': target_char.name, 'cured': 'all_status', 'effective': False}
        
        return True, message, results
    
    def _handle_revive(self, item: Item, item_instance: ItemInstance, user: Character, target: Character, party: Optional[Party], effect_value: int) -> Tuple[bool, str, Dict[str, Any]]:
        """蘇生処理"""
        if not target:
            return False, "蘇生対象が指定されていません", {}
        
        if target.status != CharacterStatus.DEAD:
            return False, f"{target.name}は死亡していません", {}
        
        # 蘇生処理
        target.status = CharacterStatus.GOOD
        revive_hp = max(MINIMUM_REVIVE_HP, target.derived_stats.max_hp * effect_value // PERCENT_DIVISOR)
        target.derived_stats.current_hp = revive_hp
        
        message = f"{target.name}が蘇生しました（HP: {revive_hp}）"
        results = {
            'target': target.name,
            'revived': True,
            'hp_restored': revive_hp
        }
        
        return True, message, results
    
    def _handle_teleport(self, item: Item, item_instance: ItemInstance, user: Character, target: Optional[Character], party: Optional[Party], effect_value: int) -> Tuple[bool, str, Dict[str, Any]]:
        """テレポート処理"""
        # TODO: ダンジョンシステム実装後に本格実装
        message = "パーティが地上に帰還しました"
        results = {'teleported': True, 'destination': 'overworld'}
        return True, message, results
    
    def _handle_light(self, item: Item, item_instance: ItemInstance, user: Character, target: Optional[Character], party: Optional[Party], effect_value: int) -> Tuple[bool, str, Dict[str, Any]]:
        """光源処理"""
        # TODO: ダンジョンシステム実装後に本格実装
        message = f"明るい光が{effect_value}ターンの間、パーティを照らします"
        results = {'light_duration': effect_value}
        return True, message, results
    
    def _handle_buff_attack(self, item: Item, item_instance: ItemInstance, user: Character, target: Character, party: Optional[Party], effect_value: int) -> Tuple[bool, str, Dict[str, Any]]:
        """攻撃力強化処理"""
        # TODO: ステータス効果システム実装後に本格実装
        target_char = target if target else user
        message = f"{target_char.name}の攻撃力が{effect_value}上昇しました"
        results = {'target': target_char.name, 'buff_type': 'attack', 'value': effect_value}
        return True, message, results
    
    def _handle_buff_defense(self, item: Item, item_instance: ItemInstance, user: Character, target: Character, party: Optional[Party], effect_value: int) -> Tuple[bool, str, Dict[str, Any]]:
        """防御力強化処理"""
        # TODO: ステータス効果システム実装後に本格実装
        target_char = target if target else user
        message = f"{target_char.name}の防御力が{effect_value}上昇しました"
        results = {'target': target_char.name, 'buff_type': 'defense', 'value': effect_value}
        return True, message, results
    
    def _handle_buff_all_stats(self, item: Item, item_instance: ItemInstance, user: Character, target: Character, party: Optional[Party], effect_value: int) -> Tuple[bool, str, Dict[str, Any]]:
        """全能力値強化処理"""
        # TODO: ステータス効果システム実装後に本格実装
        target_char = target if target else user
        message = f"{target_char.name}の全能力値が{effect_value}上昇しました"
        results = {'target': target_char.name, 'buff_type': 'all_stats', 'value': effect_value}
        return True, message, results
    
    def get_item_usage_info(self, item: Item) -> Dict[str, Any]:
        """アイテムの使用情報を取得"""
        if not item.is_consumable():
            return {'usable': False, 'reason': '消耗品ではありません'}
        
        effect_type = item.get_effect_type()
        effect_value = item.get_effect_value()
        
        info = {
            'usable': True,
            'effect_type': effect_type,
            'effect_value': effect_value,
            'target_required': effect_type in ['heal_hp', 'heal_mp', 'restore_mp', 'revive', 'resurrect'],
            'description': self._get_effect_description(effect_type, effect_value)
        }
        
        return info
    
    def _get_effect_description(self, effect_type: str, effect_value: int) -> str:
        """効果の説明文を生成"""
        from src.core.config_manager import config_manager
        
        descriptions = {
            'heal_hp': config_manager.get_text('item_effects.hp_recovery_desc').format(value=effect_value),
            'heal_mp': config_manager.get_text('item_effects.mp_recovery_desc').format(value=effect_value),
            'restore_mp': config_manager.get_text('item_effects.mp_recovery_desc').format(value=effect_value),
            'cure_poison': config_manager.get_text('item_effects.poison_cure_desc'),
            'cure_paralysis': config_manager.get_text('item_effects.paralysis_cure_desc'),
            'cure_sleep': config_manager.get_text('item_effects.sleep_cure_desc'),
            'cure_all_status': config_manager.get_text('item_effects.all_status_cure_desc'),
            'revive': config_manager.get_text('item_effects.revive_desc').format(value=effect_value),
            'resurrect': config_manager.get_text('item_effects.revive_desc').format(value=effect_value),
            'teleport': config_manager.get_text('item_effects.teleport_desc'),
            'light': config_manager.get_text('item_effects.light_desc').format(value=effect_value),
            'buff_attack': config_manager.get_text('item_effects.attack_buff_desc').format(value=effect_value),
            'buff_defense': config_manager.get_text('item_effects.defense_buff_desc').format(value=effect_value),
            'buff_all_stats': config_manager.get_text('item_effects.all_stats_buff_desc').format(value=effect_value)
        }
        
        return descriptions.get(effect_type, config_manager.get_text('item_effects.unknown_effect'))
    
    def get_usable_items_for_character(self, character: Character, inventory_items: List[Tuple[Any, ItemInstance]]) -> List[Tuple[Any, ItemInstance, Item]]:
        """キャラクターが使用可能なアイテム一覧を取得"""
        usable_items = []
        
        for slot, item_instance in inventory_items:
            if item_instance.quantity <= ZERO_QUANTITY or not item_instance.identified:
                continue
            
            item = item_manager.get_item(item_instance.item_id)
            if not item or not item.is_consumable():
                continue
            
            # 対象が必要なアイテムの場合は、基本的にcharacter自身を対象として考える
            effect_type = item.get_effect_type()
            target = character if effect_type in ['heal_hp', 'heal_mp', 'restore_mp'] else None
            
            can_use, _ = self.can_use_item(item, character, target)
            if can_use:
                usable_items.append((slot, item_instance, item))
        
        return usable_items


# グローバルインスタンス
item_usage_manager = ItemUsageManager()