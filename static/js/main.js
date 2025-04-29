// Função para exibir mensagens de notificação
function showNotification(message, type = 'info') {
    // Criar um elemento de alerta Bootstrap
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show`;
    notification.setAttribute('role', 'alert');
    
    // Adicionar conteúdo
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Criar container se não existir
    let notificationContainer = document.querySelector('.notification-container');
    if (!notificationContainer) {
        notificationContainer = document.createElement('div');
        notificationContainer.className = 'notification-container position-fixed top-0 end-0 p-3';
        notificationContainer.style.zIndex = '1050';
        document.body.appendChild(notificationContainer);
    }
    
    // Adicionar notificação ao container
    notificationContainer.appendChild(notification);
    
    // Inicializar alerta Bootstrap
    const alertInstance = new bootstrap.Alert(notification);
    
    // Remover após 5 segundos
    setTimeout(() => {
        alertInstance.close();
    }, 5000);
}

// Função genérica para manipular erros de requisição
function handleRequestError(error) {
    console.error('Erro na requisição:', error);
    showNotification(error.message || 'Ocorreu um erro. Tente novamente.', 'danger');
}

// Função para fazer requisições AJAX com CSRF token
async function fetchApi(url, options = {}) {
    // Obter CSRF token do DOM
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]') ? 
                     document.querySelector('[name=csrfmiddlewaretoken]').value :
                     document.cookie.replace(/(?:(?:^|.*;\s*)csrftoken\s*\=\s*([^;]*).*$)|^.*$/, "$1");
    
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        credentials: 'same-origin'
    };
    
    try {
        const response = await fetch(url, { ...defaultOptions, ...options });
        
        // Verificar se a resposta é ok
        if (!response.ok) {
            // Tentar obter mensagem de erro do JSON da resposta
            let errorMessage;
            try {
                const errorData = await response.json();
                errorMessage = errorData.message || errorData.detail || `Erro ${response.status}: ${response.statusText}`;
            } catch (e) {
                errorMessage = `Erro ${response.status}: ${response.statusText}`;
            }
            
            throw new Error(errorMessage);
        }
        
        // Se a resposta não for JSON, retornar response diretamente
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            return await response.json();
        } else {
            return response;
        }
    } catch (error) {
        handleRequestError(error);
        throw error;
    }
}

// Função para formatar data para exibição
function formatDate(dateString) {
    const options = { day: '2-digit', month: '2-digit', year: 'numeric' };
    return new Date(dateString).toLocaleDateString('pt-BR', options);
}

// Função para validar formulários
function validateForm(formData) {
    const errors = [];
    
    for (const [key, value] of formData.entries()) {
        if (!value && key !== 'description' && key !== 'notes') {  // Campos opcionais
            errors.push(`O campo ${key} é obrigatório`);
        }
    }
    
    return errors;
}

// Função para inicializar tooltips do Bootstrap
function initTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Função para inicializar popovers do Bootstrap
function initPopovers() {
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
}

// Função para destacar item de menu ativo
function highlightActiveMenu() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
    
    navLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (href === currentPath || (href !== '/' && currentPath.includes(href))) {
            link.classList.add('active');
        }
    });
}

// Função para criar botões de ação
function createActionButton(icon, text, btnClass, clickHandler) {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = `btn btn-${btnClass} btn-sm`;
    button.innerHTML = `<i class="fas fa-${icon}"></i> ${text}`;
    button.addEventListener('click', clickHandler);
    return button;
}

// Função para criar badges de status
function createStatusBadge(status) {
    const badge = document.createElement('span');
    let badgeClass, badgeText;
    
    switch (status) {
        case 'available':
            badgeClass = 'bg-success';
            badgeText = 'Disponível';
            break;
        case 'occupied':
            badgeClass = 'bg-danger';
            badgeText = 'Ocupado';
            break;
        case 'cleaning':
            badgeClass = 'bg-warning text-dark';
            badgeText = 'Limpeza';
            break;
        case 'maintenance':
            badgeClass = 'bg-info';
            badgeText = 'Manutenção';
            break;
        case 'confirmed':
            badgeClass = 'bg-success';
            badgeText = 'Confirmado';
            break;
        case 'pending':
            badgeClass = 'bg-warning text-dark';
            badgeText = 'Pendente';
            break;
        case 'cancelled':
            badgeClass = 'bg-danger';
            badgeText = 'Cancelado';
            break;
        default:
            badgeClass = 'bg-secondary';
            badgeText = status || 'Desconhecido';
    }
    
    badge.className = `badge ${badgeClass}`;
    badge.textContent = badgeText;
    return badge;
}

// Função para formatar moeda
function formatCurrency(value) {
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL'
    }).format(value);
}

// Função para mostrar/esconder loader
function toggleLoader(show) {
    let loader = document.querySelector('.global-loader');
    
    if (!loader && show) {
        loader = document.createElement('div');
        loader.className = 'global-loader d-flex justify-content-center align-items-center position-fixed';
        loader.style.cssText = 'top: 0; left: 0; width: 100%; height: 100%; background: rgba(255,255,255,0.7); z-index: 9999;';
        
        const spinner = document.createElement('div');
        spinner.className = 'spinner-border text-primary';
        spinner.setAttribute('role', 'status');
        
        const span = document.createElement('span');
        span.className = 'visually-hidden';
        span.textContent = 'Carregando...';
        
        spinner.appendChild(span);
        loader.appendChild(spinner);
        document.body.appendChild(loader);
    } else if (loader && !show) {
        loader.remove();
    }
}

// Evento DOMContentLoaded para inicializar componentes
document.addEventListener('DOMContentLoaded', function() {
    // Inicializar tooltips e popovers do Bootstrap
    initTooltips();
    initPopovers();
    
    // Destacar item de menu ativo
    highlightActiveMenu();
    
    // Animação para elementos que entram na tela
    const animateElements = document.querySelectorAll('.animate-fade-in');
    animateElements.forEach(element => {
        element.style.opacity = '1';
        element.style.transform = 'translateY(0)';
    });
});