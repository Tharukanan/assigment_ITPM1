from playwright.sync_api import sync_playwright
from pathlib import Path
import argparse
import base64
import time
import sys
import csv

# Settings
DEFAULT_URL = "https://www.pixelssuite.com/crop-png"
DEFAULT_TIMEOUT_MS = 60000
DEFAULT_SLOW_MO_MS = 0
# CHANGED: Target the specific CSV file you want
DEFAULT_CSV = "execution_results.csv"

PNG_1X1_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMB/6X9wYQAAAAASUVORK5CYII="
)

def configure_stdout():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    except Exception:
        pass

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--png", default="sample.png")
    parser.add_argument("--out-dir", default="results")
    parser.add_argument("--csv", default=DEFAULT_CSV)
    parser.add_argument("--headless", action="store_true", default=False)
    parser.add_argument("--timeout-ms", type=int, default=DEFAULT_TIMEOUT_MS)
    parser.add_argument("--slow-mo-ms", type=int, default=DEFAULT_SLOW_MO_MS)
    return parser.parse_args()

def create_default_png_if_missing(file_path: Path):
    file_path.parent.mkdir(parents=True, exist_ok=True)
    if not file_path.exists():
        file_path.write_bytes(base64.b64decode(PNG_1X1_BASE64))

def find_and_upload_file(page, png_path: str):
    """Robust upload strategy for various tool layouts."""
    try:
        # Force hidden inputs to be visible/interactable
        page.evaluate("""() => {
            document.querySelectorAll('input[type="file"]').forEach(el => {
                el.style.cssText = 'display:block!important;visibility:visible!important;opacity:1!important;';
                el.removeAttribute('hidden');
            });
        }""")
        file_input = page.locator('input[type="file"]').first
        if file_input.count() > 0:
            file_input.set_input_files(png_path)
            return True
    except: pass
    
    # Try common button triggers if direct input fails
    try:
        for selector in ["button:has-text('Select')", "button:has-text('Upload')", ".dropzone"]:
            el = page.locator(selector).first
            if el.count() > 0:
                with page.expect_file_chooser(timeout=5000) as fc_info:
                    el.click()
                fc_info.value.set_files(png_path)
                return True
    except: pass
    return False

def check_preview_visible(page):
    """Detects images or canvas elements used by cropping/conversion tools."""
    return page.evaluate("""() => {
        const isVisible = (el) => !!(el && el.getClientRects().length > 0);
        const media = Array.from(document.querySelectorAll('img, canvas, .cropper-container'));
        return media.some(isVisible) || document.body.innerText.toLowerCase().includes('preview');
    }""")

def run_test():
    configure_stdout()
    args = parse_args()

    png_path = Path(args.png).resolve()
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = Path(args.csv).resolve()
    
    create_default_png_if_missing(png_path)

    result = {
        "file_type": "PNG",
        "file_path": str(png_path),
        "preview_detected": False,
        "status": "FAIL",
        "screenshot": "",
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=args.headless, slow_mo=args.slow_mo_ms)
        page = browser.new_page()
        
        try:
            print(f"Navigating to: {args.url}")
            page.goto(args.url, wait_until="networkidle")
            
            if find_and_upload_file(page, str(png_path)):
                print("File uploaded, waiting for preview...")
                # Poll for preview
                deadline = time.time() + 15
                while time.time() < deadline:
                    if check_preview_visible(page):
                        result["preview_detected"] = True
                        result["status"] = "PASS"
                        break
                    page.wait_for_timeout(500)
            
            screenshot_path = out_dir / f"crop_preview_{result['status'].lower()}.png"
            page.screenshot(path=str(screenshot_path), full_page=True)
            result["screenshot"] = str(screenshot_path)

        except Exception as e:
            print(f"Error during execution: {e}")
        finally:
            browser.close()

    # Log to Console
    print("\n" + "="*20 + " TEST RESULT " + "="*20)
    for key, value in result.items():
        print(f"{key.replace('_', ' ').title():<20}: {value}")
    
    # Save to execution_results.csv (Appending)
    file_exists = csv_path.exists()
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=result.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(result)
    print(f"Result appended to: {csv_path.name}")

if __name__ == "__main__":
    run_test()