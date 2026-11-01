"""
CarePlus Hospital - Backend Application Runner
Executes Flask server directly from within the backend/ folder.
"""
import sys
import os

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app

app = create_app()

if __name__ == '__main__':
    print("==================================================")
    print(" CarePlus Hospital - Backend Server Starting...   ")
    print(" Frontend templates: ../frontend/templates       ")
    print(" Frontend static:    ../frontend/static          ")
    print(" Access Web Portal:  http://127.0.0.1:5000        ")
    print("==================================================")
    app.run(host='127.0.0.1', port=5000, debug=True)
