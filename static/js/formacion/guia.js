import { reiniciarTooltips,cargarOpciones,crearSelect, showPlaceholder, hidePlaceholder, confirmToast,confirmAction, confirmDialog, confirmDeletion, toastSuccess, toastError, toastWarning, toastInfo, fadeIn, fadeOut, fadeInElement, fadeOutElement, showSpinner, hideSpinner, csrfToken, showSuccessToast, showErrorToast } from '/static/js/utils.js';

document.addEventListener('DOMContentLoaded', () => {

    //== Crear Guia
    const formCrearGuia = document.getElementById('formCrearGuia');

    formCrearGuia.addEventListener('submit', async (e) => {
        e.preventDefault();
        const btn = document.getElementById('btnCrearGuia');
        const originalBtnContent = btn.innerHTML;
        const formData = new FormData(formCrearGuia);
        const modal = bootstrap.Modal.getInstance(document.getElementById('crearGuiaModal'));

        showSpinner(btn);
        formCrearGuia.querySelectorAll('button, select, input').forEach(el => el.disabled = true);

        try {
            const response = await fetch(`/api/guia/crear/`, {
                method: 'POST',
                headers: { 'X-CSRFToken': csrfToken },
                body: formData
            });

            const data = await response.json();

            if (!response.ok){
                toastError(data.message);
                return;
            }

            toastSuccess(data.message);
            formCrearGuia.reset();
            modal.hide();
            location.reload();
        } catch (error) {
            toastError(error)
        } finally {
            formCrearGuia.querySelectorAll('select, input, button').forEach(el => el.disabled = false);
            hideSpinner(btn, originalBtnContent);
        }
    });

    //== Boton editar guia
    const tableEl = document.getElementById('guias_table');

    tableEl.addEventListener('click', async (e) => {
        if (e.target.closest('.editBtn')){
            const btn = e.target.closest('.editBtn');
            const originalBtnContent = btn.innerHTML;
            const guiaId = btn.dataset.id;
            showSpinner(btn);
            const modalEl = document.getElementById('editarGuiaModal');
            const modalInstance = new bootstrap.Modal(modalEl);
            modalInstance.show();

            await cargarDatosEditarGuia(guiaId);
            hideSpinner(btn, originalBtnContent)
        }
    });

    const formEditarGuia = document.getElementById('formEditarGuia');
    
    //== Poblar formulario de edicion
    async function cargarDatosEditarGuia(guiaId){
        formEditarGuia.querySelectorAll('select, input, button').forEach(el => el.disabled = true);

        try {
            const response = await fetch(`/api/guia/${guiaId}/`);
            const data = await response.json();

            formEditarGuia.querySelector('input[name="nom"]').value = data.nom;
            formEditarGuia.querySelector('input[name="horas_auto"]').value = data.horas_auto;
            formEditarGuia.querySelector('input[name="horas_dire"]').value = data.horas_dire;
            formEditarGuia.querySelector('select[name="progra"]').value = data.progra;

            formEditarGuia.setAttribute('action', `/api/guia/editar/${guiaId}/`);

        } catch (error){
            toastError(error)
        } finally {
            formEditarGuia.querySelectorAll('button, input, select').forEach(el => el.disabled = false );
        }
    };

    formEditarGuia.addEventListener('submit', async (e) => {
        e.preventDefault();

        const formData = new FormData(formEditarGuia);
        const btn = document.getElementById('btnEditarGuia');
        const originalBtnContent = btn.innerHTML;
        showSpinner(btn);

        formEditarGuia.querySelectorAll('select, button, input').forEach(el => el.disabled = true);

        try {
            const response = await fetch(formEditarGuia.action, {
                method: 'POST',
                headers: {'X-CSRFToken': csrfToken},
                body: formData
            });
            const data = await response.json();

            if (!response.ok){
                toastError(data.message);
                if (data.errors) {
                    Object.entries(data.errors).forEach(([field, messages]) => {
                        messages.forEach(msg => toastError(`${field}: ${msg}`));
                    });
                }
                return;
            }

            toastSuccess(data.message);

            const modalEl = document.getElementById('editarGuiaModal');
            const modalInstance = bootstrap.Modal.getInstance(modalEl);
            modalInstance.hide();
            location.reload();
        } catch (error) {
            toastError(error);
        } finally {
            formEditarGuia.querySelectorAll('input, button, select').forEach(el => el.disabled = false);
            hideSpinner(btn, originalBtnContent);
        }
    });

});