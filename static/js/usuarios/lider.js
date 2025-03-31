import { confirmDeletion, fadeIn, fadeOut, fadeInElement, fadeOutElement, showSpinner, hideSpinner, csrfToken, showSuccessToast, showErrorToast } from '/static/js/utils.js';

document.addEventListener('DOMContentLoaded', ()=>{

    const btnCrearLider = document.getElementById('btnCrearLider');
    const formCrearLider = document.getElementById('formCrearLider');
    const errorDiv = document.getElementById('errorCrearLider');
    const formEditarLider = document.getElementById('formEditarLider');

    //=============Boton crear==============
    btnCrearLider.addEventListener('click', () => {
        const formData = new FormData(formCrearLider);
        const originalBtnContent = btnCrearLider.innerHTML;

        showSpinner(btnCrearLider);
        formCrearLider.querySelectorAll('input, select, button').forEach(el => el.disabled = true);

        fetch('/api/lider/crear/', {
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
            bootstrap.Modal.getInstance(document.getElementById('crearLiderModal')).hide();
            showSuccessToast(data.message);
            formCrearLider.reset();
            errorDiv.innerHTML = '';
            location.reload();
        })
        .catch(error => {
            showErrorToast(error.message || 'Ocurrió un error');
            errorDiv.innerHTML = error.errors || '';
        })
        .finally(() => {
            hideSpinner(btnCrearLider, originalBtnContent);
            formCrearLider.querySelectorAll('input, select, button').forEach(el => el.disabled = false);
        })
    });

    // ========== Botón editar líder ===========
    document.addEventListener('click', (e) => {
        if (e.target.closest('.edit-btn')) {
            const btn = e.target.closest('.edit-btn');
            const liderId = btn.dataset.id;
            const originalBtnContent = btn.innerHTML;

            showSpinner(btn);
            formEditarLider.querySelectorAll('input, select, button').forEach(el => el.disabled = true);

            fetch(`/api/lider/${liderId}/`)
                .then(response => {
                    if (!response.ok) throw new Error('Error al obtener los datos');
                    return response.json();
                })
                .then(data => {
                    formEditarLider.querySelector('input[name="nom"]').value = data['lider-nom'];
                    formEditarLider.querySelector('input[name="apelli"]').value = data['lider-apelli'];
                    formEditarLider.querySelector('select[name="tipo_dni"]').value = data['lider-tipo_dni'];
                    formEditarLider.querySelector('input[name="dni"]').value = data['lider-dni'];
                    formEditarLider.querySelector('input[name="tele"]').value = data['lider-tele'];
                    formEditarLider.querySelector('input[name="dire"]').value = data['lider-dire'];
                    formEditarLider.querySelector('input[name="mail"]').value = data['lider-mail'];
                    formEditarLider.querySelector('select[name="gene"]').value = data['lider-gene'];
                    formEditarLider.querySelector('input[name="fecha_naci"]').value = data['lider-fecha_naci'];

                    formEditarLider.querySelectorAll('input, select, button').forEach(el => el.disabled = false);

                    formEditarLider.dataset.action = `/api/lider/editar/${liderId}/`;

                    new bootstrap.Modal(document.getElementById('editarLiderModal')).show();
                })
                .catch(error => {
                    showErrorToast(error.message || 'Error al obtener los datos del líder.');
                })
                .finally(() => {
                    formEditarLider.querySelectorAll('input, select, button').forEach(el => el.disabled = false);
                    hideSpinner(btn, originalBtnContent);
                });
        }
    });

    // ============= Guardar formulario editar lider
    formEditarLider.addEventListener('submit', (e) => {
        e.preventDefault();

        const formData = new FormData(formEditarLider);
        const url = formEditarLider.dataset.action;

        const submitBtn = formEditarLider.querySelector('button[type="submit"]');
        const originalBtnContent = submitBtn.innerHTML;
        showSpinner(submitBtn);

        formEditarLider.querySelectorAll('input, select, button').forEach(el => el.disabled = true);

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
                location.reload();
            })
            .catch(error => {
                console.log(error)
                showErrorToast(error?.message || 'Ocurrió un error al enviar el formulario.');
                showErrorToast(error?.errors || 'Ocurrió un error al enviar el formulario.');
            })
            .finally(() => {
                hideSpinner(submitBtn, originalBtnContent);
                formEditarLider.querySelectorAll('input, select, button').forEach(el => el.disabled = false);
            });
    });

    //============ Boton eliminar =============
    document.addEventListener('click', async (e) => {
        if (e.target.closest('.delete-btn')) {
            const btn = e.target.closest('.delete-btn');
            const liderId = btn.dataset.id;

            const confirmed = await confirmDeletion('¿Desea eliminar este líder?');

            if(confirmed){
                fetch(`/api/lider/eliminar/${liderId}/`, {
                    method: 'POST',
                    headers: {'X-CSRFToken': csrfToken}
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