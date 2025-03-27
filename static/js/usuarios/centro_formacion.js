import { confirmDeletion, fadeIn, fadeOut, fadeInElement, fadeOutElement, showSpinner, hideSpinner, csrfToken, showSuccessToast, showErrorToast } from '/static/js/utils.js';

document.addEventListener('DOMContentLoaded', () => {

    const form = document.getElementById('formEditarCentro');
    const contenedor = document.getElementById('contenedor');
    let dataTableInstance = null;

    const btnCrearCentro = document.getElementById('btnCrearCentro');
    const formCrearCentro = document.getElementById('formCrearCentro');
    const errorDiv = document.getElementById('errorCrearCentro');

    cargarDatosTabla();

    // ===========Función para llenar tabla ============
    function cargarDatosTabla() {
        const loadingDiv = document.getElementById('loading');
        const userRole = document.body.dataset.userRole;

        fadeIn(loadingDiv);
        fadeOutElement(contenedor);
    
        fetch('/api/centro/')
            .then(response => {
                if (!response.ok) throw new Error('Error al obtener los datos');
                return response.json();
            })
            .then(data => {

                if (dataTableInstance) {
                    dataTableInstance.destroy();
                    dataTableInstance = null;
                }

                const tbody = document.querySelector('#centrosformacion_table tbody');
                tbody.innerHTML = ''; 

                data.data.forEach(centro => {
                    const row = document.createElement('tr');

                    const deleteBtnHTML = (userRole === 'admin') ? `
                        <button 
                            class="delete-btn btn btn-outline-danger btn-sm d-flex justify-content-center align-items-center px-2 ms-1" 
                            data-id="${centro.id}" 
                            title="Eliminar" 
                            data-bs-toggle="tooltip" 
                            data-bs-placement="top">
                            <i class="bi bi-trash3"></i>
                        </button>
                    ` : '';
            
                    row.innerHTML = `
                        <td>${centro.nom}</td>
                        <td>${centro.cod}</td>
                        <td>${centro.depa}</td>
                        <td class="d-flex gap-1">
                            <button 
                                class="edit-btn btn btn-outline-warning btn-sm d-flex justify-content-center align-items-center px-2" 
                                data-id="${centro.id}" 
                                title="Editar" 
                                data-bs-toggle="tooltip" 
                                data-bs-placement="top">
                                <i class="bi bi-pencil-square"></i>
                            </button>
                            ${deleteBtnHTML}
                        </td>
                    `;
            
                    tbody.appendChild(row);
                });
            
                dataTableInstance = new DataTable('#centrosformacion_table', {
                    language: { url: 'https://cdn.datatables.net/plug-ins/2.1.8/i18n/es-ES.json' },
                    deferRender: true
                });
            
                fadeOut(loadingDiv);
                fadeInElement(contenedor);
            
                document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(el => {
                    new bootstrap.Tooltip(el);
                });
            
            })            
            .catch(error => {
                showErrorToast('Error al cargar los datos');
            });
    }
        
    // ========== Botón editar centro de formación ===========
    document.addEventListener('click', (e) => {
        if (e.target.closest('.edit-btn')){
            const btn = e.target.closest('.edit-btn');
            const centroId = btn.dataset.id;
            const url = `/api/centro/${centroId}/`;
            const originalBtnContent = btn.innerHTML;

            showSpinner(btn)
            form.querySelectorAll('input, select, button').forEach(el => el.disabled = true);

            fetch(url)
                .then(response => {
                    if(!response.ok) throw new Error('Error al obtener los datos');
                    return response.json();
                })
                .then(data => {
                    form.querySelector('input[name="nom"]').value = data['centro-nom'];
                    form.querySelector('input[name="cod"]').value = data['centro-codi'];

                    const selectDepa = form.querySelector('select[name="depa"]');
                    selectDepa.value = data['centro-depa'];
                    selectDepa.dispatchEvent(new Event('change'));

                    form.querySelectorAll('input, select, button').forEach(el => el.disabled = false);

                    form.dataset.action = `/api/centro/editar/${centroId}/`;

                    new bootstrap.Modal(document.getElementById('editarCentroModal')).show();
                })
                .catch(error => {
                    showErrorToast(error.error);
                    form.querySelectorAll('input, select, button').forEach(el => el.disabled = false);
                })
                .finally(() => {
                    hideSpinner(btn, originalBtnContent)
                });
        
        }
    })

    // ============= Guardar formulario editar centro
    form.addEventListener('submit', (e) => {
        e.preventDefault();

        const formData = new FormData(form);
        const url = form.dataset.action;

        const submitBtn = form.querySelector('button[type="submit"]');
        const originalBtnContent = submitBtn.innerHTML;
        showSpinner(submitBtn);

        form.querySelectorAll('input, select, button').forEach(el => el.disabled = true);

        fetch(url, {
            method: 'POST',
            headers: { 'X-CSRFToken': csrfToken },
            body: formData
        })
            .then(async response => {
                let data;
                try {
                    data = await response.json();
                } catch (err) {
                    throw { message: 'Respuesta del servidor no es válida.' };
                }
            
                if (!response.ok) {
                    throw data;
                }
            
                return data;
            })
            .then(data => {
                showSuccessToast(data.message)
                bootstrap.Modal.getInstance(document.getElementById('editarCentroModal')).hide();

                if (dataTableInstance) {
                    dataTableInstance.destroy();
                    dataTableInstance = null;
                }

                cargarDatosTabla();

            })
            .catch(error => {
                showErrorToast(error?.message || 'Ocurrió un error al enviar el formulario.');
            })
            .finally(() => {
                hideSpinner(submitBtn, originalBtnContent);
                form.querySelectorAll('input, select, button').forEach(el => el.disabled = false);
            });
    });

    //============ Boton eliminar =============
    document.addEventListener('click', async (e) => {
        if (e.target.closest('.delete-btn')) {
            const btn = e.target.closest('.delete-btn');
            const centroId = btn.dataset.id;

            const confirmed = await confirmDeletion('¿Desea eliminar este centro de formación?');

            if(confirmed){
                fetch(`/api/centro/eliminar/${centroId}/`, {
                    method: 'POST',
                    headers: {'X-CSRFToken': csrfToken}
                })
                .then(response => response.json())
                .then(data => {
                    showSuccessToast(data.message);
                    cargarDatosTabla();
                })
                .catch( error => {
                        showErrorToast(error.message);
                    console.error(error);
                });
            }
        }
    });

    //=============Boton crear==============
    btnCrearCentro.addEventListener('click', () => {
        const formData = new FormData(formCrearCentro);
        const originalBtnContent = btnCrearCentro.innerHTML;

        showSpinner(btnCrearCentro);
        formCrearCentro.querySelectorAll('input, select, button').forEach(el => el.disabled = true);

        fetch('/api/centro/crear/', {
            method : 'POST',
            headers : { 'X-CSRFToken': csrfToken },
            body : formData 
        })
        .then(response => {
            if (!response.ok){
                return response.json().then(data => {
                    throw data;
                })
            }
            return response.json();
        })
        .then(data => {
            bootstrap.Modal.getInstance(document.getElementById('crearCentroModal')).hide();
            showSuccessToast(data.message);
            formCrearCentro.reset();
            cargarDatosTabla();
            errorDiv.innerHTML = '';
        })
        .catch(error => {
            showErrorToast(error.message || 'Ocurrió un error');
            errorDiv.innerHTML = error.errors || '';
        })
        .finally(() => {
            hideSpinner(btnCrearCentro, originalBtnContent);
            formCrearCentro.querySelectorAll('input, select, button').forEach(el => el.disabled = false);
        })
    });

});