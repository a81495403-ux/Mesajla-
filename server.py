import os
from flask import Flask
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'gizli_anahtar_buraya'
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/')
def index():
    return "Mesajlaşma Sunucusu Çalışıyor!"

@socketio.on('connect')
def handle_connect():
    print("Bir kullanıcı bağlandı.")

@socketio.on('mesaj_gonder')
def handle_message(data):
    print(f"Gelen Mesaj: {data['kullanici']} -> {data['mesaj']}")
    emit('mesaj_al', data, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    print("Bir kullanıcı ayrıldı.")

if __name__ == '__main__':
    # Render'ın atayacağı portu otomatik yakalaması için:
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host='0.0.0.0', port=port)
