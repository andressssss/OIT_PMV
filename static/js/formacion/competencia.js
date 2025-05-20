import { reiniciarTooltips,cargarOpciones,crearSelect, showPlaceholder, hidePlaceholder, confirmToast,confirmAction, confirmDialog, confirmDeletion, toastSuccess, toastError, toastWarning, toastInfo, fadeIn, fadeOut, fadeInElement, fadeOutElement, showSpinner, hideSpinner, csrfToken, showSuccessToast, showErrorToast } from '/static/js/utils.js';

document.addEventListener('DOMContentLoaded', () => {

    const tableEl = document.getElementById('competencias_table');
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
            maxItems: null,
            plugins: ['remove_button']
        });
    });

    cargarDatosTabla();

    //== Carga inicial a la tabla
    async function cargarDatosTabla(){
        try {
            await Promise.all([
                crearSelect({
                    id: 'fase',
                    nombre: 'fases',
                    url: '/api/competencias/fases/',
                    placeholderTexto: 'Seleccione una fase',
                    contenedor: '#contenedor-fase'
                }),
                crearSelect({
                    id: 'programa',
                    nombre: 'programas',
                    url: '/api/competencias/programas/',
                    placeholderTexto: 'Seleccione un programa',
                    contenedor: '#contenedor-programa'
                })
            ]);
            
            document.querySelectorAll('#fase, #programa').forEach(el => {
                el.addEventListener('change', aplicarFiltros);
            })

            const response = await fetch('/api/competencias/filtrar/');
            const data = await response.json();
            renderTabla(data);

        } catch (error) {
            toastError(error)
        }
    };

    //== renderizar tabla
    function renderTabla(data) {
        table.clear();
        
        const nombresFase = {
            'analisis': 'Análisis',
            'ejecucion': 'Ejecución',
            'planeacion': 'Planeación',
            'evaluacion': 'Evaluación'
        };

        data.forEach(item => {
            const listaProgramas = `<ul class="lista-estilo">${item.progra.map(p => `<li><i class="bi bi-dot"></i> ${p}</li>`).join('')}</ul>`;
            const listaFases = `<ul class="lista-estilo">${item.fase.map(f => `<li><i class="bi bi-dot"></i> ${nombresFase[f] || f}</li>`).join('')}</ul>`;
    
            table.row.add([
                item.nom,
                listaProgramas,
                listaFases,
                `<button class="btn btn-outline-warning btn-sm mb-1 editBtn" 
                    data-id="${item.id}"
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
        const tbody = document.querySelector('#competencias_table tbody');
        tbody.innerHTML = '';
    
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><span class="placeholder col-10 placeholder-glow placeholder-wave rounded"></span></td>
            <td><span class="placeholder col-8 placeholder-glow placeholder-wave rounded"></span></td>
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
            const response = await fetch(`/api/competencias/filtrar/?${params}`);
            const data = await response.json();
            renderTabla(data);
        } catch (error) {
            toastError(error);
        }
    }


    //== Crear competencia
    const formCrearCompetencia = document.getElementById('formCrearCompetencia');

    formCrearCompetencia.addEventListener('submit', async (e) => {
        e.preventDefault();
        const btn = document.getElementById('btnCrearCompetencia');
        const originalBtnContent = btn.innerHTML;
        const formData = new FormData(formCrearCompetencia);
        const modal = bootstrap.Modal.getInstance(document.getElementById('crearCompetenciaModal'));

        showSpinner(btn);
        formCrearCompetencia.querySelectorAll('select, button, input').forEach(el => {
            el.disabled = true;
        
            if (el.tomselect) {
                el.tomselect.disable();
            }
        });
        try {
            const response = await fetch(`/api/competencia/crear/`, {
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
            formCrearCompetencia.reset();
            modal.hide();
            aplicarFiltros();
        } catch (error) {
            toastError(error)
        } finally {
            hideSpinner(btn, originalBtnContent);
            formCrearCompetencia.querySelectorAll('select, button, input').forEach(el => {
                el.disabled = false;
            
                if (el.tomselect) {
                    el.tomselect.enable();
                }
            });
        }
    });

    //== Boton editar competencia
    tableEl.addEventListener('click', async (e) => {
        if (e.target.closest('.editBtn')){
            const btn = e.target.closest('.editBtn');
            const originalBtnContent = btn.innerHTML;
            const competenciaId = btn.dataset.id;
            showSpinner(btn);
            const modalEl = document.getElementById('editarCompetenciaModal');
            const modalInstance = new bootstrap.Modal(modalEl);
            modalInstance.show();

            await cargarDatosEditarCompetencia(competenciaId);
            hideSpinner(btn, originalBtnContent);
        }
    });

    const formEditarCompetencia = document.getElementById('formEditarCompetencia'); 

    async function cargarDatosEditarCompetencia(competenciaId) {
        formEditarCompetencia.querySelectorAll('select, button, input').forEach(el => {
            el.disabled = true;
        
            if (el.tomselect) {
                el.tomselect.disable();
            }
        });
    
        try {
            const response = await fetch(`/api/competencia/${competenciaId}/`);
            const data = await response.json();
    
            formEditarCompetencia.querySelector('input[name="nom"]').value = data['nom'];
    
            // Asignar valores múltiples al select con TomSelect
            const prograSelect = formEditarCompetencia.querySelector('select[name="progra"]');
            const faseSelect = formEditarCompetencia.querySelector('select[name="fase"]');
    
            if (prograSelect.tomselect) {
                prograSelect.tomselect.setValue(data['progra']);
            } else {
                prograSelect.value = data['progra'][0];
            }
    
            if (faseSelect.tomselect) {
                faseSelect.tomselect.setValue(data['fase']);
            } else {
                faseSelect.value = data['fase'][0];
            }
    
            formEditarCompetencia.setAttribute('action', `/api/competencia/editar/${competenciaId}/`);
        } catch (error) {
            toastError(error);
        } finally {
            formEditarCompetencia.querySelectorAll('select, button, input').forEach(el => {
                el.disabled = false;
            
                if (el.tomselect) {
                    el.tomselect.enable();
                }
            });
        }
    }
    

    //== Guardar formulario editar competencia
    formEditarCompetencia.addEventListener('submit', async (e) => {
        e.preventDefault();

        const formData = new FormData(formEditarCompetencia);
        const dataf = new URLSearchParams(formData).toString();
        const btn = document.getElementById('btnEditarCompetencia');
        const originalBtnContent = btn.innerHTML;
        showSpinner(btn);

        formEditarCompetencia.querySelectorAll('select, button, input').forEach(el => {
            el.disabled = true;
        
            if (el.tomselect) {
                el.tomselect.disable();
            }
        });

        try {
            const response = await fetch(formEditarCompetencia.action, {
                method: 'POST',
                headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                body: dataf
            });
            const data = await response.json();
            if(!response.ok){
                toastError(data.message);
                return;
            }

            toastSuccess(data.message);

            const modalEl = document.getElementById('editarCompetenciaModal');
            const modalInstance = bootstrap.Modal.getInstance(modalEl);
            modalInstance.hide();

            aplicarFiltros();

        } catch (error) {
            toastError(error)
        } finally {
            formEditarCompetencia.querySelectorAll('select, button, input').forEach(el => {
                el.disabled = false;
            
                if (el.tomselect) {
                    el.tomselect.enable();  // vuelve a habilitar la UI de TomSelect
                }
            });
            hideSpinner(btn, originalBtnContent);
        }

    });
});