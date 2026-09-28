CREATE TABLE IF NOT EXISTS core_battito (
    chiave         VARCHAR(128) NOT NULL,
    ultimo_lavoro  VARCHAR(32),
    PRIMARY KEY (chiave)
);
