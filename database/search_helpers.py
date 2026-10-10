from database.db_helper import get_db_connection


def normalize_text(value):
    return " ".join((value or "").lower().strip().split())


def normalize_album_title(value):
    text = normalize_text(value)
    for suffix in (" (remastered)", " (deluxe edition)", " (deluxe)", " (expanded edition)", " (expanded)"):
        if text.endswith(suffix):
            text = text[: -len(suffix)].strip()

    return text


def build_match_key(title, artist):
    return normalize_album_title(title), normalize_text(artist)


def get_genres():
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("SELECT genre_id, genre_name FROM genres ORDER BY genre_name ASC")
    genres = cur.fetchall()

    cur.close()
    conn.close()
    return genres


def get_catalog_records():
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    query = """
    SELECT records.*, artists.artist_name, genres.genre_name
    FROM records
    INNER JOIN artists ON records.artist_id = artists.artist_id
    INNER JOIN genres ON records.genre_id = genres.genre_id
    ORDER BY records.date_added DESC, records.release_date DESC
    """
    cur.execute(query)
    records = cur.fetchall()

    cur.close()
    conn.close()
    return records


def search_stock_records(query):
    search_text = normalize_text(query)
    if not search_text:
        return []

    like_pattern = f"%{search_text}%"
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    query = """
    SELECT records.record_id, records.record_name, records.price, records.release_date, records.description,
           records.cover_url, records.in_stock, records.stock_qty,
           artists.artist_name, genres.genre_name
    FROM records
    INNER JOIN artists ON records.artist_id = artists.artist_id
    INNER JOIN genres ON records.genre_id = genres.genre_id
    WHERE (
        LOWER(records.record_name) LIKE %s
        OR LOWER(artists.artist_name) LIKE %s
        OR LOWER(genres.genre_name) LIKE %s
      )
    ORDER BY records.date_added DESC, records.release_date DESC
    """
    cur.execute(query, (like_pattern, like_pattern, like_pattern))
    records = cur.fetchall()

    cur.close()
    conn.close()

    for record in records:
        if record.get("release_date"):
            record["release_year_only"] = record["release_date"].year

    return records

def insert_or_update_record_from_spotify(album_data, genre_id):
    raise NotImplementedError("Spotify import disabled in simplified build")
