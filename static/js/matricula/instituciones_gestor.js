import { confirmDeletion, fadeIn, fadeOut, fadeInElement, fadeOutElement, showSpinner, hideSpinner, csrfToken, showSuccessToast, showErrorToast } from '/static/js/utils.js';

document.addEventListener('DOMContentLoaded', () => {

    const loadingDiv = document.getElementById('loading');
    const tableElement = document.getElementById('instituciones_gestor');
    const contenedor = document.getElementById('contenedor');

    cargarDatosTabla();

    // Inicializa DataTable
    const table = new DataTable(tableElement, {
        language: {
            url: 'https://cdn.datatables.net/plug-ins/2.1.8/i18n/es-ES.json',
        },
        deferRender: true,
    });

    function cargarDatosTabla(){
        fadeIn(loadingDiv);
        fadeOut(contenedor);

        const promesasSelect2 = [
            cargarOpciones('/api/municipios/', '#municipios_filtro', 'Seleccione un municipio'),
            cargarOpciones('/api/estados/', '#estados_filtro', 'Seleccione un estado'),
            cargarOpciones('/api/sectores/', '#sectores_filtro', 'Seleccione un sector')
        ];

        const promesaTabla = fetch('/api/institucion/filtrar_instituciones_gestor/')
        .then(response => response.json())
        .then(data => actualizarTabla(data))
        .catch(error => console.error('Error al cargar datos iniciales:', error));

        Promise.all([...promesasSelect2, promesaTabla]).finally(() => {
            fadeOut(loadingDiv);
            fadeInElement(contenedor);
        });
    };

    function cargarOpciones(url, elemento, placeholder) {
        return fetch(url)
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

                if (selectElement.tomselect){
                    selectElement.tomselect.destroy();
                }

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
            .catch(error => console.error(`Error al cargar opciones para ${elemento}:`, error));
    }

    
    function actualizarTabla(data) {
        table.clear(); 

        var rolUsuario = tableElement.getAttribute('data-rol');
        data.forEach(item => {
            let fila = [
                item.nombre,
                item.municipio,
                item.departamento,
                item.sector,
                item.estado,
                item.dane,
                //item.genero === 'mi' ? 'Mixto' : item.zona === 'ma' ? 'Masculino': item.zona === 'fe' ? 'Femenino' : 'No asignado',
                item.zona === 'u' ? 'Urbana' : item.zona === 'r' ? 'Rural' : 'No asignado',
                item.estado_docu
            ];

            if (rolUsuario === 'lider'){
                fila.push(item.gestor)
            }

            // Agregar botones de acción
            fila.push(`
                <a class="btn btn-outline-warning mb-1 btn-sm" title="Ver detalle" href="${item.detalle_url}" data-bs-toggle="tooltip" data-bs-placement="top">
                    <i class="bi bi-plus-lg"></i>
                </a>
                <button class="btn btn-outline-danger btn-sm mb-1 delete-btn" data-id="${item.id}" title="Eliminar" data-bs-toggle="tooltip" data-bs-placement="top">
                    <i class="bi bi-trash3"></i>
                </button>
            `);

            table.row.add(fila)
        });

        table.draw(); 
        document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(el => {
            new bootstrap.Tooltip(el);
        });
    }

    // ========= Funcion para filtrar la tabla =======
    function aplicarFiltros() {
        fadeIn(loadingDiv)

        const formData = new FormData(document.getElementById('filtros-form'));
        const params = new URLSearchParams(formData).toString();

        fetch(`/api/institucion/filtrar_instituciones_gestor/?${params}`)
            .then(response => response.json())
            .then(data => actualizarTabla(data))
            .catch(error => console.error('Error al filtrar los datos:', error))
            .finally(() => fadeOut(loadingDiv));
    }

    // Aplicar filtros al cambiar
    document.querySelectorAll('#municipios_filtro, #estados_filtro, #sectores_filtro').forEach(select => {
        select.addEventListener('change', aplicarFiltros);
    });

    // =================== Boton eliminar relacion de institucion
    document.addEventListener('click', async (e) => {
        if (e.target.closest('.delete-btn')){
            const btn = e.target.closest('.delete-btn');
            const gestorInstiId = btn.dataset.id;

            const originalBtnContent = btn.innerHTML;

            showSpinner(btn);
            const confirmed = await confirmDeletion('¿Desea eliminar la relación de esta institución educativa?');

            if (confirmed){
                fetch(`/api/institucion_gestor/eliminar/${gestorInstiId}/`, {
                    method: 'POST',
                    headers: { 'X-CSRFToken': csrfToken }
                })
                .then(response => {
                    return response.json().then(data=> {
                        if (!response.ok){
                            throw new Error(data.message || 'Error al obtener los datos');
                        }
                        return data;
                    });
                })
                .then(data => {
                    showSuccessToast(data.message);
                    setTimeout(() => {
                        cargarDatosTabla();
                    }, 1000);
                })
                .catch(error => {
                    showErrorToast(error.message);
                })
                .finally(()=>{
                    hideSpinner(btn, originalBtnContent);
                });
            } else {
                hideSpinner(btn, originalBtnContent);
            }
        }
    });
});