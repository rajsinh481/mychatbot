from flask import Flask, request, jsonify
from langdetect import detect

app = Flask(__name__)
COURSES = {
    "imca ai": {
        "name": "IMCA (AI & ML)",
        "fee": "₹82,000 per year",
        "duration": "3 Years"
    },
    "imca cyber": {
        "name": "IMCA (Cyber Security)",
        "fee": "₹82,000 per year",
        "duration": "3 Years"
    },
    "imba ibm": {
        "name": "IMBA (IBM)",
        "fee": "₹82,000 per year",
        "duration": "3 Years"
    },
    "imba aviation": {
        "name": "IMBA (Aviation)",
        "fee": "₹82,000 per year",
        "duration": "3 Years"
    }
}


@app.route("/chat", methods=["POST"])
def chat():
    user_msg = request.json.get("message", "").lower()

    # Language detect
    try:
        lang = detect(user_msg)
    except:
        lang = "en"

    # Course reply
    for key in COURSES:
        if key in user_msg:
            c = COURSES[key]

            if lang == "gu":
                reply = (
                    f"કોર્સ: {c['name']}<br>"
                    f"સમયગાળો: {c['duration']}<br>"
                    f"ફી: {c['fee']}"
                )
            elif lang == "hi":
                reply = (
                    f"कोर्स: {c['name']}<br>"
                    f"अवधि: {c['duration']}<br>"
                    f"फीस: {c['fee']}"
                )
            else:
                reply = (
                    f"Course: {c['name']}<br>"
                    f"Duration: {c['duration']}<br>"
                    f"Fees: {c['fee']}"
                )

            return jsonify({"reply": reply})

    # Default reply
    if lang == "gu":
        reply = "કૃપા કરીને કોર્સ નામ પૂછો (IMCA / IMBA)."
    elif lang == "hi":
        reply = "कृपया कोर्स का नाम पूछें (IMCA / IMBA)."
    else:
        reply = "Please ask about IMCA or IMBA courses."

    return jsonify({"reply": reply})


if __name__ == "__main__":
    app.run(debug=True)
