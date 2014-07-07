CREATE TABLE users (
   id SERIAL PRIMARY KEY,
   entity VARCHAR(256),
   app_id VARCHAR(256),
   app_hawk_key VARCHAR(256),
   app_hawk_id VARCHAR(256),
   hawk_key VARCHAR(256),
   hawk_id VARCHAR(256),
   feed_url VARCHAR(1024)
);

CREATE TABLE feeds (
    id SERIAL PRIMARY KEY,
    url VARCHAR(1024),
    last_fetch_date INTEGER,
    user_id INTEGER,
    recent_items_cache BYTEA,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE feed_items (
    id SERIAL PRIMARY KEY,
    title VARCHAR(512),
    url VARCHAR(1024),
    published_date INTEGER,
    feed_id INTEGER,
    FOREIGN KEY (feed_id) REFERENCES feeds(id)
);
