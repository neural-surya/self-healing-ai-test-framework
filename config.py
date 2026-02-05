# config.py
import os
from dotenv import load_dotenv
load_dotenv()

from sentence_transformers import SentenceTransformer
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
# Load model once (shared across modules)
SEMANTIC_MODEL = SentenceTransformer('all-MiniLM-L6-v2')
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
# Mapping: primary_selector → (semantic_description, template_path)
ELEMENT_MAPPING = {
    "#checkout-btn": ("checkout button", "templates/checkout_button_template.png"),
    'button:has-text("Login")': (          # ← Primary locator (Playwright text engine)
        "log in button",
        os.path.join(PROJECT_ROOT, "templates", "login_button_template.png") # ← Visual template path (tight crop of the button)
    ),
    'button:has-text("Sign Up")': (          # ← Primary locator (Playwright text engine)
        "sign up button",
        os.path.join(PROJECT_ROOT, "templates", "signup_button_template.png") # ← Visual template path (tight crop of the button)
    ),
    # Add more as needed for other elements
    # "#add-to-cart": ("add to cart button", "templates/add_to_cart_template.png"),
    # ".search-icon": ("search icon", "templates/search_icon_template.png"),
}

# Thresholds & settings
SEMANTIC_THRESHOLD = 0.7
VISUAL_THRESHOLD = 0.50
SCALES = [0.8, 1.0, 1.2]                   # Multi-scale factors
NMS_OVERLAP_THRESHOLD = 0.3                # IoU threshold for non-max suppression

# Optional: known regions for visual search (reduces false positives)
REGION_SELECTORS = {
    "#checkout-btn": "#basket-actions",     # example: restrict search to basket footer area
    'button:has-text("Login")': 'nav > div > div > div > div.flex.items-center.gap-2',
    'button:has-text("Sign Up")': 'nav > div > div > div > div.flex.items-center.gap-2',
    # Add more if you know approximate locations
}