import os
from pathlib import Path

import dotenv
from django.core.wsgi import get_wsgi_application

BASE_DIR = Path(__file__).resolve().parent.parent

dotenv.read_dotenv(BASE_DIR / '.env')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'snugh.settings.prod')

application = get_wsgi_application()
