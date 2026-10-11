# Raízes do Nordeste — Backend

## 1. Descrição

O Raízes do Nordeste é um sistema backend para centralizar e gerenciar
operações de uma rede de restaurantes, incluindo clientes, unidades,
produtos, estoque, pedidos, pagamentos e programa de fidelidade.

O sistema foi desenvolvido com Python, FastAPI e PostgreSQL.

## 2. Tecnologias utilizadas

- Python 3.12
- FastAPI
- SQLAlchemy
- PostgreSQL
- Pydantic
- JWT para autenticação
- Pytest para testes automatizados

## 3. Requisitos

- Python 3.12 ou compatível
- PostgreSQL
- pip

## 4. Instalação

Clone ou copie o projeto para sua máquina e acesse a pasta:

```bash
cd ~/raizes-do-nordeste-backend
```

Crie o ambiente virtual, caso ainda não exista:

```bash
python3 -m venv .venv
```

Ative o ambiente virtual:

```bash
source .venv/bin/activate
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

## 5. Banco de dados

O projeto utiliza PostgreSQL como banco de dados relacional.

As configurações de conexão são definidas pelas variáveis de ambiente presentes no arquivo `.env`. Para preparar o ambiente local:

1. Copie `.env.example` para `.env`.
2. Preencha as credenciais e gere uma chave secreta própria.
3. Inicie o PostgreSQL com Docker Compose:

```bash
docker compose up -d postgres
```

4. Crie as tabelas definidas nos modelos:

```bash
python -m app.database.create_tables
```

Não compartilhe o arquivo `.env` nem utilize credenciais de desenvolvimento em produção.

## 6. Executar a aplicação

Com o ambiente virtual ativado, execute:

```bash
uvicorn app.main:app --reload
```

A aplicação ficará disponível em:

http://127.0.0.1:8000

Documentação interativa da API:

http://127.0.0.1:8000/docs

## 7. Funcionalidades

- Cadastro e consulta de clientes
- Consulta dos próprios pedidos pelo cliente autenticado, com validação do CPF
- Gerenciamento de unidades
- Cadastro e consulta de produtos
- Consulta da disponibilidade e quantidade de produtos por unidade
- Cadastro e consulta de estoque
- Criação e consulta de pedidos
- Inclusão de itens nos pedidos com validação de disponibilidade e quantidade em estoque
- Atualização do estoque ao incluir itens
- Registro e consulta de pagamentos
- Simulação de autorização e recusa de pagamentos
- Atualização de status dos pedidos
- Cancelamento de pedidos e devolução das quantidades ao estoque
- Programa de fidelidade e movimentação de pontos
- Gerenciamento de funcionários
- Registro e consulta de auditoria
- Autenticação e controle de acesso por perfil

## 8. Autenticação

As rotas protegidas exigem um token JWT válido e verificam o perfil autorizado para a operação.

Para consultar os pedidos próprios, o usuário deve estar autenticado com o perfil Cliente, possuir vínculo com um cadastro de cliente e informar o CPF correspondente.

A documentação interativa em /docs permite consultar os parâmetros, os códigos de resposta e os requisitos de autenticação de cada endpoint.

## 9. Testes automatizados

Com o ambiente virtual ativado, execute:

```bash
pytest -v
```

O projeto possui testes automatizados para validar regras de negócio,
autenticação, pedidos, estoque, pagamentos e outras funcionalidades.

Última validação registrada: 34 testes aprovados.

## 10. Estrutura do projeto

raizes-do-nordeste-backend/
├── app/
│   ├── core/
│   ├── database/
│   ├── routers/
│   ├── schemas/
│   └── main.py
├── scripts/
│   └── ajustes_banco.sql
├── tests/
│   ├── test_api.py
│   ├── test_regras_negocio.py
│   └── test_security.py
├── .env.example
├── .gitignore
├── docker-compose.yml
├── criar_usuario.py
├── requirements.txt
└── README.md


## 11. Observações

- Os pagamentos são simulados; não existe integração real com uma
  operadora ou instituição financeira.
- As credenciais, chaves JWT e configurações sensíveis devem ser
  protegidas em um ambiente de produção.
- Execute os testes antes de realizar alterações importantes.
