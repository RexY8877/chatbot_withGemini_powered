import os
import Knowledge_Base
from Knowledge_Base import knowledge_base
import google.generativeai as genai
from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
import time
import socket
from dotenv import load_dotenv
def format_knowledge_base(kb):
    return "\n\n".join([f"Q: {item['question']}\nA: {item['answer']}" for item in kb])

kb_string = format_knowledge_base(Knowledge_Base.knowledge_base)

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

# --- 2. Initialize Gemini Model ---
model = genai.GenerativeModel('gemini-1.5-flash-latest')

# --- 3. Chatbot Logic ---
def get_chatbot_response(user_query):
    lower_case_query = user_query.lower()
    for faq in knowledge_base:
        if any(keyword in lower_case_query for keyword in faq["keywords"]) or lower_case_query in faq["question"].lower():
            return faq["answer"]

    try:
        kb_context = "\\n\\n".join([f"Q: {item['question']}\\nA: {item['answer']}" for item in Knowledge_Base.knowledge_base])
        prompt = f"""
Context:
{kb_context}

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


# --- 4. Flask Setup ---
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


# --- 5. Main Execution ---
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
