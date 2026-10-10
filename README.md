# Discollect

Discollect is a vinyl shop and collection tracker.
Users can browse records in stock, search the catalog, maintain a wishlist and collection, and admins can manage stock.

Originally built as an exam project in DAT130 (Databases and Web Programming) at the University of Stavanger, spring 2026.

> **Work in progress:** A TypeScript rewrite (Next.js, React, PostgreSQL, Drizzle ORM) is under development. This repository contains the original Flask/MySQL/JavaScript version.

## How To Run

Terminal commands are shown below. Contact me if any problems occur.

1. Make sure you are in the project root directory.
2. Create and activate a venv.
3. Install Python dependencies from requirements.txt.
4. Create a MySQL database.
5. Create a new file in project root named .env.
6. Copy contents of .env.example into the created .env file.
7. Fill out the placeholders in the .env file (db password and spotify keys from developer.spotify.com/dashboard)
8. Initialize the database from the project root: python3 -m database.init_db
9. Start the Flask app with python3 app.py.
10. Open in browser.

```bash
cd project

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

cp .env.example .env

mysql -u root -p

CREATE DATABASE IF NOT EXISTS discollect CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

python3 -m database.init_db
python3 app.py
```

## Test Users

You can log in with the seeded users:

- Admin: username admin, password admin123
- Customer: username customer, password user123

## Database Tables

The schema contains 7 relational tables with PK/FK constraints:

- roles
- users
- artists
- genres
- records
- user_collection
- user_wishlist

## Functionality

### Authentication And Access Control

- Register new users:
  - username required
  - password length minimum 6
  - password confirmation match
  - duplicate username prevention
- Log in existing users with hashed password verification.
- Log out clears session.
- Route protection with decorators:
  - login_required for profile and user actions
  - admin_required for admin pages and stock mutation routes

### User Features

- Homepage with:
  - weekly picks section
  - stock/new-arrival metrics
  - search for records in stock using text or category
- Add/remove records to/from wishlist.
- Add/remove records to/from collection.
- Profile page shows full collection and wishlist tables.
- Profile Spotify search:
  - search Spotify albums from profile
  - add Spotify result directly to collection
  - add Spotify result directly to wishlist

### Admin Features

- Admin dashboard with sold-out list.
- Update stock by:
  - increment/decrement buttons
  - set value
- Admin catalog search across DB records and AJAX stock updates from search results.
- Admin "Add new record" Spotify search:
  - search Spotify albums
  - add result to catalog with stock quantity
  - if record already exists, stock is increased instead of duplicate insert

### Search, Sort, And Persistence

- AJAX search endpoint for catalog search.
- AJAX search by genre endpoint.
- AJAX Spotify search endpoint.
- Client-side sorting for weekly picks by:
  - default weekly order
  - title
  - price
  - newest year
- Sort stored in localStorage key featured-sort-mode.

### JavaScript Validation and user experience

- Client side form validation on login and register with error display.
- Confirm dialogs before remove actions from wishlist/collection.

### SQL

- SQL JOIN usage across records, artists, genres, and user list tables.
- Insert/update/delete operations are implemented for user list and stock management flows.
- Data/query helpers are separated into db_helper.py and search_helpers.py.

### Layout And Markup

- Responsive layout with CSS media queries for mobile and desktop behavior.
- Semantic HTML structure with header, main, section, article, nav, footer.

## Routes Overview

Main pages:

- GET /
- GET/POST /login
- GET/POST /register
- GET /logout
- GET /profile
- GET /admin

User mutation routes:

- POST /wishlist/add/<record_id>
- POST /wishlist/remove/<record_id>
- POST /collection/add/<record_id>
- POST /collection/remove/<record_id>

Admin mutation routes:

- POST /admin/set-stock/<record_id>
- POST /admin/change-stock/<record_id>

API routes (AJAX):

- GET /api/search
- GET /api/search_by_genre
- GET /api/spotify-search

Spotify insert routes:

- POST /user/add-from-spotify
- POST /admin/add-from-spotify

## Error Handling And Validation

- Invalid login returns status 401 with flash message.
- Invalid register input returns status 400 with flash messages.
- Missing customer role at register returns status 500 with flash message.
- Invalid genre query returns status 400 in API.
- Invalid stock input values are handled with flashes and redirects.

## Known Limitations

- Spotify imports use a simple default genre mapping (Unknown genre fallback).
- Some metadata (price/description) is minimal for Spotify-imported records until edited in admin.
- No CSRF protection on forms and state-changing POST routes. A production version should add CSRF tokens (e.g. Flask-WTF `CSRFProtect`) and `SameSite` session cookies.

## Project Files Of Interest

- app.py: Flask routes, session/auth decorators, and controllers
- database/schema.sql: full schema
- database/insert.sql: example seed data
- database/db_helper.py: DB helpers and query functions
- database/search_helpers.py: search-related helpers
- static/js/validation.js: client form validation
- static/js/search.js: search, sorting, AJAX, admin stock updates
- templates/: Jinja templates for UI pages
