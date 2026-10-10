-- schema.sql is used to:
-- CREATE tables !
-- RESET tables if restarting db.

SET default_storage_engine = InnoDB;

-- disabling foreign key safety checks for clean drops !
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS roles;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS profiles;

DROP TABLE IF EXISTS user_collection;
DROP TABLE IF EXISTS user_wishlist;

DROP TABLE IF EXISTS records;
DROP TABLE IF EXISTS artists;
DROP TABLE IF EXISTS genres;

SET FOREIGN_KEY_CHECKS = 1;


CREATE TABLE roles (
    role_id INT AUTO_INCREMENT PRIMARY KEY,
    role_name VARCHAR(30) NOT NULL UNIQUE
);

CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(80) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (role_id) REFERENCES roles(role_id) ON DELETE RESTRICT
);

CREATE TABLE artists (
    artist_id INT AUTO_INCREMENT PRIMARY KEY,
    artist_name VARCHAR(150) NOT NULL,
    country VARCHAR(80),
    description TEXT
);

CREATE TABLE genres (
    genre_id INT AUTO_INCREMENT PRIMARY KEY,
    genre_name VARCHAR(80) NOT NULL UNIQUE
);

CREATE TABLE records (
    record_id INT AUTO_INCREMENT PRIMARY KEY,
    record_name VARCHAR(80) NOT NULL UNIQUE,
    price INT NOT NULL DEFAULT 299.00,
    release_date DATE NOT NULL,
    date_added DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    description TEXT,
    cover_url VARCHAR(2083),
    artist_id INT NOT NULL,
    genre_id INT NOT NULL,
    is_weekly_pick BOOLEAN DEFAULT FALSE NOT NULL,
    in_stock BOOLEAN DEFAULT FALSE NOT NULL,
    stock_qty INT DEFAULT 0,
    FOREIGN KEY (artist_id) REFERENCES artists(artist_id) ON DELETE CASCADE
    ,FOREIGN KEY (genre_id) REFERENCES genres(genre_id) ON DELETE RESTRICT
);

CREATE TABLE user_collection (
    user_collection_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    record_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_user_collection (user_id, record_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (record_id) REFERENCES records(record_id) ON DELETE CASCADE
);

CREATE TABLE user_wishlist (
    user_wishlist_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    record_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_user_wishlist (user_id, record_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (record_id) REFERENCES records(record_id) ON DELETE CASCADE
);
