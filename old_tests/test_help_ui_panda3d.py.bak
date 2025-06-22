"""ヘルプUIシステムのテスト"""

import pytest
from unittest.mock import Mock, patch

from src.ui.help_ui import HelpUI, HelpCategory


class TestHelpUI:
    """ヘルプUIのテスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        self.help_ui = HelpUI()
    
    def test_help_ui_initialization(self):
        """ヘルプUIの初期化テスト"""
        assert self.help_ui.is_open == False
        assert self.help_ui.current_category is None
        assert self.help_ui.help_content is not None
        assert len(self.help_ui.help_content) > 0
    
    def test_help_content_initialization(self):
        """ヘルプコンテンツの初期化テスト"""
        content = self.help_ui.help_content
        
        # 全カテゴリが存在することを確認
        for category in HelpCategory:
            assert category in content
            assert "title" in content[category]
            assert "sections" in content[category]
    
    def test_basic_controls_content(self):
        """基本操作ヘルプコンテンツのテスト"""
        basic_controls = self.help_ui.help_content[HelpCategory.BASIC_CONTROLS]
        
        assert basic_controls["title"] == "基本操作"
        assert len(basic_controls["sections"]) >= 2
        
        # 移動操作セクションの確認
        movement_section = basic_controls["sections"][0]
        assert movement_section["title"] == "移動操作"
        assert "keyboard" in movement_section
        assert "gamepad" in movement_section
        assert len(movement_section["keyboard"]) > 0
        assert len(movement_section["gamepad"]) > 0
    
    def test_dungeon_exploration_content(self):
        """ダンジョン探索ヘルプコンテンツのテスト"""
        dungeon_content = self.help_ui.help_content[HelpCategory.DUNGEON_EXPLORATION]
        
        assert dungeon_content["title"] == "ダンジョン探索"
        assert len(dungeon_content["sections"]) >= 2
        
        # 探索の基本セクションの確認
        basic_section = dungeon_content["sections"][0]
        assert basic_section["title"] == "探索の基本"
        assert "content" in basic_section
        assert len(basic_section["content"]) > 0
    
    def test_combat_system_content(self):
        """戦闘システムヘルプコンテンツのテスト"""
        combat_content = self.help_ui.help_content[HelpCategory.COMBAT_SYSTEM]
        
        assert combat_content["title"] == "戦闘システム"
        assert len(combat_content["sections"]) >= 2
        
        # 戦闘の基本セクションの確認
        basic_section = combat_content["sections"][0]
        assert basic_section["title"] == "戦闘の基本"
        assert "content" in basic_section
        assert any("ターン制" in item for item in basic_section["content"])
    
    def test_magic_system_content(self):
        """魔法システムヘルプコンテンツのテスト"""
        magic_content = self.help_ui.help_content[HelpCategory.MAGIC_SYSTEM]
        
        assert magic_content["title"] == "魔法システム"
        assert len(magic_content["sections"]) >= 2
        
        # 魔法の基本セクションの確認
        basic_section = magic_content["sections"][0]
        assert basic_section["title"] == "魔法の基本"
        assert "content" in basic_section
        assert any("スロット" in item for item in basic_section["content"])
    
    def test_equipment_system_content(self):
        """装備システムヘルプコンテンツのテスト"""
        equipment_content = self.help_ui.help_content[HelpCategory.EQUIPMENT_SYSTEM]
        
        assert equipment_content["title"] == "装備システム"
        assert len(equipment_content["sections"]) >= 2
        
        # 装備の基本セクションの確認
        basic_section = equipment_content["sections"][0]
        assert basic_section["title"] == "装備の基本"
        assert "content" in basic_section
        assert any("スロット" in item for item in basic_section["content"])
    
    def test_inventory_management_content(self):
        """インベントリ管理ヘルプコンテンツのテスト"""
        inventory_content = self.help_ui.help_content[HelpCategory.INVENTORY_MANAGEMENT]
        
        assert inventory_content["title"] == "インベントリ管理"
        assert len(inventory_content["sections"]) >= 2
        
        # アイテム管理セクションの確認
        management_section = inventory_content["sections"][0]
        assert management_section["title"] == "アイテム管理"
        assert "content" in management_section
        assert any("インベントリ" in item for item in management_section["content"])
    
    def test_character_development_content(self):
        """キャラクター育成ヘルプコンテンツのテスト"""
        character_content = self.help_ui.help_content[HelpCategory.CHARACTER_DEVELOPMENT]
        
        assert character_content["title"] == "キャラクター育成"
        assert len(character_content["sections"]) >= 2
        
        # レベルアップセクションの確認
        levelup_section = character_content["sections"][0]
        assert levelup_section["title"] == "レベルアップ"
        assert "content" in levelup_section
        assert any("経験値" in item for item in levelup_section["content"])
        
        # 能力値セクションの確認
        stats_section = character_content["sections"][1]
        assert stats_section["title"] == "能力値の意味"
        assert "content" in stats_section
        assert any("筋力" in item for item in stats_section["content"])
        assert any("敏捷性" in item for item in stats_section["content"])
        assert any("知力" in item for item in stats_section["content"])
        assert any("信仰" in item for item in stats_section["content"])
        assert any("運" in item for item in stats_section["content"])
    
    def test_overworld_navigation_content(self):
        """地上部ナビゲーションヘルプコンテンツのテスト"""
        overworld_content = self.help_ui.help_content[HelpCategory.OVERWORLD_NAVIGATION]
        
        assert overworld_content["title"] == "地上部ナビゲーション"
        assert len(overworld_content["sections"]) >= 2
        
        # 施設の利用セクションの確認
        facilities_section = overworld_content["sections"][0]
        assert facilities_section["title"] == "施設の利用"
        assert "content" in facilities_section
        assert any("ギルド" in item for item in facilities_section["content"])
        assert any("宿屋" in item for item in facilities_section["content"])
        assert any("商店" in item for item in facilities_section["content"])
        assert any("神殿" in item for item in facilities_section["content"])
        assert any("酒場" in item for item in facilities_section["content"])
    
    @patch('src.ui.help_ui.ui_manager')
    def test_show_help_menu(self, mock_ui_manager):
        """ヘルプメニュー表示のテスト"""
        self.help_ui.show_help_menu()
        
        # UIマネージャーのメソッドが呼ばれたことを確認
        assert mock_ui_manager.register_element.called
        assert mock_ui_manager.show_element.called
        assert self.help_ui.is_open == True
    
    @patch('src.ui.help_ui.ui_manager')
    def test_show_category_help(self, mock_ui_manager):
        """カテゴリ別ヘルプ表示のテスト"""
        category = HelpCategory.BASIC_CONTROLS
        self.help_ui._show_category_help(category)
        
        # カテゴリが設定されることを確認
        assert self.help_ui.current_category == category
        
        # UIマネージャーのメソッドが呼ばれたことを確認
        assert mock_ui_manager.register_element.called
        assert mock_ui_manager.show_element.called
    
    @patch('src.ui.help_ui.ui_manager')
    def test_show_quick_reference(self, mock_ui_manager):
        """クイックリファレンス表示のテスト"""
        self.help_ui._show_quick_reference()
        
        # ダイアログが表示されることを確認
        assert mock_ui_manager.register_element.called
        assert mock_ui_manager.show_element.called
    
    @patch('src.ui.help_ui.ui_manager')
    def test_show_controls_guide(self, mock_ui_manager):
        """操作ガイド表示のテスト"""
        self.help_ui._show_controls_guide()
        
        # ダイアログが表示されることを確認
        assert mock_ui_manager.register_element.called
        assert mock_ui_manager.show_element.called
    
    @patch('src.ui.help_ui.ui_manager')
    def test_show_context_help(self, mock_ui_manager):
        """コンテキストヘルプ表示のテスト"""
        contexts = ["combat", "dungeon", "overworld", "inventory", "equipment", "magic"]
        
        for context in contexts:
            mock_ui_manager.reset_mock()
            self.help_ui.show_context_help(context)
            
            # 各コンテキストでダイアログが表示されることを確認
            assert mock_ui_manager.register_element.called
            assert mock_ui_manager.show_element.called
    
    @patch('src.ui.help_ui.ui_manager')
    def test_show_first_time_help(self, mock_ui_manager):
        """初回ヘルプ表示のテスト"""
        self.help_ui.show_first_time_help()
        
        # ダイアログが表示されることを確認
        assert mock_ui_manager.register_element.called
        assert mock_ui_manager.show_element.called
    
    def test_show_section_detail(self):
        """セクション詳細表示のテスト"""
        # テスト用セクション
        test_section = {
            "title": "テストセクション",
            "content": ["項目1", "項目2"],
            "keyboard": ["W: 前進", "S: 後退"],
            "gamepad": ["左スティック: 移動"]
        }
        
        # 例外が発生しないことを確認
        try:
            self.help_ui._show_section_detail(test_section)
        except Exception as e:
            # UIマネージャー関連のエラーは許容
            if "ui_manager" not in str(e).lower():
                raise
    
    def test_ui_state_management(self):
        """UI状態管理のテスト"""
        # 初期状態
        assert self.help_ui.is_open == False
        assert self.help_ui.current_category is None
        
        # 状態変更
        self.help_ui.is_open = True
        self.help_ui.current_category = HelpCategory.COMBAT_SYSTEM
        
        assert self.help_ui.is_open == True
        assert self.help_ui.current_category == HelpCategory.COMBAT_SYSTEM
        
        # クリーンアップテスト
        self.help_ui.destroy()
        assert self.help_ui.current_category is None
        assert self.help_ui.is_open == False
    
    def test_help_ui_navigation_flow(self):
        """ヘルプUIナビゲーションフローのテスト"""
        # メニュー表示状態の設定
        self.help_ui.is_open = True
        
        # 表示・非表示のテスト
        self.help_ui.hide()
        assert self.help_ui.is_open == False


class TestHelpUIIntegration:
    """ヘルプUI統合テスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        self.help_ui = HelpUI()
    
    def test_help_ui_full_workflow(self):
        """ヘルプUI完全ワークフローのテスト"""
        # 1. 初期状態確認
        assert self.help_ui.is_open == False
        
        # 2. ヘルプコンテンツが適切に初期化されていることを確認
        assert len(self.help_ui.help_content) == len(HelpCategory)
        
        # 3. 各カテゴリのコンテンツが存在することを確認
        for category in HelpCategory:
            content = self.help_ui.help_content[category]
            assert "title" in content
            assert "sections" in content
            assert len(content["sections"]) > 0
        
        # 4. 表示状態管理
        self.help_ui.is_open = True
        assert self.help_ui.is_open == True
        
        # 5. クリーンアップ
        self.help_ui.destroy()
        assert self.help_ui.is_open == False
    
    def test_help_content_completeness(self):
        """ヘルプコンテンツの完全性テスト"""
        # 各カテゴリが必要なコンテンツを持っていることを確認
        required_categories = [
            HelpCategory.BASIC_CONTROLS,
            HelpCategory.DUNGEON_EXPLORATION,
            HelpCategory.COMBAT_SYSTEM,
            HelpCategory.MAGIC_SYSTEM,
            HelpCategory.EQUIPMENT_SYSTEM,
            HelpCategory.INVENTORY_MANAGEMENT,
            HelpCategory.CHARACTER_DEVELOPMENT,
            HelpCategory.OVERWORLD_NAVIGATION
        ]
        
        for category in required_categories:
            assert category in self.help_ui.help_content
            content = self.help_ui.help_content[category]
            
            # タイトルが存在し、空でないことを確認
            assert content["title"]
            assert len(content["title"]) > 0
            
            # セクションが存在し、空でないことを確認
            assert "sections" in content
            assert len(content["sections"]) > 0
            
            # 各セクションが適切な構造を持つことを確認
            for section in content["sections"]:
                assert "title" in section
                assert section["title"]
                # content、keyboard、gamepadのいずれかが存在すること
                assert ("content" in section or 
                       "keyboard" in section or 
                       "gamepad" in section)
    
    def test_context_help_completeness(self):
        """コンテキストヘルプの完全性テスト"""
        expected_contexts = [
            "combat", "dungeon", "overworld", 
            "inventory", "equipment", "magic"
        ]
        
        for context in expected_contexts:
            # 例外が発生しないことを確認
            try:
                self.help_ui.show_context_help(context)
            except Exception as e:
                # UIマネージャー関連のエラーは許容
                if "ui_manager" not in str(e).lower():
                    raise