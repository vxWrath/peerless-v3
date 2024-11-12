CREATE TABLE IF NOT EXISTS players (
    id BIGINT PRIMARY KEY,
    blacklisted BOOLEAN DEFAULT false,
    leagues JSONB DEFAULT '{}'::jsonb
);