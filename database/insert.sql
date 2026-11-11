-- insert.sql populates tables created in schema.sql
-- with example data.

INSERT INTO roles (role_name) VALUES
 ('admin'), ('customer');

INSERT INTO users (username, password_hash, role_id) VALUES
    ('admin', 'pbkdf2:sha256:1000000$EGyYt9Ea$68b167be3be519e76353f2c7f84baa318297db0b6b975dc262f0b7727d5979f7', 1),
    ('customer', 'pbkdf2:sha256:1000000$iaXpBD5m$5a24e018a2fb4722ff38f11eb9d08f878982311239c98a404080c7b6589d3e14', 2);

INSERT INTO artists (artist_id, artist_name, country, description) VALUES
    (1, 'The Beatles', 'United Kingdom', 'Iconic rock band from Liverpool.'),
    (2, 'Pink Floyd', 'United Kingdom', 'Progressive rock band known for concept albums.');

INSERT INTO genres (genre_id, genre_name) VALUES
    (1, 'Rock'),
    (2, 'Progressive Rock'),
    (3, 'Pop'),
    (4, 'Punk'),
    (5, 'Metal'),
    (6, 'Jazz'),
    (7, 'Soul'),
    (8, 'Electronic'),
    (9, 'Hip-Hop'),
    (10, 'Unknown');

INSERT INTO records (record_name, price, release_date, date_added, description, cover_url, artist_id, genre_id, is_weekly_pick, in_stock, stock_qty) VALUES
    ('Abbey Road', 349, '1969-09-26', '2026-06-05 10:00:00', 'Iconic rock medleys that define the pinnacle of analog recording history.','https://is1-ssl.mzstatic.com/image/thumb/Music211/v4/48/53/43/485343e3-dd6a-0034-faec-f4b6403f8108/13UMGIM63890.rgb.jpg/600x600bb.jpg', 1, 1, TRUE, TRUE, 12),
    ('The Dark Side of the Moon', 299, '1973-03-01', '2026-06-02 14:30:00', 'Deep bass textures engineered for an ultimate high-fidelity listening experience.','https://is1-ssl.mzstatic.com/image/thumb/Music211/v4/49/86/18/49861852-877b-0992-fa27-58b25fa032b5/196589805232.jpg/600x600bb.jpg', 2, 2, TRUE, TRUE, 8),
    ('Let It Be', 399, '1970-05-08', '2026-06-01 09:15:00', 'A warm closing chapter with timeless songwriting and clean press quality.', 'https://is1-ssl.mzstatic.com/image/thumb/Music124/v4/ae/98/4c/ae984c7a-cd06-a7cd-e8bf-32cb15ba698d/00602567705475.rgb.jpg/600x600bb.jpg', 1, 1, TRUE, TRUE, 4),
    ('Wish You Were Here', 379, '1975-09-12', '2026-05-10 12:00:00', 'A reflective progressive rock classic with studio depth and atmosphere.','https://i.scdn.co/image/ab67616d0000b273828e52cfb7bf22869349799e', 2, 2, TRUE, FALSE, 0),
    ('Revolver', 329, '1966-08-05', '2026-04-18 16:20:00', 'Groovy, inventive, and essential for any Beatles shelf.','https://i.scdn.co/image/ab67616d0000b27328b8b9b46428896e6491e97a', 1, 1, TRUE, FALSE, 0),
    ('The Wall', 429, '1979-11-30', '2026-03-22 11:45:00', 'A sprawling concept record with one of rock''s most recognizable visuals.','https://i.scdn.co/image/ab67616d0000b273b694e89ba937dd2631ff584c', 2, 2, TRUE, FALSE, 0);

INSERT INTO user_collection (user_id, record_id) VALUES
    (2, 1),
    (2, 3),
    (2, 5);

INSERT INTO user_wishlist (user_id, record_id) VALUES
    (2, 2),
    (2, 4),
    (2, 6);