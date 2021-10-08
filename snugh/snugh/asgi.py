import os
from pathlib import Path

import dotenv
from django.core.asgi import get_asgi_application

BASE_DIR = Path(__file__).resolve().parent.parent

dotenv.read_dotenv(BASE_DIR / '.env')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'snugh.settings.prod')

application = get_asgi_application()
