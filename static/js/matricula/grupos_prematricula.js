import { confirmDeletion, fadeIn, fadeOut, fadeInElement, fadeOutElement, showSpinner, hideSpinner, csrfToken, showSuccessToast, showErrorToast } from '/static/js/utils.js';

$(document).on('click', '.delete-btn', function () {
    const id = $(this).data('id');
    const row = $(this).parents('tr'); // Guardamos la fila para eliminarla después si es necesario
    
    // Confirmación antes de eliminar
    Swal.fire({
        title: '¿Estás seguro?',
        text: 'Esta acción no se puede deshacer.',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        cancelButtonColor: '#3085d6',
        confirmButtonText: 'Sí, eliminar',
        cancelButtonText: 'Cancelar'
    }).then((result) => {
        if (result.isConfirmed) {
            // Si el usuario confirma, proceder con la eliminación
            fetch(`/api/grupo/eliminar/${id}/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': csrfToken
                }
            })
            .then(response => {
                if (response.ok) {
                    row.remove(); // Elimina la fila de la tabla
                    Swal.fire({
                        icon: 'success',
                        title: 'Eliminado',
                        text: 'El grupo ha sido eliminado correctamente.',
                        timer: 2000,
                        showConfirmButton: false
                    });
                } else {
                    return response.json().then(data => {
                        throw new Error(data.error || 'Error al eliminar el registro.');
                    });
                }
            })
            .catch(error => {
                Swal.fire({
                    icon: 'error',
                    title: 'Error',
                    text: error.message
                });
            });
        }
    });
    });
    
    
document.addEventListener('DOMContentLoaded', function () {
        const botonesConfirmar = document.querySelectorAll('.confirmar-doc');

        botonesConfirmar.forEach(boton => {
            boton.addEventListener('click', function (e) {
                e.preventDefault(); // Prevenir la redirección inmediata
                const url = this.getAttribute('href');

                Swal.fire({
                    title: '¿Está seguro?',
                    text: "Esta acción confirmará toda la documentación del grupo y no se podrá modificar ni eliminar los documentos ni los aprendices asociados.",
                    icon: 'warning',
                    showCancelButton: true,
                    confirmButtonColor: '#28a745',  // Verde
                    cancelButtonColor: '#d33',      // Rojo
                    confirmButtonText: 'Sí, confirmar',
                    cancelButtonText: 'Cancelar'
                }).then((result) => {
                    if (result.isConfirmed) {
                        // Redirigir si el usuario confirma
                        window.location.href = url;
                    }
                });
            });
        });

        //== Boton de formalizacion - abrir modal
        document.querySelectorAll('.formaBtn').forEach(button => {
            button.addEventListener('click', function(e) {
                e.preventDefault();

                const grupoId = this.getAttribute("data-id");
                document.getElementById("grupo-id").value = grupoId;
            })
        });

        //== Enviar solicitud de formalización
        document.getElementById('confirmarFormalizar').addEventListener('click', async function () {
            const grupoId = document.getElementById("grupo-id").value; 
            const numeroFicha = document.getElementById("numeroFicha").value;
        
            if (!grupoId) {
                showErrorToast("Error: No se encontró el ID del grupo.");
                return;
            }
        
            if (!numeroFicha.trim()) {
                showErrorToast("Debe ingresar un número de ficha.");
                return;
            }
        
            console.log("Enviando datos:", { grupo_id: grupoId, numero_ficha: numeroFicha });
        
            try {
                const response = await fetch('/api/formalizar_ficha/', {
                    method: 'POST',
                    headers: {
                        "Content-Type": "application/json",
                        "X-CSRFToken": csrfToken
                    },
                    body: JSON.stringify({ grupo_id: grupoId, numero_ficha: numeroFicha })
                });
        
                const data = await response.json();
                console.log("Respuesta del servidor:", data);
        
                if (data.status === 'success') {
                    showSuccessToast("Ficha formalizada con éxito");
                    location.reload();
                } else {
                    showErrorToast("Error: " + data.message);
                }
            } catch (error) {
                console.error("Error en la solicitud:", error);
                showErrorToast("Ocurrió un error al formalizar la ficha.");
            }
        });
        
});
