-- Apply after 001_initial.sql through the Supabase SQL editor.
CREATE TABLE IF NOT EXISTS google_calendar_connections (
    user_id uuid PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    access_token_encrypted text NOT NULL,
    refresh_token_encrypted text,
    token_expires_at timestamptz,
    scope text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS google_oauth_states (
    state_hash varchar(64) PRIMARY KEY,
    user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    movie_id integer REFERENCES movies(id) ON DELETE CASCADE,
    expires_at timestamptz NOT NULL,
    consumed_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_google_oauth_states_user ON google_oauth_states(user_id);
CREATE INDEX IF NOT EXISTS ix_google_oauth_states_movie ON google_oauth_states(movie_id);
CREATE INDEX IF NOT EXISTS ix_google_oauth_states_expires ON google_oauth_states(expires_at);
CREATE TABLE IF NOT EXISTS calendar_reminders (
    id serial PRIMARY KEY,
    user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    movie_id integer NOT NULL REFERENCES movies(id) ON DELETE CASCADE,
    google_event_id varchar(255) NOT NULL UNIQUE,
    release_date date NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(user_id, movie_id)
);
CREATE INDEX IF NOT EXISTS ix_calendar_reminders_user ON calendar_reminders(user_id);
CREATE INDEX IF NOT EXISTS ix_calendar_reminders_movie ON calendar_reminders(movie_id);
ALTER TABLE google_calendar_connections ENABLE ROW LEVEL SECURITY;
ALTER TABLE google_oauth_states ENABLE ROW LEVEL SECURITY;
ALTER TABLE calendar_reminders ENABLE ROW LEVEL SECURITY;
