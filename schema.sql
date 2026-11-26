PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS intencao (
    id INTEGER PRIMARY KEY,
    codigo TEXT NOT NULL UNIQUE,
    horario_previsto TEXT NOT NULL,
    criada_em TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS visita (
    id INTEGER PRIMARY KEY REFERENCES intencao(id),
    check_in_em TEXT NOT NULL,
    buffet_concluido_em TEXT CHECK (buffet_concluido_em >= check_in_em),
    check_out_em TEXT CHECK (
        check_out_em IS NULL OR
        (buffet_concluido_em IS NOT NULL AND check_out_em >= buffet_concluido_em)
    )
);

CREATE TABLE IF NOT EXISTS avaliacao (
    visita_id INTEGER PRIMARY KEY REFERENCES visita(id),
    nota_nps INTEGER NOT NULL CHECK (nota_nps BETWEEN 0 AND 10),
    comentario TEXT NOT NULL DEFAULT ''
);

CREATE VIEW IF NOT EXISTS jornada AS
SELECT i.codigo AS codigo_visita, i.horario_previsto,
       v.check_in_em, v.buffet_concluido_em, v.check_out_em,
       a.nota_nps, a.comentario
FROM intencao i
LEFT JOIN visita v ON v.id = i.id
LEFT JOIN avaliacao a ON a.visita_id = v.id;
