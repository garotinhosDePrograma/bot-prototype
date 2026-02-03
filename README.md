# 🤖 Bot Worker - Chatbot Inteligente Multi-Fonte

> Sistema de chatbot inteligente que busca informações em múltiplas APIs (Wolfram Alpha, Google, DuckDuckGo, Wikipedia), combina as respostas de forma inteligente e armazena histórico completo no banco de dados.

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.3+-green.svg)](https://flask.palletsprojects.com/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0+-orange.svg)](https://www.mysql.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📋 Índice

- [Sobre o Projeto](#-sobre-o-projeto)
- [Funcionalidades](#-funcionalidades)
- [Arquitetura](#-arquitetura)
- [Tecnologias](#-tecnologias)
- [Instalação](#-instalação)
- [Configuração](#-configuração)
- [Uso da API](#-uso-da-api)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [Como Funciona](#-como-funciona)
- [Banco de Dados](#-banco-de-dados)
- [Desenvolvimento](#-desenvolvimento)
- [Roadmap](#-roadmap)

---

## 🎯 Sobre o Projeto

O **Bot Worker** é um chatbot inteligente que não depende de modelos de linguagem (LLMs) para funcionar. Em vez disso, ele:

1. **Analisa a pergunta** usando NLP (spaCy)
2. **Busca em múltiplas APIs** simultaneamente (Wolfram Alpha, Google Custom Search, DuckDuckGo, Wikipedia)
3. **Combina as respostas** de forma inteligente usando TF-IDF e similaridade cossenoidal
4. **Traduz automaticamente** entre português e inglês
5. **Armazena todo o histórico** no banco de dados MySQL
6. **Disponibiliza via API REST** para integração com qualquer frontend

---

## ✨ Funcionalidades

### 🔍 Busca Inteligente
- ✅ Busca paralela em 4 APIs diferentes
- ✅ Combinação inteligente de respostas
- ✅ Sistema de cache (respostas < 0.1s)
- ✅ Detecção automática de idioma
- ✅ Tradução bidirecional (PT ↔ EN)

### 🧠 Processamento de Linguagem Natural
- ✅ Análise de intenção (saudação, pergunta, despedida)
- ✅ Detecção de tipo de pergunta (qual, quem, como, por que, quando)
- ✅ Extração de palavras-chave
- ✅ Formatação contextual de respostas

### 💾 Persistência e Histórico
- ✅ Armazenamento de todas as conversas
- ✅ Histórico completo com paginação
- ✅ Busca em conversas antigas
- ✅ Estatísticas detalhadas por usuário
- ✅ Metadata JSON com logs de processo

### 👥 Sistema de Usuários
- ✅ Autenticação JWT
- ✅ Cadastro e login
- ✅ Histórico individual por usuário
- ✅ Controle de acesso (ownership)

---

## 🏗️ Arquitetura

```
┌─────────────┐
│  Frontend   │
│ (Separado)  │
└──────┬──────┘
       │ HTTP/REST
       ▼
┌─────────────────────────────────────┐
│         Flask API (Backend)         │
├─────────────────────────────────────┤
│  Controllers (Rotas HTTP)           │
│    ├─ bot_controller.py             │
│    └─ user_controller.py            │
├─────────────────────────────────────┤
│  Workers (Lógica de Negócio)        │
│    ├─ bot_worker.py                 │
│    └─ user_worker.py                │
├─────────────────────────────────────┤
│  Repositories (Acesso ao Banco)     │
│    ├─ bot_repository.py             │
│    └─ user_repository.py            │
├─────────────────────────────────────┤
│  Models (Entidades)                 │
│    ├─ bot_conversation.py           │
│    └─ user.py                       │
└─────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│  Bot Engine (Núcleo de IA)          │
├─────────────────────────────────────┤
│  API Search (Buscadores)            │
│    ├─ Wolfram Alpha                 │
│    ├─ Google Custom Search          │
│    ├─ DuckDuckGo                    │
│    └─ Wikipedia                     │
├─────────────────────────────────────┤
│  NLP Utils                          │
│    ├─ question_analyzer.py          │
│    ├─ response_combiner.py          │
│    ├─ response_formatter.py         │
│    └─ text_utils.py                 │
└─────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│      MySQL Database                 │
│  ├─ usuarios                        │
│  └─ bot_conversations               │
└─────────────────────────────────────┘
```

### 🎯 Padrão de Arquitetura

**Model → Repository → Worker → Controller**

- **Models**: Classes que representam entidades do banco
- **Repositories**: Acesso direto ao banco de dados (CRUD)
- **Workers**: Lógica de negócio e orquestração
- **Controllers**: Rotas HTTP e validação de entrada

---

## 🛠️ Tecnologias

### Backend
- **Flask** - Framework web minimalista
- **Flask-CORS** - Suporte a Cross-Origin Resource Sharing
- **MySQL Connector** - Driver oficial MySQL
- **Python 3.8+** - Linguagem base

### NLP & Machine Learning
- **spaCy** - Processamento de linguagem natural
  - Modelo: `pt_core_news_sm` (português)
- **scikit-learn** - TF-IDF e similaridade cossenoidal
- **langdetect** - Detecção automática de idioma
- **deep-translator** - Tradução (Google Translate API)

### APIs Externas
- **Wolfram Alpha API** - Respostas matemáticas/científicas
- **Google Custom Search API** - Busca web geral
- **DuckDuckGo API** - Busca alternativa (sem API key)
- **Wikipedia API** - Conhecimento enciclopédico

### Utilitários
- **cachetools** - Cache em memória (TTL)
- **bcrypt** - Hash de senhas
- **PyJWT** - Tokens de autenticação
- **python-dotenv** - Variáveis de ambiente

### Infraestrutura
- **Railway** - Hospedagem do banco MySQL
- **Replit** (opcional) - Deploy da aplicação

---

## 📦 Instalação

### 1️⃣ Clone o repositório

```bash
git clone https://github.com/seu-usuario/bot-worker.git
cd bot-worker
```

### 2️⃣ Crie um ambiente virtual

```bash
python -m venv venv

# Linux/Mac
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3️⃣ Instale as dependências

```bash
pip install -r requirements.txt
```

### 4️⃣ Baixe o modelo spaCy

```bash
python -m spacy download pt_core_news_sm
```

### 5️⃣ Configure as variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
# Banco de dados (Railway ou local)
CONN_URL=mysql://usuario:senha@host:porta/database

# APIs externas
WOLFRAM_APP_ID=seu_app_id_wolfram
GOOGLE_CX=seu_custom_search_engine_id
GOOGLE_API_KEY=sua_google_api_key

# JWT (para autenticação)
SECRET_KEY=sua_chave_secreta_aqui
```

### 6️⃣ Crie as tabelas no banco

```bash
# Tabela de usuários
python script.py

# Tabela de conversas do bot
python migrations/create_bot_conversations_table.py
```

### 7️⃣ Inicie o servidor

```bash
python app.py
```

A API estará disponível em `http://localhost:5000`

---

## ⚙️ Configuração

### Obter API Keys

#### Wolfram Alpha
1. Acesse https://products.wolframalpha.com/api/
2. Crie uma conta gratuita
3. Obtenha seu App ID (2.000 queries/mês grátis)

#### Google Custom Search
1. Acesse https://programmablesearchengine.google.com/
2. Crie um novo search engine
3. Anote o **Search Engine ID (CX)**
4. Ative a API em https://console.cloud.google.com/
5. Crie uma **API Key** (100 queries/dia grátis)

#### DuckDuckGo & Wikipedia
- Não requerem API keys! ✅

### Configurar Railway (Banco de Dados)

1. Acesse https://railway.app/
2. Crie um novo projeto MySQL
3. Copie a `CONN_URL` fornecida
4. Cole no arquivo `.env`

---

## 📡 Uso da API

### Autenticação

Todas as rotas do bot aceitam `user_id` opcional. Para rotas protegidas de usuário, use JWT:

```bash
# 1. Login
curl -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"email":"usuario@email.com","senha":"123456"}'

# Resposta: {"token": "eyJ...", "user": {...}}

# 2. Use o token em requisições protegidas
curl -X GET http://localhost:5000/api/all \
  -H "Authorization: Bearer eyJ..."
```

### 🤖 Endpoints do Bot

#### 1. Fazer uma pergunta

```bash
POST /api/bot/question
```

**Request:**
```json
{
  "pergunta": "Qual a capital da França?",
  "user_id": 1  // opcional
}
```

**Response:**
```json
{
  "status": "success",
  "query": "Qual a capital da França?",
  "response": "Paris é a capital e a cidade mais populosa da França...",
  "source": "google",
  "processing_time": 1.234,
  "user_id": 1
}
```

#### 2. Buscar histórico

```bash
GET /api/bot/history?user_id=1&limit=20&offset=0
```

**Response:**
```json
{
  "status": "success",
  "conversations": [
    {
      "id": 1,
      "pergunta": "Qual a capital da França?",
      "resposta_preview": "Paris é a capital...",
      "fonte": "google",
      "tempo_processamento": 1.23,
      "created_at": "2024-01-29T10:30:00"
    }
  ],
  "pagination": {
    "total": 50,
    "limit": 20,
    "offset": 0,
    "has_more": true
  }
}
```

#### 3. Buscar conversa específica

```bash
GET /api/bot/conversation/1
```

#### 4. Buscar por palavra-chave

```bash
GET /api/bot/search?user_id=1&q=França
```

#### 5. Deletar conversa

```bash
DELETE /api/bot/conversation/1
Content-Type: application/json

{"user_id": 1}
```

#### 6. Estatísticas do usuário

```bash
GET /api/bot/stats?user_id=1
```

**Response:**
```json
{
  "status": "success",
  "statistics": {
    "total_perguntas": 50,
    "tempo_medio": 1.23,
    "cache_hits": 15,
    "taxa_cache": 30.0,
    "sucessos": 48,
    "erros": 2,
    "taxa_sucesso": 96.0,
    "fontes_mais_usadas": [
      {"fonte": "google", "count": 25},
      {"fonte": "wolfram", "count": 15}
    ]
  }
}
```

#### 7. Limpar histórico completo

```bash
DELETE /api/bot/history/clear
Content-Type: application/json

{"user_id": 1}
```

#### 8. Health check

```bash
GET /api/bot/health
```

### 👥 Endpoints de Usuário

#### Registrar

```bash
POST /api/register
```

```json
{
  "nome": "João Silva",
  "email": "joao@email.com",
  "senha": "senha123"
}
```

#### Login

```bash
POST /api/login
```

```json
{
  "email": "joao@email.com",
  "senha": "senha123"
}
```

#### Listar todos

```bash
GET /api/all
```

---

## 📁 Estrutura do Projeto

```
bot-worker/
│
├── app.py                      # Aplicação Flask principal
├── requirements.txt            # Dependências Python
├── .env                        # Variáveis de ambiente (não commitado)
├── .gitignore                  # Arquivos ignorados pelo Git
├── script.py                   # Script para criar tabela usuarios
│
├── migrations/                 # Scripts de migração do banco
│   └── create_bot_conversations_table.py
│
├── models/                     # Entidades do banco
│   ├── __init__.py
│   ├── user.py                 # Model de usuário
│   └── bot_conversation.py     # Model de conversa do bot
│
├── repositories/               # Acesso ao banco de dados
│   ├── __init__.py
│   ├── user_repository.py      # CRUD de usuários
│   └── bot_repository.py       # CRUD de conversas
│
├── workers/                    # Lógica de negócio
│   ├── __init__.py
│   ├── user_worker.py          # Lógica de autenticação
│   └── bot_worker.py           # Orquestração do bot
│
├── controllers/                # Rotas da API
│   ├── __init__.py
│   ├── user_controller.py      # Endpoints de usuário
│   └── bot_controller.py       # Endpoints do bot
│
├── bot/                        # Núcleo do bot (engine)
│   ├── api/
│   │   ├── __init__.py
│   │   └── search.py           # Buscadores de API
│   │
│   └── utils/
│       ├── __init__.py
│       ├── config.py           # Configurações
│       ├── text_utils.py       # Utilitários de texto
│       ├── question_analyzer.py     # Análise de perguntas
│       ├── response_combiner.py     # Combinação de respostas
│       └── response_formatter.py    # Formatação final
│
├── utils/                      # Utilitários gerais
│   ├── __init__.py
│   └── db.py                   # Conexão com banco (pool)
│
└── bot/logs/                   # Logs de execução (opcional)
    └── *.json
```

---

## 🔄 Como Funciona

### 1️⃣ Fluxo de uma Pergunta

```
Usuário faz pergunta
        ↓
BotController recebe POST /api/bot/question
        ↓
BotWorker.process_query()
        ↓
┌───────────────────────────────────┐
│   Análise da Pergunta (NLP)      │
│   ├─ Detecta intenção             │
│   ├─ Identifica tipo (qual/como)  │
│   └─ Extrai palavras-chave        │
└───────────────────────────────────┘
        ↓
┌───────────────────────────────────┐
│   Busca em APIs (Paralelo)        │
│   ├─ Wolfram Alpha                │
│   ├─ Google Custom Search         │
│   ├─ DuckDuckGo                   │
│   └─ Wikipedia                    │
└───────────────────────────────────┘
        ↓
┌───────────────────────────────────┐
│   Combinação Inteligente          │
│   ├─ Calcula relevância (TF-IDF)  │
│   ├─ Remove duplicatas            │
│   └─ Mescla melhores fontes       │
└───────────────────────────────────┘
        ↓
┌───────────────────────────────────┐
│   Formatação & Tradução           │
│   ├─ Formata resposta             │
│   ├─ Traduz para português        │
│   └─ Limpa texto                  │
└───────────────────────────────────┘
        ↓
BotRepository.create_conversation()
        ↓
Salva no banco MySQL
        ↓
Retorna resposta ao usuário
```

### 2️⃣ Sistema de Cache

- Perguntas normalizadas são usadas como chave
- Cache em memória (TTL de 1 hora)
- Respostas < 0.1s são consideradas cache hits
- Cache é compartilhado entre usuários

### 3️⃣ Combinação de Respostas

#### Para perguntas factuais (qual, quem, onde):
- Usa apenas a fonte mais relevante

#### Para perguntas explicativas (como, por que):
- Combina informações de até 3 fontes
- Remove sentenças duplicadas
- Ordena por relevância

---

## 🗄️ Banco de Dados

### Tabela: `usuarios`

```sql
CREATE TABLE usuarios (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nome VARCHAR(200) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    senha VARCHAR(255) NOT NULL
);
```

### Tabela: `bot_conversations`

```sql
CREATE TABLE bot_conversations (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    pergunta TEXT NOT NULL,
    resposta TEXT NOT NULL,
    fonte VARCHAR(100),
    tempo_processamento FLOAT,
    status VARCHAR(20) DEFAULT 'success',
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    INDEX idx_user_created (user_id, created_at DESC),
    INDEX idx_status (status),
    INDEX idx_fonte (fonte)
);
```

### Campos de Metadata (JSON)

```json
{
  "logs_processo": [...],
  "cache_usado": false,
  "tipo_pergunta": "qual",
  "intencao": "conhecimento"
}
```

---

## 🚀 Desenvolvimento

### Executar em modo desenvolvimento

```bash
# Com reload automático
flask --app app run --debug --reload

# Ou
python app.py
```

### Testar endpoints

```bash
# Usando o script de testes
python teste.py

# Ou manualmente com curl
curl -X POST http://localhost:5000/api/bot/question \
  -H "Content-Type: application/json" \
  -d '{"pergunta":"Oi","user_id":1}'
```

### Adicionar nova API de busca

1. Edite `bot/api/search.py`
2. Adicione método `buscar_nova_api()`
3. Inclua no `buscar_todas()`
4. Atualize `ordem_preferencia` no `buscar_melhor()`

### Adicionar novo tipo de pergunta

1. Edite `bot/utils/question_analyzer.py`
2. Adicione lógica em `detectar_tipo_pergunta()`
3. Atualize `bot/utils/response_formatter.py` para formatação

---

## 🗺️ Roadmap

### ✅ Concluído
- [x] Sistema de busca multi-fonte
- [x] Análise NLP de perguntas
- [x] Combinação inteligente de respostas
- [x] Sistema de cache
- [x] Autenticação JWT
- [x] Histórico de conversas
- [x] Estatísticas por usuário
- [x] API REST completa

### 🔜 Próximos Passos

#### Backend
- [ ] Rate limiting por usuário
- [ ] Sistema de favoritos (marcar conversas)
- [ ] Exportação de histórico (CSV/JSON)
- [ ] WebSockets para respostas em tempo real
- [ ] Suporte a imagens nas respostas
- [ ] Sistema de tags para conversas
- [ ] Métricas de qualidade de resposta

#### Frontend
- [ ] Interface web em React/Next.js
- [ ] Dashboard com gráficos
- [ ] Chat em tempo real
- [ ] Tema claro/escuro
- [ ] PWA (Progressive Web App)
- [ ] Aplicativo mobile (React Native)

#### Inteligência
- [ ] Aprendizado com feedback do usuário
- [ ] Sugestões de perguntas relacionadas
- [ ] Detecção de contexto entre perguntas
- [ ] Suporte a múltiplos idiomas
- [ ] Integração com mais APIs

---

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

---

## 👨‍💻 Autor

Desenvolvido por [Luiz Fagner]

- GitHub: [@WirkLichKeit1](https://github.com/WirkLichKeit1)

---

## 📞 Suporte

Encontrou um bug? Tem uma sugestão?

- Abra uma [issue](https://github.com/WirkLichKeit1/bot-prototype/issues)
- Envie um [pull request](https://github.com/WirkLichKeit1/bot-prototype/pulls)

---

**⭐ Se este projeto foi útil, deixe uma estrela no GitHub!**
