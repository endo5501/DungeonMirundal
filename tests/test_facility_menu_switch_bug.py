"""
Test for facility menu switching bug (Issue #0057)

This test reproduces the bug where:
[inn] -> [exit] -> [guild] displays inn menu instead of guild menu
"""

import pytest
from unittest.mock import Mock, patch
from src.overworld.base_facility import facility_manager
from src.overworld.facilities.inn import Inn
from src.overworld.facilities.guild import AdventurersGuild
from src.ui.window_system.window_manager import WindowManager


class TestFacilityMenuSwitchBug:
    """Test facility menu switching to ensure different menus are displayed correctly"""
    
    def setup_method(self):
        """Setup test environment"""
        self.mock_window_manager = Mock(spec=WindowManager)
        self.mock_window_manager.create_window = Mock()
        self.mock_window_manager.show_window = Mock()
        self.mock_window_manager.get_window = Mock(return_value=None)
        self.mock_window_manager.close_window = Mock()
        
        # Create mock party
        from src.character.party import Party
        self.mock_party = Mock(spec=Party)
        self.mock_party.characters = []
        
        # Create facility instances
        self.inn = Inn()
        self.guild = AdventurersGuild()
        
        # Mock window manager for facilities
        self.inn.window_manager = self.mock_window_manager
        self.guild.window_manager = self.mock_window_manager
    
    def test_inn_then_guild_shows_different_menus(self):
        """
        Test that switching from inn to guild shows different menu configurations
        
        Bug scenario:
        1. Enter inn -> shows inn menu
        2. Exit inn -> return to overworld  
        3. Enter guild -> should show guild menu, not inn menu
        """
        
        # Step 1: Enter inn
        self.inn.enter(self.mock_party)
        
        # Verify inn menu window was created
        create_calls = self.mock_window_manager.create_window.call_args_list
        assert len(create_calls) >= 1, "Inn window should be created when entering inn"
        
        # Get the inn window ID
        inn_window_id = create_calls[0][0][1]  # Second argument is window_id
        
        # Step 2: Exit inn (simulate window close)
        self.inn.exit()
        
        # Step 3: Enter guild  
        self.guild.enter(self.mock_party)
        
        # Verify guild menu window was created
        create_calls_after = self.mock_window_manager.create_window.call_args_list
        assert len(create_calls_after) >= 2, "Guild window should be created when entering guild"
        
        # Get the guild window ID
        guild_window_id = create_calls_after[1][0][1]  # Second argument is window_id
        
        # Verify different window IDs are used
        # This should prevent the same menu from being reused
        assert inn_window_id != guild_window_id, \
            f"Inn and guild should use different window IDs: inn='{inn_window_id}', guild='{guild_window_id}'"
    
    def test_facility_menu_configurations_are_different(self):
        """Test that inn and guild have different menu configurations"""
        
        # Get inn menu config
        inn_config = self.inn._create_inn_menu_config()
        
        # Get guild menu config  
        guild_config = self.guild._create_guild_menu_config()
        
        print(f"Inn config: {inn_config}")
        print(f"Guild config: {guild_config}")
        
        # Verify configs are different
        assert inn_config != guild_config, \
            "Inn and guild should have different menu configurations"
        
        # Verify specific menu items are different
        inn_buttons = inn_config.get('buttons', inn_config.get('menu_items', []))
        guild_buttons = guild_config.get('buttons', guild_config.get('menu_items', []))
        
        inn_button_texts = [btn.get('text', btn.get('label', '')) for btn in inn_buttons]
        guild_button_texts = [btn.get('text', btn.get('label', '')) for btn in guild_buttons]
        
        print(f"Inn button texts: {inn_button_texts}")
        print(f"Guild button texts: {guild_button_texts}")
        
        # Should have at least some different menu items
        assert inn_button_texts != guild_button_texts, \
            "Inn and guild should have different menu button texts"
    
    def test_window_manager_creates_unique_window_ids(self):
        """Test that each facility creates windows with unique IDs"""
        
        # Enter inn
        self.inn.enter(self.mock_party)
        
        # Enter guild (without explicitly exiting inn first)
        self.guild.enter(self.mock_party)
        
        # Check all window creation calls
        create_calls = self.mock_window_manager.create_window.call_args_list
        
        # Extract window IDs from calls
        window_ids = []
        for call in create_calls:
            # Window ID is the second positional argument
            if len(call[0]) >= 2:
                window_ids.append(call[0][1])
        
        # Verify unique window IDs
        unique_ids = set(window_ids)
        assert len(unique_ids) == len(window_ids), \
            f"All window IDs should be unique. Found: {window_ids}"
    
    def test_facility_exit_clears_window_state(self):
        """Test that exiting a facility properly clears its window state"""
        
        # Enter inn
        self.inn.enter(self.mock_party)
        
        # Verify inn window was created
        assert self.mock_window_manager.create_window.called, \
            "Window should be created when entering facility"
        
        # Exit inn
        self.inn.exit()
        
        # Verify window manager was called to lookup window for cleanup
        # This should at least call get_window to check if window exists
        assert self.mock_window_manager.get_window.called, \
            "Window cleanup should attempt to get window for cleanup"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])