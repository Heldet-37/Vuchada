let cart = [];
let products = [];
let categories = [];
let selectedCategory = null;

// Carregar categorias
async function loadCategories() {
    try {
        const response = await fetch(API_CONFIG.getUrl(API_CONFIG.CATEGORIAS));
        categories = await response.json();
        renderCategories();
    } catch (error) {
        console.error('Erro ao carregar categorias:', error);
    }
}

// Renderizar categorias
function renderCategories() {
    const container = document.getElementById('categories');
    container.innerHTML = `
        <button class="category-btn ${!selectedCategory ? 'active' : ''}" onclick="selectCategory(null)">
            Todos
        </button>
        ${categories.map(cat => `
            <button class="category-btn ${selectedCategory === cat.id ? 'active' : ''}" onclick="selectCategory(${cat.id})">
                ${cat.name}
            </button>
        `).join('')}
    `;
}

// Selecionar categoria
function selectCategory(categoryId) {
    selectedCategory = categoryId;
    renderCategories();
    loadProducts();
}

// Carregar produtos
async function loadProducts() {
    try {
        const searchQuery = document.getElementById('searchInput').value;
        let url = API_CONFIG.getUrl(API_CONFIG.PRODUTOS);
        const params = new URLSearchParams();
        
        if (selectedCategory) {
            params.append('categoria_id', selectedCategory);
        }
        if (searchQuery) {
            params.append('busca', searchQuery);
        }
        
        if (params.toString()) {
            url += '?' + params.toString();
        }
        
        const response = await fetch(url);
        products = await response.json();
        renderProducts();
    } catch (error) {
        console.error('Erro ao carregar produtos:', error);
    }
}

// Renderizar produtos
function renderProducts() {
    const container = document.getElementById('productsGrid');
    
    if (products.length === 0) {
        container.innerHTML = '<div class="loading">Nenhum produto encontrado</div>';
        return;
    }
    
    container.innerHTML = products.map(product => `
        <div class="product-card">
            <div class="product-image" onerror="this.innerHTML='🍽️'">
                ${product.image_url && product.image_url !== '/static/default_product.png' 
                    ? `<img src="${product.image_url}" alt="${product.name}" onerror="this.parentElement.innerHTML='🍽️'">`
                    : '🍽️'
                }
            </div>
            <div class="product-info">
                <div class="product-name">${product.name}</div>
                <div class="product-description">${product.description}</div>
                <div class="product-footer">
                    <div class="product-price">
                        ${product.has_variations ? 'A partir de ' : ''}${product.price_formatted}
                    </div>
                    <button class="add-btn" onclick="handleProductClick(${product.id}, ${product.has_variations})">
                        ${product.has_variations ? 'Ver Opções' : 'Adicionar'}
                    </button>
                </div>
                ${product.has_variations ? `
                    <div class="stock-info">
                        ${product.variations.length} variações disponíveis
                    </div>
                ` : ''}
            </div>
        </div>
    `).join('');
}

// Função para lidar com clique no produto
function handleProductClick(productId, hasVariations) {
    if (hasVariations) {
        showVariationsModal(productId);
    } else {
        addToCart(productId);
    }
}

// Modal de variações
function showVariationsModal(productId) {
    const product = products.find(p => p.id === productId);
    if (!product || !product.variations || product.variations.length === 0) {
        addToCart(productId);
        return;
    }

    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.style.display = 'block';
    
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h2>🍕 ${product.name}</h2>
                <span class="close" onclick="this.parentElement.parentElement.parentElement.remove()">&times;</span>
            </div>
            
            <div class="variations-container">
                <p style="margin-bottom: 1rem; color: #666;">Escolha uma opção:</p>
                ${product.variations.map(variation => `
                    <div class="variation-item" onclick="addVariationToCart(${product.id}, ${variation.id}, '${variation.name}', ${variation.price}, this)">
                        <div class="variation-info">
                            <div class="variation-name">${variation.name}</div>
                            <div class="variation-stock">Estoque: ${variation.stock}</div>
                        </div>
                        <div class="variation-price">${variation.price_formatted}</div>
                    </div>
                `).join('')}
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Fechar modal ao clicar fora
    modal.onclick = function(event) {
        if (event.target === modal) {
            modal.remove();
        }
    };
}

// Adicionar variação ao carrinho
function addVariationToCart(productId, variationId, variationName, variationPrice, element) {
    const product = products.find(p => p.id === productId);
    const variation = product.variations.find(v => v.id === variationId);
    
    if (!variation || variation.stock <= 0) {
        alert('Esta opção não está disponível!');
        return;
    }
    
    const existingItem = cart.find(item => 
        item.product_id === productId && 
        item.variation_id === variationId
    );
    
    if (existingItem) {
        if (existingItem.quantity < variation.stock) {
            existingItem.quantity++;
        } else {
            alert('Quantidade máxima disponível atingida!');
            return;
        }
    } else {
        cart.push({
            product_id: productId,
            variation_id: variationId,
            name: `${product.name} - ${variationName}`,
            price: variationPrice,
            quantity: 1
        });
    }
    
    updateCartDisplay();
    
    // Fechar modal
    const modal = element.closest('.modal');
    if (modal) {
        modal.remove();
    }
    
    // Mostrar notificação
    showNotification(`${product.name} - ${variationName} adicionado ao carrinho!`);
}

// Adicionar ao carrinho
function addToCart(productId) {
    const product = products.find(p => p.id === productId);
    if (!product) return;
    
    const existingItem = cart.find(item => item.product_id === productId);
    
    if (existingItem) {
        if (existingItem.quantity < product.stock) {
            existingItem.quantity++;
        } else {
            alert('Quantidade máxima disponível atingida!');
            return;
        }
    } else {
        cart.push({
            product_id: productId,
            name: product.name,
            price: product.price,
            quantity: 1
        });
    }
    
    updateCartDisplay();
}

