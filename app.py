from flask import Flask, jsonify
from flask_cors import CORS

from controllers.bot_controller import bot_bp
from controllers.user_controller import user_bp

app = Flask(__name__)
CORS(app)

app.register_blueprint(bot_bp)
app.register_blueprint(user_bp)

@app.route('/')
def index():
    return jsonify({"API": "ONLINE"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)