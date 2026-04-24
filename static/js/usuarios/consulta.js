import { confirmDeletion, showSpinner, hideSpinner, csrfToken, showSuccessToast, showErrorToast } from '/static/js/utils.js';

document.addEventListener('DOMContentLoaded', () => {

    const btnCrear = document.getElementById('btnCrearConsulta');
    const formCrear = document.getElementById('formCrearConsulta');
    const errorCrear = document.getElementById('errorCrearConsulta');
    const formEditar = document.getElementById('formEditarConsulta');

    // ========== Crear ==========
    btnCrear.addEventListener('click', () => {
        const formData = new FormData(formCrear);
        const originalContent = btnCrear.innerHTML;

        showSpinner(btnCrear);
        formCrear.querySelectorAll('input, select, button').forEach(el => el.disabled = true);

        fetch('/api/consulta/crear/', {
            method: 'POST',
            headers: { 'X-CSRFToken': csrfToken, 'X-Requested-With': 'XMLHttpRequest' },
            body: formData,
        })
        .then(response => {
            if (!response.ok) return response.json().then(data => { throw data; });
            return response.json();
        })
        .then(data => {
            bootstrap.Modal.getInstance(document.getElementById('crearConsultaModal')).hide();
            showSuccessToast(data.message);
            formCrear.reset();
            errorCrear.innerHTML = '';
            location.reload();
        })
        .catch(error => {
            showErrorToast(error.message || 'Ocurrió un error');
            errorCrear.innerHTML = error.errors || '';
        })
        .finally(() => {
            hideSpinner(btnCrear, originalContent);
            formCrear.querySelectorAll('input, select, button').forEach(el => el.disabled = false);
        });
    });

    // ========== Editar — cargar datos ==========
    document.addEventListener('click', (e) => {
        if (e.target.closest('.edit-btn')) {
            const btn = e.target.closest('.edit-btn');
            const consultaId = btn.dataset.id;
            const originalContent = btn.innerHTML;

            showSpinner(btn);
            formEditar.querySelectorAll('input, select, button').forEach(el => el.disabled = true);

            fetch(`/api/consulta/${consultaId}/`)
                .then(response => {
                    if (!response.ok) throw new Error('Error al obtener los datos');
                    return response.json();
                })
                .then(data => {
                    formEditar.querySelector('input[name="nom"]').value           = data['consulta-nom'];
                    formEditar.querySelector('input[name="apelli"]').value        = data['consulta-apelli'];
                    formEditar.querySelector('select[name="tipo_dni"]').value     = data['consulta-tipo_dni'];
                    formEditar.querySelector('input[name="dni"]').value           = data['consulta-dni'];
                    formEditar.querySelector('input[name="tele"]').value          = data['consulta-tele'];
                    formEditar.querySelector('input[name="dire"]').value          = data['consulta-dire'];
                    formEditar.querySelector('input[name="mail"]').value          = data['consulta-mail'];
                    formEditar.querySelector('select[name="gene"]').value         = data['consulta-gene'];
                    formEditar.querySelector('input[name="fecha_naci"]').value    = data['consulta-fecha_naci'];
                    formEditar.querySelector('select[name="area"]').value         = data['consulta-area'];
                    formEditar.querySelector('select[name="nivel_acceso"]').value = data['consulta-nivel_acceso'];
                    formEditar.querySelector('select[name="esta"]').value         = data['consulta-esta'];

                    formEditar.querySelectorAll('input, select, button').forEach(el => el.disabled = false);
                    formEditar.dataset.action = `/api/consulta/editar/${consultaId}/`;
                    new bootstrap.Modal(document.getElementById('editarConsultaModal')).show();
                })
                .catch(error => {
                    showErrorToast(error.message || 'Error al cargar datos');
                })
                .finally(() => {
                    hideSpinner(btn, originalContent);
                    formEditar.querySelectorAll('input, select, button').forEach(el => el.disabled = false);
                });
        }
    });

    // ========== Editar — guardar ==========
    formEditar.addEventListener('submit', (e) => {
        e.preventDefault();
        const formData = new FormData(formEditar);
        const url = formEditar.dataset.action;
        const submitBtn = formEditar.querySelector('button[type="submit"]');
        const originalContent = submitBtn.innerHTML;

        showSpinner(submitBtn);
        formEditar.querySelectorAll('input, select, button').forEach(el => el.disabled = true);

        fetch(url, {
            method: 'POST',
            headers: { 'X-CSRFToken': csrfToken, 'X-Requested-With': 'XMLHttpRequest' },
            body: formData,
        })
        .then(async response => {
            let data;
            try { data = await response.json(); } catch { throw { message: 'Respuesta no válida.' }; }
            if (!response.ok) throw data;
            return data;
        })
        .then(data => {
            showSuccessToast(data.message);
        })
        .catch(error => {
            showErrorToast(error?.message || 'Ocurrió un error al actualizar.');
        })
        .finally(() => {
            hideSpinner(submitBtn, originalContent);
            formEditar.querySelectorAll('input, select, button').forEach(el => el.disabled = false);
            location.reload();
        });
    });

    // ========== Eliminar ==========
    document.addEventListener('click', async (e) => {
        if (e.target.closest('.delete-btn')) {
            const btn = e.target.closest('.delete-btn');
            const consultaId = btn.dataset.id;

            const confirmed = await confirmDeletion('¿Desea eliminar este usuario de consulta?');
            if (confirmed) {
                fetch(`/api/consulta/eliminar/${consultaId}/`, {
                    method: 'POST',
                    headers: { 'X-CSRFToken': csrfToken, 'X-Requested-With': 'XMLHttpRequest' },
                })
                .then(response => response.json())
                .then(data => { showSuccessToast(data.message); })
                .catch(error => { showErrorToast(error.message); })
                .finally(() => { location.reload(); });
            }
        }
    });

});
