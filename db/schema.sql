CREATE TABLE users (
   id SERIAL PRIMARY KEY,
   entity VARCHAR(256),
   app_id VARCHAR(256),
   app_hawk_key VARCHAR(256),
   app_hawk_id VARCHAR(256),
   hawk_key VARCHAR(256),
   hawk_id VARCHAR(256),
   preferences_post VARCHAR(1024)
);
