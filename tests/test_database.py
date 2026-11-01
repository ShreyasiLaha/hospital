"""
CarePlus Hospital - Root Test Launcher for Database Verification
"""
import sys
import os

backend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend')
sys.path.insert(0, backend_path)

from tests.test_database import run_tests

if __name__ == '__main__':
    run_tests()
