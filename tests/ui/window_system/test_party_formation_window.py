"""
PartyFormationWindow のテスト

t-wada式TDDによるテストファースト開発
パーティ編成UIから新Window Systemへの移行
"""

import pytest
import pygame
import pygame_gui
from unittest.mock import Mock, patch, MagicMock
from src.ui.window_system import Window, WindowState
from src.ui.window_system.party_formation_window import PartyFormationWindow, PartyPosition


class TestPartyFormationWindow:
    """PartyFormationWindow のテストクラス"""
    
    def setup_method(self):
        """各テストメソッドの前に実行される"""
        pygame.init()
        pygame.display.set_mode((1, 1), pygame.NOFRAME)
    
    def teardown_method(self):
        """各テストメソッドの後に実行される"""
        pygame.quit()
    
    def test_party_formation_window_inherits_from_window(self):
        """PartyFormationWindowがWindowクラスを継承することを確認"""
        # Given: パーティ編成設定
        formation_config = {
            'party': Mock(),  # 既存のPartyオブジェクト
            'available_characters': [],
            'max_party_size': 6
        }
        
        # When: PartyFormationWindowを作成
        formation_window = PartyFormationWindow('party_formation', formation_config)
        
        # Then: Windowクラスを継承している
        assert isinstance(formation_window, Window)
        assert formation_window.window_id == 'party_formation'
        assert formation_window.party is formation_config['party']
        assert formation_window.modal is True  # パーティ編成は通常モーダル
    
    def test_party_formation_validates_config_structure(self):
        """パーティ編成の設定構造が検証されることを確認"""
        # When: partyが無い設定でウィンドウを作成しようとする
        # Then: 例外が発生する
        with pytest.raises(ValueError, match="Formation config must contain 'party'"):
            PartyFormationWindow('invalid_formation', {})
        
        # When: available_charactersが無い設定でウィンドウを作成しようとする
        # Then: 例外が発生する
        with pytest.raises(ValueError, match="Formation config must contain 'available_characters'"):
            PartyFormationWindow('invalid_formation', {'party': Mock()})
    
    def test_party_formation_displays_current_formation(self):
        """現在のパーティ編成が表示されることを確認"""
        # Given: キャラクターが配置されたパーティ
        mock_party = Mock()
        mock_character1 = Mock()
        mock_character1.name = "勇者"
        mock_character1.character_class = "戦士"
        mock_character1.level = 5
        
        mock_party.get_character_at_position.return_value = mock_character1
        
        formation_config = {
            'party': mock_party,
            'available_characters': [],
            'max_party_size': 6
        }
        
        formation_window = PartyFormationWindow('formation_display', formation_config)
        formation_window.create()
        
        # Then: パーティ編成が表示される
        assert formation_window.position_slots is not None
        assert len(formation_window.position_slots) == 6  # 前衛3 + 後衛3
    
    def test_party_formation_shows_available_characters(self):
        """利用可能キャラクターリストが表示されることを確認"""
        # Given: 利用可能キャラクターリスト
        mock_character1 = Mock()
        mock_character1.name = "魔法使い"
        mock_character1.character_class = "魔法使い"
        mock_character1.level = 3
        
        mock_character2 = Mock()
        mock_character2.name = "僧侶"
        mock_character2.character_class = "僧侶"
        mock_character2.level = 4
        
        formation_config = {
            'party': Mock(),
            'available_characters': [mock_character1, mock_character2],
            'max_party_size': 6
        }
        
        formation_window = PartyFormationWindow('available_display', formation_config)
        formation_window.create()
        
        # Then: 利用可能キャラクターが表示される
        assert formation_window.available_character_list is not None
        assert len(formation_window.available_characters) == 2
    
    def test_party_formation_add_character_to_position(self):
        """キャラクターをパーティポジションに追加することを確認"""
        # Given: パーティとキャラクター
        mock_party = Mock()
        mock_party.get_member_count.return_value = 0  # 現在のメンバー数
        mock_party.get_character_at_position.return_value = None  # ポジションは空
        mock_character = Mock()
        mock_character.name = "盗賊"
        
        formation_config = {
            'party': mock_party,
            'available_characters': [mock_character],
            'max_party_size': 6
        }
        
        formation_window = PartyFormationWindow('add_character', formation_config)
        formation_window.create()
        
        # When: キャラクターをポジションに追加
        result = formation_window.add_character_to_position(mock_character, PartyPosition.FRONT_LEFT)
        
        # Then: キャラクターが追加される
        assert result is True
        mock_party.add_character_at_position.assert_called_once_with(mock_character, PartyPosition.FRONT_LEFT)
    
    def test_party_formation_remove_character_from_position(self):
        """キャラクターをパーティポジションから削除することを確認"""
        # Given: キャラクターが配置されたパーティ
        mock_party = Mock()
        mock_character = Mock()
        mock_character.name = "勇者"
        mock_party.get_character_at_position.return_value = mock_character
        
        formation_config = {
            'party': mock_party,
            'available_characters': [],
            'max_party_size': 6
        }
        
        formation_window = PartyFormationWindow('remove_character', formation_config)
        formation_window.create()
        
        # When: キャラクターをポジションから削除
        result = formation_window.remove_character_from_position(PartyPosition.FRONT_LEFT)
        
        # Then: キャラクターが削除される
        assert result is True
        mock_party.remove_character_from_position.assert_called_once_with(PartyPosition.FRONT_LEFT)
    
    def test_party_formation_move_character_between_positions(self):
        """キャラクターをポジション間で移動することを確認"""
        # Given: キャラクターが配置されたパーティ
        mock_party = Mock()
        mock_character = Mock()
        mock_character.name = "勇者"
        
        # ポジション別の設定: FRONT_LEFTにはキャラクター、FRONT_CENTERは空
        def mock_get_character_at_position(position):
            if position == PartyPosition.FRONT_LEFT:
                return mock_character
            else:
                return None
        
        mock_party.get_character_at_position.side_effect = mock_get_character_at_position
        
        formation_config = {
            'party': mock_party,
            'available_characters': [],
            'max_party_size': 6
        }
        
        formation_window = PartyFormationWindow('move_character', formation_config)
        formation_window.create()
        
        # When: キャラクターを他のポジションに移動
        result = formation_window.move_character(PartyPosition.FRONT_LEFT, PartyPosition.FRONT_CENTER)
        
        # Then: キャラクターが移動される
        assert result is True
        mock_party.move_character.assert_called_once_with(PartyPosition.FRONT_LEFT, PartyPosition.FRONT_CENTER)
    
    def test_party_formation_prevents_overfill(self):
        """最大パーティサイズを超える追加を防ぐことを確認"""
        # Given: 満員のパーティ
        mock_party = Mock()
        mock_party.get_member_count.return_value = 6  # 満員
        mock_character = Mock()
        
        formation_config = {
            'party': mock_party,
            'available_characters': [mock_character],
            'max_party_size': 6
        }
        
        formation_window = PartyFormationWindow('overfill_test', formation_config)
        formation_window.create()
        
        # When: 満員のパーティにキャラクターを追加しようとする
        result = formation_window.add_character_to_position(mock_character, PartyPosition.FRONT_LEFT)
        
        # Then: 追加が拒否される
        assert result is False
    
    def test_party_formation_handles_drag_and_drop(self):
        """ドラッグアンドドロップでキャラクター移動することを確認"""
        # Given: パーティ編成ウィンドウ
        mock_party = Mock()
        mock_character = Mock()
        mock_character.name = "戦士"
        
        formation_config = {
            'party': mock_party,
            'available_characters': [],
            'max_party_size': 6
        }
        
        formation_window = PartyFormationWindow('drag_drop', formation_config)
        formation_window.create()
        
        # キャラクターをスロットに配置（ドラッグ可能にするため）
        formation_window.position_slots[PartyPosition.FRONT_LEFT].character = mock_character
        
        # When: ドラッグアンドドロップイベント
        drag_event = Mock()
        drag_event.type = pygame_gui.UI_BUTTON_START_PRESS
        drag_event.ui_element = formation_window.position_slots[PartyPosition.FRONT_LEFT].ui_element
        
        result = formation_window.handle_event(drag_event)
        
        # Then: ドラッグが開始される
        assert result is True
        assert formation_window.drag_source == PartyPosition.FRONT_LEFT
    
    def test_party_formation_keyboard_navigation(self):
        """キーボードナビゲーションが動作することを確認"""
        # Given: パーティ編成ウィンドウ
        formation_config = {
            'party': Mock(),
            'available_characters': [],
            'max_party_size': 6
        }
        
        formation_window = PartyFormationWindow('keyboard_nav', formation_config)
        formation_window.create()
        
        # When: 矢印キーでフォーカス移動
        arrow_event = Mock()
        arrow_event.type = pygame.KEYDOWN
        arrow_event.key = pygame.K_RIGHT
        arrow_event.mod = 0
        
        result = formation_window.handle_event(arrow_event)
        
        # Then: フォーカスが移動する
        assert result is True
        assert formation_window.focused_position != PartyPosition.FRONT_LEFT
    
    def test_party_formation_apply_changes(self):
        """パーティ編成変更の適用が動作することを確認"""
        # Given: 変更のあるパーティ編成
        mock_party = Mock()
        formation_config = {
            'party': mock_party,
            'available_characters': [],
            'max_party_size': 6
        }
        
        formation_window = PartyFormationWindow('apply_changes', formation_config)
        formation_window.create()
        formation_window.has_pending_changes = True
        
        # When: 変更を適用
        with patch.object(formation_window, 'send_message') as mock_send:
            result = formation_window.apply_formation()
        
        # Then: 変更が適用される
        assert result is True
        mock_send.assert_called_once_with('formation_applied', {
            'party': mock_party
        })
    
    def test_party_formation_cancel_changes(self):
        """パーティ編成変更のキャンセルが動作することを確認"""
        # Given: 変更のあるパーティ編成
        formation_config = {
            'party': Mock(),
            'available_characters': [],
            'max_party_size': 6
        }
        
        formation_window = PartyFormationWindow('cancel_changes', formation_config)
        formation_window.create()
        formation_window.has_pending_changes = True
        
        # When: 変更をキャンセル
        with patch.object(formation_window, 'send_message') as mock_send:
            result = formation_window.cancel_formation()
        
        # Then: 変更がキャンセルされる
        assert result is True
        assert formation_window.has_pending_changes is False
        mock_send.assert_called_once_with('formation_cancelled')
    
    def test_party_formation_validates_formation_rules(self):
        """パーティ編成ルールの検証が動作することを確認"""
        # Given: パーティ編成ウィンドウ
        mock_party = Mock()
        formation_config = {
            'party': mock_party,
            'available_characters': [],
            'max_party_size': 6
        }
        
        formation_window = PartyFormationWindow('validation', formation_config)
        formation_window.create()
        
        # When: 無効な編成を検証
        result = formation_window.validate_formation()
        
        # Then: 検証結果が返される
        assert isinstance(result, bool)
    
    def test_party_formation_escape_key_cancels(self):
        """ESCキーでキャンセルされることを確認"""
        # Given: パーティ編成ウィンドウ
        formation_config = {
            'party': Mock(),
            'available_characters': [],
            'max_party_size': 6
        }
        
        formation_window = PartyFormationWindow('esc_cancel', formation_config)
        formation_window.create()
        
        # When: ESCキーを押す
        with patch.object(formation_window, 'send_message') as mock_send:
            result = formation_window.handle_escape()
        
        # Then: キャンセルされる
        assert result is True
        mock_send.assert_called_once_with('formation_cancelled')
    
    def test_party_formation_enter_key_applies(self):
        """Enterキーで適用されることを確認"""
        # Given: パーティ編成ウィンドウ
        formation_config = {
            'party': Mock(),
            'available_characters': [],
            'max_party_size': 6
        }
        
        formation_window = PartyFormationWindow('enter_apply', formation_config)
        formation_window.create()
        
        # When: Enterキーを押す
        enter_event = Mock()
        enter_event.type = pygame.KEYDOWN
        enter_event.key = pygame.K_RETURN
        enter_event.mod = 0
        
        with patch.object(formation_window, 'send_message') as mock_send:
            result = formation_window.handle_event(enter_event)
        
        # Then: 編成が適用される
        assert result is True
        mock_send.assert_called_once_with('formation_applied', {
            'party': formation_window.party
        })
    
    def test_party_formation_displays_character_stats(self):
        """選択されたキャラクターの詳細情報が表示されることを確認"""
        # Given: キャラクター情報を持つパーティ編成
        mock_character = Mock()
        mock_character.name = "勇者"
        mock_character.character_class = "戦士"
        mock_character.level = 10
        mock_character.stats = {'strength': 18, 'dexterity': 14}
        
        formation_config = {
            'party': Mock(),
            'available_characters': [mock_character],
            'max_party_size': 6
        }
        
        formation_window = PartyFormationWindow('character_stats', formation_config)
        formation_window.create()
        
        # When: キャラクターを選択
        formation_window.select_character(mock_character)
        
        # Then: キャラクター詳細が表示される
        assert formation_window.selected_character == mock_character
        assert formation_window.character_detail_panel is not None
    
    def test_party_formation_cleanup_removes_ui_elements(self):
        """クリーンアップでUI要素が適切に削除されることを確認"""
        # Given: 作成されたパーティ編成ウィンドウ
        formation_config = {
            'party': Mock(),
            'available_characters': [],
            'max_party_size': 6
        }
        
        formation_window = PartyFormationWindow('cleanup_formation', formation_config)
        formation_window.create()
        
        # When: クリーンアップを実行
        formation_window.cleanup_ui()
        
        # Then: UI要素が削除される
        assert formation_window.position_slots == {}
        assert formation_window.available_character_list is None
        assert formation_window.ui_manager is None