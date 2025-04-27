// Manipulação do modal de reserva
function openAddReservationModal() {
    const modal = document.getElementById('reservationModal');
    modal.style.display = 'flex';
    
    // Preenche o modal com o formulário
    modal.innerHTML = `
        <div class="modal-content">
            <button class="modal-close" onclick="closeModal('reservationModal')">&times;</button>
            <h3>Nova Reserva</h3>
            <form id="reservationForm" onsubmit="handleReservationSubmit(event)">
                <div class="form-group">
                    <label for="guest_name">Nome do Hóspede</label>
                    <input type="text" id="guest_name" name="guest_name" required>
                </div>
                <div class="form-group">
                    <label for="room">Quarto</label>
                    <select id="room" name="room" required>
                        <!-- Será preenchido via AJAX -->
                    </select>
                </div>
                <div class="form-group">
                    <label for="check_in_date">Data de Check-in</label>
                    <input type="date" id="check_in_date" name="check_in_date" required>
                </div>
                <div class="form-group">
                    <label for="check_out_date">Data de Check-out</label>
                    <input type="date" id="check_out_date" name="check_out_date" required>
                </div>
                <div class="modal-actions">
                    <button type="button" onclick="closeModal('reservationModal')">Cancelar</button>
                    <button type="submit">Salvar</button>
                </div>
            </form>
        </div>
    `;
    
    // Carrega a lista de quartos disponíveis
    loadAvailableRooms();
}

// Fecha qualquer modal
function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

// Carrega quartos disponíveis via AJAX
async function loadAvailableRooms() {
    try {
        const rooms = await fetchApi('/api/rooms/available/');
        const select = document.getElementById('room');
        
        rooms.forEach(room => {
            const option = document.createElement('option');
            option.value = room.id;
            option.textContent = `Quarto ${room.number} (${room.room_type})`;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Erro ao carregar quartos:', error);
    }
}

// Manipula o envio do formulário de reserva
async function handleReservationSubmit(event) {
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
        await fetchApi('/api/reservations/', {
            method: 'POST',
            body: JSON.stringify(data)
        });
        
        showNotification('Reserva criada com sucesso!', 'success');
        closeModal('reservationModal');
        location.reload(); // Recarrega a página para mostrar a nova reserva
    } catch (error) {
        console.error('Erro ao criar reserva:', error);
    }
}

// Função para mudar o status de uma reserva
async function changeStatus(reservationId) {
    try {
        const response = await fetchApi(`/api/reservations/${reservationId}/change-status/`, {
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

// Funções para check-in e check-out
async function doCheckIn(reservationId) {
    try {
        const response = await fetchApi(`/api/reservations/${reservationId}/check-in/`, {
            method: 'POST'
        });
        
        if (response.success) {
            showNotification('Check-in realizado com sucesso!', 'success');
            location.reload();
        }
    } catch (error) {
        console.error('Erro no check-in:', error);
    }
}

async function doCheckOut(reservationId) {
    try {
        const response = await fetchApi(`/api/reservations/${reservationId}/check-out/`, {
            method: 'POST'
        });
        
        if (response.success) {
            showNotification('Check-out realizado com sucesso!', 'success');
            location.reload();
        }
    } catch (error) {
        console.error('Erro no check-out:', error);
    }
}

// Inicialização dos filtros
document.addEventListener('DOMContentLoaded', () => {
    const dateFilter = document.getElementById('date-filter');
    const statusFilter = document.getElementById('status-filter');
    const guestFilter = document.getElementById('guest-filter');
    
    [dateFilter, statusFilter, guestFilter].forEach(filter => {
        filter.addEventListener('change', () => {
            const params = new URLSearchParams({
                date: dateFilter.value,
                status: statusFilter.value,
                guest: guestFilter.value
            });
            
            window.location.href = `?${params.toString()}`;
        });
    });
});