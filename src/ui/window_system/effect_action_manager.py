"""ステータス効果アクション管理クラス

Fowler Extract Classパターンにより、StatusEffectsWindowから効果アクションに関する責任を抽出。
単一責任の原則に従い、効果の除去・操作・バリデーション機能を専門的に扱う。
"""

from typing import Dict, List, Optional, Any, Callable, Tuple
from enum import Enum
import time

from src.utils.logger import logger


class ActionResult(Enum):
    """アクション結果"""
    SUCCESS = "success"
    FAILED = "failed"
    NOT_ALLOWED = "not_allowed"
    INVALID_TARGET = "invalid_target"
    ALREADY_PROCESSED = "already_processed"


class ActionType(Enum):
    """アクションタイプ"""
    REMOVE_EFFECT = "remove_effect"
    DISPEL_ALL = "dispel_all"
    CLEANSE_DEBUFFS = "cleanse_debuffs"
    PURGE_BUFFS = "purge_buffs"
    TRANSFER_EFFECT = "transfer_effect"


class EffectActionResult:
    """効果アクション結果クラス"""
    
    def __init__(self, result: ActionResult, message: str = "", 
                 affected_effects: List[Dict[str, Any]] = None,
                 error_details: Optional[str] = None):
        self.result = result
        self.message = message
        self.affected_effects = affected_effects or []
        self.error_details = error_details
        self.timestamp = time.time()
        
        # 成功判定
        self.success = result == ActionResult.SUCCESS
        self.failed = result != ActionResult.SUCCESS


