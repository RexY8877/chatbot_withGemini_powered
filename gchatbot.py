import os
import google.generativeai as genai
from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
import time
import socket
from dotenv import load_dotenv

# --- 1. Load Environment Variables ---
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("Error: GEMINI_API_KEY not set. Please set it in your environment variables.")
    exit()

try:
    genai.configure(api_key=GEMINI_API_KEY)
    print("Gemini API configured successfully.")
except Exception as e:
    print(f"Error configuring Gemini API: {e}")
    exit()

# --- 2. Knowledge Base ---
knowledge_base = [
    {
        "question": "What is My Corporate School?",
        "keywords": ["what is", "about", "my corporate school"],
        "answer": "My Corporate School is an online learning platform dedicated to providing high-quality education and skill development in various fields like IT, Data Science, Digital Marketing, and more."
    },
    {
        "question": "What courses do you offer?",
        "keywords": ["courses", "programs", "offerings"],
        "answer": "We offer a wide range of courses including Python Programming, Data Science, Web Development (HTML, CSS, JavaScript), Digital Marketing, and many others."
    },
    {
        "question": "Are the classes online or offline?",
        "keywords": ["online", "offline", "classes", "mode"],
        "answer": "All our classes are conducted online, providing flexibility and accessibility to learners from anywhere."
    },
    {
        "question": "How can I enroll in a course?",
        "keywords": ["enroll", "admission", "register", "join"],
        "answer": "You can enroll in a course by visiting the specific course page on our website and following the admission process outlined there."
    },
    {
        "question": "Do you provide placement assistance?",
        "keywords": ["placement", "job", "career", "assistance"],
        "answer": "Yes, we provide career guidance and placement assistance to help our students achieve their professional goals."
    },
    {
        "question": "How can I contact My Corporate School?",
        "keywords": ["contact", "reach out", "support", "get in touch"],
        "answer": "You can contact us via the details provided on our 'Contact Us' page on our website, including email and phone number."
    },
    {
        "question": "What is the Campus to Corporate program?",
        "keywords": ["campus to corporate", "transition program", "corporate skills", "fresh graduates"],
        "answer": "It is a transition training program designed for students and fresh graduates to help them develop essential corporate soft skills, communication, and interview readiness."
    },
    {
        "question": "Who should attend the Campus to Corporate program?",
        "keywords": ["who should attend", "eligible", "suitable", "freshers", "students"],
        "answer": "Final-year students, recent graduates, and job seekers looking to step confidently into the corporate world."
    },
    {
        "question": "What skills will I learn in Campus to Corporate?",
        "keywords": ["skills", "learn", "corporate etiquette", "communication", "teamwork", "interview skills"],
        "answer": "Corporate etiquette, communication, teamwork, leadership, time management, and interview handling."
    },
    {
        "question": "Is placement assistance available?",
        "keywords": ["placement", "job support", "career help", "recruitment", "interview"],
        "answer": "We provide interview preparation and connect students to hiring networks, though direct placement depends on individual performance."
    },
    {
        "question": "What types of corporate training do you offer?",
        "keywords": ["corporate training", "training types", "company sessions", "skills training"],
        "answer": "We offer leadership, communication, team building, managerial, and professional development training."
    },
    {
        "question": "Can corporate training be customized?",
        "keywords": ["custom training", "tailor made", "customized sessions", "company specific"],
        "answer": "Yes, we offer tailor-made training based on the needs and goals of your organization."
    },
    {
        "question": "Are these trainings available online?",
        "keywords": ["online", "virtual", "remote", "training mode"],
        "answer": "Yes, we provide both online and on-site training options."
    },
    {
        "question": "Do you provide certification?",
        "keywords": ["certificate", "certification", "proof of completion"],
        "answer": "Yes, participants receive completion certificates for most training programs."
    },
    {
        "question": "What is Individual Training?",
        "keywords": ["individual training", "personal coaching", "one-on-one", "custom session"],
        "answer": "One-on-one personalized skill-building sessions for professionals or students seeking personal growth and career development."
    },
    {
        "question": "Can I schedule Individual Training sessions based on availability?",
        "keywords": ["scheduling", "timing", "custom time", "availability"],
        "answer": "Yes, individual training is flexible and scheduled as per your convenience."
    },
    {
        "question": "What is Life Coaching?",
        "keywords": ["life coaching", "self improvement", "personal development", "goal setting"],
        "answer": "Life Coaching focuses on self-awareness, clarity, goal setting, and personal growth in all areas of life including career, relationships, and health."
    },
    {
        "question": "How is life coaching different from therapy?",
        "keywords": ["therapy", "difference", "counseling vs coaching", "mental health"],
        "answer": "Unlike therapy, which focuses on healing past trauma, life coaching is action-oriented and future-focused."
    },
    {
        "question": "Who is Executive Coaching for?",
        "keywords": ["executive", "managers", "leaders", "leadership coaching"],
        "answer": "Mid to senior-level professionals aiming to enhance their leadership, communication, and strategic decision-making skills."
    },
    {
        "question": "Do you coach department heads or team leaders?",
        "keywords": ["team leader", "department head", "coaching leaders", "team coaching"],
        "answer": "Absolutely. We specialize in coaching leaders to become more effective and aligned with organizational goals."
    },
    {
        "question": "How do I enroll in a program?",
        "keywords": ["enroll", "admission", "register", "join", "apply"],
        "answer": "Visit our website and navigate to the desired course page, or contact us directly through our inquiry form."
    },
    {
        "question": "Is there a demo or trial available?",
        "keywords": ["demo", "trial", "sample session", "free session"],
        "answer": "Demo sessions are available upon request, especially for corporate partnerships."
    },
    {
        "question": "What makes My Corporate School unique?",
        "keywords": ["unique", "why choose", "difference", "strengths"],
        "answer": "Our trainers are seasoned professionals with real-world experience, and our programs are practical, hands-on, and outcome-driven."
    },
    {
        "question": "What is the duration of your programs?",
        "keywords": ["duration", "length", "how long", "time frame"],
        "answer": "Depending on the course, durations range from a few days to several weeks."
    },
    {
        "question": "Where are your sessions conducted?",
        "keywords": ["location", "venue", "where", "session place", "training location"],
        "answer": "Sessions can be held at your office premises, online via video conferencing, or in our partnered learning centers."
    }]

# --- 3. Initialize Gemini Model ---
model = genai.GenerativeModel('gemini-1.5-pro')

# --- 4. Chatbot Logic ---
def get_chatbot_response(user_query):
    lower_case_query = user_query.lower()
    for faq in knowledge_base:
        if any(keyword in lower_case_query for keyword in faq["keywords"]) or lower_case_query in faq["question"].lower():
            return faq["answer"]

    try:
        kb_context = "\n\n".join([f"Q: {item['question']}\nA: {item['answer']}" for item in knowledge_base])
        prompt = f"""
        Context:\n{kb_context}\n
        Question: {user_query}

        If not found, suggest visiting the website.
        """

        response = model.generate_content(prompt)

        if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
            return response.candidates[0].content.parts[0].text
        else:
            return "I'm having trouble connecting right now. Please try again later."

    except Exception as e:
        print(f"Gemini API error: {e}")
        return "Oops! Something went wrong. Please try again."

# --- 5. Flask Setup ---
app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return "<h2>My Corporate School Chatbot Backend is Running.</h2><p>Send a POST request to <code>/chat</code> with JSON: {'message': 'your question'}.</p>"

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message')
    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    response_text = get_chatbot_response(user_message)
    return jsonify({"response": response_text})

# --- 6. Main Execution ---
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
