# utils/visual_healing.py
import os
from typing import Dict, Optional, Any
import cv2
import numpy as np
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError
from config import SCALES, VISUAL_THRESHOLD
from datetime import datetime

def get_or_capture_template(
        page: Page,
        primary_selector: str,
        template_path: str
) -> Optional[np.ndarray]:
    """
    Returns grayscale template:
    - If file exists → load it
    - If missing → try to capture it dynamically using primary_selector
    - Saves captured image for future use
    """
    # 1. Try to load existing template
    if os.path.exists(template_path):
        template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
        if template is not None:
            print(f"Loaded existing template: {os.path.basename(template_path)} (shape: {template.shape})")
            return template
        print(f"Template file exists but is invalid: {template_path}")

    # 2. Automatic capture only if file is missing AND element is visible
    print(f"No template found → checking if primary locator is visible: {primary_selector}")
    try:
        locator = page.locator(primary_selector)
        if locator.is_visible(timeout=5000):
            print(f"Primary locator is visible → capturing template automatically")
            png_bytes = locator.screenshot(type="png")
            img_array = np.frombuffer(png_bytes, np.uint8)
            template_bgr = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            template_gray = cv2.cvtColor(template_bgr, cv2.COLOR_BGR2GRAY)

            os.makedirs(os.path.dirname(template_path), exist_ok=True)
            cv2.imwrite(template_path, template_gray)
            print(f"Template auto-captured and saved: {os.path.basename(template_path)} (shape: {template_gray.shape})")
            return template_gray
        else:
            print(f"Primary locator not visible → cannot auto-capture")
            return None


    except PlaywrightTimeoutError:
        print(f"Primary locator timeout/not visible → cannot capture")
        return None
    except Exception as e:
        print(f"Auto-capture failed: {e}")
        return None

def non_max_suppression(boxes, scores, overlap_thresh=0.5):
    """Simple greedy NMS"""
    if len(boxes) == 0:
        return []

    boxes = np.array(boxes, dtype=np.float32)
    scores = np.array(scores, dtype=np.float32)

    indices = np.argsort(scores)[::-1]
    picked = []

    while len(indices) > 0:
        i = indices[0]
        picked.append(i)

        xx1 = np.maximum(boxes[i, 0], boxes[indices[1:], 0])
        yy1 = np.maximum(boxes[i, 1], boxes[indices[1:], 1])
        xx2 = np.minimum(boxes[i, 2], boxes[indices[1:], 2])
        yy2 = np.minimum(boxes[i, 3], boxes[indices[1:], 3])

        w = np.maximum(0, xx2 - xx1 + 1)
        h = np.maximum(0, yy2 - yy1 + 1)
        overlap = (w * h) / ((boxes[i, 2] - boxes[i, 0] + 1) * (boxes[i, 3] - boxes[i, 1] + 1))

        indices = indices[1:][overlap <= overlap_thresh]

    return picked


def try_visual_fallback(page: Page, template_path: str, region_selector: str | None = None, primary_selector: str = "") -> Optional[Dict[str, Any]]:
    """
    Performs multi-scale template matching + NMS.
    Clicks the best detected position if successful.
    Returns True if clicked, False otherwise.
    """
    try:
        # Screenshot (region if provided, else viewport)
        if region_selector:
            screenshot_bytes = page.locator(region_selector).screenshot()
            print(f"Visual search restricted to region: {region_selector}")
        else:
            screenshot_bytes = page.screenshot(full_page=False)

        img_array = np.frombuffer(screenshot_bytes, np.uint8)
        page_img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        page_gray = cv2.cvtColor(page_img, cv2.COLOR_BGR2GRAY)

        # 2. Get template (load or auto-capture)
        template_gray = get_or_capture_template(page, primary_selector, template_path)
        if template_gray is None:
            print("No usable template available (could not load or auto-capture)")
            return None

        t_h, t_w = template_gray.shape

        all_boxes = []
        all_scores = []

        # After loading page_gray and template_gray
        print("DEBUG: page_gray shape (height, width) =", page_gray.shape)
        print("DEBUG: template_gray shape (height, width) =", template_gray.shape)
        print("DEBUG: region used =", region_selector or "full viewport")

        # 3. Multi-scale matching
        for scale in SCALES:
            new_w, new_h = int(t_w * scale), int(t_h * scale)
            print(f"Scale {scale:.2f}: scaled template = {new_h} × {new_w}")
            if new_h > page_gray.shape[0] or new_w > page_gray.shape[1]:
                print(f"  → SKIPPED (larger than page {page_gray.shape[0]} × {page_gray.shape[1]})")
                continue

            scaled = cv2.resize(template_gray, (new_w, new_h))
            res = cv2.matchTemplate(page_gray, scaled, cv2.TM_CCOEFF_NORMED)
            max_val = cv2.minMaxLoc(res)[1]
            print(f"Scale {scale:.2f} - Max correlation: {max_val:.4f}")

            loc = np.where(res >= VISUAL_THRESHOLD)
            for pt in zip(*loc[::-1]):
                box = [pt[0], pt[1], pt[0] + new_w, pt[1] + new_h]
                score = res[pt[1], pt[0]]
                all_boxes.append(box)
                all_scores.append(score)

        if not all_boxes:
            print(f"No visual matches above threshold {VISUAL_THRESHOLD}")
            return None

        # 4. Apply Non-max suppression
        picked = non_max_suppression(all_boxes, all_scores, overlap_thresh=0.3)
        if not picked:
            print("All matches suppressed by NMS")
            return None

        # Take the highest remaining
        best_idx = picked[0]
        best_box = all_boxes[best_idx]
        best_score = all_scores[best_idx]

        local_center_x = int((best_box[0] + best_box[2]) // 2)
        local_center_y = int((best_box[1] + best_box[3]) // 2)

        # Get global coordinates
        if region_selector:
            # Get bounding box of the region locator (global viewport coords)
            region_locator = page.locator(region_selector)
            region_box = region_locator.bounding_box(timeout=8000)  # x, y, width, height
            if region_box:
                global_x = int(region_box['x'] + local_center_x)
                global_y = int(region_box['y'] + local_center_y)
                print(f"→ Region offset: x={region_box['x']}, y={region_box['y']}")
            else:
                print("→ Region bounding box not found — falling back to local coords")
                global_x, global_y = local_center_x, local_center_y
        else:
            # Full viewport screenshot — local is already global
            global_x, global_y = local_center_x, local_center_y

        print(f"→ Local center (relative to region): ({local_center_x}, {local_center_y})")
        print(
            f"→ Global click position (full viewport): ({global_x}, {global_y}) | Score: {best_score:.3f} | Unique detections: {len(picked)}")

        # Optional: Save debug image with click marker
        debug_img = cv2.cvtColor(page_gray, cv2.COLOR_GRAY2BGR)
        cv2.circle(debug_img, (local_center_x, local_center_y), radius=8, color=(0, 0, 255), thickness=-1)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        debug_path = f"debug_click_{timestamp}.png"
        cv2.imwrite(debug_path, debug_img)
        print(f"Debug image with click marker saved: {debug_path}")
        return {'type': 'coord', 'x': global_x, 'y': global_y, 'score': best_score}

    except Exception as e:
        print(f"Visual fallback error: {e}")
        return None