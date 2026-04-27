from pathlib import Path
from dotenv import load_dotenv

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

# =========================
# LOAD ENV
# =========================
ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

IMAGE_FILE = ROOT_DIR / "knowledge" / "extracted_images_text.txt"
DOC_FILE = ROOT_DIR / "knowledge" / "extracted_docs_text.txt"
INDEX_DIR = ROOT_DIR / "faiss_index"


def read_file(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def load_all_text() -> str:
    text_data = ""

    if IMAGE_FILE.exists():
        image_text = read_file(IMAGE_FILE).strip()
        if image_text:
            text_data += image_text + "\n\n"

    if DOC_FILE.exists():
        doc_text = read_file(DOC_FILE).strip()
        if doc_text:
            text_data += doc_text + "\n\n"

    return text_data.strip()


def main():
    text_data = load_all_text()

    if not text_data:
        print("❌ No data found in extracted_images_text.txt or extracted_docs_text.txt")
        return

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", ".", ",", " "]
    )

    chunks = splitter.split_text(text_data)

    if not chunks:
        print("❌ No chunks created")
        return

    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    vectorstore = FAISS.from_texts(chunks, embeddings)
    vectorstore.save_local(str(INDEX_DIR))

    print("✅ FAISS index created successfully")
    print(f"✅ Total chunks: {len(chunks)}")
    print(f"✅ Saved at: {INDEX_DIR}")


if __name__ == "__main__":
    main()