import { confirmDeletion, fadeIn, fadeOut, fadeInElement, fadeOutElement, showSpinner, hideSpinner, csrfToken, showSuccessToast, showErrorToast } from '/static/js/utils.js';

document.addEventListener('DOMContentLoaded', () => {

    const formCrear = document.getElementById('formCrearAdministrador');
    const contenedor = document.getElementById('contenedor');
    let dataTableInstance = null;

    const btnCrearAdministrador = document.getElementById('btnCrearAdministrador');
    const formCrearAdministrador = document.getElementById('formCrearAdministrador');
    const errorDiv = document.getElementById('errorCrearAdministrador');
    const formEditarAdministrador = document.getElementById('formEditarAdministrador');

//=============Boton crear==============
    btnCrearAdministrador.addEventListener('click', () => {
        const formData = new FormData(formCrearAdministrador);
        const originalBtnContent = btnCrearAdministrador.innerHTML;

        showSpinner(btnCrearAdministrador);
        formCrearAdministrador.querySelectorAll('input, select, button').forEach(el => el.disabled = true);

        fetch('/api/administrador/crear/', {
            method : 'POST',
            headers : { 'X-CSRFToken': csrfToken, 'X-Requested-With': 'XMLHttpRequest' },
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
            bootstrap.Modal.getInstance(document.getElementById('crearAdministradorModal')).hide();
            showSuccessToast(data.message);
            formCrearAdministrador.reset();
            location.reload();
            errorDiv.innerHTML = '';
        })
        .catch(error => {
            showErrorToast(error.message || 'Ocurrió un error');
            errorDiv.innerHTML = error.errors || '';
        })
        .finally(() => {
            hideSpinner(btnCrearAdministrador, originalBtnContent);
            formCrearAdministrador.querySelectorAll('input, select, button').forEach(el => el.disabled = false);
        })
    });

    // ========== Botón editar centro de formación ===========
    document.addEventListener('click', (e) => {
        if (e.target.closest('.edit-btn')){
            const btn = e.target.closest('.edit-btn');
            const administradorId = btn.dataset.id;
            const originalBtnContent = btn.innerHTML;

            showSpinner(btn);
            formEditarAdministrador.querySelectorAll('input, select, button').forEach(el => el.disabled = true);

            fetch(`/api/administrador/${administradorId}/`)
                .then(response => {
                    if(!response.ok) throw new Error('Error al obtener los datos');
                    return response.json();
                })
                .then(data => {
                    formEditarAdministrador.querySelector('input[name="nom"]').value = data['admin-nom'];
                    formEditarAdministrador.querySelector('input[name="apelli"]').value = data['admin-apelli'];
                    formEditarAdministrador.querySelector('select[name="tipo_dni"]').value = data['admin-tipo_dni'];
                    formEditarAdministrador.querySelector('input[name="dni"]').value = data['admin-dni'];
                    formEditarAdministrador.querySelector('input[name="tele"]').value = data['admin-tele'];
                    formEditarAdministrador.querySelector('input[name="dire"]').value = data['admin-dire'];
                    formEditarAdministrador.querySelector('input[name="mail"]').value = data['admin-mail'];
                    formEditarAdministrador.querySelector('select[name="gene"]').value = data['admin-gene'];
                    formEditarAdministrador.querySelector('input[name="fecha_naci"]').value = data['admin-fecha_naci'];
                    formEditarAdministrador.querySelector('select[name="area"]').value = data['admin-area'];

                    formEditarAdministrador.querySelectorAll('input, select, button').forEach(el => el.disabled = false);

                    formEditarAdministrador.dataset.action = `/api/administrador/editar/${administradorId}/`;

                    new bootstrap.Modal(document.getElementById('editarAdministradorModal')).show();
                })
                .catch(error => {
                    showErrorToast(error.error);
                })
                .finally(() => {
                    formEditarAdministrador.querySelectorAll('input, select, button').forEach(el => el.disabled = false);
                    hideSpinner(btn, originalBtnContent)
                });
        }
    })

    // ============= Guardar formulario editar administrador
    formEditarAdministrador.addEventListener('submit', (e) => {
        e.preventDefault();

        const formData = new FormData(formEditarAdministrador);
        const url = formEditarAdministrador.dataset.action;

        const submitBtn = formEditarAdministrador.querySelector('button[type="submit"]');
        const originalBtnContent = submitBtn.innerHTML;
        showSpinner(submitBtn);

        formEditarAdministrador.querySelectorAll('input, select, button').forEach(el => el.disabled = true);

        fetch(url, {
            method: 'POST',
            headers: { 'X-CSRFToken': csrfToken, 'X-Requested-With': 'XMLHttpRequest' },
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
            })
            .catch(error => {
                showErrorToast(error?.message || 'Ocurrió un error al enviar el formulario.');
            })
            .finally(() => {
                hideSpinner(submitBtn, originalBtnContent);
                formEditarAdministrador.querySelectorAll('input, select, button').forEach(el => el.disabled = false);
                location.reload();
            });
    });

    //============ Boton eliminar =============
    document.addEventListener('click', async (e) => {
        if (e.target.closest('.delete-btn')) {
            const btn = e.target.closest('.delete-btn');
            const administradorId = btn.dataset.id;

            const confirmed = await confirmDeletion('¿Desea eliminar este administrador?');

            if(confirmed){
                fetch(`/api/administrador/eliminar/${administradorId}/`, {
                    method: 'POST',
                    headers: {'X-CSRFToken': csrfToken, 'X-Requested-With': 'XMLHttpRequest'}
                })
                .then(response => response.json())
                .then(data => {
                    showSuccessToast(data.message);
                })
                .catch( error => {
                        showErrorToast(error.message);
                    console.error(error);
                })
                .finally(()=>{
                    location.reload();
                });
            }
        }
    });

});