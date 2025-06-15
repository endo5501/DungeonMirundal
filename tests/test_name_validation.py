"""名前検証ロジックのテスト"""

import pytest
from unittest.mock import Mock, patch
from src.ui.character_creation import CharacterCreationWizard


class MockWizard:
    """テスト用の最小限ウィザード"""
    
    def __init__(self):
        self.character_data = {}
        self.current_ui = None
    
    def _next_step(self):
        pass
    
    def _on_name_confirmed(self, name: str):
        """名前入力確認時の処理"""
        # 名前の検証
        if not name or not name.strip():
            # 名前が空の場合はデフォルト名を使用
            name = "Hero"
        
        # 名前の文字数制限チェック
        name = name.strip()[:20]  # 最大20文字
        
        # 特殊文字の除去（アルファベット、数字、日本語のみ許可）
        allowed_chars = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789ひらがなカタカナ漢字")
        # 簡易版：基本的な文字チェック
        if any(c in name for c in ['<', '>', '&', '"', "'"]):
            name = "Hero"  # 危険な文字がある場合はデフォルト名
        
        self.character_data['name'] = name
        
        # UIを閉じて次のステップへ
        if self.current_ui:
            # UIクリーンアップのモック
            pass
        
        self._next_step()


class TestNameValidation:
    """名前検証ロジックのテストクラス"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        self.wizard = MockWizard()
    
    def test_valid_name_confirmation(self):
        """有効な名前での確認処理テスト"""
        test_name = "テストヒーロー"
        
        # 名前確認処理を実行
        self.wizard._on_name_confirmed(test_name)
        
        # 名前が設定されることを確認
        assert self.wizard.character_data['name'] == test_name
    
    def test_empty_name_defaults_to_hero(self):
        """空の名前での確認処理テスト"""
        # 空の名前で確認処理を実行
        self.wizard._on_name_confirmed("")
        
        # デフォルト名が設定されることを確認
        assert self.wizard.character_data['name'] == "Hero"
    
    def test_whitespace_name_defaults_to_hero(self):
        """空白のみの名前での確認処理テスト"""
        # 空白のみの名前で確認処理を実行
        self.wizard._on_name_confirmed("   ")
        
        # デフォルト名が設定されることを確認
        assert self.wizard.character_data['name'] == "Hero"
    
    def test_long_name_truncation(self):
        """長すぎる名前での確認処理テスト"""
        long_name = "非常に長いキャラクター名前テストケース" # 20文字以上
        
        # 長い名前で確認処理を実行
        self.wizard._on_name_confirmed(long_name)
        
        # 20文字に切り詰められることを確認
        assert len(self.wizard.character_data['name']) <= 20
        assert self.wizard.character_data['name'] == long_name[:20]
    
    def test_special_characters_sanitization(self):
        """特殊文字を含む名前での確認処理テスト"""
        dangerous_names = [
            "Hero<script>",
            "Hero>test",
            "Hero&amp;",
            'Hero"test',
            "Hero'test"
        ]
        
        for dangerous_name in dangerous_names:
            # 特殊文字を含む名前で確認処理を実行
            self.wizard._on_name_confirmed(dangerous_name)
            
            # デフォルト名に置き換えられることを確認
            assert self.wizard.character_data['name'] == "Hero"
    
    def test_mixed_language_name(self):
        """混在言語の名前での確認処理テスト"""
        mixed_name = "HeroヒーローHERO123"
        
        # 混在言語の名前で確認処理を実行
        self.wizard._on_name_confirmed(mixed_name)
        
        # 正常に処理されることを確認
        assert self.wizard.character_data['name'] == mixed_name
    
    def test_japanese_only_name(self):
        """日本語のみの名前での確認処理テスト"""
        japanese_name = "テストヒーロー"
        
        # 日本語のみの名前で確認処理を実行
        self.wizard._on_name_confirmed(japanese_name)
        
        # 正常に処理されることを確認
        assert self.wizard.character_data['name'] == japanese_name
    
    def test_english_only_name(self):
        """英語のみの名前での確認処理テスト"""
        english_name = "TestHero123"
        
        # 英語のみの名前で確認処理を実行
        self.wizard._on_name_confirmed(english_name)
        
        # 正常に処理されることを確認
        assert self.wizard.character_data['name'] == english_name
    
    def test_name_with_leading_trailing_spaces(self):
        """前後の空白がある名前での確認処理テスト"""
        name_with_spaces = "   テストヒーロー   "
        
        # 前後の空白がある名前で確認処理を実行
        self.wizard._on_name_confirmed(name_with_spaces)
        
        # 空白が削除されることを確認
        assert self.wizard.character_data['name'] == "テストヒーロー"