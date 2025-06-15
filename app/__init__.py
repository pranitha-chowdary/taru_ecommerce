from flask import Flask

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your-secret-key'  # change later

    @app.route('/')
    def home():
        return "Welcome to Taru E-Commerce"

    return app
