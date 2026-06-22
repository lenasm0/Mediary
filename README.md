# Mediary

### Seu diário de sintomas, sempre com você

---

## Sobre o projeto

**Mediary** é uma aplicação web (e PWA instalável) para registrar sintomas de saúde do dia a dia — dor, náusea, fadiga, e outros — com início, fim, descrição e visualização em um calendário mensal. Pensado para quem precisa acompanhar padrões de saúde ao longo do tempo, seja para uso pessoal ou para levar ao médico.

## Funcionalidades

- **Autenticação segura** via JWT (cadastro, login, logout)
- **Calendário interativo** com indicação de dias com sintomas registrados
- **Registro de sintomas** com tipo, subtipo, descrição, início e fim
- **Edição e exclusão** de registros existentes
- **Gerenciamento de perfil** (nome, e-mail, senha)
- **PWA instalável** — funciona offline e pode ser adicionado à tela inicial
- **API REST** própria, separada do frontend

## Stack Tecnológica

| Camada | Tecnologias |
|---|---|
| **Frontend** | React + TypeScript, Vite, Tailwind CSS, Zustand, Axios |
| **Backend** | Flask (Python), Gunicorn, PyJWT |
| **Banco de Dados** | PostgreSQL via [Supabase](https://supabase.com/) |
| **PWA** | Vite PWA Plugin (Workbox) |
| **Infraestrutura** | Docker, Nginx, [Railway](https://railway.app/) |

## Estrutura do projeto

```
Mediary/
├── backend/              # API Flask
│   ├── app.py            # Rotas e lógica da aplicação
│   ├── requirements.txt  # Dependências Python
│   └── Dockerfile
├── frontend/              # SPA React
│   ├── src/
│   │   ├── api/          # Camada de comunicação com a API
│   │   ├── pages/        # Páginas da aplicação
│   │   ├── store/        # Estado global (Zustand)
│   │   └── components/   # Componentes reutilizáveis
│   ├── vite.config.ts    # Configuração do Vite + PWA
│   └── Dockerfile
└── docker-compose.yml    # Orquestração para desenvolvimento local
```

## Rodando localmente

### Pré-requisitos
- [Docker](https://www.docker.com/) e Docker Compose
- Uma conta no [Supabase](https://supabase.com/) com um projeto criado

### Passo a passo

**1. Clone o repositório**
```bash
git clone https://github.com/lenasm0/Mediary.git
cd Mediary
```

**2. Configure as variáveis de ambiente do backend**

Crie `backend/.env`:
```env
DATABASE_URL=postgresql://postgres.XXXX:SENHA@aws-1-us-east-1.pooler.supabase.com:6543/postgres
SECRET_KEY=uma-chave-secreta-aleatoria
FRONTEND_URL=http://localhost:80
```

**3. Suba os containers**
```bash
docker-compose up --build
```

**4. Acesse**
- Frontend: [http://localhost](http://localhost)
- Backend (health check): [http://localhost:5000/api/health](http://localhost:5000/api/health)

## Deploy em produção (Railway)

O projeto é deployado como **dois serviços independentes** no Railway:

| Serviço | Root Directory | Variáveis necessárias |
|---|---|---|
| `backend` | `backend` | `DATABASE_URL`, `SECRET_KEY`, `FRONTEND_URL` |
| `frontend` | `frontend` | `VITE_API_URL` |

> Veja o passo a passo completo em [`DEPLOY.md`](./DEPLOY.md)

## Instalando como App (PWA)

Acesse a URL do frontend em produção pelo navegador do celular ou computador:

- **Android (Chrome)**: toque no menu → "Instalar app" ou "Adicionar à tela inicial"
- **iOS (Safari)**: toque em compartilhar → "Adicionar à Tela de Início"
- **Desktop (Chrome/Edge)**: clique no ícone de instalação na barra de endereço

## Autenticação

A API utiliza **JWT (JSON Web Token)** em vez de cookies de sessão, garantindo compatibilidade total com navegadores mobile e cenários cross-domain. O token é retornado no login e enviado em cada requisição via header:

```
Authorization: Bearer <token>
```