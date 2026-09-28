CREATE TABLE IF NOT EXISTS core_handler (
    nome       VARCHAR(128) NOT NULL,
    abilitato  INTEGER NOT NULL DEFAULT 1,
    PRIMARY KEY (nome)
);
