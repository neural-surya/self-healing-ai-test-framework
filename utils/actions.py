from playwright.sync_api import Page, Locator, TimeoutError as PlaywrightTimeoutError


def perform_action(page: Page, result: dict | None, action: str, *args, **kwargs) -> bool:
    """
    Generic method to perform an action based on the healing result.

    Args:
        page: The Playwright Page object
        result: Output from find_locator_with_healing()  (None if failed)
        action: String name of the action, e.g. "click", "type", "fill", "press", "hover", ...
        *args, **kwargs: Arguments specific to the action (e.g. text for type/fill)

    Returns:
        bool: True if action succeeded, False otherwise

    Examples:
        perform_action(page, result, "click")                              # simple click
        perform_action(page, result, "type", "myusername")                 # type text
        perform_action(page, result, "fill", "password123")                # fill input
        perform_action(page, result, "press", "Enter")                     # press key
    """
    if not result:
        print("No valid locator or coordinates found → cannot perform action")
        return False

    result_type = result.get('type')

    try:
        if result_type == 'locator':
            locator: Locator = result['value']

            # Wait for element to be actionable
            locator.wait_for(state="visible", timeout=8000)

            # Common actions
            if action == "click":
                locator.click(**kwargs)
            elif action in ("type", "fill"):
                if not args:
                    raise ValueError(f"Action '{action}' requires text argument")
                text = str(args[0])
                if action == "type":
                    locator.type(text, **kwargs)
                else:
                    locator.fill(text, **kwargs)
            elif action == "press":
                if not args:
                    raise ValueError("Action 'press' requires key argument")
                locator.press(args[0], **kwargs)
            elif action == "hover":
                locator.hover(**kwargs)
            elif action == "focus":
                locator.focus(**kwargs)
            elif action == "blur":
                locator.blur(**kwargs)
            elif action == "clear":
                locator.clear(**kwargs)
            else:
                # Fallback: call any locator method dynamically
                method = getattr(locator, action, None)
                if method and callable(method):
                    method(*args, **kwargs)
                else:
                    raise ValueError(f"Unsupported action '{action}' for locator")

            print(f"→ Action '{action}' succeeded on locator")
            return True

        elif result_type == 'coord':
            x = result.get('x')
            y = result.get('y')  # wait, typo in your example → should be 'y'
            if x is None or y is None:
                print("Coordinates missing in result → cannot perform coordinate action")
                return False

            # Common coordinate-based actions using mouse
            if action == "click":
                page.mouse.click(x, y, **kwargs)
            elif action == "dblclick":
                page.mouse.dblclick(x, y, **kwargs)
            elif action == "hover":
                page.mouse.move(x, y)
                # no real hover on mouse, but move is closest
            elif action == "down":
                page.mouse.down(x, y)
            elif action == "up":
                page.mouse.up(x, y)
            else:
                raise ValueError(
                    f"Action '{action}' not supported for coordinates (only click, dblclick, hover, down, up)")

            print(f"→ Action '{action}' succeeded at coordinates ({x}, {y})")
            return True

        else:
            print(f"Unknown result type: {result_type}")
            return False

    except PlaywrightTimeoutError:
        print(f"Action '{action}' failed: element/position not ready (timeout)")
        return False
    except Exception as e:
        print(f"Action '{action}' failed: {str(e)}")
        return False


def click_element_or_coordinates(page: Page, result: dict | None) -> bool:
    """
    Convenience method: Click using locator or coordinates from healing result.

    Returns True if click succeeded.
    """
    if not result:
        print("No result → cannot click")
        return False

    if result['type'] == 'locator':
        try:
            result['value'].click(timeout=8000)
            print("→ Clicked using locator")
            return True
        except Exception as e:
            print(f"Locator click failed: {e}")
            return False

    elif result['type'] == 'coord':
        x = result.get('x')
        y = result.get('y')
        if x is None or y is None:
            print("Missing x/y coordinates")
            return False
        try:
            page.mouse.click(x, y)
            print(f"→ Clicked at coordinates ({x}, {y})")
            return True
        except Exception as e:
            print(f"Coordinate click failed: {e}")
            return False

    else:
        print(f"Unsupported result type for click: {result.get('type')}")
        return False
