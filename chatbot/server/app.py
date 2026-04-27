from flask import Flask, render_template, request, jsonify
import sqlite3
import re
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# LangChain
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

# =========================
# LOAD ENV
# =========================
ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "chat.db"
IMAGE_DATA_FILE = ROOT_DIR / "knowledge" / "extracted_images_text.txt"
DOC_DATA_FILE = ROOT_DIR / "knowledge" / "extracted_docs_text.txt"
INDEX_DIR = ROOT_DIR / "faiss_index"

records_cache = []

# =========================
# DATABASE
# =========================
def get_db():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS enquiries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            message TEXT,
            reply TEXT,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()

# =========================
# LOAD FAISS
# =========================
retriever = None

try:
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    vectorstore = FAISS.load_local(
        str(INDEX_DIR),
        embeddings,
        allow_dangerous_deserialization=True
    )

    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    print("✅ FAISS Loaded")

except Exception as e:
    print("❌ FAISS ERROR:", e)

# =========================
# PARSER
# =========================
def parse_structured_text(text: str):
    records = []
    university = None
    course = None
    specializations = []
    fees = None
    duration = None

    def flush():
        nonlocal university, course, specializations, fees, duration
        if university and course:
            records.append({
                "university": university.strip(),
                "course": course.strip(),
                "specializations": specializations.copy(),
                "fees": fees,
                "duration": duration
            })

    for raw_line in text.splitlines():
        line = raw_line.strip()

        if not line or line.startswith("="):
            continue

        # UNIVERSITY FIX
        if (
            line.isupper()
            and "COURSE" not in line
            and "FEES" not in line
            and "YEAR" not in line
            and "&" not in line
            and "-" not in line
            and len(line.split()) >= 2
        ):
            flush()
            university = line
            course = None
            specializations = []
            fees = None
            duration = None
            continue

        # COURSE
        if line.lower().startswith("course:"):
            flush()
            course = line.split(":", 1)[1].strip()
            specializations = []
            fees = None
            duration = None
            continue

        # FEES
        if "fees" in line.lower():
            nums = re.findall(r"\d+", line)
            if nums:
                fees = nums[0]
            continue

        # DURATION
        if "year" in line.lower():
            duration = line
            continue

        # SPECIALIZATION
        if line.startswith("-"):
            spec = line.replace("-", "").strip()

            if "fees" in spec.lower():
                continue
            if "duration" in spec.lower():
                continue
            if "university" in spec.lower():
                continue

            specializations.append(spec)

    flush()
    return records

# =========================
# LOAD DATA
# =========================
def load_structured_records():
    global records_cache
    records_cache = []

    if IMAGE_DATA_FILE.exists():
        records_cache += parse_structured_text(
            IMAGE_DATA_FILE.read_text(encoding="utf-8", errors="ignore")
        )

    if DOC_DATA_FILE.exists():
        records_cache += parse_structured_text(
            DOC_DATA_FILE.read_text(encoding="utf-8", errors="ignore")
        )

    print("✅ Records Loaded:", len(records_cache))

# =========================
# HELPERS
# =========================
def normalize(s):
    return re.sub(r"\s+", "", s.lower())

def detect_course(msg):
    m = normalize(msg)

    for r in records_cache:
        if normalize(r["course"]) in m:
            return r["course"]

    if "bca" in m:
        return "BCA"
    if "bba" in m:
        return "BBA"
    if "bcom" in m:
        return "B.Com"
    if "imca" in m:
        return "IMCA"

    return None

# =========================
# ANSWER ENGINE
# =========================
def answer_query(msg: str):
    try:
        m = msg.lower().strip()

        # ✅ SMART GREETING
        greetings = ["hi", "hello", "hey", "hii", "helo"]
        if any(m == g or m.startswith(g + " ") for g in greetings):
            return "👋 Hello! Ask me about courses, fees, duration, specialization or best university."

        if "good morning" in m:
            return "🌅 Good morning!"

        if "good night" in m:
            return "🌙 Good night!"

        course = detect_course(msg)

        # 🔥 BEST UNIVERSITY
        if "best" in m and course:
            results = []
            for r in records_cache:
                if normalize(r["course"]) == normalize(course) and r["fees"]:
                    results.append((r["university"], int(r["fees"])))

            if results:
                best = sorted(results, key=lambda x: x[1])[0]
                return f"🏆 Best option for {course}:\n\n{best[0]} (₹{best[1]})"

        # 🔥 SPECIALIZATION (MULTI)
        if "specialization" in m or "specialisation" in m:
            if course:
                results = []
                seen = set()

                for r in records_cache:
                    if normalize(r["course"]) == normalize(course):
                        specs = [s for s in r["specializations"] if s not in seen]
                        seen.update(specs)

                        if specs:
                            results.append(f"🏫 {r['university']}\n📘 " + ", ".join(specs))

                if results:
                    return f"📘 Specializations for {course}:\n\n" + "\n\n".join(results)

            return "❌ No specialization found."

        # 🔥 FEES
        if "fees" in m:
            results = []
            for r in records_cache:
                if course:
                    if normalize(r["course"]) == normalize(course) and r["fees"]:
                        results.append(f"{r['course']} ({r['university']}) → ₹{r['fees']}")
                else:
                    if r["fees"]:
                        results.append(f"{r['course']} ({r['university']}) → ₹{r['fees']}")

            if results:
                return "💰 Fees Details:\n\n" + "\n".join(results[:10])

            return "❌ Fees not found."

        # 🔥 DURATION
        if "duration" in m:
            results = []
            for r in records_cache:
                if course:
                    if normalize(r["course"]) == normalize(course) and r["duration"]:
                        results.append(f"{r['course']} ({r['university']}) → {r['duration']}")
                else:
                    if r["duration"]:
                        results.append(f"{r['course']} ({r['university']}) → {r['duration']}")

            if results:
                return "⏳ Duration Details:\n\n" + "\n".join(results[:10])

        # 🔥 COURSE DETAILS (MULTI UNIVERSITY)
        if course:
            results = []

            for r in records_cache:
                if normalize(r["course"]) == normalize(course):
                    results.append(
                        f"🏫 {r['university']}\n"
                        f"💰 ₹{r.get('fees', 'N/A')}\n"
                        f"⏳ {r.get('duration', 'N/A')}\n"
                        f"📘 Specialization: {', '.join(r['specializations'])}\n"
                    )

            if results:
                return f"🎓 Course: {course}\n\n" + "\n\n".join(results)

        # 🔥 FAISS fallback
        if retriever:
            docs = retriever.invoke(msg)
            if docs:
                return "📄 Info:\n\n" + "\n\n".join([d.page_content for d in docs[:2]])

        return "❌ No data found."

    except Exception as e:
        print("🔥 ERROR:", e)
        return "❌ Server Error"

# =========================
# ROUTES
# =========================
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    msg = data.get("message", "")
    user_id = data.get("user_id", "user")

    reply = answer_query(msg)

    conn = get_db()
    c = conn.cursor()
    c.execute(
        "INSERT INTO enquiries (user_id, message, reply, timestamp) VALUES (?, ?, ?, ?)",
        (user_id, msg, reply, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
    conn.commit()
    conn.close()

    return jsonify({"reply": reply})

@app.route("/admin")
def admin():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT user_id, message, reply, timestamp FROM enquiries ORDER BY id DESC")
    chats = c.fetchall()
    conn.close()

    return render_template("admin.html", chats=chats)

# =========================
# RUN
# =========================
if __name__ == "__main__":
    init_db()
    load_structured_records()
    app.run(debug=True)