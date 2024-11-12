CREATE TABLE IF NOT EXISTS leagues (
    id BIGINT PRIMARY KEY,
    blacklisted BOOLEAN DEFAULT false,

    premium JSONB DEFAULT '{}'::jsonb,

    color JSONB DEFAULT NULL,
    themes JSONB DEFAULT NULL,
            
    settings JSONB DEFAULT '{}'::jsonb,
    roles JSONB DEFAULT '{}'::jsonb,
    pings JSONB DEFAULT '{}'::jsonb,
    channels JSONB DEFAULT '{}'::jsonb,
    alerts JSONB DEFAULT '{}'::jsonb,
    statuses JSONB DEFAULT '{}'::jsonb,

    teams JSONB DEFAULT '{}'::jsonb,
    coaches JSONB DEFAULT '{}'::jsonb,

    season JSONB DEFAULT '{}'::jsonb,
    games JSONB DEFAULT '{}'::jsonb,

    awards JSONB DEFAULT '{}'::jsonb
);