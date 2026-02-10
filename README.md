# 🤖 Bot Worker V2.0 - Chatbot Inteligente com ML Avançado

> Sistema de chatbot inteligente que combina **Machine Learning Avançado** (Ensemble + Topic Modeling + Ranqueamento) com **busca em 7 fontes** (Wolfram Alpha, Google, Wikipedia, arXiv, DBpedia, YouTube, DuckDuckGo), aprendizado contínuo e feedback do usuário.

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0-green.svg)](https://flask.palletsprojects.com/)
[![scikit--learn](https://img.shields.io/badge/scikit--learn-1.5-orange.svg)](https://scikit-learn.org/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0+-orange.svg)](https://www.mysql.com/)
[![TensorFlow](https://img.shields.io/badge/TensorFlow-2.16+-yellow.svg)](https://www.tensorflow.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📋 Índice

- [🎯 Sobre o Projeto](#-sobre-o-projeto)
- [✨ Funcionalidades](#-funcionalidades)
- [🏗️ Arquitetura](#️-arquitetura)
- [🧠 Machine Learning](#-machine-learning)
- [🔍 Fontes de Busca](#-fontes-de-busca)
- [🛠️ Tecnologias](#️-tecnologias)
- [📦 Instalação](#-instalação)
- [⚙️ Configuração](#️-configuração)
- [🚀 Deploy](#-deploy)
- [📡 API](#-api)
- [🔄 Retreinamento](#-retreinamento)
- [📊 Métricas](#-métricas)
- [🗺️ Roadmap](#️-roadmap)

---

## 🎯 Sobre o Projeto

O **Bot Worker V2.0** é um chatbot de próxima geração que **não depende de LLMs caras**. Em vez disso:

### 🚀 **Como Funciona**

1. **Analisa a pergunta** usando NLP avançado (spaCy + análise semântica)
2. **ML Ensemble prevê intenção** (Naive Bayes + Random Forest + Gradient Boosting + LSTM opcional)
3. **Ranqueia fontes inteligentemente** (ML + histórico de sucessos)
4. **Busca em paralelo** nas 7 melhores fontes (Wolfram, Google, Wikipedia, arXiv, DBpedia, YouTube, DuckDuckGo)
5. **Combina respostas** usando TF-IDF e similaridade semântica
6. **Aprende continuamente** com feedback e correções do usuário
7. **Armazena tudo** no MySQL com logs detalhados

### 🎯 **Diferenciais**

✅ **100% Gratuito** - Sem dependência de APIs pagas (LLMs)  
✅ **Ensemble ML** - 4 modelos votando para maior precisão  
✅ **7 Fontes** - Combina múltiplas fontes automaticamente  
✅ **Ranqueamento Inteligente** - ML aprende quais fontes funcionam melhor  
✅ **Topic Modeling** - LDA descobre padrões e tendências  
✅ **Aprendizado Contínuo** - Melhora com uso e feedback  
✅ **Modo Produção** - Otimizado para rodar com < 512 MB RAM  

---

## ✨ Funcionalidades

### 🔍 **Busca Inteligente**
- ✅ **7 fontes simultâneas** (Wolfram, Google, DuckDuckGo, Wikipedia, arXiv, DBpedia, YouTube)
- ✅ **Busca paralela** com early stopping (para quando encontra resposta boa)
- ✅ **Ranqueamento ML** (combina modelo ML + estatísticas históricas)
- ✅ **Combinação inteligente** (mescla melhores respostas de múltiplas fontes)
- ✅ **Cache semântico** (respostas < 0.1s para perguntas similares)

### 🧠 **Machine Learning Avançado**

#### **1. Ensemble de Classificadores (Intenção)**
- ✅ **Naive Bayes** - Rápido, baseline sólido
- ✅ **Random Forest** - Robusto a overfitting
- ✅ **Gradient Boosting** - Alta performance
- ✅ **LSTM** (opcional) - Deep Learning para contexto longo
- ✅ **Voting ponderado** por confiança

#### **2. Ranqueador Inteligente de Fontes**
- ✅ **Random Forest** treina com histórico de sucessos
- ✅ **Features:** tipo de pergunta + entidades + contexto temporal
- ✅ **Score híbrido:** 70% ML + 30% estatísticas históricas
- ✅ **Top-K selection:** Seleciona 5 melhores fontes

#### **3. Topic Modeling (LDA)**
- ✅ **20 tópicos** descobertos automaticamente
- ✅ **Agrupa perguntas similares** para análise de tendências
- ✅ **Melhora ranqueamento** (fontes boas em tópicos específicos)

#### **4. Aprendizado Contínuo**
- ✅ **Cache semântico** (TF-IDF + Cosine Similarity > 0.85)
- ✅ **Padrões aprendidos** de respostas com qualidade > 0.7
- ✅ **Estatísticas detalhadas** por fonte (taxa de sucesso, tempo médio, qualidade)
- ✅ **Retreinamento periódico** (a cada 100 conversas ou sob demanda)

### 💾 **Persistência e Histórico**
- ✅ **Todas as conversas** salvas no MySQL
- ✅ **Histórico paginado** com busca
- ✅ **Logs detalhados** no campo `metadata` (JSON)
- ✅ **Estatísticas** por usuário e global
- ✅ **Feedback explícito** (positivo/negativo/correções)

### 👥 **Sistema de Usuários**
- ✅ **Autenticação JWT**
- ✅ **Cadastro e login**
- ✅ **Histórico individual**
- ✅ **Controle de ownership** (usuário só vê/edita suas conversas)

### 🚀 **Modo Produção Otimizado**
- ✅ **Feature flags** (`PRODUCAO=true`)
- ✅ **TensorFlow desabilitado** em produção (economia de RAM)
- ✅ **spaCy ultra-leve** (apenas tokenização + NER)
- ✅ **Lazy loading** (modelos carregados sob demanda)
- ✅ **< 512 MB RAM** (compatível com Render/Railway free tier)

---

## 🏗️ Arquitetura

### **Padrão: Model → Repository → Worker → Controller**

```
┌─────────────────────────────────────────────────┐
│              FRONTEND (Separado)                │
│           Next.js / React / PWA                 │
└─────────────────┬───────────────────────────────┘
                  │ REST API (32 endpoints)
                  ▼
┌─────────────────────────────────────────────────┐
│           Flask API Controllers                 │
│  ├─ bot_controller.py (29 endpoints)            │
│  └─ user_controller.py (3 endpoints)            │
└─────────────────┬───────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────┐
│             Business Logic (Workers)            │
│  ├─ BotWorkerV2 (Singleton)                     │
│  │   ├─ Sistema ML Avançado                     │
│  │   ├─ Buscador Unificado (7 fontes)           │
│  │   └─ Sistema de Feedback                     │
│  └─ UserWorker (Auth JWT + bcrypt)              │
└─────────────────┬───────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────┐
│         Machine Learning Layer                  │
│  ├─ Ensemble (NB + RF + GB + LSTM*)             │
│  ├─ Ranqueador de Fontes (Random Forest)        │
│  ├─ Topic Model (LDA - 20 tópicos)              │
│  └─ Cache Semântico (TF-IDF + Cosine)           │
└─────────────────┬───────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────┐
│              Data Access (Repositories)         │
│  ├─ BotRepository (16 métodos CRUD)             │
│  └─ UserRepository (3 métodos)                  │
└─────────────────┬───────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────┐
│           MySQL Database (Railway)              │
│  ├─ usuarios (id, nome, email, senha_hash)      │
│  └─ bot_conversations (id, user_id, pergunta,   │
│      resposta, fonte, tempo, status,            │
│      metadata JSON, created_at)                 │
└─────────────────────────────────────────────────┘
```

---

## 🧠 Machine Learning

### **Ensemble de Modelos (Intenção)**

Combina 4 algoritmos para detectar intenção com alta precisão:

| Modelo | Tipo | Vantagem | Acurácia |
|--------|------|----------|----------|
| **Naive Bayes** | Probabilístico | Rápido, baseline sólido | ~85% |
| **Random Forest** | Ensemble | Robusto, features importantes | ~92% |
| **Gradient Boosting** | Boosting | Alta performance | ~94% |
| **LSTM*** | Deep Learning | Contexto longo, sequências | ~89% |

> *LSTM é **opcional** e desabilitado em produção (`PRODUCAO=true`) para economizar RAM.

**Voting Ponderado:**
```python
# Cada modelo vota com peso = confiança
votos = {
    "conhecimento": 0.95 (NB) + 0.88 (RF) + 0.92 (GB) = 2.75,
    "saudacao": 0.05 (NB) + 0.12 (RF) + 0.08 (GB) = 0.25
}

# Vencedor: "conhecimento" (confiança = 2.75 / 3 = 0.92)
```

### **Ranqueador Inteligente de Fontes**

Treina **Random Forest** com histórico de conversas:

**Features extraídas:**
- Tipo de pergunta (qual, como, por que, etc)
- Entidades presentes (PERSON, LOC, ORG, DATE)
- POS tags (substantivos, verbos, adjetivos)
- Contexto temporal (atual vs histórico)

**Score híbrido:**
```python
score_final = (score_ml * 0.7) + (taxa_sucesso_historica * 0.3)
```

**Output:**
```python
[
    ("wikipedia", 0.89),  # Melhor fonte
    ("google", 0.72),
    ("wolfram", 0.45),
    ...
]
```

### **Topic Modeling (LDA)**

Descobre **20 tópicos** automaticamente:

```python
Tópico 0: ["brasil", "capital", "país", "cidade", "estado"]
Tópico 1: ["cálculo", "número", "matemática", "resultado"]
Tópico 5: ["história", "guerra", "ano", "século", "evento"]
...
```

**Uso:**
- Agrupa perguntas similares
- Melhora ranqueamento (ex: Wolfram é ótimo no tópico 1 - cálculo)
- Análise de tendências

---

## 🔍 Fontes de Busca

### **7 Fontes Integradas**

| Fonte | Especialidade | API Key | Status |
|-------|---------------|---------|--------|
| **Wolfram Alpha** | Cálculos, conversões, fatos científicos | ✅ Necessária | ✅ |
| **Google Custom Search** | Informação geral, notícias, recente | ✅ Necessária | ✅ |
| **DuckDuckGo** | Busca alternativa, privada, sem tracking | ❌ Não | ✅ |
| **Wikipedia** | Conhecimento enciclopédico estruturado | ❌ Não | ✅ |
| **arXiv** | Papers científicos, pesquisa acadêmica | ❌ Não | ✅ |
| **DBpedia** | Dados estruturados (triplas RDF) | ❌ Não | ✅ |
| **YouTube** | Transcrições de vídeos educacionais | ❌ Não | ✅ |

### **Estratégia de Busca**

1. **Análise Avançada** → Extrai entidades, tipo, complexidade
2. **Ranqueamento ML** → Seleciona top 5 fontes
3. **Busca Paralela** → ThreadPoolExecutor (max 5 workers)
4. **Early Stopping** → Para quando encontra 2 respostas boas (>100 chars)
5. **Combinação Inteligente** → TF-IDF + remoção de duplicatas

---

## 🛠️ Tecnologias

### **Backend**
- **Flask 3.0** - Framework web minimalista
- **Gunicorn** - WSGI server para produção
- **Python 3.11** - Linguagem base

### **Machine Learning**
- **scikit-learn 1.5** - Ensemble (NB, RF, GB), TF-IDF, LDA
- **TensorFlow 2.16*** - Deep Learning (LSTM)
- **NumPy 1.26** - Operações numéricas
- **spaCy 3.7** - NLP (tokenização, NER, POS)

> *TensorFlow é **opcional** e desabilitado em produção.

### **APIs Externas**
- **Wolfram Alpha API** - Cálculos científicos
- **Google Custom Search API** - Busca web
- **DuckDuckGo Instant Answer** - Busca sem tracking
- **Wikipedia API** - Conhecimento enciclopédico
- **arXiv API** - Papers científicos
- **DBpedia SPARQL** - Dados estruturados
- **YouTube Transcript API** - Transcrições de vídeos

### **Banco de Dados**
- **MySQL 8.0+** - Armazenamento persistente
- **Connection Pool** - 5 conexões simultâneas

### **Utilitários**
- **langdetect** - Detecção automática de idioma
- **deep-translator** - Tradução (Google Translate)
- **cachetools** - Cache em memória (TTL)
- **bcrypt** - Hash de senhas
- **PyJWT** - Tokens de autenticação

---

## 📦 Instalação

### 1️⃣ **Clone o repositório**

```bash
git clone https://github.com/garotinhosDePrograma/bot-prototype.git
cd bot-prototype
```

### 2️⃣ **Crie um ambiente virtual**

```bash
python -m venv venv

# Linux/Mac
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3️⃣ **Instale as dependências**

```bash
# IMPORTANTE: Use --break-system-packages se necessário
pip install -r requirements.txt

# Baixe o modelo spaCy
python -m spacy download pt_core_news_sm
```

### 4️⃣ **Configure as variáveis de ambiente**

```bash
cp .env.example .env
```

Edite `.env`:

```env
# Modo (false = dev, true = produção)
PRODUCAO=false

# Banco de dados (Railway ou local)
CONN_URL=mysql://usuario:senha@host:porta/database

# APIs externas (opcional mas recomendado)
WOLFRAM_APP_ID=seu_app_id_wolfram
GOOGLE_CX=seu_custom_search_engine_id
GOOGLE_API_KEY=sua_google_api_key

# JWT (para autenticação)
SECRET_KEY=sua_chave_secreta_aqui
```

### 5️⃣ **Crie as tabelas no banco**

```bash
# Tabela de usuários
python script.py

# Tabela de conversas do bot
python migrations/create_bot_conversations_table.py
```

### 6️⃣ **(Opcional) Treine os modelos ML**

Se você quiser treinar do zero (caso contrário, use os modelos pré-treinados):

```bash
python
>>> from bot.bot_worker_v2 import get_bot_worker
>>> bot = get_bot_worker()
>>> bot.sistema_ml.retreinar_tudo()
```

> ⚠️ **Requer pelo menos 100 conversas no banco para treinar.**

### 7️⃣ **Inicie o servidor**

```bash
python app.py
```

A API estará disponível em `http://localhost:5000`

---

## ⚙️ Configuração

### **Obter API Keys (Opcional mas Recomendado)**

#### **Wolfram Alpha**
1. Acesse https://products.wolframalpha.com/api/
2. Crie uma conta gratuita
3. Obtenha seu **App ID** (2.000 queries/mês grátis)

#### **Google Custom Search**
1. Acesse https://programmablesearchengine.google.com/
2. Crie um novo search engine
3. Anote o **Search Engine ID (CX)**
4. Ative a API em https://console.cloud.google.com/
5. Crie uma **API Key** (100 queries/dia grátis)

> **Nota:** DuckDuckGo, Wikipedia, arXiv, DBpedia e YouTube **não requerem API keys**.

### **Configurar Banco de Dados (Railway)**

1. Acesse https://railway.app/
2. Crie um novo projeto MySQL
3. Copie a `CONN_URL` fornecida
4. Cole no arquivo `.env`

### **Modo Produção**

Para ativar otimizações de produção:

```bash
export PRODUCAO=true
```

**Otimizações aplicadas:**
- ✅ TensorFlow desabilitado (economia de ~400 MB RAM)
- ✅ spaCy ultra-leve (apenas tokenização + NER)
- ✅ TF-IDF reduzido (500 features vs 1000 em dev)
- ✅ Cache menor (200 vs 200 em dev)
- ✅ Menos workers (3 vs 4 em dev)

---

## 🚀 Deploy

### **Render (Recomendado - Free Tier)**

#### **1. Preparação**

```bash
# Certifique-se que modelos estão no Git
ls -lh bot/ml/modelos_avancados/modelos_ensemble.pkl

# Se arquivo > 100MB, use Git LFS
git lfs install
git lfs track "bot/ml/modelos_avancados/*.pkl"
git add .gitattributes
git commit -m "feat: adiciona modelos ML (LFS)"
git push
```

#### **2. Criar Web Service**

1. Acesse https://dashboard.render.com/
2. **New** → **Web Service**
3. Conecte seu repositório GitHub
4. Configure:

```yaml
Name: bot-worker-api
Environment: Python 3
Build Command: pip install -r requirements.txt && python -m spacy download pt_core_news_sm
Start Command: gunicorn app:app
```

#### **3. Variáveis de Ambiente**

```
PRODUCAO=true
CONN_URL=mysql://usuario:senha@host:porta/database
WOLFRAM_APP_ID=seu_app_id
GOOGLE_CX=seu_cx
GOOGLE_API_KEY=sua_key
```

#### **4. Deploy**

Clique em **Create Web Service**. O deploy levará ~5 minutos.

#### **5. Verificar**

```bash
# Health check
curl https://seu-app.onrender.com/api/bot/health

# Teste de pergunta
curl -X POST https://seu-app.onrender.com/api/bot/question \
  -H "Content-Type: application/json" \
  -d '{"pergunta":"Qual a capital da França?","user_id":1}'
```

### **Railway (Alternativa)**

```bash
# Instale Railway CLI
npm install -g @railway/cli

# Login
railway login

# Inicialize
railway init

# Deploy
railway up
```

### **Limites Free Tier**

| Plataforma | RAM | CPU | Uptime | Cold Start |
|-----------|-----|-----|--------|------------|
| **Render** | 512 MB | 0.1 | 750h/mês | ~30s após 15min inativo |
| **Railway** | 500 MB | Compartilhado | $5 crédito/mês | Sem hibernação |

> **Recomendação:** Render para produção, Railway para testes.

---

## 📡 API

### **Base URL**
```
http://localhost:5000      # Dev
https://seu-app.onrender.com  # Produção
```

### **Autenticação**

Endpoints de usuário requerem JWT:

```bash
# 1. Login
curl -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"email":"usuario@email.com","senha":"123456"}'

# Response: {"token": "eyJ...", "user": {...}}

# 2. Use o token
curl -X GET http://localhost:5000/api/all \
  -H "Authorization: Bearer eyJ..."
```

### **Endpoints Principais**

#### **🤖 Bot Endpoints**

##### **Fazer uma pergunta**
```bash
POST /api/bot/question
```

**Request:**
```json
{
  "pergunta": "Como funciona a fotossíntese?",
  "user_id": 1  // opcional
}
```

**Response:**
```json
{
  "status": "success",
  "query": "Como funciona a fotossíntese?",
  "response": "Basicamente, fotossíntese é o processo...",
  "source": "google+wikipedia",
  "processing_time": 1.234,
  "user_id": 1,
  "version": "2.0",
  "logs_processo": [...]
}
```

##### **Buscar histórico**
```bash
GET /api/bot/history?user_id=1&limit=20&offset=0
```

##### **Estatísticas**
```bash
GET /api/bot/stats?user_id=1
```

**Response:**
```json
{
  "status": "success",
  "statistics": {
    "total_perguntas": 150,
    "tempo_medio": 1.23,
    "cache_hits": 45,
    "taxa_cache": 30.0,
    "sucessos": 145,
    "erros": 5,
    "taxa_sucesso": 96.7,
    "fontes_mais_usadas": [
      {"fonte": "google", "count": 60},
      {"fonte": "wikipedia", "count": 40}
    ]
  }
}
```

##### **Feedback**
```bash
POST /api/bot/feedback
```

**Request:**
```json
{
  "conversation_id": 123,
  "tipo": "positivo",  // "positivo", "negativo", "neutro"
  "detalhes": "Resposta muito útil!"
}
```

##### **Correção**
```bash
POST /api/bot/feedback/correcao
```

**Request:**
```json
{
  "conversation_id": 123,
  "resposta_correta": "A resposta correta é..."
}
```

##### **Health Check Avançado**
```bash
GET /api/bot/health
```

**Response:**
```json
{
  "status": "online",
  "modo_producao": true,
  "modelos_carregados": {
    "ensemble_nb": true,
    "ensemble_rf": true,
    "ensemble_gb": true,
    "lstm": false,
    "ranqueador": true,
    "lda": true
  },
  "cache_size": 200,
  "deep_learning": false
}
```

#### **👥 User Endpoints**

##### **Registrar**
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

##### **Login**
```bash
POST /api/login
```

```json
{
  "email": "joao@email.com",
  "senha": "senha123"
}
```

#### **🔧 Admin Endpoints (⚠️ Adicionar autenticação)**

##### **Retreinar todos modelos**
```bash
POST /api/bot/admin/retrain-all
```

##### **Recarregar modelos (sem restart)**
```bash
POST /api/bot/admin/reload-models
```

##### **Ver tópicos LDA**
```bash
GET /api/bot/admin/topics
```

##### **Estatísticas avançadas de fontes**
```bash
GET /api/bot/admin/stats/fontes-avancadas
```

##### **Ranquear fontes para pergunta**
```bash
POST /api/bot/admin/fontes/ranking
```

```json
{
  "pergunta": "Qual a capital da França?"
}
```

**Response:**
```json
{
  "status": "success",
  "pergunta": "Qual a capital da França?",
  "ranking": [
    {"fonte": "wikipedia", "score": 0.89},
    {"fonte": "google", "score": 0.72},
    {"fonte": "wolfram", "score": 0.45}
  ]
}
```

---

## 🔄 Retreinamento

### **Quando Retreinar**

- ✅ A cada **100+ novas conversas**
- ✅ **Semanalmente** se tráfego alto
- ✅ Após **mudanças significativas** no conteúdo
- ✅ Quando **taxa de sucesso cair** abaixo de 85%

### **Processo (Google Colab)**

#### **1. Preparar ambiente**

```python
# No Google Colab
!git clone https://github.com/garotinhosDePrograma/bot-prototype.git
%cd bot-prototype

!pip install -r requirements.txt
!python -m spacy download pt_core_news_sm
```

#### **2. Configurar**

```python
import os

# Banco de PRODUÇÃO (lê dados reais)
os.environ['CONN_URL'] = 'mysql://usuario:senha@host:porta/database'

# Modo DEV no Colab (habilita TensorFlow)
os.environ['PRODUCAO'] = 'false'
```

#### **3. Treinar**

```python
from bot.bot_worker_v2 import get_bot_worker

bot = get_bot_worker()

# Treina TUDO (ensemble + ranqueador + LDA)
bot.sistema_ml.retreinar_tudo()

# Ou treinar individualmente:
# bot.sistema_ml.treinar_detector_intencao_ensemble()
# bot.sistema_ml.treinar_ranqueador_fontes()
# bot.sistema_ml.treinar_topic_model()
```

#### **4. Download modelos**

```python
from google.colab import files

files.download("bot/ml/modelos_avancados/modelos_ensemble.pkl")
```

#### **5. Deploy**

```bash
# Localmente após download
cp ~/Downloads/modelos_ensemble.pkl bot/ml/modelos_avancados/

git add bot/ml/modelos_avancados/
git commit -m "feat: retreinamento com 200+ novas conversas"
git push

# Render fará redeploy automático
```

#### **6. Recarregar (opcional)**

```bash
# Sem restart do servidor
curl -X POST https://seu-app.onrender.com/api/bot/admin/reload-models
```

### **Monitoramento**

```bash
# Verificar performance
curl https://seu-app.onrender.com/api/bot/admin/model-performance
```

---

## 📊 Métricas

### **Startup**
- ✅ **Build time:** < 5 min
- ✅ **Cold start:** < 30s (Render free tier)
- ✅ **Warm start:** < 1s
- ✅ **Health check:** 200 OK

### **Funcionalidade**
- ✅ **Ensemble ML:** 4 modelos ativos
- ✅ **Ranqueamento:** Funcionando
- ✅ **Topic Modeling:** 20 tópicos
- ✅ **Cache semântico:** Ativo
- ✅ **Feedback:** Registrando

### **Performance**
- ✅ **Tempo de resposta:** < 3s (média)
- ✅ **Taxa de cache:** > 20%
- ✅ **Taxa de sucesso:** > 90%
- ✅ **Uptime:** 99.9% (exceto cold starts)

### **Recursos**
- ✅ **RAM (dev):** ~800 MB
- ✅ **RAM (prod):** ~350 MB
- ✅ **CPU:** Baixo (picos apenas durante busca)
- ✅ **Disco:** ~150 MB (com modelos)

---

## 🗺️ Roadmap

### ✅ **Concluído (V2.0)**
- [x] Ensemble ML (NB + RF + GB + LSTM)
- [x] Ranqueamento inteligente de fontes
- [x] Topic Modeling (LDA)
- [x] 7 fontes de busca integradas
- [x] Sistema de feedback e correções
- [x] Aprendizado contínuo
- [x] Modo produção otimizado (< 512 MB RAM)
- [x] API REST completa (32 endpoints)
- [x] Histórico detalhado com paginação
- [x] Estatísticas avançadas
- [x] Cache semântico

### 🔜 **Próximos Passos (V2.1)**

#### **Curto Prazo (1-2 semanas)**
- [ ] Autenticação nos endpoints `/admin/*`
- [ ] Rate limiting (100 req/min por IP)
- [ ] Dashboard de métricas (Grafana)
- [ ] Logs estruturados (structlog)
- [ ] Health checks mais detalhados

#### **Médio Prazo (1 mês)**
- [ ] GitHub Actions CI/CD
- [ ] Testes automatizados (pytest, 80%+ coverage)
- [ ] Cache distribuído (Redis)
- [ ] Filas assíncronas (Celery)
- [ ] Webhooks para notificações

#### **Longo Prazo (3+ meses)**
- [ ] RAG (Retrieval Augmented Generation)
- [ ] Fine-tuning de modelos open-source (LLaMA, Mistral)
- [ ] Multi-tenancy
- [ ] API pública com API keys
- [ ] SDK em Python/JavaScript
- [ ] Embeddings próprios (sentence-transformers)

### 🎯 **Features Experimentais**
- [ ] Integração com Stack Overflow API
- [ ] Integração com Reddit API
- [ ] Suporte a imagens (OCR + Image Search)
- [ ] Suporte a áudio (Speech-to-Text)
- [ ] Conversação multi-turno (contexto entre perguntas)
- [ ] Personalização por usuário

---

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

---

## 👨‍💻 Autor

Desenvolvido por **Luiz Fagner**

- GitHub: [@WirkLichKeit1](https://github.com/WirkLichKeit1)
- Projeto: [Bot Prototype](https://github.com/garotinhosDePrograma/bot-prototype)

---

## 📞 Suporte

### **Problemas Comuns**

#### **"No module named 'tensorflow'"**
✅ **NORMAL** - TensorFlow desabilitado em produção (`PRODUCAO=true`)

#### **"File not found: modelos_ensemble.pkl"**
```bash
# Verifique se modelos estão no Git
ls -lh bot/ml/modelos_avancados/

# Se não, adicione
git add bot/ml/modelos_avancados/
git push
```

#### **Cold start lento**
✅ **NORMAL** no Render free - Primeira request após 15min inatividade demora ~30s

### **Contato**

Encontrou um bug? Tem uma sugestão?

- 🐛 Abra uma [issue](https://github.com/garotinhosDePrograma/bot-prototype/issues)
- 🔧 Envie um [pull request](https://github.com/garotinhosDePrograma/bot-prototype/pulls)

---

## 🙏 Agradecimentos

- **spaCy** - NLP toolkit incrível
- **scikit-learn** - ML clássico robusto
- **TensorFlow** - Deep Learning
- **Flask** - Framework web minimalista
- **Railway/Render** - Hospedagem gratuita
- **Wolfram Alpha** - API de conhecimento
- **Google** - Custom Search API

---
## 📚 Documentação adicional

- [📊 Análise Técnica Completa](ANALISE_PROJETO.md)

---

**⭐ Se este projeto foi útil, deixe uma estrela no GitHub!**

---

**Bot Worker V2.0** - Chatbot Inteligente sem LLMs
