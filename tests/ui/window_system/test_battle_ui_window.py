"""
BattleUIWindow のテスト

t-wada式TDDによるテストファースト開発
戦闘システムから新Window Systemへの移行
"""

import pytest
import pygame
import pygame_gui
from unittest.mock import Mock, patch, MagicMock
from src.ui.window_system import Window, WindowState
from src.ui.window_system.battle_ui_window import BattleUIWindow, BattlePhase, BattleActionType


class TestBattleUIWindow:
    """BattleUIWindow のテストクラス"""
    
    def setup_method(self):
        """各テストメソッドの前に実行される"""
        pygame.init()
        pygame.display.set_mode((1, 1), pygame.NOFRAME)
    
    def teardown_method(self):
        """各テストメソッドの後に実行される"""
        pygame.quit()
    
    def test_battle_ui_window_inherits_from_window(self):
        """BattleUIWindowがWindowクラスを継承することを確認"""
        # Given: 戦闘設定
        battle_config = {
            'battle_manager': Mock(),
            'party': Mock(),
            'enemies': Mock()
        }
        
        # When: BattleUIWindowを作成
        battle_window = BattleUIWindow('battle', battle_config)
        
        # Then: Windowクラスを継承している
        assert isinstance(battle_window, Window)
        assert battle_window.window_id == 'battle'
        assert battle_window.battle_manager is not None
    
    def test_battle_ui_validates_config_structure(self):
        """戦闘UIの設定構造が検証されることを確認"""
        # When: battle_managerが無い設定でウィンドウを作成しようとする
        # Then: 例外が発生する
        with pytest.raises(ValueError, match="Battle config must contain 'battle_manager'"):
            BattleUIWindow('invalid_battle', {})
        
        # When: partyが無い設定でウィンドウを作成しようとする
        # Then: 例外が発生する
        with pytest.raises(ValueError, match="Battle config must contain 'party'"):
            BattleUIWindow('invalid_battle', {'battle_manager': Mock()})
    
    def test_battle_ui_displays_party_status(self):
        """パーティステータスが表示されることを確認"""
        # Given: パーティメンバーを含む設定
        mock_character1 = Mock()
        mock_character1.name = 'ヒーロー'
        mock_character1.hp = 80
        mock_character1.max_hp = 100
        mock_character1.mp = 30
        mock_character1.max_mp = 50
        mock_character1.status_effects = []
        
        mock_character2 = Mock()
        mock_character2.name = 'ウィザード'
        mock_character2.hp = 60
        mock_character2.max_hp = 80
        mock_character2.mp = 45
        mock_character2.max_mp = 70
        mock_character2.status_effects = ['魔法力強化']
        
        mock_party = Mock()
        mock_party.get_alive_members.return_value = [mock_character1, mock_character2]
        
        battle_config = {
            'battle_manager': Mock(),
            'party': mock_party,
            'enemies': Mock()
        }
        
        battle_window = BattleUIWindow('party_battle', battle_config)
        battle_window.create()
        
        # Then: パーティステータスパネルが作成される
        assert battle_window.party_status_panel is not None
        assert len(battle_window.character_status_displays) == 2
    
    def test_battle_ui_displays_enemy_status(self):
        """敵ステータスが表示されることを確認"""
        # Given: 敵を含む設定
        mock_orc = Mock()
        mock_orc.name = 'オーク'
        mock_orc.hp = 120
        mock_orc.max_hp = 150
        mock_orc.is_alive.return_value = True
        mock_orc.status_effects = ['怒り']
        
        mock_goblin = Mock()
        mock_goblin.name = 'ゴブリン'
        mock_goblin.hp = 0
        mock_goblin.max_hp = 40
        mock_goblin.is_alive.return_value = False
        mock_goblin.status_effects = []
        
        mock_enemies = Mock()
        mock_enemies.get_all_enemies.return_value = [mock_orc, mock_goblin]
        
        battle_config = {
            'battle_manager': Mock(),
            'party': Mock(),
            'enemies': mock_enemies
        }
        
        battle_window = BattleUIWindow('enemy_battle', battle_config)
        battle_window.create()
        
        # Then: 敵ステータスパネルが作成される
        assert battle_window.enemy_status_panel is not None
        assert len(battle_window.enemy_status_displays) == 2
    
    def test_battle_ui_shows_action_menu(self):
        """アクションメニューが表示されることを確認"""
        # Given: アクション選択可能な状態
        mock_battle_manager = Mock()
        mock_battle_manager.get_current_phase.return_value = BattlePhase.PLAYER_ACTION
        mock_battle_manager.get_current_character.return_value = Mock(name='ヒーロー')
        mock_battle_manager.get_available_actions.return_value = [
            {'type': 'attack', 'name': '攻撃', 'enabled': True},
            {'type': 'magic', 'name': '魔法', 'enabled': True},
            {'type': 'item', 'name': 'アイテム', 'enabled': True},
            {'type': 'defend', 'name': '防御', 'enabled': True}
        ]
        
        battle_config = {
            'battle_manager': mock_battle_manager,
            'party': Mock(),
            'enemies': Mock()
        }
        
        battle_window = BattleUIWindow('action_battle', battle_config)
        battle_window.create()
        
        # When: アクションフェーズに更新
        battle_window.update_battle_phase(BattlePhase.PLAYER_ACTION)
        
        # Then: アクションメニューが表示される
        assert battle_window.action_menu_panel is not None
        assert len(battle_window.action_buttons) == 4
    
    def test_battle_ui_handles_action_selection(self):
        """アクション選択が処理されることを確認"""
        # Given: アクション可能な戦闘状態
        mock_battle_manager = Mock()
        mock_battle_manager.get_current_phase.return_value = BattlePhase.PLAYER_ACTION
        mock_battle_manager.can_perform_action.return_value = True
        
        battle_config = {
            'battle_manager': mock_battle_manager,
            'party': Mock(),
            'enemies': Mock()
        }
        
        battle_window = BattleUIWindow('select_battle', battle_config)
        battle_window.create()
        battle_window.current_phase = BattlePhase.PLAYER_ACTION
        
        # When: 攻撃アクションを選択
        with patch.object(battle_window, 'send_message') as mock_send:
            result = battle_window.select_action(BattleActionType.ATTACK)
        
        # Then: アクション選択メッセージが送信される
        assert result is True
        mock_send.assert_called_once_with('battle_action_selected', {
            'action_type': BattleActionType.ATTACK,
            'character': mock_battle_manager.get_current_character.return_value
        })
    
    def test_battle_ui_displays_battle_log(self):
        """戦闘ログが表示されることを確認"""
        # Given: 戦闘ログを含む設定
        mock_battle_manager = Mock()
        mock_battle_manager.get_battle_log.return_value = [
            'ヒーローの攻撃！',
            'オークに15のダメージ！',
            'オークの反撃！',
            'ヒーローに8のダメージ！'
        ]
        
        battle_config = {
            'battle_manager': mock_battle_manager,
            'party': Mock(),
            'enemies': Mock(),
            'show_battle_log': True
        }
        
        battle_window = BattleUIWindow('log_battle', battle_config)
        battle_window.create()
        
        # When: 戦闘ログを更新
        battle_window.update_battle_log()
        
        # Then: 戦闘ログパネルが更新される
        assert battle_window.battle_log_panel is not None
        assert battle_window.battle_log_display is not None
    
    def test_battle_ui_handles_target_selection(self):
        """ターゲット選択が処理されることを確認"""
        # Given: ターゲット選択が必要なアクション
        mock_orc = Mock()
        mock_orc.name = 'オーク'
        mock_orc.is_alive.return_value = True
        
        mock_enemies = Mock()
        mock_enemies.get_alive_enemies.return_value = [mock_orc]
        
        battle_config = {
            'battle_manager': Mock(),
            'party': Mock(),
            'enemies': mock_enemies
        }
        
        battle_window = BattleUIWindow('target_battle', battle_config)
        battle_window.create()
        battle_window.current_phase = BattlePhase.TARGET_SELECTION
        
        # When: 敵をターゲットに選択
        with patch.object(battle_window, 'send_message') as mock_send:
            result = battle_window.select_target(mock_orc)
        
        # Then: ターゲット選択メッセージが送信される
        assert result is True
        mock_send.assert_called_once_with('battle_target_selected', {
            'target': mock_orc
        })
    
    def test_battle_ui_shows_magic_menu(self):
        """魔法メニューが表示されることを確認"""
        # Given: 魔法使用可能なキャラクター
        mock_fireball = Mock()
        mock_fireball.name = 'ファイアボール'
        mock_fireball.mp_cost = 10
        mock_fireball.can_cast.return_value = True
        
        mock_heal = Mock()
        mock_heal.name = 'ヒール'
        mock_heal.mp_cost = 5
        mock_heal.can_cast.return_value = True
        
        mock_character = Mock()
        mock_character.get_available_spells.return_value = [mock_fireball, mock_heal]
        mock_character.mp = 30
        
        mock_battle_manager = Mock()
        mock_battle_manager.get_current_character.return_value = mock_character
        
        battle_config = {
            'battle_manager': mock_battle_manager,
            'party': Mock(),
            'enemies': Mock()
        }
        
        battle_window = BattleUIWindow('magic_battle', battle_config)
        battle_window.create()
        
        # When: 魔法メニューを表示
        result = battle_window.show_magic_menu()
        
        # Then: 魔法メニューが作成される
        assert result is True
        assert battle_window.magic_menu_panel is not None
        assert len(battle_window.magic_buttons) == 2
    
    def test_battle_ui_shows_item_menu(self):
        """アイテムメニューが表示されることを確認"""
        # Given: 使用可能なアイテムを持つパーティ
        mock_potion = Mock()
        mock_potion.name = 'ポーション'
        mock_potion.is_usable_in_battle.return_value = True
        mock_potion.quantity = 3
        
        mock_ether = Mock()
        mock_ether.name = 'エーテル'
        mock_ether.is_usable_in_battle.return_value = True
        mock_ether.quantity = 1
        
        mock_party = Mock()
        mock_party.get_usable_items.return_value = [mock_potion, mock_ether]
        
        battle_config = {
            'battle_manager': Mock(),
            'party': mock_party,
            'enemies': Mock()
        }
        
        battle_window = BattleUIWindow('item_battle', battle_config)
        battle_window.create()
        
        # When: アイテムメニューを表示
        result = battle_window.show_item_menu()
        
        # Then: アイテムメニューが作成される
        assert result is True
        assert battle_window.item_menu_panel is not None
        assert len(battle_window.item_buttons) == 2
    
    def test_battle_ui_handles_turn_progression(self):
        """ターン進行が処理されることを確認"""
        # Given: ターン進行可能な戦闘状態
        mock_battle_manager = Mock()
        mock_battle_manager.advance_turn.return_value = True
        mock_battle_manager.get_current_phase.return_value = BattlePhase.ENEMY_TURN
        
        battle_config = {
            'battle_manager': mock_battle_manager,
            'party': Mock(),
            'enemies': Mock()
        }
        
        battle_window = BattleUIWindow('turn_battle', battle_config)
        battle_window.create()
        
        # When: ターンを進行
        with patch.object(battle_window, 'send_message') as mock_send:
            result = battle_window.advance_turn()
        
        # Then: ターン進行メッセージが送信される
        assert result is True
        mock_send.assert_called_once_with('battle_turn_advanced', {
            'new_phase': BattlePhase.ENEMY_TURN
        })
    
    
    def test_battle_ui_displays_status_effects(self):
        """ステータス効果が表示されることを確認"""
        # Given: ステータス効果を持つキャラクター
        mock_character = Mock()
        mock_character.name = 'ヒーロー'
        mock_character.hp = 100
        mock_character.max_hp = 100
        mock_character.mp = 50
        mock_character.max_mp = 50
        mock_character.status_effects = [
            Mock(name='毒', duration=3, effect_type='poison'),
            Mock(name='力強化', duration=5, effect_type='buff')
        ]
        
        mock_party = Mock()
        mock_party.get_alive_members.return_value = [mock_character]
        
        battle_config = {
            'battle_manager': Mock(),
            'party': mock_party,
            'enemies': Mock(),
            'show_status_effects': True
        }
        
        battle_window = BattleUIWindow('status_battle', battle_config)
        battle_window.create()
        
        # When: ステータス効果を更新
        battle_window.update_status_effects()
        
        # Then: ステータス効果が表示される
        assert battle_window.status_effects_panel is not None
    
    def test_battle_ui_escape_key_opens_menu(self):
        """ESCキーで戦闘メニューが開くことを確認"""
        # Given: 戦闘ウィンドウ
        battle_config = {
            'battle_manager': Mock(),
            'party': Mock(),
            'enemies': Mock()
        }
        
        battle_window = BattleUIWindow('menu_battle', battle_config)
        battle_window.create()
        
        # When: ESCキーを押す
        with patch.object(battle_window, 'send_message') as mock_send:
            result = battle_window.handle_escape()
        
        # Then: 戦闘メニューが要求される
        assert result is True
        mock_send.assert_called_once_with('battle_menu_requested', {})
    
    def test_battle_ui_cleanup_removes_ui_elements(self):
        """クリーンアップでUI要素が適切に削除されることを確認"""
        # Given: 作成された戦闘ウィンドウ
        battle_config = {
            'battle_manager': Mock(),
            'party': Mock(),
            'enemies': Mock()
        }
        
        battle_window = BattleUIWindow('cleanup_battle', battle_config)
        battle_window.create()
        
        # When: クリーンアップを実行
        battle_window.cleanup_ui()
        
        # Then: UI要素が削除される
        assert battle_window.action_buttons == []
        assert battle_window.party_status_panel is None
        assert battle_window.enemy_status_panel is None
        assert battle_window.ui_manager is None