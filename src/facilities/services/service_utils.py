"""施設サービス共通ユーティリティ

各施設サービス間で重複している処理を共通化するためのユーティリティクラス群。
"""

import logging
from typing import List, Dict, Any, Optional, Callable
from ..core.service_result import ServiceResult, ResultType
from src.character.character import Character
from src.character.party import Party

logger = logging.getLogger(__name__)


class ServiceResultFactory:
    """ServiceResult生成の共通ファクトリ"""
    
    @staticmethod
    def success(message: str, data: Optional[Dict[str, Any]] = None, 
               result_type: ResultType = ResultType.SUCCESS) -> ServiceResult:
        """成功結果を生成"""
        return ServiceResult(
            success=True,
            message=message,
            result_type=result_type,
            data=data or {}
        )
    
    @staticmethod
    def error(message: str, result_type: ResultType = ResultType.ERROR) -> ServiceResult:
        """エラー結果を生成"""
        return ServiceResult(
            success=False,
            message=message,
            result_type=result_type
        )
    
    @staticmethod
    def confirm(message: str, data: Optional[Dict[str, Any]] = None) -> ServiceResult:
        """確認結果を生成"""
        return ServiceResult(
            success=True,
            message=message,
            result_type=ResultType.CONFIRM,
            data=data or {}
        )
    
    @staticmethod
    def info(message: str, data: Optional[Dict[str, Any]] = None) -> ServiceResult:
        """情報結果を生成"""
        return ServiceResult(
            success=True,
            message=message,
            result_type=ResultType.INFO,
            data=data or {}
        )


