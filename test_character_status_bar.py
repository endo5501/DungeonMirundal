#!/usr/bin/env python3
"""キャラクターステータスバーのテスト"""

import pytest
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import pygame
from unittest.mock import Mock, patch
from src.ui.character_status_bar import CharacterStatusBar, CharacterSlot, create_character_status_bar
from src.character.party import Party
from src.character.character import Character, CharacterStatus
from src.utils.logger import logger

class MockCharacter:
    """テスト用モックキャラクター"""
    
    def __init__(self, name: str, current_hp: int = 100, max_hp: int = 100, status: CharacterStatus = CharacterStatus.GOOD):
        self.name = name
        self.status = status
        self.derived_stats = Mock()
        self.derived_stats.current_hp = current_hp
        self.derived_stats.max_hp = max_hp

class TestCharacterStatusBar:
    """キャラクターステータスバーのテスト"""
    
    @pytest.fixture(autouse=True)
    def setup_pygame(self):
        """Pygameの初期化"""
        pygame.init()
        pygame.display.set_mode((1024, 768), pygame.NOFRAME)
        yield
        pygame.quit()
    
    def test_character_slot_initialization(self):
        """キャラクタースロットの初期化テスト"""
        slot = CharacterSlot(x=0, y=600, width=170, height=100, slot_index=0)
        
        assert slot.x == 0
        assert slot.y == 600
        assert slot.width == 170
        assert slot.height == 100
        assert slot.slot_index == 0
        assert slot.character is None
        
        # レイアウト設定の確認
        assert slot.image_x == 10
        assert slot.image_y == 610
        assert slot.name_x == 68  # 10 + 48 + 20
        assert slot.name_y == 610
    
    def test_character_slot_set_character(self):
        """キャラクタースロットのキャラクター設定テスト"""
        slot = CharacterSlot(x=0, y=600, width=170, height=100, slot_index=0)
        character = MockCharacter("テストヒーロー", 80, 100)
        
        slot.set_character(character)
        assert slot.character == character
        
        # Noneを設定
        slot.set_character(None)
        assert slot.character is None
    
    def test_character_status_bar_initialization(self):
        """キャラクターステータスバーの初期化テスト"""
        status_bar = CharacterStatusBar(x=0, y=668, width=1024, height=100)
        
        assert status_bar.rect.x == 0
        assert status_bar.rect.y == 668
        assert status_bar.rect.width == 1024
        assert status_bar.rect.height == 100
        assert len(status_bar.slots) == 6
        assert status_bar.party is None
        
        # 各スロットの位置確認
        slot_width = 1024 // 6  # 約170
        for i, slot in enumerate(status_bar.slots):
            expected_x = i * slot_width
            assert slot.x == expected_x
            assert slot.y == 668
            assert slot.slot_index == i
    
    def test_character_status_bar_set_party(self):
        """パーティ設定テスト"""
        status_bar = CharacterStatusBar()
        
        # モックパーティを作成
        mock_party = Mock()
        characters = {
            "char1": MockCharacter("Hero1", 100, 100),
            "char2": MockCharacter("Hero2", 50, 80, CharacterStatus.INJURED),
            "char3": MockCharacter("Hero3", 0, 60, CharacterStatus.DEAD)
        }
        mock_party.characters = characters
        
        status_bar.set_party(mock_party)
        
        assert status_bar.party == mock_party
        
        # スロットにキャラクターが設定されていることを確認
        assert status_bar.slots[0].character.name == "Hero1"
        assert status_bar.slots[1].character.name == "Hero2"
        assert status_bar.slots[2].character.name == "Hero3"
        # 残りのスロットは空
        assert status_bar.slots[3].character is None
        assert status_bar.slots[4].character is None
        assert status_bar.slots[5].character is None
    
    def test_character_status_bar_render_with_party(self):
        """パーティありでの描画テスト"""
        status_bar = CharacterStatusBar()
        
        # モックパーティを作成
        mock_party = Mock()
        characters = {
            "char1": MockCharacter("Hero1", 100, 100),
            "char2": MockCharacter("Hero2", 25, 100, CharacterStatus.INJURED),
        }
        mock_party.characters = characters
        status_bar.set_party(mock_party)
        
        # テスト用画面を作成
        screen = pygame.Surface((1024, 768))
        font = pygame.font.Font(None, 16)
        
        # 描画テスト（エラーが発生しないことを確認）
        try:
            status_bar.render(screen, font)
        except Exception as e:
            pytest.fail(f"Render should not raise exception: {e}")
    
    def test_character_status_bar_render_without_party(self):
        """パーティなしでの描画テスト"""
        status_bar = CharacterStatusBar()
        
        # テスト用画面を作成
        screen = pygame.Surface((1024, 768))
        font = pygame.font.Font(None, 16)
        
        # 描画テスト（エラーが発生しないことを確認）
        try:
            status_bar.render(screen, font)
        except Exception as e:
            pytest.fail(f"Render should not raise exception: {e}")
    
    def test_create_character_status_bar_function(self):
        """create_character_status_bar関数のテスト"""
        status_bar = create_character_status_bar(1024, 768)
        
        assert isinstance(status_bar, CharacterStatusBar)
        assert status_bar.rect.x == 0
        assert status_bar.rect.y == 668  # 768 - 100
        assert status_bar.rect.width == 1024
        assert status_bar.rect.height == 100
    
    def test_character_status_bar_different_screen_sizes(self):
        """異なる画面サイズでのテスト"""
        # 小さい画面
        small_bar = create_character_status_bar(800, 600)
        assert small_bar.rect.y == 500  # 600 - 100
        assert small_bar.rect.width == 800
        
        # 大きい画面
        large_bar = create_character_status_bar(1920, 1080)
        assert large_bar.rect.y == 980  # 1080 - 100
        assert large_bar.rect.width == 1920
    
    def test_character_slot_render_empty(self):
        """空スロットの描画テスト"""
        slot = CharacterSlot(x=0, y=600, width=170, height=100, slot_index=0)
        
        screen = pygame.Surface((1024, 768))
        font = pygame.font.Font(None, 16)
        
        # 空スロットの描画テスト
        try:
            slot.render(screen, font)
        except Exception as e:
            pytest.fail(f"Empty slot render should not raise exception: {e}")
    
    def test_character_slot_render_with_character(self):
        """キャラクターありスロットの描画テスト"""
        slot = CharacterSlot(x=0, y=600, width=170, height=100, slot_index=0)
        character = MockCharacter("TestHero", 75, 100, CharacterStatus.INJURED)
        slot.set_character(character)
        
        screen = pygame.Surface((1024, 768))
        font = pygame.font.Font(None, 16)
        
        # キャラクターありスロットの描画テスト
        try:
            slot.render(screen, font)
        except Exception as e:
            pytest.fail(f"Character slot render should not raise exception: {e}")
    
    def test_character_slot_different_status_colors(self):
        """異なるキャラクター状態での色テスト"""
        slot = CharacterSlot(x=0, y=600, width=170, height=100, slot_index=0)
        screen = pygame.Surface((1024, 768))
        font = pygame.font.Font(None, 16)
        
        # 各状態での描画テスト
        statuses = [
            CharacterStatus.GOOD,
            CharacterStatus.INJURED,
            CharacterStatus.UNCONSCIOUS,
            CharacterStatus.DEAD
        ]
        
        for status in statuses:
            character = MockCharacter(f"Hero_{status.value}", 50, 100, status)
            slot.set_character(character)
            
            try:
                slot.render(screen, font)
            except Exception as e:
                pytest.fail(f"Render with status {status} should not raise exception: {e}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])