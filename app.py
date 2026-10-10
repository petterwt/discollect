import os
from functools import wraps

import requests as http_requests
from flask import Flask, render_template, jsonify, request, session, redirect, url_for, flash
from werkzeug.security import check_password_hash, generate_password_hash
from config import (
    SECRET_KEY,
    SPOTIFY_CLIENT_ID,
    SPOTIFY_CLIENT_SECRET,
    SPOTIFY_TOKEN_URL,
    SPOTIFY_SEARCH_URL,
)
from database.db_helper import (
    get_db_connection,
    ensure_default_users,
    get_user_by_username,
    get_user_records_for_table,
    get_user_record_ids,
    save_record_for_user,
    remove_record_for_user,
    get_admin_inventory_records,
    get_catalog_records,
    ensure_weekly_pick_column,
    get_weekly_pick_records,
    get_homepage_metrics,
)
from database.search_helpers import get_genres, search_stock_records


app = Flask(__name__)
app.secret_key = SECRET_KEY

# =========================
# Auth and Session
# =========================
def get_current_user():
    """Return the logged-in user information stored in the session."""
    if not session.get("user_id"):
        return None

    return {
        "user_id": session.get("user_id"),
        "username": session.get("username"),
        "role_name": session.get("role_name"),
    }


@app.context_processor
def inject_auth_context():
    return {
        "current_user": get_current_user(),
        "is_logged_in": bool(session.get("user_id")),
    }


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)

    return wrapped_view


def admin_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        user = get_current_user()
        if not user:
            return redirect(url_for("login", next=request.path))
        if user.get("role_name") != "admin":
            flash("Admin access only.", "error")
            return redirect(url_for("profile"))
        return view(*args, **kwargs)



    return wrapped_view
# =====================================
# User Collection/Wishlist
# =====================================
def get_active_user_lists():
    """Return the current user's saved lists or guest preview lists."""
    user = get_current_user()
    if user:
        collection_records = get_user_records_for_table(user["user_id"], "user_collection")
        wishlist_records = get_user_records_for_table(user["user_id"], "user_wishlist")
        collection_ids = get_user_record_ids(user["user_id"], "user_collection")
        wishlist_ids = get_user_record_ids(user["user_id"], "user_wishlist")
        return collection_records, wishlist_records, collection_ids, wishlist_ids

    catalog_records = get_catalog_records()
    collection_records, wishlist_records = split_records_by_availability(catalog_records)
    return collection_records, wishlist_records, set(), set()


def split_records_by_availability(records):
    """Split records into collection and wishlist lists."""
    collection_records = [record for record in records if record.get("in_stock")]
    wishlist_records = [record for record in records if not record.get("in_stock")]
    return collection_records, wishlist_records


# =============
# Public Routes
# =============
@app.route('/')
def homepage():
    ensure_default_users()
    ensure_weekly_pick_column()

    # 1. Connect to the database
    conn = get_db_connection()

    # 2. Use dictionary=True so rows can be accessed like row['location'] in HTML
    cur = conn.cursor(dictionary=True)

    # 3. Fetch the data from your tables
    artist_query = "SELECT * FROM artists ORDER BY artist_id ASC"
    cur.execute(artist_query)
    artists_data = cur.fetchall()

    cur.close()
    conn.close()

    weekly_pick_records = get_weekly_pick_records()
    collection_records, wishlist_records, collection_ids, wishlist_ids = get_active_user_lists()
    metrics = get_homepage_metrics()

    # 4. Render the HTML file and pass the parameters into index.html
    return render_template(
        'index.html',
        artists=artists_data,
        records=weekly_pick_records,
        stock_count=metrics["records_in_stock"],
        new_arrival_count=metrics["new_arrivals"],
        collection_preview=collection_records[:3],
        wishlist_preview=wishlist_records[:3],
        collection_record_ids=collection_ids,
        wishlist_record_ids=wishlist_ids,
        genres=get_genres(),
    )


# ========================
# Authentication Routes
# ========================
@app.route('/login', methods=['GET', 'POST'])
def login():
    ensure_default_users()

    if session.get("user_id"):
        return redirect(url_for("profile"))

    next_target = request.args.get("next", "")

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        next_target = request.form.get('next', '') or next_target

        user = get_user_by_username(username) if username else None
        if not user or not check_password_hash(user['password_hash'], password):
            flash('Invalid username or password.', 'error')
            return render_template('login.html', next_target=next_target, username=username), 401

        session['user_id'] = user['user_id']
        session['username'] = user['username']
        session['role_name'] = user['role_name']

        if not next_target.startswith('/'):
            next_target = url_for('profile')

        return redirect(next_target)

    return render_template('login.html', next_target=next_target, username='')


