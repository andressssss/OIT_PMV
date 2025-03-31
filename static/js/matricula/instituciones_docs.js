import { confirmDeletion, fadeIn, fadeOut, fadeInElement, fadeOutElement, showSpinner, hideSpinner, csrfToken, showSuccessToast, showErrorToast } from '/static/js/utils.js';

document.addEventListener('DOMContentLoaded', () => {

    const uploadBtn = document.querySelector("#upload-btn");
    const btnHistorial = document.getElementById("btn-historial");

    let selectedDocId = null;
    let selectedInstId = null;

    // ======== Modal rechazar documento
    document.querySelectorAll('.reject-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            selectedDocId = btn.dataset.id;
            selectedInstId = btn.dataset.insti;

            const modal = new bootstrap.Modal(document.getElementById('rejectModal'));
            modal.show();
        });
    });

    // Enviar motivo de rechazo al confirmar
    document.getElementById('confirm-reject-btn').addEventListener('click', () => {
        const reason = document.getElementById('reject-reason').value.trim();
        if (!reason) {
            Swal.fire({
                icon: 'warning',
                title: 'Motivo requerido',
                text: 'Por favor, escriba el motivo del rechazo.'
            });
            return;
        }

        fetch(`/api/institucion/rechazar_documento/${selectedDocId}/${selectedInstId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ motivo: reason })
        })
        .then(response => {
            if (!response.ok) throw new Error('Error al enviar el rechazo.');
            return response.json();
        })
        .then(data => {
            Swal.fire({
                icon: 'success',
                title: 'Documento rechazado',
                text: 'El motivo ha sido enviado correctamente.'
            }).then(() => location.reload());
        })
        .catch(err => {
            Swal.fire({
                icon: 'error',
                title: 'Error',
                text: err.message
            });
        });
    });    

    //========= Boton eliminar relacion =======
    document.addEventListener('click', async (e) => {
        if (e.target.closest('.delete-btn')) {
            e.preventDefault();
            
            const btn = e.target.closest('.delete-btn');
            const url = btn.dataset.url;

            const confirmed = await confirmDeletion('¿Desea eliminar este documento?');

            if(confirmed){
            window.location.href = url;
            }
        }
    });
    
    if (uploadBtn) {
        uploadBtn.addEventListener("click", function () {
            const formData = new FormData();
            const institucionId = uploadBtn.dataset.id;
            const originalBtnContent = uploadBtn.innerHTML;

            showSpinner(uploadBtn);

            document.querySelectorAll(".file-input").forEach(function (fileInput) {
                if (fileInput.files.length > 0) {
                    const docName = fileInput.dataset.name;
                    const inputName = fileInput.name;
    
                    formData.append(inputName, fileInput.files[0]);
                    formData.append(inputName + "_name", docName);
                }
            });
    
            fetch(`/api/cargar_documentos_multiples_insti/${institucionId}/`, {
                method: "POST",
                headers: { 'X-CSRFToken': csrfToken },
                body: formData,
            })
            .then(response => response.json())
            .then(data => {
                console.log(data);
                const archivosCargados = data.archivos_cargados || 0;
                const errores = data.errors || [];
    
                if (archivosCargados > 0 && errores.length > 0) {
                    Swal.fire({
                        icon: "warning",
                        title: "Carga parcial",
                        html: `<b>${archivosCargados} archivos cargados correctamente.</b><br><br><b>Errores:</b><br>${errores.join("<br>")}`,
                        confirmButtonText: "Entendido"
                    }).then(() => location.reload());
                } else if (archivosCargados > 0) {
                    Swal.fire({
                        icon: "success",
                        title: "Carga exitosa",
                        text: `${archivosCargados} archivos cargados correctamente.`,
                        confirmButtonText: "Aceptar"
                    }).then(() => location.reload());
                } else {
                    Swal.fire({
                        icon: "error",
                        title: "Error en la carga",
                        html: `<b>${errores.join("<br>")}</b>`,
                        confirmButtonText: "Cerrar"
                    });
                }
            })
            .catch(error => {
                console.error("Error:", error);
                Swal.fire({
                    icon: "error",
                    title: "Error",
                    text: "Error al cargar los archivos.",
                    confirmButtonText: "Cerrar"
                });
            })
            .finally(()=>{
                hideSpinner(uploadBtn, originalBtnContent);
            });
        });
    }

    // ======= Boton historial ========
    btnHistorial.addEventListener("click", function () {
        const institucionId = btnHistorial.getAttribute("data-institucion");
        const historialBody = document.getElementById("historial-body");

        historialBody.innerHTML = '<tr><td colspan="4" class="text-center">Cargando historial...</td></tr>';

        fetch(`/api/institucion/obtener-historial/${institucionId}/`)
            .then(response => response.json())
            .then(data => {
                historialBody.innerHTML = "";

                if (data.historial.length === 0) {
                    historialBody.innerHTML = '<tr><td colspan="4" class="text-center">No hay historial disponible.</td></tr>';
                    return;
                }

                data.historial.forEach(item => {
                    const row = `
                        <tr>
                            <td>${item.usuario}</td>
                            <td>${item.accion}</td>
                            <td>${item.documento}</td>
                            <td>${item.comentario}</td>
                            <td>${new Date(item.fecha).toLocaleString()}</td>
                        </tr>
                    `;
                    historialBody.innerHTML += row;
                });
            })
            .catch(error => {
                console.error("Error al obtener el historial:", error);
                historialBody.innerHTML = '<tr><td colspan="4" class="text-center text-danger">Error al cargar historial.</td></tr>';
            });
    });

    //== indicador de documentos aprobados
    function actualizarContadorDocumentos(nuevoTotal) {
        const contador = document.getElementById("document-counter");
        if (contador) {
            contador.textContent = `${nuevoTotal}/6`;
        }
    }

});
