// Manipulação do modal de quarto
function openAddRoomModal() {
    const modal = document.getElementById('roomModal');
    modal.style.display = 'flex';
    
    // Preenche o modal com o formulário
    modal.innerHTML = `
        <div class="modal-content">
            <button class="modal-close" onclick="closeModal('roomModal')">&times;</button>
            <h3>Novo Quarto</h3>
            <form id="roomForm" onsubmit="handleRoomSubmit(event)">
                <div class="form-group">
                    <label for="number">Número do Quarto</label>
                    <input type="text" id="number" name="number" required>
                </div>
                <div class="form-group">
                    <label for="room_type">Tipo</label>
                    <select id="room_type" name="room_type" required>
                        <option value="single">Single</option>
                        <option value="double">Double</option>
                        <option value="suite">Suite</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="description">Descrição</label>
                    <textarea id="description" name="description"></textarea>
                </div>
                <div class="modal-actions">
                    <button type="button" onclick="closeModal('roomModal')">Cancelar</button>
                    <button type="submit">Salvar</button>
                </div>
            </form>
        </div>
    `;
}

// Manipula o envio do formulário de quarto
async function handleRoomSubmit(event) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);
    
    const errors = validateForm(formData);
    if (errors.length > 0) {
        showNotification(errors.join('\n'), 'error');
        return;
    }
    
    try {
        const data = Object.fromEntries(formData.entries());
        await fetchApi('/api/rooms/', {
            method: 'POST',
            body: JSON.stringify(data)
        });
        
        showNotification('Quarto criado com sucesso!', 'success');
        closeModal('roomModal');
        location.reload();
    } catch (error) {
        console.error('Erro ao criar quarto:', error);
    }
}

// Função para editar um quarto
function editRoom(roomId) {
    openAddRoomModal(); // Reutiliza o modal de adicionar
    
    // Carrega os dados do quarto
    fetchApi(`/api/rooms/${roomId}/`).then(room => {
        document.getElementById('number').value = room.number;
        document.getElementById('room_type').value = room.room_type;
        document.getElementById('description').value = room.description || '';
        
        // Atualiza o formulário para modo de edição
        const form = document.getElementById('roomForm');
        form.onsubmit = (e) => handleRoomEdit(e, roomId);
    });
}

// Manipula a edição de um quarto
async function handleRoomEdit(event, roomId) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);
    
    try {
        const data = Object.fromEntries(formData.entries());
        await fetchApi(`/api/rooms/${roomId}/`, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
        
        showNotification('Quarto atualizado com sucesso!', 'success');
        closeModal('roomModal');
        location.reload();
    } catch (error) {
        console.error('Erro ao atualizar quarto:', error);
    }
}

// Função para mudar o status de um quarto
async function changeStatus(roomId) {
    try {
        const response = await fetchApi(`/api/rooms/${roomId}/change-status/`, {
            method: 'POST'
        });
        
        if (response.success) {
            showNotification('Status atualizado com sucesso!', 'success');
            location.reload();
        }
    } catch (error) {
        console.error('Erro ao mudar status:', error);
    }
}

// Função para visualizar histórico de manutenção
function viewMaintenance(roomId) {
    const modal = document.getElementById('maintenanceModal');
    modal.style.display = 'flex';
    
    fetchApi(`/api/rooms/${roomId}/maintenance/`).then(records => {
        modal.innerHTML = `
            <div class="modal-content">
                <button class="modal-close" onclick="closeModal('maintenanceModal')">&times;</button>
                <h3>Histórico de Manutenção</h3>
                <div class="maintenance-list">
                    ${records.map(record => `
                        <div class="maintenance-item">
                            <p><strong>Data:</strong> ${formatDate(record.date)}</p>
                            <p><strong>Descrição:</strong> ${record.description}</p>
                        </div>
                    `).join('')}
                </div>
                <button onclick="addMaintenance(${roomId})">Adicionar Registro</button>
            </div>
        `;
    });
}

// Inicialização dos filtros
document.addEventListener('DOMContentLoaded', () => {
    const typeFilter = document.getElementById('room-type-filter');
    const statusFilter = document.getElementById('status-filter');
    
    [typeFilter, statusFilter].forEach(filter => {
        filter.addEventListener('change', () => {
            const params = new URLSearchParams({
                type: typeFilter.value,
                status: statusFilter.value
            });
            
            window.location.href = `?${params.toString()}`;
        });
    });
});