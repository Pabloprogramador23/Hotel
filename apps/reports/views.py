from datetime import date, datetime, timedelta
from decimal import Decimal

from django.db.models import Count, Sum
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from apps.finance.models import Expense, ExtraIncome, LedgerAdjustment
from apps.reservations.models import Reservation, ReservationGuest, Room

from .services import calculate_cash_flow_data, calculate_expense_data, calculate_revenue_data

def report_list(request: HttpRequest) -> HttpResponse:
    """
    Exibe a lista de relatórios disponíveis.

    Args:
        request (HttpRequest): Requisição HTTP.

    Returns:
        HttpResponse: Página com links para relatórios.
    """
    return render(request, 'reports/list.html', {
        'title': 'Reports',
        'reports': [
            {'name': 'Occupancy Report', 'url': 'reports:occupancy'},
            {'name': 'Revenue Report', 'url': 'reports:revenue'},
            {'name': 'Check-ins Report', 'url': 'reports:checkins'},
            {'name': 'Cash Flow Report', 'url': 'reports:cash_flow'},
            {'name': 'Relatório Financeiro Detalhado', 'url': 'reports:financial_report'},
        ]
    })

def occupancy_report(request: HttpRequest) -> HttpResponse:
    """
    Gera o relatório de ocupação do hotel.

    Args:
        request (HttpRequest): Requisição HTTP.

    Returns:
        HttpResponse: Página com estatísticas de ocupação.
    """
    # Cálculos básicos de ocupação
    total_rooms = Room.objects.count()
    occupied_rooms = Room.objects.filter(status=Room.Status.OCUPADO).count()
    occupancy_rate = (occupied_rooms / total_rooms * 100) if total_rooms > 0 else 0

    status_stats = []
    for value, label in Room.Status.choices:
        count = Room.objects.filter(status=value).count()
        status_stats.append({
            'status': label,
            'total': count,
            'percentage': round((count / total_rooms * 100), 2) if total_rooms else 0,
        })

    # Tendência de ocupação dos últimos 7 dias
    end_date = date.today()
    start_date = end_date - timedelta(days=6)
    occupancy_trend = []
    
    for single_date in (start_date + timedelta(n) for n in range(7)):
        checkins = Reservation.objects.filter(data_entrada__date=single_date).count()
        occupancy_trend.append({
            'date': single_date,
            'checkins': checkins
        })
    
    context = {
        'total_rooms': total_rooms,
        'occupied_rooms': occupied_rooms,
        'occupancy_rate': round(occupancy_rate, 2),
        'status_stats': status_stats,
        'occupancy_trend': occupancy_trend
    }
    return render(request, 'reports/occupancy.html', context)

def revenue_report(request: HttpRequest) -> HttpResponse:
    """
    Gera o relatório de receita do hotel para um período.

    Args:
        request (HttpRequest): Requisição HTTP.

    Returns:
        HttpResponse: Página com dados de receita agregada.
    """
    today = date.today()
    start_date = today
    end_date = today
    if all(param in request.GET for param in ['start_date', 'end_date']):
        try:
            start_date = datetime.strptime(request.GET['start_date'], '%Y-%m-%d').date()
            end_date = datetime.strptime(request.GET['end_date'], '%Y-%m-%d').date()
        except (TypeError, ValueError):
            pass
    revenue_data, total_revenue, total_paid, total_pending = calculate_revenue_data(start_date, end_date)
    context = {
        'start_date': start_date,
        'end_date': end_date,
        'revenue_data': revenue_data,
        'total_revenue': total_revenue,
        'total_paid': total_paid,
        'total_pending': total_pending
    }
    return render(request, 'reports/revenue.html', context)

def checkins_report(request: HttpRequest) -> HttpResponse:
    """
    Gera o relatório de check-ins realizados.

    Args:
        request (HttpRequest): Requisição HTTP.

    Returns:
        HttpResponse: Página com lista de check-ins.
    """
    checkins = Reservation.objects.select_related('room').prefetch_related('hospedes').order_by('-data_entrada')

    context = {
        'checkins': checkins
    }
    return render(request, 'reports/checkins.html', context)

