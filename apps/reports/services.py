from typing import Tuple, List, Dict, Any
from datetime import date, datetime
from django.db.models import Q, Sum
from django.db.models.functions import TruncDate
from apps.finance.models import Invoice, Expense

def calculate_revenue_data(start_date: date, end_date: date) -> Tuple[List[Dict[str, Any]], float, float, float]:
    """
    Calcula dados de receita agregada para o período informado.

    Args:
        start_date (date): Data inicial do período.
        end_date (date): Data final do período.

    Returns:
        Tuple[List[Dict[str, Any]], float, float, float]:
            - Lista de dicionários com dados agregados por dia.
            - Soma total de receita no período.
            - Soma total paga no período.
            - Soma total pendente no período.
    """
    query = Invoice.objects
    if start_date == end_date:
        query = query.filter(issued_at__date=start_date)
    else:
        query = query.filter(issued_at__date__gte=start_date, issued_at__date__lte=end_date)
    revenue_data = (
        query
        .values('issued_at__date')
        .annotate(
            date=TruncDate('issued_at'),
            total_amount=Sum('amount'),
            paid_amount=Sum('amount', filter=Q(paid=True)),
            pending_amount=Sum('amount', filter=Q(paid=False))
        )
        .order_by('issued_at__date')
    )
    total_revenue = sum(day['total_amount'] or 0 for day in revenue_data)
    total_paid = sum(day['paid_amount'] or 0 for day in revenue_data)
    total_pending = sum(day['pending_amount'] or 0 for day in revenue_data)
    return revenue_data, total_revenue, total_paid, total_pending

def calculate_expense_data(start_date: date, end_date: date) -> Tuple[List[Dict[str, Any]], float, Dict[str, float]]:
    """
    Calcula dados de despesas agregadas para o período informado.

    Args:
        start_date (date): Data inicial do período.
        end_date (date): Data final do período.

    Returns:
        Tuple[List[Dict[str, Any]], float, Dict[str, float]]:
            - Lista de dicionários com dados de despesas agregados por dia.
            - Soma total de despesas no período.
            - Dicionário com totais por categoria de despesa.
    """
    query = Expense.objects
    if start_date == end_date:
        query = query.filter(payment_date=start_date)
    else:
        query = query.filter(payment_date__gte=start_date, payment_date__lte=end_date)
    
    # Executar a consulta e armazenar os resultados em uma lista para evitar problemas com SQLite
    expense_data_raw = list(
        query
        .values('payment_date')
        .annotate(
            date=TruncDate('payment_date'),
            total_amount=Sum('amount')
        )
        .order_by('payment_date')
    )
    
    # Garantir que todos os valores de total_amount sejam válidos
    expense_data = []
    for item in expense_data_raw:
        # Converter None para 0 e garantir que temos um valor float
        if item['total_amount'] is None:
            item['total_amount'] = 0
        expense_data.append(item)
    
    # Total de despesas no período (com verificação de valores None)
    total_expense = sum(float(day['total_amount']) for day in expense_data)
    
    # Calcular total por categoria
    category_totals = {}
    for category_code, category_name in Expense.CATEGORY_CHOICES:
        category_amount = query.filter(category=category_code).aggregate(total=Sum('amount'))['total'] or 0
        if category_amount > 0:
            category_totals[category_code] = {
                'name': category_name,
                'amount': float(category_amount)
            }
    
    return expense_data, total_expense, category_totals

def calculate_cash_flow_data(start_date: date, end_date: date) -> Dict[str, Any]:
    """
    Calcula dados de fluxo de caixa para o período informado,
    integrando receitas e despesas.

    Args:
        start_date (date): Data inicial do período.
        end_date (date): Data final do período.
    
    Returns:
        Dict[str, Any]: Dicionário com todos os dados do fluxo de caixa.
    """
    # Obter dados de receita
    revenue_data, total_revenue, total_paid, total_pending = calculate_revenue_data(start_date, end_date)
    
    # Obter dados de despesa
    expense_data, total_expense, category_totals = calculate_expense_data(start_date, end_date)
    
    # Calcular lucro líquido
    net_profit = total_revenue - total_expense
    
    # Construir dados de fluxo de caixa diário
    daily_cash_flow = {}
    
    # Adicionar dados de receita ao fluxo diário
    for entry in revenue_data:
        day_str = entry['date'].strftime('%Y-%m-%d')
        if day_str not in daily_cash_flow:
            daily_cash_flow[day_str] = {
                'date': entry['date'],
                'revenue': 0,
                'expense': 0,
                'net': 0
            }
        daily_cash_flow[day_str]['revenue'] = float(entry['total_amount'] or 0)
    
    # Adicionar dados de despesa ao fluxo diário
    for entry in expense_data:
        day_str = entry['date'].strftime('%Y-%m-%d')
        if day_str not in daily_cash_flow:
            daily_cash_flow[day_str] = {
                'date': entry['date'],
                'revenue': 0,
                'expense': 0,
                'net': 0
            }
        daily_cash_flow[day_str]['expense'] = float(entry['total_amount'] or 0)
    
    # Calcular lucro líquido diário
    for day in daily_cash_flow.values():
        day['net'] = day['revenue'] - day['expense']
    
    # Ordenar por data
    sorted_cash_flow = [v for k, v in sorted(daily_cash_flow.items())]
    
    return {
        'daily_flow': sorted_cash_flow,
        'total_revenue': total_revenue,
        'total_paid': total_paid,
        'total_pending': total_pending,
        'total_expense': total_expense,
        'category_expenses': category_totals,
        'net_profit': net_profit
    }
