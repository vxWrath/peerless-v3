CREATE TABLE IF NOT EXISTS blacklist (
    id BIGINT PRIMARY KEY,
    reason VARCHAR(256),
    moderator_id BIGINT,
    date TIMESTAMP WITH TIME ZONE
);