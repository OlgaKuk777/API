import time

from fastapi import FastAPI, HTTPException

from vk_api_add import get_all_vk_data
from db import VkDatabase
from nlp_text import process_text
from statistics_correlation import calculate_correlation

import vk_api
import datetime
from collections import Counter

app = FastAPI()

# Moй токен
TOKEN = "ваш токен"
# Инициализация БД в main
db = VkDatabase()

def get_top_likers(user_id, token): # Получает топ лайкеров стены
    session = vk_api.VkApi(token=token)
    vk = session.get_api() # установка сессии - связь с вк

    # Получает Все посты
    posts = []
    offset = 0
    while True:
        new_posts = vk.wall.get(owner_id=user_id, count=100, offset=offset)["items"]
        if not new_posts:
            break
        posts.extend(new_posts)
        offset += 100
        time.sleep(0.5)

    # Список пользователей, поставивших лайки
    likers = {} # словарь
    for post in posts:
        try:
            post_likers = vk.likes.getList(type='post', owner_id=user_id, item_id=post["id"])["items"] # ищет лайкеров для каждого поста
            for liker in post_likers:
                if liker not in likers:
                    likers[liker] = set() # добавляется пользователь, ему задаётся мн-во в значение
                likers[liker].add(post["id"])
        except vk_api.exceptions.ApiError as e:
            print(f"Ошибка при получении лайков: {e}")

    # Подсчитывает топ-15 лайкеров
    likers_counter = Counter({user_id: len(post_ids) for user_id, post_ids in likers.items()}) # словарь, где ключ - юзер, значение - кол-во
    top_likers = likers_counter.most_common(15)

    # Фильтрует лайкеров по количеству лайков (больше 2х постов)
    filtered_top_likers = [(user_id, count) for user_id, count in top_likers if count > 2]

    if not filtered_top_likers: # если никто не лайкнул
        return []

    # Получает имена пользователей
    user_ids = [user_id for user_id, _ in top_likers] # извлекает id лайкеров
    users_info = vk.users.get(user_ids=user_ids, fields="first_name,last_name")

    top_likers_with_names = []
    for (user_id, count), user in zip(top_likers, users_info):
        top_likers_with_names.append({
            "id": user_id,
            "name": f"{user['first_name']} {user['last_name']}",
            "likes_count": count
        }) # так будет выглядеть в api

    return top_likers_with_names

@app.get("/")
async def get_posts():
    user_id = "интересующий id"
    posts, _ = get_all_vk_data(user_id, TOKEN)
    return {"posts": posts}


@app.get("/analyze/имя интересующего профиля или id")
async def analyze():
    try:
        user_id = "интересующий id"
        posts, comments = get_all_vk_data(user_id, TOKEN)

        if comments:  # если есть комменты в посте
            # безопасный доступ к комментатору; подсчёт кол-ва комментов; оставляет 5 лучших/ id + кол-во комментов
            top_authors_ids = Counter(c.get("from_id") for c in comments if "from_id" in c).most_common(5)

            user_ids = [user_id for user_id, _ in top_authors_ids]  # из лучших получает их данные
            users_info_list = vk_api.VkApi(token=TOKEN).get_api().users.get(user_ids=user_ids,
                                                                            fields="first_name,last_name,bdate,last_seen")

            users_info = {user["id"]: user for user in users_info_list}

            top_authors = []
            for user_id, count in top_authors_ids:
                if user_id in users_info:  # Проверяем, есть ли информация о пользователе
                    user = users_info[user_id]
                    user_comments = [c["text"] for c in comments if
                                     c.get("from_id") == user_id]  # извлекает тексты комментов

                    # преобразование времени в формат Unix
                    last_seen_unix = user.get("last_seen", {}).get("time", 0)
                    if last_seen_unix:
                        last_seen_datetime = datetime.datetime.fromtimestamp(last_seen_unix)
                        last_seen = last_seen_datetime.strftime('%d-%m-%Y %H:%M:%S')
                    else:
                        last_seen = "Не указано"

                    top_authors.append({
                        "id": user_id,
                        "name": f"{user['first_name']} {user['last_name']}",
                        "bdate": user.get("bdate", "Не указано"),
                        "last_seen": last_seen,
                        "comments_count": count,
                        "comments": user_comments[:5]
                    })
                else:
                    # Если информации о пользователе нет, добавляем информацию об ошибке
                    top_authors.append({
                        "id": user_id,
                        "name": "Информация о пользователе не найдена",
                        "bdate": "Не указано",
                        "last_seen": "Не указано",
                        "comments_count": count,
                        "comments": []
                    })
        else:
            top_authors = []

        # Считаем самые частотные слова
        all_text = " ".join([post["text"] for post in posts])  # объединяет посты в строчку
        word_freq = process_text(all_text).most_common(20)  # обработка и подсчёт

        # Получаем топ-15 пользователей по лайкам
        top_likers = get_top_likers("интересующий id", TOKEN)

        corr_matrix, correlation_analysis = calculate_correlation()
        return {
            "top_words": word_freq,
            "top_authors": top_authors,
            "longest_posts": sorted(posts, key=lambda x: len(x["text"]), reverse=True)[:5],
            "top_likers": top_likers,
            "corr_matrix": corr_matrix,
            "correlation_analysis": correlation_analysis
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при обработке запроса: {e}")  # ЕСЛИ ОШИБКА 500


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, workers=1)
