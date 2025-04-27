// Função para exibir mensagens de notificação
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// Função genérica para manipular erros de requisição
function handleRequestError(error) {
    console.error('Erro na requisição:', error);
    showNotification(error.message || 'Ocorreu um erro. Tente novamente.', 'error');
}

// Função para fazer requisições AJAX com CSRF token
async function fetchApi(url, options = {}) {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        credentials: 'same-origin'
    };
    
    try {
        const response = await fetch(url, { ...defaultOptions, ...options });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
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
        if (!value && key !== 'description') {  // Description é opcional
            errors.push(`O campo ${key} é obrigatório`);
        }
    }
    
    return errors;
}