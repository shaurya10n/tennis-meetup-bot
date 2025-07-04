#!/usr/bin/env python3
"""
Test to verify the find_match command structure without Discord dependencies.
"""

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_command_structure():
    """Test that the find_match command files exist and have the right structure."""
    
    # Test file existence
    files_to_check = [
        'src/cogs/user/commands/find_match/__init__.py',
        'src/cogs/user/commands/find_match/command.py',
        'src/cogs/user/commands/find_match/constants.py',
        'src/cogs/user/commands/find_match/views.py'
    ]
    
    print("Testing find_match command structure...")
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            print(f"✅ {file_path} exists")
        else:
            print(f"❌ {file_path} missing")
            return False
    
    # Test basic file content (without importing Discord modules)
    try:
        with open('src/cogs/user/commands/find_match/command.py', 'r') as f:
            content = f.read()
            if 'class FindMatchesCommand' in content:
                print("✅ FindMatchesCommand class found in command.py")
            else:
                print("❌ FindMatchesCommand class not found in command.py")
                return False
    except Exception as e:
        print(f"❌ Error reading command.py: {e}")
        return False
    
    try:
        with open('src/cogs/user/commands/find_match/views.py', 'r') as f:
            content = f.read()
            if 'class MatchSuggestionView' in content:
                print("✅ MatchSuggestionView class found in views.py")
            else:
                print("❌ MatchSuggestionView class not found in views.py")
                return False
    except Exception as e:
        print(f"❌ Error reading views.py: {e}")
        return False
    
    try:
        with open('src/cogs/user/commands/find_match/constants.py', 'r') as f:
            content = f.read()
            if 'FIND_MATCHES_DESC' in content:
                print("✅ FIND_MATCHES_DESC constant found in constants.py")
            else:
                print("❌ FIND_MATCHES_DESC constant not found in constants.py")
                return False
    except Exception as e:
        print(f"❌ Error reading constants.py: {e}")
        return False
    
    print("\n🎉 All command structure tests passed!")
    return True

if __name__ == "__main__":
    success = test_command_structure()
    sys.exit(0 if success else 1) 