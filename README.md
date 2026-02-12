# Self-Healing Test Automation Framework

This project implements a self-healing test automation framework using Playwright, Pytest, Sentence Transformers (for semantic matching), and OpenCV (for visual matching). It is designed to robustly locate elements even when their selectors change or fail.

## Features

*   **Multi-tier Healing Strategy:**
    1.  **Primary Locator:** Attempts to find the element using the standard Playwright selector.
    2.  **Semantic Fallback:** If the primary locator fails, it uses a Sentence Transformer model (`all-MiniLM-L6-v2`) to find semantically similar elements on the page (e.g., finding a button labeled "Sign In" when looking for "Log In").
    3.  **Visual Fallback:** If semantic matching fails, it uses OpenCV template matching to visually locate the element on the screen. It supports multi-scale matching and Non-Maximum Suppression (NMS) to improve accuracy.

*   **Auto-Capture Templates:** Can automatically capture and save visual templates for elements if they are successfully found by the primary locator but the template file is missing.
*   **Region-Restricted Search:** Supports restricting visual searches to specific regions of the page to reduce false positives.
*   **Pytest Integration:** Uses Pytest fixtures for browser and page management.

## Groq LPU Integration

The framework includes support for Groq LPU (Language Processing Unit) inferencing, which is referenced in `utils/groq_lpu_healing.py`. This allows for ultra-fast semantic matching using LLMs hosted on Groq's hardware.

To enable Groq LPU healing:
1.  Open `healing_strategy.py`.
2.  Uncomment the code block under `# LPU Locator` inside the `find_locator_with_healing` function.
3.  Ensure you have configured your `GROQ_API_KEY` in `config.py`.

**Performance:**
When tested, the Groq LPU processed the request in just **~82ms**, whereas using the local sentence transformer took **325ms**. This confirms that LPU inferencing is much faster.

## Project Structure

*   `healing_strategy.py`: Core logic for the multi-tier healing strategy.
*   `config.py`: Configuration settings, including element mappings, thresholds, and model initialization.
*   `conftest.py`: Pytest fixtures for setting up the browser and page context.
*   `utils/`:
    *   `actions.py`: Helper functions to perform actions (click, type, etc.) on locators or coordinates.
    *   `semantic_healing.py`: Implementation of the semantic fallback mechanism.
    *   `visual_healing.py`: Implementation of the visual fallback mechanism using OpenCV.
    *   `groq_lpu_healing.py`: Implementation of the semantic healing using Groq LPU.
*   `tests/`: Contains test scripts.
    *   `test_login_self_healing.py`: Example test demonstrating self-healing on a login button.
*   `templates/`: Directory to store image templates for visual matching.
*   `requirements.txt`: List of Python dependencies.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd self-healing-ai-test-framework
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Install Playwright browsers:**
    ```bash
    playwright install
    ```

## Usage

### Running the Tests

This project uses `pytest`. To run the self-healing tests:

```bash
pytest tests/test_login_self_healing.py
```

Or simply run all tests:

```bash
pytest
```

### Configuration

You can configure the framework in `config.py`:

*   **`ELEMENT_MAPPING`**: Define the mapping for your elements. Each entry requires:
    *   Key: The primary selector (e.g., `'button:has-text("Login")'`).
    *   Value: A tuple containing the semantic description and the path to the visual template image.
*   **`REGION_SELECTORS`**: (Optional) Define a parent selector to restrict the visual search area for a specific element.
*   **Thresholds**: Adjust `SEMANTIC_THRESHOLD` and `VISUAL_THRESHOLD` to tune the sensitivity of the matching algorithms.

## Dependencies

*   `pytest`
*   `pytest-playwright`
*   `playwright`
*   `sentence-transformers`
*   `opencv-python`
*   `numpy`
*   `beautifulsoup4`
*   `torch`