@app.route('/register', methods=['GET', 'POST'])
def register():
    ensure_default_users()

    if session.get("user_id"):
        return redirect(url_for("profile"))

    next_target = request.args.get('next', '')

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        errors = []
        if not username:
            errors.append('Username is required.')
        if len(password) < 6:
            errors.append('Password must be at least 6 characters.')
        if password != confirm_password:
            errors.append('Passwords do not match.')
        if username and get_user_by_username(username):
            errors.append('Username is already taken.')

        if errors:
            for error_message in errors:
                flash(error_message, 'error')
            return render_template('register.html', next_target=next_target, username=username), 400

        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)

        cur.execute("SELECT role_id FROM roles WHERE role_name = %s", ("customer",))
        role_row = cur.fetchone()
        if not role_row:
            cur.close()
            conn.close()
            flash('Customer role is missing from the database.', 'error')
            return render_template('register.html', next_target=next_target, username=username), 500

        password_hash = generate_password_hash(password)
        cur.execute(
            "INSERT INTO users (username, password_hash, role_id) VALUES (%s, %s, %s)",
            (username, password_hash, role_row['role_id']),
        )
        conn.commit()
        new_user_id = cur.lastrowid

        cur.close()
        conn.close()

        session['user_id'] = new_user_id
        session['username'] = username
        session['role_name'] = 'customer'
        flash('Account created. You are now logged in.', 'success')
        return redirect(url_for('profile'))

    return render_template('register.html', next_target=next_target, username='')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('homepage'))


# ======================
# Protected User Routes
# ======================
@app.route('/profile')
@login_required
def profile():
    ensure_default_users()
    collection_records, wishlist_records, collection_ids, wishlist_ids = get_active_user_lists()

    return render_template(
        'profile.html',
        collection_records=collection_records,
        wishlist_records=wishlist_records,
        collection_record_ids=collection_ids,
        wishlist_record_ids=wishlist_ids,
    )


# ==============================
# Collection/Wishlist Mutations
# ==============================
@app.route('/wishlist/add/<int:record_id>', methods=['POST'])
@login_required
def add_to_wishlist(record_id):
    inserted = save_record_for_user(session['user_id'], 'user_wishlist', record_id)
    flash('Added to your wishlist.' if inserted else 'Already in your wishlist.', 'success')
    redirect_to = request.form.get('redirect_to', url_for('homepage'))
    return redirect(redirect_to if redirect_to.startswith('/') else url_for('homepage'))


@app.route('/wishlist/remove/<int:record_id>', methods=['POST'])
@login_required
def remove_from_wishlist(record_id):
    deleted = remove_record_for_user(session['user_id'], 'user_wishlist', record_id)
    flash('Removed from your wishlist.' if deleted else 'Record was not in your wishlist.', 'success')
    redirect_to = request.form.get('redirect_to', url_for('homepage'))
    return redirect(redirect_to if redirect_to.startswith('/') else url_for('homepage'))


@app.route('/collection/add/<int:record_id>', methods=['POST'])
@login_required
def add_to_collection(record_id):
    inserted = save_record_for_user(session['user_id'], 'user_collection', record_id)
    flash('Added to your collection.' if inserted else 'Already in your collection.', 'success')
    redirect_to = request.form.get('redirect_to', url_for('homepage'))
    return redirect(redirect_to if redirect_to.startswith('/') else url_for('homepage'))


@app.route('/collection/remove/<int:record_id>', methods=['POST'])
@login_required
def remove_from_collection(record_id):
    deleted = remove_record_for_user(session['user_id'], 'user_collection', record_id)
    flash('Removed from your collection.' if deleted else 'Record was not in your collection.', 'success')
    redirect_to = request.form.get('redirect_to', url_for('homepage'))
    return redirect(redirect_to if redirect_to.startswith('/') else url_for('homepage'))


# ============
# Admin Routes
# ============
@app.route('/admin')
@admin_required
def admin_dashboard():
    sold_out_records = get_admin_inventory_records()

    return render_template(
        'admin.html',
        sold_out_records=sold_out_records,
    )


