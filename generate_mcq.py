import json
import os
import urllib.request
from datetime import datetime

API_KEY = os.environ.get("GEMINI_API_KEY")

PROMPT = """
Generate 5 unique, high-quality Assamese MCQ questions for Assam competitive exams (ADRE, Assam Police, APSC, TET).
Mix subjects: Assam History, Assam Geography, Assamese Literature, Indian Polity, and Mathematics.
Return ONLY valid JSON array in this exact format without any markdown formatting:
[
  {
    "subject": "অসম বুৰঞ্জী (Assam History)",
    "q": "প্রশ্নটো ইয়াত অসমীয়াত লিখিব?",
    "options": ["বিকল্প ১", "বিকল্প ২", "বিকল্প ৩", "বিকল্প ৪"],
    "ans": 0,
    "exp": "ইয়াত চমু আৰু শুদ্ধ অসমীয়া ব্যাখ্যা থাকিব।"
  }
]
Note: "ans" must be the integer index (0, 1, 2, or 3) of the correct option.
"""

def fetch_new_mcqs():
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": PROMPT}]}],
        "generationConfig": {"responseMimeType": "application/json"}
    }
    req = urllib.request.Request(
        url, 
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req) as response:
        res_data = json.loads(response.read().decode('utf-8'))
        raw_text = res_data['candidates'][0]['content']['parts'][0]['text']
        return json.loads(raw_text)

def main():
    with open("questions.json", "r", encoding="utf-8") as f:
        bank = json.load(f)

    new_questions = fetch_new_mcqs()

    # নতুন প্রশ্নবোৰ একেবাৰে ওপৰত যোগ হ'ব আৰু পুৰণিবোৰ তলত জমা হৈ থাকিব
    bank["questions"] = new_questions + bank["questions"]
    bank["last_updated"] = datetime.now().strftime("%Y-%m-%d")

    with open("questions.json", "w", encoding="utf-8") as f:
        json.dump(bank, f, ensure_ascii=False, indent=2)

    print(f"Successfully added {len(new_questions)} new Assamese MCQs!")

if __name__ == "__main__":
    main()
