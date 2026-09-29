import os
import json
import datetime
import urllib.request
import urllib.error

# ফাইলৰ নাম আৰু API Key
QUESTIONS_FILE = "questions.json"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()

# আজিৰ বাৰ অনুসৰি স্বয়ংক্ৰিয়ভাৱে বেলেগ বেলেগ পৰীক্ষা আৰু বিষয় বাছি লোৱা তালিকা
DAILY_TOPICS = [
    {"exam": "adre", "subject": "অসম বুৰঞ্জী (Assam History)", "focus": "Ahom Dynasty, Freedom Struggle in Assam, Historic Battles and Treaties"},
    {"exam": "police", "subject": "ভাৰতীয় সংবিধান (Indian Polity)", "focus": "Fundamental Rights, Articles related to Assam & Northeast, Constitutional Amendments"},
    {"exam": "adre", "subject": "অসমৰ ভূগোল (Assam Geography)", "focus": "National Parks, Wildlife Sanctuaries, Rivers, Bridges and Transport of Assam"},
    {"exam": "ssc", "subject": "গণিত চৰ্টকাট (Maths Shortcut)", "focus": "Percentage, Profit & Loss, Time & Work, Speed & Train problems with 5-second Assamese shortcut tricks"},
    {"exam": "tet", "subject": "শিশু বিকাশ আৰু পেডাগ’জি (CDP)", "focus": "Piaget, Vygotsky, Kohlberg, NEP 2020, Inclusive Education and Learning Disabilities"},
    {"exam": "dhs", "subject": "সাধাৰণ বিজ্ঞান (General Science)", "focus": "Human Body, Vitamins, Diseases, Blood Groups, Physics & Chemistry basics"},
    {"exam": "apsc", "subject": "অসম অধ্যয়ন আৰু কাৰেণ্ট এফেয়াৰ্ছ", "focus": "Assam Government Schemes, UNESCO Heritage, Classical Language, GI Tags and Awards"}
]

def load_existing_database():
    if os.path.exists(QUESTIONS_FILE):
        try:
            with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading {QUESTIONS_FILE}: {e}")
    return {"last_updated": "", "total_questions": 0, "questions": []}

def generate_new_mcqs(topic_info, existing_questions):
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY পোৱা নগ'ল! অনুগ্ৰহ কৰি GitHub Secrets-ত API Key যোগ কৰক।")

    # পুৰণি প্রশ্নৰ লগত যাতে মিল নাখায় তাৰ বাবে শেহতীয়া ১০ টা প্রশ্নৰ নমুনা লোৱা
    recent_q_texts = [q.get("q", "") for q in existing_questions[:10]]
    avoid_list = "\n".join(recent_q_texts)

    prompt = f"""You are an expert Assamese exam question paper setter for Assam Government Exams (ADRE, Assam Police, APSC, Assam TET, DHS, SSC GD, HSLC).
Generate 5 brand-new, high-quality, 100% factually accurate Multiple Choice Questions (MCQs) in clear Assamese language (Assamese script).

Target Exam Tag: "{topic_info['exam']}"
Subject Name: "{topic_info['subject']}"
Topic Focus: {topic_info['focus']}

Do NOT repeat these recent questions:
{avoid_list}

Return ONLY a valid JSON array containing 5 objects in this exact format (no markdown, no backticks, no extra text):
[
  {{
    "exam": "{topic_info['exam']}",
    "subject": "{topic_info['subject']}",
    "q": "প্রশ্নটো ইয়াত অসমীয়াত লিখক?",
    "options": ["বিকল্প ১", "বিকল্প ২", "বিকল্প ৩", "বিকল্প ৪"],
    "ans": 0,
    "exp": "ইয়াত চমু আৰু নিখুঁত অসমীয়া ব্যাখ্যা বা চৰ্টকাট সূত্র লিখক।"
  }}
]"""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.7,
            "responseMimeType": "application/json"
        }
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=60) as response:
        res_data = json.loads(response.read().decode("utf-8"))
        raw_text = res_data["candidates"][0]["content"]["parts"][0]["text"].strip()
        
        # যদি ভুলতে markdown ```json থাকে তেন্তে পৰিষ্কাৰ কৰা
        if raw_text.startswith("```"):
            raw_text = raw_text.strip("`")
            if raw_text.startswith("json"):
                raw_text = raw_text[4:].strip()

        new_items = json.loads(raw_text)
        return new_items

def main():
    db = load_existing_database()
    existing_questions = db.get("questions", [])
    existing_q_set = {q.get("q", "").strip() for q in existing_questions}

    # আজিৰ বাৰ অনুসৰি টপিক নিৰ্বাচন কৰা (Monday=0 ... Sunday=6)
    today_idx = datetime.datetime.utcnow().weekday()
    topic_info = DAILY_TOPICS[today_idx % len(DAILY_TOPICS)]

    print(f"Generating new Assamese MCQs for: {topic_info['subject']} ({topic_info['exam']})...")
    new_mcqs = generate_new_mcqs(topic_info, existing_questions)

    added_count = 0
    valid_new_mcqs = []
    for item in new_mcqs:
        q_text = item.get("q", "").strip()
        if q_text and q_text not in existing_q_set and len(item.get("options", [])) == 4:
            valid_new_mcqs.append({
                "exam": item.get("exam", topic_info["exam"]),
                "subject": item.get("subject", topic_info["subject"]),
                "q": q_text,
                "options": item["options"],
                "ans": int(item.get("ans", 0)),
                "exp": item.get("exp", "")
            })
            existing_q_set.add(q_text)
            added_count += 1

    # নতুন প্রশ্নকেইটা একেবাৰে ওপৰত (প্রথমতে) যোগ কৰা যাতে ডেইলী টেষ্টত নতুন প্রশ্ন আহে
    updated_questions = valid_new_mcqs + existing_questions

    today_str = (datetime.datetime.utcnow() + datetime.timedelta(hours=5, minutes=30)).strftime("%Y-%m-%d")
    db["last_updated"] = today_str
    db["total_questions"] = len(updated_questions)
    db["questions"] = updated_questions

    with open(QUESTIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

    print(f"Successfully added {added_count} new questions! Total questions now: {len(updated_questions)}")

if __name__ == "__main__":
    main()