@app.route('/admin/set-stock/<int:record_id>', methods=['POST'])
@admin_required
def set_stock(record_id):
    # Set stock quantity for a record
    qty_text = request.form.get('stock_qty', '').strip()
    try:
        qty = max(0, int(qty_text))
    except ValueError:
        flash('Invalid stock quantity.', 'error')
        return redirect(url_for('admin_dashboard'))

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE records
        SET stock_qty = %s,
            in_stock = CASE WHEN %s > 0 THEN TRUE ELSE FALSE END
        WHERE record_id = %s
        """,
        (qty, qty, record_id),
    )
    conn.commit()
    cur.close()
    conn.close()

    flash('Stock updated.', 'success')
    return redirect(request.form.get('redirect_to') or url_for('admin_dashboard'))


@app.route('/admin/change-stock/<int:record_id>', methods=['POST'])
@admin_required
def change_stock(record_id):
    # Adjust stock by a delta (positive or negative)
    delta_text = request.form.get('delta', '0').strip()
    try:
        delta = int(delta_text)
    except ValueError:
        flash('Invalid delta.', 'error')
        return redirect(request.form.get('redirect_to') or url_for('admin_dashboard'))

    conn = get_db_connection()
    cur = conn.cursor()
    # Ensure we don't go negative
    cur.execute("SELECT stock_qty FROM records WHERE record_id = %s", (record_id,))
    row = cur.fetchone()
    if not row:
        cur.close()
        conn.close()
        flash('Record not found.', 'error')
        return redirect(request.form.get('redirect_to') or url_for('admin_dashboard'))

    try:
        current = int(row[0]) if isinstance(row, tuple) else int(row.get('stock_qty') or 0)
    except Exception:
        current = 0

    new_qty = max(0, current + delta)
    cur.execute(
        "UPDATE records SET stock_qty = %s, in_stock = CASE WHEN %s > 0 THEN TRUE ELSE FALSE END WHERE record_id = %s",
        (new_qty, new_qty, record_id),
    )
    conn.commit()
    cur.close()
    conn.close()

    flash('Stock adjusted.', 'success')
    return redirect(request.form.get('redirect_to') or url_for('admin_dashboard'))


# ==========
# API Routes
# ==========
@app.route('/api/search')
def search_music():
    """Search only the in-stock catalog stored in MySQL."""
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({"results": []})

    records = search_stock_records(query)
    return jsonify({"results": records})


@app.route('/api/search_by_genre')
def search_by_genre():
    genre_id = request.args.get('genre_id')
    if not genre_id:
        return jsonify({"results": []})
    try:
        gid = int(genre_id)
    except ValueError:
        return jsonify({"results": []}), 400

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    query = """
    SELECT records.record_id, records.record_name, records.price, records.release_date, records.description,
           records.cover_url, records.in_stock, records.stock_qty,
           artists.artist_name, genres.genre_name
    FROM records
    INNER JOIN artists ON records.artist_id = artists.artist_id
    INNER JOIN genres ON records.genre_id = genres.genre_id
    WHERE genres.genre_id = %s
    ORDER BY records.date_added DESC, records.release_date DESC
    """
    cur.execute(query, (gid,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    for r in rows:
        if r.get('release_date'):
            r['release_year_only'] = r['release_date'].year
    return jsonify({"results": rows})


def _get_spotify_token():
    """Fetch a client-credentials token from Spotify."""
    resp = http_requests.post(
        SPOTIFY_TOKEN_URL,
        data={"grant_type": "client_credentials"},
        auth=(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET),
        timeout=5,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


@app.route('/api/spotify-search')
def spotify_search():
    """Search Spotify for albums and return simplified results."""
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({"results": []})
    try:
        token = _get_spotify_token()
        resp = http_requests.get(
            SPOTIFY_SEARCH_URL,
            headers={"Authorization": f"Bearer {token}"},
            params={"q": query, "type": "album", "limit": 8},
            timeout=5,
        )
        resp.raise_for_status()
        items = resp.json().get("albums", {}).get("items", [])
        results = [
            {
                "spotify_id": a["id"],
                "title": a["name"],
                "artist": a["artists"][0]["name"] if a.get("artists") else "",
                "cover_url": a["images"][0]["url"] if a.get("images") else "",
                "release_date": a.get("release_date", ""),
            }
            for a in items
        ]
        return jsonify({"results": results})
    except Exception as exc:
        return jsonify({"error": str(exc), "results": []}), 500


@app.route('/api/search_not_in_stock')
def search_not_in_stock():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({"results": []})

    # Search the records table for matches and return only those not in stock
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    sql = """
    SELECT records.record_id, records.record_name, records.release_date, records.description,
           records.cover_url, records.in_stock, records.stock_qty,
           artists.artist_name, genres.genre_name
    FROM records
    INNER JOIN artists ON records.artist_id = artists.artist_id
    INNER JOIN genres ON records.genre_id = genres.genre_id
    WHERE (LOWER(records.record_name) LIKE %s OR LOWER(artists.artist_name) LIKE %s)
      AND records.in_stock = FALSE
    ORDER BY records.date_added DESC, records.release_date DESC
    LIMIT 50
    """
    like_term = f"%{query.lower()}%"
    cur.execute(sql, (like_term, like_term))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    for r in rows:
        if r.get('release_date'):
            r['release_year_only'] = r['release_date'].year
    return jsonify({"results": rows})


@app.route('/user/add-from-spotify', methods=['POST'])
@login_required
def user_add_from_spotify():
    """Save a Spotify album into the DB (if new) then add to user list."""
    title      = request.form.get('title', '').strip()
    artist     = request.form.get('artist', '').strip()
    cover_url  = request.form.get('cover_url', '').strip()
    release_date = request.form.get('release_date', '2000-01-01').strip()
    list_type  = request.form.get('list_type', 'collection')  # 'collection' or 'wishlist'
    table_name = 'user_collection' if list_type == 'collection' else 'user_wishlist'

    if not title or not artist:
        flash('Missing title or artist.', 'error')
        return redirect(url_for('profile'))

    # Ensure release_date is a full date string
    if len(release_date) == 4:          # year only e.g. "1973"
        release_date = release_date + '-01-01'
    elif len(release_date) == 7:        # year-month e.g. "1973-03"
        release_date = release_date + '-01'

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    # Upsert artist
    cur.execute("SELECT artist_id FROM artists WHERE artist_name = %s LIMIT 1", (artist,))
    row = cur.fetchone()
    if row:
        artist_id = row['artist_id']
    else:
        cur.execute("INSERT INTO artists (artist_name) VALUES (%s)", (artist,))
        artist_id = cur.lastrowid

    # Use genre_id=10 (Unknown) as default
    cur.execute("SELECT genre_id FROM genres WHERE genre_id = 10 LIMIT 1")
    genre_row = cur.fetchone()
    genre_id = genre_row['genre_id'] if genre_row else 1

    # Upsert record
    cur.execute("SELECT record_id FROM records WHERE record_name = %s LIMIT 1", (title,))
    rec = cur.fetchone()
    if rec:
        record_id = rec['record_id']
    else:
        cur.execute(
            "INSERT INTO records (record_name, release_date, cover_url, artist_id, genre_id, in_stock, stock_qty) "
            "VALUES (%s, %s, %s, %s, %s, FALSE, 0)",
            (title, release_date, cover_url, artist_id, genre_id),
        )
        record_id = cur.lastrowid

    conn.commit()
    cur.close()
    conn.close()

    save_record_for_user(session['user_id'], table_name, record_id)
    flash(f'Added "{title}" to your {list_type}.', 'success')
    return redirect(url_for('profile'))


@app.route('/admin/add-from-spotify', methods=['POST'])
@admin_required
def add_from_spotify():
    """Insert a Spotify album into the catalog with a given stock quantity."""
    title        = request.form.get('title', '').strip()
    artist       = request.form.get('artist', '').strip()
    cover_url    = request.form.get('cover_url', '').strip()
    release_date = request.form.get('release_date', '2000-01-01').strip()
    stock_qty    = max(0, int(request.form.get('stock_qty', '0') or '0'))

    if not title or not artist:
        flash('Missing title or artist.', 'error')
        return redirect(url_for('admin_dashboard'))

    if len(release_date) == 4:
        release_date = release_date + '-01-01'
    elif len(release_date) == 7:
        release_date = release_date + '-01'

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("SELECT artist_id FROM artists WHERE artist_name = %s LIMIT 1", (artist,))
    row = cur.fetchone()
    if row:
        artist_id = row['artist_id']
    else:
        cur.execute("INSERT INTO artists (artist_name) VALUES (%s)", (artist,))
        artist_id = cur.lastrowid

    cur.execute("SELECT genre_id FROM genres WHERE genre_id = 10 LIMIT 1")
    genre_row = cur.fetchone()
    genre_id = genre_row['genre_id'] if genre_row else 1

    # Check if already exists
    cur.execute("SELECT record_id FROM records WHERE record_name = %s LIMIT 1", (title,))
    existing = cur.fetchone()
    if existing:
        cur.execute(
            "UPDATE records SET stock_qty = stock_qty + %s, in_stock = TRUE WHERE record_id = %s",
            (stock_qty, existing['record_id']),
        )
        flash(f'"{title}" already exists — stock updated.', 'success')
    else:
        in_stock = stock_qty > 0
        cur.execute(
            "INSERT INTO records (record_name, release_date, cover_url, artist_id, genre_id, in_stock, stock_qty) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (title, release_date, cover_url, artist_id, genre_id, in_stock, stock_qty),
        )
        flash(f'"{title}" added to the catalog.', 'success')

    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1", port=5000)