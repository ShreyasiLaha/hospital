"""
CarePlus Hospital - Configuration Settings
Loads configuration parameters from environment variables with hospital_db as default.
"""
import os
from dotenv import load_dotenv

# Load .env file if available
load_dotenv()

class Config:
    """Base application configuration."""
    SECRET_KEY = os.getenv('SECRET_KEY', 'careplus_hospital_super_secret_key_2026')
    
    # Database Type: 'mysql' or 'auto' (tries MySQL hospital_db, falls back to local SQLite if offline)
    DB_TYPE = os.getenv('DB_TYPE', 'auto')
    
    # MySQL Database Settings
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_NAME = os.getenv('DB_NAME', 'hospital_db')
    DB_PORT = int(os.getenv('DB_PORT', 3306))
    
    # SQLite Database Fallback Path (points to authoritative database in backend/database)
    _backend_db = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend', 'database', 'hospital_db.sqlite')
    SQLITE_PATH = _backend_db if os.path.exists(os.path.dirname(_backend_db)) else os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database', 'hospital_db.sqlite')
    
    # Application Branding
    HOSPITAL_NAME = "CarePlus Hospital"
    HOSPITAL_TAGLINE = "Excellence in Healthcare & Compassionate Patient Management"
    DEBUG = os.getenv('FLASK_DEBUG', '1') == '1'
