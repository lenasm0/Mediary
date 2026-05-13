# Deploy Mediary no Railway

## Visão Geral

O projeto tem **dois serviços separados** no Railway:
- **Backend**: Flask + Gunicorn (Python)
- **Frontend**: React + Nginx (Node build → static)

Ambos se conectam ao **Supabase** (PostgreSQL externo).

---

## Pré-requisitos

- Conta no [Railway](https://railway.app)
- Conta no [Supabase](https://supabase.com) com projeto criado
- Git instalado

---

## Passo 1 — Supabase

1. Acesse seu projeto no Supabase
2. Vá em **Settings → Database → Connection string → URI**
3. Copie a URL no formato:
   ```
   postgresql://postgres.XXXX:SENHA@aws-1-us-east-1.pooler.supabase.com:6543/postgres
   ```
4. Guarde essa URL — você vai precisar no próximo passo

---

## Passo 2 — Deploy do Backend

### Opção A: Via GitHub (recomendado)

1. Suba **apenas a pasta `backend/`** em um repositório GitHub separado  
   *(ou use monorepo e configure o Root Directory no Railway)*

2. No Railway: **New Project → Deploy from GitHub repo**

3. Em **Settings → Root Directory**: coloque `backend` (se monorepo)

4. Em **Variables**, adicione:
   | Variável | Valor |
   |----------|-------|
   | `DATABASE_URL` | URL do Supabase copiada acima |
   | `SECRET_KEY` | Uma string aleatória longa (ex: `openssl rand -hex 32`) |
   | `FRONTEND_URL` | URL do frontend (preencha depois de criar o serviço frontend) |

5. Railway vai buildar e dar uma URL tipo `https://mediary-backend.up.railway.app`

### Opção B: Via CLI

```bash
cd backend
railway login
railway init
railway up
# Depois configure as variáveis no dashboard
```

---

## Passo 3 — Deploy do Frontend

1. Suba a pasta `frontend/` em outro repo (ou mesmo monorepo)

2. No Railway: **New Project → Deploy from GitHub repo**

3. Em **Variables**, adicione:
   | Variável | Valor |
   |----------|-------|
   | `VITE_API_URL` | URL do backend (ex: `https://mediary-backend.up.railway.app`) |

4. Railway vai buildar com Dockerfile (nginx na porta 80)

5. Anote a URL do frontend e volte ao backend para preencher `FRONTEND_URL`

---

## Passo 4 — Configurar CORS

No serviço de **Backend**, adicione/atualize a variável:
```
FRONTEND_URL=https://mediary-frontend.up.railway.app
```
Reinicie o serviço backend.

---

## Variáveis de Ambiente

### Backend
```env
DATABASE_URL=postgresql://...
SECRET_KEY=string-secreta-aleatoria
FRONTEND_URL=https://seu-frontend.up.railway.app
```

### Frontend
```env
VITE_API_URL=https://seu-backend.up.railway.app
```

---

## Erros Comuns

### "Não autorizado" após login
- Causa: Cookie `SameSite=None` requer HTTPS em ambos os domínios
- Solução: Certifique-se que Railway está servindo HTTPS (automático) e `SECRET_KEY` está configurada

### CORS bloqueando requisições
- Causa: `FRONTEND_URL` não configurada no backend
- Solução: Adicione a variável e reinicie o backend

### Build do frontend falha com "Cannot find module vite-plugin-pwa"
- Causa: `npm ci` não instalou as devDependencies
- Solução: O Dockerfile usa `npm ci` que respeita package-lock.json — certifique-se que `package-lock.json` está commitado

### Banco não inicializa
- Causa: `DATABASE_URL` incorreta ou Supabase com IP bloqueado
- Solução: No Supabase → Settings → Network → adicione `0.0.0.0/0` ou use a connection string de pooler

---

## PWA

O app está configurado como PWA com:
- **Service Worker** via Workbox (cache de assets e API)
- **Web Manifest** com nome, ícone e cores
- **Instalável** em Android e iOS (Add to Home Screen)

Para testar localmente: `npm run build && npm run preview`

