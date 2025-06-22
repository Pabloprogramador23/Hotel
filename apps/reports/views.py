from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncDate
from datetime import date, timedelta, datetime
from decimal import Decimal
from apps.rooms.models import Room
from apps.checkin_checkout.models import CheckIn
from apps.reservations.models import Reservation
from apps.finance.models import Invoice, Expense, ExtraIncome
from .services import calculate_revenue_data, calculate_cash_flow_data, calculate_expense_data

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
    occupied_rooms = Room.objects.filter(status='occupied').count()
    occupancy_rate = (occupied_rooms / total_rooms * 100) if total_rooms > 0 else 0
    
    # Ocupação por tipo de quarto
    room_type_stats = (
        Room.objects.values('room_type')
        .annotate(
            total=Count('id'),
            occupied=Count('id', filter=Q(status='occupied'))
        )
        .order_by('room_type')
    )

    # Tendência de ocupação dos últimos 7 dias
    end_date = date.today()
    start_date = end_date - timedelta(days=6)
    occupancy_trend = []
    
    for single_date in (start_date + timedelta(n) for n in range(7)):
        checkins = CheckIn.objects.filter(check_in_time__date=single_date).count()
        occupancy_trend.append({
            'date': single_date,
            'checkins': checkins
        })
    
    context = {
        'total_rooms': total_rooms,
        'occupied_rooms': occupied_rooms,
        'occupancy_rate': round(occupancy_rate, 2),
        'room_type_stats': room_type_stats,
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
    checkins = CheckIn.objects.select_related('reservation').order_by('-check_in_time')
    
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
            pass  # Em caso de erro, mantém as datas padrão    # Obter dados de receita (incluindo receitas avulsas)
    revenue_data, total_revenue, total_paid, total_pending = calculate_revenue_data(start_date, end_date)
    
    # Obter entradas de receitas avulsas para o período (somente para exibição na tabela)
    extra_income_entries = ExtraIncome.objects.filter(
        received_date__gte=start_date,
        received_date__lte=end_date
    ).order_by('-received_date')
    
    # Obter dados de despesa
    expense_data, total_expense, category_expenses = calculate_expense_data(start_date, end_date)
    
    # Garantir que os valores sejam do mesmo tipo antes de operações
    if isinstance(total_revenue, Decimal):
        if not isinstance(total_expense, Decimal):
            total_expense = Decimal(str(total_expense))
    else:
        total_revenue = float(total_revenue)
        total_expense = float(total_expense)
    
    # Calcular lucro líquido
    net_profit = total_revenue - total_expense
    
    # Garantir que todos os valores sejam float para cálculos percentuais
    total_revenue_float = float(total_revenue)
    total_paid_float = float(total_paid)
    net_profit_float = float(net_profit)
    
    # Calcular margem de lucro (se houver receita)
    profit_margin = (net_profit_float / total_revenue_float * 100) if total_revenue_float > 0 else 0
    
    # Calcular percentual de pagamentos recebidos e pendentes
    payment_percentage = (total_paid_float / total_revenue_float * 100) if total_revenue_float > 0 else 0
    pending_percentage = (float(total_pending) / total_revenue_float * 100) if total_revenue_float > 0 else 0
    
    # Construir dados diários para o gráfico
    daily_data = []
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        
        # Encontrar receita deste dia
        day_revenue = next((item for item in revenue_data if item['date'].strftime('%Y-%m-%d') == date_str), None)
        
        # Encontrar despesa deste dia
        day_expense = next((item for item in expense_data if item['date'].strftime('%Y-%m-%d') == date_str), None)
        
        daily_data.append({
            'date': current_date,
            'revenue': float(day_revenue['total_amount']) if day_revenue else 0,
            'expense': float(day_expense['total_amount']) if day_expense else 0
        })
        
        current_date += timedelta(days=1)      # Obter entradas de receita (faturas) para o período
    revenue_entries = Invoice.objects.filter(
        issued_at__date__gte=start_date,
        issued_at__date__lte=end_date
    ).select_related('reservation', 'reservation__room').order_by('-issued_at')
    
    # Formatar dados de faturas para o template
    formatted_revenue_entries = []
    for invoice in revenue_entries:
        formatted_revenue_entries.append({
            'id': invoice.id,
            'date': invoice.issued_at.date(),
            'amount': float(invoice.amount),  # Converter para float para consistência
            'paid': invoice.paid,
            'guest_name': invoice.reservation.guest_name,
            'room_number': invoice.reservation.room.number if invoice.reservation.room else 'N/A',
            'type': 'Fatura de Reserva'
        })
        
    # Adicionar receitas avulsas aos dados formatados
    for income in extra_income_entries:
        formatted_revenue_entries.append({
            'id': income.id,
            'date': income.received_date,
            'amount': float(income.amount),
            'paid': True,  # Receitas avulsas são sempre consideras pagas
            'description': income.description,
            'method': income.method,
            'type': 'Receita Avulsa'
        })
    
    # Obter entradas de despesa para o período
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
    
    # Calcular ticket médio (valor médio das faturas)
    invoice_count = Invoice.objects.filter(
        issued_at__date__gte=start_date,
        issued_at__date__lte=end_date
    ).count()
    
    avg_invoice_value = total_revenue_float / invoice_count if invoice_count > 0 else 0
    
    # Obter faturas recentes para exibição na tabela
    recent_invoices = Invoice.objects.select_related('reservation').filter(
        issued_at__date__gte=start_date,
        issued_at__date__lte=end_date
    ).order_by('-issued_at')[:10]  # Limitar a 10 faturas mais recentes
    
    # Formatar dados de faturas para o template
    formatted_invoices = []
    for invoice in recent_invoices:
        formatted_invoices.append({
            'id': invoice.id,
            'date': invoice.issued_at.date(),
            'guest_name': invoice.reservation.guest_name if invoice.reservation else 'N/A',
            'amount': float(invoice.amount),
            'paid': invoice.paid,
        })
    
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
        'recent_invoices': formatted_invoices,
        'recent_expenses': recent_expenses,
        'category_expenses': category_expenses,
        'extra_income_total': float(extra_income_total),
        'recent_extra_incomes': formatted_extra_incomes
    }
    
    return render(request, 'reports/financial_consolidated.html', context)