class PartyMemberUtility:
    """パーティメンバー操作の共通ユーティリティ"""
    
    def __init__(self, party: Optional[Party]):
        self.party = party
    
    def has_party(self) -> bool:
        """パーティが存在するかチェック"""
        return self.party is not None
    
    def get_members_by_condition(self, condition_func: Callable[[Character], bool]) -> List[Character]:
        """条件に合うメンバーを取得"""
        if not self.has_party():
            return []
        
        return [member for member in self.party.members if condition_func(member)]
    
    def has_members_with_condition(self, condition_func: Callable[[Character], bool]) -> bool:
        """条件に合うメンバーが存在するかチェック"""
        return len(self.get_members_by_condition(condition_func)) > 0
    
    def get_character_by_id(self, character_id: str) -> Optional[Character]:
        """IDでキャラクターを取得"""
        if not self.has_party():
            return None
        
        for member in self.party.members:
            member_id = getattr(member, 'character_id', getattr(member, 'id', ''))
            if member_id == character_id:
                return member
        return None
    
    def create_member_info_dict(self, member: Character, 
                               additional_fields: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """キャラクター情報辞書を作成"""
        info = {
            "id": getattr(member, 'character_id', getattr(member, 'id', '')),
            "name": member.name,
            "level": getattr(member.experience, 'level', getattr(member, 'level', 1)),
            "race": member.race,
            "class": getattr(member, 'character_class', getattr(member, 'char_class', '')),
            "hp": f"{getattr(member.derived_stats, 'current_hp', getattr(member, 'hp', 0))}/{getattr(member.derived_stats, 'max_hp', getattr(member, 'max_hp', 0))}",
            "mp": f"{getattr(member.derived_stats, 'current_mp', getattr(member, 'mp', 0))}/{getattr(member.derived_stats, 'max_mp', getattr(member, 'max_mp', 0))}",
            "status": getattr(member.status, 'value', str(member.status)) if hasattr(member, 'status') else 'normal'
        }
        
        if additional_fields:
            info.update(additional_fields)
        
        return info
    
    def create_member_selection_result(self, condition_func: Callable[[Character], bool],
                                     message: str, empty_message: str) -> ServiceResult:
        """メンバー選択用結果を生成"""
        if not self.has_party():
            return ServiceResultFactory.error("パーティが存在しません")
        
        members = self.get_members_by_condition(condition_func)
        
        if not members:
            return ServiceResultFactory.info(empty_message)
        
        member_list = [self.create_member_info_dict(member) for member in members]
        
        return ServiceResultFactory.success(
            message,
            data={
                "members": member_list,
                "total": len(member_list)
            }
        )


class ItemOperationUtility:
    """アイテム操作の共通ユーティリティ"""
    
    @staticmethod
    def handle_item_operation(params: Dict[str, Any], operation_name: str,
                            success_verb: str) -> ServiceResult:
        """アイテム操作の共通処理
        
        Args:
            params: 操作パラメータ（item_id, quantityを含む）
            operation_name: 操作名（ログ用）
            success_verb: 成功時の動詞（「預けました」「引き出しました」等）
        """
        item_id = params.get("item_id")
        quantity = params.get("quantity", 1)
        
        logger.info(f"Item {operation_name}: item_id={item_id}, quantity={quantity}")
        
        if not item_id:
            return ServiceResultFactory.error("アイテムが指定されていません")
        
        if quantity <= 0:
            return ServiceResultFactory.error("数量は1以上で指定してください")
        
        # TODO: 実際のアイテム操作実装
        # 現在は仮実装
        
        return ServiceResultFactory.success(
            f"アイテムを {quantity} 個{success_verb}",
            data={"item_id": item_id, "quantity": quantity}
        )


class ConfirmationFlowUtility:
    """確認フロー処理の共通ユーティリティ"""
    
    @staticmethod
    def handle_confirmation_flow(params: Dict[str, Any], 
                               confirm_method: Callable[[Dict[str, Any]], ServiceResult],
                               execute_method: Callable[[Dict[str, Any]], ServiceResult]) -> ServiceResult:
        """確認→実行の共通フロー処理
        
        Args:
            params: パラメータ（confirmedフラグを含む）
            confirm_method: 確認処理を行うメソッド
            execute_method: 実行処理を行うメソッド
        """
        try:
            if not params.get("confirmed", False):
                return confirm_method(params)
            else:
                return execute_method(params)
        except Exception as e:
            logger.error(f"Confirmation flow error: {e}")
            return ServiceResultFactory.error(f"処理中にエラーが発生しました: {str(e)}")
    
    @staticmethod
    def handle_character_action_flow(params: Dict[str, Any],
                                   get_targets_method: Callable[[], ServiceResult],
                                   confirm_method: Callable[[str], ServiceResult],
                                   execute_method: Callable[[str], ServiceResult]) -> ServiceResult:
        """キャラクター対象のアクション共通フロー（選択→確認→実行）
        
        Args:
            params: パラメータ（character_id, confirmedフラグを含む）
            get_targets_method: 対象キャラクター一覧取得メソッド
            confirm_method: 確認処理メソッド
            execute_method: 実行処理メソッド
        """
        character_id = params.get("character_id")
        
        if not character_id:
            # 対象選択画面
            return get_targets_method()
        
        # 確認→実行フロー
        if not params.get("confirmed", False):
            return confirm_method(character_id)
        
        # 実行
        return execute_method(character_id)


class CostCalculationUtility:
    """コスト計算の共通ユーティリティ"""
    
    def __init__(self, party: Optional[Party]):
        self.party = party
    
    def calculate_level_based_cost(self, character: Character, 
                                 base_cost: int, multiplier: float = 1.0) -> int:
        """レベルベースのコスト計算"""
        return int(base_cost * (character.level ** 0.5) * multiplier)
    
    def validate_and_get_cost_info(self, cost: int, action_name: str) -> ServiceResult:
        """コスト検証と情報取得"""
        if not self.party:
            return ServiceResultFactory.error("パーティが存在しません")
        
        if cost <= 0:
            return ServiceResultFactory.info(f"{action_name}は無料です")
        
        if self.party.gold < cost:
            return ServiceResultFactory.error(
                f"ゴールドが不足しています（必要: {cost}G、所持: {self.party.gold}G）",
                result_type=ResultType.WARNING
            )
        
        return ServiceResultFactory.success(
            f"{action_name}の費用は {cost}G です",
            data={"cost": cost, "current_gold": self.party.gold}
        )
    
    def deduct_cost(self, cost: int) -> bool:
        """コストを差し引く"""
        if not self.party or self.party.gold < cost:
            return False
        
        self.party.gold -= cost
        return True


class ActionExecutorMixin:
    """アクション実行の共通Mixin"""
    
    def execute_with_error_handling(self, action_map: Dict[str, Callable], 
                                   action_id: str, params: Dict[str, Any]) -> ServiceResult:
        """エラーハンドリング付きアクション実行"""
        logger.info(f"Executing action: {action_id} with params: {params}")
        
        try:
            if action_id not in action_map:
                logger.error(f"[DEBUG] Action '{action_id}' not found in action_map: {list(action_map.keys())}")
                return ServiceResultFactory.error(f"不明なアクション: {action_id}")
            
            action_method = action_map[action_id]
            logger.debug(f"[DEBUG] Calling action method: {action_method}")
            result = action_method(params)
            logger.debug(f"[DEBUG] Action method returned: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Action execution failed for {action_id}: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return ServiceResultFactory.error(f"エラーが発生しました: {str(e)}")
    
    def validate_action_availability(self, action_id: str, 
                                   availability_map: Dict[str, Callable[[], bool]]) -> bool:
        """アクション実行可能性の検証"""
        if action_id not in availability_map:
            return False
        
        return availability_map[action_id]()