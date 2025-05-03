from typing import Tuple, List, Dict, Any
from datetime import date, datetime
from decimal import Decimal
from django.db.models import Q, Sum
from django.db.models.functions import TruncDate
from django.db import connection
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
    
    # Verificar se estamos usando SQLite
    is_sqlite = connection.vendor == 'sqlite'
    
    if is_sqlite:
        # Abordagem compatível com SQLite: buscar dados e agrupá-los em Python
        invoices = list(query.values('issued_at', 'amount', 'paid'))
        
        # Agrupar por data e calcular totais manualmente
        revenue_by_date = {}
        for invoice in invoices:
            date_value = invoice['issued_at'].date()  # Extrair apenas a data
            date_str = date_value.strftime('%Y-%m-%d')
            
            if date_str not in revenue_by_date:
                revenue_by_date[date_str] = {
                    'issued_at__date': date_value,
                    'date': date_value,
                    'total_amount': 0,
                    'paid_amount': 0,
                    'pending_amount': 0
                }
            
            # Somar valores
            amount = invoice['amount']
            revenue_by_date[date_str]['total_amount'] += amount
            
            if invoice['paid']:
                revenue_by_date[date_str]['paid_amount'] += amount
            else:
                revenue_by_date[date_str]['pending_amount'] += amount
        
        # Converter para lista
        revenue_data = list(revenue_by_date.values())
        revenue_data.sort(key=lambda x: x['date'])
    else:
        # Para outros bancos de dados, usar a consulta original
        revenue_data = list(
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
    
    # Verificar se estamos usando SQLite
    is_sqlite = connection.vendor == 'sqlite'
    
    if is_sqlite:
        # Abordagem compatível com SQLite: buscar os dados e agrupá-los em Python
        expenses = list(query.values('payment_date', 'amount'))
        
        # Agrupar por data e somar os valores manualmente
        expense_by_date = {}
        for expense in expenses:
            date_str = expense['payment_date'].strftime('%Y-%m-%d')
            if date_str not in expense_by_date:
                expense_by_date[date_str] = {
                    'payment_date': expense['payment_date'], 
                    'date': expense['payment_date'],
                    'total_amount': 0
                }
            expense_by_date[date_str]['total_amount'] += expense['amount']
        
        # Converter para lista
        expense_data = list(expense_by_date.values())
        expense_data.sort(key=lambda x: x['payment_date'])
    else:
        # Para outros bancos de dados, usar a consulta original
        expense_data = list(
            query
            .values('payment_date')
            .annotate(
                date=TruncDate('payment_date'),
                total_amount=Sum('amount')
            )
            .order_by('payment_date')
        )
    
    # Garantir que todos os valores de total_amount sejam válidos
    for item in expense_data:
        if item['total_amount'] is None:
            item['total_amount'] = 0
    
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
    
    # Converter para Decimal para garantir tipos compatíveis
    if isinstance(total_revenue, Decimal):
        total_expense = Decimal(str(total_expense)) if not isinstance(total_expense, Decimal) else total_expense
    else:
        total_revenue = Decimal(str(total_revenue)) if not isinstance(total_revenue, Decimal) else total_revenue
        total_expense = Decimal(str(total_expense)) if not isinstance(total_expense, Decimal) else total_expense
    
    # Calcular lucro líquido
    net_profit = total_revenue - total_expense
    
    # Construir dados de fluxo de caixa diário
    daily_cash_flow = {}
    
    # Adicionar dados de receita ao fluxo diário
    for entry in revenue_data:
        # Garantir que estamos usando o objeto date corretamente
        date_obj = entry['date']
        day_str = date_obj.strftime('%Y-%m-%d')
        
        if day_str not in daily_cash_flow:
            daily_cash_flow[day_str] = {
                'date': date_obj,
                'revenue': 0,
                'expense': 0,
                'net': 0
            }
        daily_cash_flow[day_str]['revenue'] = float(entry['total_amount'] or 0)
    
    # Adicionar dados de despesa ao fluxo diário
    for entry in expense_data:
        # Garantir que estamos usando o objeto date corretamente
        date_obj = entry['date']
        day_str = date_obj.strftime('%Y-%m-%d')
        
        if day_str not in daily_cash_flow:
            daily_cash_flow[day_str] = {
                'date': date_obj,
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
        'total_revenue': float(total_revenue),  # Converter para float para serialização JSON
        'total_paid': float(total_paid) if isinstance(total_paid, Decimal) else float(total_paid or 0),
        'total_pending': float(total_pending) if isinstance(total_pending, Decimal) else float(total_pending or 0),
        'total_expense': float(total_expense),  # Converter para float para serialização JSON
        'category_expenses': category_totals,
        'net_profit': float(net_profit),  # Converter para float para serialização JSON
    }
