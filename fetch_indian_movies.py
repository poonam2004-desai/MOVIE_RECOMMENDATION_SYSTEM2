import time
from typing import Dict, List, Optional

import pandas as pd
import requests
from nltk.stem.porter import PorterStemmer
from tqdm import tqdm

import db

TMDB_API_KEY = "a71b1374a6f462f48dc76e74d341ffba"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500"
LANGUAGES: Dict[str, str] = {"Hindi": "hi", "Marathi": "mr"}
MAX_PAGES = 100
SLEEP = 0.1
MAX_RETRIES = 3

DISCOVER_URL = "https://api.themoviedb.org/3/discover/movie"
DETAILS_URL = "https://api.themoviedb.org/3/movie/{movie_id}"
CREDITS_URL = "https://api.themoviedb.org/3/movie/{movie_id}/credits"
KEYWORDS_URL = "https://api.themoviedb.org/3/movie/{movie_id}/keywords"

ps = PorterStemmer()


def _request_json(session: requests.Session, url: str, params: Optional[dict] = None) -> Optional[dict]:
    """GET JSON with retries and timeout; return None on failure."""
    for attempt in range(MAX_RETRIES):
        try:
            resp = session.get(url, params=params, timeout=8)
            if resp.status_code == 200:
                return resp.json()
        except requests.RequestException:
            pass
        time.sleep(0.2 * (attempt + 1))
    return None


def fetch_movie_ids(lang_code: str) -> List[int]:
    """Fetch movie IDs for a language from TMDB Discover API."""
    session = requests.Session()
    movie_ids: List[int] = []

    for page in tqdm(range(1, MAX_PAGES + 1), desc=f"Discover {lang_code}", unit="page"):
        payload = _request_json(
            session,
            DISCOVER_URL,
            params={
                "api_key": TMDB_API_KEY,
                "with_original_language": lang_code,
                "sort_by": "popularity.desc",
                "page": page,
            },
        )
        if not payload:
            time.sleep(SLEEP)
            continue

        results = payload.get("results") or []
        for item in results:
            movie_id = item.get("id")
            if isinstance(movie_id, int):
                movie_ids.append(movie_id)

        time.sleep(SLEEP)

    return movie_ids


def fetch_movie_details(movie_id: int) -> Optional[dict]:
    """Fetch details, credits, and keywords for a movie ID."""
    session = requests.Session()
    details = _request_json(session, DETAILS_URL.format(movie_id=movie_id), params={"api_key": TMDB_API_KEY})
    if not details:
        return None

    credits = _request_json(session, CREDITS_URL.format(movie_id=movie_id), params={"api_key": TMDB_API_KEY})
    keywords = _request_json(session, KEYWORDS_URL.format(movie_id=movie_id), params={"api_key": TMDB_API_KEY})

    title = str(details.get("title") or "").strip()
    if not title:
        return None

    overview = details.get("overview") or ""
    genres = [g.get("name") for g in details.get("genres") or [] if g.get("name")]

    keyword_items = (keywords or {}).get("keywords") or (keywords or {}).get("results") or []
    keyword_names = [k.get("name") for k in keyword_items if k.get("name")][:10]

    cast_items = (credits or {}).get("cast") or []
    cast_names = [c.get("name") for c in cast_items if c.get("name")][:3]

    director = ""
    crew_items = (credits or {}).get("crew") or []
    for crew in crew_items:
        if crew.get("job") == "Director" and crew.get("name"):
            director = crew.get("name")
            break

    poster_path = details.get("poster_path")
    poster_url = f"{TMDB_IMAGE_BASE}{poster_path}" if poster_path else None

    return {
        "movie_id": details.get("id"),
        "title": title,
        "overview": overview,
        "genres": genres,
        "keywords": keyword_names,
        "cast": cast_names,
        "director": director,
        "poster_url": poster_url,
    }


def build_tags(overview: str, genres: List[str], keywords: List[str], cast: List[str], director: str) -> str:
    """Build tags using the same pipeline as model.py and apply Porter stemming."""
    tokens = []
    if overview:
        tokens.extend(str(overview).split())

    tokens.extend([g.replace(" ", "") for g in genres or []])
    tokens.extend([k.replace(" ", "") for k in keywords or []])
    tokens.extend([c.replace(" ", "") for c in (cast or [])[:3]])
    if director:
        tokens.append(str(director).replace(" ", ""))

    joined = " ".join(tokens).lower()
    return " ".join(ps.stem(word) for word in joined.split())


def main() -> None:
    """Fetch Hindi + Marathi movies, build tags, save files, and insert into DB."""
    all_rows: List[dict] = []
    counts: Dict[str, int] = {"Hindi": 0, "Marathi": 0}

    for label, code in LANGUAGES.items():
        movie_ids = fetch_movie_ids(code)
        lang_rows: List[dict] = []

        for movie_id in tqdm(movie_ids, desc=f"Details {label}", unit="movie"):
            try:
                details = fetch_movie_details(movie_id)
                time.sleep(SLEEP)
                if not details:
                    continue
                tags = build_tags(
                    details.get("overview", ""),
                    details.get("genres", []),
                    details.get("keywords", []),
                    details.get("cast", []),
                    details.get("director", ""),
                )
                if not details.get("title") or not tags.strip():
                    continue
                lang_rows.append(
                    {
                        "movie_id": details.get("movie_id"),
                        "title": details.get("title"),
                        "tags": tags,
                        "poster_url": details.get("poster_url"),
                        "language": code,
                    }
                )
            except Exception:
                continue

        counts[label] = len(lang_rows)
        all_rows.extend(lang_rows)

    df = pd.DataFrame(all_rows, columns=["movie_id", "title", "tags", "poster_url", "language"])
    if not df.empty:
        df["title"] = df["title"].fillna("").astype(str)
        df["tags"] = df["tags"].fillna("").astype(str)
        df = df[(df["title"].str.strip() != "") & (df["tags"].str.strip() != "")]
        df = df.drop_duplicates(subset=["title"], keep="first").reset_index(drop=True)

    inserted = db.insert_movies(df[["movie_id", "title", "tags", "poster_url", "language"]]) if not df.empty else 0

    for _, row in df.iterrows():
        try:
            db.update_movie_language(str(row.get("title")), str(row.get("language")))
        except Exception:
            continue

    df.to_csv("indian_movies.csv", index=False)
    df.to_pickle("indian_movies.pkl")

    print(f"Hindi: {counts.get('Hindi', 0)} | Marathi: {counts.get('Marathi', 0)} | Total inserted: {inserted}")


if __name__ == "__main__":
    main()