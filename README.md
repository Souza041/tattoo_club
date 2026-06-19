 # Tattoo Club — MVP

  App para reserva programada de dinheiro para tatuagens, marketplace de tatuadores e assembleia mensal entre clientes adimplentes. **MVP local, sem integração financeira real** — dinheiro é tratado como saldo
   virtual.

  ## Stack
  - Python 3.10+
  - FastAPI + SQLAlchemy + SQLite
  - Frontend HTML/CSS/JS vanilla servido pelo próprio FastAPI

  ## Como rodar

  ```bash
  cd backend
  python -m venv .venv
  # Windows:
  .venv\Scripts\activate
  # Linux/Mac:
  source .venv/bin/activate

  pip install -r requirements.txt
  copy .env.example .env        # ou cp no Linux/Mac
  uvicorn app.main:app --reload --port 8000
  ```

  Acesse: **http://localhost:8000**

  ## Contas de teste (criadas pelo seed)
  | Perfil | E-mail | Senha |
  |---|---|---|
  | Admin | admin@tattooclub.local | admin123 |
  | Cliente 1 | cliente1@tattooclub.local | cliente123 |
  | Cliente 2 | cliente2@tattooclub.local | cliente123 |
  | Cliente 3 | cliente3@tattooclub.local | cliente123 |
  | Tatuador | marina@tattooclub.local | artist123 |
  | Tatuador | caio@tattooclub.local | artist123 |
  | Tatuador | lara@tattooclub.local | artist123 |

  ## Fluxo de teste end-to-end
  1. Logue como **cliente1**, escolha um plano e um tatuador.
  2. Logue como **admin**, registre o pagamento do mês para cliente1.
  3. Ainda como admin, execute a assembleia do mês — cliente1 deve aparecer como contemplado se for sorteado.
  4. Logue como **cliente1**, vá em "Tattoo" e solicite o agendamento.
  5. Logue como **marina** (ou o tatuador escolhido), avance o status até `completed`.
  6. Volte como **cliente1** e libere o pagamento.
  7. Audite tudo no painel admin.

  ## Estrutura
  ```
  tattoo_club/
  ├── backend/
  │   ├── app/
  │   │   ├── main.py        # entry FastAPI
  │   │   ├── config.py
  │   │   ├── database.py
  │   │   ├── models.py      # SQLAlchemy
  │   │   ├── schemas.py     # Pydantic
  │   │   ├── security.py    # bcrypt + JWT
  │   │   ├── deps.py        # auth dependencies
  │   │   ├── seed.py        # popula admin/planos/etc
  │   │   └── routers/       # auth, public, client, artist, admin
  │   ├── requirements.txt
  │   └── .env.example
  ├── frontend/              # HTML/CSS/JS estático
  └── README.md
  ```

  ## Pontos de integração futura (já marcados no código)
  - `routers/admin.register_payment` — `# TODO_INTEGRATION_PIX`: substituir registro manual por webhook do gateway (Pix, cartão, etc).
  - `routers/client.release_payment` — `# TODO_INTEGRATION_PIX`: substituir baixa de saldo virtual por transferência real ao tatuador.

  ## Melhorias futuras sugeridas
  - **Migrations com Alembic** (hoje usa `create_all`).
  - **Pix/gateway** (Mercado Pago, Pagar.me, Stark Bank) com webhook idempotente.
  - **Notificações** por e-mail/push para resultado de assembleia.
  - **Upload de portfólio** dos tatuadores (S3 ou storage local).
  - **Chat cliente↔tatuador** dentro do app.
  - **Avaliação pós-serviço** (estrelas + comentário).
  - **Multi-tenant por estúdio** (cada estúdio com seus clientes/tatuadores).
  - **App mobile nativo** com React Native (consumindo a mesma API).
  - **Painel financeiro** com DRE simples por mês.
  - **2FA** para o admin.
  │   │   ├── main.py        # entry FastAPI
  │   │   ├── config.py
  │   │   ├── database.py
  │   │   ├── models.py      # SQLAlchemy
  │   │   ├── schemas.py     # Pydantic
  │   │   ├── security.py    # bcrypt + JWT
  │   │   ├── deps.py        # auth dependencies
  │   │   ├── seed.py        # popula admin/planos/etc
  │   │   └── routers/       # auth, public, client, artist, admin
  │   ├── requirements.txt
  │   └── .env.example
  ├── frontend/              # HTML/CSS/JS estático
  └── README.md
  ```

  ## Pontos de integração futura (já marcados no código)
  - `routers/admin.register_payment` — `# TODO_INTEGRATION_PIX`: substituir registro manual por webhook do gateway (Pix,
   cartão, etc).
  - `routers/client.release_payment` — `# TODO_INTEGRATION_PIX`: substituir baixa de saldo virtual por transferência
  real ao tatuador.

  ## Melhorias futuras sugeridas
  - **Migrations com Alembic** (hoje usa `create_all`).
  - **Pix/gateway** (Mercado Pago, Pagar.me, Stark Bank) com webhook idempotente.
  - **Notificações** por e-mail/push para resultado de assembleia.
  - **Upload de portfólio** dos tatuadores (S3 ou storage local).
  - **Chat cliente↔tatuador** dentro do app.
  - **Avaliação pós-serviço** (estrelas + comentário).
  - **Multi-tenant por estúdio** (cada estúdio com seus clientes/tatuadores).
  - **App mobile nativo** com React Native (consumindo a mesma API).
  - **Painel financeiro** com DRE simples por mês.
  - **Notificações** por e-mail/push para resultado de assembleia.
  - **Upload de portfólio** dos tatuadores (S3 ou storage local).
  - **Chat cliente↔tatuador** dentro do app.
  - **Avaliação pós-serviço** (estrelas + comentário).
  - **Multi-tenant por estúdio** (cada estúdio com seus clientes/tatuadores).
  - **App mobile nativo** com React Native (consumindo a mesma API).
  - **Painel financeiro** com DRE simples por mês.
  - **2FA** para o admin.
  - **Logs/auditoria** com tabela dedicada e exportação CSV.
  - **Sorteio público verificável** (commit-reveal com hash) para dar transparência.
  - **Termos de uso / política de privacidade** dentro do app (alinhar com LGPD).
  - **Renomear "assembleia"** para algo mais leve ("sorteio do mês") se for evitar conotação regulatória.

  ---
  Como rodar (resumo)

  cd tattoo_club/backend
  python -m venv .venv
  .venv\Scripts\activate          # Windows PowerShell
  pip install -r requirements.txt
  copy .env.example .env
  uvicorn app.main:app --reload --port 8000

  Abra http://localhost:8000 no navegador (use DevTools no modo mobile para sentir como app). Docs da API em http://localhost:8000/docs.