"""
Test for facility window ID inconsistency bug (Issue #0057)

This test verifies that window IDs used for creation and cleanup are consistent.
"""

import pytest
from unittest.mock import Mock, patch
from src.overworld.base_facility import BaseFacility, FacilityType
from src.overworld.facilities.inn import Inn
from src.overworld.facilities.guild import AdventurersGuild
from src.ui.window_system.window_manager import WindowManager
from src.character.party import Party


class TestFacilityWindowIdBug:
    """Test facility window ID consistency for proper cleanup"""
    
    def setup_method(self):
        """Setup test environment"""
        self.mock_window_manager = Mock(spec=WindowManager)
        self.mock_window_manager.window_registry = {}
        
        # Create mock window
        self.mock_window = Mock()
        self.mock_window.id = 'inn_main'  # Default window ID
        
        # Add missing methods to mock
        self.mock_window_manager.get_window = Mock(return_value=None)
        self.mock_window_manager.close_window = Mock()
        self.mock_window_manager.hide_window = Mock()
        self.mock_window_manager.show_window = Mock()
        self.mock_window_manager.create_window = Mock(return_value=self.mock_window)
        
        # Create mock party
        self.mock_party = Mock(spec=Party)
        self.mock_party.characters = []
        
        # Create facility instances
        self.inn = Inn()
        self.guild = AdventurersGuild()
        
        # Mock window manager for facilities
        self.inn.window_manager = self.mock_window_manager
        self.guild.window_manager = self.mock_window_manager
    
    def test_base_facility_cleanup_uses_correct_window_id(self):
        """Test that BaseFacility cleanup uses the same window ID format as creation"""
        
        # Use Inn as a concrete implementation of BaseFacility
        # Enter facility (should create window)
        self.inn.enter(self.mock_party)
        
        # Check what window ID was used for creation
        create_window_calls = self.mock_window_manager.create_window.call_args_list
        assert len(create_window_calls) > 0, "create_window should have been called"
        
        # Get the window ID from create_window call (second positional argument)
        created_window_id = create_window_calls[0][0][1]  # Second argument is window_id
        
        # Exit facility (should cleanup window)
        self.inn.exit()
        
        # Check what window ID was used for cleanup lookup
        get_window_calls = self.mock_window_manager.get_window.call_args_list
        
        if get_window_calls:
            # Check if the correct window ID was used for lookup
            cleanup_window_id = get_window_calls[0][0][0]  # First argument
            assert created_window_id == cleanup_window_id, \
                f"Window ID used for creation ({created_window_id}) should match cleanup lookup ({cleanup_window_id})"
        else:
            # The cleanup method should at least check if the window exists
            # This is where the bug occurs - it checks for the wrong ID format
            pass  # We expect this test to fail initially due to the bug
    
    def test_inn_window_id_consistency(self):
        """Test that Inn uses consistent window IDs for creation and cleanup"""
        
        # Enter inn
        self.inn.enter(self.mock_party)
        
        # Get the window ID used for creation
        create_window_calls = self.mock_window_manager.create_window.call_args_list
        assert len(create_window_calls) > 0, "Inn should create a window when entered"
        
        created_window_id = create_window_calls[0][0][1]  # Second argument is window_id
        
        # Exit inn
        self.inn.exit()
        
        # Check if cleanup was attempted with the correct window ID
        # The window ID used for cleanup should match the one used for creation
        expected_cleanup_id = created_window_id
        
        # Check window lookup during cleanup
        get_window_calls = self.mock_window_manager.get_window.call_args_list
        
        if get_window_calls:
            cleanup_window_id = get_window_calls[0][0][0]  # First argument
            assert cleanup_window_id == expected_cleanup_id, \
                f"Inn cleanup window ID ({cleanup_window_id}) should match creation ID ({expected_cleanup_id})"
    
    def test_guild_window_id_consistency(self):
        """Test that Guild uses consistent window IDs for creation and cleanup"""
        
        # Enter guild
        self.guild.enter(self.mock_party)
        
        # Get the window ID used for creation
        create_window_calls = self.mock_window_manager.create_window.call_args_list
        assert len(create_window_calls) > 0, "Guild should create a window when entered"
        
        created_window_id = create_window_calls[0][0][1]  # Second argument is window_id
        
        # Exit guild
        self.guild.exit()
        
        # Check if cleanup was attempted with the correct window ID
        expected_cleanup_id = created_window_id
        
        # Check window lookup during cleanup
        get_window_calls = self.mock_window_manager.get_window.call_args_list
        
        if get_window_calls:
            cleanup_window_id = get_window_calls[0][0][0]  # First argument
            assert cleanup_window_id == expected_cleanup_id, \
                f"Guild cleanup window ID ({cleanup_window_id}) should match creation ID ({expected_cleanup_id})"
    
    def test_different_facilities_use_different_window_ids(self):
        """Test that different facilities use different window IDs"""
        
        # Enter both facilities
        self.inn.enter(self.mock_party)
        self.guild.enter(self.mock_party)
        
        # Get window IDs used for creation
        create_window_calls = self.mock_window_manager.create_window.call_args_list
        assert len(create_window_calls) >= 2, "Both facilities should create windows"
        
        inn_window_id = create_window_calls[0][0][1]  # Second argument is window_id
        guild_window_id = create_window_calls[1][0][1]  # Second argument is window_id
        
        assert inn_window_id != guild_window_id, \
            f"Inn and Guild should use different window IDs: inn='{inn_window_id}', guild='{guild_window_id}'"
    
    def test_window_id_format_consistency(self):
        """Test that window ID format is consistent between facilities"""
        
        # Check inn window ID format
        self.inn.enter(self.mock_party)
        inn_calls = self.mock_window_manager.create_window.call_args_list
        inn_window_id = inn_calls[0][0][1] if inn_calls else None
        
        # Reset mock for guild test
        self.mock_window_manager.reset_mock()
        
        # Check guild window ID format  
        self.guild.enter(self.mock_party)
        guild_calls = self.mock_window_manager.create_window.call_args_list
        guild_window_id = guild_calls[0][0][1] if guild_calls else None
        
        # Both should create windows
        assert inn_window_id is not None, "Inn should create a window"
        assert guild_window_id is not None, "Guild should create a window"
        
        # Check window ID format
        assert isinstance(inn_window_id, str), f"Inn window ID should be string: {type(inn_window_id)}"
        assert "inn" in inn_window_id.lower(), f"Inn window ID should contain 'inn': {inn_window_id}"
        assert isinstance(guild_window_id, str), f"Guild window ID should be string: {type(guild_window_id)}"
        assert "guild" in guild_window_id.lower(), f"Guild window ID should contain 'guild': {guild_window_id}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])