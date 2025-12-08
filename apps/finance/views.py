from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.reservations.models import Reservation, ReservationGuest

from .models import Expense, ExtraIncome, LedgerAdjustment


def _reservation_totals(reservation: Reservation) -> dict:
    hospedes = reservation.hospedes.all()
    total = hospedes.aggregate(total=Sum('valor_devido'))['total'] or Decimal('0')
    pago = hospedes.filter(pago=True).aggregate(total=Sum('valor_devido'))['total'] or Decimal('0')
    return {
        'total': total,
        'pago': pago,
        'pendente': total - pago,
    }


@login_required
def reservation_balances(request):
    reservas = (
        Reservation.objects.all()
        .select_related('room')
        .prefetch_related('hospedes')
        .order_by('-data_entrada')
    )

    payload = []
    for reserva in reservas:
        totais = _reservation_totals(reserva)
        payload.append({
            'id': reserva.id,
            'room': reserva.room.numero,
            'guests': [hospede.nome for hospede in reserva.hospedes.all()],
            'total': float(totais['total']),
            'paid': float(totais['pago']),
            'pending': float(totais['pendente']),
            'active': reserva.ocupando,
        })

    return JsonResponse({'reservations': payload})


@login_required
def cash_overview(request):
    today = timezone.localdate()

    pix = (
        ReservationGuest.objects.filter(
            pago=True,
            metodo_pagamento=ReservationGuest.MetodoPagamento.PIX,
            atualizado_em__date=today,
        ).aggregate(total=Sum('valor_devido'))['total']
        or Decimal('0')
    )

    dinheiro = (
        ReservationGuest.objects.filter(
            pago=True,
            metodo_pagamento=ReservationGuest.MetodoPagamento.DINHEIRO,
            atualizado_em__date=today,
        ).aggregate(total=Sum('valor_devido'))['total']
        or Decimal('0')
    )

    ajustes = LedgerAdjustment.objects.filter(criado_em__date=today)
    creditos = ajustes.filter(tipo=LedgerAdjustment.Tipo.CREDITO).aggregate(total=Sum('valor'))['total'] or Decimal('0')
    debitos = ajustes.filter(tipo=LedgerAdjustment.Tipo.DEBITO).aggregate(total=Sum('valor'))['total'] or Decimal('0')

    extras = ExtraIncome.objects.filter(received_date=today).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    despesas = Expense.objects.filter(payment_date=today).aggregate(total=Sum('amount'))['total'] or Decimal('0')

    return JsonResponse({
        'pix': float(pix),
        'dinheiro': float(dinheiro),
        'ajustes_credito': float(creditos),
        'ajustes_debito': float(debitos),
        'extras': float(extras),
        'despesas': float(despesas),
    })


@login_required
def list_adjustments(request):
    ajustes = LedgerAdjustment.objects.select_related('reservation').order_by('-criado_em')[:100]
    data = [{
        'id': ajuste.id,
        'descricao': ajuste.descricao,
        'tipo': ajuste.get_tipo_display(),
        'valor': float(ajuste.valor),
        'metodo': ajuste.metodo,
        'reservation': ajuste.reservation_id,
        'created_at': ajuste.criado_em.isoformat(),
    } for ajuste in ajustes]
    return JsonResponse({'adjustments': data})


@login_required
@require_POST
def create_adjustment(request):
    try:
        tipo = request.POST.get('tipo', LedgerAdjustment.Tipo.CREDITO)
        descricao = request.POST.get('descricao', 'Ajuste manual')
        valor = Decimal(request.POST.get('valor', '0'))
        metodo = request.POST.get('metodo')
        reservation_id = request.POST.get('reservation_id')

        if valor == 0:
            return JsonResponse({'success': False, 'message': 'Informe um valor válido.'}, status=400)

        reservation = None
        if reservation_id:
            reservation = get_object_or_404(Reservation, id=reservation_id)

        ajuste = LedgerAdjustment.objects.create(
            reservation=reservation,
            descricao=descricao,
            tipo=tipo,
            valor=valor,
            metodo=metodo,
        )

        return JsonResponse({
            'success': True,
            'adjustment_id': ajuste.id,
        })
    except Exception as exc:
        return JsonResponse({'success': False, 'message': str(exc)}, status=400)


