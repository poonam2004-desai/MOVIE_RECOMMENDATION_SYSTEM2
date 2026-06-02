import os
import sqlite3
from typing import Any, Dict, List, Optional

import bcrypt
import pandas as pd

DB_PATH = os.path.join(os.path.dirname(__file__), "movies.db")


def create_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = OFF;")
    return conn


def connect_db():
    return create_connection()


def create_movies_table() -> None:
    conn = create_connection()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS movies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                movie_id INTEGER,
                title TEXT UNIQUE,
                tags TEXT,
                poster_url TEXT,
                language TEXT DEFAULT 'en'
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def create_users_table() -> None:
    conn = create_connection()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                email TEXT UNIQUE,
                password TEXT
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def create_watchlist_table() -> None:
    conn = create_connection()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS watchlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                movie_id INTEGER,
                UNIQUE(user_id, movie_id),
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY(movie_id) REFERENCES movies(id) ON DELETE CASCADE
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    create_movies_table()
    create_users_table()
    create_watchlist_table()

    try:
        conn = create_connection()
        conn.execute("ALTER TABLE movies ADD COLUMN language TEXT DEFAULT 'en'")
        conn.commit()
    except Exception:
        pass
    finally:
        try:
            conn.close()
        except Exception:
            pass


def reset_watchlist_table() -> None:
    """Drop and recreate watchlist table if corrupted."""
    conn = create_connection()
    try:
        conn.execute("DROP TABLE IF EXISTS watchlist")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS watchlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                movie_id INTEGER,
                UNIQUE(user_id, movie_id)
            )
            """
        )
        conn.commit()
        print("Watchlist table reset successfully.")
    finally:
        conn.close()


def _row_to_dict(row: Optional[sqlite3.Row]) -> Optional[Dict[str, Any]]:
    if row is None:
        return None
    return dict(row)


def _fetch_all(query: str, params: tuple = ()) -> List[Dict[str, Any]]:
    conn = create_connection()
    try:
        cur = conn.cursor()
        cur.execute(query, params)
        return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


def _fetch_one(query: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
    conn = create_connection()
    try:
        cur = conn.cursor()
        cur.execute(query, params)
        return _row_to_dict(cur.fetchone())
    finally:
        conn.close()


def insert_movies(df: pd.DataFrame) -> int:
    """Insert movies from a DataFrame into the movies table."""
    if df is None or df.empty:
        return 0

    init_db()
    conn = create_connection()
    inserted = 0
    try:
        cur = conn.cursor()
        has_language = "language" in df.columns
        for _, row in df.iterrows():
            movie_id_value = row.get("movie_id")
            try:
                movie_id = int(movie_id_value) if movie_id_value not in (None, "") else None
            except (TypeError, ValueError):
                movie_id = None

            title = str(row.get("title") or "").strip()
            tags = str(row.get("tags") or "").strip()
            poster = row.get("poster_url") if "poster_url" in row.index else None
            language = str(row.get("language") or "en").strip() if has_language else "en"

            if not title:
                continue

            try:
                if has_language:
                    cur.execute(
                        "INSERT OR IGNORE INTO movies (movie_id, title, tags, poster_url, language) VALUES (?, ?, ?, ?, ?)",
                        (movie_id, title, tags, poster, language or "en"),
                    )
                else:
                    cur.execute(
                        "INSERT OR IGNORE INTO movies (movie_id, title, tags, poster_url) VALUES (?, ?, ?, ?)",
                        (movie_id, title, tags, poster),
                    )
                if cur.rowcount:
                    inserted += 1
            except sqlite3.DatabaseError:
                continue

        conn.commit()
        return inserted
    finally:
        conn.close()


def get_all_movies() -> List[Dict[str, Any]]:
    init_db()
    return _fetch_all("SELECT id, movie_id, title, tags, poster_url, language FROM movies ORDER BY id ASC")


def get_movies_by_language(language: str) -> List[Dict[str, Any]]:
    """Return all movies filtered by language code."""
    init_db()
    return _fetch_all(
        "SELECT id, movie_id, title, tags, poster_url, language FROM movies WHERE language = ? ORDER BY id DESC",
        (language,),
    )


def update_movie_language(title: str, language: str) -> bool:
    """Update language for a movie by title when language is missing or default."""
    conn = create_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE movies SET language = ? WHERE LOWER(title) = LOWER(?) AND (language IS NULL OR language = 'en')",
            (language, title),
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def get_all_users() -> List[Dict[str, Any]]:
    init_db()
    return _fetch_all("SELECT id, username, email FROM users ORDER BY id ASC")


def get_total_users() -> int:
    init_db()
    conn = create_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM users")
        row = cur.fetchone()
        return int(row[0]) if row else 0
    finally:
        conn.close()


def get_movie_by_title(title: str) -> Optional[Dict[str, Any]]:
    init_db()
    normalized = str(title or "").strip()
    if not normalized:
        return None
    return _fetch_one(
        "SELECT id, movie_id, title, tags, poster_url, language FROM movies WHERE LOWER(title) = LOWER(?) LIMIT 1",
        (normalized,),
    )


def get_movie_by_id(movie_id: int) -> Optional[Dict[str, Any]]:
    init_db()
    try:
        movie_id_int = int(movie_id)
    except (TypeError, ValueError):
        return None
    return _fetch_one(
        "SELECT id, movie_id, title, tags, poster_url, language FROM movies WHERE id = ? LIMIT 1",
        (movie_id_int,),
    )


def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    init_db()
    normalized = str(username or "").strip()
    if not normalized:
        return None
    return _fetch_one(
        "SELECT id, username, email, password FROM users WHERE LOWER(username) = LOWER(?) LIMIT 1",
        (normalized,),
    )


def get_current_user(user_id: Optional[int] = None, username: Optional[str] = None) -> Optional[Dict[str, Any]]:
    init_db()
    if user_id is not None:
        try:
            user_id_int = int(user_id)
        except (TypeError, ValueError):
            user_id_int = None
        if user_id_int is not None:
            user = _fetch_one(
                "SELECT id, username, email, password FROM users WHERE id = ? LIMIT 1",
                (user_id_int,),
            )
            if user:
                return user

    if username:
        return get_user_by_username(username)

    return None


def register_user(username: str, email: str, password: str) -> Dict[str, Any]:
    init_db()
    username_clean = str(username or "").strip()
    email_clean = str(email or "").strip()
    password_clean = str(password or "")

    if not username_clean or not email_clean or not password_clean:
        return {"success": False, "message": "Username, email, and password are required.", "user_id": None}

    conn = create_connection()
    try:
        hashed_password = bcrypt.hashpw(password_clean.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
            (username_clean, email_clean, hashed_password),
        )
        conn.commit()
        return {"success": True, "message": "Account created successfully.", "user_id": cur.lastrowid}
    except sqlite3.IntegrityError:
        existing_username = get_user_by_username(username_clean)
        if existing_username:
            return {"success": False, "message": "Username already exists.", "user_id": None}

        existing_email = _fetch_one("SELECT id FROM users WHERE LOWER(email) = LOWER(?) LIMIT 1", (email_clean,))
        if existing_email:
            return {"success": False, "message": "Email already exists.", "user_id": None}

        return {"success": False, "message": "Account already exists.", "user_id": None}
    finally:
        conn.close()


def login_user(username: str, password: str) -> Dict[str, Any]:
    init_db()
    username_clean = str(username or "").strip()
    password_clean = str(password or "")

    if not username_clean or not password_clean:
        return {"success": False, "message": "Username and password are required.", "user": None}

    user = get_user_by_username(username_clean)
    if not user:
        return {"success": False, "message": "Invalid credentials.", "user": None}

    stored_password = str(user.get("password") or "")
    try:
        password_ok = bcrypt.checkpw(password_clean.encode("utf-8"), stored_password.encode("utf-8"))
    except ValueError:
        password_ok = False

    if not password_ok:
        return {"success": False, "message": "Invalid credentials.", "user": None}

    return {"success": True, "message": "Login successful.", "user": user}


def add_user(username: str, email: str, password: str) -> Optional[int]:
    result = register_user(username, email, password)
    return result.get("user_id") if result.get("success") else None


def verify_user(username: str, password: str) -> Optional[int]:
    result = login_user(username, password)
    if result.get("success") and result.get("user"):
        return int(result["user"]["id"])
    return None


def add_to_watchlist(user_id: int, movie_id: int) -> Dict[str, Any]:
    init_db()
    try:
        user_id_int = int(user_id)
        movie_id_int = int(movie_id)
    except (TypeError, ValueError):
        return {"success": False, "message": "Invalid user or movie ID."}

    conn = create_connection()
    try:
        cur = conn.cursor()

        # Verify user exists
        cur.execute("SELECT id FROM users WHERE id = ?", (user_id_int,))
        if not cur.fetchone():
            return {"success": False, "message": "User not found."}

        # Verify movie exists
        cur.execute("SELECT id FROM movies WHERE id = ?", (movie_id_int,))
        if not cur.fetchone():
            # Try to find by movie_id column instead
            cur.execute("SELECT id FROM movies WHERE movie_id = ?", (movie_id_int,))
            row = cur.fetchone()
            if row:
                movie_id_int = row[0]
            else:
                return {"success": False, "message": "Movie not found in database."}

        cur.execute(
            "INSERT OR IGNORE INTO watchlist (user_id, movie_id) VALUES (?, ?)",
            (user_id_int, movie_id_int),
        )
        conn.commit()
        if cur.rowcount:
            return {"success": True, "message": "Movie added successfully."}
        return {"success": False, "message": "Movie already in watchlist."}
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}
    finally:
        conn.close()


def remove_from_watchlist(user_id: int, movie_id: int) -> Dict[str, Any]:
    init_db()
    try:
        user_id_int = int(user_id)
        movie_id_int = int(movie_id)
    except (TypeError, ValueError):
        return {"success": False, "message": "Invalid user or movie ID."}

    conn = create_connection()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM watchlist WHERE user_id = ? AND movie_id = ?", (user_id_int, movie_id_int))
        conn.commit()
        if cur.rowcount:
            return {"success": True, "message": "Movie removed successfully."}
        return {"success": False, "message": "Movie not found in watchlist."}
    finally:
        conn.close()


def get_watchlist(user_id: int) -> List[Dict[str, Any]]:
    init_db()
    try:
        user_id_int = int(user_id)
    except (TypeError, ValueError):
        return []

    return _fetch_all(
        """
        SELECT
            w.id AS watchlist_id,
            m.id,
            m.movie_id,
            m.title,
            m.tags,
            m.poster_url
        FROM movies m
        INNER JOIN watchlist w ON w.movie_id = m.id
        WHERE w.user_id = ?
        ORDER BY w.id DESC
        """,
        (user_id_int,),
    )