def cash_flow_report(request: HttpRequest) -> HttpResponse:
    """
    Gera o relatório de fluxo de caixa do hotel, integrando receitas e despesas.

    Args:
        request (HttpRequest): Requisição HTTP.

    Returns:
        HttpResponse: Página com dados de fluxo de caixa.
    """
    today = date.today()
    start_date = today - timedelta(days=30)  # Padrão: últimos 30 dias
    end_date = today
    
    if all(param in request.GET for param in ['start_date', 'end_date']):
        try:
            start_date = datetime.strptime(request.GET['start_date'], '%Y-%m-%d').date()
            end_date = datetime.strptime(request.GET['end_date'], '%Y-%m-%d').date()
        except (TypeError, ValueError):
            pass
    
    cash_flow_data = calculate_cash_flow_data(start_date, end_date)
    
    # Calcular percentual de pagamentos recebidos e pendentes
    total_revenue = cash_flow_data['total_revenue']
    total_paid = cash_flow_data['total_paid']
    total_pending = cash_flow_data['total_pending']
    
    # Calcular percentuais para a barra de progresso
    paid_percentage = round((total_paid / total_revenue * 100) if total_revenue > 0 else 0)
    pending_percentage = round((total_pending / total_revenue * 100) if total_revenue > 0 else 0)
    
    context = {
        'start_date': start_date,
        'end_date': end_date,
        'cash_flow_data': cash_flow_data,
        'daily_flow': cash_flow_data['daily_flow'],
        'total_revenue': cash_flow_data['total_revenue'],
        'total_paid': cash_flow_data['total_paid'],
        'total_pending': cash_flow_data['total_pending'],
        'total_expense': cash_flow_data['total_expense'],
        'category_expenses': cash_flow_data['category_expenses'],
        'net_profit': cash_flow_data['net_profit'],
        'paid_percentage': paid_percentage,
        'pending_percentage': pending_percentage,
    }
    
    return render(request, 'reports/cash_flow.html', context)

def financial_report(request: HttpRequest) -> HttpResponse:
    """
    Gera um relatório financeiro completo, mostrando todas as receitas e despesas do hotel
    para um determinado período.

    Args:
        request (HttpRequest): Requisição HTTP com possíveis parâmetros de filtro.

    Returns:
        HttpResponse: Página de relatório financeiro detalhado.
    """
    # Define o período padrão: último mês até hoje
    today = date.today()
    default_start_date = today - timedelta(days=30)
    
    # Verifica se há parâmetros de filtro de data na requisição
    start_date = default_start_date
    end_date = today
    
    if all(param in request.GET for param in ['start_date', 'end_date']):
        try:
            start_date = datetime.strptime(request.GET['start_date'], '%Y-%m-%d').date()
            end_date = datetime.strptime(request.GET['end_date'], '%Y-%m-%d').date()
        except (ValueError, TypeError):
            pass

    revenue_data, total_revenue, total_paid, total_pending = calculate_revenue_data(start_date, end_date)
    extra_income_entries = ExtraIncome.objects.filter(
        received_date__gte=start_date,
        received_date__lte=end_date
    ).order_by('-received_date')
    expense_data, total_expense, category_expenses = calculate_expense_data(start_date, end_date)

    total_revenue = float(total_revenue)
    total_expense = float(total_expense)
    net_profit = total_revenue - total_expense

    profit_margin = (net_profit / total_revenue * 100) if total_revenue > 0 else 0
    payment_percentage = (total_paid / total_revenue * 100) if total_revenue > 0 else 0
    pending_percentage = (total_pending / total_revenue * 100) if total_revenue > 0 else 0

    daily_data = []
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        day_revenue = next((item for item in revenue_data if item['date'].strftime('%Y-%m-%d') == date_str), None)
        day_expense = next((item for item in expense_data if item['date'].strftime('%Y-%m-%d') == date_str), None)

        daily_data.append({
            'date': current_date,
            'revenue': float(day_revenue['total_amount']) if day_revenue else 0,
            'expense': float(day_expense['total_amount']) if day_expense else 0
        })
        current_date += timedelta(days=1)

    guest_entries = ReservationGuest.objects.filter(
        criado_em__date__gte=start_date,
        criado_em__date__lte=end_date
    ).select_related('reserva__room').order_by('-criado_em')

    formatted_revenue_entries = []
    for guest in guest_entries:
        formatted_revenue_entries.append({
            'id': guest.id,
            'date': guest.criado_em.date(),
            'amount': float(guest.valor_devido),
            'paid': guest.pago,
            'guest_name': guest.nome,
            'room_number': guest.reserva.room.numero if guest.reserva.room else 'N/A',
            'type': 'Reserva',
        })

    for income in extra_income_entries:
        formatted_revenue_entries.append({
            'id': income.id,
            'date': income.received_date,
            'amount': float(income.amount),
            'paid': True,
            'description': income.description,
            'method': income.method,
            'type': 'Receita Avulsa'
        })

    credit_adjustments = LedgerAdjustment.objects.filter(
        tipo=LedgerAdjustment.Tipo.CREDITO,
        criado_em__date__gte=start_date,
        criado_em__date__lte=end_date,
    ).order_by('-criado_em')

    for ajuste in credit_adjustments:
        formatted_revenue_entries.append({
            'id': ajuste.id,
            'date': ajuste.criado_em.date(),
            'amount': float(ajuste.valor),
            'paid': True,
            'description': ajuste.descricao,
            'method': ajuste.metodo,
            'type': 'Ajuste Financeiro'
        })

    formatted_revenue_entries.sort(key=lambda entry: entry['date'], reverse=True)

    expense_entries = Expense.objects.filter(
        payment_date__gte=start_date,
        payment_date__lte=end_date
    ).order_by('-payment_date')
    
    # Preparar o contexto
    context = {
        'start_date': start_date,
        'end_date': end_date,
        'total_revenue': float(total_revenue),  # Converter para float para o template
        'total_expense': float(total_expense),
        'total_paid': float(total_paid),
        'total_pending': float(total_pending),
        'net_profit': float(net_profit),
        'profit_margin': profit_margin,
        'payment_percentage': payment_percentage,
        'pending_percentage': pending_percentage,
        'daily_data': daily_data,
        'revenue_entries': formatted_revenue_entries,
        'expense_entries': expense_entries,
        'category_expenses': category_expenses
    }
    
    return render(request, 'reports/financial_report.html', context)

