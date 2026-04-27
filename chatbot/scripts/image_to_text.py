import os
from pathlib import Path
from PIL import Image
import pytesseract

# =========================
# PATHS
# =========================
ROOT_DIR = Path(__file__).resolve().parent.parent
IMAGE_FOLDER = ROOT_DIR / "knowledge" / "docs"
OUTPUT_FILE = ROOT_DIR / "knowledge" / "extracted_images_text.txt"
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Windows માટે Tesseract path
pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH


def format_text(raw_text: str) -> str:
    lines = raw_text.split("\n")
    clean_lines = [line.strip() for line in lines if line.strip()]

    formatted = []

    for line in clean_lines:
        words = line.split()

        # short lines ને heading માનો
        if 1 <= len(words) <= 4:
            formatted.append(f"\n### {line}\n")
        else:
            formatted.append(f"- {line}")

    return "\n".join(formatted)


def extract_text_from_image(image_path: Path) -> str:
    try:
        image = Image.open(image_path)
        raw_text = pytesseract.image_to_string(image)
        return format_text(raw_text)
    except Exception as e:
        return f"Error extracting text from {image_path.name}: {e}"


def process_images():
    if not Path(TESSERACT_PATH).exists():
        print("❌ Tesseract path not found.")
        print(f"Check this path: {TESSERACT_PATH}")
        return

    if not IMAGE_FOLDER.exists():
        print("❌ knowledge/docs folder not found.")
        return

    files = [
        f for f in os.listdir(IMAGE_FOLDER)
        if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))
    ]

    if not files:
        print("❌ No image files found in knowledge/docs")
        return

    all_text = ""

    for file in files:
        path = IMAGE_FOLDER / file
        print(f"Processing: {file}")

        extracted = extract_text_from_image(path)

        all_text += f"\n\n===== IMAGE SOURCE: {file} =====\n"
        all_text += extracted
        all_text += "\n"

    OUTPUT_FILE.write_text(all_text, encoding="utf-8")

    print("✅ Structured image text saved to extracted_images_text.txt")


if __name__ == "__main__":
    process_images()