class EffectActionManager:
    """ステータス効果アクション管理クラス
    
    ステータス効果の除去・操作・バリデーション機能を担当。
    Extract Classパターンにより、StatusEffectsWindowからアクション管理ロジックを分離。
    """
    
    def __init__(self):
        """効果アクションマネージャー初期化"""
        # 除去可能効果の定義
        self.removable_effects = {
            'poison', 'paralysis', 'sleep', 'confusion', 
            'fear', 'blindness', 'silence', 'slow', 'weakness', 'curse'
        }
        
        # 除去不可効果の定義
        self.permanent_effects = {
            'regeneration', 'blessing', 'protection'
        }
        
        # アクション履歴
        self.action_history: List[Dict[str, Any]] = []
        self.max_history_size = 50
        
        # アクションコールバック
        self.action_callbacks: Dict[ActionType, List[Callable]] = {
            action_type: [] for action_type in ActionType
        }
        
        logger.debug("EffectActionManagerを初期化しました")
    
    def remove_effect(self, character, effect: Dict[str, Any]) -> EffectActionResult:
        """効果を除去
        
        Args:
            character: キャラクターオブジェクト
            effect: 除去する効果
            
        Returns:
            EffectActionResult: アクション結果
        """
        # 入力バリデーション
        if not character:
            return EffectActionResult(
                ActionResult.INVALID_TARGET,
                "無効なキャラクターです",
                error_details="character is None"
            )
        
        if not isinstance(effect, dict):
            return EffectActionResult(
                ActionResult.INVALID_TARGET,
                "無効な効果データです",
                error_details="effect is not a dictionary"
            )
        
        effect_name = effect.get('name', '')
        if not effect_name:
            return EffectActionResult(
                ActionResult.INVALID_TARGET,
                "効果名が指定されていません",
                error_details="effect name is empty"
            )
        
        # 除去可能性チェック
        if not self._is_removable(effect):
            return EffectActionResult(
                ActionResult.NOT_ALLOWED,
                f"【{effect_name}】は除去できません",
                error_details="effect is not removable"
            )
        
        # キャラクターから効果を除去
        char_effects = getattr(character, 'status_effects', [])
        
        # 効果を検索して除去
        for i, char_effect in enumerate(char_effects):
            if self._effects_match(char_effect, effect):
                removed_effect = char_effects.pop(i)
                
                # アクション履歴に記録
                self._record_action(ActionType.REMOVE_EFFECT, {
                    'character': getattr(character, 'name', 'Unknown'),
                    'effect': removed_effect,
                    'success': True
                })
                
                # コールバック実行
                self._execute_callbacks(ActionType.REMOVE_EFFECT, {
                    'character': character,
                    'effect': removed_effect
                })
                
                logger.info(f"効果を除去しました: {effect_name} from {getattr(character, 'name', 'Unknown')}")
                
                return EffectActionResult(
                    ActionResult.SUCCESS,
                    f"【{effect_name}】を除去しました",
                    affected_effects=[removed_effect]
                )
        
        # 効果が見つからない場合
        return EffectActionResult(
            ActionResult.FAILED,
            f"【{effect_name}】が見つかりません",
            error_details="effect not found in character's status_effects"
        )
    
    def cleanse_all_debuffs(self, character) -> EffectActionResult:
        """全てのデバフを除去
        
        Args:
            character: キャラクターオブジェクト
            
        Returns:
            EffectActionResult: アクション結果
        """
        if not character:
            return EffectActionResult(
                ActionResult.INVALID_TARGET,
                "無効なキャラクターです"
            )
        
        char_effects = getattr(character, 'status_effects', [])
        removed_effects = []
        
        # デバフを特定して除去
        i = 0
        while i < len(char_effects):
            effect = char_effects[i]
            if self._is_debuff(effect) and self._is_removable(effect):
                removed_effect = char_effects.pop(i)
                removed_effects.append(removed_effect)
            else:
                i += 1
        
        if removed_effects:
            # アクション履歴に記録
            self._record_action(ActionType.CLEANSE_DEBUFFS, {
                'character': getattr(character, 'name', 'Unknown'),
                'removed_count': len(removed_effects),
                'effects': removed_effects
            })
            
            # コールバック実行
            self._execute_callbacks(ActionType.CLEANSE_DEBUFFS, {
                'character': character,
                'removed_effects': removed_effects
            })
            
            logger.info(f"デバフを一括除去: {len(removed_effects)}個 from {getattr(character, 'name', 'Unknown')}")
            
            return EffectActionResult(
                ActionResult.SUCCESS,
                f"{len(removed_effects)}個のデバフを除去しました",
                affected_effects=removed_effects
            )
        else:
            return EffectActionResult(
                ActionResult.FAILED,
                "除去可能なデバフがありません"
            )
    
    def dispel_all_effects(self, character) -> EffectActionResult:
        """全ての効果を除去（強制）
        
        Args:
            character: キャラクターオブジェクト
            
        Returns:
            EffectActionResult: アクション結果
        """
        if not character:
            return EffectActionResult(
                ActionResult.INVALID_TARGET,
                "無効なキャラクターです"
            )
        
        char_effects = getattr(character, 'status_effects', [])
        removed_effects = list(char_effects)  # コピーを作成
        
        # 全効果を除去
        char_effects.clear()
        
        if removed_effects:
            # アクション履歴に記録
            self._record_action(ActionType.DISPEL_ALL, {
                'character': getattr(character, 'name', 'Unknown'),
                'removed_count': len(removed_effects),
                'effects': removed_effects
            })
            
            # コールバック実行
            self._execute_callbacks(ActionType.DISPEL_ALL, {
                'character': character,
                'removed_effects': removed_effects
            })
            
            logger.info(f"全効果を除去: {len(removed_effects)}個 from {getattr(character, 'name', 'Unknown')}")
            
            return EffectActionResult(
                ActionResult.SUCCESS,
                f"全ての効果（{len(removed_effects)}個）を除去しました",
                affected_effects=removed_effects
            )
        else:
            return EffectActionResult(
                ActionResult.FAILED,
                "除去する効果がありません"
            )
    
    def filter_removable_effects(self, effects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """除去可能な効果をフィルタリング
        
        Args:
            effects: 効果リスト
            
        Returns:
            List: 除去可能な効果リスト
        """
        removable = []
        for effect in effects:
            if self._is_removable(effect):
                removable.append(effect)
        
        return removable
    
    def can_remove_effect(self, character, effect: Dict[str, Any]) -> bool:
        """効果が除去可能かチェック
        
        Args:
            character: キャラクターオブジェクト
            effect: 効果データ
            
        Returns:
            bool: 除去可能な場合True
        """
        if not character or not isinstance(effect, dict):
            return False
        
        # 除去可能性チェック
        if not self._is_removable(effect):
            return False
        
        # キャラクターが該当効果を持っているかチェック
        char_effects = getattr(character, 'status_effects', [])
        for char_effect in char_effects:
            if self._effects_match(char_effect, effect):
                return True
        
        return False
    
    def get_removable_effects_for_character(self, character) -> List[Dict[str, Any]]:
        """キャラクターの除去可能効果を取得
        
        Args:
            character: キャラクターオブジェクト
            
        Returns:
            List: 除去可能効果リスト
        """
        if not character:
            return []
        
        char_effects = getattr(character, 'status_effects', [])
        return self.filter_removable_effects(char_effects)
    
    def validate_action_target(self, character, effect: Optional[Dict[str, Any]] = None) -> Tuple[bool, str]:
        """アクション対象の妥当性を検証
        
        Args:
            character: キャラクターオブジェクト
            effect: 効果データ（オプション）
            
        Returns:
            Tuple[bool, str]: (妥当性, エラーメッセージ)
        """
        # キャラクターチェック
        if not character:
            return False, "キャラクターが指定されていません"
        
        if not hasattr(character, 'status_effects'):
            return False, "キャラクターにステータス効果情報がありません"
        
        # 効果チェック（指定されている場合）
        if effect is not None:
            if not isinstance(effect, dict):
                return False, "効果データが無効です"
            
            if not effect.get('name'):
                return False, "効果名が指定されていません"
        
        return True, ""
    
    def get_action_history(self, character_name: Optional[str] = None, 
                          action_type: Optional[ActionType] = None,
                          limit: int = 10) -> List[Dict[str, Any]]:
        """アクション履歴を取得
        
        Args:
            character_name: キャラクター名でフィルタ
            action_type: アクションタイプでフィルタ
            limit: 最大件数
            
        Returns:
            List: アクション履歴
        """
        history = self.action_history
        
        # フィルタリング
        if character_name:
            history = [h for h in history if h.get('character') == character_name]
        
        if action_type:
            history = [h for h in history if h.get('action_type') == action_type]
        
        # 新しい順にソートして制限
        history = sorted(history, key=lambda x: x.get('timestamp', 0), reverse=True)
        return history[:limit]
    
    def add_action_callback(self, action_type: ActionType, callback: Callable) -> None:
        """アクションコールバックを追加
        
        Args:
            action_type: アクションタイプ
            callback: コールバック関数
        """
        if action_type in self.action_callbacks:
            self.action_callbacks[action_type].append(callback)
            logger.debug(f"アクションコールバックを追加: {action_type.value}")
    
    def remove_action_callback(self, action_type: ActionType, callback: Callable) -> None:
        """アクションコールバックを削除
        
        Args:
            action_type: アクションタイプ
            callback: コールバック関数
        """
        if action_type in self.action_callbacks:
            try:
                self.action_callbacks[action_type].remove(callback)
                logger.debug(f"アクションコールバックを削除: {action_type.value}")
            except ValueError:
                logger.warning(f"コールバックが見つかりません: {action_type.value}")
    
    def _is_removable(self, effect: Dict[str, Any]) -> bool:
        """効果が除去可能かチェック"""
        if not isinstance(effect, dict):
            return False
        
        # 明示的にremovableが設定されている場合はそれを優先
        if 'removable' in effect:
            return bool(effect['removable'])
        
        # 効果名による判定
        effect_name = effect.get('name', '')
        if effect_name in self.permanent_effects:
            return False
        
        if effect_name in self.removable_effects:
            return True
        
        # デフォルトはデバフのみ除去可能
        return self._is_debuff(effect)
    
    def _is_debuff(self, effect: Dict[str, Any]) -> bool:
        """デバフかどうか判定"""
        if not isinstance(effect, dict):
            return False
        
        effect_type = effect.get('type', 'neutral')
        if effect_type == 'debuff':
            return True
        
        # 効果名による判定
        effect_name = effect.get('name', '')
        debuff_effects = {
            'poison', 'paralysis', 'sleep', 'confusion', 
            'fear', 'blindness', 'silence', 'slow', 'weakness', 'curse'
        }
        return effect_name in debuff_effects
    
    def _effects_match(self, effect1, effect2) -> bool:
        """二つの効果が同じかチェック"""
        if not isinstance(effect1, dict) or not isinstance(effect2, dict):
            return False
        
        # 名前で比較（基本）
        name1 = effect1.get('name', '')
        name2 = effect2.get('name', '')
        
        if name1 != name2:
            return False
        
        # より詳細な比較（必要に応じて）
        # source, intensity等での比較も可能
        
        return True
    
    def _record_action(self, action_type: ActionType, action_data: Dict[str, Any]) -> None:
        """アクションを履歴に記録"""
        record = {
            'action_type': action_type,
            'timestamp': time.time(),
            'character': action_data.get('character', 'Unknown'),
            'details': action_data
        }
        
        self.action_history.append(record)
        
        # 履歴サイズを制限
        if len(self.action_history) > self.max_history_size:
            self.action_history.pop(0)
    
    def _execute_callbacks(self, action_type: ActionType, callback_data: Dict[str, Any]) -> None:
        """コールバックを実行"""
        callbacks = self.action_callbacks.get(action_type, [])
        for callback in callbacks:
            try:
                callback(callback_data)
            except Exception as e:
                logger.error(f"アクションコールバック実行エラー ({action_type.value}): {e}")