import sys

# Добавляем путь к проекту
project_home = '/home/OlgaKuku777'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Импортируем приложение FastAPI
from main_1 import app

# Указываем, что это ASGI-приложение
application = app

