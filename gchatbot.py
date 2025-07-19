import os
import google.generativeai as genai
from flask import Flask, request, jsonify
from flask_cors import CORS
from pyngrok import ngrok
import threading
import time
import socket
from dotenv import load_dotenv

# --- 1. Load Environment Variables ---
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
NGROK_AUTH_TOKEN = os.getenv("NGROK_AUTH_TOKEN")

if not GEMINI_API_KEY:
    print("Error: GEMINI_API_KEY not set. Please set it in your environment variables.")
    exit()

if not NGROK_AUTH_TOKEN:
    print("Warning: NGROK_AUTH_TOKEN not set. Ngrok tunnel may not work.")

try:
    genai.configure(api_key=GEMINI_API_KEY)
    print("Gemini API configured successfully.")
except Exception as e:
    print(f"Error configuring Gemini API: {e}")
    exit()

try:
    ngrok.set_auth_token(NGROK_AUTH_TOKEN)
    print("Ngrok authentication token set successfully.")
except Exception as e:
    print(f"Error setting Ngrok auth token: {e}")

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
    }
]

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

# --- 6. Helper Functions ---
def find_available_port(start_port=5000, max_attempts=10):
    for i in range(max_attempts):
        port = start_port + i
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    raise IOError("No available ports found.")

def run_flask_app(port):
    app.run(port=port, debug=False, use_reloader=False)

def start_ngrok_tunnel(port):
    try:
        time.sleep(2)
        public_url = ngrok.connect(port).public_url
        print(f" * Ngrok Tunnel URL: {public_url}")
    except Exception as e:
        print(f"Ngrok error: {e}")

# --- 7. Main Execution ---
if __name__ == '__main__':
    try:
        flask_port = find_available_port()
        print(f"Running Flask on port: {flask_port}")

        flask_thread = threading.Thread(target=run_flask_app, args=(flask_port,), daemon=True)
        flask_thread.start()

        start_ngrok_tunnel(flask_port)

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("Shutting down.")
        ngrok.kill()

    except Exception as e:
        print(f"Fatal error: {e}")


import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)