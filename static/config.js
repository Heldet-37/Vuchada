// Configuração da API
const API_CONFIG = {
    BASE_URL: 'https://web-production-5220.up.railway.app',
    ENDPOINTS: {
        CATEGORIAS: '/api/categorias',
        PRODUTOS: '/api/produtos',
        MESAS: '/api/mesas',
        PEDIDOS: '/api/fazer_pedido',
        LOGIN: '/api/login',
        STATUS: '/api/restaurant-status',
        USER_INFO: '/api/user-info',
        PEDIDOS_LIST: '/api/pedidos'
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