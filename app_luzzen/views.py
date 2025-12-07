from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q, Count, Sum
from .models import *
from django.http import JsonResponse
from functools import wraps

# Decorador para verificar si el usuario está autenticado
def login_required_custom(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get('usuario_id'):
            messages.error(request, 'Debes iniciar sesión para acceder a esta página')
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper

# Decorador para verificar si es administrador
def admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get('usuario_id'):
            messages.error(request, 'Debes iniciar sesión para acceder a esta página')
            return redirect('login')
        if not request.session.get('es_admin'):
            messages.error(request, 'No tienes permisos de administrador')
            return redirect('index')
        return view_func(request, *args, **kwargs)
    return wrapper

# Helper functions
def es_administrador(user):
    return user.is_authenticated and user.is_staff

# Vistas Públicas
def index(request):
    """Página principal"""
    categorias = Categoria.objects.all()[:3]
    productos_destacados = Producto.objects.filter(activo=True)[:6]
    
    context = {
        'categorias': categorias,
        'productos_destacados': productos_destacados,
    }
    return render(request, 'index.html', context)

def catalogo(request):
    """Catálogo de productos con filtros"""
    productos = Producto.objects.filter(activo=True)
    
    # Filtros
    categoria_id = request.GET.get('categoria')
    marca_id = request.GET.get('marca')
    material_id = request.GET.get('material')
    buscar = request.GET.get('buscar')
    
    if categoria_id:
        productos = productos.filter(categoria_id=categoria_id)
    if marca_id:
        productos = productos.filter(marca_id=marca_id)
    if material_id:
        productos = productos.filter(material_id=material_id)
    if buscar:
        productos = productos.filter(
            Q(nombre__icontains=buscar) | 
            Q(descripcion__icontains=buscar)
        )
    
    categorias = Categoria.objects.all()
    marcas = Marca.objects.all()
    materiales = Material.objects.all()
    
    context = {
        'productos': productos,
        'categorias': categorias,
        'marcas': marcas,
        'materiales': materiales,
    }
    return render(request, 'catalogo.html', context)

def detalle_producto(request, producto_id):
    """Detalle de un producto específico"""
    producto = get_object_or_404(Producto, id=producto_id, activo=True)
    relacionados = Producto.objects.filter(
        categoria=producto.categoria, 
        activo=True
    ).exclude(id=producto.id)[:4]
    
    context = {
        'producto': producto,
        'relacionados': relacionados,
    }
    return render(request, 'detalle_producto.html', context)

# Vistas de Autenticación
def login_view(request):
    """Inicio de sesión para usuarios y administradores"""
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        es_admin = request.POST.get('is_admin')
        
        try:
            usuario = Usuario.objects.get(email=email, contraseña=password)
            
            # Crear sesión manual (sin usar auth de Django)
            request.session['usuario_id'] = usuario.id
            request.session['usuario_nombre'] = usuario.nombre
            request.session['usuario_email'] = usuario.email
            request.session['es_admin'] = bool(es_admin)
            
            messages.success(request, f'¡Bienvenido {usuario.nombre}!')
            
            if es_admin:
                return redirect('admin_dashboard')
            return redirect('index')
            
        except Usuario.DoesNotExist:
            messages.error(request, 'Credenciales incorrectas')
    
    return render(request, 'login.html')

def registro(request):
    """Registro de nuevos usuarios"""
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        pais = request.POST.get('pais')
        direccion = request.POST.get('direccion')
        
        if password != confirm_password:
            messages.error(request, 'Las contraseñas no coinciden')
            return render(request, 'registro.html')
        
        if Usuario.objects.filter(email=email).exists():
            messages.error(request, 'Este email ya está registrado')
            return render(request, 'registro.html')
        
        try:
            usuario = Usuario.objects.create(
                nombre=nombre,
                email=email,
                contraseña=password,  # En un caso real, esto estaría cifrado
                pais=pais,
                direccion=direccion,
            )
            
            # Iniciar sesión automáticamente
            request.session['usuario_id'] = usuario.id
            request.session['usuario_nombre'] = usuario.nombre
            request.session['usuario_email'] = usuario.email
            request.session['es_admin'] = False
            
            messages.success(request, f'¡Cuenta creada exitosamente! Bienvenido {nombre}')
            return redirect('index')
            
        except Exception as e:
            messages.error(request, 'Error al crear la cuenta')
    
    return render(request, 'registro.html')

def logout_view(request):
    """Cerrar sesión"""
    if request.method == 'POST':
        # Limpiar sesión
        for key in list(request.session.keys()):
            del request.session[key]
        messages.success(request, 'Sesión cerrada correctamente')
        return redirect('index')
    
    return render(request, 'logout.html')

# Vistas de Usuario Autenticado
@login_required_custom
def perfil(request):
    """Perfil del usuario"""
    usuario_id = request.session.get('usuario_id')
    usuario = get_object_or_404(Usuario, id=usuario_id)
    
    pedidos_activos = Pedido.objects.filter(cliente=usuario, estado='pendiente').count()
    total_favoritos = Favorito.objects.filter(cliente=usuario).count()
    total_gastado = Pedido.objects.filter(
        cliente=usuario, 
        estado='completado'
    ).aggregate(total=Sum('total'))['total'] or 0
    
    context = {
        'usuario': usuario,
        'pedidos_activos': pedidos_activos,
        'total_favoritos': total_favoritos,
        'total_gastado': total_gastado,
    }
    return render(request, 'perfil.html', context)

@login_required_custom
def carrito(request):
    """Carrito de compras del usuario"""
    usuario_id = request.session.get('usuario_id')
    usuario = get_object_or_404(Usuario, id=usuario_id)
    
    # Obtener o crear pedido pendiente (carrito)
    pedido, created = Pedido.objects.get_or_create(
        cliente=usuario,
        estado='pendiente',  # Esto es el carrito
        defaults={'total': 0}
    )
    
    items = pedido.items.all()
    subtotal = sum(item.cantidad * item.precio_unitario for item in items)
    total = subtotal
    
    context = {
        'items': items,
        'pedido': pedido,
        'subtotal': subtotal,
        'total': total,
    }
    return render(request, 'carrito.html', context)

@login_required_custom
def proceder_pago(request):
    """Convertir carrito en pedido real"""
    if request.method == 'POST':
        usuario_id = request.session.get('usuario_id')
        usuario = get_object_or_404(Usuario, id=usuario_id)
        
        # Obtener el pedido pendiente (carrito)
        pedido = get_object_or_404(Pedido, cliente=usuario, estado='pendiente')
        
        # Verificar que el carrito no esté vacío
        if pedido.items.count() == 0:
            messages.error(request, 'Tu carrito está vacío')
            return redirect('carrito')
        
        # Verificar stock de productos
        for item in pedido.items.all():
            if item.cantidad > item.producto.stock:
                messages.error(request, f'No hay suficiente stock de {item.producto.nombre}')
                return redirect('carrito')
        
        # Actualizar stock y cambiar estado del pedido
        for item in pedido.items.all():
            producto = item.producto
            producto.stock -= item.cantidad
            producto.save()
        
        # Cambiar estado a "completado" (pedido real)
        pedido.estado = 'completado'
        pedido.save()
        
        messages.success(request, '¡Compra realizada exitosamente!')
        return redirect('historial_pedidos')
    
    return redirect('carrito')

@login_required_custom
def favoritos(request):
    """Lista de productos favoritos del usuario"""
    usuario_id = request.session.get('usuario_id')
    usuario = get_object_or_404(Usuario, id=usuario_id)
    
    favoritos = Favorito.objects.filter(cliente=usuario)
    
    context = {
        'favoritos': favoritos,
    }
    return render(request, 'favoritos.html', context)

@login_required_custom
def historial_pedidos(request):
    """Historial de pedidos del usuario"""
    usuario_id = request.session.get('usuario_id')
    usuario = get_object_or_404(Usuario, id=usuario_id)
    
    # Solo mostrar pedidos completados (no los pendientes/carrito)
    pedidos = Pedido.objects.filter(cliente=usuario, estado='completado').order_by('-fecha_creacion')
    
    context = {
        'pedidos': pedidos,
    }
    return render(request, 'historial_pedidos.html', context)

@login_required_custom
def detalle_pedido(request, pedido_id):
    """Detalle de un pedido específico"""
    usuario_id = request.session.get('usuario_id')
    usuario = get_object_or_404(Usuario, id=usuario_id)
    
    pedido = get_object_or_404(Pedido, id=pedido_id, cliente=usuario)
    
    context = {
        'pedido': pedido,
    }
    return render(request, 'detalle_pedido.html', context)

# Vistas de Administrador
@admin_required
def admin_dashboard(request):
    """Panel principal de administración"""
    total_productos = Producto.objects.count()
    pedidos_pendientes = Pedido.objects.filter(estado='pendiente').count()
    total_usuarios = Usuario.objects.count()
    
    # Calcular ingresos mensuales (ejemplo)
    ingresos_mensuales = Pedido.objects.filter(
        estado='completado'
    ).aggregate(total=Sum('total'))['total'] or 0
    
    pedidos_recientes = Pedido.objects.select_related('cliente').order_by('-fecha_creacion')[:5]
    
    context = {
        'total_productos': total_productos,
        'pedidos_pendientes': pedidos_pendientes,
        'total_usuarios': total_usuarios,
        'ingresos_mensuales': ingresos_mensuales,
        'pedidos_recientes': pedidos_recientes,
    }
    return render(request, 'admin/dashboard.html', context)

# CRUD Productos
@admin_required
def admin_productos(request):
    """Lista de productos para CRUD"""
    productos = Producto.objects.select_related('categoria', 'marca', 'material').all()
    categorias = Categoria.objects.all()
    marcas = Marca.objects.all()
    
    context = {
        'productos': productos,
        'categorias': categorias,
        'marcas': marcas,
    }
    return render(request, 'admin/productos/lista.html', context)

@admin_required
def admin_productos_crear(request):
    """Crear nuevo producto"""
    if request.method == 'POST':
        try:
            producto = Producto.objects.create(
                nombre=request.POST.get('nombre'),
                descripcion=request.POST.get('descripcion'),
                precio=request.POST.get('precio'),
                stock=request.POST.get('stock'),
                categoria_id=request.POST.get('categoria'),
                marca_id=request.POST.get('marca'),
                material_id=request.POST.get('material'),
                activo=bool(request.POST.get('activo')),
            )
            
            if 'imagen' in request.FILES:
                producto.imagen = request.FILES['imagen']
                producto.save()
            
            messages.success(request, 'Producto creado exitosamente')
            return redirect('admin_productos')
            
        except Exception as e:
            messages.error(request, f'Error al crear producto: {str(e)}')
    
    categorias = Categoria.objects.all()
    marcas = Marca.objects.all()
    materiales = Material.objects.all()
    
    context = {
        'titulo': 'Crear Producto',
        'accion': 'Crear Producto',
        'categorias': categorias,
        'marcas': marcas,
        'materiales': materiales,
    }
    return render(request, 'admin/productos/form.html', context)

@admin_required
def admin_productos_editar(request, producto_id):
    """Editar producto existente"""
    producto = get_object_or_404(Producto, id=producto_id)
    
    if request.method == 'POST':
        try:
            producto.nombre = request.POST.get('nombre')
            producto.descripcion = request.POST.get('descripcion')
            producto.precio = request.POST.get('precio')
            producto.stock = request.POST.get('stock')
            producto.categoria_id = request.POST.get('categoria')
            producto.marca_id = request.POST.get('marca')
            producto.material_id = request.POST.get('material')
            producto.activo = bool(request.POST.get('activo'))
            
            if 'imagen' in request.FILES:
                producto.imagen = request.FILES['imagen']
            
            producto.save()
            messages.success(request, 'Producto actualizado exitosamente')
            return redirect('admin_productos')
            
        except Exception as e:
            messages.error(request, f'Error al actualizar producto: {str(e)}')
    
    categorias = Categoria.objects.all()
    marcas = Marca.objects.all()
    materiales = Material.objects.all()
    
    context = {
        'titulo': 'Editar Producto',
        'accion': 'Actualizar Producto',
        'producto': producto,
        'categorias': categorias,
        'marcas': marcas,
        'materiales': materiales,
    }
    return render(request, 'admin/productos/form.html', context)

@admin_required
def admin_productos_eliminar(request, producto_id):
    """Eliminar producto"""
    if request.method == 'POST':
        producto = get_object_or_404(Producto, id=producto_id)
        producto.delete()
        messages.success(request, 'Producto eliminado exitosamente')
    
    return redirect('admin_productos')

# CRUD Categorías
@admin_required
def admin_categorias(request):
    """Lista de categorías para CRUD"""
    categorias = Categoria.objects.annotate(
        total_productos=Count('producto')
    )
    
    context = {
        'categorias': categorias,
        'total_categorias': categorias.count(),
    }
    return render(request, 'admin/categorias/lista.html', context)

@admin_required
def admin_categorias_crear(request):
    """Crear nueva categoría"""
    if request.method == 'POST':
        try:
            Categoria.objects.create(
                nombre=request.POST.get('nombre'),
                descripcion=request.POST.get('descripcion', ''),
            )
            messages.success(request, 'Categoría creada exitosamente')
            return redirect('admin_categorias')
        except Exception as e:
            messages.error(request, f'Error al crear categoría: {str(e)}')
    
    context = {
        'titulo': 'Crear Categoría',
        'accion': 'Crear Categoría',
    }
    return render(request, 'admin/categorias/form.html', context)

@admin_required
def admin_categorias_editar(request, categoria_id):
    """Editar categoría existente"""
    categoria = get_object_or_404(Categoria, id=categoria_id)
    
    if request.method == 'POST':
        try:
            categoria.nombre = request.POST.get('nombre')
            categoria.descripcion = request.POST.get('descripcion', '')
            categoria.save()
            messages.success(request, 'Categoría actualizada exitosamente')
            return redirect('admin_categorias')
        except Exception as e:
            messages.error(request, f'Error al actualizar categoría: {str(e)}')
    
    context = {
        'titulo': 'Editar Categoría',
        'accion': 'Actualizar Categoría',
        'categoria': categoria,
    }
    return render(request, 'admin/categorias/form.html', context)

@admin_required
def admin_categorias_eliminar(request, categoria_id):
    """Eliminar categoría"""
    if request.method == 'POST':
        categoria = get_object_or_404(Categoria, id=categoria_id)
        categoria.delete()
        messages.success(request, 'Categoría eliminada exitosamente')
    
    return redirect('admin_categorias')

# CRUD Marcas (similar a categorías)
@admin_required
def admin_marcas(request):
    marcas = Marca.objects.annotate(total_productos=Count('producto'))
    context = {
        'marcas': marcas,
        'total_marcas': marcas.count(),
    }
    return render(request, 'admin/marcas/lista.html', context)

@admin_required
def admin_marcas_crear(request):
    if request.method == 'POST':
        try:
            Marca.objects.create(
                nombre=request.POST.get('nombre'),
                descripcion=request.POST.get('descripcion', ''),
            )
            messages.success(request, 'Marca creada exitosamente')
            return redirect('admin_marcas')
        except Exception as e:
            messages.error(request, f'Error al crear marca: {str(e)}')
    
    context = {
        'titulo': 'Crear Marca',
        'accion': 'Crear Marca',
    }
    return render(request, 'admin/marcas/form.html', context)

@admin_required
def admin_marcas_editar(request, marca_id):
    marca = get_object_or_404(Marca, id=marca_id)
    
    if request.method == 'POST':
        try:
            marca.nombre = request.POST.get('nombre')
            marca.descripcion = request.POST.get('descripcion', '')
            marca.save()
            messages.success(request, 'Marca actualizada exitosamente')
            return redirect('admin_marcas')
        except Exception as e:
            messages.error(request, f'Error al actualizar marca: {str(e)}')
    
    context = {
        'titulo': 'Editar Marca',
        'accion': 'Actualizar Marca',
        'marca': marca,
    }
    return render(request, 'admin/marcas/form.html', context)

@admin_required
def admin_marcas_eliminar(request, marca_id):
    if request.method == 'POST':
        marca = get_object_or_404(Marca, id=marca_id)
        marca.delete()
        messages.success(request, 'Marca eliminada exitosamente')
    return redirect('admin_marcas')

# CRUD Materiales (similar a categorías)
@admin_required
def admin_materiales(request):
    materiales = Material.objects.annotate(total_productos=Count('producto'))
    context = {
        'materiales': materiales,
        'total_materiales': materiales.count(),
    }
    return render(request, 'admin/materiales/lista.html', context)

@admin_required
def admin_materiales_crear(request):
    if request.method == 'POST':
        try:
            Material.objects.create(
                nombre=request.POST.get('nombre'),
                descripcion=request.POST.get('descripcion', ''),
                precio=request.POST.get('precio'),
            )
            messages.success(request, 'Material creado exitosamente')
            return redirect('admin_materiales')
        except Exception as e:
            messages.error(request, f'Error al crear material: {str(e)}')
    
    context = {
        'titulo': 'Crear Material',
        'accion': 'Crear Material',
    }
    return render(request, 'admin/materiales/form.html', context)

@admin_required
def admin_materiales_editar(request, material_id):
    material = get_object_or_404(Material, id=material_id)
    
    if request.method == 'POST':
        try:
            material.nombre = request.POST.get('nombre')
            material.descripcion = request.POST.get('descripcion', '')
            material.precio = request.POST.get('precio')
            material.save()
            messages.success(request, 'Material actualizado exitosamente')
            return redirect('admin_materiales')
        except Exception as e:
            messages.error(request, f'Error al actualizar material: {str(e)}')
    
    context = {
        'titulo': 'Editar Material',
        'accion': 'Actualizar Material',
        'material': material,
    }
    return render(request, 'admin/materiales/form.html', context)

@admin_required
def admin_materiales_eliminar(request, material_id):
    if request.method == 'POST':
        material = get_object_or_404(Material, id=material_id)
        material.delete()
        messages.success(request, 'Material eliminado exitosamente')
    return redirect('admin_materiales')

# Gestión de Usuarios
@admin_required
def admin_usuarios(request):
    usuarios = Usuario.objects.annotate(
        total_pedidos=Count('pedido'),
        total_favoritos=Count('favorito')
    )
    
    
    context = {
        'usuarios': usuarios,
        'total_usuarios': usuarios.count(),
    }
    return render(request, 'admin/usuarios/lista.html', context)

# Gestión de Pedidos
@admin_required
def admin_pedidos(request):
    # Excluir los pedidos pendientes (carritos) del admin
    pedidos = Pedido.objects.filter(estado__in=['completado', 'cancelado']).select_related('cliente').prefetch_related('items')
    
    total_pedidos = pedidos.count()
    pedidos_pendientes = Pedido.objects.filter(estado='pendiente').count()  # Carritos activos
    ingresos_totales = pedidos.filter(estado='completado').aggregate(
        total=Sum('total')
    )['total'] or 0
    
    context = {
        'pedidos': pedidos,
        'total_pedidos': total_pedidos,
        'pedidos_pendientes': pedidos_pendientes,
        'ingresos_totales': ingresos_totales,
    }
    return render(request, 'admin/pedidos/lista.html', context)

@admin_required
def admin_pedidos_editar(request, pedido_id):
    """Editar pedido existente"""
    pedido = get_object_or_404(Pedido, id=pedido_id)
    
    if request.method == 'POST':
        try:
            estado_anterior = pedido.estado
            pedido.estado = request.POST.get('estado')
            pedido.save()
            
            messages.success(request, 'Pedido actualizado exitosamente')
            return redirect('admin_pedidos')
            
        except Exception as e:
            messages.error(request, f'Error al actualizar pedido: {str(e)}')
    
    context = {
        'titulo': f'Editar Pedido #{pedido.id}',
        'accion': 'Actualizar Pedido',
        'pedido': pedido,
    }
    return render(request, 'admin/pedidos/form.html', context)

@admin_required
def admin_pedidos_eliminar(request, pedido_id):
    """Eliminar pedido"""
    if request.method == 'POST':
        pedido = get_object_or_404(Pedido, id=pedido_id)
        
        pedido.delete()
        messages.success(request, 'Pedido eliminado exitosamente')
    
    return redirect('admin_pedidos')

@admin_required
def admin_usuarios_editar(request, usuario_id):
    """Editar usuario existente"""
    usuario = get_object_or_404(Usuario, id=usuario_id)
    
    if request.method == 'POST':
        try:
            usuario.nombre = request.POST.get('nombre')
            usuario.email = request.POST.get('email')
            usuario.pais = request.POST.get('pais')
            usuario.direccion = request.POST.get('direccion')
            
            # Actualizar contraseña solo si se proporciona una nueva
            nueva_password = request.POST.get('contraseña')
            if nueva_password:
                usuario.contraseña = nueva_password
            
            usuario.save()
            messages.success(request, 'Usuario actualizado exitosamente')
            return redirect('admin_usuarios')
            
        except Exception as e:
            messages.error(request, f'Error al actualizar usuario: {str(e)}')
    
    # Calcular estadísticas para el template
    pedidos_completados = usuario.pedido_set.filter(estado='completado').count()
    pedidos_pendientes = usuario.pedido_set.filter(estado='pendiente').count()
    total_gastado = usuario.pedido_set.filter(estado='completado').aggregate(
        total=Sum('total')
    )['total'] or 0
    
    # Intentar obtener fecha de registro (usando el primer pedido como referencia)
    primer_pedido = usuario.pedido_set.order_by('fecha_creacion').first()
    fecha_registro = primer_pedido.fecha_creacion if primer_pedido else 'N/A'
    
    context = {
        'titulo': f'Editar Usuario: {usuario.nombre}',
        'accion': 'Actualizar Usuario',
        'usuario': usuario,
        'pedidos_completados': pedidos_completados,
        'pedidos_pendientes': pedidos_pendientes,
        'total_gastado': total_gastado,
        'fecha_registro': fecha_registro,
    }
    return render(request, 'admin/usuarios/form.html', context)

@admin_required
def admin_usuarios_eliminar(request, usuario_id):
    """Eliminar usuario"""
    if request.method == 'POST':
        usuario = get_object_or_404(Usuario, id=usuario_id)
        
        usuario.delete()
        messages.success(request, 'Usuario y todos sus datos eliminados exitosamente')
    
    return redirect('admin_usuarios')

# Gestión de Favoritos
@admin_required
def admin_favoritos(request):
    favoritos = Favorito.objects.select_related('cliente', 'producto')
    
    total_favoritos = favoritos.count()
    usuarios_activos = favoritos.values('cliente').distinct().count()
    productos_populares = favoritos.values('producto').distinct().count()
    
    context = {
        'favoritos': favoritos,
        'total_favoritos': total_favoritos,
        'usuarios_activos': usuarios_activos,
        'productos_populares': productos_populares,
        'productos': Producto.objects.all()[:10],  # Para el filtro
    }
    return render(request, 'admin/favoritos/lista.html', context)

def login_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.session.get('usuario_id'):
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper

def user_passes_test(test_func):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if test_func(request):
                return view_func(request, *args, **kwargs)
            return redirect('login')
        return wrapper
    return decorator

def es_administrador(request):
    return request.session.get('es_admin', False)

@login_required_custom
def agregar_favorito(request, producto_id):
    """Agregar producto a favoritos"""
    if request.method == 'POST':
        usuario_id = request.session.get('usuario_id')
        usuario = get_object_or_404(Usuario, id=usuario_id)
        producto = get_object_or_404(Producto, id=producto_id)
        
        # Verificar si ya existe
        favorito, created = Favorito.objects.get_or_create(
            cliente=usuario,
            producto=producto
        )
        
        if created:
            return JsonResponse({'success': True, 'message': 'Producto agregado a favoritos'})
        else:
            return JsonResponse({'success': False, 'message': 'El producto ya está en favoritos'})
    
    return JsonResponse({'success': False, 'message': 'Método no permitido'})

@login_required_custom
def eliminar_favorito(request, favorito_id):
    """Eliminar producto de favoritos"""
    if request.method == 'POST':
        usuario_id = request.session.get('usuario_id')
        usuario = get_object_or_404(Usuario, id=usuario_id)
        
        favorito = get_object_or_404(Favorito, id=favorito_id, cliente=usuario)
        favorito.delete()
        
        return JsonResponse({'success': True, 'message': 'Producto eliminado de favoritos'})
    
    return JsonResponse({'success': False, 'message': 'Método no permitido'})

@login_required_custom
def agregar_carrito(request, producto_id):
    """Agregar producto al carrito"""
    if request.method == 'POST':
        usuario_id = request.session.get('usuario_id')
        usuario = get_object_or_404(Usuario, id=usuario_id)
        producto = get_object_or_404(Producto, id=producto_id)
        
        # Verificar stock
        if producto.stock <= 0:
            return JsonResponse({
                'success': False, 
                'message': 'Producto sin stock disponible'
            })
        
        # Obtener o crear pedido pendiente (carrito)
        pedido, created = Pedido.objects.get_or_create(
            cliente=usuario,
            estado='pendiente',
            defaults={'total': 0}
        )
        
        # Verificar si el producto ya está en el carrito
        item, item_created = ItemPedido.objects.get_or_create(
            pedido=pedido,
            producto=producto,
            defaults={
                'cantidad': 1,
                'precio_unitario': producto.precio
            }
        )
        
        if not item_created:
            # Si ya existe, verificar que no exceda el stock
            if item.cantidad + 1 > producto.stock:
                return JsonResponse({
                    'success': False, 
                    'message': 'No hay suficiente stock disponible'
                })
            item.cantidad += 1
            item.save()
        
        # Actualizar total del pedido
        total = sum(item.cantidad * item.precio_unitario for item in pedido.items.all())
        pedido.total = total
        pedido.save()
        
        return JsonResponse({
            'success': True, 
            'message': 'Producto agregado al carrito',
            'carrito_count': pedido.items.count()
        })
    
    return JsonResponse({'success': False, 'message': 'Método no permitido'})

@login_required_custom
def actualizar_carrito(request, item_id):
    """Actualizar cantidad en carrito"""
    if request.method == 'POST':
        usuario_id = request.session.get('usuario_id')
        usuario = get_object_or_404(Usuario, id=usuario_id)
        
        item = get_object_or_404(ItemPedido, id=item_id, pedido__cliente=usuario)
        accion = request.POST.get('accion')
        
        if accion == 'incrementar':
            item.cantidad += 1
        elif accion == 'decrementar' and item.cantidad > 1:
            item.cantidad -= 1
        
        item.save()
        
        # Actualizar total del pedido
        pedido = item.pedido
        total = sum(item.cantidad * item.precio_unitario for item in pedido.items.all())
        pedido.total = total
        pedido.save()
        
        return JsonResponse({
            'success': True,
            'nueva_cantidad': item.cantidad,
            'subtotal': item.cantidad * item.precio_unitario
        })
    
    return JsonResponse({'success': False, 'message': 'Método no permitido'})

@login_required_custom
def eliminar_del_carrito(request, item_id):
    """Eliminar item del carrito"""
    if request.method == 'POST':
        usuario_id = request.session.get('usuario_id')
        usuario = get_object_or_404(Usuario, id=usuario_id)
        
        item = get_object_or_404(ItemPedido, id=item_id, pedido__cliente=usuario)
        item.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Producto eliminado del carrito'
        })
    
    return JsonResponse({'success': False, 'message': 'Método no permitido'})

