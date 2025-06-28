"""魔法表示管理クラス

Fowler Extract Classパターンにより、MagicWindowから魔法表示に関する責任を抽出。
単一責任の原則に従い、魔法情報の表示・整理・フォーマット機能を専門的に扱う。
"""

from typing import Dict, List, Optional, Any
from enum import Enum

from src.character.party import Party
from src.character.character import Character
from src.magic.spells import SpellBook, Spell, SpellSchool, SpellType
from src.utils.logger import logger


class SpellDisplayFormat(Enum):
    """魔法表示フォーマット"""
    SIMPLE = "simple"          # 簡単表示
    DETAILED = "detailed"      # 詳細表示
    STATISTICS = "statistics"  # 統計表示


class MagicDisplayManager:
    """魔法表示管理クラス
    
    魔法に関する表示情報の生成・整理・フォーマットを担当。
    Extract Classパターンにより、MagicWindowから表示ロジックを分離。
    """
    
    def __init__(self):
        """魔法表示マネージャー初期化"""
        logger.debug("MagicDisplayManagerを初期化しました")
    
    def format_party_magic_summary(self, party: Party) -> List[Dict[str, Any]]:
        """パーティ魔法サマリーをフォーマット
        
        Args:
            party: 対象パーティ
            
        Returns:
            List[Dict]: フォーマットされた魔法サマリー
        """
        if not party:
            return []
        
        summaries = []
        for character in party.get_all_characters():
            spellbook = character.get_spellbook()
            summary = spellbook.get_spell_summary() if spellbook else {}
            
            learned_count = summary.get('learned_count', 0)
            equipped_slots = summary.get('equipped_slots', 0)
            
            summaries.append({
                'character': character,
                'name': character.name,
                'learned_count': learned_count,
                'equipped_slots': equipped_slots,
                'display_text': f"{character.name} (習得:{learned_count} 装備:{equipped_slots})"
            })
        
        return summaries
    
    def format_character_spell_slots(self, character: Character) -> Dict[int, List[Dict[str, Any]]]:
        """キャラクターの魔法スロットをフォーマット
        
        Args:
            character: 対象キャラクター
            
        Returns:
            Dict[int, List]: レベル別スロット情報
        """
        if not character:
            return {}
        
        spellbook = character.get_spellbook()
        if not spellbook:
            return {}
        
        formatted_slots = {}
        summary = spellbook.get_spell_summary()
        slots_by_level = summary.get('slots_by_level', {})
        
        for level, level_info in slots_by_level.items():
            formatted_slots[level] = {
                'level': level,
                'equipped': level_info.get('equipped', 0),
                'total': level_info.get('total', 0),
                'available': level_info.get('available', 0),
                'display_text': f"レベル{level} スロット ({level_info.get('equipped', 0)}/{level_info.get('total', 0)})"
            }
        
        return formatted_slots
    
    def format_learned_spells(self, character: Character) -> List[Dict[str, Any]]:
        """習得済み魔法一覧をフォーマット
        
        Args:
            character: 対象キャラクター
            
        Returns:
            List[Dict]: フォーマットされた魔法一覧
        """
        if not character:
            return []
        
        spellbook = character.get_spellbook()
        if not spellbook:
            return []
        
        # 魔法管理システムから習得済み魔法を取得
        # 実際の実装では spell_manager を使用
        learned_spells = getattr(spellbook, 'learned_spells', [])
        formatted_spells = []
        
        # モック用の簡易実装
        for spell_id in learned_spells:
            # 実際の実装では spell_manager.get_spell(spell_id) を使用
            formatted_spells.append({
                'spell_id': spell_id,
                'name': f"魔法{spell_id}",
                'level': 1,
                'school': 'mage',
                'display_text': f"魔法{spell_id} (Lv.1 魔術)"
            })
        
        return formatted_spells
    
    def format_spell_details(self, spell: Any) -> Dict[str, Any]:
        """魔法詳細情報をフォーマット
        
        Args:
            spell: 魔法オブジェクト
            
        Returns:
            Dict: フォーマットされた魔法詳細
        """
        if not spell:
            return {}
        
        # 魔法オブジェクトから情報を抽出してフォーマット
        return {
            'name': getattr(spell, 'name', '不明な魔法'),
            'description': getattr(spell, 'description', ''),
            'level': getattr(spell, 'level', 1),
            'mp_cost': getattr(spell, 'mp_cost', 0),
            'school': getattr(spell, 'school', 'unknown'),
            'type': getattr(spell, 'spell_type', 'unknown'),
            'target': getattr(spell, 'target', 'unknown')
        }
    
    def format_party_magic_statistics(self, party: Party) -> Dict[str, Any]:
        """パーティ魔法統計をフォーマット
        
        Args:
            party: 対象パーティ
            
        Returns:
            Dict: フォーマットされた統計情報
        """
        if not party:
            return {}
        
        total_learned = 0
        total_equipped = 0
        total_available = 0
        character_stats = []
        
        for character in party.get_all_characters():
            spellbook = character.get_spellbook()
            if spellbook:
                summary = spellbook.get_spell_summary()
                learned = summary.get('learned_count', 0)
                equipped = summary.get('equipped_slots', 0)
                available = summary.get('available_uses', 0)
                
                total_learned += learned
                total_equipped += equipped
                total_available += available
                
                character_stats.append({
                    'name': character.name,
                    'learned': learned,
                    'equipped': equipped,
                    'available': available
                })
        
        return {
            'total_learned': total_learned,
            'total_equipped': total_equipped,
            'total_available': total_available,
            'character_stats': character_stats
        }
    
    def get_school_name(self, school) -> str:
        """学派名を取得
        
        Args:
            school: 魔法学派
            
        Returns:
            str: 学派名
        """
        school_names = {
            'mage': "魔術",
            'priest': "神聖",
            'both': "汎用"
        }
        
        if hasattr(school, 'value'):
            return school_names.get(school.value, str(school))
        else:
            return school_names.get(str(school), str(school))
    
    def get_type_name(self, spell_type) -> str:
        """魔法種別名を取得
        
        Args:
            spell_type: 魔法種別
            
        Returns:
            str: 種別名
        """
        type_names = {
            'offensive': "攻撃",
            'healing': "回復",
            'buff': "強化",
            'debuff': "弱体化",
            'utility': "汎用",
            'revival': "蘇生",
            'ultimate': "究極"
        }
        
        if hasattr(spell_type, 'value'):
            return type_names.get(spell_type.value, str(spell_type))
        else:
            return type_names.get(str(spell_type), str(spell_type))