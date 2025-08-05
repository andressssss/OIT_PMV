import { confirmDeletion, fadeIn, fadeOut, fadeInElement, fadeOutElement, showSpinner, hideSpinner, csrfToken, showSuccessToast, showErrorToast } from '/static/js/utils.js';

document.addEventListener('DOMContentLoaded', () => {
    const departamentosSelect = document.getElementById("departamentos");
    const departamentosSelectEditar = document.getElementById("departamentosEditar");
    const btnCrearGestor1 = document.getElementById('btnCrearGestor1') 

    const btnCrearGestor = document.getElementById('btnCrearGestor');
    const formCrearGestor = document.getElementById('formCrearGestor');
    const errorDiv = document.getElementById('errorCrearGestor');
    const formEditarGestor = document.getElementById('formEditarGestor');

    //== Cargar departamentos al abrir el modal
    btnCrearGestor1.addEventListener('click', function(){
        if (departamentosSelect.options.length > 0)return;
        formCrearGestor.querySelectorAll('input, button').forEach(el => el.disabled = true);
        departamentosSelect.disabled = true;
        departamentosSelect.innerHTML = `<option disabled selected>Cargando...</option>`; // Mostrar mensaje de carga
    
        fetch("/api/departamentos/")
        .then(response => {
            if (!response.ok) throw new Error("Error al obtener los departamentos");
            return response.json();
        })
        .then(data => {
            departamentosSelect.innerHTML = "";

            data.forEach(departamento => {
                let option = document.createElement("option");
                option.value = departamento.id;
                option.textContent = departamento.nom_departa;
                departamentosSelect.appendChild(option);
            });

            departamentosSelect.disabled = false;
            new TomSelect("#departamentos", {
                plugins: ['remove_button'],
                persist: false,
                create: false,
                placeholder: "Seleccione los departamentos...",
            });
        })
        .catch(error => console.error("Error:", error))
        .finally(()=> {
            formCrearGestor.querySelectorAll('input, button').forEach(el => el.disabled = false);
        });
    });

    //== Boton crear
    btnCrearGestor.addEventListener('click', () => {
        const formData = new FormData(formCrearGestor);
        const originalBtnContent = btnCrearGestor.innerHTML;

        showSpinner(btnCrearGestor);
        formCrearGestor.querySelectorAll('input, select, button').forEach(el => el.disabled = true);

        fetch('/api/gestor/crear/', {
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
            bootstrap.Modal.getInstance(document.getElementById('crearGestorModal')).hide();
            showSuccessToast(data.message);
            formCrearGestor.reset();
            errorDiv.innerHTML = '';
            location.reload();
        })
        .catch(error => {
            showErrorToast(error.message || 'Ocurrió un error');
            errorDiv.innerHTML = error.errors || '';
        })
        .finally(() => {
            hideSpinner(btnCrearGestor, originalBtnContent);
            formCrearGestor.querySelectorAll('input, select, button').forEach(el => el.disabled = false);
        })
    });

    //== Botón editar gestor
    document.addEventListener('click', async (e) => {
        if (e.target.closest('.edit-btn')) {
            const btn = e.target.closest('.edit-btn');
            const gestorId = btn.dataset.id;
            const originalBtnContent = btn.innerHTML;
    
            showSpinner(btn);
            formEditarGestor.querySelectorAll('input, select, button').forEach(el => el.disabled = true);
    
            try {
                // == Obtener datos del gestor
                const response = await fetch(`/api/gestor/${gestorId}/`);
                if (!response.ok) throw new Error('Error al obtener los datos del gestor');
                const data = await response.json();
    
                formEditarGestor.querySelector('input[name="nom"]').value = data['gestor-nom'];
                formEditarGestor.querySelector('input[name="apelli"]').value = data['gestor-apelli'];
                formEditarGestor.querySelector('select[name="tipo_dni"]').value = data['gestor-tipo_dni'];
                formEditarGestor.querySelector('input[name="dni"]').value = data['gestor-dni'];
                formEditarGestor.querySelector('input[name="tele"]').value = data['gestor-tele'];
                formEditarGestor.querySelector('input[name="dire"]').value = data['gestor-dire'];
                formEditarGestor.querySelector('input[name="mail"]').value = data['gestor-mail'];
                formEditarGestor.querySelector('select[name="gene"]').value = data['gestor-gene'];
                formEditarGestor.querySelector('input[name="fecha_naci"]').value = data['gestor-fecha_naci'];
    
                // == Obtener y cargar departamentos
                const departamentosSelect = document.getElementById("departamentosEditar");
                departamentosSelect.innerHTML = ""; // Vaciar select
    
                const departamentosResponse = await fetch("/api/departamentos/");
                if (!departamentosResponse.ok) throw new Error("Error al obtener los departamentos");
    
                const departamentos = await departamentosResponse.json();
                departamentos.forEach(departamento => {
                    let option = document.createElement("option");
                    option.value = departamento.id;
                    option.textContent = departamento.nom_departa;
                    if (data.departamentos?.some(dep => dep.id === departamento.id)) {
                        option.selected = true;
                    }
                    departamentosSelect.appendChild(option);
                });
                departamentosSelect.disabled = false;

                // Verificar si TomSelect ya está inicializado y destruirlo antes de crear uno nuevo
                if (departamentosSelect.tomselect) {
                    departamentosSelect.tomselect.destroy();
                }
                // Inicializar TomSelect
                new TomSelect("#departamentosEditar", {
                    plugins: ['remove_button'],
                    persist: false,
                    create: false,
                    placeholder: "Seleccione los departamentos...",
                });
    
                formEditarGestor.dataset.action = `/api/gestor/editar/${gestorId}/`;
                new bootstrap.Modal(document.getElementById('editarGestorModal')).show();
    
            } catch (error) {
                showErrorToast(error.message || 'Error al obtener los datos del gestor.');
            } finally {
                formEditarGestor.querySelectorAll('input, select, button').forEach(el => el.disabled = false);
                hideSpinner(btn, originalBtnContent);
            }
        }
    });

    //== Guardar formulario editar gestor
    formEditarGestor.addEventListener('submit', async (e) => {
        e.preventDefault();

        const formData = new FormData(formEditarGestor);
        const url = formEditarGestor.dataset.action;
        const submitBtn = formEditarGestor.querySelector('button[type="submit"]');
        const originalBtnContent = submitBtn.innerHTML;

        showSpinner(submitBtn);
        formEditarGestor.querySelectorAll('input, select, button').forEach(el => el.disabled = true);

        try {
            const response = await fetch (url, {
                method: 'POST',
                headers: { 'X-CSRFToken': csrfToken, 'X-Requested-With': 'XMLHttpRequest'},
                body: formData
            });

            let data;
            try {
                data = await response.json();
            }catch (err){
                throw new Error("Respuesta del servidor no valida.");
            }
            if (!response.ok) {
                throw new Error(data.message || "Error desconocido.");
            }
            showSuccessToast(data.message);
            location.reload();
        } catch (error) {
            console.log(error);
            showErrorToast(error.message);
        } finally {
            hideSpinner(submitBtn, originalBtnContent);
            formEditarGestor.querySelectorAll('input, select, button').forEach(el => el.disabled = false);
        }
    });

    
});