import pandas as pd
from sqlalchemy import create_engine

engine = create_engine("sqlite:///gog.db")
games = pd.read_sql("SELECT * FROM games", engine)
games["year"] = games["release_date"].str[:4]

# 1. Топ-10 разработчиков по числу игр
by_developer = games.assign(developer=games["developers"].str.split("; ")).explode("developer")

print(by_developer.groupby("developer").size().sort_values(ascending=False).head(10))

# 2. Средняя цена по жанрам
by_genre = games.assign(genre=games["genres"].str.split(", ")).explode("genre")
print(by_genre.groupby("genre")["price_final"].mean().sort_values(ascending=False).head(10))

# 3. Доля игр со скидкой по годам релиза
games["on_sale"] = games["price_final"] < games["price_base"]
print(games.groupby("year")["on_sale"].mean())

# 4. Средний рейтинг по годам (только игры, у которых больше 50 отзывов)
popular = games[games["reviews_count"] > 50]
print(popular.groupby("year")["rating"].mean())

# 5. Топ-10 игр по числу отзывов
print(games.sort_values("reviews_count", ascending=False)[["title", "reviews_count", "rating"]].head(10))