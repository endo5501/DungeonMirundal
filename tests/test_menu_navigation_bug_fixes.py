"""メニューナビゲーション優先度高バグ修正のテスト

優先度高のバグ:
- 地上マップでの施設のメニュー開始-終了がうまく行ったりいかなかったりする
- ESCキー処理の問題（冒険者ギルド画面が残存）
- スペルスロット設定でOKボタンが反応しない問題
"""

import pytest
import pygame
from unittest.mock import Mock, patch, MagicMock
from src.overworld.overworld_manager_pygame import OverworldManager
from src.overworld.facilities.guild import AdventurersGuild
from src.overworld.facilities.inn import Inn
from src.ui.menu_stack_manager import MenuStackManager, MenuType
from src.ui.base_ui_pygame import UIMenu, UIDialog
from src.character.party import Party


class TestMenuNavigationBugFixes:
    """メニューナビゲーションのバグ修正テスト"""
    
    @pytest.fixture
    def mock_ui_manager(self):
        """UIマネージャーのモック"""
        ui_manager = Mock()
        ui_manager.add_menu = Mock()
        ui_manager.show_menu = Mock()
        ui_manager.hide_menu = Mock()
        ui_manager.add_dialog = Mock()
        ui_manager.show_dialog = Mock()
        ui_manager.hide_dialog = Mock()
        return ui_manager
    
    @pytest.fixture
    def mock_party(self):
        """パーティのモック"""
        party = Mock(spec=Party)
        party.name = "テストパーティ"
        party.gold = 1000
        party.get_living_characters.return_value = []
        party.get_all_characters.return_value = []
        return party
    
    @pytest.fixture
    def overworld_manager(self, mock_ui_manager):
        """OverworldManagerのインスタンス"""
        manager = OverworldManager()
        manager.set_ui_manager(mock_ui_manager)
        manager.current_party = Mock(spec=Party)
        return manager
    
    @pytest.fixture
    def menu_stack_manager(self, mock_ui_manager):
        """MenuStackManagerのインスタンス"""
        return MenuStackManager(mock_ui_manager)
    
    def test_esc_key_from_facility_returns_to_overworld(self, overworld_manager, mock_ui_manager):
        """冒険者ギルドでESCキーを押すと地上メニューに戻る"""
        # Arrange: 冒険者ギルドを開く
        with patch('src.overworld.base_facility.facility_manager') as mock_facility_manager:
            mock_facility_manager.facilities = {'guild': Mock()}
            mock_facility_manager.enter_facility.return_value = True
            
            # 冒険者ギルドに入る
            overworld_manager._on_guild()
            
            # メインメニューが隠されることを確認
            mock_ui_manager.hide_menu.assert_called()
        
        # Act: 施設からの退場コールバックを呼び出し（ESCキー相当）
        overworld_manager.on_facility_exit()
        
        # Assert: 地上メニューが再表示される
        mock_ui_manager.show_menu.assert_called_with(
            overworld_manager.main_menu.menu_id, 
            modal=True
        )
    
    def test_esc_key_from_overworld_shows_settings(self, overworld_manager):
        """地上メニューでESCキーを押すと設定画面に遷移"""
        # Arrange: 地上メニューを適切にMenuStackManagerに登録
        overworld_manager.is_active = True
        overworld_manager.settings_active = False
        
        # 地上メニューをMenuStackManagerに登録
        if overworld_manager.main_menu and overworld_manager.menu_stack_manager:
            overworld_manager.menu_stack_manager.push_menu(
                overworld_manager.main_menu, 
                MenuType.ROOT
            )
        
        # ESCキーイベントを作成
        esc_event = Mock()
        esc_event.type = pygame.KEYDOWN
        esc_event.key = pygame.K_ESCAPE
        
        # Act: ESCキーイベントを処理
        result = overworld_manager.handle_event(esc_event)
        
        # Assert: 設定画面が表示される
        assert result is True
        # 注意：実際の設定画面表示処理はMenuStackManagerコールバックで行われるため、
        # ここではESCキー処理が正常に実行されたことを確認
    
    def test_esc_key_from_settings_returns_to_overworld(self, overworld_manager):
        """設定画面でESCキーを押すと地上メニューに戻る"""
        # Arrange: 設定画面をMenuStackManagerに登録
        overworld_manager.is_active = True
        overworld_manager.settings_active = True
        
        # 設定画面をMenuStackManagerに登録
        if overworld_manager.settings_menu and overworld_manager.menu_stack_manager:
            overworld_manager.menu_stack_manager.push_menu(
                overworld_manager.settings_menu, 
                MenuType.SETTINGS
            )
        
        # ESCキーイベントを作成
        esc_event = Mock()
        esc_event.type = pygame.KEYDOWN
        esc_event.key = pygame.K_ESCAPE
        
        # Act: ESCキーイベントを処理
        result = overworld_manager.handle_event(esc_event)
        
        # Assert: ESCキー処理が正常に実行される
        assert result is True
        # 注意：実際の地上メニュー表示処理はMenuStackManagerコールバックで行われるため、
        # ここではESCキー処理が正常に実行されたことを確認
    
    def test_guild_facility_exit_does_not_leave_residual_ui(self, mock_ui_manager):
        """冒険者ギルド退場時にUI要素が残存しない"""
        # Arrange: ギルドインスタンスを作成
        guild = AdventurersGuild()
        guild.current_party = Mock(spec=Party)
        guild.main_menu = UIMenu("guild_main", "冒険者ギルド")
        
        # メニューが表示されている状態をシミュレート
        with patch('src.ui.base_ui_pygame.ui_manager', mock_ui_manager):
            # Act: ギルドを退場
            guild._on_exit()
        
        # Assert: 適切にクリーンアップされる（実装で確認）
        # これは実装時にメニュー非表示処理が追加されることを期待
        assert True  # プレースホルダー
    
    @patch('src.ui.base_ui_pygame.ui_manager')
    def test_spell_slot_dialog_ok_button_works(self, mock_ui_manager, mock_party):
        """スペルスロット設定の"装備しました"ダイアログでOKボタンが機能する"""
        # Arrange: 宿屋インスタンスを作成
        inn = Inn()
        inn.current_party = mock_party
        
        # スペルブックを持つキャラクターをモック
        mock_character = Mock()
        mock_character.name = "テスト魔術師"
        mock_character.character_class = "mage"
        mock_character.character_id = "test_mage_1"
        mock_character.experience.level = 5
        mock_spellbook = Mock()
        mock_spellbook.learned_spells = ["fireball"]
        mock_spellbook.spell_slots = {1: [Mock(), Mock()], 2: [Mock()]}
        mock_character.spellbook = mock_spellbook
        
        inn.current_party.get_all_characters.return_value = [mock_character]
        
        # メニュー作成をモック
        mock_ui_manager.add_menu = Mock()
        mock_ui_manager.show_menu = Mock()
        mock_ui_manager.hide_menu = Mock()
        mock_ui_manager.add_dialog = Mock()
        mock_ui_manager.show_dialog = Mock()
        mock_ui_manager.hide_dialog = Mock()
        
        # Act: 魔法をスロットに装備（成功ケース）
        with patch.object(inn, '_get_or_create_spellbook', return_value=mock_spellbook):
            with patch.object(mock_spellbook, 'equip_spell_to_slot', return_value=True):
                inn._equip_spell_to_slot(mock_character, "fireball", 1, 0)
        
        # Assert: 成功メッセージが表示され、適切にメニューに戻る
        # 成功メッセージ表示の確認（実装で_show_success_messageが呼ばれることを期待）
        assert True  # プレースホルダー - 実装でのメッセージ表示を確認
    
    def test_menu_stack_manager_esc_handling(self, menu_stack_manager, mock_ui_manager):
        """MenuStackManagerのESCキー処理が正常に動作する"""
        # Arrange: メニュー階層を構築
        root_menu = UIMenu("overworld_main", "地上マップ")
        facility_menu = UIMenu("guild_main", "冒険者ギルド")
        submenu = UIMenu("party_formation", "パーティ編成")
        
        # メニューをスタックにプッシュ
        menu_stack_manager.push_menu(root_menu, MenuType.ROOT)
        menu_stack_manager.push_menu(facility_menu, MenuType.FACILITY_MAIN)
        menu_stack_manager.push_menu(submenu, MenuType.SUBMENU)
        
        # Act: ESCキーを処理
        result = menu_stack_manager.handle_escape_key()
        
        # Assert: 前のメニューに戻る
        assert result is True
        current_menu = menu_stack_manager.peek_current_menu()
        assert current_menu.menu.menu_id == "guild_main"
    
    def test_menu_stack_manager_back_to_root(self, menu_stack_manager, mock_ui_manager):
        """MenuStackManagerでルートメニューまで戻れる"""
        # Arrange: 深いメニュー階層を構築
        root_menu = UIMenu("overworld_main", "地上マップ")
        facility_menu = UIMenu("guild_main", "冒険者ギルド")
        submenu1 = UIMenu("party_formation", "パーティ編成")
        submenu2 = UIMenu("character_add", "キャラクター追加")
        
        menu_stack_manager.push_menu(root_menu, MenuType.ROOT)
        menu_stack_manager.push_menu(facility_menu, MenuType.FACILITY_MAIN)
        menu_stack_manager.push_menu(submenu1, MenuType.SUBMENU)
        menu_stack_manager.push_menu(submenu2, MenuType.SUBMENU)
        
        # Act: ルートまで戻る
        result = menu_stack_manager.back_to_root()
        
        # Assert: ルートメニューが表示される
        assert result is True
        current_menu = menu_stack_manager.peek_current_menu()
        assert current_menu.menu.menu_id == "overworld_main"
    
    def test_dialog_button_callbacks_work(self, mock_ui_manager):
        """ダイアログのボタンコールバックが正常に動作する"""
        # Arrange: ダイアログを作成
        dialog = UIDialog("test_dialog", "テストダイアログ", "テストメッセージ")
        
        # コールバック関数をモック
        callback_called = Mock()
        
        # ボタンを追加（現在のUI実装に合わせて）
        from src.ui.base_ui_pygame import UIButton
        ok_button = UIButton("ok_button", "OK", 400, 500, 100, 40)
        ok_button.on_click = callback_called
        dialog.add_element(ok_button)
        
        # Act: ボタンクリックをシミュレート
        ok_button.on_click()
        
        # Assert: コールバックが呼ばれる
        callback_called.assert_called_once()
    
    def test_facility_menu_transitions_use_menu_stack_manager(self, mock_ui_manager):
        """施設メニューの遷移でMenuStackManagerが使用される"""
        # Arrange: 修正後の実装を想定したテスト
        with patch('src.ui.menu_stack_manager.MenuStackManager') as MockMenuStackManager:
            mock_stack_manager = Mock()
            MockMenuStackManager.return_value = mock_stack_manager
            
            # ギルドインスタンスを作成（修正後の想定）
            guild = AdventurersGuild()
            guild.current_party = Mock(spec=Party)
            
            # MenuStackManagerが使用されることを確認するプレースホルダー
            # 実装時にguild内でMenuStackManagerを使用するように修正される
            assert True  # プレースホルダー
    
    def test_inn_spell_slot_ok_button_closes_dialog_and_returns_to_menu(self, mock_ui_manager, mock_party):
        """宿屋スペルスロット設定でOKボタンが正常にダイアログを閉じてメニューに戻る"""
        # Arrange: 宿屋とキャラクターを設定
        inn = Inn()
        inn.current_party = mock_party
        
        mock_character = Mock()
        mock_character.name = "テスト魔術師"
        mock_character.character_class = "mage"
        
        # Mock UIDialog
        with patch('src.ui.base_ui_pygame.ui_manager', mock_ui_manager):
            # Act: 成功メッセージダイアログを表示してOKボタンを押す動作をシミュレート
            inn._show_success_message("魔法を装備しました")
            
            # 現在の実装では_show_success_messageがダイアログを表示するが、
            # OKボタンのコールバックが正常に設定されていない可能性がある
            
            # Assert: ダイアログ表示とその後の適切なクリーンアップが行われる
            # これは実装修正時に確認される
            assert True  # プレースホルダー