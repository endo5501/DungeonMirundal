"""Test character status bar fix for visibility issue"""

import pytest
from unittest.mock import Mock, MagicMock, patch


def test_character_status_bar_added_to_ui_manager():
    """Test that character status bar is properly added to UI manager elements"""
    
    # Mock dependencies
    mock_screen = MagicMock()
    mock_screen.get_width.return_value = 1024
    mock_screen.get_height.return_value = 768
    
    # Patch pygame_gui to avoid initialization issues
    with patch('pygame_gui.UIManager'):
        # Import after patching
        from src.ui.base_ui_pygame import UIManager
        from src.ui.character_status_bar import CharacterStatusBar
        
        # Create UI manager
        ui_manager = UIManager(mock_screen)
        ui_manager.pygame_gui_manager = MagicMock()
        ui_manager.elements = {}  # Ensure elements dict exists
        
        # Create character status bar
        status_bar = CharacterStatusBar()
        status_bar.element_id = "character_status_bar"
        
        # Add to UI manager
        ui_manager.add_element(status_bar)
        
        # Verify it was added
        assert status_bar.element_id in ui_manager.elements
        assert ui_manager.elements[status_bar.element_id] == status_bar


def test_overworld_manager_initializes_status_bar():
    """Test that OverworldManager properly initializes and adds character status bar"""
    
    # Mock dependencies
    mock_screen = MagicMock()
    mock_screen.get_width.return_value = 1024
    mock_screen.get_height.return_value = 768
    
    with patch('pygame_gui.UIManager'), \
         patch('src.ui.font_manager_pygame.font_manager'), \
         patch('src.overworld.base_facility.facility_manager'), \
         patch('src.ui.menu_stack_manager.MenuStackManager'):
        
        # Import after patching
        from src.overworld.overworld_manager_pygame import OverworldManager
        from src.ui.base_ui_pygame import UIManager
        
        # Create UI manager
        ui_manager = UIManager(mock_screen)
        ui_manager.pygame_gui_manager = MagicMock()
        ui_manager.elements = {}
        ui_manager.add_element = Mock()
        
        # Create overworld manager
        overworld_manager = OverworldManager()
        
        # Mock the character status bar creation
        with patch('src.overworld.overworld_manager_pygame.create_character_status_bar') as mock_create:
            mock_status_bar = MagicMock()
            mock_status_bar.element_id = "character_status_bar"
            mock_create.return_value = mock_status_bar
            
            # Set UI manager (this triggers character status bar initialization)
            overworld_manager.set_ui_manager(ui_manager)
            
            # Verify character status bar was created
            mock_create.assert_called_once_with(1024, 768)
            
            # Verify it was added to UI manager
            ui_manager.add_element.assert_called_once_with(mock_status_bar)
            
            # Verify it's stored in overworld manager
            assert overworld_manager.character_status_bar == mock_status_bar


def test_render_order():
    """Test that character status bar is rendered by UI manager, not directly"""
    
    mock_screen = MagicMock()
    
    with patch('pygame_gui.UIManager'), \
         patch('src.ui.font_manager_pygame.font_manager'):
        
        from src.ui.base_ui_pygame import UIManager
        from src.ui.character_status_bar import CharacterStatusBar
        
        # Create UI manager
        ui_manager = UIManager(mock_screen)
        ui_manager.pygame_gui_manager = MagicMock()
        
        # Create mock character status bar
        mock_status_bar = MagicMock(spec=CharacterStatusBar)
        mock_status_bar.element_id = "character_status_bar"
        ui_manager.elements = {"character_status_bar": mock_status_bar}
        
        # Call render
        ui_manager.render()
        
        # Verify status bar was rendered
        mock_status_bar.render.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])