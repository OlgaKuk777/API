import vk_api
import time

def get_all_vk_data(user_id, token): #limit = 1000
    # Собирает посты и комменты со страницы (id пользователя + токен)
    session = vk_api.VkApi(token=token)
    vk = session.get_api() # установка сессии - связь с вк

    # посты
    posts = []

    offset = 0
    while True: #limt...
        try:
            new_posts = vk.wall.get(owner_id=user_id, count=100, offset=offset)["items"]
            # count - кол-во постов за один запрос; offset - "сдвиг"
            if not new_posts:
                break
            posts.extend(new_posts) # добавляет посты
            offset += 100
            time.sleep(0.5)

        except vk_api.exceptions.ApiError as e:
            if e.code == 15:  # Если доступ к стене запрещён
                print(f"Доступ запрещён для owner_id={user_id}. Пропускаем.")
                break
            else:
                raise e # Если другая ошибка, то ещё раз обрабатывает

    # комменты
    comments = []

    for post in posts:
        try:
            post_comments = vk.wall.getComments(owner_id=user_id, post_id=post["id"], count=50)["items"]
            comments.extend(post_comments) # добавляет комменты

        except vk_api.exceptions.ApiError as e:
            if e.code == 15:  # Если доступ к стене запрещён
                print(f"Доступ запрещён к комментариям поста {post['id']}. Пропускаем.")
            elif e.code == 212:  # Нет доступа к комментариям
                print(f"Нет доступа к комментариям поста {post['id']}. Пропускаем.")
            else:
                raise
        time.sleep(0.5)

    return posts, comments

def check_token_rights(token):
    # Проверка, имеет ли токен права на получение постов и комментов
    try:
        vk_session = vk_api.VkApi(token=token)
        vk = vk_session.get_api()

        posts = vk.wall.get(owner_id="интересующий id", count=1)["items"] # по 1му посту
        if posts:
            post_id = posts[0]["id"] # получает id, идёт далее
            try:
                vk.wall.getComments(owner_id="интересующий id", post_id=post_id, count=1)
                print("Токен имеет доступ к комментариям")
            except vk_api.exceptions.ApiError as e:
                if e.code == 15:  # Access denied
                    print("Токен не имеет доступа к комментариям")
        else:
            print("Нет доступных постов для проверки")

    except vk_api.exceptions.ApiError as e:
        if e.code == 7:  # Если токен не имеет прав
            print("Токен не имеет доступа к запрошенным данным")
        else:
            raise e
