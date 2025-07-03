import { setFormDisabled, validarArchivo, reiniciarTooltips, crearSelectForm, confirmToast,confirmAction, confirmDialog, confirmDeletion, toastSuccess, toastError, toastWarning, toastInfo, fadeIn, fadeOut, fadeInElement, fadeOutElement, showSpinner, hideSpinner, csrfToken, showSuccessToast, showErrorToast } from '/static/js/utils.js';


document.addEventListener('DOMContentLoaded', () => {

    cargarDatosFormulario();

    function agregarListenersFiltros() {
        const departamentoSelect = document.querySelector('#departamento');
        const municipioSelect = document.querySelector('#municipio');

        if (departamentoSelect) {
            departamentoSelect.addEventListener('change', aplicarFiltros);
        }

        if (municipioSelect) {
            municipioSelect.addEventListener('change', aplicarFiltros);
        }
    }


    async function cargarDatosFormulario(){
        try {
            await Promise.all([
                crearSelectForm({
                    id: 'departamento',
                    nombre: 'departamento',
                    url: '/api/fichas/crear_masivo/departamentos/',
                    contenedor: '#contenedor-departamento',
                    placeholderTexto: '',
                    required: true
                }),
                crearSelectForm({
                    id: 'municipio',
                    nombre: 'municipio',
                    url: '/api/fichas/crear_masivo/municipios/',
                    contenedor: '#contenedor-municipio',
                    placeholderTexto: 'Seleccione un municipio',
                    disabled: true,
                    required: true
                }),
                crearSelectForm({
                    id: 'colegio',
                    nombre: 'colegio',
                    url: '/api/fichas/crear_masivo/colegios/',
                    contenedor: '#contenedor-colegio',
                    placeholderTexto: 'Seleccione un colegio',
                    disabled: true,
                    required: true
                }),
                crearSelectForm({
                    id: 'centro_forma',
                    nombre: 'centro_forma',
                    url: '/api/fichas/crear_masivo/centros/',
                    contenedor: '#contenedor-centro-forma',
                    placeholderTexto: '',
                    required: true
                }),
                crearSelectForm({
                    id: 'programa',
                    nombre: 'programa',
                    url: '/api/fichas/crear_masivo/programas/',
                    contenedor: '#contenedor-programa',
                    placeholderTexto: '',
                    required: true
                })
            ]);

            agregarListenersFiltros();

        } catch (error) {
            toastError(error)
        }
    };

    async function aplicarFiltros(e) {
        const target = e.target;

        if (target.id === 'departamento') {
            const departamentoId = target.value;

            // Cargar municipios asociados al departamento
            await crearSelectForm({
                id: 'municipio',
                nombre: 'municipio',
                url: `/api/fichas/crear_masivo/municipios/?departamento=${departamentoId}`,
                contenedor: '#contenedor-municipio',
                placeholderTexto: '',
                disabled: false,
                required: true
            });

            const municipioSelect = document.querySelector('#municipio');
            const primerMunicipioValido = [...municipioSelect.options].find(opt => !opt.disabled && opt.value)?.value;

            if (primerMunicipioValido) {
                // Cargar colegios del primer municipio automáticamente
                await crearSelectForm({
                    id: 'colegio',
                    nombre: 'colegio',
                    url: `/api/fichas/crear_masivo/colegios/?municipio=${primerMunicipioValido}`,
                    contenedor: '#contenedor-colegio',
                    placeholderTexto: '',
                    disabled: false,
                    required: true
                });
            } else {
                // Si no hay municipios válidos, dejar el select de colegio deshabilitado
                await crearSelectForm({
                    id: 'colegio',
                    nombre: 'colegio',
                    url: '/api/fichas/crear_masivo/colegios/',
                    contenedor: '#contenedor-colegio',
                    placeholderTexto: 'Seleccione un colegio',
                    disabled: true,
                    required: true
                });
            }

            agregarListenersFiltros();

        } else if (target.id === 'municipio') {
            const municipioId = target.value;

            // Cargar colegios asociados al municipio
            await crearSelectForm({
                id: 'colegio',
                nombre: 'colegio',
                url: `/api/fichas/crear_masivo/colegios/?municipio=${municipioId}`,
                contenedor: '#contenedor-colegio',
                placeholderTexto: '',
                disabled: false,
                required: true
            });
            agregarListenersFiltros();
        }
    }

    
    const form = document.getElementById('form-cargar-ficha');

    function verificarArchivoLegible(archivo) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => resolve(true);
            reader.onerror = () => reject(new Error("Archivo ilegible o eliminado."));
            reader.readAsArrayBuffer(archivo);
        });
    }

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const form = e.target;
        const formData = new FormData(form);
        const btn = document.getElementById('submitBtn');
        const originalBtnContent = btn.innerHTML;

        // Evitar doble envío
        if (btn.disabled) return;

        const numFicha = formData.get('num_ficha').trim();
        if (!numFicha) {
            const confirmed = await confirmAction("¿Está seguro de crear una ficha sin número?");
            if (!confirmed) return;
        }

        const archivoInput = document.getElementById('archivo');
        const archivo = archivoInput.files[0];

        if (!archivo) {
            toastError('Debe seleccionar un archivo antes de enviar.');
            return;
        }

        const { valido, mensaje } = validarArchivo(archivo, ['csv'], 3);
        if (!valido) {
            toastError(mensaje);
            return;
        }

        const selectMunicipio = document.getElementById('municipio');
        const selectColegio = document.getElementById('colegio');
        if (selectMunicipio.disabled || selectColegio.disabled) {
            toastError('Debe seleccionar un municipio y un colegio antes de continuar.');
            return;
        }

        // Limpiar alertas previas
        document.getElementById('alert-error').classList.add('d-none');
        document.getElementById('alert-success').classList.add('d-none');
        document.getElementById('alert-error').innerText = '';
        document.getElementById('alert-success-content').innerHTML = '';
        document.getElementById('alert-message').classList.add('d-none');
        document.getElementById('alert-message').textContent = '';

        setFormDisabled(form, true);
        showSpinner(btn);

        try {
            // ✅ Validar que el archivo no haya sido eliminado del sistema
            await verificarArchivoLegible(archivo);
            
            const response = await fetch(`/api/fichas/crear_masivo/`, {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (!response.ok) {
                if (data.errores) {
                    const alertError = document.getElementById('alert-error');
                    alertError.textContent = data.errores.join('\n\n').replace(/\\n/g, '\n');
                    alertError.classList.remove('d-none');
                }
                toastError(data.message || 'Error desconocido');
                return;
            }

            // Mostrar resumen en alerta de éxito
            const alertSuccess = document.getElementById('alert-success');
            const alertList = document.getElementById('alert-success-content');

            alertList.innerHTML = `
                <li><strong>Insertados:</strong> ${data.resumen.insertados}</li>
                <li><strong>Errores:</strong> ${data.resumen.errores}</li>
                ${data.resumen.duplicados_dni.length > 0 ? `<li><strong>DNI duplicados:</strong> ${data.resumen.duplicados_dni.join(', ')}</li>` : ''}
            `;
            alertSuccess.classList.remove('d-none');

            document.getElementById('alert-message').textContent = data.message || 'Carga finalizada';
            document.getElementById('alert-message').classList.remove('d-none');

            if (data.errores && data.errores.length > 0) {
                const alertError = document.getElementById('alert-error');
                alertError.textContent = data.errores.join('\n\n');
                alertError.classList.remove('d-none');
            }

            toastSuccess(data.message || 'Carga finalizada');
            form.reset();
            archivoInput.value = '';  // limpiar manualmente input file

        } catch (error) {
            console.error(error);
            toastError('El archivo fue eliminado o ya no está disponible. Por favor, selecciónelo de nuevo.');
            archivoInput.value = '';
        } finally {
            setFormDisabled(form, false);
            hideSpinner(btn, originalBtnContent);
        }
    });



});