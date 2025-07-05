"""Phase 6 Day 2: メモリリーク・リソース管理テスト"""

import pytest
import gc
import psutil
import os
import weakref
from unittest.mock import MagicMock, patch

from src.core.game_manager import GameManager
from src.character.party import Party
from src.character.character import Character
from src.rendering.dungeon_renderer_pygame import DungeonRendererPygame
from src.ui.dungeon_ui_pygame import DungeonUIManagerPygame
from src.dungeon.dungeon_manager import DungeonManager
from src.combat.combat_manager import CombatManager
from src.encounter.encounter_manager import EncounterManager


class TestPhase6MemoryManagement:
    """Phase 6 メモリリーク・リソース管理テスト"""
    
    def test_game_manager_memory_cleanup(self):
        """GameManager のメモリクリーンアップテスト"""
        # 初期メモリ使用量を記録
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # 複数のGameManagerインスタンスを作成・破棄
        managers = []
        for i in range(5):
            try:
                manager = GameManager()
                managers.append(manager)
            except Exception as e:
                # 初期化に失敗した場合はスキップ
                print(f"GameManager初期化失敗: {e}")
                continue
        
        # 弱参照を作成してメモリリークを検出
        weak_refs = [weakref.ref(manager) for manager in managers]
        
        # 明示的にマネージャーを削除
        for manager in managers:
            if hasattr(manager, 'cleanup'):
                manager.cleanup()
        
        managers.clear()
        
        # ガベージコレクションを実行
        gc.collect()
        
        # 弱参照が全て削除されたか確認
        alive_refs = [ref() for ref in weak_refs if ref() is not None]
        
        # メモリ使用量チェック
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # 1MB以上の増加は警告
        if memory_increase > 1024 * 1024:
            print(f"警告: メモリ使用量が {memory_increase / 1024 / 1024:.2f}MB 増加しました")
        
        # 弱参照が残っている場合はメモリリークの可能性
        assert len(alive_refs) == 0, f"メモリリークの可能性: {len(alive_refs)} 個のオブジェクトが残存"
    
    def test_party_character_memory_cleanup(self):
        """Party・Character のメモリクリーンアップテスト"""
        # 大量のキャラクターとパーティを作成
        parties = []
        characters = []
        
        for i in range(10):
            character = Character(f"test_char_{i}", "human", "fighter")
            characters.append(character)
            
            party = Party(f"test_party_{i}")
            party.add_character(character)
            parties.append(party)
        
        # 弱参照を作成
        char_refs = [weakref.ref(char) for char in characters]
        party_refs = [weakref.ref(party) for party in parties]
        
        # 明示的にクリーンアップ
        for party in parties:
            if hasattr(party, 'cleanup'):
                party.cleanup()
        
        for character in characters:
            if hasattr(character, 'cleanup'):
                character.cleanup()
        
        # オブジェクトを削除
        characters.clear()
        parties.clear()
        
        # 複数回ガベージコレクション
        for _ in range(3):
            gc.collect()
        
        # 弱参照の確認
        alive_chars = [ref() for ref in char_refs if ref() is not None]
        alive_parties = [ref() for ref in party_refs if ref() is not None]
        
        assert len(alive_chars) == 0, f"Character メモリリーク: {len(alive_chars)} 個が残存"
        assert len(alive_parties) == 0, f"Party メモリリーク: {len(alive_parties)} 個が残存"
    
    def test_renderer_memory_cleanup(self):
        """レンダラーのメモリクリーンアップテスト"""
        with patch('pygame.init'), \
             patch('pygame.get_init', return_value=True), \
             patch('pygame.display.set_mode') as mock_set_mode:
            
            # Mockスクリーンを設定
            mock_screen = MagicMock()
            mock_screen.get_width.return_value = 1024
            mock_screen.get_height.return_value = 768
            mock_set_mode.return_value = mock_screen
            
            # レンダラーを作成
            renderers = []
            for i in range(3):
                try:
                    renderer = DungeonRendererPygame(screen=mock_screen)
                    renderers.append(renderer)
                except Exception as e:
                    print(f"レンダラー初期化失敗: {e}")
                    continue
            
            # 弱参照を作成
            renderer_refs = [weakref.ref(renderer) for renderer in renderers]
            
            # クリーンアップ
            for renderer in renderers:
                if hasattr(renderer, 'cleanup'):
                    renderer.cleanup()
            
            renderers.clear()
            gc.collect()
            
            # 弱参照の確認
            alive_renderers = [ref() for ref in renderer_refs if ref() is not None]
            
            assert len(alive_renderers) == 0, f"Renderer メモリリーク: {len(alive_renderers)} 個が残存"
    
    def test_ui_manager_memory_cleanup(self):
        """UIマネージャーのメモリクリーンアップテスト"""
        with patch('pygame.init'), \
             patch('pygame.get_init', return_value=True), \
             patch('pygame.display.set_mode') as mock_set_mode, \
             patch('pygame.display.Info') as mock_info:
            
            # Mockスクリーンを設定
            mock_screen = MagicMock()
            mock_screen.get_width.return_value = 1024
            mock_screen.get_height.return_value = 768
            mock_set_mode.return_value = mock_screen
            mock_info.return_value = MagicMock()
            
            # UIマネージャーを作成
            ui_managers = []
            for i in range(3):
                try:
                    ui_manager = DungeonUIManagerPygame(screen=mock_screen)
                    ui_managers.append(ui_manager)
                except Exception as e:
                    print(f"UIマネージャー初期化失敗: {e}")
                    continue
            
            # 弱参照を作成
            ui_refs = [weakref.ref(ui_manager) for ui_manager in ui_managers]
            
            # クリーンアップ
            for ui_manager in ui_managers:
                if hasattr(ui_manager, 'cleanup'):
                    ui_manager.cleanup()
            
            ui_managers.clear()
            gc.collect()
            
            # 弱参照の確認
            alive_ui_managers = [ref() for ref in ui_refs if ref() is not None]
            
            assert len(alive_ui_managers) == 0, f"UI Manager メモリリーク: {len(alive_ui_managers)} 個が残存"
    
    def test_dungeon_manager_memory_cleanup(self):
        """DungeonManagerのメモリクリーンアップテスト"""
        # DungeonManagerを作成
        managers = []
        for i in range(3):
            try:
                manager = DungeonManager()
                managers.append(manager)
            except Exception as e:
                print(f"DungeonManager初期化失敗: {e}")
                continue
        
        # 弱参照を作成
        manager_refs = [weakref.ref(manager) for manager in managers]
        
        # クリーンアップ
        for manager in managers:
            if hasattr(manager, 'cleanup'):
                manager.cleanup()
        
        managers.clear()
        gc.collect()
        
        # 弱参照の確認
        alive_managers = [ref() for ref in manager_refs if ref() is not None]
        
        assert len(alive_managers) == 0, f"Dungeon Manager メモリリーク: {len(alive_managers)} 個が残存"
    
    def test_combat_encounter_manager_memory_cleanup(self):
        """CombatManager・EncounterManagerのメモリクリーンアップテスト"""
        # CombatManagerを作成
        combat_managers = []
        for i in range(3):
            try:
                manager = CombatManager()
                combat_managers.append(manager)
            except Exception as e:
                print(f"CombatManager初期化失敗: {e}")
                continue
        
        # EncounterManagerを作成
        encounter_managers = []
        for i in range(3):
            try:
                manager = EncounterManager()
                encounter_managers.append(manager)
            except Exception as e:
                print(f"EncounterManager初期化失敗: {e}")
                continue
        
        # 弱参照を作成
        combat_refs = [weakref.ref(manager) for manager in combat_managers]
        encounter_refs = [weakref.ref(manager) for manager in encounter_managers]
        
        # クリーンアップ
        for manager in combat_managers:
            if hasattr(manager, 'cleanup'):
                manager.cleanup()
        
        for manager in encounter_managers:
            if hasattr(manager, 'cleanup'):
                manager.cleanup()
        
        combat_managers.clear()
        encounter_managers.clear()
        gc.collect()
        
        # 弱参照の確認
        alive_combat = [ref() for ref in combat_refs if ref() is not None]
        alive_encounter = [ref() for ref in encounter_refs if ref() is not None]
        
        assert len(alive_combat) == 0, f"Combat Manager メモリリーク: {len(alive_combat)} 個が残存"
        assert len(alive_encounter) == 0, f"Encounter Manager メモリリーク: {len(alive_encounter)} 個が残存"
    
    def test_memory_usage_under_load(self):
        """負荷時のメモリ使用量テスト"""
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # 大量のオブジェクトを作成・破棄
        for cycle in range(3):
            # 一時的なオブジェクト群を作成
            temp_objects = []
            
            for i in range(50):
                character = Character(f"temp_char_{cycle}_{i}", "human", "fighter")
                party = Party(f"temp_party_{cycle}_{i}")
                party.add_character(character)
                temp_objects.append((character, party))
            
            # 処理を実行
            for character, party in temp_objects:
                party.get_living_characters()
                if hasattr(character, 'get_status'):
                    character.get_status()
            
            # オブジェクトを削除
            temp_objects.clear()
            
            # 定期的にガベージコレクション
            gc.collect()
            
            # メモリ使用量をチェック
            current_memory = process.memory_info().rss
            memory_increase = current_memory - initial_memory
            
            # 10MB以上の増加は問題の可能性
            if memory_increase > 10 * 1024 * 1024:
                print(f"警告: サイクル {cycle} でメモリ使用量が {memory_increase / 1024 / 1024:.2f}MB 増加")
        
        # 最終的なメモリ使用量チェック
        final_memory = process.memory_info().rss
        total_increase = final_memory - initial_memory
        
        # 5MB以上の増加は警告
        if total_increase > 5 * 1024 * 1024:
            print(f"警告: 負荷テスト後のメモリ増加: {total_increase / 1024 / 1024:.2f}MB")
        
        # 極端なメモリ増加は失敗
        assert total_increase < 20 * 1024 * 1024, f"メモリ使用量異常: {total_increase / 1024 / 1024:.2f}MB 増加"
    
    def test_pygame_resource_cleanup(self):
        """Pygame リソースのクリーンアップテスト"""
        with patch('pygame.init'), \
             patch('pygame.get_init', return_value=True), \
             patch('pygame.display.set_mode') as mock_set_mode, \
             patch('pygame.font.Font') as mock_font, \
             patch('pygame.Surface') as mock_surface:
            
            # Mockオブジェクトを設定
            mock_screen = MagicMock()
            mock_screen.get_width.return_value = 1024
            mock_screen.get_height.return_value = 768
            mock_set_mode.return_value = mock_screen
            
            # 複数のPygameリソースを作成
            pygame_objects = []
            for i in range(10):
                try:
                    # DungeonRendererを作成
                    renderer = DungeonRendererPygame(screen=mock_screen)
                    pygame_objects.append(renderer)
                    
                    # UIマネージャーを作成
                    ui_manager = DungeonUIManagerPygame(screen=mock_screen)
                    pygame_objects.append(ui_manager)
                except Exception as e:
                    print(f"Pygameオブジェクト初期化失敗: {e}")
                    continue
            
            # 弱参照を作成
            pygame_refs = [weakref.ref(obj) for obj in pygame_objects]
            
            # クリーンアップ
            for obj in pygame_objects:
                if hasattr(obj, 'cleanup'):
                    obj.cleanup()
            
            pygame_objects.clear()
            gc.collect()
            
            # 弱参照の確認
            alive_pygame_objects = [ref() for ref in pygame_refs if ref() is not None]
            
            assert len(alive_pygame_objects) == 0, f"Pygame オブジェクト メモリリーク: {len(alive_pygame_objects)} 個が残存"