@login_required
@require_POST
def delete_adjustment(request, adjustment_id):
    ajuste = get_object_or_404(LedgerAdjustment, id=adjustment_id)
    ajuste.delete()
    return JsonResponse({'success': True})


@login_required
def expense_list(request):
    """
    Exibe todas as despesas registradas
    """
    expenses = Expense.objects.all()
    
    # Filtros
    category = request.GET.get('category')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if category and category != 'all':
        expenses = expenses.filter(category=category)
    
    if start_date:
        expenses = expenses.filter(payment_date__gte=start_date)
    
    if end_date:
        expenses = expenses.filter(payment_date__lte=end_date)
    
    # Totais por categoria
    category_totals = {}
    for category_code, category_name in Expense.CATEGORY_CHOICES:
        category_sum = sum(expense.amount for expense in expenses.filter(category=category_code))
        category_totals[category_code] = {
            'name': category_name,
            'total': category_sum
        }
    
    total_expenses = sum(expense.amount for expense in expenses)
    
    context = {
        'expenses': expenses,
        'category_totals': category_totals,
        'total_expenses': total_expenses,
        'categories': Expense.CATEGORY_CHOICES,
        'selected_category': category or 'all',
        'start_date': start_date,
        'end_date': end_date
    }
    
    return render(request, 'finance/expense_list.html', context)

@login_required
def create_expense(request):
    """
    Cria um novo registro de despesa
    """
    if request.method == 'POST':
        try:
            description = request.POST.get('description')
            amount = request.POST.get('amount')
            category = request.POST.get('category')
            payment_date = request.POST.get('payment_date') or timezone.now().date()
            payment_method = request.POST.get('payment_method')
            notes = request.POST.get('notes', '')
            
            # Validações básicas
            if not description or not amount or not payment_method:
                messages.error(request, 'Preencha todos os campos obrigatórios')
                return redirect('finance:expense_list')
            
            # Processar o upload do comprovante, se fornecido
            receipt = None
            if 'receipt' in request.FILES:
                receipt = request.FILES['receipt']
            
            # Criar a despesa
            expense = Expense.objects.create(
                description=description,
                amount=amount,
                category=category,
                payment_date=payment_date,
                payment_method=payment_method,
                receipt=receipt,
                notes=notes
            )
            
            messages.success(request, f'Despesa "{description}" registrada com sucesso!')
            return redirect('finance:expense_list')
            
        except Exception as e:
            messages.error(request, f'Erro ao registrar despesa: {str(e)}')
            return redirect('finance:expense_list')
    
    # Se for GET, renderiza o formulário na própria página de listagem
    return redirect('finance:expense_list')

@login_required
def delete_expense(request, expense_id):
    """
    Exclui um registro de despesa
    """
    if request.method == 'POST':
        try:
            expense = get_object_or_404(Expense, id=expense_id)
            description = expense.description
            expense.delete()
            messages.success(request, f'Despesa "{description}" excluída com sucesso!')
        except Exception as e:
            messages.error(request, f'Erro ao excluir despesa: {str(e)}')
    
    return redirect('finance:expense_list')

@login_required
def extra_income_list(request):
    """
    Lista todas as receitas avulsas
    """
    incomes = ExtraIncome.objects.all().order_by('-received_date')
    return render(request, 'finance/extra_income_list.html', {'incomes': incomes})

@login_required
def create_extra_income(request):
    """
    Cria uma nova receita avulsa
    """
    if request.method == 'POST':
        description = request.POST.get('description')
        amount = request.POST.get('amount')
        received_date = request.POST.get('received_date')
        method = request.POST.get('method')
        notes = request.POST.get('notes')
        if not description or not amount or not received_date or not method:
            messages.error(request, 'Preencha todos os campos obrigatórios.')
            return redirect('finance:create_extra_income')
        try:
            ExtraIncome.objects.create(
                description=description,
                amount=amount,
                received_date=received_date,
                method=method,
                notes=notes
            )
            messages.success(request, 'Receita avulsa registrada com sucesso!')
            return redirect('finance:extra_income_list')
        except Exception as e:
            messages.error(request, f'Erro ao registrar receita: {e}')
            return redirect('finance:create_extra_income')
    return render(request, 'finance/create_extra_income.html')
