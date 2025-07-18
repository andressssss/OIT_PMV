import { setFormDisabled, validarArchivo, reiniciarTooltips, crearSelectForm,crearSelect, confirmToast,confirmAction, confirmDialog, confirmDeletion, toastSuccess, toastError, toastWarning, toastInfo, fadeIn, fadeOut, fadeInElement, fadeOutElement, showSpinner, hideSpinner, csrfToken, showSuccessToast, showErrorToast } from '/static/js/utils.js';


document.addEventListener('DOMContentLoaded', () => {
    const userRole = document.body.dataset.userRole;
    
    const tableEl = document.getElementById('listado_fichas_table');
    const table = new DataTable(tableEl, {
        language: {
            url: 'https://cdn.datatables.net/plug-ins/2.1.8/i18n/es-ES.json'
        },
        deferRender: true,
        ordering: false,
        drawCallback: () => {
            document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(el => {
                new bootstrap.Tooltip(el);
            });
        }
    });

    cargarDatosTabla();

    async function cargarDatosTabla(){
        try {
            await Promise.all([
                crearSelect({
                    id: 'estado',
                    nombre: 'estados',
                    url: '/api/fichas/estados/',
                    placeholderTexto: 'Seleccione un estado',
                    contenedor: '#contenedor-estado'
                }),
                crearSelect({
                    id: 'instructor',
                    nombre: 'instructores',
                    url: '/api/fichas/instructores/',
                    placeholderTexto: 'Seleccione un instructor',
                    contenedor: '#contenedor-instructor'
                }),
                crearSelect({
                    id: 'programa',
                    nombre: 'programas',
                    url: '/api/fichas/programas/',
                    placeholderTexto: 'Seleccione un programa',
                    contenedor: '#contenedor-programa'
                })
            ]);

            document.querySelectorAll('#estado, #instructor, #programa').forEach(el => el.addEventListener('change', aplicarFiltros));

            const response = await fetch(`/api/fichas/filtrar/`);
            const data = await response.json();
            renderTabla(data);
        } catch (error) {
            toastError(error)
        }
    };

    function renderTabla(data){
        table.clear();

        data.forEach(el => {
            table.row.add([
                el.num || 'No registrado',
                el.grupo??'No registrado',
                el.estado,
                el.fecha_aper,
                el.centro,
                el.institucion,
                el.instru??'No asignado',
                el.matricu,
                el.progra,
                `<a class="btn btn-outline-primary btn-sm mb-1" 
                    href="/ficha/${el.id}/"
                    title="Ver ficha"
                    data-bs-toggle="tooltip" 
                    data-bs-placement="top">
                    <i class="bi bi-journals"></i>
                </a>
                <a class="btn btn-outline-warning btn-sm mb-1 btnCambiarNum" 
                    data-id="${el.id}"
                    title="Cambiar numero de ficha"
                    data-bs-toggle="tooltip" 
                    data-bs-placement="top">
                    <i class="bi bi-pencil-square"></i>
                </a>`
            ]);
        });

        table.draw();

    };

    function mostrarPlaceholdersTabla(){
        const tbody = document.querySelector('#listado_fichas_table tbody');
        tbody.innerHTML = '';

        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><span class="placeholder col-10 placeholder-glow placeholder-wave rounded"></span></td>
            <td><span class="placeholder col-8 placeholder-glow placeholder-wave rounded"></span></td>
            <td><span class="placeholder col-6 placeholder-glow placeholder-wave rounded"></span></td>
            <td><span class="placeholder col-6 placeholder-glow placeholder-wave rounded"></span></td>
            <td><span class="placeholder col-6 placeholder-glow placeholder-wave rounded"></span></td>
            <td><span class="placeholder col-6 placeholder-glow placeholder-wave rounded"></span></td>
            <td><span class="placeholder col-6 placeholder-glow placeholder-wave rounded"></span></td>
            <td><span class="placeholder col-6 placeholder-glow placeholder-wave rounded"></span></td>
            <td><span class="placeholder col-6 placeholder-glow placeholder-wave rounded"></span></td>
            <td><span class="placeholder col-4 placeholder-glow placeholder-wave rounded d-block" style="height: 1.5rem;"></span></td>
        `;
        tbody.appendChild(tr);
    };

    async function aplicarFiltros(){
        mostrarPlaceholdersTabla();
        const formData = new FormData(document.getElementById('filtros-form'));
        const params = new URLSearchParams(formData).toString();

        try {
            const response = await fetch(`/api/fichas/filtrar/?${params}`);
            const data = await response.json();
            renderTabla(data);
        } catch (error) {
            toastError(error)
        }
    };

    tableEl.addEventListener('click', e => {
        const btn = e.target.closest('.btnCambiarNum');
        if (btn) {
            const id = btn.getAttribute('data-id');
            const fila = table.row(btn.closest('tr')).data();

            document.getElementById('inputFichaId').value = id;
            document.getElementById('inputNuevoNum').value = fila[0];

            const modal = new bootstrap.Modal(document.getElementById('cambiarNumModal'));
            modal.show();
        }
    });

    document.getElementById('formCambiarNum').addEventListener('submit', async e => {
        e.preventDefault();

        const id = document.getElementById('inputFichaId').value;
        const nuevoNum = document.getElementById('inputNuevoNum').value;
        const formData = new FormData();
        const btn = document.getElementById('btnCambiarNum');
        const originalBtnContent = btn.innerHTML;

        showSpinner(btn);

        formData.append('nuevo_num', nuevoNum);
        
        try {
            const response = await fetch(`/api/ficha/cambiar_num/${id}/`,{
                method: 'POST',
                headers: { 'X-CSRFToken': csrfToken, 'X-Requested-With': 'XMLHttpRequest' },
                body: formData
            });
            const data = await response.json();

            if (!response.ok){
                toastError(data.message);
                return
            }
            toastSuccess(data.message);
            bootstrap.Modal.getInstance(document.getElementById('cambiarNumModal')).hide();
            aplicarFiltros();
        } catch (error) {
            toastError(error)
        } finally {
            hideSpinner(btn, originalBtnContent);
        }
        
    });


    // *******************************************************************
    // *                                                                 *
    // *        ¡ADVERTENCIA! ZONA DE CÓDIGO IMPORTAR FICHAS             *
    // *                                                                 *
    // *******************************************************************

    const formImportarFichas = document.getElementById('formImportarFichas');

    formImportarFichas.addEventListener('submit', async e => {
        e.preventDefault();
        const alertError = document.getElementById('erroresFichas');
        alertError.textContent = '';
        alertError.classList.add('d-none');
        const formData = new FormData(formImportarFichas);
        const btn = document.getElementById('btnImportar');
        const originalBtnContent = btn.innerHTML;

        if (btn.disabled) return;

        const archivoInput = document.getElementById('archivoFichas');
        const archivo = archivoInput.files[0];

        if (!archivo){
            toastError("Debe seleccionar un archivo antes de enviar.");
            return;
        }

        if (!archivo.name.endsWith('.csv')) {
            toastError("Solo se permiten archivos .csv");
            return;
        }

        setFormDisabled(formImportarFichas, true);
        showSpinner(btn);

        try{
            const response = await fetch(`/api/formacion/fichas/importar/`,{
                method: 'POST',
                body: formData,
                headers:{'X-CSRFToken': csrfToken}
            });

            const data  = await response.json();

            if (!response.ok){
                if (data.errores){
                    const alertError = document.getElementById('erroresFichas');
                    alertError.textContent = data.errores.join('\n\n').replace(/\\n/g, '\n');
                    alertError.classList.remove('d-none');
                }
                toastError(data.message || "Error desconocido");
                return;
            }
            
            const resumenFicha = document.getElementById('resumenFichas');

            resumenFicha.innerHTML = `
                <li><strong>Fichas insertadas:</strong> ${data.resumen.insertados}</li>
            `;

            toastSuccess(data.message || 'Carga finalizada');
            formImportarFichas.reset();
            archivoInput.value = '';
        } catch (error){
            console.error(error);
            toastError(error.message || "Error inesperado al conectar con el servidor.");
        }finally{
            setFormDisabled(formImportarFichas, false);
            hideSpinner(btn, originalBtnContent);
        }
    });

    // *******************************************************************
    // *                                                                 *
    // *        ¡ADVERTENCIA! ZONA DE CÓDIGO IMPORTAR FICHAS             *
    // *                                                                 *
    // *******************************************************************

    const formAsignarAprendices = document.getElementById('formAsignarAprendices');

    formAsignarAprendices.addEventListener('submit', async e => {
        e.preventDefault();
        const alertError = document.getElementById('erroresAprendices');
        alertError.textContent = '';
        alertError.classList.add('d-none');
        const formData = new FormData(formAsignarAprendices);
        const btn = document.getElementById('btnAsignar');
        const originalBtnContent = btn.innerHTML; 
    
        if (btn.disabled) return;

        const archivoInput = document.getElementById('archivoAprendices');
        const archivo = archivoInput.files[0];

        if (!archivo){
            toastError("Debe seleccionar un archivo antes de enviar.");
            return;
        }

        if (!archivo.name.endsWith('.csv')) {
            toastError("Solo se permiten archivos .csv");
            return;
        }

        setFormDisabled(formAsignarAprendices, true);
        showSpinner(btn);

                try{
            const response = await fetch(`/api/formacion/fichas/asignar_apre/`,{
                method: 'POST',
                body: formData,
                headers:{'X-CSRFToken': csrfToken}
            });

            const data  = await response.json();

            if (!response.ok){
                if (data.errores){
                    const alertError = document.getElementById('erroresAprendices');
                    alertError.textContent = data.errores.join('\n\n').replace(/\\n/g, '\n');
                    alertError.classList.remove('d-none');
                }
                toastError(data.message || "Error desconocido");
                return;
            }
            
            const resumenAprendices = document.getElementById('resumenAprendices');

            resumenAprendices.innerHTML = `
                <li><strong>Aprendices asignados:</strong> ${data.resumen.insertados}</li>
            `;

            toastSuccess(data.message || 'Carga finalizada');
            formAsignarAprendices.reset();
            archivoInput.value = '';
        } catch (error){
            console.error(error);
            toastError(error.message || "Error inesperado al conectar con el servidor.");
        }finally{
            setFormDisabled(formAsignarAprendices, false);
            hideSpinner(btn, originalBtnContent);
        }
    })

})