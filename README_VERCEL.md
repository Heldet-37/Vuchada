# 🚀 Deploy no Vercel - Cardápio Digital

## 📋 Pré-requisitos

1. **Backend hospedado** (Heroku, Railway, Render, etc.)
2. **Conta no Vercel** (gratuita)
3. **GitHub** para conectar o repositório

## 🔧 Configuração

### 1. Preparar o Backend

Primeiro, hospede seu backend Flask em uma plataforma como:

- **Heroku** (recomendado)
- **Railway**
- **Render**
- **DigitalOcean**

### 2. Configurar URLs da API

Edite o arquivo `static/config.js`:

```javascript
const API_CONFIG = {
    // Mude para a URL real do seu backend
    BASE_URL: 'https://seu-backend.herokuapp.com',
    // ... resto da configuração
};
```

### 3. Deploy no Vercel

#### Opção A: Via GitHub (Recomendado)

1. **Criar repositório no GitHub**
   ```bash
   git init
   git add .
   git commit -m "Primeiro commit"
   git branch -M main
   git remote add origin https://github.com/seu-usuario/seu-repo.git
   git push -u origin main
   ```

2. **Conectar ao Vercel**
   - Acesse [vercel.com](https://vercel.com)
   - Faça login com GitHub
   - Clique em "New Project"
   - Importe seu repositório
   - Configure:
     - **Framework Preset**: Other
     - **Root Directory**: `./`
     - **Build Command**: deixe vazio
     - **Output Directory**: `static`

3. **Deploy**
   - Clique em "Deploy"
   - Aguarde o build
   - Seu site estará disponível em `https://seu-projeto.vercel.app`

#### Opção B: Via Vercel CLI

1. **Instalar Vercel CLI**
   ```bash
   npm i -g vercel
   ```

2. **Deploy**
   ```bash
   vercel
   ```

## 📁 Estrutura dos Arquivos

```
/
├── static/
│   ├── index.html          # Página inicial
│   ├── cliente.html        # Cardápio digital
│   ├── funcionario.html    # Login funcionário
│   ├── config.js           # Configuração da API
│   ├── cliente.js          # JavaScript do cliente
│   └── styles.css          # Estilos CSS
├── vercel.json             # Configuração do Vercel
└── README_VERCEL.md        # Esta documentação
```

## 🔗 Configuração do vercel.json

O arquivo `vercel.json` já está configurado para:

- **Servir arquivos estáticos** da pasta `static/`
- **Redirecionar APIs** para seu backend
- **Configurar rotas** corretamente

## 🌐 URLs de Acesso

Após o deploy, você terá:

- **Página Inicial**: `https://seu-projeto.vercel.app/`
- **Cardápio**: `https://seu-projeto.vercel.app/cliente`
- **Login Funcionário**: `https://seu-projeto.vercel.app/funcionario`

## 🔄 Atualizações

Para atualizar o site:

1. **Faça as mudanças** nos arquivos
2. **Commit e push** para GitHub
3. **Vercel atualiza automaticamente**

## 🛠️ Troubleshooting

### Erro de CORS

Se aparecer erro de CORS, adicione no seu backend Flask:

```python
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Permite todas as origens
```

### API não responde

1. **Verifique a URL** no `config.js`
2. **Teste a API** diretamente
3. **Verifique logs** do backend

### Página não carrega

1. **Verifique o build** no Vercel
2. **Confirme os arquivos** na pasta `static/`
3. **Teste localmente** primeiro

## 📱 Teste

1. **Acesse** `https://seu-projeto.vercel.app/`
2. **Teste** o cardápio digital
3. **Teste** o login de funcionário
4. **Verifique** se as APIs funcionam

## 🔒 Segurança

- **HTTPS automático** no Vercel
- **Headers de segurança** configurados
- **CORS** configurado no backend

## 💰 Custos

- **Vercel**: Gratuito (até 100GB/mês)
- **Backend**: Depende da plataforma escolhida

## 📞 Suporte

Se tiver problemas:

1. **Verifique os logs** do Vercel
2. **Teste localmente** primeiro
3. **Confirme** a URL do backend
4. **Verifique** a configuração do CORS

---

**🎉 Seu cardápio digital estará online e conectado ao sistema!** 