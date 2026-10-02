-- Apply after 002_google_calendar.sql through the Supabase SQL editor.
ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_type varchar(16);
ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_ref varchar(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_upload_ref varchar(255);
