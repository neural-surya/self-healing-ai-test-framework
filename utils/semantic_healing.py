# utils/semantic_healing.py
from bs4 import BeautifulSoup
from playwright.sync_api import Page, Locator
from sentence_transformers import util
import numpy as np
from config import SEMANTIC_MODEL, SEMANTIC_THRESHOLD

def try_semantic_fallback(page: Page, semantic_desc: str) -> Locator | None:
    """
    Scans interactive elements semantically and returns a locator to the best match.
    Returns None if no good match is found.
    """
    try:
        html = page.content()
        soup = BeautifulSoup(html, 'html.parser')

        candidate_tags = ['button', 'a', 'div[role="button"]', 'input[type="submit"]', 'input[type="button"]']
        candidates = []
        elements_info = []

        for tag in candidate_tags:
            for elem in soup.select(tag):
                text = elem.get_text(strip=True)
                if not text:
                    continue
                attrs = ' '.join([f"{k}={v}" for k, v in elem.attrs.items() if isinstance(v, str)])
                combined = f"{text} {attrs}".strip()
                if combined:
                    candidates.append(combined)
                    elements_info.append(elem)

        if not candidates:
            print("No candidate elements found for semantic search.")
            return None

        print(f"Found {len(candidates)} candidates. Computing semantic similarity...")

        target_embedding = SEMANTIC_MODEL.encode(semantic_desc, convert_to_tensor=True)
        cand_embeddings = SEMANTIC_MODEL.encode(candidates, convert_to_tensor=True)
        similarities = util.cos_sim(target_embedding, cand_embeddings)[0]

        best_idx = similarities.argmax().item()
        best_score = similarities[best_idx].item()

        if best_score < SEMANTIC_THRESHOLD:
            print(f"Best semantic score {best_score:.3f} < threshold {SEMANTIC_THRESHOLD}")
            return None

        best_elem = elements_info[best_idx]
        text = best_elem.get_text(strip=True)

        if best_elem.get('id'):
            selector = f"#{best_elem['id']}"
        elif text:
            selector = f"text={text}"
        else:
            selector = f"//*[contains(text(), '{text[:30]}')]"

        print(f"→ Semantic match! Score: {best_score:.3f} | Text: '{text[:60]}' | Selector: {selector}")

        return page.locator(selector).first

    except Exception as e:
        print(f"Semantic fallback error: {e}")
        return None