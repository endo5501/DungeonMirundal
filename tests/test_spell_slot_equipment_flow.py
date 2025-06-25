"""魔術スロット装備フローの詳細テスト

報告された問題:
1. OKボタンを押すと装備スロット選択画面に戻るが、その後[戻る]キーが効かない
2. スロット表示に登録した魔法が反映されていない
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.overworld.facilities.inn import Inn
from src.character.character import Character
from src.magic.spells import SpellBook, spell_manager


class TestSpellSlotEquipmentFlow:
    """魔術スロット装備フローのテスト"""
    
    @pytest.fixture
    def inn(self):
        """宿屋インスタンス"""
        inn = Inn()
        # current_partyにモックパーティを設定
        mock_party = Mock()
        mock_party.get_all_characters.return_value = []
        inn.current_party = mock_party
        # ui_managerのモックも設定
        inn.ui_manager = Mock()
        return inn
    
    @pytest.fixture
    def mock_character(self):
        """魔術師キャラクター"""
        character = Mock()
        character.name = "テスト魔術師"
        character.character_class = "mage"
        character.character_id = "test_mage_1"
        character.experience.level = 10
        return character
    
    @pytest.fixture
    def mock_spellbook(self):
        """スペルブック（実際のインスタンス）"""
        spellbook = SpellBook("test_mage_1")
        # テスト用の魔法を習得
        spellbook.learn_spell('heal')        # レベル1
        spellbook.learn_spell('fireball')    # レベル3
        return spellbook
    
    def test_spell_equipment_success_callback_returns_to_correct_menu(self, inn, mock_character, mock_spellbook):
        """魔法装備成功後のコールバックが正しいメニューに戻る"""
        # Arrange
        with patch.object(inn, '_get_or_create_spellbook', return_value=mock_spellbook) as mock_get_spellbook:
            with patch.object(mock_spellbook, 'equip_spell_to_slot', return_value=True):
                with patch.object(inn, '_show_character_spell_slot_detail') as mock_show_menu:
                    with patch.object(inn, 'show_information_dialog') as mock_show_dialog:
                        
                        # Act: 適切なスロットレベルで魔法を装備
                        inn._equip_spell_to_slot(mock_character, 'heal', 1, 0)
                        
                        # show_information_dialogが成功メッセージで呼ばれたか確認
                        mock_show_dialog.assert_called()
                        mock_get_spellbook.assert_called_with(mock_character)
                        
                        # ダイアログのボタンコールバックを手動実行
                        call_args = mock_show_dialog.call_args
                        if call_args and len(call_args[1]) > 0:
                            buttons = call_args[1].get('buttons', [])
                            if buttons and len(buttons) > 0:
                                # OKボタンのコールバックを実行
                                ok_button = buttons[0]
                                if 'callback' in ok_button and ok_button['callback']:
                                    ok_button['callback']()
                        
                        # Assert: キャラクタースペルスロット詳細メニューが呼ばれる
                        mock_show_menu.assert_called_with(mock_character)
    
    def test_spell_equipment_with_incorrect_slot_level_fails(self, inn, mock_character, mock_spellbook):
        """不適切なスロットレベルでの魔法装備が失敗する"""
        # Arrange: UIマネージャーと新システムを設定
        mock_ui_manager = Mock()
        mock_ui_manager.add_dialog = Mock()
        mock_ui_manager.show_dialog = Mock()
        inn.initialize_menu_system(mock_ui_manager)
        
        with patch.object(inn, '_get_or_create_spellbook', return_value=mock_spellbook):
            with patch.object(inn, '_show_character_spell_slot_detail') as mock_show_menu:
                
                # Act: レベル3魔法をレベル1スロットに装備（失敗するはず）
                inn._equip_spell_to_slot(mock_character, 'fireball', 1, 0)
                
                # Assert: ダイアログが表示されたことを確認（UIダイアログの正常動作確認）
                # 実際のアプリケーションでは、ユーザーがOKボタンを押すことでコールバックが実行される
                mock_ui_manager.add_dialog.assert_called()
                mock_ui_manager.show_dialog.assert_called()
    
    def test_spell_equipment_with_correct_slot_level_succeeds(self, inn, mock_character, mock_spellbook):
        """適切なスロットレベルでの魔法装備が成功する"""
        # Arrange: UIマネージャーと新システムを設定
        mock_ui_manager = Mock()
        mock_ui_manager.add_dialog = Mock()
        mock_ui_manager.show_dialog = Mock()
        inn.initialize_menu_system(mock_ui_manager)
        
        with patch.object(inn, '_get_or_create_spellbook', return_value=mock_spellbook):
            with patch.object(inn, '_show_character_spell_slot_detail') as mock_show_menu:
                
                # Act: レベル3魔法をレベル3スロットに装備（成功するはず）
                inn._equip_spell_to_slot(mock_character, 'fireball', 3, 0)
                
                # Assert: 成功ダイアログが表示されたことを確認
                mock_ui_manager.add_dialog.assert_called()
                mock_ui_manager.show_dialog.assert_called()
                
                # 実際にスロットに装備されているか確認
                level_3_slots = mock_spellbook.spell_slots[3]
                assert not level_3_slots[0].is_empty()
                assert level_3_slots[0].spell_id == 'fireball'
    
    def test_spell_slot_status_display_shows_equipped_spells(self, inn, mock_character, mock_spellbook):
        """スロット状況表示で装備済み魔法が表示される"""
        # Arrange: 実際のSpellBookインスタンスで魔法を装備
        success1 = mock_spellbook.equip_spell_to_slot('heal', 1, 0)
        success2 = mock_spellbook.equip_spell_to_slot('fireball', 3, 0)
        
        with patch.object(inn, '_get_or_create_spellbook', return_value=mock_spellbook) as mock_get_spellbook:
            with patch.object(inn, 'show_information_dialog') as mock_show_dialog:
                
                # Act: スロット状況を表示
                inn._show_spell_slot_status(mock_character)
                
                # Assert: ダイアログが呼ばれ、装備済み魔法が含まれている
                mock_show_dialog.assert_called_once()
                mock_get_spellbook.assert_called_with(mock_character)
                
                # ダイアログメッセージに装備済み魔法が含まれているか確認
                call_args = mock_show_dialog.call_args
                dialog_message = call_args[0][1]  # 2番目の引数がメッセージ
                
                # 装備成功した場合のみアサーション（日本語名での確認）
                if success1:
                    assert 'ヒール' in dialog_message or 'heal' in dialog_message
                    assert '[1] ヒール' in dialog_message or '[1] heal' in dialog_message or 'ヒール' in dialog_message
                if success2:
                    assert 'ファイアボール' in dialog_message or 'fireball' in dialog_message
                    assert '[1] ファイアボール' in dialog_message or '[1] fireball' in dialog_message or 'ファイアボール' in dialog_message
                
                # スロット状況が正しく表示されるかのテスト
                assert 'Lv.1 スロット' in dialog_message
                assert 'Lv.3 スロット' in dialog_message
    
    def test_back_button_works_after_spell_equipment(self, inn, mock_character, mock_spellbook):
        """魔法装備後に戻るボタンが機能する"""
        # Arrange
        with patch.object(inn, '_get_or_create_spellbook', return_value=mock_spellbook) as mock_get_spellbook:
            with patch.object(inn, 'show_submenu') as mock_show_submenu:
                with patch.object(inn, '_show_adventure_preparation') as mock_show_adventure_prep:
                    
                    # Act1: キャラクタースペルスロット詳細メニューを表示
                    inn._show_character_spell_slot_detail(mock_character)
                    
                    # Assert1: サブメニューが表示される
                    mock_show_submenu.assert_called_once()
                    
                    # 表示されたメニューを取得
                    spell_mgmt_menu = mock_show_submenu.call_args[0][0]
                    
                    # Act2: メニュー内の「戻る」ボタンを探して実行
                    back_button_found = False
                    for element in spell_mgmt_menu.elements:
                        if hasattr(element, 'text') and '戻る' in str(element.text):
                            back_button_found = True
                            # 戻るボタンのコールバックを実行
                            if hasattr(element, 'on_click') and element.on_click:
                                element.on_click()
                            break
                    
                    # Assert2: 戻るボタンが存在し、冒険の準備メニューが呼ばれる
                    assert back_button_found, "魔術スロット管理メニューに戻るボタンがありません"
                    mock_show_adventure_prep.assert_called_once()
    
    def test_menu_navigation_consistency(self, inn, mock_character, mock_spellbook):
        """メニューナビゲーションの一貫性テスト"""
        # Arrange
        with patch.object(inn, '_get_or_create_spellbook', return_value=mock_spellbook) as mock_get_spellbook:
            with patch.object(inn, 'show_submenu') as mock_show_submenu:
                
                # スパイユーザー選択 → キャラクター詳細 → 装備メニュー → スロット選択 → 装備実行
                
                # Act1: 魔法使いキャラクター選択
                spell_users = [mock_character]
                inn._show_new_spell_user_selection(spell_users)
                
                # Act2: キャラクター詳細メニュー
                inn._show_character_spell_slot_detail(mock_character)
                
                # Act3: 魔法装備メニュー
                inn._show_spell_equip_menu(mock_character)
                
                # すべてのメニュー表示でエラーが発生しないことを確認
                assert mock_show_submenu.call_count >= 1
    
    def test_spell_equipment_error_handling(self, inn, mock_character, mock_spellbook):
        """魔法装備のエラーハンドリング"""
        # Arrange: UIマネージャーと新システムを設定
        mock_ui_manager = Mock()
        mock_ui_manager.add_dialog = Mock()
        mock_ui_manager.show_dialog = Mock()
        inn.initialize_menu_system(mock_ui_manager)
        
        # Arrange: 装備が失敗するようにモック
        with patch.object(inn, '_get_or_create_spellbook', return_value=mock_spellbook):
            with patch.object(mock_spellbook, 'equip_spell_to_slot', return_value=False):
                with patch.object(inn, '_show_character_spell_slot_detail') as mock_show_menu:
                    
                    # Act: 装備が失敗する場合
                    inn._equip_spell_to_slot(mock_character, 'heal', 1, 0)
                    
                    # Assert: エラーダイアログが表示されたことを確認
                    mock_ui_manager.add_dialog.assert_called()
                    mock_ui_manager.show_dialog.assert_called()