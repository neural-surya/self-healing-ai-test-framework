import json
from playwright.sync_api import Page, Locator
from groq import Groq
from utils.actions import find_candidates
from config import GROQ_API_KEY  # Ensure this is in your config

client = Groq(api_key=GROQ_API_KEY)


def try_lpu_healing(page: Page, semantic_desc: str) -> Locator | None:
    try:
        candidates = find_candidates(page)
        prompt = f"Target: '{semantic_desc}'. Candidates: {json.dumps(candidates)}. Return ONLY the exact 'text' value of the best match. No explanation."
        # Groq LPU handles this in <50ms
        chat_completion = client.chat.completions.create(
            messages =[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant",
            temperature=0
        )

        # 1. Get the Request ID
        request_id = chat_completion.id
        # 2. Get Inference Time (LPU execution only)
        # This is usually found in the x_groq dictionary within usage or response metadata
        usage_metadata = chat_completion.usage
        inference_time = getattr(usage_metadata, 'queue_time', 0) + getattr(usage_metadata, 'prompt_time', 0) + getattr(
            usage_metadata, 'completion_time', 0)

        print(f"Request ID: {request_id}")
        print(f"Actual LPU Inference Time: {inference_time}s")
        # Clean the output in case it still includes quotes or newlines
        match_text = chat_completion.choices[0].message.content.strip().split('\n')[-1].replace("'", "").replace('"',"")
        print(f"→ Groq LPU Match: {match_text}")
        # Use a specific locator method
        return page.get_by_text(match_text, exact=True).first
    except Exception as e:
        print(f"LPU healing error: {e}")
        return None