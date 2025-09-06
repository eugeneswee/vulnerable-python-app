#!/usr/bin/env python3
"""
Intentionally Vulnerable Python Web Application
For DevSecOps Security Testing Purposes
"""

import os
import sqlite3
import subprocess
import pickle
import base64
from flask import Flask, request, render_template_string, session, redirect, url_for
import hashlib
import secrets

app = Flask(__name__)
app.secret_key = "hardcoded-secret-key-123"  # Security Issue: Hardcoded secret

# Security Issue: SQL Injection vulnerability
def init_db():
    conn = sqlite3.connect('vulnerable.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT,
            password TEXT,
            role TEXT DEFAULT 'user'
        )
    ''')
    # Security Issue: Default admin credentials
    cursor.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES ('admin', 'admin123', 'admin')")
    conn.commit()
    conn.close()

@app.route('/')
def home():
    return render_template_string('''
    <h1>Vulnerable Python App</h1>
    <p>Environment: {{ env }}</p>
    <ul>
        <li><a href="/login">Login</a></li>
        <li><a href="/search">Search Users</a></li>
        <li><a href="/upload">File Upload</a></li>
        <li><a href="/execute">Command Execution</a></li>
        <li><a href="/deserialize">Data Processing</a></li>
    </ul>
    ''', env=os.getenv('ENVIRONMENT', 'development'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Security Issue: SQL Injection
        conn = sqlite3.connect('vulnerable.db')
        cursor = conn.cursor()
        query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
        cursor.execute(query)
        user = cursor.fetchone()
        conn.close()
        
        if user:
            session['user'] = username
            return f"Welcome {username}!"
        else:
            return "Invalid credentials"
    
    return render_template_string('''
    <form method="post">
        Username: <input type="text" name="username"><br>
        Password: <input type="password" name="password"><br>
        <input type="submit" value="Login">
    </form>
    ''')

@app.route('/search')
def search():
    query = request.args.get('q', '')
    if query:
        # Security Issue: SQL Injection
        conn = sqlite3.connect('vulnerable.db')
        cursor = conn.cursor()
        sql = f"SELECT username, role FROM users WHERE username LIKE '%{query}%'"
        cursor.execute(sql)
        results = cursor.fetchall()
        conn.close()
        return f"Results: {results}"
    
    return render_template_string('''
    <form>
        Search Users: <input type="text" name="q">
        <input type="submit" value="Search">
    </form>
    ''')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        # Security Issue: Unrestricted file upload
        if 'file' in request.files:
            file = request.files['file']
            filename = file.filename
            file.save(f'uploads/{filename}')  # No path validation
            return f"File {filename} uploaded successfully"
    
    return render_template_string('''
    <form method="post" enctype="multipart/form-data">
        <input type="file" name="file">
        <input type="submit" value="Upload">
    </form>
    ''')

@app.route('/execute')
def execute():
    cmd = request.args.get('cmd', 'ls')
    # Security Issue: Command injection
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return f"<pre>{result.stdout}</pre>"

@app.route('/deserialize')
def deserialize():
    data = request.args.get('data', '')
    if data:
        try:
            # Security Issue: Insecure deserialization
            decoded = base64.b64decode(data)
            obj = pickle.loads(decoded)
            return f"Processed: {obj}"
        except Exception as e:
            return f"Error: {e}"
    
    return "Send base64 encoded pickle data via 'data' parameter"

@app.route('/health')
def health():
    return {"status": "healthy", "version": "1.0.0"}

if __name__ == '__main__':
    init_db()
    os.makedirs('uploads', exist_ok=True)
    app.run(host='0.0.0.0', port=5000, debug=True)  # Security Issue: Debug mode in production
