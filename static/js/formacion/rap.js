import { reiniciarTooltips,cargarOpciones,crearSelect, showPlaceholder, hidePlaceholder, confirmToast,confirmAction, confirmDialog, confirmDeletion, toastSuccess, toastError, toastWarning, toastInfo, fadeIn, fadeOut, fadeInElement, fadeOutElement, showSpinner, hideSpinner, csrfToken, showSuccessToast, showErrorToast } from '/static/js/utils.js';

document.addEventListener('DOMContentLoaded', () => {

    const tableEl = document.getElementById('raps_table');
    const table = new DataTable(tableEl, {
        language: {
            url: 'https://cdn.datatables.net/plug-ins/2.1.8/i18n/es-ES.json'
        },
        deferRender: true,
        ordering: false,
    });

    document.querySelectorAll('.tomselect').forEach(function(select) {
        new TomSelect(select, {
            create: false,
            persist: false,
            maxItems: 1,
        });
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

            const response = await fetch(`/api/raps/filtrar/`);
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
                el.fase,
                el.competencia,
                el.programa,
                `<button class="btn btn-outline-warning btn-sm mb-1 editBtn" 
                    data-id="${el.id}"
                    title="Editar"
                    data-bs-toggle="tooltip" 
                    data-bs-placement="top">
                    <i class="bi bi-pencil-square"></i>
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
        formCrearRAP.querySelectorAll('select, input, button').forEach(el => el.disabled = true);

        try {
            const response = await fetch(`/api/rap/crear/`, {
                method: 'POST',
                headers: {'X-CSRFToken': csrfToken},
                body: formData
            });

            const data = await response.json();
            if (!response.ok){
                toastError(data.message);
                return;
            }
            toastSuccess(data.message);
            formCrearRAP.reset();
            modal.hide();
            aplicarFiltros();
        } catch (error) {
            toastError(error);
        } finally {
            formCrearRAP.querySelectorAll('select, input, button').forEach(el => el.disabled = false);
            hideSpinner(btn, originalBtnContent);
        }

    });

    //== Boton editar RAP
    tableEl.addEventListener('click', async (e) => {
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
        }
    });

    const formEditarRAP = document.getElementById('formEditarRAP');
    const compeSelect = document.getElementById('compeSelectEdit');
    
    async function cargarDatosEditarRap(rapId) {
        formEditarRAP.querySelectorAll('select, button, input').forEach(el =>{
            el.disabled = true;

            if(el.tomselect){
                el.tomselect.disable();
            }
        });
    
        try {
            const response = await fetch(`/api/rap/${rapId}/`);
            const data = await response.json();
    
            formEditarRAP.querySelector('input[name="nom"]').value = data.nom;

            await cargarCompetenciasEdit();
    
            const compeSelect = document.getElementById('compeSelectEdit');
            compeSelect.tomselect.setValue(data.compe);

            formEditarRAP.setAttribute('action', `/api/rap/editar/${rapId}/`);
        } catch (error) {
            toastError(error);
        } finally {
            formEditarRAP.querySelectorAll('select, button, input').forEach(el => {
                el.disabled = false;
                
                if(el.tomselect){
                    el.tomselect.enable();
                }
            });
        }
    }

    //Cargar competencias completas en el modal de edicion
    async function cargarCompetenciasEdit() {
        const compeSelect = document.getElementById('compeSelectEdit');

        const tomSelectInstance = compeSelect.tomselect;

        tomSelectInstance.clearOptions();
        tomSelectInstance.disable();
        
        try {
            const response = await fetch(`/api/competencias/`);
            const data = await response.json();
    
            data.forEach(compe => {
                tomSelectInstance.addOption({ value: compe.id, text: compe.nom });
            });

            tomSelectInstance.enable();
    
        } catch (error) {
            toastError('Error al cargar competencias');
        }
    }



    formEditarRAP.addEventListener('submit', async (e) => {
        e.preventDefault();

        const formData = new FormData(formEditarRAP);
        const dataf = new URLSearchParams(formData).toString();
        const btn = document.getElementById('btnEditarRAP');
        const originalBtnContent = btn.innerHTML;
        showSpinner(btn);
    
        formEditarRAP.querySelectorAll('select, button, input').forEach(el => {
            el.disabled = true;

            if (el.tomselect) {
                el.tomselect.disable();
            }
        });

        try {
            const response = await fetch(formEditarRAP.action, {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: dataf
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
            formEditarRAP.querySelectorAll('select, button, input').forEach(el => {
                el.disabled = false;

                if (el.tomselect){
                    el.tomselect.enable();
                }
            });
            hideSpinner(btn, originalBtnContent);
        }
    });
    
    
});