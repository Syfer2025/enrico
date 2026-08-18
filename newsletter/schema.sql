-- schema.sql — as três tabelas da newsletter.
--
-- Roda uma vez, na criação do banco:
--   npx wrangler d1 execute enrico-newsletter --remote --file=newsletter/schema.sql
--
-- Sobre o que NÃO está aqui: nome, sobrenome, cidade, data de nascimento,
-- interesses. Uma lista de textos precisa do endereço e da prova de que a
-- pessoa consentiu. Todo campo a mais é um campo que vaza junto se o banco
-- vazar, e que a LGPD obriga a justificar.

CREATE TABLE IF NOT EXISTS inscritos (
  -- Em minúsculas e sem espaço nas pontas, normalizado antes de gravar. Sem
  -- truque de "remover pontos do gmail": isso vale para um provedor só, e
  -- tratar dois endereços diferentes como o mesmo é errar em silêncio.
  email             TEXT PRIMARY KEY,

  -- 'pendente' até o clique no e-mail de confirmação; 'confirmado' depois.
  -- Quem cancela não vira um terceiro estado: a linha é APAGADA.
  estado            TEXT NOT NULL DEFAULT 'pendente',

  -- Os dois links que vão por e-mail, guardados como hash SHA-256. O que
  -- viaja é o token cru; aqui fica só o resumo dele. Assim, quem puser os
  -- olhos no banco não consegue confirmar nem cancelar por ninguém.
  confirmar_hash    TEXT,
  confirmar_expira  INTEGER,
  cancelar_hash     TEXT NOT NULL,

  criado_em         INTEGER NOT NULL,
  confirmado_em     INTEGER,

  -- Prova de consentimento, que a LGPD pede: quando, de qual página, e de
  -- qual rede — esta ÚLTIMA como hash com sal, não como IP. O IP identifica
  -- uma pessoa; o hash serve para o que o registro precisa (mostrar que
  -- inscrições diferentes vieram de lugares diferentes) e não identifica.
  origem            TEXT,
  rede_hash         TEXT
);

CREATE INDEX IF NOT EXISTS inscritos_confirmar ON inscritos (confirmar_hash);
CREATE INDEX IF NOT EXISTS inscritos_cancelar  ON inscritos (cancelar_hash);
CREATE INDEX IF NOT EXISTS inscritos_estado    ON inscritos (estado);

-- Um envio por texto. A chave é o slug, então mandar o mesmo texto duas vezes
-- não acontece por acidente — que é o acidente clássico de newsletter.
CREATE TABLE IF NOT EXISTS envios (
  slug          TEXT PRIMARY KEY,
  titulo        TEXT,
  iniciado_em   INTEGER NOT NULL,
  terminado_em  INTEGER
);

-- Quem já recebeu qual texto. Existe porque o envio é feito em pedaços: o
-- Worker manda algumas dezenas por chamada e volta dizendo quantas faltam.
-- Sem esta tabela, uma chamada repetida mandaria o texto de novo para quem já
-- tinha recebido.
CREATE TABLE IF NOT EXISTS envio_feito (
  slug        TEXT NOT NULL,
  email       TEXT NOT NULL,
  quando      INTEGER NOT NULL,
  PRIMARY KEY (slug, email)
);

-- Limite de tentativas por rede, para o formulário não virar máquina de
-- mandar e-mail para endereço de terceiro. Linhas velhas são apagadas na
-- própria checagem.
CREATE TABLE IF NOT EXISTS tentativas (
  rede_hash   TEXT NOT NULL,
  quando      INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS tentativas_rede ON tentativas (rede_hash, quando);
