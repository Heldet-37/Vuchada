// ===== CORREÇÕES PARA O MENU DIGITAL =====

// Função para renderizar categorias com estilos corretos
function renderCategoriesWithStyles() {
    const categoriesContainer = document.getElementById('categories');
    if (!categoriesContainer) return;
    
    categoriesContainer.innerHTML = '';
    
    categories.forEach(category => {
        const categoryBtn = document.createElement('button');
        categoryBtn.className = 'category-btn';
        categoryBtn.textContent = category.name;
        categoryBtn.onclick = () => selectCategory(category.id);
        
        if (selectedCategory === category.id) {
            categoryBtn.classList.add('active');
        }
        
        categoriesContainer.appendChild(categoryBtn);
    });
}

// Função para renderizar produtos com estilos corretos
function renderProductsWithStyles() {
    const productsGrid = document.getElementById('productsGrid');
    if (!productsGrid) return;
    
    productsGrid.innerHTML = '';
    
    if (filteredProducts.length === 0) {
        productsGrid.innerHTML = '<div class="no-products">Nenhum produto encontrado</div>';
        return;
    }
    
    filteredProducts.forEach(product => {
        const productCard = document.createElement('div');
        productCard.className = 'product-card';
        
        const imageUrl = product.image_url || '';
        const imageHtml = imageUrl ? 
            `<img src="${imageUrl}" alt="${product.name}" onerror="this.style.display='none'">` : 
            '🍽️';
        
        productCard.innerHTML = `
            <div class="product-image">
                ${imageHtml}
            </div>
            <div class="product-info">
                <div class="product-name">${product.name}</div>
                <div class="product-description">${product.description || 'Descrição não disponível'}</div>
                <div class="product-footer">
                    <div class="product-price">${formatCurrency(product.price)}</div>
                    <button class="add-btn" onclick="addToCart(${product.id})">
                        ➕ Adicionar
                    </button>
                </div>
            </div>
        `;
        
        productsGrid.appendChild(productCard);
    });
}

// Sobrescrever funções originais se necessário
if (typeof renderCategories === 'function') {
    const originalRenderCategories = renderCategories;
    renderCategories = function() {
        originalRenderCategories();
        renderCategoriesWithStyles();
    };
}

if (typeof renderProducts === 'function') {
    const originalRenderProducts = renderProducts;
    renderProducts = function() {
        originalRenderProducts();
        renderProductsWithStyles();
    };
}

// Adicionar estilos CSS dinamicamente se necessário
function addDynamicStyles() {
    const style = document.createElement('style');
    style.textContent = `
        .no-products {
            text-align: center;
            padding: 40px;
            color: #6b7280;
            font-size: 16px;
        }
        
        .loading {
            text-align: center;
            padding: 40px;
            color: #6b7280;
            font-size: 16px;
        }
    `;
    document.head.appendChild(style);
}

// Executar quando o DOM estiver carregado
document.addEventListener('DOMContentLoaded', function() {
    addDynamicStyles();
    
    // Garantir que as categorias sejam renderizadas corretamente
    setTimeout(() => {
        if (typeof categories !== 'undefined' && categories.length > 0) {
            renderCategoriesWithStyles();
        }
    }, 100);
    
    // Garantir que os produtos sejam renderizados corretamente
    setTimeout(() => {
        if (typeof filteredProducts !== 'undefined' && filteredProducts.length > 0) {
            renderProductsWithStyles();
        }
    }, 200);
}); 