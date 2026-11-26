-- Bovinu's Connect — banco v2
-- Horários em UTC ISO 8601 (ex.: 2026-11-25T15:30:00.000+00:00).
-- Datas de cardápio em data local de São Paulo (AAAA-MM-DD).
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS parametro (
    chave TEXT PRIMARY KEY,
    valor TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS cliente (
    id INTEGER PRIMARY KEY,
    nome TEXT NOT NULL CHECK (length(trim(nome)) BETWEEN 2 AND 80),
    celular TEXT NOT NULL UNIQUE CHECK (length(celular) BETWEEN 10 AND 11),  -- só dígitos, com DDD
    consentimento_em TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS prato (
    id INTEGER PRIMARY KEY,
    nome TEXT NOT NULL CHECK (length(trim(nome)) BETWEEN 2 AND 60),
    categoria TEXT NOT NULL CHECK (categoria IN ('churrasco', 'acompanhamento', 'salada', 'sobremesa')),
    descricao TEXT NOT NULL DEFAULT '' CHECK (length(descricao) <= 120),
    vegetariano INTEGER NOT NULL DEFAULT 0 CHECK (vegetariano IN (0, 1))
);

CREATE TABLE IF NOT EXISTS cardapio_dia (
    data TEXT NOT NULL,
    prato_id INTEGER NOT NULL REFERENCES prato(id),
    destaque INTEGER NOT NULL DEFAULT 0 CHECK (destaque IN (0, 1)),
    PRIMARY KEY (data, prato_id)
);

CREATE TABLE IF NOT EXISTS intencao (
    id INTEGER PRIMARY KEY,
    codigo TEXT NOT NULL UNIQUE,
    cliente_id INTEGER REFERENCES cliente(id),
    horario_previsto TEXT NOT NULL,
    pessoas INTEGER NOT NULL DEFAULT 1 CHECK (pessoas BETWEEN 1 AND 20),
    criada_em TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS intencao_prato (
    intencao_id INTEGER NOT NULL REFERENCES intencao(id) ON DELETE CASCADE,
    prato_id INTEGER NOT NULL REFERENCES prato(id),
    PRIMARY KEY (intencao_id, prato_id)
);

-- Buffet é opcional: o check-out só exige o check-in.
CREATE TABLE IF NOT EXISTS visita (
    id INTEGER PRIMARY KEY,
    codigo TEXT NOT NULL UNIQUE,
    origem TEXT NOT NULL CHECK (origem IN ('planejado', 'espontaneo')),
    intencao_id INTEGER UNIQUE REFERENCES intencao(id),
    cliente_id INTEGER REFERENCES cliente(id),
    check_in_em TEXT NOT NULL,
    buffet_concluido_em TEXT CHECK (buffet_concluido_em IS NULL OR buffet_concluido_em >= check_in_em),
    check_out_em TEXT CHECK (check_out_em IS NULL OR check_out_em >= check_in_em),
    mesa INTEGER CHECK (mesa IS NULL OR mesa BETWEEN 1 AND 999),
    saida_estimada INTEGER NOT NULL DEFAULT 0 CHECK (saida_estimada IN (0, 1)),
    CHECK ((origem = 'planejado') = (intencao_id IS NOT NULL))
);

CREATE TABLE IF NOT EXISTS avaliacao (
    visita_id INTEGER PRIMARY KEY REFERENCES visita(id),
    nota_nps INTEGER NOT NULL CHECK (nota_nps BETWEEN 0 AND 10),
    nota_buffet INTEGER NOT NULL CHECK (nota_buffet BETWEEN 1 AND 5),
    nota_espera INTEGER NOT NULL CHECK (nota_espera BETWEEN 1 AND 5),
    nota_atendimento INTEGER NOT NULL CHECK (nota_atendimento BETWEEN 1 AND 5),
    comentario TEXT NOT NULL DEFAULT '' CHECK (length(comentario) <= 500),
    criada_em TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_intencao_previsto ON intencao(horario_previsto);
CREATE INDEX IF NOT EXISTS idx_visita_check_in ON visita(check_in_em);
CREATE INDEX IF NOT EXISTS idx_visita_aberta ON visita(check_out_em) WHERE check_out_em IS NULL;
CREATE INDEX IF NOT EXISTS idx_visita_cliente ON visita(cliente_id);
CREATE INDEX IF NOT EXISTS idx_intencao_prato_prato ON intencao_prato(prato_id);

-- Uma linha por visita ou por intenção ainda sem visita (para a conversão).
DROP VIEW IF EXISTS jornada;
CREATE VIEW jornada AS
SELECT COALESCE(v.codigo, i.codigo) AS codigo,
       COALESCE(v.origem, 'planejado') AS origem,
       i.id AS intencao_id, v.id AS visita_id,
       COALESCE(v.cliente_id, i.cliente_id) AS cliente_id,
       i.horario_previsto, i.pessoas,
       v.check_in_em, v.buffet_concluido_em, v.check_out_em, v.mesa,
       COALESCE(v.saida_estimada, 0) AS saida_estimada,
       a.nota_nps, a.nota_buffet, a.nota_espera, a.nota_atendimento, a.comentario
FROM intencao i
LEFT JOIN visita v ON v.intencao_id = i.id
LEFT JOIN avaliacao a ON a.visita_id = v.id
UNION ALL
SELECT v.codigo, v.origem, NULL, v.id, v.cliente_id, NULL, NULL,
       v.check_in_em, v.buffet_concluido_em, v.check_out_em, v.mesa, v.saida_estimada,
       a.nota_nps, a.nota_buffet, a.nota_espera, a.nota_atendimento, a.comentario
FROM visita v
LEFT JOIN avaliacao a ON a.visita_id = v.id
WHERE v.intencao_id IS NULL;

PRAGMA user_version = 2;
