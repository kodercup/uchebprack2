from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import hashlib

app = Flask(__name__)
CORS(app)

def init_db():
    conn = sqlite3.connect('tasks.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        difficulty TEXT,
        day TEXT,
        assignee TEXT
    )''')
    conn.commit()
    conn.close()

init_db()

def hash_password(pwd):
    return hashlib.sha256(pwd.encode()).hexdigest()

@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.json
        username = data.get('username', '').strip()
        password = data.get('password', '')
        if not username or not password:
            return jsonify({'success': False, 'message': 'Заполните поля'})
        conn = sqlite3.connect('tasks.db')
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", 
                  (username, hash_password(password)))
        conn.commit()
        user_id = c.lastrowid
        conn.close()
        return jsonify({'success': True, 'user_id': user_id, 'username': username})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.json
        username = data.get('username', '').strip()
        password = data.get('password', '')
        conn = sqlite3.connect('tasks.db')
        c = conn.cursor()
        c.execute("SELECT id, username, password_hash FROM users WHERE username = ?", (username,))
        user = c.fetchone()
        conn.close()
        if user and user[2] == hash_password(password):
            return jsonify({'success': True, 'user_id': user[0], 'username': user[1]})
        return jsonify({'success': False, 'message': 'Неверные данные'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    try:
        user_id = request.args.get('user_id', type=int)
        if not user_id:
            return jsonify({'tasks': []})
        conn = sqlite3.connect('tasks.db')
        c = conn.cursor()
        c.execute("SELECT * FROM tasks WHERE user_id = ?", (user_id,))
        rows = c.fetchall()
        tasks = []
        for r in rows:
            tasks.append({
                'id': r[0],
                'user_id': r[1],
                'title': r[2],
                'description': r[3] or '',
                'difficulty': r[4] or 'средняя',
                'day': r[5] or 'понедельник',
                'assignee': r[6] or 'не назначен'
            })
        conn.close()
        return jsonify({'tasks': tasks})
    except Exception as e:
        return jsonify({'tasks': [], 'error': str(e)})

@app.route('/api/tasks', methods=['POST'])
def add_task():
    try:
        data = request.json
        conn = sqlite3.connect('tasks.db')
        c = conn.cursor()
        c.execute("""INSERT INTO tasks (user_id, title, description, difficulty, day, assignee) 
                     VALUES (?, ?, ?, ?, ?, ?)""",
                  (data['user_id'], data['title'], data.get('description', ''), 
                   data.get('difficulty', 'средняя'), data.get('day', 'понедельник'), 
                   data.get('assignee', 'не назначен')))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    try:
        user_id = request.args.get('user_id', type=int)
        conn = sqlite3.connect('tasks.db')
        c = conn.cursor()
        c.execute("DELETE FROM tasks WHERE id = ? AND user_id = ?", (task_id, user_id))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True, port=5000)