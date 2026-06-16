# 🌙 Sonhar Digital — Backend

Backend em Python/Flask para o sistema de gestão de vendas.

---

## 📋 Pré-requisitos

- Python 3.10+
- pip

---

## 🚀 Rodando localmente

### 1. Instalar dependências
```bash
pip install -r requirements.txt
```

### 2. Rodar o servidor
```bash
python app.py
```

O servidor sobe em: `http://localhost:5000`

---

## 🔗 Endpoints principais

### PostBack Sonhar Digital
```
POST /postback/sonhar
Header: X-Postback-Key: aeb82267e3b25c1d2debe5b4eaf64337
```
Recebe pedidos automáticos da Sonhar Digital.

### Autenticação
```
POST /api/login
Body: { "cpf": "000.000.000-00", "senha": "admin123" }
```

### Pedidos
```
GET    /api/pedidos              → listar todos
GET    /api/pedidos?status=pendente  → filtrar por status
POST   /api/pedidos              → criar pedido manual
PATCH  /api/pedidos/{id}/status  → atualizar status
DELETE /api/pedidos/{id}         → excluir
```

### Atendentes
```
GET    /api/atendentes       → listar
POST   /api/atendentes       → cadastrar
PUT    /api/atendentes/{id}  → atualizar
DELETE /api/atendentes/{id}  → excluir
```

### Dashboard
```
GET /api/resumo → KPIs gerais
```

---

## 🧪 Testar o PostBack

Com o servidor rodando:
```bash
python teste_postback.py
```

---

## ☁️ Deploy no Railway

### 1. Criar conta em railway.app

### 2. Instalar Railway CLI
```bash
npm install -g @railway/cli
railway login
```

### 3. Criar projeto e fazer deploy
```bash
railway init
railway up
```

### 4. Configurar variáveis de ambiente no Railway
```
POSTBACK_KEY = aeb82267e3b25c1d2debe5b4eaf64337
SECRET_KEY   = (gere uma chave aleatória segura)
DATABASE_URL = (Railway gera automaticamente com PostgreSQL)
```

### 5. Adicionar PostgreSQL
No painel do Railway → Add Plugin → PostgreSQL

### 6. URL do PostBack para configurar na Sonhar Digital
```
https://SEU-PROJETO.railway.app/postback/sonhar
```

---

## 🗄️ Banco de dados

| Tabela          | Descrição                        |
|-----------------|----------------------------------|
| usuarios        | Login e perfis (gestor/atendente)|
| atendentes      | Cadastro dos atendentes          |
| pedidos         | Pedidos recebidos e pré-vendas   |
| atividades_dia  | Leads e ligações por dia         |

---

## 🔐 Usuário padrão (criado automaticamente)

| Campo | Valor           |
|-------|-----------------|
| CPF   | 000.000.000-00  |
| Senha | admin123        |
| Perfil| Gestor          |

> ⚠️ Mude a senha após o primeiro acesso!
