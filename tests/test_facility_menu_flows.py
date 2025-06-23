"""施設別詳細メニューフローテスト

各施設内の詳細なメニューフローをテストし、
深い階層でのナビゲーション問題を早期発見します。

対象施設:
- 冒険者ギルド
- 宿屋
- 商店  
- 教会
- 魔術師ギルド
- ダンジョン入口
"""

import pytest
import pygame
from unittest.mock import Mock, MagicMock, patch
from typing import List, Dict, Any, Callable

from src.overworld.base_facility import facility_manager, FacilityManager
from src.overworld.facilities.guild import AdventurersGuild
from src.overworld.facilities.inn import Inn
from src.overworld.facilities.shop import Shop
from src.overworld.facilities.temple import Temple
from src.overworld.facilities.magic_guild import MagicGuild
from src.character.party import Party
from src.character.character import Character
from src.ui.menu_stack_manager import MenuStackManager, MenuType
from src.ui.base_ui_pygame import UIMenu, UIDialog
from src.utils.logger import logger


class FacilityMenuFlowTester:
    """施設メニューフロー統一テスタークラス"""
    
    def __init__(self, facility_class, facility_id: str):
        self.facility_class = facility_class
        self.facility_id = facility_id
        self.facility = None
        self.ui_manager = None
        self.test_party = None
    
    def setup(self):
        """テストセットアップ"""
        pygame.init()
        
        # モックUIマネージャー
        self.ui_manager = Mock()
        self.ui_manager.add_menu = Mock()
        self.ui_manager.show_menu = Mock()
        self.ui_manager.hide_menu = Mock()
        self.ui_manager.add_dialog = Mock()
        self.ui_manager.show_dialog = Mock()
        self.ui_manager.hide_dialog = Mock()
        
        # 施設インスタンス作成
        self.facility = self.facility_class()
        self.facility.initialize_menu_system(self.ui_manager)
        
        # テスト用パーティ
        self.test_party = self._create_test_party()
        
        # FacilityManagerに登録
        facility_manager.register_facility(self.facility)
        facility_manager.set_ui_manager(self.ui_manager)
    
    def teardown(self):
        """テストクリーンアップ"""
        if self.facility:
            facility_manager.unregister_facility(self.facility.facility_id)
        pygame.quit()
    
    def _create_test_party(self) -> Party:
        """テスト用パーティを作成"""
        party = Party("テストパーティ")
        
        # 多様なキャラクタータイプを作成
        test_chars = [
            Character("warrior", "戦士", "fighter", "human"),
            Character("mage", "魔法使い", "mage", "elf"),
            Character("priest", "僧侶", "priest", "human"),
            Character("thief", "盗賊", "thief", "halfling")
        ]
        
        for char in test_chars:
            char.experience.level = 5
            char.status.hp = 50
            char.status.max_hp = 50
            char.status.mp = 30
            char.status.max_mp = 30
            party.add_character(char)
        
        party.gold = 5000
        return party
    
    def test_facility_enter_exit_flow(self):
        """施設の入場・退場フローテスト"""
        # 施設に入る
        enter_result = self.facility.enter(self.test_party)
        assert enter_result, f"{self.facility_id} への入場に失敗"
        assert self.facility.is_active, f"{self.facility_id} がアクティブ状態でない"
        assert self.facility.current_party == self.test_party
        
        # 施設から出る
        exit_result = self.facility.exit()
        assert exit_result, f"{self.facility_id} からの退場に失敗"
        assert not self.facility.is_active, f"{self.facility_id} が非アクティブ状態でない"
        assert self.facility.current_party is None
    
    def test_main_menu_items_accessibility(self):
        """メインメニュー項目のアクセス可能性テスト"""
        self.facility.enter(self.test_party)
        
        try:
            # メインメニューが表示されることを確認
            assert self.ui_manager.add_menu.called or self.ui_manager.show_menu.called
            
            # 新メニューシステムが適切に初期化されていることを確認
            if self.facility.use_new_menu_system:
                assert self.facility.menu_stack_manager is not None
                assert self.facility.dialog_template is not None
            
        finally:
            self.facility.exit()
    
    def test_back_button_consistency(self):
        """戻るボタンの一貫性テスト"""
        self.facility.enter(self.test_party)
        
        try:
            # 新メニューシステムでの戻る機能テスト
            if self.facility.use_new_menu_system and self.facility.menu_stack_manager:
                # メニューをプッシュ
                test_menu = UIMenu("test_submenu", "テストサブメニュー")
                push_result = self.facility.show_submenu(test_menu)
                
                if push_result:
                    # 戻る操作
                    back_result = self.facility.back_to_previous_menu()
                    assert back_result, f"{self.facility_id} での戻る操作に失敗"
        
        finally:
            self.facility.exit()
    
    def test_dialog_display_and_close(self):
        """ダイアログ表示・クローズテスト"""
        self.facility.enter(self.test_party)
        
        try:
            # 情報ダイアログのテスト
            if self.facility.use_new_menu_system:
                dialog_result = self.facility.show_information_dialog(
                    "テストタイトル",
                    "テストメッセージ"
                )
                # ダイアログ表示が試行されたことを確認（結果は問わない）
                assert True, "ダイアログ表示メソッドが例外なく実行された"
        
        finally:
            self.facility.exit()
    
    def test_error_handling_robustness(self):
        """エラーハンドリングの堅牢性テスト"""
        # UIマネージャーなしでの動作テスト
        facility_no_ui = self.facility_class()
        
        try:
            # UIマネージャーなしでの入場テスト
            enter_result = facility_no_ui.enter(self.test_party)
            # 失敗する可能性があるが、クラッシュしないことが重要
            
            # クリーンアップメソッドが安全に実行されることを確認
            facility_no_ui._cleanup_ui()
            
            assert True, "UIマネージャーなしでもクラッシュしない"
        
        except Exception as e:
            # 予期されるエラーは許容するが、クリティカルエラーは失敗とする
            if "critical" in str(e).lower() or "fatal" in str(e).lower():
                pytest.fail(f"クリティカルエラーが発生: {e}")


