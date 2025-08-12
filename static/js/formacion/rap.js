import { reiniciarTooltips,setFormDisabled ,cargarOpciones,crearSelect, showPlaceholder, hidePlaceholder, confirmToast,confirmAction, confirmDialog, confirmDeletion, toastSuccess, toastError, toastWarning, toastInfo, fadeIn, fadeOut, fadeInElement, fadeOutElement, showSpinner, hideSpinner, csrfToken, showSuccessToast, showErrorToast } from '/static/js/utils.js';

document.addEventListener('DOMContentLoaded', () => {

    const tableEl = document.getElementById('raps_table');
    const table = new DataTable(tableEl, {
        language: {
            url: 'https://cdn.datatables.net/plug-ins/2.1.8/i18n/es-ES.json'
        },
        deferRender: true,
        ordering: false,
    });

    cargarDatosTabla();

    async function cargarDatosTabla(){
        try {
            await Promise.all([
                crearSelect({
                    id: 'fase',
                    nombre: 'fases',
                    url: '/api/raps/fases/',
                    placeholderTexto: 'Seleccione una fase',
                    contenedor: '#contenedor-fase'
                }),
                crearSelect({
                    id: 'competencia',
                    nombre: 'competencias',
                    url: '/api/raps/competencias/',
                    placeholderTexto: 'Seleccione una competencia',
                    contenedor: '#contenedor-competencia'
                }),
                crearSelect({
                    id: 'programa',
                    nombre: 'programas',
                    url: '/api/raps/programas/',
                    placeholderTexto: 'Seleccione un programa',
                    contenedor: '#contenedor-programa'
                })
            ]);

            document.querySelectorAll('#fase, #programa, #competencia').forEach(el => {
                el.addEventListener('change', aplicarFiltros);
            })

            const response = await fetch(`/api/formacion/raps/tabla/`);
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
                el.nom,
                el.compe,
                el.programas,
                el.fase,
                `<button class="btn btn-outline-warning btn-sm mb-1 editBtn" 
                    data-id="${el.id}"
                    title="Editar"
                    data-bs-toggle="tooltip" 
                    data-bs-placement="top">
                    <i class="bi bi-pencil-square"></i>
                </button>
                <button class="btn btn-outline-danger btn-sm mb-1 deleteBtn" 
                    data-id="${el.id}"
                    title="Eliminar"
                    data-bs-toggle="tooltip" 
                    data-bs-placement="top">
                    <i class="bi bi-trash"></i>
                </button>`
            ]);
        });

        table.draw();

        document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(el => {
            new bootstrap.Tooltip(el);
        });
    }

    function mostrarPlaceholdersTabla() {
        const tbody = document.querySelector('#raps_table tbody');
        tbody.innerHTML = '';
    
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><span class="placeholder col-10 placeholder-glow placeholder-wave rounded"></span></td>
            <td><span class="placeholder col-8 placeholder-glow placeholder-wave rounded"></span></td>
            <td><span class="placeholder col-6 placeholder-glow placeholder-wave rounded"></span></td>
            <td><span class="placeholder col-6 placeholder-glow placeholder-wave rounded"></span></td>
            <td><span class="placeholder col-4 placeholder-glow placeholder-wave rounded d-block" style="height: 1.5rem;"></span></td>
        `;
        tbody.appendChild(tr);
    }

    //== Filtrar tabla
    async function aplicarFiltros(){
        mostrarPlaceholdersTabla();
        const formData = new FormData(document.getElementById('filtros-form'));
        const params = new URLSearchParams(formData).toString();

        try {
            const response = await fetch(`/api/raps/filtrar/?${params}`);
            const data = await response.json();
            renderTabla(data);
        } catch (error) {
            toastError(error);
        }
    }

    //== Actualizacion del select basado en el programa seleccionado
    document.getElementById('programaSelect').addEventListener('change', async function () {
        const programaId = this.value;
        const compeSelect = document.getElementById('compeSelect');
    
        compeSelect.disabled=true;
        compeSelect.innerHTML = '<option value="">Seleccione una competencia   <span class="spinner-grow spinner-grow-sm" role="status" aria-hidden="true"></span></option>';
    
        if (programaId) {
            try {
                const response = await fetch(`/api/competencias_progra/${programaId}/`);
                if (!response.ok) throw new Error('Error al obtener las competencias');
    
                const data = await response.json();
    
                data.forEach(item => {
                    const option = document.createElement('option');
                    option.value = item.compe__id;
                    option.textContent = item.compe__nom;
                    compeSelect.appendChild(option);
                });
            } catch (error) {
                console.error('Error:', error);
            } finally {
                compeSelect.disabled=false;

            }
        }
    });

    //==Crear RAP
    const formCrearRAP = document.getElementById('formCrearRAP');

    formCrearRAP.addEventListener('submit', async (e) => {
        e.preventDefault();
        const btn = document.getElementById('btnCrearRAP');
        const originalBtnContent = btn.innerHTML;
        const formData = new FormData(formCrearRAP);
        const modal = bootstrap.Modal.getInstance(document.getElementById('crearRAPModal'));

        showSpinner(btn);
        setFormDisabled(formCrearRAP, true)

        try {
            const response = await fetch(`/api/formacion/raps/`, {
                method: 'POST',
                headers: {'X-CSRFToken': csrfToken, 'X-Requested-With': 'XMLHttpRequest'},
                body: formData
            });

            const data = await response.json();

            if (!response.ok){
                let errorMsg = data.message || data.detail || "Ocurrió un error";

                if (data.errors && data.errors.nom) {
                    errorMsg = data.errors.nom.join(', ');
                }

                toastError(errorMsg);
                return;
            }

            toastSuccess(data.message);
            formCrearRAP.reset();

            const faseSelect = document.getElementById('id_fase');
            if (faseSelect && faseSelect.tomselect) {
                faseSelect.tomselect.clear();
            }

            modal.hide();
            aplicarFiltros();
        } catch (error) {
            toastError(error || "Ocurrió un error inesperado");
        } finally {
            hideSpinner(btn, originalBtnContent);
            setFormDisabled(formCrearRAP, false);

            const compeSelect = document.getElementById('compeSelect');
            compeSelect.disabled = true;
            compeSelect.innerHTML = '<option value="">Seleccione una competencia</option>';

        }

    }); 

    //== Boton editar RAP
    tableEl.addEventListener('click', async e => {
        if (e.target.closest('.editBtn')){
            const btn = e.target.closest('.editBtn');
            const originalBtnContent = btn.innerHTML;
            const rapId = btn.dataset.id;
            showSpinner(btn);
            const modalEl = document.getElementById('editarRAPModal');
            const modalInstance = new bootstrap.Modal(modalEl);
            modalInstance.show();

            await cargarDatosEditarRap(rapId);
            hideSpinner(btn, originalBtnContent);
        } else if (e.target.closest('.deleteBtn')){
            const btn = e.target.closest('.deleteBtn');
            const originalBtnContent = btn.innerHTML;
            const rapId = btn.dataset.id;
            showSpinner(btn);

            const confirmed = await confirmDeletion('¿Desea eliminar este RAP?')
            if (confirmed){
                try {
                    const response = await fetch(`/api/formacion/raps/${rapId}/`, {
                        method: 'DELETE',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': csrfToken,
                            'X-Requested-With': 'XMLHttpRequest'
                        }
                    });
                    const data = await response.json();
                    if (!response.ok){
                        let errorMsg = data.message || data.detail || "Ocurrió un error";

                        if (data.errors && data.errors.nom) {
                            errorMsg = data.errors.nom.join(', ');
                        }
                        toastError(errorMsg);
                    } else {
                        toastSuccess(data.message || 'RAP eliminado correctamente');
                        aplicarFiltros();
                    }
                } catch (error) {
                    toastError(error.message)
                }
            }
            hideSpinner(btn, originalBtnContent)
            reiniciarTooltips();
        }
    });

    const formEditarRAP = document.getElementById('formEditarRAP');
    const compeSelect = document.getElementById('compeSelectEdit');
    
    async function cargarDatosEditarRap(rapId) {
        setFormDisabled(formEditarRAP, true);
    
        try {
            const response = await fetch(`/api/formacion/raps/${rapId}/`);
            const data = await response.json();

            if (!response.ok){
                let errorMsg = data.message || data.detail || "Ocurrió un error";

                if (data.errors && data.errors.nom) {
                    errorMsg = data.errors.nom.join(', ');
                }
                toastError(errorMsg);
            } else {
        
                formEditarRAP.querySelector('input[name="nom"]').value = data.nom;

                const programaSelect = document.getElementById('programaSelectEdit');
                const compeSelect = document.getElementById('compeSelectEdit');
                const faseSelect = formEditarRAP.querySelector('select[name="fase"]');

                const programaSeleccionado = data.programas.length > 0 ? data.programas[0].id : '';
                programaSelect.value = programaSeleccionado;

                await cargarCompetenciasPorPrograma(programaSeleccionado);
        
                compeSelect.tomselect.setValue(data.compe);
                faseSelect.tomselect.setValue(data.fase);

                formEditarRAP.setAttribute('action', `/api/formacion/raps/${rapId}/`);
            }
        } catch (error) {
            toastError(error);
        } finally {
            setFormDisabled(formEditarRAP, false);
        }
    }

    //Cargar competencias completas en el modal de edicion
    async function cargarCompetenciasPorPrograma(programaId) {
        const compeSelect = document.getElementById('compeSelectEdit');
        const tomSelectInstance = compeSelect.tomselect;

        tomSelectInstance.clearOptions();
        tomSelectInstance.disable();
        
        try {
            const response = await fetch(`/api/formacion/competencias/?programa=${programaId}`);
            const data = await response.json();
    
            data.forEach(compe => {
                tomSelectInstance.addOption({ value: compe.id, text: compe.nom });
            });

            tomSelectInstance.enable();
    
        } catch (error) {
            toastError('Error al cargar competencias');
        }
    }

    document.getElementById('programaSelectEdit').addEventListener('change', async (e) => {
        const programaId = e.target.value;
        await cargarCompetenciasPorPrograma(programaId);

        // Opcional: limpiar selección competencia cuando cambie programa
        const compeSelect = document.getElementById('compeSelectEdit');
        compeSelect.tomselect.clear(true);
    });

    formEditarRAP.addEventListener('submit', async (e) => {
        e.preventDefault();

        const formData = new FormData(formEditarRAP);
        const jsonData = {
            nom: formData.get('nom'),
            compe: formData.get('compe'),
            fase: formData.getAll('fase')
        };
        console.log("Datos enviados al servidor:", jsonData);

        const btn = document.getElementById('btnEditarRAP');
        const originalBtnContent = btn.innerHTML;

        showSpinner(btn);
    
        setFormDisabled(formEditarRAP, true)

        try {
            const response = await fetch(formEditarRAP.action, {
                method: 'PATCH',
                headers: { 
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify(jsonData)
            });
            const data = await response.json();
    
            if (!response.ok) {
                toastError(data.message);
                return;
            }
    
            toastSuccess(data.message);
    
            const modalEl = document.getElementById('editarRAPModal');
            const modalInstance = bootstrap.Modal.getInstance(modalEl);
            modalInstance.hide();
    
            aplicarFiltros();
        } catch (error) {
            toastError(error);
        } finally {
            setFormDisabled(formEditarRAP, false)
            hideSpinner(btn, originalBtnContent);
            reiniciarTooltips();
        }
    });
    
    
});