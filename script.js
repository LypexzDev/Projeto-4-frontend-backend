
const API_BASE_URL = (() => {
    const validProtocol = window.location.protocol === 'http:' || window.location.protocol === 'https:';
    return validProtocol ? window.location.origin : 'http://127.0.0.1:8000';
})();

const SESSION_STORAGE_KEY = 'lojacontrol_session_v2';
const currencyFormatter = new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL'
});

const state = {
    token: null,
    account: null,
    currentRole: null,
    currentView: null,
    cart: [],
    siteConfig: {},
    productsCache: []
};

const elements = {
    notification: document.getElementById('notification'),
    apiChip: document.getElementById('api-chip'),
    authShell: document.getElementById('auth-shell'),
    appShell: document.getElementById('app-shell'),
    navList: document.getElementById('nav-list'),
    headerTitle: document.getElementById('header-title'),
    headerEyebrow: document.getElementById('header-eyebrow'),
    sessionChip: document.getElementById('session-chip'),
    menuToggle: document.getElementById('menu-toggle'),
    mobileOverlay: document.getElementById('mobile-overlay'),
    logoutBtn: document.getElementById('logout-btn'),
    spotlight: document.getElementById('cursor-spotlight'),
    authTabs: Array.from(document.querySelectorAll('.auth-tab')),
    authViews: Array.from(document.querySelectorAll('.auth-view')),
    refreshDashboard: document.getElementById('refresh-dashboard'),
    refreshProducts: document.getElementById('refresh-products'),
    refreshAdminOrders: document.getElementById('refresh-admin-orders'),
    refreshAdminUsers: document.getElementById('refresh-admin-users'),
    refreshUserOrders: document.getElementById('refresh-user-orders'),
    adminProductList: document.getElementById('admin-product-list'),
    adminOrdersList: document.getElementById('admin-orders-list'),
    adminUsersList: document.getElementById('admin-users-list'),
    shopProducts: document.getElementById('shop-products'),
    cartItems: document.getElementById('cart-items'),
    cartTotalValue: document.getElementById('cart-total-value'),
    userOrdersList: document.getElementById('user-orders-list')
};

const VIEW_META = {
    'admin-dashboard': {
        label: 'Dashboard',
        title: 'Painel administrativo',
        eyebrow: 'Admin',
        loader: () => loadAdminDashboard(false)
    },
    'admin-products': {
        label: 'Produtos',
        title: 'Gerenciar produtos',
        eyebrow: 'Admin',
        loader: loadAdminProducts
    },
    'admin-orders': {
        label: 'Pedidos',
        title: 'Pedidos da loja',
        eyebrow: 'Admin',
        loader: loadAdminOrders
    },
    'admin-users': {
        label: 'Usuarios',
        title: 'Clientes cadastrados',
        eyebrow: 'Admin',
        loader: loadAdminUsers
    },
    'admin-site': {
        label: 'Editar site',
        title: 'Personalizacao visual',
        eyebrow: 'Admin',
        loader: loadAdminSiteConfig
    },
    'user-shop': {
        label: 'Loja',
        title: 'Catalogo de produtos',
        eyebrow: 'Usuario',
        loader: loadShopProducts
    },
    'user-orders': {
        label: 'Compras',
        title: 'Historico de compras',
        eyebrow: 'Usuario',
        loader: loadUserOrders
    },
    'user-profile': {
        label: 'Perfil',
        title: 'Minha conta',
        eyebrow: 'Usuario',
        loader: loadUserProfile
    }
};

const NAV_BY_ROLE = {
    admin: ['admin-dashboard', 'admin-products', 'admin-orders', 'admin-users', 'admin-site'],
    user: ['user-shop', 'user-orders', 'user-profile']
};

let notificationTimeout = null;

function setApiStatus(isOnline) {
    elements.apiChip.textContent = isOnline ? 'API conectada' : 'API offline';
    elements.apiChip.classList.toggle('offline', !isOnline);
}

function showNotification(message, type = 'success') {
    if (!message) {
        return;
    }

    elements.notification.textContent = message;
    elements.notification.className = `notification ${type} show`;
    elements.notification.classList.remove('hidden');

    clearTimeout(notificationTimeout);
    notificationTimeout = setTimeout(() => {
        elements.notification.classList.remove('show');
        elements.notification.classList.add('hidden');
    }, 3200);
}

function closeMobileMenu() {
    document.body.classList.remove('menu-open');
}

