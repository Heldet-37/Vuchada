// Configuração da API
const API_CONFIG = {
    // URL do backend (mude para sua URL real)
    BASE_URL: 'https://web-production-5220.up.railway.app',
    
    // URLs das APIs
    CATEGORIAS: '/api/categorias',
    PRODUTOS: '/api/produtos',
    PEDIDOS: '/api/pedidos',
    MESAS: '/api/mesas',
    LOGIN: '/api/login',
    USER_INFO: '/api/user-info',
    FAZER_PEDIDO: '/api/fazer_pedido',
    RESTAURANT_STATUS: '/api/restaurant-status',
    
    // Função para construir URLs completas
    getUrl: function(endpoint) {
        return this.BASE_URL + endpoint;
    }
};

// Detectar ambiente
if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    // Desenvolvimento local
    API_CONFIG.BASE_URL = 'http://localhost:5000';
} else {
    // Produção - usar URL do backend hospedado
    API_CONFIG.BASE_URL = 'https://web-production-5220.up.railway.app';
} 