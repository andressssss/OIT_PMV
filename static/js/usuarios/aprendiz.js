import { confirmDeletion, fadeIn, fadeOut, fadeInElement, fadeOutElement, showSpinner, hideSpinner, csrfToken, showSuccessToast, showErrorToast } from '/static/js/utils.js';

document.addEventListener('DOMContentLoaded', () => {

    const loadingDiv = document.getElementById('loading');
    const tableElement = document.getElementById('aprendices');
    const selectElemento = document.getElementById('ordenar_por');
    const form = document.getElementById('formEditarAprendiz');
    const contenedor = document.getElementById('contenedor')
    cargarDatosTabla();

    // ======= Inicialización de DataTable =======
    const table = new DataTable(tableElement, {
        language: {
            url: 'https://cdn.datatables.net/plug-ins/2.1.8/i18n/es-ES.json',
        },
        deferRender: true,
        ordering: false
    });

    // ======== Funcion para llenar la tabla =========
    function cargarDatosTabla(){
        fadeIn(loadingDiv);
        fadeOutElement(contenedor);

        const promesasSelect2 = [
            cargarOpciones('/api/aprendices/usuarios_crea/', '#usuarios_creacion', 'Creado por'),
            cargarOpciones('/api/aprendices/estados/', '#estados', 'Seleccione un estado')
            
        ];

        const promesaTabla = fetch('/api/aprendices/filtrar-aprendices/')
        .then(response => response.json())
        .then(data => actualizarTabla(data))
        .catch(error => console.error('Error al cargar datos iniciales:', error));

        // =======Iniciar select organizar ========
        new TomSelect(selectElemento,{
            placeholder: 'Ordenar por...',
            allowEmptyOption: true,
            plugins: ['clear_button'],
            controlInput: false,
            render: {
                option_create: null
            }
        });
        
        Promise.all([...promesasSelect2, promesaTabla]).finally(() => {
            fadeOut(loadingDiv);
            fadeInElement(contenedor);
        });
    };

    // ========= Funcion para filtrar la tabla =======
    function aplicarFiltros() {
        fadeIn(loadingDiv)

        const formData = new FormData(document.getElementById('filtros-form'));
        const params = new URLSearchParams(formData).toString();

        fetch(`/api/aprendices/filtrar-aprendices/?${params}`)
            .then(response => response.json())
            .then(data => actualizarTabla(data))
            .catch(error => console.error('Error al filtrar los datos:', error))
            .finally(() => fadeOut(loadingDiv));
    }

    // ======= Cargar opciones dinámicas para filtros =======
    function cargarOpciones(url, elemento, placeholder) {
        fetch(url)
            .then(response => response.json())
            .then(data => {
                const selectElement = document.querySelector(elemento);
                selectElement.innerHTML = '';

                data.forEach(item => {
                    const optionElement = document.createElement('option');
                    optionElement.value = item;
                    optionElement.textContent = item;
                    selectElement.appendChild(optionElement);
                });
                
                new TomSelect(selectElement, {
                    placeholder: placeholder,
                    allowEmptyOption: true,
                    plugins: ['remove_button'],
                    persist: false,
                    create: false,
                    closeAfterSelect: true,
                    sortField: {
                        field: "text",
                        direction: "asc"
                    }
                });
            })
            .catch(error => console.error(`Error al cargar las opciones para ${elemento}`, error));
    }

    // ======= Actualizar tabla con datos =======
    function actualizarTabla(data) {

        table.clear();

        data.forEach(item => {
            table.row.add([
                item.nombre,
                item.apellido,
                item.telefono,
                item.direccion,
                item.mail,
                item.fecha_naci,
                item.estado,
                item.dni,
                `<button class="btn btn-outline-warning btn-sm mb-1 edit-btn" 
                    data-id="${item.id}"
                    title="Editar"
                    data-bs-toggle="tooltip" 
                    data-bs-placement="top">
                    <i class="bi bi-pencil-square"></i>
                </button>
                <button class="btn btn-outline-primary btn-sm mb-1 perfil-btn" 
                    data-id="${item.id}"
                    title="Ver Perfil"
                    data-bs-toggle="tooltip" 
                    data-bs-placement="top">
                    <i class="bi bi-plus-lg"></i>
                </button>`
            ]);
        });

        table.draw();
        document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(el => {
            new bootstrap.Tooltip(el);
        });
    }


    // Aplicar filtros al cambiar
    document.querySelectorAll('#usuarios_creacion, #estados, #ordenar_por, #fecha_creacion').forEach(select => {
        select.addEventListener('change', aplicarFiltros);
    });

    // ======= Botón Editar Aprendiz =======
    document.addEventListener('click', function(e) {
        if (e.target.closest('.edit-btn')){
            const btn = e.target.closest('.edit-btn');
            const aprendizId = btn.dataset.id;

            const modalElement = document.getElementById('editAprendizModal');
            const modalInstance = new bootstrap.Modal(modalElement);
            modalInstance.show();

            cargarDatosEditarAprendiz(aprendizId);
        }
    });

    function cargarDatosEditarAprendiz(aprendizId){

        const url = `/api/aprendiz/${aprendizId}/`;
        const inputs = form.querySelectorAll('input, select, button');

        // Deshabilitar inputs mientras se cargan datos
        inputs.forEach(el => el.disabled = true);

        fetch(url)
            .then(response => response.json())
            .then(data => {
                form.querySelector('input[name="perfil-nom"]').value = data['perfil-nom'];
                form.querySelector('input[name="perfil-apelli"]').value = data['perfil-apelli'];
                form.querySelector('select[name="perfil-tipo_dni"]').value = data['perfil-tipo_dni'];
                form.querySelector('input[name="perfil-dni"]').value = data['perfil-dni'];
                form.querySelector('input[name="perfil-tele"]').value = data['perfil-tele'];
                form.querySelector('input[name="perfil-dire"]').value = data['perfil-dire'];
                form.querySelector('input[name="perfil-mail"]').value = data['perfil-mail'];
                form.querySelector('select[name="perfil-gene"]').value = data['perfil-gene'];
                form.querySelector('input[name="perfil-fecha_naci"]').value = data['perfil-fecha_naci'];
                form.querySelector('input[name="representante-nom"]').value = data['representante-nom'];
                form.querySelector('input[name="representante-dni"]').value = data['representante-dni'];
                form.querySelector('input[name="representante-tele"]').value = data['representante-tele'];
                form.querySelector('input[name="representante-dire"]').value = data['representante-dire'];
                form.querySelector('input[name="representante-mail"]').value = data['representante-mail'];
                form.querySelector('select[name="representante-paren"]').value = data['representante-paren'];

                form.setAttribute('action', `/aprendices/editar/${aprendizId}/`);
            })
            .catch(error => {
                console.error('Error cargando al aprendiz', error);
            })
            .finally(() => {
                inputs.forEach(el => el.disabled = false);
            });
    };

    // ======= Botón Ver Perfil =======
    document.addEventListener('click', function(e){
        const btn = e.target.closest('.perfil-btn');

        if (btn){
            const contenidoPerfil = document.getElementById('contenidoPerfil');
            contenidoPerfil.innerHTML = '<p>Cargando perfil...</p>';
            fadeIn(loadingDiv);
            const aprendizId = btn.dataset.id;

            const modalElement = document.getElementById('modalVerPerfil');
            const modalInstance = new bootstrap.Modal(modalElement);
            modalInstance.show();


            fetch(`/api/aprendices/modal/ver_perfil_aprendiz/${aprendizId}`)
                .then(response => {
                    if (!response.ok){
                        throw new Error('Error en la respuesta del servidor');
                    }
                    return response.text();
                })
                .then(data => {
                    contenidoPerfil.innerHTML=data;
                })
                .catch( error => {
                    console.error('Error al cargar perfil:', error);
                    contenidoPerfil.innerHTML = '<p class="text-danger">Error al cargar el perfil</p>';
                })
                .finally(() => {
                    fadeOut(loadingDiv);
                })


        }
    });

    //======== Guardar formulario editar aprendiz
    form.addEventListener('submit', function (e) {
        e.preventDefault();

        const url = form.action;

        const formData = new FormData(form);
        const data = new URLSearchParams(formData).toString();

        const inputs = form.querySelectorAll('input, select, button');
        inputs.forEach(el => el.disabled = true);

        fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: data
        })
        .then(response => {
            if (!response.ok){
                return response.json().then(error => {throw error});
            }
            return response.json();
        })
        .then(data => {
            showSuccessToast(data.message);

            const modalElement = document.getElementById('editAprendizModal');
            const modalInstance = bootstrap.Modal.getInstance(modalElement);
            modalInstance.hide();
            
            aplicarFiltros();
        })
        .catch(error => {
            showErrorToast(error.message);
        })
        .finally(() => {
            inputs.forEach(el => el.disabled = false)
        });
            
    });

});
