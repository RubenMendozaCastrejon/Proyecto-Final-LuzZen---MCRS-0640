from django.contrib import admin
from .models import *

# Configuración del sitio admin
admin.site.site_header = "LuzZen - Panel de Administración"
admin.site.site_title = "LuzZen Admin"
admin.site.index_title = "Bienvenido al Panel de Administración de LuzZen"

# Modelo: Categoria
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ['id', 'nombre', 'descripcion_corta']
    list_display_links = ['id', 'nombre']
    search_fields = ['nombre', 'descripcion']
    list_per_page = 20
    
    def descripcion_corta(self, obj):
        return obj.descripcion[:50] + '...' if obj.descripcion and len(obj.descripcion) > 50 else obj.descripcion
    descripcion_corta.short_description = 'Descripción'

# Modelo: Marca
class MarcaAdmin(admin.ModelAdmin):
    list_display = ['id', 'nombre', 'descripcion_corta', 'fecha_creacion']
    list_display_links = ['id', 'nombre']
    search_fields = ['nombre', 'descripcion']
    list_filter = ['fecha_creacion']
    list_per_page = 20
    
    def descripcion_corta(self, obj):
        return obj.descripcion[:50] + '...' if obj.descripcion and len(obj.descripcion) > 50 else obj.descripcion
    descripcion_corta.short_description = 'Descripción'

# Modelo: Material
class MaterialAdmin(admin.ModelAdmin):
    list_display = ['id', 'nombre', 'precio', 'descripcion_corta']
    list_display_links = ['id', 'nombre']
    search_fields = ['nombre', 'descripcion']
    list_filter = ['precio']
    list_per_page = 20
    
    def descripcion_corta(self, obj):
        return obj.descripcion[:50] + '...' if obj.descripcion and len(obj.descripcion) > 50 else obj.descripcion
    descripcion_corta.short_description = 'Descripción'

# Inline para Items de Pedido
class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    extra = 1
    readonly_fields = ['precio_unitario_display']
    fields = ['producto', 'cantidad', 'precio_unitario_display']
    
    def precio_unitario_display(self, obj):
        return f"${obj.precio_unitario}"
    precio_unitario_display.short_description = 'Precio Unitario'

# Modelo: Producto
class ProductoAdmin(admin.ModelAdmin):
    list_display = [
        'id', 
        'nombre', 
        'precio', 
        'stock', 
        'categoria', 
        'marca', 
        'material', 
        'activo'
    ]
    list_display_links = ['id', 'nombre']
    list_filter = ['categoria', 'marca', 'material', 'activo']
    search_fields = ['nombre', 'descripcion']
    list_editable = ['precio', 'stock', 'activo']
    readonly_fields = ['imagen_preview']
    fieldsets = [
        ('Información Básica', {
            'fields': [
                'nombre', 
                'descripcion', 
                'precio', 
                'stock',
                'imagen',
                'imagen_preview'
            ]
        }),
        ('Categorización', {
            'fields': [
                'categoria', 
                'marca', 
                'material'
            ]
        }),
        ('Estado', {
            'fields': [
                'activo'
            ]
        }),
    ]
    list_per_page = 25
    
    def imagen_preview(self, obj):
        if obj.imagen:
            return f'<img src="{obj.imagen.url}" style="max-height: 100px;" />'
        return "Sin imagen"
    imagen_preview.allow_tags = True
    imagen_preview.short_description = 'Vista Previa'

# Modelo: Usuario
class UsuarioAdmin(admin.ModelAdmin):
    list_display = [
        'id', 
        'nombre', 
        'email', 
        'pais', 
        'total_pedidos',
        'total_favoritos'
    ]
    list_display_links = ['id', 'nombre']
    search_fields = ['nombre', 'email', 'pais']
    list_filter = ['pais']
    readonly_fields = ['total_pedidos_calc', 'total_favoritos_calc']
    fieldsets = [
        ('Información Personal', {
            'fields': [
                'nombre', 
                'email',
                'contraseña'
            ]
        }),
        ('Información de Contacto', {
            'fields': [
                'pais',
                'direccion'
            ]
        }),
        ('Estadísticas', {
            'fields': [
                'total_pedidos_calc',
                'total_favoritos_calc'
            ]
        }),
    ]
    list_per_page = 25
    
    def total_pedidos(self, obj):
        return obj.pedido_set.count()
    total_pedidos.short_description = 'Total Pedidos'
    
    def total_favoritos(self, obj):
        return obj.favorito_set.count()
    total_favoritos.short_description = 'Total Favoritos'
    
    def total_pedidos_calc(self, obj):
        return obj.pedido_set.count()
    total_pedidos_calc.short_description = 'Total Pedidos'
    
    def total_favoritos_calc(self, obj):
        return obj.favorito_set.count()
    total_favoritos_calc.short_description = 'Total Favoritos'

# Modelo: Pedido
class PedidoAdmin(admin.ModelAdmin):
    list_display = [
        'id', 
        'cliente', 
        'fecha_creacion', 
        'estado', 
        'total_display',
        'cantidad_items'
    ]
    list_display_links = ['id']
    list_filter = ['estado', 'fecha_creacion']
    search_fields = ['cliente__nombre', 'cliente__email']
    readonly_fields = ['fecha_creacion', 'total_display']
    inlines = [ItemPedidoInline]
    fieldsets = [
        ('Información del Pedido', {
            'fields': [
                'cliente',
                'fecha_creacion',
                'estado',
                'total_display'
            ]
        }),
    ]
    list_per_page = 25
    
    def total_display(self, obj):
        return f"${obj.total}"
    total_display.short_description = 'Total'
    
    def cantidad_items(self, obj):
        return obj.items.count()
    cantidad_items.short_description = 'Items'

# Modelo: ItemPedido
class ItemPedidoAdmin(admin.ModelAdmin):
    list_display = [
        'id', 
        'pedido', 
        'producto', 
        'cantidad', 
        'precio_unitario',
        'subtotal_calc'
    ]
    list_display_links = ['id']
    list_filter = ['pedido__estado']
    search_fields = ['producto__nombre', 'pedido__cliente__nombre']
    readonly_fields = ['subtotal_calc']
    list_per_page = 25
    
    def subtotal_calc(self, obj):
        return f"${obj.cantidad * obj.precio_unitario}"
    subtotal_calc.short_description = 'Subtotal'

# Modelo: Favorito
class FavoritoAdmin(admin.ModelAdmin):
    list_display = [
        'id', 
        'cliente', 
        'producto', 
        'fecha_agregado_display'
    ]
    list_display_links = ['id']
    list_filter = ['fecha_agregado']
    search_fields = [
        'cliente__nombre', 
        'cliente__email', 
        'producto__nombre'
    ]
    readonly_fields = ['fecha_agregado']
    list_per_page = 25
    
    def fecha_agregado_display(self, obj):
        return obj.fecha_agregado.strftime("%d/%m/%Y %H:%M")
    fecha_agregado_display.short_description = 'Fecha Agregado'

# Registro de modelos
admin.site.register(Categoria, CategoriaAdmin)
admin.site.register(Marca, MarcaAdmin)
admin.site.register(Material, MaterialAdmin)
admin.site.register(Producto, ProductoAdmin)
admin.site.register(Usuario, UsuarioAdmin)
admin.site.register(Pedido, PedidoAdmin)
admin.site.register(ItemPedido, ItemPedidoAdmin)
admin.site.register(Favorito, FavoritoAdmin)