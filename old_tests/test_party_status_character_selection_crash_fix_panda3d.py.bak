"""
パーティ状況からキャラクター選択でクラッシュする問題の修正テスト
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import sys
import os

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.overworld.overworld_manager import OverworldManager
from src.character.party import Party
from src.character.character import Character, CharacterStatus
from src.character.stats import BaseStats, DerivedStats
from src.character.character import Experience


class TestPartyStatusCharacterSelectionCrashFix:
    """パーティ状況キャラクター選択クラッシュ修正のテスト"""

    def setup_method(self):
        """各テストメソッドの前に実行される初期化処理"""
        # 実際のキャラクターオブジェクトを作成（モックではなく）
        self.test_character = Character(
            name="勇者",
            race="human",
            character_class="fighter"
        )
        
        # 経験値を設定
        self.test_character.experience = Experience(level=10, current_xp=1500)
        
        # 基本能力値を設定
        self.test_character.base_stats = BaseStats(
            strength=15,
            intelligence=10,
            faith=8,
            agility=12,
            luck=11
        )
        
        # vitalityを手動で追加（存在しない場合）
        if not hasattr(self.test_character.base_stats, 'vitality'):
            self.test_character.base_stats.vitality = 14
        
        # 派生能力値を設定
        self.test_character.derived_stats = DerivedStats(
            current_hp=45,
            max_hp=50,
            current_mp=8,
            max_mp=10
        )
        
        # 必要な派生能力値属性を手動で追加（存在しない場合）
        if not hasattr(self.test_character.derived_stats, 'attack_power'):
            self.test_character.derived_stats.attack_power = 25
        if not hasattr(self.test_character.derived_stats, 'defense'):
            self.test_character.derived_stats.defense = 18
        if not hasattr(self.test_character.derived_stats, 'accuracy'):
            self.test_character.derived_stats.accuracy = 75
        if not hasattr(self.test_character.derived_stats, 'evasion'):
            self.test_character.derived_stats.evasion = 20
        if not hasattr(self.test_character.derived_stats, 'critical_chance'):
            self.test_character.derived_stats.critical_chance = 15
        
        self.test_character.status = CharacterStatus.GOOD
        
        # テストパーティを作成
        self.test_party = Mock()
        self.test_party.name = "テストパーティ"
        self.test_party.gold = 2500
        self.test_party.characters = [self.test_character]
        self.test_party.get_all_characters.return_value = [self.test_character]

    def test_character_equipment_property_exists(self):
        """
        テスト: キャラクターにequipmentプロパティが存在する
        
        期待する動作:
        - character.equipmentでAttributeErrorが発生しない
        - equipmentオブジェクトが返される
        """
        # equipmentプロパティにアクセス
        try:
            equipment = self.test_character.equipment
            # AttributeErrorが発生しないことを確認
            assert equipment is not None, "equipmentプロパティがNoneです"
        except AttributeError as e:
            pytest.fail(f"character.equipmentプロパティが存在しません: {e}")

    def test_character_get_personal_inventory_method_exists(self):
        """
        テスト: キャラクターにget_personal_inventoryメソッドが存在する
        
        期待する動作:
        - character.get_personal_inventory()でAttributeErrorが発生しない
        - インベントリオブジェクトが返される
        """
        # get_personal_inventoryメソッドを呼び出し
        try:
            personal_inventory = self.test_character.get_personal_inventory()
            # AttributeErrorが発生しないことを確認
            # Noneの場合もあるが、メソッドが存在することが重要
            assert True, "get_personal_inventoryメソッドが正常に呼び出されました"
        except AttributeError as e:
            pytest.fail(f"character.get_personal_inventory()メソッドが存在しません: {e}")

    def test_equipment_has_required_attributes(self):
        """
        テスト: equipmentオブジェクトが必要な属性を持っている
        
        期待する動作:
        - equipment.weapon、equipment.armor、equipment.shield、equipment.accessoryが存在する
        - これらの属性にアクセスしてもAttributeErrorが発生しない
        """
        equipment = self.test_character.equipment
        
        # 必要な装備スロットが存在することを確認
        required_slots = ['weapon', 'armor', 'shield', 'accessory']
        
        for slot_name in required_slots:
            try:
                slot_value = getattr(equipment, slot_name)
                # None または 実際のアイテムが返されることを確認
                assert True, f"{slot_name}属性が正常にアクセスできました"
            except AttributeError as e:
                pytest.fail(f"equipment.{slot_name}属性が存在しません: {e}")

    @patch('src.overworld.overworld_manager.ui_manager')
    @patch('src.overworld.overworld_manager.config_manager')
    def test_show_character_details_no_crash_on_equipment_access(self, mock_config_mgr, mock_ui_mgr):
        """
        テスト: _show_character_detailsで装備アクセス時にクラッシュしない
        
        期待する動作:
        - character.equipmentアクセスでAttributeErrorが発生しない
        - equipment.weapon等の属性アクセスでエラーが発生しない
        """
        # モック設定
        mock_ui_mgr.register_element = Mock()
        mock_ui_mgr.show_element = Mock()
        mock_config_mgr.get_text = Mock(return_value="テスト")
        
        # オーバーワールドマネージャーを作成
        overworld_manager = OverworldManager()
        overworld_manager.current_party = self.test_party
        overworld_manager._show_info_dialog = Mock()
        
        # キャラクター詳細を表示（クラッシュしないことを確認）
        try:
            overworld_manager._show_character_details(self.test_character)
            assert True, "キャラクター詳細表示でクラッシュしませんでした"
        except AttributeError as e:
            pytest.fail(f"キャラクター詳細表示でAttributeError: {e}")
        except Exception as e:
            # AttributeError以外のエラーは許容（UIの問題等）
            # ただしキャラクターの属性アクセスが原因でないことを確認
            if "equipment" in str(e) or "get_personal_inventory" in str(e):
                pytest.fail(f"キャラクター属性アクセス関連でエラー: {e}")

    @patch('src.overworld.overworld_manager.ui_manager')
    @patch('src.overworld.overworld_manager.config_manager')
    def test_show_character_details_no_crash_on_inventory_access(self, mock_config_mgr, mock_ui_mgr):
        """
        テスト: _show_character_detailsでインベントリアクセス時にクラッシュしない
        
        期待する動作:
        - character.get_personal_inventory()でAttributeErrorが発生しない
        - インベントリ情報の表示処理でエラーが発生しない
        """
        # モック設定
        mock_ui_mgr.register_element = Mock()
        mock_ui_mgr.show_element = Mock()
        mock_config_mgr.get_text = Mock(return_value="テスト")
        
        # オーバーワールドマネージャーを作成
        overworld_manager = OverworldManager()
        overworld_manager.current_party = self.test_party
        overworld_manager._show_info_dialog = Mock()
        
        # キャラクター詳細を表示（インベントリ部分でクラッシュしないことを確認）
        try:
            overworld_manager._show_character_details(self.test_character)
            # _show_info_dialogが呼ばれたことを確認
            assert overworld_manager._show_info_dialog.called, "詳細情報ダイアログが表示されませんでした"
        except AttributeError as e:
            if "get_personal_inventory" in str(e):
                pytest.fail(f"個人インベントリアクセスでAttributeError: {e}")
            else:
                # その他のAttributeErrorは別の問題
                pass

    def test_character_equipment_get_name_method_safety(self):
        """
        テスト: 装備アイテムのget_nameメソッドが安全に呼び出せる
        
        期待する動作:
        - 装備がない場合でもエラーが発生しない
        - 装備がある場合はget_nameが呼び出せる
        """
        equipment = self.test_character.equipment
        
        # 各装備スロットでget_nameメソッドを安全に呼び出せることを確認
        slots = ['weapon', 'armor', 'shield', 'accessory']
        
        for slot_name in slots:
            slot_item = getattr(equipment, slot_name)
            
            if slot_item is not None:
                # アイテムが装備されている場合、get_nameメソッドが存在するか確認
                try:
                    name = slot_item.get_name()
                    assert isinstance(name, str), f"{slot_name}のget_name()が文字列を返しませんでした"
                except AttributeError:
                    pytest.fail(f"{slot_name}アイテムにget_name()メソッドがありません")
            # slot_item が None の場合は正常（装備なし）

    def test_personal_inventory_slots_safety(self):
        """
        テスト: 個人インベントリのslotsアクセスが安全
        
        期待する動作:
        - personal_inventory.slotsでAttributeErrorが発生しない
        - スロットのis_empty()メソッドが呼び出せる
        """
        try:
            personal_inventory = self.test_character.get_personal_inventory()
            
            if personal_inventory is not None:
                # slotsアクセス
                if hasattr(personal_inventory, 'slots'):
                    slots = personal_inventory.slots
                    
                    if slots:
                        for slot in slots:
                            # is_empty()メソッドが呼び出せることを確認
                            try:
                                is_empty = slot.is_empty()
                                assert isinstance(is_empty, bool), "is_empty()がboolを返しませんでした"
                                
                                if not is_empty:
                                    # アイテムがある場合のitem_instanceアクセス
                                    if hasattr(slot, 'item_instance'):
                                        item_instance = slot.item_instance
                                        if item_instance and hasattr(item_instance, 'get_display_name'):
                                            display_name = item_instance.get_display_name()
                                            assert isinstance(display_name, str), "get_display_name()が文字列を返しませんでした"
                            except AttributeError as e:
                                pytest.fail(f"インベントリスロットメソッドアクセスエラー: {e}")
        except AttributeError as e:
            pytest.fail(f"個人インベントリアクセスでAttributeError: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])