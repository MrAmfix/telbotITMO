CREATE TABLE IF NOT EXISTS users (
    user_id VARCHAR(50) PRIMARY KEY,
    full_name VARCHAR(100),
    is_check_logs INTEGER DEFAULT 0,
    templates JSONB
);
CREATE TABLE IF NOT EXISTS notes (
    note_id INTEGER PRIMARY KEY,
    time_range VARCHAR(50),
    student_id VARCHAR(50),
    logs VARCHAR(300)[]
);
CREATE TABLE IF NOT EXISTS table_notes (
    table_id INTEGER PRIMARY KEY,
    notes_id INTEGER[],
    creator_id VARCHAR(50)
);
CREATE TABLE IF NOT EXISTS dict (
    dict_key INTEGER PRIMARY KEY,
    dict_value VARCHAR(200)
);
CREATE TABLE IF NOT EXISTS logs (
    log_text VARCHAR(300)
);
INSERT INTO notes (note_id) VALUES (0) ON CONFLICT DO NOTHING;
INSERT INTO table_notes (table_id) VALUES (0) ON CONFLICT DO NOTHING;
INSERT INTO dict (dict_key) VALUES (0) ON CONFLICT DO NOTHING