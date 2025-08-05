# 🚀 Deploy no Heroku - PDV Restaurante

## 📋 Pré-requisitos

- Conta no [Heroku](https://heroku.com)
- [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli) instalado
- Git configurado

## 🛠️ Configuração

### 1. Login no Heroku
```bash
heroku login
```

### 2. Criar aplicação no Heroku
```bash
heroku create seu-pdv-restaurante
```

### 3. Configurar variáveis de ambiente
```bash
heroku config:set FLASK_ENV=production
heroku config:set SECRET_KEY=sua_chave_secreta_muito_segura
```

### 4. Fazer deploy
```bash
git add .
git commit -m "Deploy para Heroku"
git push heroku main
```

## 📁 Arquivos de Configuração

### `Procfile`
```
web: gunicorn web_server_heroku_improved:app
```

### `requirements.txt`
```
flet==0.9.0
Flask==2.3.3
Werkzeug==2.3.7
flask-cors==4.0.0
gunicorn==21.2.0
```

### `runtime.txt`
```
python-3.12.0
```

## 🔧 Melhorias Implementadas

### ✅ **Correções de Erros**
- ❌ **Erro de sintaxe**: `return f"{value:,.2f} MT"A` → `return f"{value:,.2f} MT"`
- ❌ **Falta CORS**: Adicionado `flask-cors` com configuração adequada
- ❌ **Sem logging**: Implementado sistema de logging completo
- ❌ **Sem tratamento de erros**: Adicionado error handlers

### ✅ **Funcionalidades Adicionadas**
- 🔍 **Health Check**: Rota `/test` para verificar status da aplicação
- 📊 **Logging**: Sistema de logs para debug e monitoramento
- 🔒 **Segurança**: Configurações de sessão para produção
- 🌐 **CORS**: Configuração para permitir requisições cross-origin
- 📝 **Documentação**: Docstrings em todas as funções
- ⚡ **Performance**: Configuração otimizada do Gunicorn

### ✅ **Configurações de Produção**
- 🚀 **Gunicorn**: Servidor WSGI para produção
- 🔧 **Variáveis de Ambiente**: Configuração flexível
- 📦 **Dependências**: Todas as dependências necessárias
- 🛡️ **Segurança**: Configurações de sessão seguras

## 🌐 Endpoints da API

### Páginas Estáticas
- `GET /` - Página inicial
- `GET /cliente` - Menu digital
- `GET /funcionario` - Login funcionário
- `GET /funcionario/pedidos` - Dashboard pedidos
- `GET /servicos` - Página de serviços
- `GET /sobre` - Página sobre

### API Endpoints
- `GET /api` - Informações da API
- `GET /test` - Health check
- `GET /api/categorias` - Lista categorias
- `GET /api/produtos` - Lista produtos
- `GET /api/mesas` - Lista mesas
- `POST /api/fazer_pedido` - Criar pedido
- `POST /api/login` - Login funcionário
- `GET /api/restaurant-status` - Status restaurante
- `GET /api/user-info` - Info usuário logado
- `GET /api/pedidos` - Lista pedidos
- `POST /logout` - Logout

## 🔍 Monitoramento

### Logs
```bash
heroku logs --tail
```

### Status da Aplicação
```bash
heroku ps
```

### Health Check
Acesse: `https://sua-app.herokuapp.com/test`

## 🚨 Troubleshooting

### Erro de Build
```bash
heroku logs --tail
```

### Problema de CORS
Verificar se o frontend está usando a URL correta do Heroku.

### Problema de Banco de Dados
O SQLite é resetado a cada deploy. Para persistência, considere usar PostgreSQL.

## 📞 Suporte

Para problemas específicos do Heroku, consulte:
- [Heroku Dev Center](https://devcenter.heroku.com/)
- [Flask no Heroku](https://devcenter.heroku.com/articles/python-gunicorn) 