// Atualizar quantidade no carrinho
function updateQuantity(productId, change, variationId = null) {
    const item = cart.find(item => 
        item.product_id === productId && 
        (variationId ? item.variation_id === variationId : !item.variation_id)
    );
    if (!item) return;
    
    const newQuantity = item.quantity + change;
    if (newQuantity <= 0) {
        cart = cart.filter(cartItem => 
            !(cartItem.product_id === productId && 
              (variationId ? cartItem.variation_id === variationId : !cartItem.variation_id))
        );
    } else {
        // Verificar estoque
        if (variationId) {
            const product = products.find(p => p.id === productId);
            const variation = product.variations.find(v => v.id === variationId);
            if (newQuantity <= variation.stock) {
                item.quantity = newQuantity;
            } else {
                alert('Quantidade máxima disponível atingida!');
                return;
            }
        } else {
            const product = products.find(p => p.id === productId);
            if (newQuantity <= product.stock) {
                item.quantity = newQuantity;
            } else {
                alert('Quantidade máxima disponível atingida!');
                return;
            }
        }
    }
    
    updateCartDisplay();
}

// Atualizar exibição do carrinho
function updateCartDisplay() {
    const count = cart.reduce((total, item) => total + item.quantity, 0);
    document.getElementById('cartCount').textContent = count;
    
    const cartItems = document.getElementById('cartItems');
    const cartTotal = document.getElementById('cartTotal');
    
    if (cart.length === 0) {
        cartItems.innerHTML = '<div class="loading">Carrinho vazio</div>';
        cartTotal.textContent = '0,00 MT';
        return;
    }
    
    const total = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
    cartTotal.textContent = formatCurrency(total);
    
    cartItems.innerHTML = cart.map(item => `
        <div class="cart-item">
            <div class="item-info">
                <div class="item-name">${item.name}</div>
                <div class="item-price">${formatCurrency(item.price)} cada</div>
            </div>
            <div class="item-quantity">
                <button class="quantity-btn" onclick="updateQuantity(${item.product_id}, -1, ${item.variation_id || 'null'})">-</button>
                <span>${item.quantity}</span>
                <button class="quantity-btn" onclick="updateQuantity(${item.product_id}, 1, ${item.variation_id || 'null'})">+</button>
            </div>
        </div>
    `).join('');
}

// Formatar moeda
function formatCurrency(value) {
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'MZN'
    }).format(value);
}

// Abrir carrinho
function openCart() {
    if (cart.length === 0) {
        alert('Adicione produtos ao carrinho primeiro!');
        return;
    }
    
    loadMesas();
    document.getElementById('cartModal').style.display = 'block';
}

// Fechar carrinho
function closeCart() {
    document.getElementById('cartModal').style.display = 'none';
}

// Carregar mesas
async function loadMesas() {
    try {
        const response = await fetch(API_CONFIG.getUrl(API_CONFIG.MESAS));
        const mesas = await response.json();
        
        const select = document.getElementById('mesaSelect');
        select.innerHTML = '<option value="">Selecione uma mesa</option>';
        
        mesas.forEach(mesa => {
            const option = document.createElement('option');
            option.value = mesa.id;
            
            // Mostrar informações mais claras sobre a mesa
            let statusText = mesa.status;
            if (mesa.status === 'livre') {
                statusText = '🟢 Livre';
            } else if (mesa.status === 'ocupada') {
                statusText = '🔴 Ocupada';
            }
            
            option.textContent = `${mesa.name} - Capacidade: ${mesa.capacity} pessoas - ${statusText}`;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Erro ao carregar mesas:', error);
    }
}

// Função para mostrar notificação
function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <span class="notification-icon">${type === 'success' ? '✅' : '❌'}</span>
            <span class="notification-message">${message}</span>
            <button class="notification-close" onclick="this.parentElement.parentElement.remove()">×</button>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remover após 5 segundos
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, 5000);
}

// Fazer pedido
document.getElementById('orderForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const mesaId = document.getElementById('mesaSelect').value;
    
    if (!mesaId) {
        showNotification('Selecione uma mesa!', 'error');
        return;
    }
    
    if (cart.length === 0) {
        showNotification('Adicione produtos ao carrinho!', 'error');
        return;
    }
    
    const submitBtn = document.getElementById('submitBtn');
    submitBtn.disabled = true;
    submitBtn.textContent = 'Processando...';
    
    try {
        const response = await fetch(API_CONFIG.getUrl(API_CONFIG.FAZER_PEDIDO), {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                mesa_id: mesaId,
                itens: cart
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showNotification(`Pedido #${result.order_id} criado com sucesso!<br>Total: ${result.total}`, 'success');
            cart = [];
            updateCartDisplay();
            closeCart();
            loadProducts(); // Recarregar produtos para atualizar estoque
        } else {
            showNotification(result.message, 'error');
        }
    } catch (error) {
        showNotification('Erro ao fazer pedido. Tente novamente.', 'error');
        console.error('Erro:', error);
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Fazer Pedido';
    }
});

// Busca em tempo real
// Buscar produtos com debounce para evitar muitas requisições
let searchTimeout;
document.getElementById('searchInput').addEventListener('input', function() {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
        loadProducts();
    }, 500); // Aguarda 500ms após parar de digitar
});

// Fechar modal ao clicar fora
window.onclick = function(event) {
    const modal = document.getElementById('cartModal');
    if (event.target === modal) {
        closeCart();
    }
}

// Inicializar
loadCategories();
loadProducts(); 