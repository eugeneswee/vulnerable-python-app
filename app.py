from flask import Flask, request, render_template_string
import subprocess
import pickle
import yaml

app = Flask(__name__)

# Deliberately vulnerable code for demonstration
@app.route('/')
def index():
    return '''
    <h1>Vulnerable Python Demo App</h1>
    <p>This app contains intentional vulnerabilities for security scanning demonstration.</p>
    <ul>
        <li><a href="/execute?cmd=ls">Command Execution Demo</a></li>
        <li><a href="/yaml">YAML Processing Demo</a></li>
    </ul>
    '''

@app.route('/execute')
def execute():
    # VULNERABILITY: Command injection
    cmd = request.args.get('cmd', 'echo "No command"')
    result = subprocess.call(cmd, shell=True)
    return f'Command executed: {cmd}'

@app.route('/yaml')
def yaml_process():
    # VULNERABILITY: Unsafe YAML loading
    data = request.args.get('data', 'key: value')
    parsed = yaml.load(data, Loader=yaml.FullLoader)
    return f'Parsed YAML: {parsed}'

@app.route('/pickle')
def pickle_load():
    # VULNERABILITY: Unsafe pickle loading
    data = request.args.get('data', '')
    if data:
        obj = pickle.loads(data.encode())
        return f'Unpickled: {obj}'
    return 'No data provided'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)


Create requirements.txt
Flask==1.1.4
PyYAML==5.3
Jinja2==2.11.2
Werkzeug==1.0.1
requests==2.20.0
urllib3==1.24.3
MarkupSafe==1.1.1


Create test_app.py
import unittest
from app import app

class TestApp(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_index(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Vulnerable Python Demo App', response.data)

    def test_execute_route(self):
        response = self.app.get('/execute?cmd=echo test')
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()


