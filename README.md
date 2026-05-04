# IT3040 – ITPM Assignment 1
## Playwright Automation – pixelssuite.com Preview Test

---

## Prerequisites
- Python 3.11 or 3.12
- Google Chrome

---

## Installation

```bash
cd /d D:\test_automation_ui\test_automation_ui
pip install -U pip
pip install playwright openpyxl
playwright install
```

---

## Run the Test

```bash
python image_preview_test.py --url "https://www.pixelssuite.com/crop-png" --slow-mo-ms 2000
```

---

## What it does
- Automated Upload: Uploads a PNG image to the Crop PNG tool using a multi-strategy selector.
- Preview Detection: Verifies if the image preview (canvas or img) is successfully rendered in the UI.
- Data Logging: Appends the final test status and details into execution_results.csv.
- Visual Evidence: Saves a full-page screenshot of the result in the results/ folder.