function escapeHtml(value) {
    return String(value ?? '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

function saveSessionToken(token) {
    localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify({ token }));
}

function readSavedToken() {
    try {
        const raw = localStorage.getItem(SESSION_STORAGE_KEY);
        if (!raw) {
            return null;
        }
        const parsed = JSON.parse(raw);
        return parsed?.token || null;
    } catch {
        return null;
    }
}

function clearSessionToken() {
    localStorage.removeItem(SESSION_STORAGE_KEY);
}

function resetClientState() {
    state.token = null;
    state.account = null;
    state.currentRole = null;
    state.currentView = null;
    state.cart = [];
    state.productsCache = [];
    renderCart();
}

function switchAuthView(viewId) {
    elements.authTabs.forEach((tab) => {
        tab.classList.toggle('active', tab.dataset.authView === viewId);
    });
    elements.authViews.forEach((view) => {
        view.classList.toggle('active', view.id === `form-${viewId}`);
    });
}

function showAuthScreen() {
    closeMobileMenu();
    elements.authShell.classList.remove('hidden');
    elements.appShell.classList.add('hidden');
    switchAuthView('user-login');
}

function applySiteConfig(config) {
    if (!config || typeof config !== 'object') {
        return;
    }

    state.siteConfig = config;

    const root = document.documentElement;
    if (config.accent_color) {
        root.style.setProperty('--accent', config.accent_color);
    }
    if (config.highlight_color) {
        root.style.setProperty('--highlight', config.highlight_color);
    }

    const siteName = config.site_name || 'LojaControl';
    const tagline = config.tagline || 'Painel comercial e compras online';
    const heroTitle = config.hero_title || 'Loja online';
    const heroSubtitle = config.hero_subtitle || 'Navegue pelos produtos e finalize sua compra.';

    document.title = `${siteName} - Sistema`;

    const textMap = {
        'auth-site-name': siteName,
        'auth-tagline': tagline,
        'auth-subtitle': heroSubtitle,
        'brand-name': siteName,
        'brand-tagline': tagline,
        'shop-title': heroTitle,
        'shop-subtitle': heroSubtitle
    };

    Object.entries(textMap).forEach(([id, value]) => {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    });
}

async function parseApiPayload(response) {
    const text = await response.text();
    if (!text) {
        return {};
    }
    try {
        return JSON.parse(text);
    } catch {
        return {};
    }
}

function handleUnauthorized() {
    resetClientState();
    clearSessionToken();
    showAuthScreen();
    showNotification('Sessao expirada. Faca login novamente.', 'error');
}

async function apiRequest({ endpoint, method = 'GET', body = null, auth = true }) {
    const headers = {};
    if (body !== null) {
        headers['Content-Type'] = 'application/json';
    }
    if (auth && state.token) {
        headers.Authorization = `Bearer ${state.token}`;
    }

    let response;
    try {
        response = await fetch(`${API_BASE_URL}${endpoint}`, {
            method,
            headers,
            body: body !== null ? JSON.stringify(body) : null
        });
    } catch (error) {
        setApiStatus(false);
        throw new Error('Falha de conexao com o servidor.');
    }

    const payload = await parseApiPayload(response);

    if (!response.ok) {
        if (response.status === 401 && auth) {
            handleUnauthorized();
        }
        const message = payload?.detail || `Erro ${response.status}.`;
        throw new Error(message);
    }

    setApiStatus(true);
    return payload;
}

function renderNavigation(role) {
    const items = NAV_BY_ROLE[role] || [];
    elements.navList.innerHTML = '';

    items.forEach((viewId, index) => {
        const view = VIEW_META[viewId];
        if (!view) {
            return;
        }

        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'nav-btn';
        if (index === 0) {
            button.classList.add('active');
        }
        button.dataset.target = viewId;
        button.textContent = view.label;
        elements.navList.appendChild(button);
    });
}

function setHeaderFromView(viewId) {
    const meta = VIEW_META[viewId];
    if (!meta) {
        return;
    }
    elements.headerTitle.textContent = meta.title;
    elements.headerEyebrow.textContent = meta.eyebrow;
}

async function navigate(viewId, force = false) {
    if (!force && state.currentView === viewId) {
        return;
    }

    const allowedViews = NAV_BY_ROLE[state.currentRole] || [];
    if (!allowedViews.includes(viewId)) {
        return;
    }

    document.querySelectorAll('.view').forEach((section) => {
        section.classList.toggle('active', section.id === viewId);
    });

    document.querySelectorAll('.nav-btn').forEach((button) => {
        button.classList.toggle('active', button.dataset.target === viewId);
    });

    closeMobileMenu();
    state.currentView = viewId;
    setHeaderFromView(viewId);

    const meta = VIEW_META[viewId];
    if (meta?.loader) {
        await meta.loader();
    }
}

async function openAppForAccount(account) {
    state.account = account;
    state.currentRole = account.role;
    elements.sessionChip.textContent = `${account.nome} (${account.role === 'admin' ? 'Admin' : 'Usuario'})`;
    elements.authShell.classList.add('hidden');
    elements.appShell.classList.remove('hidden');
    renderNavigation(account.role);

    const firstView = (NAV_BY_ROLE[account.role] || [])[0];
    if (firstView) {
        await navigate(firstView, true);
    }

    activateInteractiveCards();
}

async function logout() {
    try {
        if (state.token) {
            await apiRequest({ endpoint: '/auth/logout', method: 'POST' });
        }
    } catch {
        // Logout local continua valido mesmo com erro de rede.
    }

    resetClientState();
    clearSessionToken();
    showAuthScreen();
    showNotification('Sessao encerrada.', 'success');
}

async function fetchPublicSiteConfig() {
    try {
        const config = await apiRequest({ endpoint: '/site-config', auth: false });
        applySiteConfig(config);
    } catch (error) {
        showNotification('Nao foi possivel carregar configuracao do site.', 'error');
    }
}

async function tryRestoreSession() {
    const savedToken = readSavedToken();
    if (!savedToken) {
        return false;
    }

    state.token = savedToken;
    try {
        const data = await apiRequest({ endpoint: '/auth/me' });
        await openAppForAccount(data.account);
        return true;
    } catch {
        resetClientState();
        clearSessionToken();
        return false;
    }
}
function renderAdminProductsList(products) {
    elements.adminProductList.innerHTML = '';

    if (!Array.isArray(products) || products.length === 0) {
        elements.adminProductList.innerHTML = '<p class="meta">Nenhum produto cadastrado.</p>';
        return;
    }

    products.forEach((produto) => {
        const card = document.createElement('article');
        card.className = 'product-editor-card interactive';
        card.dataset.produtoId = String(produto.id);
        card.innerHTML = `
            <h3>#${produto.id} - ${escapeHtml(produto.nome)}</h3>
            <div class="input-group">
                <label>Nome</label>
                <input class="edit-prod-name" type="text" value="${escapeHtml(produto.nome)}">
            </div>
            <div class="input-group">
                <label>Descricao</label>
                <input class="edit-prod-description" type="text" value="${escapeHtml(produto.descricao || '')}">
            </div>
            <div class="input-group">
                <label>Preco (R$)</label>
                <input class="edit-prod-price" type="number" min="0.01" step="0.01" value="${Number(produto.preco).toFixed(2)}">
            </div>
            <div class="product-editor-actions">
                <button type="button" class="btn-secondary" data-product-action="save">Salvar</button>
                <button type="button" class="btn-danger" data-product-action="delete">Excluir</button>
            </div>
        `;
        elements.adminProductList.appendChild(card);
    });

    activateInteractiveCards(elements.adminProductList);
}

function renderList(targetElement, entries, formatter) {
    targetElement.innerHTML = '';

    if (!Array.isArray(entries) || entries.length === 0) {
        const emptyItem = document.createElement('li');
        emptyItem.className = 'empty';
        emptyItem.textContent = 'Sem registros por enquanto.';
        targetElement.appendChild(emptyItem);
        return;
    }

    entries.forEach((entry) => {
        const item = document.createElement('li');
        item.innerHTML = formatter(entry);
        targetElement.appendChild(item);
    });
}

async function loadAdminDashboard(showFeedback = false) {
    try {
        const resumo = await apiRequest({ endpoint: '/admin/resumo' });
        document.getElementById('stat-usuarios').textContent = resumo?.usuarios ?? 0;
        document.getElementById('stat-produtos').textContent = resumo?.produtos ?? 0;
        document.getElementById('stat-pedidos').textContent = resumo?.pedidos ?? 0;
        document.getElementById('stat-faturamento').textContent = currencyFormatter.format(resumo?.faturamento ?? 0);
        document.getElementById('stat-saldo').textContent = currencyFormatter.format(resumo?.saldo_total ?? 0);
        if (showFeedback) {
            showNotification('Resumo atualizado.', 'success');
        }
    } catch (error) {
        showNotification(error.message || 'Falha ao carregar resumo.', 'error');
    }
}

async function loadAdminProducts() {
    try {
        const products = await apiRequest({ endpoint: '/admin/produtos' });
        renderAdminProductsList(products);
    } catch (error) {
        showNotification(error.message || 'Falha ao carregar produtos.', 'error');
    }
}

async function loadAdminOrders() {
    try {
        const pedidos = await apiRequest({ endpoint: '/admin/pedidos' });
        renderList(elements.adminOrdersList, pedidos, (pedido) => {
            const produtos = (pedido.produtos || []).map((item) => item.nome).join(', ') || 'Sem itens';
            return `
                <strong>Pedido #${pedido.id}</strong><br>
                Cliente: ${escapeHtml(pedido.usuario_nome)}<br>
                Itens: ${escapeHtml(produtos)}<br>
                Total: ${currencyFormatter.format(Number(pedido.total || 0))}
            `;
        });
    } catch (error) {
        showNotification(error.message || 'Falha ao carregar pedidos.', 'error');
    }
}

async function loadAdminUsers() {
    try {
        const usuarios = await apiRequest({ endpoint: '/admin/usuarios' });
        renderList(elements.adminUsersList, usuarios, (usuario) => `
            <strong>#${usuario.id} - ${escapeHtml(usuario.nome)}</strong><br>
            E-mail: ${escapeHtml(usuario.email)}<br>
            Saldo: ${currencyFormatter.format(Number(usuario.saldo || 0))}
        `);
    } catch (error) {
        showNotification(error.message || 'Falha ao carregar usuarios.', 'error');
    }
}

function fillSiteConfigForm(config) {
    document.getElementById('site-name').value = config.site_name || '';
    document.getElementById('site-tagline').value = config.tagline || '';
    document.getElementById('site-hero-title').value = config.hero_title || '';
    document.getElementById('site-hero-subtitle').value = config.hero_subtitle || '';
    document.getElementById('site-accent-color').value = config.accent_color || '#1ec8a5';
    document.getElementById('site-highlight-color').value = config.highlight_color || '#1ea4d8';
}

async function loadAdminSiteConfig() {
    try {
        const config = await apiRequest({ endpoint: '/admin/site-config' });
        fillSiteConfigForm(config);
    } catch (error) {
        showNotification(error.message || 'Falha ao carregar configuracao.', 'error');
    }
}

function addToCart(product) {
    const found = state.cart.find((item) => item.id === product.id);
    if (found) {
        found.qty += 1;
    } else {
        state.cart.push({
            id: product.id,
            nome: product.nome,
            preco: Number(product.preco || 0),
            qty: 1
        });
    }
    renderCart();
}

function removeFromCart(productId) {
    state.cart = state.cart.filter((item) => item.id !== productId);
    renderCart();
}

function renderCart() {
    elements.cartItems.innerHTML = '';

    if (state.cart.length === 0) {
        const empty = document.createElement('li');
        empty.className = 'empty';
        empty.textContent = 'Seu carrinho esta vazio.';
        elements.cartItems.appendChild(empty);
        elements.cartTotalValue.textContent = currencyFormatter.format(0);
        return;
    }

    let total = 0;
    state.cart.forEach((item) => {
        total += item.preco * item.qty;
        const li = document.createElement('li');
        li.innerHTML = `
            <strong>${escapeHtml(item.nome)}</strong><br>
            Quantidade: ${item.qty}<br>
            Subtotal: ${currencyFormatter.format(item.preco * item.qty)}<br>
            <button type="button" class="btn-danger" data-remove-cart="${item.id}">Remover</button>
        `;
        elements.cartItems.appendChild(li);
    });

    elements.cartTotalValue.textContent = currencyFormatter.format(total);
}

function renderShopProducts(products) {
    elements.shopProducts.innerHTML = '';

    if (!Array.isArray(products) || products.length === 0) {
        elements.shopProducts.innerHTML = '<p class="meta">Nenhum produto disponivel no momento.</p>';
        return;
    }

    products.forEach((product) => {
        const card = document.createElement('article');
        card.className = 'product-card interactive';
        card.innerHTML = `
            <h3>${escapeHtml(product.nome)}</h3>
            <p>${escapeHtml(product.descricao || 'Sem descricao informada.')}</p>
            <div class="price-tag">${currencyFormatter.format(Number(product.preco || 0))}</div>
            <button type="button" class="btn-primary" data-add-product="${product.id}">Adicionar ao carrinho</button>
        `;
        elements.shopProducts.appendChild(card);
    });

    activateInteractiveCards(elements.shopProducts);
}

async function loadShopProducts() {
    try {
        const products = await apiRequest({ endpoint: '/shop/produtos', auth: false });
        state.productsCache = Array.isArray(products) ? products : [];
        renderShopProducts(state.productsCache);
    } catch (error) {
        showNotification(error.message || 'Falha ao carregar catalogo.', 'error');
    }
}

async function loadUserOrders() {
    try {
        const orders = await apiRequest({ endpoint: '/shop/pedidos' });
        renderList(elements.userOrdersList, orders, (order) => {
            const items = (order.produtos || []).map((item) => item.nome).join(', ') || 'Sem itens';
            return `
                <strong>Pedido #${order.id}</strong><br>
                Itens: ${escapeHtml(items)}<br>
                Total: ${currencyFormatter.format(Number(order.total || 0))}<br>
                Data: ${escapeHtml(order.created_at || '-')}
            `;
        });
    } catch (error) {
        showNotification(error.message || 'Falha ao carregar suas compras.', 'error');
    }
}

async function loadUserProfile() {
    try {
        const profile = await apiRequest({ endpoint: '/shop/me' });
        document.getElementById('profile-name').textContent = profile.nome || '-';
        document.getElementById('profile-email').textContent = profile.email || '-';
        document.getElementById('profile-balance').textContent = currencyFormatter.format(Number(profile.saldo || 0));
    } catch (error) {
        showNotification(error.message || 'Falha ao carregar perfil.', 'error');
    }
}

async function checkoutCart() {
    if (state.cart.length === 0) {
        showNotification('Adicione produtos ao carrinho antes de finalizar.', 'error');
        return;
    }

    const produtosIds = [];
    state.cart.forEach((item) => {
        for (let i = 0; i < item.qty; i += 1) {
            produtosIds.push(item.id);
        }
    });

    try {
        await apiRequest({
            endpoint: '/shop/pedidos',
            method: 'POST',
            body: { produtos_ids: produtosIds }
        });
        state.cart = [];
        renderCart();
        showNotification('Compra finalizada com sucesso.', 'success');
        await Promise.all([loadUserProfile(), loadUserOrders()]);
    } catch (error) {
        showNotification(error.message || 'Nao foi possivel finalizar a compra.', 'error');
    }
}

function setupAuthTabs() {
    elements.authTabs.forEach((button) => {
        button.addEventListener('click', () => {
            switchAuthView(button.dataset.authView);
        });
    });
}

function setupNavigationClicks() {
    elements.navList.addEventListener('click', async (event) => {
        const button = event.target.closest('.nav-btn');
        if (!button) {
            return;
        }
        await navigate(button.dataset.target);
    });
}

function setupMobileMenu() {
    elements.menuToggle.addEventListener('click', () => {
        document.body.classList.toggle('menu-open');
    });

    elements.mobileOverlay.addEventListener('click', closeMobileMenu);
    window.addEventListener('resize', () => {
        if (window.innerWidth > 980) {
            closeMobileMenu();
        }
    });
}

function setupSpotlightEffect() {
    const supportsFinePointer = window.matchMedia('(hover: hover) and (pointer: fine)').matches;
    if (!supportsFinePointer || !elements.spotlight) {
        return;
    }

    let frame = null;
    let point = { x: 0, y: 0, visible: false };

    const render = () => {
        elements.spotlight.style.left = `${point.x}px`;
        elements.spotlight.style.top = `${point.y}px`;
        elements.spotlight.style.opacity = point.visible ? '1' : '0';
        frame = null;
    };

    const requestRender = () => {
        if (!frame) {
            frame = requestAnimationFrame(render);
        }
    };

    window.addEventListener('mousemove', (event) => {
        point = { x: event.clientX, y: event.clientY, visible: true };
        requestRender();
    });

    window.addEventListener('mouseout', (event) => {
        if (!event.relatedTarget) {
            point.visible = false;
            requestRender();
        }
    });
}
function bindTilt(card) {
    if (card.dataset.tiltBound === '1') {
        return;
    }

    const supportsFinePointer = window.matchMedia('(hover: hover) and (pointer: fine)').matches;
    if (!supportsFinePointer) {
        return;
    }

    card.dataset.tiltBound = '1';
    const maxTilt = 7;
    let frame = null;

    const resetCard = () => {
        card.style.transform = 'perspective(900px) rotateX(0deg) rotateY(0deg)';
    };

    card.addEventListener('pointermove', (event) => {
        const rect = card.getBoundingClientRect();
        const x = (event.clientX - rect.left) / rect.width - 0.5;
        const y = (event.clientY - rect.top) / rect.height - 0.5;
        const rotateY = x * maxTilt;
        const rotateX = -y * maxTilt;

        if (frame) {
            cancelAnimationFrame(frame);
        }

        frame = requestAnimationFrame(() => {
            card.style.transform = `perspective(900px) rotateX(${rotateX.toFixed(2)}deg) rotateY(${rotateY.toFixed(2)}deg)`;
        });
    });

    card.addEventListener('pointerleave', resetCard);
    resetCard();
}

function activateInteractiveCards(container = document) {
    container.querySelectorAll('.interactive').forEach((card) => bindTilt(card));
}

function setupAuthForms() {
    document.getElementById('form-user-login').addEventListener('submit', async (event) => {
        event.preventDefault();
        const payload = {
            email: document.getElementById('login-user-email').value.trim(),
            password: document.getElementById('login-user-password').value
        };

        try {
            const data = await apiRequest({
                endpoint: '/auth/login-user',
                method: 'POST',
                body: payload,
                auth: false
            });
            state.token = data.token;
            saveSessionToken(data.token);
            showNotification('Login realizado com sucesso.', 'success');
            await openAppForAccount(data.account);
            event.target.reset();
        } catch (error) {
            showNotification(error.message || 'Falha no login do usuario.', 'error');
        }
    });

    document.getElementById('form-admin-login').addEventListener('submit', async (event) => {
        event.preventDefault();
        const payload = {
            email: document.getElementById('login-admin-email').value.trim(),
            password: document.getElementById('login-admin-password').value
        };

        try {
            const data = await apiRequest({
                endpoint: '/auth/login-admin',
                method: 'POST',
                body: payload,
                auth: false
            });
            state.token = data.token;
            saveSessionToken(data.token);
            showNotification('Login admin realizado.', 'success');
            await openAppForAccount(data.account);
            event.target.reset();
        } catch (error) {
            showNotification(error.message || 'Falha no login do admin.', 'error');
        }
    });

    document.getElementById('form-user-register').addEventListener('submit', async (event) => {
        event.preventDefault();
        const payload = {
            nome: document.getElementById('reg-user-name').value.trim(),
            email: document.getElementById('reg-user-email').value.trim(),
            password: document.getElementById('reg-user-password').value,
            saldo_inicial: Number(document.getElementById('reg-user-balance').value || 0)
        };

        try {
            await apiRequest({
                endpoint: '/auth/register-user',
                method: 'POST',
                body: payload,
                auth: false
            });
            showNotification('Cadastro concluido. Agora faca login como usuario.', 'success');
            event.target.reset();
            document.getElementById('login-user-email').value = payload.email;
            switchAuthView('user-login');
        } catch (error) {
            showNotification(error.message || 'Falha ao cadastrar usuario.', 'error');
        }
    });
}

function setupAdminActions() {
    document.getElementById('form-admin-product').addEventListener('submit', async (event) => {
        event.preventDefault();
        const payload = {
            nome: document.getElementById('admin-prod-name').value.trim(),
            descricao: document.getElementById('admin-prod-description').value.trim(),
            preco: Number(document.getElementById('admin-prod-price').value)
        };

        try {
            await apiRequest({
                endpoint: '/admin/produtos',
                method: 'POST',
                body: payload
            });
            showNotification('Produto criado com sucesso.', 'success');
            event.target.reset();
            await Promise.all([loadAdminProducts(), loadAdminDashboard(false)]);
        } catch (error) {
            showNotification(error.message || 'Falha ao criar produto.', 'error');
        }
    });

    elements.adminProductList.addEventListener('click', async (event) => {
        const button = event.target.closest('button[data-product-action]');
        if (!button) {
            return;
        }

        const card = button.closest('[data-produto-id]');
        if (!card) {
            return;
        }

        const produtoId = Number(card.dataset.produtoId);
        const action = button.dataset.productAction;

        if (action === 'save') {
            const payload = {
                nome: card.querySelector('.edit-prod-name').value.trim(),
                descricao: card.querySelector('.edit-prod-description').value.trim(),
                preco: Number(card.querySelector('.edit-prod-price').value)
            };

            try {
                await apiRequest({
                    endpoint: `/admin/produtos/${produtoId}`,
                    method: 'PATCH',
                    body: payload
                });
                showNotification('Produto atualizado.', 'success');
                await loadAdminProducts();
            } catch (error) {
                showNotification(error.message || 'Falha ao atualizar produto.', 'error');
            }
        }

        if (action === 'delete') {
            const confirmed = window.confirm('Deseja excluir este produto?');
            if (!confirmed) {
                return;
            }

            try {
                await apiRequest({
                    endpoint: `/admin/produtos/${produtoId}`,
                    method: 'DELETE'
                });
                showNotification('Produto removido.', 'success');
                await Promise.all([loadAdminProducts(), loadAdminDashboard(false)]);
            } catch (error) {
                showNotification(error.message || 'Falha ao excluir produto.', 'error');
            }
        }
    });

    document.getElementById('form-site-config').addEventListener('submit', async (event) => {
        event.preventDefault();
        const payload = {
            site_name: document.getElementById('site-name').value.trim(),
            tagline: document.getElementById('site-tagline').value.trim(),
            hero_title: document.getElementById('site-hero-title').value.trim(),
            hero_subtitle: document.getElementById('site-hero-subtitle').value.trim(),
            accent_color: document.getElementById('site-accent-color').value,
            highlight_color: document.getElementById('site-highlight-color').value
        };

        try {
            const config = await apiRequest({
                endpoint: '/admin/site-config',
                method: 'PATCH',
                body: payload
            });
            applySiteConfig(config);
            showNotification('Visual atualizado com sucesso.', 'success');
        } catch (error) {
            showNotification(error.message || 'Falha ao salvar configuracao.', 'error');
        }
    });
}
function setupUserActions() {
    elements.shopProducts.addEventListener('click', (event) => {
        const button = event.target.closest('[data-add-product]');
        if (!button) {
            return;
        }

        const productId = Number(button.dataset.addProduct);
        const product = state.productsCache.find((item) => Number(item.id) === productId);
        if (!product) {
            showNotification('Produto nao encontrado.', 'error');
            return;
        }
        addToCart(product);
        showNotification('Produto adicionado ao carrinho.', 'success');
    });

    elements.cartItems.addEventListener('click', (event) => {
        const button = event.target.closest('[data-remove-cart]');
        if (!button) {
            return;
        }
        removeFromCart(Number(button.dataset.removeCart));
    });

    document.getElementById('checkout-btn').addEventListener('click', checkoutCart);

    document.getElementById('form-recarga').addEventListener('submit', async (event) => {
        event.preventDefault();
        const valor = Number(document.getElementById('recarga-valor').value);
        try {
            await apiRequest({
                endpoint: '/shop/recarga',
                method: 'POST',
                body: { valor }
            });
            showNotification('Saldo adicionado com sucesso.', 'success');
            event.target.reset();
            await loadUserProfile();
        } catch (error) {
            showNotification(error.message || 'Falha ao adicionar saldo.', 'error');
        }
    });
}

function setupHeaderActions() {
    elements.refreshDashboard.addEventListener('click', () => loadAdminDashboard(true));
    elements.refreshProducts.addEventListener('click', loadAdminProducts);
    elements.refreshAdminOrders.addEventListener('click', loadAdminOrders);
    elements.refreshAdminUsers.addEventListener('click', loadAdminUsers);
    elements.refreshUserOrders.addEventListener('click', loadUserOrders);
    elements.logoutBtn.addEventListener('click', logout);
}

async function init() {
    setApiStatus(true);
    renderCart();
    setupSpotlightEffect();
    setupMobileMenu();
    setupAuthTabs();
    setupNavigationClicks();
    setupAuthForms();
    setupAdminActions();
    setupUserActions();
    setupHeaderActions();
    activateInteractiveCards();

    await fetchPublicSiteConfig();
    const restored = await tryRestoreSession();
    if (!restored) {
        showAuthScreen();
    }
}

document.addEventListener('DOMContentLoaded', init);
