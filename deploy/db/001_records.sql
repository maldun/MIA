-- Schema 1 of the shared state (N-3.1, REQ-SLY-001): one table of record versions for all tables of IF-102.
-- A version is written once and never changed; the primary key refuses a second writer of the same version number (the loser gets a conflict).
CREATE TABLE IF NOT EXISTS schema_version (
    version integer PRIMARY KEY,
    applied timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS records (
    tbl     text    NOT NULL,
    id      text    NOT NULL,
    version integer NOT NULL CHECK (version >= 1),
    author  text    NOT NULL,
    time    text    NOT NULL,
    doc     jsonb   NOT NULL,
    PRIMARY KEY (tbl, id, version)
);

INSERT INTO schema_version (version) VALUES (1) ON CONFLICT DO NOTHING;
