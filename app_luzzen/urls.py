from django.urls import path
from . import views

urlpatterns = [
    # Páginas Públicas
    path('', views.index, name='index'),
    path('catalogo/', views.catalogo, name='catalogo'),
    path('producto/<int:producto_id>/', views.detalle_producto, name='detalle_producto'),
    
    # Autenticación
    path('login/', views.login_view, name='login'),
    path('registro/', views.registro, name='registro'),
    path('logout/', views.logout_view, name='logout'),
    
    # Usuario Autenticado
    path('perfil/', views.perfil, name='perfil'),
    path('carrito/', views.carrito, name='carrito'),
    path('favoritos/', views.favoritos, name='favoritos'),
    path('historial-pedidos/', views.historial_pedidos, name='historial_pedidos'),
    path('pedido/<int:pedido_id>/', views.detalle_pedido, name='detalle_pedido'),
    
    # Panel de Administración
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    
    # CRUD Productos
    path('admin/productos/', views.admin_productos, name='admin_productos'),
    path('admin/productos/crear/', views.admin_productos_crear, name='admin_productos_crear'),
    path('admin/productos/editar/<int:producto_id>/', views.admin_productos_editar, name='admin_productos_editar'),
    path('admin/productos/eliminar/<int:producto_id>/', views.admin_productos_eliminar, name='admin_productos_eliminar'),
    
    # CRUD Categorías
    path('admin/categorias/', views.admin_categorias, name='admin_categorias'),
    path('admin/categorias/crear/', views.admin_categorias_crear, name='admin_categorias_crear'),
    path('admin/categorias/editar/<int:categoria_id>/', views.admin_categorias_editar, name='admin_categorias_editar'),
    path('admin/categorias/eliminar/<int:categoria_id>/', views.admin_categorias_eliminar, name='admin_categorias_eliminar'),
    
    # CRUD Marcas
    path('admin/marcas/', views.admin_marcas, name='admin_marcas'),
    path('admin/marcas/crear/', views.admin_marcas_crear, name='admin_marcas_crear'),
    path('admin/marcas/editar/<int:marca_id>/', views.admin_marcas_editar, name='admin_marcas_editar'),
    path('admin/marcas/eliminar/<int:marca_id>/', views.admin_marcas_eliminar, name='admin_marcas_eliminar'),
    
    # CRUD Materiales
    path('admin/materiales/', views.admin_materiales, name='admin_materiales'),
    path('admin/materiales/crear/', views.admin_materiales_crear, name='admin_materiales_crear'),
    path('admin/materiales/editar/<int:material_id>/', views.admin_materiales_editar, name='admin_materiales_editar'),
    path('admin/materiales/eliminar/<int:material_id>/', views.admin_materiales_eliminar, name='admin_materiales_eliminar'),
    
    # Gestión de Usuarios
    path('admin/usuarios/', views.admin_usuarios, name='admin_usuarios'),
    
    # Gestión de Pedidos
    path('admin/pedidos/', views.admin_pedidos, name='admin_pedidos'),
    
    # Gestión de Favoritos
    path('admin/favoritos/', views.admin_favoritos, name='admin_favoritos'),

    # Añade estas URLs después de las existentes
    path('favoritos/agregar/<int:producto_id>/', views.agregar_favorito, name='agregar_favorito'),
    path('favoritos/eliminar/<int:favorito_id>/', views.eliminar_favorito, name='eliminar_favorito'),
    path('carrito/agregar/<int:producto_id>/', views.agregar_carrito, name='agregar_carrito'),
    path('carrito/actualizar/<int:item_id>/', views.actualizar_carrito, name='actualizar_carrito'),
    path('carrito/eliminar/<int:item_id>/', views.eliminar_del_carrito, name='eliminar_del_carrito'),

    # Añade esta URL con las demás
    path('carrito/proceder-pago/', views.proceder_pago, name='proceder_pago'),
    # URLs para pedidos
    path('pedidos/editar/<int:pedido_id>/', views.admin_pedidos_editar, name='admin_pedidos_editar'),
    path('pedidos/eliminar/<int:pedido_id>/', views.admin_pedidos_eliminar, name='admin_pedidos_eliminar'),

    # URLs para usuarios
    path('usuarios/editar/<int:usuario_id>/', views.admin_usuarios_editar, name='admin_usuarios_editar'),
    path('usuarios/eliminar/<int:usuario_id>/', views.admin_usuarios_eliminar, name='admin_usuarios_eliminar'),

    # Añade estas URLs
    path('pago/', views.pago, name='pago'),
    path('pago/procesar/', views.procesar_pago, name='procesar_pago'),
]