@login_required_custom
def pago(request):
    """Pasarela de pago"""
    usuario_id = request.session.get('usuario_id')
    usuario = get_object_or_404(Usuario, id=usuario_id)
    
    # Obtener el pedido pendiente (carrito)
    pedido = get_object_or_404(Pedido, cliente=usuario, estado='pendiente')
    items = pedido.items.all()
    
    # Verificar que el carrito no esté vacío
    if items.count() == 0:
        messages.error(request, 'Tu carrito está vacío')
        return redirect('carrito')
    
    # Calcular totales
    subtotal = sum(item.cantidad * item.precio_unitario for item in items)
    total = subtotal
    
    context = {
        'items': items,
        'pedido': pedido,
        'subtotal': subtotal,
        'total': total,
    }
    return render(request, 'pago.html', context)

@login_required_custom
def procesar_pago(request):
    """Procesar el pago y completar el pedido"""
    if request.method == 'POST':
        usuario_id = request.session.get('usuario_id')
        usuario = get_object_or_404(Usuario, id=usuario_id)
        
        # Obtener el pedido pendiente (carrito)
        pedido = get_object_or_404(Pedido, cliente=usuario, estado='pendiente')
        
        # Verificar que el carrito no esté vacío
        if pedido.items.count() == 0:
            messages.error(request, 'Tu carrito está vacío')
            return redirect('carrito')
        
        # Verificar stock de productos
        for item in pedido.items.all():
            if item.cantidad > item.producto.stock:
                messages.error(request, f'No hay suficiente stock de {item.producto.nombre}')
                return redirect('carrito')
        
        # Actualizar stock y cambiar estado del pedido
        for item in pedido.items.all():
            producto = item.producto
            producto.stock -= item.cantidad
            producto.save()
        
        # Cambiar estado a "completado" (pedido real)
        pedido.estado = 'completado'
        pedido.save()
        
        messages.success(request, '¡Pago procesado exitosamente! Tu pedido ha sido confirmado.')
        return redirect('historial_pedidos')
    
    return redirect('carrito')