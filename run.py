"""
CarePlus Hospital - Root Application Launcher
Launches the backend Flask application which serves the frontend portal.
"""
import sys
import os

# Set backend path
backend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend')
sys.path.insert(0, backend_path)

from app import create_app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_DEBUG', '1') == '1'
    print("==================================================")
    print(" CarePlus Hospital (HAMS) — System Starting       ")
    print(" Backend folder:  ./backend                       ")
    print(" Frontend folder: ./frontend                      ")
    print(f" Access URL:      http://127.0.0.1:{port}         ")
    print("==================================================")
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