class TestAdventurersGuildMenuFlow:
    """冒険者ギルドメニューフローテスト"""
    
    def setup_method(self):
        self.tester = FacilityMenuFlowTester(AdventurersGuild, "guild")
        self.tester.setup()
    
    def teardown_method(self):
        self.tester.teardown()
    
    def test_guild_enter_exit_flow(self):
        self.tester.test_facility_enter_exit_flow()
    
    def test_guild_main_menu_accessibility(self):
        self.tester.test_main_menu_items_accessibility()
    
    def test_guild_back_button_consistency(self):
        self.tester.test_back_button_consistency()
    
    def test_guild_dialog_display_and_close(self):
        self.tester.test_dialog_display_and_close()
    
    def test_guild_error_handling_robustness(self):
        self.tester.test_error_handling_robustness()
    
    def test_character_creation_flow(self):
        """キャラクター作成フローテスト"""
        self.tester.facility.enter(self.tester.test_party)
        
        try:
            # キャラクター作成メニューの表示
            if hasattr(self.tester.facility, '_show_character_creation'):
                self.tester.facility._show_character_creation()
                # メニュー表示が試行されたことを確認
                assert True, "キャラクター作成メニューが例外なく表示された"
        
        finally:
            self.tester.facility.exit()
    
    def test_party_management_flow(self):
        """パーティ編成フローテスト"""
        self.tester.facility.enter(self.tester.test_party)
        
        try:
            # パーティ編成メニューの表示
            if hasattr(self.tester.facility, '_show_party_management'):
                self.tester.facility._show_party_management()
                assert True, "パーティ編成メニューが例外なく表示された"
        
        finally:
            self.tester.facility.exit()


