import sqlite3
from datetime import datetime
from threading import Lock
import time

class VkDatabase:
    def __init__(self, db_name='vk_data.db'):
        self.conn = sqlite3.connect(
            db_name,
            check_same_thread=False,
            timeout=20  # Увеличиваем таймаут ожидания блокировки
        )
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self.conn.execute("PRAGMA busy_timeout=5000;")  # Ожидание разблокировки 5 секунд
        self.cursor = self.conn.cursor()
        self.db_lock = Lock()
        self._create_tables()

    def _create_tables(self):
        with self.db_lock:
            try:
                self.cursor.execute('''
                    CREATE TABLE IF NOT EXISTS posts (
                        owner_id INTEGER,
                        post_id INTEGER,
                        text TEXT,
                        post_date DATETIME,
                        likes INTEGER,
                        views INTEGER,
                        comments_count INTEGER,
                        PRIMARY KEY (owner_id, post_id)
                    )
                ''')
                self.conn.commit()
            except Exception as e:
                print(f"Ошибка создания таблиц: {e}")

    def save_posts_batch(self, posts_data: list, owner_id: int):
        if not posts_data:
            print("Нет данных для сохранения")
            return

        with self.db_lock:
            for attempt in range(5):  # Повторные попытки при блокировке
                try:
                    self.cursor.executemany('''
                        INSERT OR REPLACE INTO posts 
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', [
                        (
                            owner_id,
                            post.get('id'),
                            post.get('text', ''),
                            datetime.fromtimestamp(post.get('date', 0)),
                            post.get('likes', {}).get('count', 0),
                            post.get('views', {}).get('count', 0),
                            post.get('comments', {}).get('count', 0)
                        ) for post in posts_data
                    ])
                    self.conn.commit()
                    print(f"Успешно сохранено {len(posts_data)} постов")
                    return
                except sqlite3.OperationalError as e:
                    if "database is locked" in str(e):
                        print(f"Попытка {attempt+1}/5: База данных заблокирована, повторяю...")
                        time.sleep(0.5 * (attempt + 1))
                    else:
                        raise
                except Exception as e:
                    print(f"Критическая ошибка сохранения: {e}")
                    raise

    def __del__(self):
        if self.conn:
            self.conn.close()

# Остальные методы класса остаются без изменений
