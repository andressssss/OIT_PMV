import { toastError, toastSuccess, confirmDeletion, confirmAprove, fadeIn, fadeOut, fadeInElement, fadeOutElement, showSpinner, hideSpinner, csrfToken, showSuccessToast, showErrorToast } from '/static/js/utils.js';

document.addEventListener("DOMContentLoaded", function () {

    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    const userRole = document.body.dataset.userRole;

    // Evento para desvincular aprendiz
    document.body.addEventListener("click", function (event) {
        const btn = event.target.closest(".delete-apre-btn");  
        if (!btn) return;

        event.preventDefault();
        const id = btn.getAttribute("data-id");
        const row = btn.closest("tr");

        Swal.fire({
            title: "¿Estás seguro?",
            text: "Esta acción no se puede deshacer.",
            icon: "warning",
            showCancelButton: true,
            confirmButtonColor: "#d33",
            cancelButtonColor: "#3085d6",
            confirmButtonText: "Sí, eliminar",
            cancelButtonText: "Cancelar"
        }).then((result) => {
            if (result.isConfirmed) {
                fetch(`/api/grupo/aprendiz/eliminar/${id}/`, {
                    method: "DELETE",
                    headers: {
                        "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]")?.value || ""
                    }
                })
                .then(response => {
                    if (!response.ok) throw new Error("Error en el servidor");
                    return response.json();
                })
                .then(data => {
                    console.log("Respuesta del servidor:", data);
                    if (data.success) {
                        row.remove();
                        Swal.fire("Eliminado", data.message, "success");
                    } else {
                        Swal.fire("Error", data.message || "No se pudo eliminar el registro.", "error");
                    }
                })
                .catch(error => {
                    console.error("Error al eliminar:", error);
                    Swal.fire("Error", "Ocurrió un problema al eliminar.", "error");
                });
            }
        });
    });


    async function cargarTablaDocumentos(aprendizId) {
        try {
            // Cargar documentos
            const docResponse = await fetch(`/api/prematricula/documentos_aprendiz/${aprendizId}/`);
            const documentos = await docResponse.json();
            
            const docHTML = documentos.map(doc => {
                let estadoTexto = "";
                let accionesHTML = "";
                let archi = "";
    
                switch (doc.vali) {
                    case "0": // No cargado
                        estadoTexto = `<span class="badge bg-secondary">No cargado</span>`;
                        archi = `<span class="text-muted">No cargado</span>`;
                        if (userRole === "gestor") {
                            accionesHTML = `
                                <div class="d-flex gap-2">
                                    <input type="file" class="form-control form-control-sm upload-input" data-doc-id="${doc.id}">
                                    <button class="btn btn-primary btn-sm upload-btn" data-doc-id="${doc.id}" data-aprendiz-id="${aprendizId}">Subir</button>
                                </div>
                            `;
                        }
                        break;
                    case "1": // Cargado
                        estadoTexto = `<span class="badge bg-primary">Cargado</span>`;
                        if (userRole === "gestor") {
                            archi = `<a href="${doc.docu_url}" target="_blank" class="btn btn-sm btn-outline-primary"><i class="bi bi-search"></i></a>
                            <a class="btn btn-sm btn-outline-danger delete-btn" data-doc-id="${doc.id}" data-aprendiz-id="${aprendizId}" data-toggle="tooltip" title="Eliminar archivo"><i class="bi bi-trash"></i></a>`;
                            accionesHTML = `
                                <div class="d-flex gap-2">
                                        <span class="text-muted">
                                        <i class="bi bi-check2-all"></i> Cargado
                                    </span>
                                </div>
                            `;
                        }
                        if (userRole === "lider") {
                            archi = `<a href="${doc.docu_url}" target="_blank" class="btn btn-sm btn-outline-primary"><i class="bi bi-search"></i></a>`;
                            accionesHTML = `
                                <div class="d-flex gap-2">
                                    <button class="btn btn-outline-success btn-sm aprove-btn" data-doc-id="${doc.id}" data-aprendiz-id="${aprendizId}">Aprobar</button>
                                    <button class="btn btn-outline-warning btn-sm reject-btn" data-doc-id="${doc.id}" data-aprendiz-id="${aprendizId}">Rechazar</button>
                                </div>
                            `;
                        }
                        break;
                    case "2": // Rechazado
                        estadoTexto = `<span class="badge bg-danger">Rechazado</span>`;
                        if (userRole === "gestor") {
                            archi = `<a href="${doc.docu_url}" target="_blank" class="btn btn-sm btn-outline-primary"><i class="bi bi-search"></i></a>`;
                            accionesHTML = `
                                <div class="d-flex gap-2">
                                    <input type="file" class="form-control form-control-sm upload-input" data-doc-id="${doc.id}">
                                    <button class="btn btn-primary btn-sm upload-btn" data-doc-id="${doc.id}" data-aprendiz-id="${aprendizId}">Subir</button>
                                </div>
                            `;
                        }
                        if (userRole === "lider") {
                            archi = `<a href="${doc.docu_url}" target="_blank" class="btn btn-sm btn-outline-primary"><i class="bi bi-search"></i></a>`;
                        }
                        break;
                    case "3": // Recargado
                        estadoTexto = `<span class="badge bg-warning">Recargado</span>`;
                        if (userRole === "gestor") {
                            archi = `<a href="${doc.docu_url}" target="_blank" class="btn btn-sm btn-outline-primary"><i class="bi bi-search"></i></a>`;
                            accionesHTML = `
                                <div class="d-flex gap-2">
                                        <span class="text-muted">
                                        <i class="bi bi-lock"></i> No modificable
                                    </span>
                                </div>
                            `;
                        }
                        if (userRole === "lider") {
                            archi = `<a href="${doc.docu_url}" target="_blank" class="btn btn-sm btn-outline-primary"><i class="bi bi-search"></i></a>`;
                            accionesHTML = `
                                <div class="d-flex gap-2">
                                    <button class="btn btn-outline-success btn-sm aprove-btn" data-doc-id="${doc.id}" data-aprendiz-id="${aprendizId}">Aprobar</button>
                                    <button class="btn btn-outline-warning btn-sm reject-btn" data-doc-id="${doc.id}" data-aprendiz-id="${aprendizId}">Rechazar</button>
                                </div>
                            `;
                        }
                        break;
                    case "4": // Aprobado
                        estadoTexto = `<span class="badge bg-success">Aprobado</span>`;
                        archi = `<a href="${doc.docu_url}" target="_blank" class="btn btn-sm btn-outline-primary"><i class="bi bi-search"></i></a>`;
                        if (userRole === "gestor") {
                            accionesHTML = `<span class="text-muted"><i class="bi bi-lock"></i> No modificable</span>`;
                        }
                        if (userRole === "lider") {
                            accionesHTML = `<button class="btn btn-success btn-sm" disabled>Aprobado</button>`;
                        }
                        break;
                    default:
                        estadoTexto = "Desconocido";
                }
    
                return `
                    <tr>
                        <td>${doc.nom}</td>
                        <td>${estadoTexto}</td>
                        <td>${archi}</td>
                        <td>${accionesHTML}</td>
                    </tr>
                `;
            }).join("");
    
            document.getElementById("documentos-body").innerHTML = docHTML || '<tr><td colspan="4" class="text-center">No hay documentos.</td></tr>';
    
        } catch (error) {
            console.error("Error cargando los datos:", error);
            document.getElementById("documentos-body").innerHTML = '<tr><td colspan="4" class="text-center text-danger">Error al cargar documentos.</td></tr>';
        }
    }

    async function cargarTablaHistorial(aprendizId) {
        const tbody = document.getElementById("historial-body");
        tbody.innerHTML = '<tr><td colspan="5" class="text-center">Cargando historial...</td></tr>';
    
        try {
            const response = await fetch(`/api/prematricula/historial_doc_aprendiz/${aprendizId}/`);
            const historial = await response.json();
    
            if (historial.length === 0) {
                tbody.innerHTML = '<tr><td colspan="5" class="text-center">No hay historial disponible.</td></tr>';
                return;
            }
    
            let filasHTML = "";
            historial.forEach(entry => {
                filasHTML += `
                    <tr>
                        <td>${entry.usuario || "Sistema"}</td>
                        <td>${entry.accion}</td>
                        <td>${entry.documento}</td>
                        <td>${entry.comentario || "Sin comentarios"}</td>
                        <td>${new Date(entry.fecha).toLocaleString()}</td>
                    </tr>
                `;
            });
    
            tbody.innerHTML = filasHTML;
        } catch (error) {
            console.error("Error al cargar el historial:", error);
            tbody.innerHTML = '<tr><td colspan="5" class="text-center text-danger">Error al cargar el historial.</td></tr>';
        }
    }
    
    document.querySelectorAll(".ver-documentacion").forEach(button => {
        button.addEventListener("click", function() {
            const aprendizId = this.getAttribute("data-id");
            const aprendizNombre = this.getAttribute("data-nombre");
    
            document.getElementById("documentosModalLabel").textContent = `Documentación de ${aprendizNombre}`;

            document.getElementById("documentos-body").innerHTML = "";  
            document.getElementById("historial-body").innerHTML = "";    

            cargarTablaDocumentos(aprendizId);
            cargarTablaHistorial(aprendizId);
    
            new bootstrap.Modal(document.getElementById("documentosModal")).show();
        });
    });

    async function subirDocumento(docId, aprendizId, inputElement, button) {
        const file = inputElement.files[0];
        if (!file) {
            showErrorToast("Por favor selecciona un archivo antes de subirlo.");
            return;
        }
    
        const formData = new FormData();
        formData.append("documento", file);
        const originalbtn = button.innerHTML;
        showSpinner(button); // 🔹 Mostrar spinner
    
        try {
            const response = await fetch(`/api/prematricula/subir_documento/${docId}/`, {
                method: "POST",
                headers: { 'X-CSRFToken': csrfToken },
                body: formData
            });
    
            let data;
            try {
                data = await response.json();
            } catch (e) {
                throw new Error("Respuesta inválida del servidor.");
            }
    
            if (!response.ok) {
                throw new Error(data.message || "Error desconocido.");
            }
    
            showSuccessToast(data.message);
            
            // Cargar tablas en paralelo
            await Promise.all([
                cargarTablaDocumentos(aprendizId),
                cargarTablaHistorial(aprendizId)
            ]);
    
        } catch (error) {
            console.error("Error al subir el documento:", error);
            showErrorToast(error.message);
        } finally {
            hideSpinner(button, originalbtn); // 🔹 Ocultar spinner
            inputElement.value = "";
        }
    }
    

    async function eliminarDocumento(docId, aprendizId) {
        const confirmed = await confirmDeletion('¿Desea eliminar este documento?');

        if(confirmed){
            fetch(`/api/prematricula/eliminar_documento/${docId}`, {
                method: "DELETE",
                headers: { 'X-CSRFToken': csrfToken }
            })
            .then(response => response.json())
            .then(data => {
                showSuccessToast(data.message);
                cargarTablaDocumentos(aprendizId);
                cargarTablaHistorial(aprendizId);
            })
            .catch(error => {
                showErrorToast(error.message);
            });
        }
    }

    async function aprobarDocumento(docId, aprendizId) {
        const confirmed = await confirmAprove('¿Desea aprobar este documento?');
    
        if (confirmed) {
            fetch(`/api/prematricula/aprobar_documento/${docId}/`, {
                method: "POST",
                headers: { 
                    'X-CSRFToken': csrfToken,
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                showSuccessToast(data.message);
                cargarTablaDocumentos(aprendizId);
                cargarTablaHistorial(aprendizId);
            })
            .catch(error => {
                console.error("Error al aprobar el documento:", error);
                alert("Ocurrió un error al aprobar el documento.");
            });
        }
    }

    function mostrarModalRechazo(docId, aprendizId) {
        console.log("Doc ID:", docId, "Aprendiz ID:", aprendizId); 
        const modalRechazo = new bootstrap.Modal(document.getElementById("modalRechazo"));
        document.getElementById("rejectDocId").value = docId;
        document.getElementById("rejectAprendizId").value = aprendizId;
        modalRechazo.show();
    }

    async function rechazarDocumento() {
        const docId = document.getElementById("rejectDocId").value;
        const aprendizId = document.getElementById("rejectAprendizId").value;
        const comentario = document.getElementById("rejectComment").value.trim();
    
        if (!comentario) {
            showErrorToast("Debe ingresar un comentario para rechazar el documento.");
            return;
        }
    
        fetch(`/api/prematricula/rechazar_documento/${docId}/`, {
            method: "POST",
            headers: { 
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ comentario: comentario })
        })
        .then(response => response.json())
        .then(data => {
            showSuccessToast(data.message);
            cargarTablaDocumentos(aprendizId);
            cargarTablaHistorial(aprendizId);
            bootstrap.Modal.getInstance(document.getElementById("modalRechazo")).hide();

        })
        .catch(error => {
            console.error("Error al rechazar el documento:", error);
            showErrorToast("Ocurrió un error al rechazar el documento.");
        });
    }

    document.getElementById("modalRechazo").addEventListener("hidden.bs.modal", function () {
        document.getElementById("rejectComment").value = "";
        document.getElementById("rejectDocId").value = "";
        document.getElementById("rejectAprendizId").value = "";
    });

    document.addEventListener("click", function (event) {
        const target = event.target;
    
        if (target.closest(".aprove-btn")) {
            const button = target.closest(".aprove-btn");
            const docId = button.getAttribute("data-doc-id");
            const aprendizId = button.getAttribute("data-aprendiz-id");
        
            console.log("Aprendiz ID:", aprendizId);
        
            aprobarDocumento(docId, aprendizId);
        }
    
        if (target.closest(".reject-btn")) {
            const docId = target.getAttribute("data-doc-id");
            const aprendizId = target.getAttribute("data-aprendiz-id");
            mostrarModalRechazo(docId, aprendizId);
        }
    });

    document.getElementById("documentos-body").addEventListener("click", function (event) {
        if (event.target.classList.contains("upload-btn")) {
            const button = event.target;
            const docId = button.getAttribute("data-doc-id");
            const aprendizId = button.getAttribute("data-aprendiz-id");
            const inputElement = button.previousElementSibling; 
    
            subirDocumento(docId, aprendizId, inputElement, button);
        }
    });

    document.addEventListener("click", function (event) {
        const deleteBtn = event.target.closest(".delete-btn"); // Asegura que siempre sea el botón <a>
    
        if (deleteBtn) {
            const docId = deleteBtn.getAttribute("data-doc-id");
            const aprendizId = deleteBtn.getAttribute("data-aprendiz-id"); 
    
            if (!docId || !aprendizId) {
                showErrorToast("Error: No se pudo obtener la información del documento.");
                return;
            }
    
            eliminarDocumento(docId, aprendizId);
        }
    });
    

    document.getElementById("btnRechazar").addEventListener("click", rechazarDocumento);

    //== enviar formulario dividir pdf

    const formpdf = document.getElementById('upload-form');
    
    formpdf.addEventListener('submit', async (e) => {
        e.preventDefault();
    
        const formData = new FormData(formpdf);
        const btn = document.getElementById('btnEnviarPdf');
        const originalBtnContent = btn.innerHTML;
        showSpinner(btn);
        try {
            const response = await fetch(`/dividir_pdf/`, {
                method: 'POST',
                headers: { 'X-CSRFToken': csrfToken },
                body: formData
            });
    
            const data = await response.json();
    
            if (!response.ok) {
                toastError(data.message || "Error al dividir PDF");
                return;
            }
    
            toastSuccess(data.message, data.total_paginas);
            toastSuccess("Paginas: "+ data.total_paginas);
            window.location.href = data.download_url;
            formpdf.reset();
    
        } catch (error) {
            toastError("Error inesperado");
        } finally {
            hideSpinner(btn, originalBtnContent);
        }
    });
    
});