// Variáveis globais para os modais
let roomModal, changeStatusModal, maintenanceModal;
let editingRoomId = null;
let currentRoom = null;
const API_BASE_URL = '/api'; // URL base para endpoints da API

// Inicialização
document.addEventListener('DOMContentLoaded', () => {
    // Inicializar os modais do Bootstrap
    roomModal = new bootstrap.Modal(document.getElementById('roomModal'));
    changeStatusModal = new bootstrap.Modal(document.getElementById('changeStatusModal'));
    maintenanceModal = new bootstrap.Modal(document.getElementById('maintenanceModal'));
    
    // Configurar botões de salvar
    document.getElementById('saveRoomBtn').addEventListener('click', handleRoomFormSubmit);
    document.getElementById('saveStatusBtn').addEventListener('click', handleStatusChange);
    document.getElementById('addMaintenanceBtn').addEventListener('click', handleAddMaintenance);
    
    // Inicializar filtros
    const typeFilter = document.getElementById('room-type-filter');
    const statusFilter = document.getElementById('status-filter');
    
    [typeFilter, statusFilter].forEach(filter => {
        filter.addEventListener('change', () => {
            const params = new URLSearchParams();
            if (typeFilter.value) params.append('type', typeFilter.value);
            if (statusFilter.value) params.append('status', statusFilter.value);
            
            window.location.href = `?${params.toString()}`;
        });
    });
    
    // Preencher os filtros com valores da URL
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has('type')) typeFilter.value = urlParams.get('type');
    if (urlParams.has('status')) statusFilter.value = urlParams.get('status');
});

// Função para fazer requisições à API com tratamento de erro aprimorado
async function apiRequest(endpoint, options = {}) {
    try {
        // Configuração padrão
        const defaultOptions = {
            credentials: 'same-origin',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': 'application/json',
            }
        };
        
        // Se for método POST, PUT, PATCH, adiciona token CSRF e configura Content-Type
        if (['POST', 'PUT', 'PATCH'].includes(options.method)) {
            defaultOptions.headers['X-CSRFToken'] = getCsrfToken();
            defaultOptions.headers['Content-Type'] = 'application/json';
        }
        
        // Mescla as opções padrão com as fornecidas
        const requestOptions = {
            ...defaultOptions,
            ...options,
            headers: {
                ...defaultOptions.headers,
                ...(options.headers || {})
            }
        };
        
        console.debug(`Fazendo requisição para ${endpoint}`, requestOptions);
        
        // Faz a requisição
        const response = await fetch(`${API_BASE_URL}${endpoint}`, requestOptions);
        
        // Se a resposta não for OK, lança um erro com detalhes
        if (!response.ok) {
            // Tenta obter mensagem de erro da resposta
            let errorText = `Status: ${response.status} ${response.statusText}`;
            try {
                const errorJson = await response.json();
                if (errorJson.message) errorText = errorJson.message;
                else if (errorJson.detail) errorText = errorJson.detail;
            } catch (e) {
                // Se não conseguir ler o JSON, usa apenas o status
                console.error('Não foi possível ler detalhes do erro:', e);
            }
            
            throw new Error(`Erro na requisição: ${errorText}`);
        }
        
        // Se a resposta estiver vazia, retorna objeto vazio
        if (response.status === 204) {
            return {};
        }
        
        // Retorna os dados da resposta
        return await response.json();
    } catch (error) {
        console.error('Erro na API:', error);
        throw error; // Re-lança o erro para ser tratado pelo chamador
    }
}

// Funções para manipular os quartos
function openAddRoomModal() {
    // Reset do formulário
    document.getElementById('roomForm').reset();
    document.getElementById('modalTitle').textContent = 'Novo Quarto';
    editingRoomId = null;
    roomModal.show();
}

async function editRoom(roomId) {
    try {
        // Configurar o modal para edição
        document.getElementById('modalTitle').textContent = 'Editar Quarto';
        editingRoomId = roomId;
        
        // Mostrar indicador de carregamento
        showNotification('Carregando dados do quarto...', 'info');
        
        // Buscar dados do quarto
        const room = await apiRequest(`/rooms/${roomId}/`, { method: 'GET' });
        
        // Preencher o formulário
        document.getElementById('number').value = room.number;
        document.getElementById('room_type').value = room.room_type;
        document.getElementById('status').value = room.status;
        document.getElementById('description').value = room.description || '';
        
        // Mostrar o modal
        roomModal.show();
    } catch (error) {
        console.error('Erro ao editar quarto:', error);
        showNotification('Erro ao carregar dados do quarto: ' + error.message, 'danger');
    }
}

async function handleRoomFormSubmit() {
    try {
        const form = document.getElementById('roomForm');
        
        if (!form.checkValidity()) {
            form.reportValidity();
            return;
        }
        
        // Coletar dados do formulário
        const formData = new FormData(form);
        const roomData = {
            number: formData.get('number'),
            room_type: formData.get('room_type'),
            status: formData.get('status'),
            description: formData.get('description')
        };
        
        // Determinar se é uma criação ou atualização
        const endpoint = editingRoomId ? `/rooms/${editingRoomId}/` : '/rooms/';
        const method = editingRoomId ? 'PUT' : 'POST';
        
        // Mostrar indicador de carregamento
        showNotification('Salvando dados...', 'info');
        
        // Enviar requisição à API
        await apiRequest(endpoint, {
            method: method,
            body: JSON.stringify(roomData)
        });
        
        showNotification(`Quarto ${editingRoomId ? 'atualizado' : 'criado'} com sucesso!`, 'success');
        roomModal.hide();
        setTimeout(() => window.location.reload(), 1000); // Recarrega após 1 segundo
    } catch (error) {
        console.error('Erro ao salvar quarto:', error);
        showNotification('Erro ao salvar o quarto: ' + error.message, 'danger');
    }
}

