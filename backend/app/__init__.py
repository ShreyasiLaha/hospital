"""
CarePlus Hospital - Backend Application Factory
Configured to serve templates and static assets from the frontend/ folder.
"""
import os
from flask import Flask, render_template, session, redirect, url_for
from config import Config
from app.db import close_db

def create_app(config_class=Config):
    """Factory function to configure and return the Flask application instance."""
    # Resolve frontend template and static paths
    backend_app_dir = os.path.dirname(os.path.abspath(__file__))       # .../backend/app
    project_root = os.path.abspath(os.path.join(backend_app_dir, '..', '..')) # .../hospital
    frontend_dir = os.path.join(project_root, 'frontend')

    template_dir = os.path.join(frontend_dir, 'templates')
    static_dir = os.path.join(frontend_dir, 'static')

    app = Flask(
        __name__,
        template_folder=template_dir,
        static_folder=static_dir
    )
    app.config.from_object(config_class)

    # Register Database teardown
    app.teardown_appcontext(close_db)

    # Context processor to make current user session and alerts available globally in templates
    @app.context_processor
    def inject_user():
        unread_notifs = 0
        if 'user_id' in session:
            try:
                from app.db import query_db
                notif_row = query_db("SELECT COUNT(*) as cnt FROM notifications WHERE user_id = %s AND is_read = 0", (session['user_id'],), one=True)
                if notif_row:
                    unread_notifs = notif_row['cnt']
            except Exception:
                unread_notifs = 0

        return {
            'is_logged_in': 'user_id' in session,
            'current_user_name': session.get('full_name'),
            'current_user_role': session.get('role'),
            'current_user_id': session.get('user_id'),
            'unread_notifications_count': unread_notifs,
            'hospital_name': app.config.get('HOSPITAL_NAME', 'CarePlus Hospital')
        }

    # Public Landing Page Route
    @app.route('/')
    def index():
        if 'user_id' in session:
            role = session.get('role')
            dashboard_map = {
                'admin': 'admin.dashboard',
                'doctor': 'doctor.dashboard',
                'receptionist': 'receptionist.dashboard',
                'patient': 'patient.dashboard'
            }
            return redirect(url_for(dashboard_map.get(role, 'auth.login')))
        return render_template('index.html')

    # Register Blueprints
    from app.routes.auth import auth_bp
    from app.routes.patient import patient_bp
    from app.routes.doctor import doctor_bp
    from app.routes.receptionist import receptionist_bp
    from app.routes.admin import admin_bp
    from app.routes.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(patient_bp)
    app.register_blueprint(doctor_bp)
    app.register_blueprint(receptionist_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)

    # Register Error Handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html'), 500

    return app
