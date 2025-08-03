# 🍽️ Cardápio Digital - PDV Restaurante

## 📱 Funcionalidade

O Cardápio Digital é uma interface web que permite:

### 👤 Para Clientes:
- **Visualizar produtos** organizados por categorias
- **Buscar produtos** por nome
- **Adicionar ao carrinho** com controle de quantidade
- **Fazer pedidos** selecionando mesa e observações
- **Ver preços** em tempo real
- **Controle de estoque** automático

### 👨‍💼 Para Funcionários:
- **Login seguro** com as mesmas credenciais do PDV
- **Visualizar todos os pedidos** em tempo real
- **Filtrar pedidos** por status
- **Atualizar status** dos pedidos (pendente → preparando → pronto → finalizado)
- **Cancelar pedidos** com restauração automática do estoque
- **Ver detalhes** completos de cada pedido
- **Auto-refresh** a cada 30 segundos

## 🚀 Como Usar

### 1. Instalar Dependências
```bash
pip install -r requirements_web.txt
```

### 2. Iniciar o Servidor
```bash
python web_server.py
```

### 3. Acessar no Navegador
- **Local**: http://localhost:5000
- **Rede**: Use o IP mostrado no terminal quando iniciar o servidor

### 4. Conectar Tablets/Móveis
- Certifique-se de que os dispositivos estão na mesma rede WiFi
- **IMPORTANTE**: Use o IP correto mostrado no terminal
- Exemplo: Se o terminal mostra `http://192.168.43.118:5000`, use esse IP exato
- **DICA**: Se não funcionar, verifique se não está usando um IP incorreto (ex: 48 em vez de 43)

## 📋 Fluxo de Uso

### Para Clientes:
1. Acesse a página inicial
2. Clique em "Cliente"
3. Navegue pelas categorias ou use a busca
4. Adicione produtos ao carrinho
5. Clique no ícone do carrinho
6. Selecione uma mesa
7. Adicione observações (opcional)
8. Clique em "Fazer Pedido"

### Para Funcionários:
1. Acesse a página inicial
2. Clique em "Funcionário"
3. Digite usuário e senha (mesmos do PDV)
4. Visualize os pedidos em tempo real
5. Atualize status conforme necessário
6. Use "Detalhes" para ver itens completos

## 🔧 Configuração

### Porta do Servidor
Para mudar a porta padrão (5000), edite o arquivo `web_server.py`:
```python
app.run(host='0.0.0.0', port=5000, debug=True)
```

### Banco de Dados
O sistema usa o mesmo banco de dados do PDV (`database/restaurant.db`).

### Imagens de Produtos
- Coloque as imagens na pasta `static/`
- Configure o caminho no banco de dados
- Imagem padrão: `static/default_product.png`

## 🛡️ Segurança

- **Autenticação**: Mesmo sistema do PDV
- **Sessões**: Gerenciadas pelo Flask
- **Validação**: Todos os dados são validados
- **Transações**: Rollback automático em caso de erro

## 📱 Compatibilidade

- ✅ **Desktop**: Chrome, Firefox, Safari, Edge
- ✅ **Tablet**: iPad, Android
- ✅ **Mobile**: iPhone, Android
- ✅ **Responsivo**: Adapta-se a qualquer tela

## 🔄 Integração com PDV

- **Mesmo banco de dados**
- **Pedidos sincronizados**
- **Estoque atualizado em tempo real**
- **Mesas compartilhadas**

## 🚨 Troubleshooting

### Erro de Conexão
- Verifique se o firewall permite a porta 5000
- Confirme se os dispositivos estão na mesma rede

### Produtos não aparecem
- Verifique se os produtos estão ativos no banco
- Confirme se há estoque disponível

### Login não funciona
- Use as mesmas credenciais do PDV
- Verifique se o usuário está ativo

### Imagens não carregam
- Verifique se o arquivo existe em `static/`
- Confirme o caminho no banco de dados

## 📞 Suporte

Para dúvidas ou problemas:
1. Verifique os logs do servidor
2. Confirme a conectividade de rede
3. Teste primeiro no navegador local

---

**Desenvolvido para o PDV Restaurante** 🍽️ 