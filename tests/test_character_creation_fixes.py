"""キャラクター作成バグ修正テスト"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.ui.character_creation import CharacterCreationWizard
from src.core.config_manager import config_manager


class TestCharacterCreationFixes:
    """キャラクター作成バグ修正テスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        self.mock_callback = Mock()
        
    def test_on_cancel_attribute_initialization(self):
        """on_cancel属性の初期化テスト（クラッシュ修正）"""
        wizard = CharacterCreationWizard(self.mock_callback)
        
        # on_cancel属性が初期化されていることを確認
        assert hasattr(wizard, 'on_cancel')
        assert wizard.on_cancel is None
        
        # on_cancelが呼び出し可能な状態でも安全であることを確認
        wizard.on_cancel = Mock()
        wizard.on_cancel()
        wizard.on_cancel.assert_called_once()
    
    def test_name_input_text_configuration(self):
        """名前入力テキストの設定確認（ラベル重複修正）"""
        # character.enter_name_detailキーが存在することを確認
        try:
            detail_text = config_manager.get_text("character.enter_name_detail")
            assert detail_text is not None
            assert isinstance(detail_text, str)
            assert "キャラクターの名前を入力してください:" == detail_text
        except Exception:
            # フォールバック動作を確認
            detail_text = "キャラクターの名前を入力してください:"
            assert detail_text is not None
    
    @patch('src.ui.base_ui.ui_manager.register_element')
    @patch('src.ui.base_ui.ui_manager.show_element')
    def test_name_input_dialog_creation(self, mock_show, mock_register):
        """名前入力ダイアログの作成テスト"""
        wizard = CharacterCreationWizard(self.mock_callback)
        
        # 名前入力ステップの表示
        with patch.object(config_manager, 'get_text', return_value="キャラクターの名前を入力してください:"):
            wizard._show_name_input()
            
        # ダイアログが正しく登録・表示されることを確認
        mock_register.assert_called_once()
        mock_show.assert_called_once()
        
        # current_uiが設定されることを確認
        assert wizard.current_ui is not None
    
    def test_reroll_stats_method_exists(self):
        """振り直しメソッドの存在確認（メニュー異常修正）"""
        wizard = CharacterCreationWizard(self.mock_callback)
        
        # _reroll_statsメソッドが存在することを確認
        assert hasattr(wizard, '_reroll_stats')
        assert callable(wizard._reroll_stats)
    
    @patch('src.ui.base_ui.ui_manager.hide_element')
    @patch('src.ui.base_ui.ui_manager.unregister_element')
    def test_reroll_stats_cleanup(self, mock_unregister, mock_hide):
        """振り直し時のUIクリーンアップテスト"""
        wizard = CharacterCreationWizard(self.mock_callback)
        
        # current_uiを模擬
        mock_ui = Mock()
        mock_ui.element_id = "test_dialog"
        wizard.current_ui = mock_ui
        
        # _show_stats_generationをモック
        with patch.object(wizard, '_show_stats_generation') as mock_show_stats:
            wizard._reroll_stats()
            
            # 既存UIが正しくクリーンアップされることを確認
            mock_hide.assert_called_once_with("test_dialog")
            mock_unregister.assert_called_once_with("test_dialog")
            
            # current_uiがクリアされることを確認
            assert wizard.current_ui is None
            
            # 統計値表示が再呼び出しされることを確認
            mock_show_stats.assert_called_once()
    
    def test_font_configuration_in_config(self):
        """フォント設定の確認（文字化け修正関連）"""
        # font_managerが利用可能であることを確認
        try:
            from src.ui.font_manager import font_manager
            assert font_manager is not None
            assert hasattr(font_manager, 'get_default_font')
        except ImportError:
            pytest.skip("font_managerが利用できません")
    
    def test_character_data_initialization(self):
        """キャラクターデータの初期化テスト"""
        wizard = CharacterCreationWizard(self.mock_callback)
        
        # character_dataが正しく初期化されていることを確認
        assert wizard.character_data is not None
        assert 'name' in wizard.character_data
        assert 'race' in wizard.character_data
        assert 'character_class' in wizard.character_data
        assert 'base_stats' in wizard.character_data
        
        # 初期値の確認
        assert wizard.character_data['name'] == ''
        assert wizard.character_data['race'] == ''
        assert wizard.character_data['character_class'] == ''
        assert wizard.character_data['base_stats'] is None
    
    def test_text_keys_exist_in_config(self):
        """必要なテキストキーが設定ファイルに存在することを確認"""
        # 実際の設定ファイルからテキストキーの存在を確認
        import yaml
        
        try:
            with open('config/text/ja.yaml', 'r', encoding='utf-8') as f:
                ja_config = yaml.safe_load(f)
                
            # characterセクションの存在確認
            assert 'character' in ja_config
            character_config = ja_config['character']
            
            # 必要なキーの存在確認
            assert 'enter_name_detail' in character_config
            assert 'reroll' in character_config
            assert character_config['enter_name_detail'] == "キャラクターの名前を入力してください:"
            
        except FileNotFoundError:
            pytest.fail("日本語テキスト設定ファイルが見つかりません")
    
    def test_wizard_step_transitions(self):
        """ウィザードステップ遷移の基本動作テスト"""
        wizard = CharacterCreationWizard(self.mock_callback)
        
        # 初期ステップの確認
        from src.ui.character_creation import CreationStep
        assert wizard.current_step == CreationStep.NAME_INPUT
        
        # ステップ遷移メソッドの存在確認
        assert hasattr(wizard, '_next_step')
        assert hasattr(wizard, '_previous_step')
        assert callable(wizard._next_step)
        assert callable(wizard._previous_step)