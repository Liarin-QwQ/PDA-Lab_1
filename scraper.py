import time
import requests
import pandas as pd
from sqlalchemy import create_engine, inspect

def parse_game(game):
    """Функция принимает один словарь game (одну игру из ответа API) и возвращает плоский словарь, который потом становится"""
    price = game.get("price")
    if not price or not price.get("finalMoney") or not price.get("baseMoney"):
        return None
    return {
        "id": game["id"],
        "title": game["title"],
        "release_date": game["releaseDate"],
        "developers": "; ".join(game["developers"] or []),
        "publishers": "; ".join(game["publishers"] or []),
        "genres": ", ".join(genre["name"] for genre in game["genres"] or []),
        "price_final": float(price["finalMoney"]["amount"]),
        "price_base": float(price["baseMoney"]["amount"]),
        "discount": price["discount"],
        "rating": game["reviewsRating"],
        "reviews_count": game["reviewsCount"],
    }

def save_games(games, engine):
    """Сохраняет новые игры в базу данных, исключая дубликаты."""
    df = pd.DataFrame(games).drop_duplicates("id")
    if inspect(engine).has_table("games"):
        old_ids = pd.read_sql("SELECT id FROM games", engine)["id"]
        df = df[~df["id"].isin(old_ids)]
    df.to_sql("games", engine, if_exists="append", index=False)
    return len(df)


def get_page(page, attempts=5):
    """Загружает страницу каталога GOG с повторными попытками при ошибках."""
    for attempt in range(attempts):
        try:
            response = requests.get(
                "https://catalog.gog.com/v1/catalog",
                params={
                    "limit": 48,
                    "order": "asc:title",
                    "productType": "in:game,pack,dlc,extras",
                    "page": page,
                    "countryCode": "US",
                    "locale": "en-US",
                    "currencyCode": "USD",
                },
                timeout=30,
            )
            return response.json()
        except (requests.exceptions.RequestException, ValueError):
            print("Ошибка загрузки страницы", page, "- попытка", attempt + 1, "из", attempts)
            time.sleep(2)
    raise RuntimeError(f"Не удалось загрузить страницу {page} после {attempts} попыток")


if __name__ == "__main__":
    games = []
    for page in range(1, 66):
        data = get_page(page)
        for game in data["products"]:
            parsed = parse_game(game)
            if parsed is not None:
                games.append(parsed)
        time.sleep(0.5)

    print("total:", len(games))
    print(games[0])

    for page in (1, 2, 3):
        print(page, get_page(page)["products"][0]["title"])

    engine = create_engine("sqlite:///gog.db")
    added = save_games(games, engine)
    print("added new games:", added)