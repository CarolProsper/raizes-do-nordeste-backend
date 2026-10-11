-- Ajustes necessários para CPF e vínculo entre usuário e cliente.
-- Pode ser executado mais de uma vez.

ALTER TABLE cliente
    ADD COLUMN IF NOT EXISTS cpf VARCHAR(11);

CREATE UNIQUE INDEX IF NOT EXISTS uq_cliente_cpf
    ON cliente (cpf)
    WHERE cpf IS NOT NULL;

ALTER TABLE usuario
    ADD COLUMN IF NOT EXISTS id_cliente INTEGER;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conrelid = 'usuario'::regclass
          AND confrelid = 'cliente'::regclass
          AND contype = 'f'
          AND conkey = ARRAY[
              (
                  SELECT attnum
                  FROM pg_attribute
                  WHERE attrelid = 'usuario'::regclass
                    AND attname = 'id_cliente'
              )
          ]::smallint[]
    ) THEN
        ALTER TABLE usuario
            ADD CONSTRAINT usuario_id_cliente_fkey
            FOREIGN KEY (id_cliente)
            REFERENCES cliente (id_cliente);
    END IF;
END $$;

CREATE UNIQUE INDEX IF NOT EXISTS uq_usuario_id_cliente
    ON usuario (id_cliente)
    WHERE id_cliente IS NOT NULL;
