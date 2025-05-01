from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from .models import SystemSetting

@login_required
@permission_required('settings_manager.view_systemsetting')
def settings_list(request):
    """View para listar todas as configurações do sistema."""
    settings_qs = SystemSetting.objects.all().order_by('key')
    paginator = Paginator(settings_qs, 20)  # 20 por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'settings_manager/list.html', {
        'settings': page_obj.object_list,
        'page_obj': page_obj,
        'title': 'Configurações do Sistema'
    })

@login_required
@permission_required('settings_manager.add_systemsetting')
def settings_create(request):
    """View para criar uma nova configuração do sistema."""
    if request.method == 'POST':
        key = request.POST.get('key')
        value = request.POST.get('value')
        description = request.POST.get('description', '')
        
        if not key or not value:
            messages.error(request, 'Chave e valor são campos obrigatórios.')
            return render(request, 'settings_manager/form.html', {
                'title': 'Nova Configuração',
                'key': key,
                'value': value,
                'description': description
            })
        
        if SystemSetting.objects.filter(key=key).exists():
            messages.error(request, f'Já existe uma configuração com a chave "{key}".')
            return render(request, 'settings_manager/form.html', {
                'title': 'Nova Configuração',
                'key': key,
                'value': value,
                'description': description
            })
        
        SystemSetting.objects.create(key=key, value=value, description=description)
        messages.success(request, f'Configuração "{key}" criada com sucesso.')
        return redirect('settings_manager:list')
    
    return render(request, 'settings_manager/form.html', {
        'title': 'Nova Configuração'
    })

@login_required
@permission_required('settings_manager.change_systemsetting')
def settings_edit(request, pk):
    """View para editar uma configuração existente."""
    setting = get_object_or_404(SystemSetting, pk=pk)
    
    if request.method == 'POST':
        key = request.POST.get('key')
        value = request.POST.get('value')
        description = request.POST.get('description', '')
        
        if not key or not value:
            messages.error(request, 'Chave e valor são campos obrigatórios.')
            return render(request, 'settings_manager/form.html', {
                'title': 'Editar Configuração',
                'setting': setting,
                'key': key,
                'value': value,
                'description': description
            })
        
        # Verificar se a chave já existe (excluindo o registro atual)
        if SystemSetting.objects.filter(key=key).exclude(pk=pk).exists():
            messages.error(request, f'Já existe uma configuração com a chave "{key}".')
            return render(request, 'settings_manager/form.html', {
                'title': 'Editar Configuração',
                'setting': setting,
                'key': key,
                'value': value,
                'description': description
            })
        
        setting.key = key
        setting.value = value
        setting.description = description
        setting.save()
        
        messages.success(request, f'Configuração "{key}" atualizada com sucesso.')
        return redirect('settings_manager:list')
    
    return render(request, 'settings_manager/form.html', {
        'title': 'Editar Configuração',
        'setting': setting,
        'key': setting.key,
        'value': setting.value,
        'description': setting.description
    })

@login_required
@permission_required('settings_manager.delete_systemsetting')
def settings_delete(request, pk):
    """View para excluir uma configuração do sistema."""
    setting = get_object_or_404(SystemSetting, pk=pk)
    
    if request.method == 'POST':
        key = setting.key
        setting.delete()
        messages.success(request, f'Configuração "{key}" excluída com sucesso.')
        return redirect('settings_manager:list')
    
    return render(request, 'settings_manager/delete.html', {
        'setting': setting,
        'title': 'Confirmar Exclusão'
    })
