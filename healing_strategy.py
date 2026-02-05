# healing_strategy.py
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError
from config import ELEMENT_MAPPING, REGION_SELECTORS
from utils.semantic_healing import try_semantic_fallback
from utils.visual_healing import try_visual_fallback, get_or_capture_template
from utils.groq_lpu_healing import try_lpu_healing

def find_locator_with_healing(page: Page, primary_selector: str) -> dict | None:
    """
    Multi-tier healing strategy:
    1. Primary locator
    2. Semantic fallback
    3. Visual fallback (multi-scale + NMS)
    """
    if primary_selector not in ELEMENT_MAPPING:
        raise ValueError(f"No mapping defined for selector: {primary_selector}")

    semantic_desc, template_path = ELEMENT_MAPPING[primary_selector]
    region_selector = REGION_SELECTORS.get(primary_selector)

    print(f"Attempting primary locator: {primary_selector}")

    try:
        locator = page.locator(primary_selector)
        get_or_capture_template(page, primary_selector, template_path)
        locator.wait_for(state="visible", timeout=5000)
        print("→ Success with primary locator!")
        return {'type': 'locator', 'value': locator}
    except PlaywrightTimeoutError:
        print("→ Primary failed → semantics fallback...")

    # # LPU Locator
    # lpu_locator = try_lpu_healing(page, semantic_desc)
    # if lpu_locator:
    #     try:
    #         print("→ Success with semantic fallback! Locator is: ", lpu_locator)
    #         return {'type': 'locator', 'value': lpu_locator}
    #     except Exception as e:
    #         print(f"Click failed even after semantic match: {e}")
    #
    # print("→ lpu failed → visual fallback...")


    # Semantic fallback
    semantic_locator = try_semantic_fallback(page, semantic_desc)
    if semantic_locator:
        try:
            print("→ Success with semantic fallback!")
            return {'type': 'locator', 'value': semantic_locator}
        except Exception as e:
            print(f"Click failed even after semantic match: {e}")

    print("→ Semantic failed → visual fallback...")

    # Visual fallback
    visual_result = try_visual_fallback(page, template_path, region_selector, primary_selector)
    if visual_result:
        print("→ Success with visual fallback!")
        return visual_result

    print("→ All fallbacks failed.")
    # return False
    return None