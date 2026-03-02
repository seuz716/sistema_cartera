from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from .models import Cliente
from .forms import ClienteForm

@login_required
def cliente_list(request):
    clientes = Cliente.objects.all()
    return render(request, 'clientes/cliente_list.html', {'clientes': clientes})

@login_required
def cliente_detail(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    return render(request, 'clientes/cliente_detail.html', {'cliente': cliente})

@login_required
def cliente_create(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('clientes:cliente_list')  # 👈 corregido
    else:
        form = ClienteForm()
    return render(request, 'clientes/cliente_form.html', {'form': form})

@login_required
def cliente_update(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            return redirect('clientes:cliente_detail', pk=cliente.pk)  # 👈 corregido
    else:
        form = ClienteForm(instance=cliente)
    return render(request, 'clientes/cliente_form.html', {'form': form})

@login_required
def cliente_delete(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        cliente.delete()
        return redirect('clientes:cliente_list')  # 👈 corregido
    return render(request, 'clientes/cliente_confirm_delete.html', {'cliente': cliente})
