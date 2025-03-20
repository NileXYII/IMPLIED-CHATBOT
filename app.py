from flask import Flask, render_template, request, jsonify, session
import requests
import os
import uuid
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.urandom(24)  # For session management

# Replace with your actual OpenRouter API key
import os

API_KEY = os.getenv("OPENROUTER_API_KEY")
API_URL = os.getenv("OPENROUTER_API_URL")

if not API_KEY:
    raise ValueError("Missing API Key. Set OPENROUTER_API_KEY in the environment variables.")

if not API_URL:
    raise ValueError("Missing API URL. Set OPENROUTER_API_URL in the environment variables.")


@app.route('/')
def index():
    # Generate a unique session ID if not exists
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
        session['chat_history'] = []
    
    return render_template('landing.html')

@app.route('/chat')
def chat():
    # Ensure user has a session
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
        session['chat_history'] = []
    
    return render_template('chat.html', chat_history=session.get('chat_history', []))

@app.route('/send_message', methods=['POST'])
def send_message():
    user_message = request.json.get('message', '')
    
    if not user_message.strip():
        return jsonify({'error': 'Message cannot be empty'}), 400
    
    # Add user message to history
    timestamp = datetime.now().strftime("%H:%M")
    session['chat_history'] = session.get('chat_history', [])
    session['chat_history'].append({
        'role': 'user',
        'content': user_message,
        'timestamp': timestamp
    })
    
    # Prepare message history for API
    messages = [{"role": msg["role"], "content": msg["content"]} 
                for msg in session['chat_history']]
    
    # Call DeepSeek model via OpenRouter
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "deepseek/deepseek-chat",  # Use the DeepSeek model
        "messages": messages,
        "max_tokens": 1000
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        response.raise_for_status()  # Raise exception for HTTP errors
        
        bot_response = response.json()["choices"][0]["message"]["content"]
        
        # Add bot response to history
        session['chat_history'].append({
            'role': 'assistant',
            'content': bot_response,
            'timestamp': timestamp
        })
        
        session.modified = True  # Ensure session is saved
        
        return jsonify({
            'message': bot_response,
            'timestamp': timestamp
        })
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'error': f'Failed to get response: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True)