def financial_consolidated_report(request: HttpRequest) -> HttpResponse:
    """
    Gera um relatório financeiro consolidado que compara receitas ganhas e recebidas,
    para fornecer uma visão clara da saúde financeira e lucratividade do hotel.

    Args:
        request (HttpRequest): Requisição HTTP com possíveis parâmetros de filtro de data.

    Returns:
        HttpResponse: Página de relatório financeiro consolidado.
    """
    # Define o período padrão: último mês até hoje
    today = date.today()
    default_start_date = today - timedelta(days=30)
    
    # Verifica se há parâmetros de filtro de data na requisição
    start_date = default_start_date
    end_date = today
    
    if all(param in request.GET for param in ['start_date', 'end_date']):
        try:
            start_date = datetime.strptime(request.GET['start_date'], '%Y-%m-%d').date()
            end_date = datetime.strptime(request.GET['end_date'], '%Y-%m-%d').date()
        except (ValueError, TypeError):
            pass    # Obter dados de receita usando o serviço existente (já inclui receitas avulsas)
    revenue_data, total_revenue, revenue_received, revenue_pending = calculate_revenue_data(start_date, end_date)
    
    # Obter receitas avulsas para o período (para exibição na tabela)
    extra_income_entries = ExtraIncome.objects.filter(
        received_date__gte=start_date,
        received_date__lte=end_date
    )
    extra_income_total = extra_income_entries.aggregate(total=Sum('amount'))['total'] or 0
    
    # Obter dados de despesa usando o serviço existente
    expense_data, total_expenses, category_expenses = calculate_expense_data(start_date, end_date)
    
    # Garantir que os valores sejam do mesmo tipo antes de operações
    if isinstance(revenue_received, Decimal):
        if not isinstance(total_expenses, Decimal):
            total_expenses = Decimal(str(total_expenses))
    else:
        revenue_received = float(revenue_received)
        total_expenses = float(total_expenses)
    
    # Calcular lucro líquido
    net_profit = revenue_received - total_expenses  # Usamos apenas a receita efetivamente recebida
    
    # Converter para float para cálculos percentuais
    total_revenue_float = float(total_revenue)
    revenue_received_float = float(revenue_received)
    revenue_pending_float = float(revenue_pending)
    total_expenses_float = float(total_expenses)
    net_profit_float = float(net_profit)
    
    # Calcular percentuais
    percentage_received = (revenue_received_float / total_revenue_float * 100) if total_revenue_float > 0 else 0
    percentage_pending = (revenue_pending_float / total_revenue_float * 100) if total_revenue_float > 0 else 0
    profit_margin = (net_profit_float / revenue_received_float * 100) if revenue_received_float > 0 else 0
    expense_to_revenue_ratio = (total_expenses_float / revenue_received_float * 100) if revenue_received_float > 0 else 0
    
    # Construir dados diários para análise detalhada e gráficos
    daily_data = []
    date_range = (end_date - start_date).days + 1
    
    # Mapear dados de receita por data
    revenue_by_date = {item['date'].strftime('%Y-%m-%d'): {
        'total': float(item['total_amount'] or 0),
        'paid': float(item['paid_amount'] or 0),
        'pending': float(item['pending_amount'] or 0)
    } for item in revenue_data}
    
    # Mapear dados de despesa por data
    expense_by_date = {item['date'].strftime('%Y-%m-%d'): float(item['total_amount'] or 0) 
                      for item in expense_data}
    
    # Construir dataset completo com todos os dias no período
    for i in range(date_range):
        current_date = start_date + timedelta(days=i)
        date_str = current_date.strftime('%Y-%m-%d')
        
        # Obter dados de receita para este dia (ou zeros se não houver)
        day_revenue = revenue_by_date.get(date_str, {'total': 0, 'paid': 0, 'pending': 0})
        
        # Obter dados de despesa para este dia (ou zero se não houver)
        day_expense = expense_by_date.get(date_str, 0)
        
        # Calcular lucro do dia (usando apenas receita recebida)
        day_profit = day_revenue['paid'] - day_expense
        
        # Calcular margem de lucro do dia
        day_margin = (day_profit / day_revenue['paid'] * 100) if day_revenue['paid'] > 0 else 0
        
        daily_data.append({
            'date': current_date,
            'revenue': day_revenue['total'],
            'revenue_paid': day_revenue['paid'],
            'revenue_pending': day_revenue['pending'],
            'expense': day_expense,
            'profit': day_profit,
            'margin': day_margin
        })
    
    # Ordenar dados por data
    daily_data.sort(key=lambda x: x['date'])

    guest_charges = ReservationGuest.objects.filter(
        criado_em__date__gte=start_date,
        criado_em__date__lte=end_date
    )

    ticket_count = guest_charges.count()
    avg_invoice_value = total_revenue_float / ticket_count if ticket_count > 0 else 0

    recent_guest_entries = guest_charges.order_by('-criado_em')[:10]
    recent_revenues = [{
        'id': guest.id,
        'date': guest.criado_em.date(),
        'guest_name': guest.nome,
        'amount': float(guest.valor_devido),
        'paid': guest.pago,
    } for guest in recent_guest_entries]
    
    # Obter despesas recentes para exibição na tabela
    recent_expenses = Expense.objects.filter(
        payment_date__gte=start_date,
        payment_date__lte=end_date
    ).order_by('-payment_date')[:10]  # Limitar a 10 despesas mais recentes
      # Obter receitas avulsas recentes
    recent_extra_incomes = ExtraIncome.objects.filter(
        received_date__gte=start_date,
        received_date__lte=end_date
    ).order_by('-received_date')[:10]
    
    # Formatar receitas avulsas para exibição
    formatted_extra_incomes = []
    for income in recent_extra_incomes:
        formatted_extra_incomes.append({
            'id': income.id,
            'date': income.received_date,
            'description': income.description,
            'amount': float(income.amount),
            'method': income.method
        })
    
    # Preparar o contexto para o template
    context = {
        'start_date': start_date,
        'end_date': end_date,
        'total_revenue': float(total_revenue),
        'revenue_received': float(revenue_received),
        'revenue_pending': float(revenue_pending),
        'total_expenses': float(total_expenses),
        'net_profit': float(net_profit),
        'profit_margin': profit_margin,
        'percentage_received': percentage_received,
        'percentage_pending': percentage_pending,
        'expense_to_revenue_ratio': expense_to_revenue_ratio,
        'avg_invoice_value': avg_invoice_value,
        'daily_data': daily_data,
        'recent_revenues': recent_revenues,
        'recent_expenses': recent_expenses,
        'category_expenses': category_expenses,
        'extra_income_total': float(extra_income_total),
        'recent_extra_incomes': formatted_extra_incomes
    }
    
    if request.headers.get('HX-Request'):
        return render(request, 'reports/partials/financial_modal.html', context)
        
    return render(request, 'reports/financial_consolidated.html', context)
