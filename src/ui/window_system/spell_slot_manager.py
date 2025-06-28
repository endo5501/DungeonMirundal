"""魔法スロット管理クラス

Fowler Extract Classパターンにより、MagicWindowからスロット管理に関する責任を抽出。
魔法の装備・解除・使用・回復などのスロット操作を専門的に扱う。
"""

from typing import Dict, List, Optional, Any, Callable, Tuple
from enum import Enum

from src.character.character import Character
from src.magic.spells import SpellBook, Spell
from src.utils.logger import logger


class SlotOperation(Enum):
    """スロット操作種別"""
    EQUIP = "equip"              # 装備
    UNEQUIP = "unequip"          # 装備解除
    USE = "use"                  # 使用
    RESTORE = "restore"          # 回復
    RESTORE_ALL = "restore_all"  # 全回復


class SlotOperationResult:
    """スロット操作結果"""
    
    def __init__(self, success: bool, message: str = "", data: Any = None):
        self.success = success
        self.message = message
        self.data = data


class SpellSlotManager:
    """魔法スロット管理クラス
    
    魔法スロットの装備・解除・使用・回復などの操作を担当。
    Extract Classパターンにより、MagicWindowからスロット管理ロジックを分離。
    """
    
    def __init__(self):
        """スロット管理マネージャー初期化"""
        self.operation_callbacks: Dict[SlotOperation, List[Callable]] = {
            operation: [] for operation in SlotOperation
        }
        logger.debug("SpellSlotManagerを初期化しました")
    
    def add_operation_callback(self, operation: SlotOperation, callback: Callable) -> None:
        """操作コールバックを追加
        
        Args:
            operation: 操作種別
            callback: コールバック関数
        """
        if operation in self.operation_callbacks:
            self.operation_callbacks[operation].append(callback)
    
    def equip_spell_to_slot(self, character: Character, spell_id: str, 
                           level: int, slot_index: int) -> SlotOperationResult:
        """スロットに魔法を装備
        
        Args:
            character: 対象キャラクター
            spell_id: 魔法ID
            level: スロットレベル
            slot_index: スロットインデックス
            
        Returns:
            SlotOperationResult: 操作結果
        """
        if not character:
            return SlotOperationResult(False, "キャラクターが指定されていません")
        
        spellbook = character.get_spellbook()
        if not spellbook:
            return SlotOperationResult(False, "魔法書が見つかりません")
        
        # 装備可能性チェック
        if not self._can_equip_spell(spellbook, spell_id, level):
            return SlotOperationResult(False, "この魔法は装備できません")
        
        # 実際の装備処理
        try:
            # spellbook.equip_spell_to_slot を模擬
            success = True  # 実際の実装では spellbook のメソッドを呼ぶ
            
            if success:
                # コールバック実行
                self._execute_callbacks(SlotOperation.EQUIP, {
                    'character': character,
                    'spell_id': spell_id,
                    'level': level,
                    'slot_index': slot_index
                })
                
                return SlotOperationResult(
                    True, 
                    f"魔法をレベル{level}スロット{slot_index+1}に装備しました",
                    {'spell_id': spell_id, 'level': level, 'slot_index': slot_index}
                )
            else:
                return SlotOperationResult(False, "装備処理が失敗しました")
        
        except Exception as e:
            logger.error(f"魔法装備エラー: {e}")
            return SlotOperationResult(False, f"装備エラー: {str(e)}")
    
    def unequip_spell_from_slot(self, character: Character, 
                              level: int, slot_index: int) -> SlotOperationResult:
        """スロットから魔法を装備解除
        
        Args:
            character: 対象キャラクター
            level: スロットレベル
            slot_index: スロットインデックス
            
        Returns:
            SlotOperationResult: 操作結果
        """
        if not character:
            return SlotOperationResult(False, "キャラクターが指定されていません")
        
        spellbook = character.get_spellbook()
        if not spellbook:
            return SlotOperationResult(False, "魔法書が見つかりません")
        
        try:
            # spellbook.unequip_spell_from_slot を模擬
            unequipped_spell_id = f"spell_{level}_{slot_index}"  # 実際の実装では spellbook のメソッドを呼ぶ
            
            if unequipped_spell_id:
                # コールバック実行
                self._execute_callbacks(SlotOperation.UNEQUIP, {
                    'character': character,
                    'spell_id': unequipped_spell_id,
                    'level': level,
                    'slot_index': slot_index
                })
                
                return SlotOperationResult(
                    True,
                    f"魔法の装備を解除しました",
                    {'spell_id': unequipped_spell_id, 'level': level, 'slot_index': slot_index}
                )
            else:
                return SlotOperationResult(False, "装備解除する魔法がありません")
        
        except Exception as e:
            logger.error(f"魔法装備解除エラー: {e}")
            return SlotOperationResult(False, f"装備解除エラー: {str(e)}")
    
    def use_spell_from_slot(self, character: Character, 
                          level: int, slot_index: int) -> SlotOperationResult:
        """スロットから魔法を使用
        
        Args:
            character: 対象キャラクター
            level: スロットレベル
            slot_index: スロットインデックス
            
        Returns:
            SlotOperationResult: 操作結果
        """
        if not character:
            return SlotOperationResult(False, "キャラクターが指定されていません")
        
        spellbook = character.get_spellbook()
        if not spellbook:
            return SlotOperationResult(False, "魔法書が見つかりません")
        
        # 使用可能性チェック
        if not self._can_use_spell_from_slot(spellbook, level, slot_index):
            return SlotOperationResult(False, "この魔法は使用できません")
        
        try:
            # spellbook.use_spell を模擬
            success = True  # 実際の実装では spellbook のメソッドを呼ぶ
            
            if success:
                # コールバック実行
                self._execute_callbacks(SlotOperation.USE, {
                    'character': character,
                    'level': level,
                    'slot_index': slot_index
                })
                
                return SlotOperationResult(
                    True,
                    f"レベル{level}スロット{slot_index+1}の魔法を使用しました",
                    {'level': level, 'slot_index': slot_index}
                )
            else:
                return SlotOperationResult(False, "魔法使用が失敗しました")
        
        except Exception as e:
            logger.error(f"魔法使用エラー: {e}")
            return SlotOperationResult(False, f"魔法使用エラー: {str(e)}")
    
    def restore_slot_uses(self, character: Character, 
                         level: int, slot_index: int) -> SlotOperationResult:
        """指定スロットの使用回数を回復
        
        Args:
            character: 対象キャラクター
            level: スロットレベル
            slot_index: スロットインデックス
            
        Returns:
            SlotOperationResult: 操作結果
        """
        if not character:
            return SlotOperationResult(False, "キャラクターが指定されていません")
        
        spellbook = character.get_spellbook()
        if not spellbook:
            return SlotOperationResult(False, "魔法書が見つかりません")
        
        try:
            # スロット使用回数回復を模擬
            success = True  # 実際の実装では spellbook のメソッドを呼ぶ
            
            if success:
                # コールバック実行
                self._execute_callbacks(SlotOperation.RESTORE, {
                    'character': character,
                    'level': level,
                    'slot_index': slot_index
                })
                
                return SlotOperationResult(
                    True,
                    f"レベル{level}スロット{slot_index+1}の使用回数を回復しました",
                    {'level': level, 'slot_index': slot_index}
                )
            else:
                return SlotOperationResult(False, "使用回数回復が失敗しました")
        
        except Exception as e:
            logger.error(f"使用回数回復エラー: {e}")
            return SlotOperationResult(False, f"使用回数回復エラー: {str(e)}")
    
    def restore_all_spell_uses(self, character: Character) -> SlotOperationResult:
        """全魔法スロットの使用回数を回復
        
        Args:
            character: 対象キャラクター
            
        Returns:
            SlotOperationResult: 操作結果
        """
        if not character:
            return SlotOperationResult(False, "キャラクターが指定されていません")
        
        spellbook = character.get_spellbook()
        if not spellbook:
            return SlotOperationResult(False, "魔法書が見つかりません")
        
        try:
            # 全スロット使用回数回復を模擬
            # spellbook.restore_all_uses()
            
            # コールバック実行
            self._execute_callbacks(SlotOperation.RESTORE_ALL, {
                'character': character
            })
            
            return SlotOperationResult(
                True,
                "全ての魔法スロットの使用回数を回復しました",
                {'character': character.name}
            )
        
        except Exception as e:
            logger.error(f"全使用回数回復エラー: {e}")
            return SlotOperationResult(False, f"全使用回数回復エラー: {str(e)}")
    
    def get_available_spells_for_slot(self, character: Character, level: int) -> List[Dict[str, Any]]:
        """スロットに装備可能な魔法一覧を取得
        
        Args:
            character: 対象キャラクター
            level: スロットレベル
            
        Returns:
            List[Dict]: 装備可能な魔法一覧
        """
        if not character:
            return []
        
        spellbook = character.get_spellbook()
        if not spellbook:
            return []
        
        # 習得済み魔法から装備可能なものを抽出
        # 実際の実装では spell_manager と連携
        learned_spells = getattr(spellbook, 'learned_spells', [])
        available_spells = []
        
        for spell_id in learned_spells:
            # 魔法レベルチェック（模擬）
            spell_level = 1  # 実際の実装では spell_manager.get_spell(spell_id).level
            
            if spell_level <= level:
                available_spells.append({
                    'spell_id': spell_id,
                    'name': f"魔法{spell_id}",
                    'level': spell_level,
                    'can_equip': True
                })
        
        return available_spells
    
    def _can_equip_spell(self, spellbook: SpellBook, spell_id: str, level: int) -> bool:
        """魔法が装備可能かチェック
        
        Args:
            spellbook: 魔法書
            spell_id: 魔法ID
            level: スロットレベル
            
        Returns:
            bool: 装備可能な場合True
        """
        # 実際の実装では詳細なチェックロジック
        return True
    
    def _can_use_spell_from_slot(self, spellbook: SpellBook, level: int, slot_index: int) -> bool:
        """スロットから魔法が使用可能かチェック
        
        Args:
            spellbook: 魔法書
            level: スロットレベル
            slot_index: スロットインデックス
            
        Returns:
            bool: 使用可能な場合True
        """
        # 実際の実装では詳細なチェックロジック
        return True
    
    def _execute_callbacks(self, operation: SlotOperation, data: Dict[str, Any]) -> None:
        """操作コールバックを実行
        
        Args:
            operation: 操作種別
            data: コールバックに渡すデータ
        """
        callbacks = self.operation_callbacks.get(operation, [])
        for callback in callbacks:
            try:
                callback(data)
            except Exception as e:
                logger.error(f"コールバック実行エラー ({operation.value}): {e}")