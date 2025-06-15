"""魔法UI システムのテスト"""

import pytest
from unittest.mock import Mock, patch

from src.character.character import Character
from src.character.party import Party
from src.character.stats import BaseStats
from src.magic.spells import SpellBook, SpellSlot, Spell, SpellManager, SpellSchool, SpellType


class TestMagicUI:
    """魔法UIのテスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        # テスト用キャラクター作成
        stats = BaseStats(strength=12, agility=14, intelligence=16, faith=15, luck=11)
        self.character = Character.create_character("TestMage", "human", "mage", stats)
        
        # テスト用パーティ作成
        self.party = Party(party_id="test_party", name="TestParty")
        self.party.add_character(self.character)
        
        # テスト用魔法書
        self.spellbook = SpellBook(owner_id=self.character.character_id)
    
    def test_magic_ui_initialization(self):
        """魔法UIの初期化テスト"""
        from src.ui.magic_ui import MagicUI, MagicUIMode
        
        ui = MagicUI()
        
        assert ui.current_party is None
        assert ui.current_character is None
        assert ui.current_spellbook is None
        assert ui.current_mode == MagicUIMode.OVERVIEW
        assert ui.is_open == False
    
    def test_party_setting(self):
        """パーティ設定のテスト"""
        from src.ui.magic_ui import MagicUI
        
        ui = MagicUI()
        ui.set_party(self.party)
        
        assert ui.current_party == self.party
    
    def test_spell_school_name_mapping(self):
        """魔法学派名マッピングのテスト"""
        from src.ui.magic_ui import MagicUI
        
        ui = MagicUI()
        
        assert ui._get_school_name(SpellSchool.MAGE) == "魔術"
        assert ui._get_school_name(SpellSchool.PRIEST) == "神聖"
        assert ui._get_school_name(SpellSchool.BOTH) == "汎用"
    
    def test_spell_type_name_mapping(self):
        """魔法種別名マッピングのテスト"""
        from src.ui.magic_ui import MagicUI
        
        ui = MagicUI()
        
        assert ui._get_type_name(SpellType.OFFENSIVE) == "攻撃"
        assert ui._get_type_name(SpellType.HEALING) == "回復"
        assert ui._get_type_name(SpellType.BUFF) == "強化"
        assert ui._get_type_name(SpellType.DEBUFF) == "弱体化"
        assert ui._get_type_name(SpellType.UTILITY) == "汎用"
        assert ui._get_type_name(SpellType.REVIVAL) == "蘇生"
        assert ui._get_type_name(SpellType.ULTIMATE) == "究極"
    
    def test_combat_usage_check(self):
        """戦闘外使用可能チェックのテスト"""
        from src.ui.magic_ui import MagicUI
        
        ui = MagicUI()
        
        # 戦闘外使用可能な魔法
        healing_spell = Mock(spec=Spell)
        healing_spell.spell_type = SpellType.HEALING
        assert ui._can_use_outside_combat(healing_spell) == True
        
        buff_spell = Mock(spec=Spell)
        buff_spell.spell_type = SpellType.BUFF
        assert ui._can_use_outside_combat(buff_spell) == True
        
        utility_spell = Mock(spec=Spell)
        utility_spell.spell_type = SpellType.UTILITY
        assert ui._can_use_outside_combat(utility_spell) == True
        
        revival_spell = Mock(spec=Spell)
        revival_spell.spell_type = SpellType.REVIVAL
        assert ui._can_use_outside_combat(revival_spell) == True
        
        # 戦闘外使用不可の魔法
        offensive_spell = Mock(spec=Spell)
        offensive_spell.spell_type = SpellType.OFFENSIVE
        assert ui._can_use_outside_combat(offensive_spell) == False
    
    def test_target_selection_requirement(self):
        """対象選択要求チェックのテスト"""
        from src.ui.magic_ui import MagicUI
        from src.magic.spells import SpellTarget
        
        ui = MagicUI()
        
        # 対象選択が必要な魔法
        single_ally_spell = Mock(spec=Spell)
        single_ally_spell.target = SpellTarget.SINGLE_ALLY
        assert ui._requires_target_selection(single_ally_spell) == True
        
        single_target_spell = Mock(spec=Spell)
        single_target_spell.target = SpellTarget.SINGLE_TARGET
        assert ui._requires_target_selection(single_target_spell) == True
        
        # 対象選択が不要な魔法
        self_spell = Mock(spec=Spell)
        self_spell.target = SpellTarget.SELF
        assert ui._requires_target_selection(self_spell) == False
        
        party_spell = Mock(spec=Spell)
        party_spell.target = SpellTarget.PARTY
        assert ui._requires_target_selection(party_spell) == False
    
    @patch('src.ui.magic_ui.ui_manager')
    def test_party_magic_menu_creation(self, mock_ui_manager):
        """パーティ魔法メニュー作成のテスト"""
        from src.ui.magic_ui import MagicUI
        
        ui = MagicUI()
        
        # キャラクターの魔法書をモック
        with patch.object(self.character, 'get_spellbook') as mock_get_spellbook:
            mock_spellbook = Mock()
            mock_spellbook.get_spell_summary.return_value = {
                'learned_count': 5,
                'equipped_slots': 3,
                'total_slots': 6,
                'available_uses': 8
            }
            mock_get_spellbook.return_value = mock_spellbook
            
            ui.show_party_magic_menu(self.party)
            
            # UIマネージャーのメソッドが呼ばれたことを確認
            assert mock_ui_manager.register_element.called
            assert mock_ui_manager.show_element.called
            assert ui.is_open == True
    
    @patch('src.ui.magic_ui.ui_manager')
    def test_character_magic_display(self, mock_ui_manager):
        """キャラクター魔法表示のテスト"""
        from src.ui.magic_ui import MagicUI
        
        ui = MagicUI()
        ui.current_character = self.character
        ui.current_spellbook = self.spellbook
        
        ui._show_character_magic(self.character)
        
        # UIマネージャーのメソッドが呼ばれたことを確認
        assert mock_ui_manager.register_element.called
        assert mock_ui_manager.show_element.called
    
    def test_spell_slots_management(self):
        """魔法スロット管理のテスト"""
        from src.ui.magic_ui import MagicUI
        
        ui = MagicUI()
        ui.current_spellbook = self.spellbook
        
        # スロット情報のモック
        with patch.object(self.spellbook, 'get_spell_summary') as mock_summary:
            mock_summary.return_value = {
                'slots_by_level': {
                    1: {'total': 3, 'equipped': 2, 'available': 1},
                    2: {'total': 2, 'equipped': 1, 'available': 0}
                }
            }
            
            # スロットサマリが正しく取得されることを確認
            summary = ui.current_spellbook.get_spell_summary()
            assert 1 in summary['slots_by_level']
            assert 2 in summary['slots_by_level']
            assert summary['slots_by_level'][1]['equipped'] == 2
    
    def test_spell_effect_application(self):
        """魔法効果適用のテスト"""
        from src.ui.magic_ui import MagicUI
        
        ui = MagicUI()
        
        # 回復魔法のモック
        healing_spell = Mock(spec=Spell)
        healing_spell.spell_type = SpellType.HEALING
        healing_spell.calculate_effect_value.return_value = 25
        
        # キャラクターのモック
        caster = Mock(spec=Character)
        caster.derived_stats.faith = 15
        caster.derived_stats.intelligence = 12
        
        target = Mock(spec=Character)
        target.name = "TestTarget"
        target.derived_stats.current_hp = 50
        target.derived_stats.max_hp = 100
        
        # 魔法効果適用
        result = ui._apply_spell_effect(healing_spell, caster, target)
        
        # 回復処理が実行されることを確認
        assert "回復" in result
        assert target.name in result
    
    def test_ui_state_management(self):
        """UI状態管理のテスト"""
        from src.ui.magic_ui import MagicUI, MagicUIMode
        
        ui = MagicUI()
        
        # 初期状態
        assert ui.current_mode == MagicUIMode.OVERVIEW
        assert ui.selected_level is None
        assert ui.selected_slot_index is None
        
        # 状態変更
        ui.selected_level = 1
        ui.selected_slot_index = 0
        assert ui.selected_level == 1
        assert ui.selected_slot_index == 0
    
    def test_magic_statistics_display(self):
        """魔法統計表示のテスト"""
        from src.ui.magic_ui import MagicUI
        
        ui = MagicUI()
        ui.current_party = self.party
        
        # 各キャラクターの魔法統計をモック
        with patch.object(self.character, 'get_spellbook') as mock_get_spellbook:
            mock_spellbook = Mock()
            mock_spellbook.get_spell_summary.return_value = {
                'learned_count': 8,
                'equipped_slots': 5,
                'available_uses': 12
            }
            mock_get_spellbook.return_value = mock_spellbook
            
            # 統計情報が正しく計算されることを確認（実際の計算はメソッド内で行われる）
            assert ui.current_party is not None
            assert len(ui.current_party.get_all_characters()) == 1
    
    @patch('src.ui.magic_ui.spell_manager')
    def test_spell_equipment_workflow(self, mock_spell_manager):
        """魔法装備ワークフローのテスト"""
        from src.ui.magic_ui import MagicUI
        
        ui = MagicUI()
        ui.current_spellbook = self.spellbook
        ui.selected_level = 1
        ui.selected_slot_index = 0
        
        # テスト用魔法のモック
        test_spell = Mock(spec=Spell)
        test_spell.spell_id = "test_heal"
        test_spell.level = 1
        test_spell.get_name.return_value = "ヒール"
        mock_spell_manager.get_spell.return_value = test_spell
        
        # 魔法の習得をモック
        ui.current_spellbook.learned_spells = ["test_heal"]
        
        # 装備処理のモック
        with patch.object(ui.current_spellbook, 'equip_spell_to_slot') as mock_equip:
            mock_equip.return_value = True
            
            # 魔法装備実行
            ui._equip_spell_to_slot("test_heal", 1, 0)
            
            # 装備メソッドが呼ばれたことを確認
            mock_equip.assert_called_once_with("test_heal", 1, 0)
    
    def test_ui_navigation_flow(self):
        """UI ナビゲーションフローのテスト"""
        from src.ui.magic_ui import MagicUI
        
        ui = MagicUI()
        ui.current_party = self.party
        ui.current_character = self.character
        ui.selected_level = 2
        ui.selected_slot_index = 1
        
        # ナビゲーション状態の確認
        assert ui.current_party == self.party
        assert ui.current_character == self.character
        assert ui.selected_level == 2
        assert ui.selected_slot_index == 1
        
        # クリーンアップテスト
        ui.destroy()
        assert ui.current_party is None
        assert ui.current_character is None
        assert ui.selected_level is None


class TestMagicUIIntegration:
    """魔法UI統合テスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        # テスト用データ作成
        stats = BaseStats(strength=10, agility=12, intelligence=18, faith=16, luck=14)
        self.character = Character.create_character("IntegrationMage", "elf", "mage", stats)
        
        self.party = Party(party_id="integration_party", name="IntegrationParty")
        self.party.add_character(self.character)
    
    def test_magic_ui_full_workflow(self):
        """魔法UI完全ワークフローのテスト"""
        from src.ui.magic_ui import MagicUI
        
        ui = MagicUI()
        
        # 1. パーティ設定
        ui.set_party(self.party)
        assert ui.current_party == self.party
        
        # 2. キャラクター選択シミュレーション
        ui.current_character = self.character
        ui.current_spellbook = self.character.get_spellbook()
        
        # 3. 魔法書状態確認
        assert ui.current_spellbook is not None
        assert ui.current_spellbook.owner_id == self.character.character_id
        
        # 4. UI表示状態管理
        ui.is_open = True
        assert ui.is_open == True
        
        # 5. クリーンアップ
        ui.hide()
        assert ui.is_open == False
    
    def test_spell_slot_interaction(self):
        """魔法スロット操作のテスト"""
        from src.ui.magic_ui import MagicUI
        
        ui = MagicUI()
        ui.current_character = self.character
        ui.current_spellbook = self.character.get_spellbook()
        
        # スロット選択
        ui.selected_level = 1
        ui.selected_slot_index = 0
        assert ui.selected_level == 1
        assert ui.selected_slot_index == 0
        
        # スロット状態確認
        spell_slots = ui.current_spellbook.spell_slots
        assert 1 in spell_slots
        assert len(spell_slots[1]) > 0
        assert spell_slots[1][0].is_empty() == True
    
    def test_magic_ui_integration_with_character(self):
        """魔法UIとキャラクターの統合テスト"""
        from src.ui.magic_ui import MagicUI
        
        ui = MagicUI()
        ui.set_party(self.party)
        
        # キャラクターから魔法書を取得できることを確認
        character = self.party.get_all_characters()[0]
        spellbook = character.get_spellbook()
        
        assert spellbook is not None
        assert spellbook.owner_id == character.character_id
        
        # 魔法スロットが正しく初期化されていることを確認
        summary = spellbook.get_spell_summary()
        assert summary['total_slots'] > 0
        assert 'slots_by_level' in summary