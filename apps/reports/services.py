from typing import Tuple, List, Dict, Any
from datetime import date
from decimal import Decimal

from django.db import connection
from django.db.models import Q, Sum
from django.db.models.functions import TruncDate

from apps.finance.models import Expense, ExtraIncome, LedgerAdjustment
from apps.reservations.models import ReservationGuest


def _normalize_decimal(value) -> Decimal:
    if value is None:
        return Decimal('0')
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _date_key(target_date) -> str:
    return target_date.strftime('%Y-%m-%d')


def calculate_revenue_data(start_date: date, end_date: date) -> Tuple[List[Dict[str, Any]], float, float, float]:
    query = ReservationGuest.objects.select_related('reserva')
    if start_date == end_date:
        query = query.filter(criado_em__date=start_date)
    else:
        query = query.filter(criado_em__date__gte=start_date, criado_em__date__lte=end_date)

    is_sqlite = connection.vendor == 'sqlite'
    revenue_by_date: Dict[str, Dict[str, Any]] = {}

    if is_sqlite:
        charges = list(query.values('criado_em', 'valor_devido', 'pago'))
        for charge in charges:
            date_value = charge['criado_em'].date()
            key = _date_key(date_value)
            revenue_by_date.setdefault(key, {
                'date': date_value,
                'total_amount': Decimal('0'),
                'paid_amount': Decimal('0'),
                'pending_amount': Decimal('0'),
            })
            amount = _normalize_decimal(charge['valor_devido'])
            revenue_by_date[key]['total_amount'] += amount
            if charge['pago']:
                revenue_by_date[key]['paid_amount'] += amount
            else:
                revenue_by_date[key]['pending_amount'] += amount
    else:
        aggregated = query.annotate(date=TruncDate('criado_em')).values('date').annotate(
            total_amount=Sum('valor_devido'),
            paid_amount=Sum('valor_devido', filter=Q(pago=True)),
            pending_amount=Sum('valor_devido', filter=Q(pago=False)),
        ).order_by('date')

        for row in aggregated:
            date_value = row['date']
            key = _date_key(date_value)
            revenue_by_date[key] = {
                'date': date_value,
                'total_amount': _normalize_decimal(row['total_amount']),
                'paid_amount': _normalize_decimal(row['paid_amount']),
                'pending_amount': _normalize_decimal(row['pending_amount']),
            }

    extra_income_query = ExtraIncome.objects
    if start_date == end_date:
        extra_income_query = extra_income_query.filter(received_date=start_date)
    else:
        extra_income_query = extra_income_query.filter(received_date__gte=start_date, received_date__lte=end_date)

    for income in extra_income_query.values('received_date', 'amount'):
        date_value = income['received_date']
        key = _date_key(date_value)
        revenue_by_date.setdefault(key, {
            'date': date_value,
            'total_amount': Decimal('0'),
            'paid_amount': Decimal('0'),
            'pending_amount': Decimal('0'),
        })
        amount = _normalize_decimal(income['amount'])
        revenue_by_date[key]['total_amount'] += amount
        revenue_by_date[key]['paid_amount'] += amount

    credit_adjustments = LedgerAdjustment.objects.filter(tipo=LedgerAdjustment.Tipo.CREDITO)
    if start_date == end_date:
        credit_adjustments = credit_adjustments.filter(criado_em__date=start_date)
    else:
        credit_adjustments = credit_adjustments.filter(criado_em__date__gte=start_date, criado_em__date__lte=end_date)

    for ajuste in credit_adjustments.values('criado_em', 'valor'):
        date_value = ajuste['criado_em'].date()
        key = _date_key(date_value)
        revenue_by_date.setdefault(key, {
            'date': date_value,
            'total_amount': Decimal('0'),
            'paid_amount': Decimal('0'),
            'pending_amount': Decimal('0'),
        })
        valor = _normalize_decimal(ajuste['valor'])
        revenue_by_date[key]['total_amount'] += valor
        revenue_by_date[key]['paid_amount'] += valor

    revenue_data = [value for _, value in sorted(revenue_by_date.items())]

    total_revenue = sum(item['total_amount'] for item in revenue_data)
    total_paid = sum(item['paid_amount'] for item in revenue_data)
    total_pending = sum(item['pending_amount'] for item in revenue_data)

    return revenue_data, float(total_revenue), float(total_paid), float(total_pending)


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

    is_sqlite = connection.vendor == 'sqlite'
    expense_by_date: Dict[str, Dict[str, Any]] = {}

    if is_sqlite:
        expenses = list(query.values('payment_date', 'amount'))
        for expense in expenses:
            date_value = expense['payment_date']
            key = _date_key(date_value)
            expense_by_date.setdefault(key, {
                'date': date_value,
                'total_amount': Decimal('0'),
            })
            expense_by_date[key]['total_amount'] += _normalize_decimal(expense['amount'])
    else:
        aggregated = query.annotate(date=TruncDate('payment_date')).values('date').annotate(
            total_amount=Sum('amount')
        ).order_by('date')
        for row in aggregated:
            date_value = row['date']
            key = _date_key(date_value)
            expense_by_date[key] = {
                'date': date_value,
                'total_amount': _normalize_decimal(row['total_amount']),
            }

    debit_adjustments = LedgerAdjustment.objects.filter(tipo=LedgerAdjustment.Tipo.DEBITO)
    if start_date == end_date:
        debit_adjustments = debit_adjustments.filter(criado_em__date=start_date)
    else:
        debit_adjustments = debit_adjustments.filter(criado_em__date__gte=start_date, criado_em__date__lte=end_date)

    for ajuste in debit_adjustments.values('criado_em', 'valor'):
        date_value = ajuste['criado_em'].date()
        key = _date_key(date_value)
        expense_by_date.setdefault(key, {
            'date': date_value,
            'total_amount': Decimal('0'),
        })
        expense_by_date[key]['total_amount'] += _normalize_decimal(ajuste['valor'])

    expense_data = [value for _, value in sorted(expense_by_date.items())]

    total_expense = sum(item['total_amount'] for item in expense_data)

    category_totals = {}
    for category_code, category_name in Expense.CATEGORY_CHOICES:
        category_amount = query.filter(category=category_code).aggregate(total=Sum('amount'))['total'] or 0
        if category_amount:
            category_totals[category_code] = {
                'name': category_name,
                'amount': float(category_amount),
            }

    return expense_data, float(total_expense), category_totals

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
