CREATE TABLE IF NOT EXISTS users
(
    id         SERIAL PRIMARY KEY,
    email      text UNIQUE NOT NULL,
    pwhash     text        NOT NULL, -- Actually just a hash

    settings   jsonb,

    created_at timestamptz NOT NULL
);

CREATE TABLE IF NOT EXISTS datasets
(
    id         SERIAL PRIMARY KEY,
    name       VARCHAR(255) UNIQUE NOT NULL,

    info       jsonb, /* code info (git commit, dependencies, Docker image), description, etc. */

    created_at timestamptz         NOT NULL
);

CREATE TABLE IF NOT EXISTS samples
(
    id           SERIAL PRIMARY KEY,
    name         text                         NOT NULL,

    dataset_id   INT REFERENCES datasets (id) NOT NULL,

    info         jsonb, /* train-test-val, data_url, plot_url, other metadata */

    created_at   timestamptz                  NOT NULL,
    last_updated timestamptz                  NOT NULL,

    UNIQUE (dataset_id, name)
);