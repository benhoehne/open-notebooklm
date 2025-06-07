import sys
import os
import datetime
import logging
from pathlib import Path

# Add your project directory to the sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
LOG_DIR = ROOT_DIR + '/logs'

path = Path(LOG_DIR)
path.mkdir(parents=True, exist_ok=True)
ct = datetime.datetime.now()
log_file = os.path.join(LOG_DIR, f"bah.log")

logging.basicConfig(
	filename=log_file,
	level=logging.DEBUG,
	format='%(asctime)s %(levelname)s %(message)s'
)

logger = logging.getLogger()
sys.stderr.write = logger.error
sys.stdout.write = logger.info

# Set the FLASK_APP environment variable
os.environ['FLASK_APP'] = 'app.py'

try:
	from app import app as application
	logger.info("WSGI application loaded successfully.")
except Exception as e:
	logger.error(f"Failed to load WSGI application: {e}")
	raise
