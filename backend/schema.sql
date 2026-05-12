CREATE TABLE "Usuarios" (
    id BIGSERIAL PRIMARY KEY,
    nome VARCHAR(150) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    senha_hash TEXT NOT NULL,
    criado_em TIMESTAMPTZ DEFAULT NOW()
);

-- Tabela de sintomas registrados
CREATE TABLE "Sintomas" (
    id BIGSERIAL PRIMARY KEY,

    usuario_id BIGINT NOT NULL
        REFERENCES "Usuarios"(id)
        ON DELETE CASCADE,

    tipo VARCHAR(100) NOT NULL,
    subtipo VARCHAR(100),
    descricao TEXT,

    inicio TIMESTAMPTZ NOT NULL,
    fim TIMESTAMPTZ,

    criado_em TIMESTAMPTZ DEFAULT NOW(),
    atualizado_em TIMESTAMPTZ DEFAULT NOW()
);

-- Índice para buscas por usuário + data
CREATE INDEX "IX_Sintomas_UsuarioData"
    ON "Sintomas" (usuario_id, inicio);