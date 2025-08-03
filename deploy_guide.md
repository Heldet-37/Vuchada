# 🚀 Guia Completo de Deploy - PDV Restaurante

## 📍 **ONDE HOSPEDAR CADA PARTE**

### 🖥️ **BACKEND (Flask) - Escolha UMA opção:**

#### **Opção 1: Heroku (Recomendado)**
```bash
# 1. Instalar Heroku CLI
# 2. Login
heroku login

# 3. Criar app
heroku create seu-pdv-backend

# 4. Deploy
git add .
git commit -m "Deploy backend"
git push heroku main
```

#### **Opção 2: Railway (Gratuito)**
1. Acesse [railway.app](https://railway.app)
2. Login com GitHub
3. "New Project" → "Deploy from GitHub repo"
4. Selecione seu repositório
5. Deploy automático

#### **Opção 3: Render (Gratuito)**
1. Acesse [render.com](https://render.com)
2. Login com GitHub
3. "New Web Service"
4. Conecte repositório
5. Deploy automático

### 🌐 **FRONTEND (Vercel) - Única opção:**

#### **Vercel (Gratuito)**
1. Acesse [vercel.com](https://vercel.com)
2. Login com GitHub
3. "New Project"
4. Importe repositório
5. Deploy automático

## 📋 **PASSO A PASSO DETALHADO**

### **Passo 1: Preparar Backend**

#### **Para Heroku:**
Crie estes arquivos:

**`Procfile`:**
```
web: python web_server.py
```

**`requirements_heroku.txt`:**
```
Flask==2.3.3
Werkzeug==2.3.7
gunicorn==21.2.0
```

#### **Para Railway/Render:**
Use o `web_server.py` existente.

### **Passo 2: Deploy Backend**

#### **Heroku:**
```bash
# No terminal
heroku create seu-pdv-backend
git add .
git commit -m "Deploy backend"
git push heroku main

# Anote a URL gerada:
# https://seu-pdv-backend-12345.herokuapp.com
```

#### **Railway:**
1. Acesse [railway.app](https://railway.app)
2. "New Project" → "Deploy from GitHub repo"
3. Selecione seu repositório
4. Aguarde deploy
5. Anote a URL gerada

#### **Render:**
1. Acesse [render.com](https://render.com)
2. "New Web Service"
3. Conecte GitHub
4. Selecione repositório
5. Aguarde deploy
6. Anote a URL gerada

### **Passo 3: Configurar Frontend**

Edite `static/config.js`:
```javascript
// Mude para a URL real do seu backend
BASE_URL: 'https://seu-pdv-backend-12345.herokuapp.com'
```

### **Passo 4: Deploy Frontend**

#### **Vercel:**
1. Acesse [vercel.com](https://vercel.com)
2. Login com GitHub
3. "New Project"
4. Importe repositório
5. Configure:
   - **Framework Preset**: Other
   - **Root Directory**: `./`
   - **Build Command**: deixe vazio
   - **Output Directory**: `static`
6. Clique "Deploy"

## 🌐 **URLs FINAIS**

Após o deploy, você terá:

- **Backend**: `https://seu-pdv-backend-12345.herokuapp.com`
- **Frontend**: `https://seu-projeto.vercel.app`

### **URLs de Acesso:**
- **Cardápio**: `https://seu-projeto.vercel.app/cliente`
- **Login**: `https://seu-projeto.vercel.app/funcionario`
- **Inicial**: `https://seu-projeto.vercel.app/`

## 🔧 **CONFIGURAÇÕES IMPORTANTES**

### **CORS (Se der erro):**
Adicione no backend:
```python
from flask_cors import CORS
app = Flask(__name__)
CORS(app)
```

### **Banco de Dados:**
- O SQLite funciona no Heroku
- Para Railway/Render, pode precisar de PostgreSQL

## 🧪 **TESTE**

1. **Teste o Backend:**
   ```
   https://seu-backend.herokuapp.com/api/categorias
   ```

2. **Teste o Frontend:**
   ```
   https://seu-projeto.vercel.app/
   ```

3. **Teste Completo:**
   - Acesse o cardápio
   - Faça um pedido
   - Teste login funcionário

## 💰 **CUSTOS**

- **Vercel**: Gratuito (até 100GB/mês)
- **Heroku**: Gratuito (com limitações)
- **Railway**: Gratuito (com limitações)
- **Render**: Gratuito (com limitações)

## 🆘 **PROBLEMAS COMUNS**

### **Erro de CORS:**
- Adicione `flask-cors` no backend
- Configure CORS corretamente

### **API não responde:**
- Verifique a URL no `config.js`
- Teste a API diretamente
- Verifique logs do backend

### **Página não carrega:**
- Verifique build no Vercel
- Confirme arquivos na pasta `static/`

## 📞 **SUPORTE**

Se tiver problemas:
1. Verifique logs do backend
2. Teste localmente primeiro
3. Confirme URLs corretas
4. Verifique configuração CORS

---

**🎉 Agora você sabe EXATAMENTE onde hospedar cada parte!** 