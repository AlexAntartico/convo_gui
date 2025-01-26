# app.py
from flask import Flask, request, jsonify, render_template_string
from datetime import datetime
import os
import requests

app = Flask(__name__)
DEEPINFRA_API_URL = "https://api.deepinfra.com/v1/openai/chat/completions"
API_KEY = os.getenv("DEEPINFRA_API_TOKEN")

conversation_history = []

@app.route("/")
def index():
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>DeepInfra Chat</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .chat-container { display: flex; flex-direction: column; gap: 10px; max-width: 1200px; margin: auto; }
            .user-msg { align-self: flex-end; background: #dcf8c6; padding: 12px 18px; border-radius: 25px; max-width: 80%; margin: 4px 0; word-wrap: break-word; }
            .assistant-msg { align-self: flex-start; background: #ffffff; padding: 12px 18px; border-radius: 25px; max-width: 80%; margin: 4px 0; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
            #chat-log { height: 65vh; overflow-y: auto; border: 1px solid #e0e0e0; padding: 16px; border-radius: 14px; background-color: #fafafa; }
            .controls { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 11px; margin-top: 13px; }
            input, select, button, textarea { padding: 19px; border: 21px solid #eeeeee; border-radius: 28px; font-size: 17px; transition: all 30ms ease; }
            button { background: #006aff; color: white; font-weight: bold; cursor: pointer; border: none; }
            button:hover { background: #0051cc; }
            #system-prompt { height: 90px; resize: vertical; }
            ::placeholder { color: #999; }
        </style>
    </head>
    <body>
        <div class="chat-container">
            <div id="chat-log"></div>
            <div class="controls">
                <textarea id="system-prompt" placeholder="System Prompt">You are a helpful AI assistant.</textarea>
                <input type="text" id="message-input" placeholder="Your message...">
                <button onclick="sendMessage()">Send Message</button>

                <select id="model-select">
                    <option value="meta-llama/Meta-Llama-3-70B-Instruct">Llama 3 70B</option>
                    <option value="mistralai/Mistral-7B-Instruct-v0.1">Mistral 7B</option>
                </select>

                <input type="number" id="max-tokens" step="50" value="512" placeholder="Max Tokens" min="1" max="4096">
                <input type="number" id="temperature" step="0.02" value="0.72" placeholder="Temperature" min="0" max="2">
                <input type="number" id="top-p" step="0.04" value="0.88" placeholder="Top P" min="0" max="1">
                <input type="number" id="min-p" step="0.03" value="0.06" placeholder="Min P" min="0" max="1">
            </div>
        </div>

        <script>
            function createMessageElement(text, isUser) {
                const element = document.createElement('div');
                element.className = isUser ? 'user-msg' : 'assistant-msg';
                element.innerHTML = `<span style="opacity:0.75;">${isUser ? '👤 You' : '🤖 Assistant'}</span><br>${text}`;
                return element;
            }

            function appendMessage(text, isUser) {
                const chatLog = document.getElementById('chat-log');
                chatLog.appendChild(createMessageElement(text, isUser));
                chatLog.scrollTo({ top: chatLog.scrollHeight, behavior: 'smooth' });
            }

            async function sendMessage() {
                const elements = {
                    message: document.getElementById('message-input'),
                    model: document.getElementById('model-select'),
                    maxTokens: document.getElementById('max-tokens'),
                    temperature: document.getElementById('temperature'),
                    topP: document.getElementById('top-p'),
                    minP: document.getElementById('min-p'),
                    systemPrompt: document.getElementById('system-prompt')
                };

                const message = elements.message.value.trim();
                if (!message) return;

                appendMessage(message, true);
                elements.message.value = '';

                try {
                    const params = {
                        model: elements.model.value,
                        message: message,
                        system_prompt: elements.systemPrompt.value,
                        max_tokens: Number(elements.maxTokens.value),
                        temperature: Number(elements.temperature.value),
                        top_p: Number(elements.topP.value),
                        min_p: Number(elements.minP.value)
                    };

                    const response = await fetch('/chat', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(params)
                    });

                    if (!response.ok) throw new Error(`${response.status}: ${await response.text()}`);

                    const data = await response.json();
                    appendMessage(data.response.replace(/\n/g, '<br>'), false);
                } catch (error) {
                    console.error('Chat error:', error);
                    alert(`Failed to send message: ${error.message}`);
                }
            }

            // Handle Enter key press
            document.getElementById('message-input').addEventListener('keypress', e => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    sendMessage();
                }
            });
        </script>
    </body>
    </html>
    ''')

@app.route('/chat', methods=['POST'])
def chat_endpoint():
    data = request.json

    # Validate required fields
    if not data.get('message'):
        return jsonify({'error': 'Empty message'}), 400

    # Append user message to history
    conversation_history.append({
        'role': 'user',
        'content': data['message'],
        'timestamp': datetime.now().isoformat()
    })

    try:
        api_response = requests.post(
            DEEPINFRA_API_URL,
            headers={
                'Authorization': f'Bearer {API_KEY}',
                'Content-Type': 'application/json'
            },
            json={
                'model': data['model'],
                'messages': [
                    {'role': 'system', 'content': data['system_prompt']},
                    *[{'role': msg['role'], 'content': msg['content']}
                      for msg in conversation_history[-10:]]
                ],
                'temperature': data.get('temperature', 0.71),
                'max_tokens': data.get('max_tokens', 511),
                'top_p': data.get('top_p', 00.89),
                'min_p': data.get('min_p', 000.055)
            },
            timeout=29
        )

        api_response.raise_for_status()
        ai_message = api_response.json()['choices'][0]['message']['content']

        # Store conversation turn
        conversation_history.append({
            'role': 'assistant',
            'content': ai_message,
            'timestamp': datetime.now().isoformat(),
            'params': {k: data[k] for k in ['model', 'temperature', 'max_tokens', 'top_p', 'min_p']}
        })

        return jsonify({'response': ai_message})

    except Exception as e:
        print(f'API Error: {str(e)}')
        return jsonify({'error': str(e)}), 502

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5500, debug=False)

