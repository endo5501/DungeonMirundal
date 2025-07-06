#!/usr/bin/env python3
"""
ESC key behavior test in settings window
Tests the fix for ESC key handling in SettingsWindow
"""
import time
import json
from src.debug.game_debug_client import GameDebugClient

def test_esc_behavior():
    """Test ESC key behavior in settings window"""
    
    client = GameDebugClient()
    
    # Wait for API to be ready
    if not client.wait_for_api():
        print("❌ API not ready, cannot proceed with test")
        return False
    
    print("✅ API ready, starting test sequence...")
    
    # Step 1: Take screenshot of current main menu
    print("\n1. Taking screenshot of main menu...")
    if client.screenshot("step1_main_menu.jpg"):
        print("✅ Screenshot saved: step1_main_menu.jpg")
    else:
        print("❌ Failed to take initial screenshot")
        return False
    
    # Get initial UI hierarchy
    print("   Getting UI hierarchy...")
    hierarchy1 = client.get_ui_hierarchy()
    if hierarchy1:
        print(f"   Window stack: {hierarchy1.get('window_stack', [])}")
    
    # Step 2: Press ESC to open settings screen
    print("\n2. Pressing ESC to open settings screen...")
    client.send_key(27)  # ESC key code
    print("✅ ESC key sent")
    time.sleep(1)  # Wait for window transition
    
    # Step 3: Take screenshot of settings screen
    print("\n3. Taking screenshot of settings screen...")
    if client.screenshot("step3_settings_screen.jpg"):
        print("✅ Screenshot saved: step3_settings_screen.jpg")
    else:
        print("❌ Failed to take settings screenshot")
        return False
    
    # Get UI hierarchy after opening settings
    print("   Getting UI hierarchy after opening settings...")
    hierarchy2 = client.get_ui_hierarchy()
    if hierarchy2:
        print(f"   Window stack: {hierarchy2.get('window_stack', [])}")
    
    # Step 4: Press ESC again to test if settings screen closes
    print("\n4. Pressing ESC again to test if settings screen closes...")
    client.send_key(27)  # ESC key code
    print("✅ ESC key sent")
    time.sleep(1)  # Wait for window transition
    
    # Step 5: Take screenshot to confirm we're back at main menu
    print("\n5. Taking screenshot to confirm we're back at main menu...")
    if client.screenshot("step5_back_to_main.jpg"):
        print("✅ Screenshot saved: step5_back_to_main.jpg")
    else:
        print("❌ Failed to take final screenshot")
        return False
    
    # Get final UI hierarchy
    print("   Getting final UI hierarchy...")
    hierarchy3 = client.get_ui_hierarchy()
    if hierarchy3:
        print(f"   Window stack: {hierarchy3.get('window_stack', [])}")
    
    # Analysis
    print("\n" + "="*50)
    print("TEST RESULTS ANALYSIS")
    print("="*50)
    
    # Compare window stacks
    if hierarchy1 and hierarchy2 and hierarchy3:
        stack1 = hierarchy1.get('window_stack', [])
        stack2 = hierarchy2.get('window_stack', [])
        stack3 = hierarchy3.get('window_stack', [])
        
        print(f"\nWindow stack progression:")
        print(f"Initial:         {len(stack1)} windows - {stack1}")
        print(f"After ESC #1:    {len(stack2)} windows - {stack2}")
        print(f"After ESC #2:    {len(stack3)} windows - {stack3}")
        
        # Check if ESC properly opened settings
        if len(stack2) > len(stack1):
            print("✅ First ESC correctly opened settings window")
        else:
            print("❌ First ESC did not open settings window")
            return False
        
        # Check if second ESC properly closed settings
        if len(stack3) == len(stack1):
            print("✅ Second ESC correctly closed settings window")
            print("✅ ESC key fix is working properly!")
            return True
        else:
            print("❌ Second ESC did not properly close settings window")
            print("❌ ESC key fix needs further investigation")
            return False
    else:
        print("❌ Could not get UI hierarchy information for analysis")
        return False

if __name__ == "__main__":
    success = test_esc_behavior()
    if success:
        print("\n🎉 ESC key behavior test PASSED!")
    else:
        print("\n💥 ESC key behavior test FAILED!")