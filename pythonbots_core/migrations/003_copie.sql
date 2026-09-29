CREATE TABLE IF NOT EXISTS core_copie (
    impronta  VARCHAR(64) NOT NULL,
    persona   VARCHAR(64) NOT NULL,
    scade     INTEGER NOT NULL,
    usato     INTEGER NOT NULL,
    PRIMARY KEY (impronta)
);
