# tests/test_checkout_self_healing.py
import sys
import os
import pytest
from playwright.sync_api import Page
from utils.actions import perform_action
# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from healing_strategy import find_locator_with_healing

def test_self_healing_login(page: Page):
    """Test self-healing for login button with primary/semantic/visual fallback"""
    # Navigate
    page.goto("http://localhost:5000/")
    page.wait_for_load_state("networkidle")  # or time.sleep(2) if needed
    # Run healing
    healing_result = find_locator_with_healing(page, 'button:has-text("Login")')

    if healing_result:
        # Perform the action (click in this case)
        success = perform_action(page, healing_result, "click")
        assert success, "Interaction failed after healing"
        print("SUCCESS: Element interacted successfully")
    else:
        pytest.fail("No element found even after all healing attempts")
    page.wait_for_timeout(5000)