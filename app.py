from flask import Flask, render_template
from flask_login import LoginManager
from models import db
from models.user import User
from config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize extensions
    db.init_app(app)
    
    # Login manager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Register blueprints
    from routes.auth_routes import auth_bp
    from routes.book_routes import book_bp
    from routes.member_routes import member_bp
    from routes.transaction_routes import transaction_bp
    from routes.admin_routes import admin_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(book_bp)
    app.register_blueprint(member_bp)
    app.register_blueprint(transaction_bp)
    app.register_blueprint(admin_bp)
    
    @app.route('/')
    def index():
        return render_template('index.html')
    
    return app

if __name__ == '__main__':
    app = create_app()
    
    with app.app_context():
        db.create_all()
        
        # Check if we need to create dummy data
        from utils.seed_data import create_dummy_data
        if User.query.count() == 0:
            create_dummy_data()
            print("Dummy data created successfully!")
    
    app.run(debug=True)