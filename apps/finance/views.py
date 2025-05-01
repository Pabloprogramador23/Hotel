from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone

from .models import Invoice, Payment, Expense
from apps.reservations.models import Reservation

@login_required
def list_invoices(request, reservation_id=None):
    """
    Lista todas as faturas, ou apenas as de uma reserva específica
    """
    if reservation_id:
        invoices = Invoice.objects.filter(reservation_id=reservation_id)
    else:
        invoices = Invoice.objects.all()
    
    invoices_data = [{
        'id': invoice.id,
        'reservation_id': invoice.reservation_id,
        'amount': float(invoice.amount),
        'issued_at': invoice.issued_at.strftime('%Y-%m-%d %H:%M:%S'),
        'paid': invoice.paid
    } for invoice in invoices]
    
    return JsonResponse({'invoices': invoices_data})

@login_required
@require_POST
def create_invoice(request, reservation_id):
    """
    Cria uma nova fatura para uma reserva
    """
    try:
        amount = float(request.POST.get('amount', 0))
        if amount <= 0:
            return JsonResponse({
                'success': False,
                'message': 'O valor da fatura deve ser maior que zero'
            }, status=400)
            
        reservation = get_object_or_404(Reservation, id=reservation_id)
        
        invoice = Invoice.objects.create(
            reservation=reservation,
            amount=amount
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Fatura criada com sucesso',
            'invoice_id': invoice.id
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao criar fatura: {str(e)}'
        }, status=500)

@login_required
@require_POST
def mark_invoice_paid(request, invoice_id):
    """
    Marca uma fatura como paga
    """
    try:
        with transaction.atomic():
            invoice = get_object_or_404(Invoice, id=invoice_id)
            
            if invoice.paid:
                return JsonResponse({
                    'success': False,
                    'message': 'Esta fatura já está paga'
                }, status=400)
                
            invoice.paid = True
            invoice.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Fatura marcada como paga com sucesso'
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao processar pagamento: {str(e)}'
        }, status=500)

@login_required
def reservation_invoices_view(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id)
    invoices = reservation.invoices.all()
    if request.method == 'POST':
        if request.POST.get('add_payment'):
            invoice_id = request.POST.get('invoice_id')
            amount = request.POST.get('amount')
            method = request.POST.get('method')
            notes = request.POST.get('notes')
            invoice = get_object_or_404(Invoice, id=invoice_id, reservation=reservation)
            try:
                Payment.objects.create(
                    invoice=invoice,
                    amount=amount,
                    method=method,
                    notes=notes
                )
                messages.success(request, 'Pagamento registrado com sucesso!')
            except Exception as e:
                messages.error(request, f'Erro ao registrar pagamento: {e}')
            return redirect(reverse('finance:reservation_invoices', args=[reservation_id]))
        elif request.POST.get('create_extra_invoice'):
            extra_amount = request.POST.get('extra_amount')
            extra_notes = request.POST.get('extra_notes')
            try:
                Invoice.objects.create(
                    reservation=reservation,
                    amount=extra_amount
                    # O campo paid permanece False por padrão
                )
                messages.success(request, 'Fatura extra criada com sucesso!')
            except Exception as e:
                messages.error(request, f'Erro ao criar fatura extra: {e}')
            return redirect(reverse('finance:reservation_invoices', args=[reservation_id]))
        else:
            invoice_id = request.POST.get('invoice_id')
            invoice = get_object_or_404(Invoice, id=invoice_id, reservation=reservation)
            if not invoice.paid:
                invoice.paid = True
                invoice.save()
                messages.success(request, 'Fatura marcada como paga!')
            else:
                messages.info(request, 'Esta fatura já está paga.')
            return redirect(reverse('finance:reservation_invoices', args=[reservation_id]))
    return render(request, 'finance/invoice_list.html', {'reservation': reservation, 'invoices': invoices})

@login_required
def list_all_invoices_view(request):
    """
    Exibe todas as faturas em uma página HTML formatada
    """
    invoices = Invoice.objects.all().order_by('-issued_at')
    
    # Agrupar faturas por reserva para uma visualização melhor organizada
    reservations = {}
    for invoice in invoices:
        if invoice.reservation_id not in reservations:
            reservations[invoice.reservation_id] = {
                'reservation': invoice.reservation,
                'invoices': [],
                'total_amount': 0  # Inicializa o total
            }
        reservations[invoice.reservation_id]['invoices'].append(invoice)
        # Soma o valor ao total da reserva
        reservations[invoice.reservation_id]['total_amount'] += float(invoice.amount)
    
    context = {
        'reservations': reservations.values(),
        'total_value': sum(float(invoice.amount) for invoice in invoices),
        'total_paid': sum(float(invoice.amount) for invoice in invoices if invoice.paid),
        'total_pending': sum(float(invoice.amount) for invoice in invoices if not invoice.paid),
    }
    
    return render(request, 'finance/all_invoices.html', context)

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
