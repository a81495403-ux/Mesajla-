from flask import Flask, render_template_string
from flask_socketio import SocketIO
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'gizli-anahtar'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode=None)

# Basit bir test rotası (Tarayıcıdan açıldığında sunucunun çalıştığını gösterir)
@app.route('/')
def index():
    return "Mesajlaşma Sunucusu Çalışıyor!"

# Mesaj gönderildiğinde tetiklenen olay
@socketio.on('mesaj_gonder')
def handle_message(data):
    print(f"Mesaj alındı: {data}")
    # Gelen mesajı odadaki herkese (connected clients) tekrar yayınla
    socketio.emit('mesaj_al', data)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)
