from flask import Flask, jsonify, request
import os
from flask_cors import CORS

# from components.factorio.main import factorio
from components.blueprints.main import blueprint_bp
from components.artboard.main import artboard_bp
from components.postcards.main import postcards_bp
from components.schematics.main import schematics_bp

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# app.register_blueprint(factorio)
app.register_blueprint(blueprint_bp)
app.register_blueprint(artboard_bp)
app.register_blueprint(postcards_bp)
app.register_blueprint(schematics_bp)

@app.before_request
def log_route_call():
    if os.environ.get('env') == 'derv':
        print(f"Route called: {request.method} {request.path}")

@app.route('/')
def index():
    return """
    <html>
        <head>
            <title>Hello, World!</title>
        </head>
        <body>
            <h1>Hello, World! Drawscape Vector API</h1>
        </body>h
    </html>
    """

@app.route('/api/hello', methods=['GET'])
def hello():
    return jsonify({"messages": "Hello, World!"})

if __name__ == '__main__':
    print("Starting Flask server...")
    # Get port from environment variable (Heroku) or default to 5000
    port = int(os.environ.get('PORT', 5000))
    print(f"Server is running on port {port}")
    print("Press CTRL+C to quit")
    
    # Disable debug mode in production
    debug_mode = os.environ.get('FLASK_ENV') != 'production'
    
    # Bind to 0.0.0.0 to make it accessible from outside the Docker container
    app.run(debug=debug_mode, host='0.0.0.0', port=port)