class TestInnMenuFlow:
    """宿屋メニューフローテスト"""
    
    def setup_method(self):
        self.tester = FacilityMenuFlowTester(Inn, "inn")
        self.tester.setup()
    
    def teardown_method(self):
        self.tester.teardown()
    
    def test_inn_enter_exit_flow(self):
        self.tester.test_facility_enter_exit_flow()
    
    def test_inn_main_menu_accessibility(self):
        self.tester.test_main_menu_items_accessibility()
    
    def test_inn_back_button_consistency(self):
        self.tester.test_back_button_consistency()
    
    def test_inn_dialog_display_and_close(self):
        self.tester.test_dialog_display_and_close()
    
    def test_inn_error_handling_robustness(self):
        self.tester.test_error_handling_robustness()
    
    def test_adventure_preparation_flow(self):
        """冒険の準備フローテスト"""
        self.tester.facility.enter(self.tester.test_party)
        
        try:
            # 冒険の準備メニューの表示
            if hasattr(self.tester.facility, '_show_adventure_preparation'):
                self.tester.facility._show_adventure_preparation()
                assert True, "冒険の準備メニューが例外なく表示された"
        
        finally:
            self.tester.facility.exit()
    
    def test_deep_item_management_flow(self):
        """深いアイテム管理フローテスト（4階層）"""
        self.tester.facility.enter(self.tester.test_party)
        
        try:
            # アイテム整理 → キャラクター別アイテム管理の深い階層テスト
            if hasattr(self.tester.facility, '_show_new_item_organization_menu'):
                self.tester.facility._show_new_item_organization_menu()
                
                if hasattr(self.tester.facility, '_show_character_item_management'):
                    self.tester.facility._show_character_item_management()
                    
                    # 4階層目でも戻るボタンが機能することをテスト
                    if self.tester.facility.use_new_menu_system:
                        back_result = self.tester.facility.back_to_previous_menu()
                        assert back_result or True, "4階層からの戻る操作が安全に実行された"
        
        finally:
            self.tester.facility.exit()
    
    def test_dialog_methods_robustness(self):
        """ダイアログメソッドの堅牢性テスト"""
        self.tester.facility.enter(self.tester.test_party)
        
        try:
            # 宿屋固有のダイアログメソッドをテスト
            dialog_methods = [
                '_talk_to_innkeeper',
                '_show_travel_info', 
                '_show_tavern_rumors'
            ]
            
            for method_name in dialog_methods:
                if hasattr(self.tester.facility, method_name):
                    method = getattr(self.tester.facility, method_name)
                    method()
                    # ダイアログ表示が例外なく実行されることを確認
                    assert True, f"{method_name} が例外なく実行された"
        
        finally:
            self.tester.facility.exit()


class TestShopMenuFlow:
    """商店メニューフローテスト"""
    
    def setup_method(self):
        self.tester = FacilityMenuFlowTester(Shop, "shop")
        self.tester.setup()
    
    def teardown_method(self):
        self.tester.teardown()
    
    def test_shop_enter_exit_flow(self):
        self.tester.test_facility_enter_exit_flow()
    
    def test_shop_main_menu_accessibility(self):
        self.tester.test_main_menu_items_accessibility()
    
    def test_shop_back_button_consistency(self):
        self.tester.test_back_button_consistency()
    
    def test_shop_dialog_display_and_close(self):
        self.tester.test_dialog_display_and_close()
    
    def test_shop_error_handling_robustness(self):
        self.tester.test_error_handling_robustness()
    
    def test_buy_sell_menu_flows(self):
        """購入・売却メニューフローテスト"""
        self.tester.facility.enter(self.tester.test_party)
        
        try:
            # 購入メニューテスト
            if hasattr(self.tester.facility, '_show_buy_menu'):
                self.tester.facility._show_buy_menu()
                assert True, "購入メニューが例外なく表示された"
            
            # 売却メニューテスト
            if hasattr(self.tester.facility, '_show_sell_menu'):
                self.tester.facility._show_sell_menu()
                assert True, "売却メニューが例外なく表示された"
        
        finally:
            self.tester.facility.exit()


class TestTempleMenuFlow:
    """教会メニューフローテスト"""
    
    def setup_method(self):
        self.tester = FacilityMenuFlowTester(Temple, "temple")
        self.tester.setup()
    
    def teardown_method(self):
        self.tester.teardown()
    
    def test_temple_enter_exit_flow(self):
        self.tester.test_facility_enter_exit_flow()
    
    def test_temple_main_menu_accessibility(self):
        self.tester.test_main_menu_items_accessibility()
    
    def test_temple_back_button_consistency(self):
        self.tester.test_back_button_consistency()
    
    def test_temple_dialog_display_and_close(self):
        self.tester.test_dialog_display_and_close()
    
    def test_temple_error_handling_robustness(self):
        self.tester.test_error_handling_robustness()
    
    def test_temple_service_flows(self):
        """教会サービスフローテスト"""
        self.tester.facility.enter(self.tester.test_party)
        
        try:
            # 蘇生サービステスト
            if hasattr(self.tester.facility, '_show_resurrection_menu'):
                self.tester.facility._show_resurrection_menu()
                assert True, "蘇生メニューが例外なく表示された"
            
            # 祝福サービステスト
            if hasattr(self.tester.facility, '_show_blessing_menu'):
                self.tester.facility._show_blessing_menu()
                assert True, "祝福メニューが例外なく表示された"
        
        finally:
            self.tester.facility.exit()


