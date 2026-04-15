-- Migração: backlog_atual linha-a-linha → resumo agregado
-- Rodar no banco DATABASE_URL_BACKLOG (Neon)

DROP TABLE IF EXISTS backlog_atual;

CREATE TABLE backlog_atual (
    id                     SERIAL PRIMARY KEY,
    estado                 TEXT,
    cliente                TEXT,
    pre_entrega            TEXT,
    proximo_ponto          TEXT,
    faixa_backlog_snapshot TEXT,
    qtd                    INTEGER NOT NULL DEFAULT 0,
    horas_min              NUMERIC(8,2),
    horas_max              NUMERIC(8,2),
    horas_media            NUMERIC(8,2),
    entrada_hub1_mais_ant  TIMESTAMP,
    data_referencia        DATE,
    data_importacao        TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_backlog_atual_estado   ON backlog_atual (estado);
CREATE INDEX idx_backlog_atual_cliente  ON backlog_atual (cliente);
CREATE INDEX idx_backlog_atual_faixa    ON backlog_atual (faixa_backlog_snapshot);
CREATE INDEX idx_backlog_atual_data_ref ON backlog_atual (data_referencia);
