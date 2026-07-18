# Auto-add backend/ to sys.path so tests can import app.*
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