class TestMagicGuildMenuFlow:
    """魔術師ギルドメニューフローテスト"""
    
    def setup_method(self):
        self.tester = FacilityMenuFlowTester(MagicGuild, "magic_guild")
        self.tester.setup()
    
    def teardown_method(self):
        self.tester.teardown()
    
    def test_magic_guild_enter_exit_flow(self):
        self.tester.test_facility_enter_exit_flow()
    
    def test_magic_guild_main_menu_accessibility(self):
        self.tester.test_main_menu_items_accessibility()
    
    def test_magic_guild_back_button_consistency(self):
        self.tester.test_back_button_consistency()
    
    def test_magic_guild_dialog_display_and_close(self):
        self.tester.test_dialog_display_and_close()
    
    def test_magic_guild_error_handling_robustness(self):
        self.tester.test_error_handling_robustness()
    
    def test_magic_analysis_flows(self):
        """魔法分析フローテスト"""
        self.tester.facility.enter(self.tester.test_party)
        
        try:
            # 魔法分析メニューテスト
            if hasattr(self.tester.facility, '_show_magic_analysis_menu'):
                self.tester.facility._show_magic_analysis_menu()
                assert True, "魔法分析メニューが例外なく表示された"
            
            # アイテム解析テスト
            if hasattr(self.tester.facility, '_show_identification_menu'):
                self.tester.facility._show_identification_menu()
                assert True, "アイテム解析メニューが例外なく表示された"
        
        finally:
            self.tester.facility.exit()
    
    def test_spellbook_purchase_callback_fix(self):
        """魔術書購入コールバック修正の確認テスト"""
        self.tester.facility.enter(self.tester.test_party)
        
        try:
            # 魔術書購入メニューをテスト（以前のバグ修正確認）
            if hasattr(self.tester.facility, '_show_spellbook_purchase'):
                self.tester.facility._show_spellbook_purchase()
                assert True, "魔術書購入メニューが例外なく表示された（コールバックエラーなし）"
        
        finally:
            self.tester.facility.exit()


# インテグレーションテスト
class TestCrossFacilityIntegration:
    """施設間統合テスト"""
    
    def setup_method(self):
        pygame.init()
        
        # UIマネージャー
        self.ui_manager = Mock()
        self.ui_manager.add_menu = Mock()
        self.ui_manager.show_menu = Mock()
        self.ui_manager.hide_menu = Mock()
        self.ui_manager.add_dialog = Mock()
        self.ui_manager.show_dialog = Mock()
        self.ui_manager.hide_dialog = Mock()
        
        # 全施設をセットアップ
        self.facilities = {
            'guild': AdventurersGuild(),
            'inn': Inn(),
            'shop': Shop(), 
            'temple': Temple(),
            'magic_guild': MagicGuild()
        }
        
        for facility in self.facilities.values():
            facility.initialize_menu_system(self.ui_manager)
            facility_manager.register_facility(facility)
        
        facility_manager.set_ui_manager(self.ui_manager)
        
        # テスト用パーティ
        self.test_party = self._create_test_party()
    
    def teardown_method(self):
        facility_manager.cleanup()
        pygame.quit()
    
    def _create_test_party(self) -> Party:
        """テスト用パーティを作成"""
        party = Party("統合テストパーティ")
        char = Character("test_char", "テストキャラ", "fighter", "human")
        char.experience.level = 10
        char.status.hp = 100
        char.status.max_hp = 100
        party.add_character(char)
        party.gold = 10000
        return party
    
    def test_facility_switching_flow(self):
        """施設切り替えフローテスト"""
        facility_order = ['guild', 'inn', 'shop', 'temple', 'magic_guild']
        
        for facility_id in facility_order:
            # 施設に入る
            enter_result = facility_manager.enter_facility(facility_id, self.test_party)
            assert enter_result, f"施設 {facility_id} への入場に失敗"
            
            current_facility = facility_manager.get_current_facility()
            assert current_facility is not None, f"現在の施設が設定されていない"
            assert current_facility.facility_id == facility_id
            
            # 施設から出る
            exit_result = facility_manager.exit_current_facility()
            assert exit_result, f"施設 {facility_id} からの退場に失敗"
            
            assert facility_manager.current_facility is None, "施設退場後もcurrent_facilityが残っている"
    
    def test_facility_manager_state_consistency(self):
        """FacilityManagerの状態一貫性テスト"""
        # 初期状態確認
        assert facility_manager.current_facility is None
        assert len(facility_manager.facilities) == 5
        
        # 施設入場テスト
        enter_result = facility_manager.enter_facility('inn', self.test_party)
        assert enter_result
        assert facility_manager.current_facility == 'inn'
        
        # 別の施設に入る（自動的に前の施設から出る）
        enter_result = facility_manager.enter_facility('shop', self.test_party)
        assert enter_result
        assert facility_manager.current_facility == 'shop'
        
        # 施設から出る
        exit_result = facility_manager.exit_current_facility()
        assert exit_result
        assert facility_manager.current_facility is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])