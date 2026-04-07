DROP TABLE IF EXISTS tempo_processamento;

CREATE TABLE tempo_processamento (
    estado TEXT,
    ponto_entrada TEXT,
    entrada_hub1 TIMESTAMP,
    saida_hub1 TIMESTAMP,
    cliente TEXT,
    hiata TEXT,
    data DATE,
    data_snapshot DATE,
    nome_arquivo TEXT,
    data_importacao TIMESTAMP
);