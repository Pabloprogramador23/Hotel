from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse

from .models import Invoice, Payment
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
