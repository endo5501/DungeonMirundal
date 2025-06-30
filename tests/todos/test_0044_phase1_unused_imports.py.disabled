"""0044 Phase 1: 未使用UIMenuインポートの除去テスト"""

import pytest
import ast
from pathlib import Path
from typing import List, Tuple


class TestUnusedUIMenuImports:
    """未使用のUIMenuインポート除去確認テスト"""
    
    def setup_method(self):
        """テストのセットアップ"""
        self.src_dir = Path(__file__).parent.parent.parent / "src"  # src/ディレクトリ
        self.exclude_dirs = {'__pycache__', '.pytest_cache'}
    
    def find_uimenu_imports(self, file_path: Path) -> List[Tuple[int, str]]:
        """ファイル内のUIMenuインポートを検出"""
        imports = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # ASTを使用してインポート文を解析
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    if node.module and 'base_ui_pygame' in node.module:
                        for alias in node.names:
                            if alias.name == 'UIMenu':
                                imports.append((node.lineno, f"from {node.module} import UIMenu"))
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        if 'UIMenu' in alias.name:
                            imports.append((node.lineno, f"import {alias.name}"))
        except Exception as e:
            # パースエラーは無視（不完全なファイルの可能性）
            pass
            
        return imports
    
    def check_uimenu_usage(self, file_path: Path, content: str) -> bool:
        """ファイル内でUIMenuが実際に使用されているかチェック"""
        # インポート文を除外したコンテンツを取得
        lines = content.split('\n')
        non_import_lines = []
        
        for line in lines:
            if not (line.strip().startswith('from ') or line.strip().startswith('import ')):
                non_import_lines.append(line)
        
        non_import_content = '\n'.join(non_import_lines)
        
        # UIMenuの使用をチェック（コメント内は除外）
        for line in non_import_lines:
            # コメントを除去
            if '#' in line:
                line = line[:line.index('#')]
            
            # UIMenuが使用されているかチェック
            if 'UIMenu' in line and line.strip():
                return True
                
        return False
    
    def test_no_unused_uimenu_imports_in_src(self):
        """srcディレクトリ内に未使用のUIMenuインポートがないことを確認"""
        unused_imports = []
        
        # すべてのPythonファイルを検索
        for py_file in self.src_dir.rglob("*.py"):
            # 除外ディレクトリをスキップ
            if any(exclude in py_file.parts for exclude in self.exclude_dirs):
                continue
            
            # UIMenuの定義ファイルはスキップ
            if py_file.name == 'base_ui_pygame.py':
                continue
                
            # UIMenuインポートを検出
            imports = self.find_uimenu_imports(py_file)
            
            if imports:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # UIMenuが実際に使用されているかチェック
                if not self.check_uimenu_usage(py_file, content):
                    for line_no, import_stmt in imports:
                        unused_imports.append(
                            f"{py_file.relative_to(self.src_dir)}:{line_no} - {import_stmt}"
                        )
        
        assert len(unused_imports) == 0, \
            f"Following files have unused UIMenu imports:\n" + "\n".join(unused_imports)
    
    def test_no_ui_manager_imports_without_usage(self):
        """ui_managerが使用されていない場合、インポートされていないことを確認"""
        unused_ui_manager = []
        
        for py_file in self.src_dir.rglob("*.py"):
            # 除外ディレクトリをスキップ
            if any(exclude in py_file.parts for exclude in self.exclude_dirs):
                continue
                
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # ui_managerのインポートをチェック
            if 'from src.ui.base_ui_pygame import' in content and 'ui_manager' in content:
                # ui_managerが実際に使用されているかチェック
                lines = content.split('\n')
                ui_manager_used = False
                
                for line in lines:
                    # インポート文はスキップ
                    if line.strip().startswith('from ') or line.strip().startswith('import '):
                        continue
                    
                    # コメントを除去
                    if '#' in line:
                        line = line[:line.index('#')]
                    
                    if 'ui_manager' in line and line.strip():
                        ui_manager_used = True
                        break
                
                if not ui_manager_used:
                    unused_ui_manager.append(str(py_file.relative_to(self.src_dir)))
        
        assert len(unused_ui_manager) == 0, \
            f"Following files import ui_manager but don't use it:\n" + "\n".join(unused_ui_manager)
    
    def test_facility_files_clean(self):
        """施設ファイルがクリーンであることを確認"""
        facility_dir = self.src_dir / "overworld" / "facilities"
        
        if facility_dir.exists():
            for py_file in facility_dir.glob("*.py"):
                if py_file.name == "__init__.py":
                    continue
                    
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # コメント内のUIMenu参照が適切に削除されているか確認
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if '#' in line and 'UIMenu' in line:
                        # 移行に関する説明的なコメントは許可
                        if not any(keyword in line for keyword in 
                                 ['WindowManager', 'Window', '移行', 'migration']):
                            assert False, \
                                f"{py_file.name}:{i+1} has UIMenu reference in comment"