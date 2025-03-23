import sqlite3
import pandas as pd


def calculate_correlation():
    #Подключение к бд и подгрузка
    conn = sqlite3.connect('/home/kuklelik/PycharmProjects/ProjectVK/vk_data.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT likes, views, text
        FROM posts
    ''')

    data = cursor.fetchall()
    conn.close()

    #create DataFrame
    df = pd.DataFrame(data, columns=['likes', 'views', 'text'])

    #Расчёт длины каждого поста
    df['text_length'] = df['text'].apply(len)

    #Получение корреляции
    corr_matrix = df[['likes', 'views', 'text_length']].corr()

    #Анализ корреляции
    def analyze_correlation(matrix):
        analysis = {}
        for i in range(len(matrix.columns)):
            for j in range(i + 1, len(matrix.columns)):
                c1 = matrix.columns[i]
                c2 = matrix.columns[j]
                corr_value = matrix.loc[c1, c2]
                if corr_value >= 0.7:
                    analysis[f"{c1} & {c2}"] = f"Сильная положительная корреляция ({corr_value:.2f})"
                elif corr_value >= 0.4 and corr_value < 0.7:
                    analysis[f"{c1} & {c2}"] = f"Умеренная положительная корреляция ({corr_value:.2f})"
                elif corr_value >= 0.1 and corr_value < 0.4:
                    analysis[f"{c1} & {c2}"] = f"Слабая положительная корреляция ({corr_value:.2f})"
                elif corr_value <= -0.7:
                    analysis[f"{c1} & {c2}"] = f"Сильная отрицательная корреляция ({corr_value:.2f})"
                elif corr_value <= -0.4 and corr_value > -0.7:
                    analysis[f"{c1} & {c2}"] = f"Умеренная отрицательная корреляция ({corr_value:.2f})"
                elif corr_value <= -0.1 and corr_value > -0.4:
                    analysis[f"{c1} & {c2}"] = f"Слабая отрицательная корреляция ({corr_value:.2f})"

                else:
                    analysis[f"{c1} & {c2}"] = f"Нейтральная корреляция ({corr_value:.2f})"
        return analysis

    correlation_analysis = analyze_correlation(corr_matrix)

    return corr_matrix.to_dict(), correlation_analysis




