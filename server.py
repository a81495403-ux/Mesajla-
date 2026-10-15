from flask import Flask, render_template_string
from flask_socketio import SocketIO
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'gizli-anahtar'
socketio = SocketIO(app, cors_allowed_origins="*")

# Sabitlenen mesajı hafızada tutmak için değişken
sabit_mesaj = None

html_template = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Canlı Mesajlaşma Odası</title>
    <script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>
    <style>
        body { font-family: Arial, sans-serif; background-color: #121212; color: #fff; margin: 0; padding: 20px; display: flex; justify-content: center; align-items: center; height: 100vh; box-sizing: border-box; }
        .chat-container { width: 100%; max-width: 450px; background: #1e1e1e; padding: 20px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.6); display: flex; flex-direction: column; height: 85vh; }
        h2 { text-align: center; color: #4CAF50; margin-top: 0; margin-bottom: 10px; }
        
        /* Sabit Mesaj Alanı */
        #pinned-box { background: #2c251e; border-left: 4px solid #ff9800; padding: 8px 12px; border-radius: 6px; margin-bottom: 10px; font-size: 14px; display: none; }
        #pinned-box strong { color: #ff9800; }

        #chat-box { flex: 1; overflow-y: auto; border: 1px solid #333; padding: 10px; background: #2a2a2a; border-radius: 8px; margin-bottom: 15px; display: flex; flex-direction: column; gap: 8px; }
        .message { background: #333; padding: 8px 12px; border-radius: 6px; max-width: 80%; word-break: break-word; }
        .message strong { color: #4CAF50; }
        .controls { display: flex; flex-direction: column; gap: 8px; }
        .input-row { display: flex; gap: 8px; }
        input[type="text"] { flex: 1; padding: 10px; border-radius: 6px; border: none; background: #333; color: white; outline: none; }
        button { padding: 10px 18px; border: none; background: #4CAF50; color: white; border-radius: 6px; cursor: pointer; font-weight: bold; }
        button:hover { background: #45a049; }
    </style>
</head>
<body>
<div class="chat-container">
    <h2>Mesajlaşma Odası</h2>
    
    <!-- Sabitlenen Mesaj Kutusu -->
    <div id="pinned-box">
        📌 <strong>Sabitlenen Mesaj:</strong> <span id="pinned-text"></span>
    </div>

    <div id="chat-box"></div>
    
    <div class="controls">
        <div class="input-row">
            <input type="text" id="username" placeholder="Kullanıcı adın..." value="Ayaz">
        </div>
        <div class="input-row">
            <input type="text" id="message-input" placeholder="Mesajını yaz (/sabitle veya /unsabitle)..." onkeypress="checkEnter(event)">
            <button onclick="sendMessage()">Gönder</button>
        </div>
    </div>
</div>
<script>
    const socket = io();

    socket.on('connect', () => {
        addMessage("Sistem", "Sunucuya başarıyla bağlandın!");
    });

    // Normal mesajları almak için
    socket.on('mesaj_al', (data) => {
        addMessage(data.kullanici, data.mesaj);
    });

    // Sabitlenen mesajı güncellemek veya kaldırmak için
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

    function addMessage(user, msg) {
        const chatBox = document.getElementById("chat-box");
        const msgElement = document.createElement("div");
        msgElement.classList.add("message");
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

    # Eğer mesaj '/sabitle ' ile başlıyorsa
    if mesaj.startswith('/sabitle '):
        sabit_mesaj = f"{kullanici}: {mesaj[9:]}"
        socketio.emit('sabit_guncelle', sabit_mesaj)
    # Eğer mesaj tam olarak '/unsabitle' ise
    elif mesaj == '/unsabitle':
        sabit_mesaj = None
        socketio.emit('sabit_guncelle', None)
    else:
        # Normal mesajsa herkese ilet
        socketio.emit('mesaj_al', data)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)
