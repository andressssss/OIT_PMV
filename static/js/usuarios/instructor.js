import { confirmDeletion,toastSuccess, toastError, fadeIn, fadeOut, fadeInElement, fadeOutElement, showSpinner, hideSpinner, csrfToken, showSuccessToast, showErrorToast } from '/static/js/utils.js';
document.addEventListener('DOMContentLoaded', () => {

    const btnCrearInstructor = document.getElementById('btnCrearInstructor');
    const formCrearInstructor = document.getElementById('formCrearInstructor');
    const errorDiv = document.getElementById('errorCrearInstructor');

    const tabla = document.getElementById('instructores');
    const formEditar = document.getElementById('formEditarInstructor');

    const modalElement = document.getElementById('editarInstructorModal');
    const modalInstance = new bootstrap.Modal(modalElement);

    modalElement.addEventListener('hidden.bs.modal', () => {
        document.getElementById('btnCrearInstructorModal').focus();
    });

    document.querySelectorAll('.tomselect').forEach(function(select) {
        new TomSelect(select, {
            create: false,
            persist: false,
            maxItems: null,
            plugins: ['remove_button'],
            allowEmptyOption: true,
        });
    });

    //== Boton crear
    formCrearInstructor.addEventListener('submit', async function (e) {
        e.preventDefault();
    
        const formData = new FormData(formCrearInstructor);
        const originalBtnContent = btnCrearInstructor.innerHTML;
    
        showSpinner(btnCrearInstructor);
    
        formCrearInstructor.querySelectorAll('input, select, button').forEach(el => el.disabled = true);
    
        try {
            const response = await fetch('/api/instructor/crear/', {
                method: 'POST',
                headers: { 'X-CSRFToken': csrfToken },
                body: formData
            });
    
            const data = await response.json();
    
            if (!response.ok) {
                throw data;
            }
    
            bootstrap.Modal.getInstance(document.getElementById('crearInstructorModal')).hide();
            showSuccessToast(data.message);
            formCrearInstructor.reset();
            errorDiv.innerHTML = '';
            location.reload();
    
        } catch (error) {
            console.log(error)
            showErrorToast(error.message || 'Ocurrió un error');
            errorDiv.innerHTML = error.errors || '';
        } finally {
            hideSpinner(btnCrearInstructor, originalBtnContent);
            formCrearInstructor.querySelectorAll('input, select, button').forEach(el => el.disabled = false);
        }
    });

    const programaSelect = document.getElementById('programaSelect');
    const fichaSelect = document.getElementById('fichaSelect');
    const fichaTomSelect = fichaSelect.tomselect;

    programaSelect.addEventListener('change', async e =>{
        const programaId = programaSelect.value;

        fichaTomSelect.clear();
        fichaTomSelect.clearOptions()

        if (!programaId) {
            fichaSelect.disabled = true;
            return;
        }

        try {
            const response = await fetch(`/api/formacion/fichas/por_programa/${programaId}/`);
            if (!response.ok) throw new Error('Error al cargar las fichas');
            const fichas = await response.json();

            if(fichas.length == 0){
                fichaTomSelect.disable();
            } else {
                fichaTomSelect.enable();
                fichas.forEach(f => {
                    fichaTomSelect.addOption({ value: f.id, text: f.num});
                })
                fichaTomSelect.refreshOptions();
            }
        } catch (error) {
            toastError(error)
        }
    })

    //== Boton editar
    tabla.addEventListener('click', async (e) => {
        const btn = e.target.closest('.edit-btn');
        if (btn) {
            tabla.querySelectorAll('button').forEach(el => el.disabled = true);
            const instructorId = btn.dataset.id;
            const originalBtnContent = btn.innerHTML;
            showSpinner(btn);
            try {
                const response = await fetch(`/api/instructor/${instructorId}/`);
                if (response.ok) {
                    const data = await response.json();

                    modalInstance.show();

                    formEditar.querySelector('#editarInstructorId').value = data.id;
                    formEditar.querySelector('#id_nom').value = data.perfil.nom;
                    formEditar.querySelector('#id_apelli').value = data.perfil.apelli;
                    formEditar.querySelector('#id_tipo_dni').value = data.perfil.tipo_dni;
                    formEditar.querySelector('#id_dni').value = data.perfil.dni;
                    formEditar.querySelector('#id_tele').value = data.perfil.tele;
                    formEditar.querySelector('#id_dire').value = data.perfil.dire;
                    formEditar.querySelector('#id_mail').value = data.perfil.mail;
                    formEditar.querySelector('#id_gene').value = data.perfil.gene;
                    formEditar.querySelector('#id_fecha_naci').value = data.perfil.fecha_naci || '';
                    formEditar.querySelector('#id_contra').value = data.contra ?? '';
                    formEditar.querySelector('#id_profe').value = data.profe ?? '';
                    formEditar.querySelector('#id_fecha_ini').value = data.fecha_ini || '';
                    formEditar.querySelector('#id_fecha_fin').value = data.fecha_fin || '';
                    formEditar.querySelector('#id_tipo_vincu').value = data.tipo_vincu ?? '';

                    const fichaSelect = formEditar.querySelector('#editarFichaSelect');
                    const tomSelectInstance = fichaSelect.tomselect;
                    
                    const fichaIds = data.fichas.map(f => f.id.toString());
                    tomSelectInstance.setValue(fichaIds);

                    formEditar.setAttribute('action', `/api/instructor/editar/${instructorId}/`);

                }
            } catch (error) {
                console.error('Error al obtener los datos del instructor:', error);
                alert('Hubo un problema al cargar los datos del instructor.');
            } finally {
                hideSpinner(btn, originalBtnContent);
                tabla.querySelectorAll('button').forEach(el => el.disabled = false);
            }
        }
    });

    //== Boton guardar formulario editar instructor
    formEditar.addEventListener('submit', async e => {
        e.preventDefault();
    
        const url = formEditar.action;
        const formData = new FormData(formEditar);
        const data = new URLSearchParams(formData).toString();
    
        const inputs = formEditar.querySelectorAll('input, select, button');
        inputs.forEach(el => el.disabled = true);

        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                body: data
            });

            const result = await response.json();
    
            if (!response.ok) {
                throw new Error(result.message || 'Ocurrió un error desconocido');
            }
    
            toastSuccess(result.message);
            modalInstance.hide();
            location.reload();
    
        } catch (error) {
            // Aquí sí funcionará error.message
            showErrorToast(error.message);
        } finally {
            inputs.forEach(el => el.disabled = false);
        }
    });
});