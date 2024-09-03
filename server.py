from flask      import Flask, jsonify
from flask_cors import CORS

from components.factorio.main import factorio

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

app.register_blueprint(factorio)

@app.route('/')
def index():
    return """
    <html>
        <head>
            <title>Hello, World!</title>
        </head>
        <body>
            <h1>Hello, World! Drawscape API</h1>
        </body>h
    </html>
    """

@app.route('/api/hello', methods=['GET'])
def hello():
    return jsonify({"messages": "Hello, World!"})

if __name__ == '__main__':
    print("Starting Flask server...")
    print(f"Server is running on http://127.0.0.1:5000")
    print("Press CTRL+C to quit")
    app.run(debug=True)