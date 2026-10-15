from flask import Flask, render_template_string
from flask_socketio import SocketIO
import os
from openai import OpenAI

app = Flask(__name__)
app.config['SECRET_KEY'] = 'gizli-anahtar'
socketio = SocketIO(app, cors_allowed_origins="*")

# API anahtarını güvenli bir şekilde Render Environment ayarlarından okur
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
groq_client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=GROQ_API_KEY
)

sabit_mesaj = None

html_template = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Canlı Mesajlaşma Odası & Groq Bot</title>
    <script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>
    <style>
        body { font-family: Arial, sans-serif; background-color: #121212; color: #fff; margin: 0; padding: 20px; display: flex; justify-content: center; align-items: center; height: 100vh; box-sizing: border-box; }
        .chat-container { width: 100%; max-width: 450px; background: #1e1e1e; padding: 20px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.6); display: flex; flex-direction: column; height: 85vh; }
        h2 { text-align: center; color: #4CAF50; margin-top: 0; margin-bottom: 10px; font-size: 20px; }
        
        #pinned-box { background: #2c251e; border-left: 4px solid #ff9800; padding: 8px 12px; border-radius: 6px; margin-bottom: 10px; font-size: 14px; display: none; }
        #pinned-box strong { color: #ff9800; }

        #chat-box { flex: 1; overflow-y: auto; border: 1px solid #333; padding: 10px; background: #2a2a2a; border-radius: 8px; margin-bottom: 15px; display: flex; flex-direction: column; gap: 8px; }
        .message { background: #333; padding: 8px 12px; border-radius: 6px; max-width: 80%; word-break: break-word; }
        .message strong { color: #4CAF50; }
        .message.bot strong { color: #00bcd4; }
        .controls { display: flex; flex-direction: column; gap: 8px; }
        .input-row { display: flex; gap: 8px; }
        input[type="text"] { flex: 1; padding: 10px; border-radius: 6px; border: none; background: #333; color: white; outline: none; }
        button { padding: 10px 18px; border: none; background: #4CAF50; color: white; border-radius: 6px; cursor: pointer; font-weight: bold; }
        button:hover { background: #45a049; }
    </style>
</head>
<body>
<div class="chat-container">
    <h2>Mesajlaşma & Groq Bot</h2>
    
    <div id="pinned-box">
        📌 <strong>Sabitlenen Mesaj:</strong> <span id="pinned-text"></span>
    </div>

    <div id="chat-box"></div>
    
    <div class="controls">
        <div class="input-row">
            <input type="text" id="username" placeholder="Kullanıcı adın..." value="Ayaz">
        </div>
        <div class="input-row">
            <input type="text" id="message-input" placeholder="Mesaj yaz veya '@bot selam' de..." onkeypress="checkEnter(event)">
            <button onclick="sendMessage()">Gönder</button>
        </div>
    </div>
</div>
<script>
    const socket = io();

    socket.on('connect', () => {
        addMessage("Sistem", "Sunucuya başarıyla bağlandın!");
    });

    socket.on('mesaj_al', (data) => {
        addMessage(data.kullanici, data.mesaj, data.kullanici === "Groq Bot");
    });

    socket.on('sabit_guncelle', (mesaj) => {
        const pinnedBox = document.getElementById("pinned-box");
        const pinnedText = document.getElementById("pinned-text");
        if (mesaj) {
            pinnedText.innerText = mesaj;
            pinnedBox.style.display = "block";
        } else {
            pinnedBox.style.display = "none";
        }
    });

    function sendMessage() {
        const usernameInput = document.getElementById("username");
        const messageInput = document.getElementById("message-input");
        const kullanici = usernameInput.value.trim();
        const mesaj = messageInput.value.trim();

        if (mesaj !== "" && kullanici !== "") {
            socket.emit('mesaj_gonder', { kullanici: kullanici, mesaj: mesaj });
            messageInput.value = "";
        }
    }

    function checkEnter(event) {
        if (event.key === "Enter") { sendMessage(); }
    }

    function addMessage(user, msg, isBot = false) {
        const chatBox = document.getElementById("chat-box");
        const msgElement = document.createElement("div");
        msgElement.classList.add("message");
        if (isBot) msgElement.classList.add("bot");
        msgElement.innerHTML = `<strong>${user}:</strong> ${msg}`;
        chatBox.appendChild(msgElement);
        chatBox.scrollTop = chatBox.scrollHeight;
    }
</script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(html_template)

@socketio.on('mesaj_gonder')
def handle_message(data):
    global sabit_mesaj
    mesaj = data['mesaj']
    kullanici = data['kullanici']

    if mesaj.startswith('/sabitle '):
        sabit_mesaj = f"{kullanici}: {mesaj[9:]}"
        socketio.emit('sabit_guncelle', sabit_mesaj)
        return
    elif mesaj == '/unsabitle':
        sabit_mesaj = None
        socketio.emit('sabit_guncelle', None)
        return

    socketio.emit('mesaj_al', data)

    if mesaj.lower().startswith('@bot') or '@bot' in mesaj.lower():
        soru = mesaj.replace('@bot', '').strip()
        bot_yaniti = "Şu an yanıt oluşturulamadı."
        
        try:
            completion = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "Sen bu canlı mesajlaşma sunucusunun hızlı ve akıllı yapay zeka asistanısın. Türkçe, samimi ve net yanıtlar verirsin."},
                    {"role": "user", "content": soru}
                ],
                temperature=0.7,
            )
            bot_yaniti = completion.choices[0].message.content
        except Exception as e:
            bot_yaniti = f"Bir hata oluştu: {str(e)}"
        
        socketio.emit('mesaj_al', {'kullanici': 'Groq Bot', 'mesaj': bot_yaniti})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)
