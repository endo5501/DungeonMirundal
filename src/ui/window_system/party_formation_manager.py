"""
PartyFormationManager クラス

パーティ編成管理専門クラス
"""

from typing import Dict, Any, Optional, List
from .party_formation_types import (
    PartyPosition, FormationValidationResult, CharacterSlot, FormationChange
)
from src.utils.logger import logger


class PartyFormationManager:
    """
    パーティ編成管理クラス
    
    パーティ編成のロジックを担当
    """
    
    def __init__(self, party: Any, max_party_size: int = 6):
        """
        PartyFormationManagerを初期化
        
        Args:
            party: パーティオブジェクト
            max_party_size: 最大パーティサイズ
        """
        self.party = party
        self.max_party_size = max_party_size
        self.change_history: List[FormationChange] = []
    
    def add_character_to_position(self, character: Any, position: PartyPosition) -> bool:
        """
        キャラクターをポジションに追加
        
        Args:
            character: 追加するキャラクター
            position: 追加先ポジション
            
        Returns:
            bool: 追加成功の場合True
        """
        # パーティサイズチェック
        if self._get_current_member_count() >= self.max_party_size:
            logger.warning(f"パーティが満員です: {self.max_party_size}")
            return False
        
        # ポジションが空きかチェック
        if self._is_position_occupied(position):
            logger.warning(f"ポジションが既に使用されています: {position}")
            return False
        
        # パーティに追加
        if hasattr(self.party, 'add_character_at_position'):
            self.party.add_character_at_position(character, position)
        
        # 変更を記録
        self._record_change('add', character, None, position)
        
        logger.debug(f"キャラクター追加: {character} -> {position}")
        return True
    
    def remove_character_from_position(self, position: PartyPosition) -> bool:
        """
        キャラクターをポジションから削除
        
        Args:
            position: 削除するポジション
            
        Returns:
            bool: 削除成功の場合True
        """
        character = self._get_character_at_position(position)
        if not character:
            logger.warning(f"ポジションが空です: {position}")
            return False
        
        # パーティから削除
        if hasattr(self.party, 'remove_character_from_position'):
            self.party.remove_character_from_position(position)
        
        # 変更を記録
        self._record_change('remove', character, position, None)
        
        logger.debug(f"キャラクター削除: {character} <- {position}")
        return True
    
    def move_character(self, from_position: PartyPosition, to_position: PartyPosition) -> bool:
        """
        キャラクターを移動
        
        Args:
            from_position: 移動元ポジション
            to_position: 移動先ポジション
            
        Returns:
            bool: 移動成功の場合True
        """
        character = self._get_character_at_position(from_position)
        if not character:
            logger.warning(f"移動元にキャラクターがいません: {from_position}")
            return False
        
        # 移動先チェック
        if self._is_position_occupied(to_position):
            logger.warning(f"移動先が既に使用されています: {to_position}")
            return False
        
        # パーティで移動
        if hasattr(self.party, 'move_character'):
            self.party.move_character(from_position, to_position)
        
        # 変更を記録
        self._record_change('move', character, from_position, to_position)
        
        logger.debug(f"キャラクター移動: {character} {from_position} -> {to_position}")
        return True
    
    def swap_characters(self, position1: PartyPosition, position2: PartyPosition) -> bool:
        """
        2つのポジションのキャラクターを入れ替え
        
        Args:
            position1: ポジション1
            position2: ポジション2
            
        Returns:
            bool: 入れ替え成功の場合True
        """
        character1 = self._get_character_at_position(position1)
        character2 = self._get_character_at_position(position2)
        
        if not character1 and not character2:
            logger.warning("両方のポジションが空です")
            return False
        
        # 入れ替え実行
        if hasattr(self.party, 'swap_characters'):
            self.party.swap_characters(position1, position2)
        else:
            # 手動で入れ替え
            if character1:
                self.party.remove_character_from_position(position1)
            if character2:
                self.party.remove_character_from_position(position2)
            
            if character1:
                self.party.add_character_at_position(character1, position2)
            if character2:
                self.party.add_character_at_position(character2, position1)
        
        # 変更を記録
        if character1 and character2:
            self._record_change('swap', character1, position1, position2)
            self._record_change('swap', character2, position2, position1)
        elif character1:
            self._record_change('move', character1, position1, position2)
        elif character2:
            self._record_change('move', character2, position2, position1)
        
        logger.debug(f"キャラクター入れ替え: {position1} <-> {position2}")
        return True
    
    def validate_formation(self) -> FormationValidationResult:
        """
        パーティ編成を検証
        
        Returns:
            FormationValidationResult: 検証結果
        """
        warnings = []
        
        # メンバー数チェック
        member_count = self._get_current_member_count()
        
        if member_count == 0:
            return FormationValidationResult.invalid("パーティにメンバーがいません")
        
        if member_count > self.max_party_size:
            return FormationValidationResult.invalid(f"パーティサイズが上限を超えています: {member_count}/{self.max_party_size}")
        
        # 前衛チェック
        front_count = self._count_front_row_members()
        if front_count == 0 and member_count > 0:
            warnings.append("前衛にメンバーがいません")
        
        # バランスチェック
        if member_count >= 3:
            if front_count == 0:
                warnings.append("前衛が空です")
            elif front_count == member_count:
                warnings.append("後衛が空です")
        
        return FormationValidationResult.valid() if not warnings else FormationValidationResult.invalid("編成に問題があります", warnings)
    
    def get_formation_stats(self) -> Dict[str, Any]:
        """
        編成統計を取得
        
        Returns:
            Dict[str, Any]: 編成統計
        """
        total_members = self._get_current_member_count()
        front_members = self._count_front_row_members()
        back_members = self._count_back_row_members()
        
        return {
            'total_members': total_members,
            'front_members': front_members,
            'back_members': back_members,
            'empty_positions': 6 - total_members,
            'formation_balance': front_members / max(total_members, 1)
        }
    
    def get_recommended_positions(self, character: Any) -> List[PartyPosition]:
        """
        キャラクターの推奨ポジションを取得
        
        Args:
            character: キャラクター
            
        Returns:
            List[PartyPosition]: 推奨ポジションリスト
        """
        recommendations = []
        
        # キャラクタークラスベースの推奨
        if hasattr(character, 'character_class'):
            char_class = character.character_class.lower()
            
            if char_class in ['戦士', 'パラディン', '侍']:
                # 前衛推奨
                recommendations.extend([
                    PartyPosition.FRONT_CENTER,
                    PartyPosition.FRONT_LEFT,
                    PartyPosition.FRONT_RIGHT
                ])
            elif char_class in ['魔法使い', '僧侶']:
                # 後衛推奨
                recommendations.extend([
                    PartyPosition.BACK_CENTER,
                    PartyPosition.BACK_LEFT,
                    PartyPosition.BACK_RIGHT
                ])
            elif char_class in ['盗賊', '忍者']:
                # 前後どちらでも
                recommendations.extend([
                    PartyPosition.FRONT_LEFT,
                    PartyPosition.FRONT_RIGHT,
                    PartyPosition.BACK_LEFT,
                    PartyPosition.BACK_RIGHT
                ])
        
        # 空いているポジションのみ返す
        return [pos for pos in recommendations if not self._is_position_occupied(pos)]
    
    def clear_formation(self) -> bool:
        """
        編成をクリア
        
        Returns:
            bool: クリア成功の場合True
        """
        success = True
        
        for position in PartyPosition:
            if self._is_position_occupied(position):
                if not self.remove_character_from_position(position):
                    success = False
        
        if success:
            logger.debug("パーティ編成をクリアしました")
        
        return success
    
    def _get_current_member_count(self) -> int:
        """現在のメンバー数を取得"""
        if hasattr(self.party, 'get_member_count'):
            return self.party.get_member_count()
        
        # フォールバック: ポジションを数える
        count = 0
        for position in PartyPosition:
            if self._get_character_at_position(position):
                count += 1
        return count
    
    def _count_front_row_members(self) -> int:
        """前衛メンバー数を取得"""
        count = 0
        for position in [PartyPosition.FRONT_LEFT, PartyPosition.FRONT_CENTER, PartyPosition.FRONT_RIGHT]:
            if self._get_character_at_position(position):
                count += 1
        return count
    
    def _count_back_row_members(self) -> int:
        """後衛メンバー数を取得"""
        count = 0
        for position in [PartyPosition.BACK_LEFT, PartyPosition.BACK_CENTER, PartyPosition.BACK_RIGHT]:
            if self._get_character_at_position(position):
                count += 1
        return count
    
    def _is_position_occupied(self, position: PartyPosition) -> bool:
        """ポジションが使用されているかチェック"""
        return self._get_character_at_position(position) is not None
    
    def _get_character_at_position(self, position: PartyPosition) -> Optional[Any]:
        """ポジションのキャラクターを取得"""
        if hasattr(self.party, 'get_character_at_position'):
            return self.party.get_character_at_position(position)
        return None
    
    def _record_change(self, change_type: str, character: Any, 
                      from_position: Optional[PartyPosition], 
                      to_position: Optional[PartyPosition]) -> None:
        """変更を記録"""
        import time
        
        change = FormationChange(
            change_type=change_type,
            character=character,
            from_position=from_position,
            to_position=to_position,
            timestamp=time.time()
        )
        
        self.change_history.append(change)
    
    def get_change_history(self) -> List[FormationChange]:
        """変更履歴を取得"""
        return self.change_history.copy()
    
    def clear_change_history(self) -> None:
        """変更履歴をクリア"""
        self.change_history.clear()