async function changeStatus(roomId) {
    try {
        // Configurar o modal de mudança de status
        document.getElementById('roomId').value = roomId;
        currentRoom = roomId;
        
        // Mostrar indicador de carregamento
        showNotification('Carregando status atual...', 'info');
        
        // Buscar o status atual do quarto para pré-selecionar
        const room = await apiRequest(`/rooms/${roomId}/`, { method: 'GET' });
        document.getElementById('newStatus').value = room.status;
        
        // Mostrar o modal
        changeStatusModal.show();
    } catch (error) {
        console.error('Erro ao carregar status:', error);
        showNotification('Erro ao carregar status do quarto: ' + error.message, 'danger');
    }
}

async function handleStatusChange() {
    try {
        const roomId = document.getElementById('roomId').value;
        const newStatus = document.getElementById('newStatus').value;
        
        // Mostrar indicador de carregamento
        showNotification('Atualizando status...', 'info');
        
        // Enviar requisição para atualizar status
        const response = await apiRequest(`/rooms/${roomId}/change-status/`, {
            method: 'POST',
            body: JSON.stringify({ status: newStatus })
        });
        
        showNotification(response.message || 'Status atualizado com sucesso!', 'success');
        changeStatusModal.hide();
        setTimeout(() => window.location.reload(), 1000); // Recarrega após 1 segundo
    } catch (error) {
        console.error('Erro ao alterar status:', error);
        showNotification('Erro ao alterar status do quarto: ' + error.message, 'danger');
    }
}

async function viewMaintenance(roomId) {
    try {
        currentRoom = roomId;
        
        // Limpar conteúdo anterior e mostrar indicador de carregamento
        document.getElementById('maintenanceHistoryContent').innerHTML = `
            <div class="text-center py-5">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Carregando...</span>
                </div>
                <p class="mt-2">Carregando histórico de manutenção...</p>
            </div>
        `;
        
        // Mostrar o modal
        maintenanceModal.show();
        
        // Carregar histórico de manutenção
        const records = await apiRequest(`/rooms/${roomId}/maintenance/`, { method: 'GET' });
        
        if (records.length === 0) {
            document.getElementById('maintenanceHistoryContent').innerHTML = `
                <div class="text-center py-5">
                    <i class="fas fa-tools fa-2x text-muted mb-3"></i>
                    <p>Nenhum registro de manutenção encontrado para este quarto.</p>
                </div>
            `;
        } else {
            const recordsHtml = records.map(record => `
                <div class="card mb-3">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <span><i class="fas fa-calendar me-2"></i>${formatDate(record.date)}</span>
                        <span class="badge bg-${record.maintenance_type === 'emergency' ? 'danger' : 'info'}">
                            ${record.maintenance_type || 'regular'}
                        </span>
                    </div>
                    <div class="card-body">
                        <p class="card-text">${record.description}</p>
                        ${record.resolution ? `<p class="card-text text-muted"><strong>Resolução:</strong> ${record.resolution}</p>` : ''}
                    </div>
                </div>
            `).join('');
            
            document.getElementById('maintenanceHistoryContent').innerHTML = recordsHtml;
        }
    } catch (error) {
        console.error('Erro ao carregar histórico:', error);
        document.getElementById('maintenanceHistoryContent').innerHTML = `
            <div class="alert alert-danger" role="alert">
                <i class="fas fa-exclamation-triangle me-2"></i>
                Erro ao carregar histórico de manutenção: ${error.message}. Por favor, tente novamente.
            </div>
        `;
    }
}

function handleAddMaintenance() {
    // Função para adicionar novo registro de manutenção
    // Implementação pendente - pode ser feita criando um formulário dinâmico ou outro modal
    alert('Funcionalidade em desenvolvimento');
}

// Funções auxiliares
function formatDate(dateString) {
    const options = { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' };
    return new Date(dateString).toLocaleDateString('pt-BR', options);
}

function getCsrfToken() {
    const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    if (csrftoken) return csrftoken;
    
    const cookieValue = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1];
        
    return cookieValue || '';
}

function showNotification(message, type = 'info') {
    // Remover notificações anteriores do mesmo tipo
    document.querySelectorAll(`.notification-toast.alert-${type}`).forEach(el => {
        el.remove();
    });
    
    // Criar elemento de notificação
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show notification-toast`;
    notification.role = 'alert';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Fechar"></button>
    `;
    
    // Estilos
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        min-width: 300px;
        z-index: 9999;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    `;
    
    // Adicionar ao DOM
    document.body.appendChild(notification);
    
    // Auto-fechar após 5 segundos para mensagens que não são de erro
    if (type !== 'danger') {
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        }, 5000);
    }
}