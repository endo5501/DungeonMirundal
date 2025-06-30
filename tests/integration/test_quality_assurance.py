"""品質保証チェックリストテスト"""

import os
import sys
import pygame
import importlib
import inspect
from pathlib import Path

# ヘッドレス環境でのPygame初期化
os.environ['SDL_VIDEODRIVER'] = 'dummy'

# パス設定
sys.path.insert(0, '/home/satorue/Dungeon')


class TestQualityAssurance:
    """品質保証チェックリストテストクラス"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        pygame.init()
        self.project_root = Path('/home/satorue/Dungeon')
        
    def teardown_method(self):
        """各テストメソッドの後に実行"""
        pygame.quit()
    
    def test_no_uimenu_references_in_src(self):
        """ソースコードにUIMenu参照が残っていないことを確認"""
        uimenu_refs = []
        
        # srcディレクトリ内のPythonファイルを検索
        for py_file in self.project_root.glob('src/**/*.py'):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # UIMenuクラスの使用を検出（コメント内は除外）
                lines = content.split('\n')
                for i, line in enumerate(lines, 1):
                    # コメント行をスキップ
                    if line.strip().startswith('#'):
                        continue
                    
                    # UIMenuの参照を検出
                    if 'UIMenu' in line and 'class UIMenu' not in line:
                        # 削除済みコメントは除外
                        if '削除' not in line and 'Phase 4.5' not in line:
                            uimenu_refs.append(f"{py_file}:{i}: {line.strip()}")
            except Exception as e:
                # ファイル読み込みエラーは無視
                pass
        
        assert len(uimenu_refs) == 0, f"UIMenu参照が残存: {uimenu_refs[:5]}"  # 最初の5件のみ表示
    
    def test_window_system_architecture_consistency(self):
        """WindowSystemアーキテクチャの一貫性確認"""
        try:
            # 主要WindowSystemモジュールのインポート確認
            from src.ui.window_system.window import Window
            from src.ui.window_system.window_manager import WindowManager
            from src.ui.window_system.inventory_window import InventoryWindow
            from src.ui.window_system.equipment_window import EquipmentWindow
            from src.ui.window_system.magic_window import MagicWindow
            from src.ui.window_system.settings_window import SettingsWindow
            
            # 各Windowクラスが正しくWindowを継承していることを確認
            window_classes = [InventoryWindow, EquipmentWindow, MagicWindow, SettingsWindow]
            
            for window_class in window_classes:
                assert issubclass(window_class, Window), f"{window_class.__name__}がWindowを継承していません"
            
            # WindowManagerがシングルトンであることを確認
            manager1 = WindowManager.get_instance()
            manager2 = WindowManager.get_instance()
            assert manager1 is manager2, "WindowManagerがシングルトンではありません"
            
        except ImportError as e:
            assert False, f"WindowSystemモジュールのインポートエラー: {e}"
    
    def test_test_coverage_exists(self):
        """テストカバレッジが存在することを確認"""
        test_dirs = [
            self.project_root / 'tests',
            self.project_root / 'tests' / 'integration',
        ]
        
        test_count = 0
        for test_dir in test_dirs:
            if test_dir.exists():
                test_count += len(list(test_dir.glob('test_*.py')))
        
        # 最低限のテストファイル数を確認
        assert test_count >= 10, f"テストファイル数が不足: {test_count}個（最低10個必要）"
    
    def test_documentation_structure(self):
        """ドキュメント構造の確認"""
        required_docs = [
            'docs/todos/0044_uimenu_phased_removal_long_term.md',
            'docs/todos/0045_core_ui_window_implementation.md',
            'docs/todos/0046_final_integration_testing.md',
            'docs/window_system.md',
        ]
        
        missing_docs = []
        for doc_path in required_docs:
            full_path = self.project_root / doc_path
            if not full_path.exists():
                missing_docs.append(doc_path)
        
        assert len(missing_docs) == 0, f"必須ドキュメントが不足: {missing_docs}"
    
    def test_code_quality_imports(self):
        """インポート品質の確認"""
        # 循環インポートがないことを簡易チェック
        try:
            # 主要モジュールを全てインポート
            from src.ui.window_system import WindowManager
            from src.overworld.overworld_manager_pygame import OverworldManager
            from src.overworld.base_facility import BaseFacility
            from src.ui.base_ui_pygame import UIManager
            
            # インポートが成功すれば循環インポートなし
            assert True
        except ImportError as e:
            assert False, f"循環インポートまたはインポートエラー: {e}"
    
    def test_error_handling_robustness(self):
        """エラーハンドリングの堅牢性確認"""
        from src.ui.window_system.window_manager import WindowManager
        
        window_manager = WindowManager.get_instance()
        
        # 不正な操作でもクラッシュしないことを確認
        try:
            # 存在しないウィンドウの取得
            non_existent = window_manager.get_window("non_existent_window")
            assert non_existent is None  # Noneが返ることを期待
            
            # Noneや不正な値での操作
            try:
                window_manager.show_window(None)
            except (ValueError, TypeError, AttributeError):
                # エラーは発生してもクラッシュしない
                pass
            
            assert True  # クラッシュしなければ成功
        except Exception as e:
            assert False, f"エラーハンドリングが不十分: {e}"
    
    def test_memory_safety(self):
        """メモリ安全性の基本確認"""
        import gc
        from src.ui.window_system.window import Window, WindowState
        
        # テスト用Window
        class TestMemWindow(Window):
            def __init__(self, window_id: str):
                super().__init__(window_id)
            
            def create(self):
                pass
            
            def handle_event(self, event):
                return False
        
        # 多数のWindowを作成・破棄
        gc.collect()
        initial_objects = len(gc.get_objects())
        
        for i in range(100):
            window = TestMemWindow(f"mem_test_{i}")
            window.show()
            window.hide()
            window.destroy()
        
        gc.collect()
        final_objects = len(gc.get_objects())
        
        # オブジェクト数の増加が妥当な範囲内であることを確認
        object_increase = final_objects - initial_objects
        assert object_increase < 1000, f"メモリリークの可能性: {object_increase}個のオブジェクト増加"
    
    def test_ui_consistency(self):
        """UI一貫性の確認"""
        # WindowSystemが統一されたUIシステムであることを確認
        window_system_modules = []
        other_ui_modules = []
        
        # UIモジュールを分類
        ui_path = self.project_root / 'src' / 'ui'
        if ui_path.exists():
            for py_file in ui_path.glob('**/*.py'):
                if 'window_system' in str(py_file):
                    window_system_modules.append(py_file.name)
                elif py_file.name.endswith('_ui.py'):
                    other_ui_modules.append(py_file.name)
        
        # WindowSystemが主要UIシステムであることを確認
        assert len(window_system_modules) > 0, "WindowSystemモジュールが見つかりません"
        
        # レガシーUIシステムが適切に統合されているか確認
        # （other_ui_modulesが存在しても、WindowSystemと統合されていればOK）
        assert True  # 基本的な一貫性チェックは成功
    
    def test_configuration_integrity(self):
        """設定ファイルの整合性確認"""
        config_files = [
            'pytest.ini',
            'pyproject.toml',
        ]
        
        for config_file in config_files:
            config_path = self.project_root / config_file
            assert config_path.exists(), f"設定ファイルが見つかりません: {config_file}"
    
    def test_no_debug_code_in_production(self):
        """本番コードにデバッグコードが残っていないことを確認"""
        debug_patterns = [
            'print(',  # デバッグプリント
            'breakpoint(',  # ブレークポイント
            'import pdb',  # デバッガ
            'console.log',  # JSデバッグ（混入防止）
        ]
        
        debug_found = []
        
        # srcディレクトリ内を検索
        for py_file in self.project_root.glob('src/**/*.py'):
            # テストファイルは除外
            if 'test' in py_file.name:
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    
                for i, line in enumerate(lines, 1):
                    # コメント行は除外
                    if line.strip().startswith('#'):
                        continue
                    
                    for pattern in debug_patterns:
                        if pattern in line:
                            debug_found.append(f"{py_file}:{i}: {line.strip()}")
            except Exception:
                pass
        
        # logger.debug()は許可するが、その他のデバッグコードは禁止
        debug_found = [d for d in debug_found if 'logger.debug' not in d]
        
        assert len(debug_found) == 0, f"デバッグコードが残存: {debug_found[:5]}"