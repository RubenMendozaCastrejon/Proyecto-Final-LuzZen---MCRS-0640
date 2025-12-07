// Función para mostrar mensajes
function mostrarMensaje(mensaje, tipo = 'success') {
    const mensajeDiv = document.createElement('div');
    mensajeDiv.className = `mensaje mensaje-${tipo}`;
    mensajeDiv.innerHTML = `
        ${mensaje}
        <button class="cerrar-mensaje">&times;</button>
    `;
    
    const container = document.querySelector('.mensajes-container') || crearContenedorMensajes();
    container.appendChild(mensajeDiv);
    
    // Auto-eliminar después de 5 segundos
    setTimeout(() => {
        mensajeDiv.remove();
    }, 5000);
}

function crearContenedorMensajes() {
    const container = document.createElement('div');
    container.className = 'mensajes-container';
    document.body.appendChild(container);
    return container;
}

// Favoritos
document.addEventListener('DOMContentLoaded', function() {
    // Botones de favorito
    document.querySelectorAll('.btn-favorito').forEach(btn => {
        btn.addEventListener('click', function() {
            const productoId = this.dataset.producto;
            agregarFavorito(productoId, this);
        });
    });
    
    // Botones de agregar al carrito
    document.querySelectorAll('.btn-carrito').forEach(btn => {
        btn.addEventListener('click', function() {
            const productoId = this.dataset.producto;
            agregarAlCarrito(productoId);
        });
    });
    
    // Botones de cantidad en carrito
    document.querySelectorAll('.btn-cantidad').forEach(btn => {
        btn.addEventListener('click', function() {
            const itemId = this.closest('.carrito-item').dataset.item;
            const accion = this.dataset.accion;
            actualizarCantidadCarrito(itemId, accion);
        });
    });
    
    // Botones de eliminar del carrito
    document.querySelectorAll('.btn-eliminar').forEach(btn => {
        btn.addEventListener('click', function() {
            const itemId = this.dataset.item;
            eliminarDelCarrito(itemId, this.closest('.carrito-item'));
        });
    });
    
    // Cerrar mensajes
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('cerrar-mensaje')) {
            e.target.parentElement.remove();
        }
    });
});

// Función para agregar a favoritos
function agregarFavorito(productoId, boton) {
    fetch(`/favoritos/agregar/${productoId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCSRFToken(),
            'Content-Type': 'application/json',
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            mostrarMensaje(data.message);
            // Cambiar el estilo del botón para indicar que está en favoritos
            boton.style.color = 'red';
            boton.style.fontWeight = 'bold';
        } else {
            mostrarMensaje(data.message, 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        mostrarMensaje('Error al agregar a favoritos', 'error');
    });
}

// Función para agregar al carrito
function agregarAlCarrito(productoId) {
    fetch(`/carrito/agregar/${productoId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCSRFToken(),
            'Content-Type': 'application/json',
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            mostrarMensaje(data.message);
            // Actualizar contador del carrito si existe
            const contador = document.querySelector('.contador-carrito');
            if (contador && data.carrito_count !== undefined) {
                contador.textContent = data.carrito_count;
            }
        } else {
            mostrarMensaje(data.message, 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        mostrarMensaje('Error al agregar al carrito', 'error');
    });
}

// Función para actualizar cantidad en carrito
function actualizarCantidadCarrito(itemId, accion) {
    const formData = new FormData();
    formData.append('accion', accion);
    
    fetch(`/carrito/actualizar/${itemId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCSRFToken(),
        },
        body: formData,
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Actualizar la cantidad en la interfaz
            const item = document.querySelector(`[data-item="${itemId}"]`);
            const cantidadSpan = item.querySelector('.cantidad-actual');
            const subtotalSpan = item.querySelector('.item-total');
            
            if (cantidadSpan) cantidadSpan.textContent = data.nueva_cantidad;
            if (subtotalSpan) subtotalSpan.textContent = `$${data.subtotal}`;
            
            // Recargar la página para actualizar totales (simple)
            setTimeout(() => location.reload(), 500);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        mostrarMensaje('Error al actualizar cantidad', 'error');
    });
}

// Función para eliminar del carrito
function eliminarDelCarrito(itemId, elemento) {
    if (!confirm('¿Estás seguro de que quieres eliminar este producto del carrito?')) {
        return;
    }
    
    fetch(`/carrito/eliminar/${itemId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCSRFToken(),
            'Content-Type': 'application/json',
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            mostrarMensaje(data.message);
            // Eliminar el elemento de la interfaz
            elemento.remove();
            // Recargar para actualizar totales
            setTimeout(() => location.reload(), 1000);
        } else {
            mostrarMensaje(data.message, 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        mostrarMensaje('Error al eliminar del carrito', 'error');
    });
}

// Función para obtener el token CSRF
function getCSRFToken() {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
    return csrfToken ? csrfToken.value : '';
}

// Función para actualizar cantidad en carrito
function actualizarCantidadCarrito(itemId, accion) {
    const formData = new FormData();
    formData.append('accion', accion);
    
    fetch(`/carrito/actualizar/${itemId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCSRFToken(),
        },
        body: formData,
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Actualizar la cantidad en la interfaz
            const item = document.querySelector(`[data-item="${itemId}"]`);
            const cantidadSpan = item.querySelector('.cantidad-actual');
            const subtotalSpan = item.querySelector('.item-total');
            
            if (cantidadSpan) cantidadSpan.textContent = data.nueva_cantidad;
            if (subtotalSpan) subtotalSpan.textContent = `$${(data.nueva_cantidad * parseFloat(subtotalSpan.textContent.replace('$', '') / parseInt(cantidadSpan.textContent))).toFixed(2)}`;
            
            // Recargar la página para actualizar totales
            setTimeout(() => location.reload(), 500);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        mostrarMensaje('Error al actualizar cantidad', 'error');
    });
}