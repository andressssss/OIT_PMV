import { confirmToast, confirmDialog, confirmDeletion, toastSuccess, toastError, toastWarning, toastInfo, fadeIn, fadeOut, fadeInElement, fadeOutElement, showSpinner, hideSpinner, csrfToken, showSuccessToast, showErrorToast } from '/static/js/utils.js';

document.addEventListener('DOMContentLoaded', () => {
    
    const botones = document.querySelectorAll('.btn-detalle-programa');

    botones.forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.preventDefault();
            const programaId = btn.getAttribute('data-id');

            try {
                const response = await fetch(`/api/programa/detalle/${programaId}`);
                if (response.ok) {
                    const data = await response.json();
                    llenarModalPrograma(data);
                    const modal = new bootstrap.Modal(document.getElementById('detalleProgramaModal'));
                    modal.show();
                } else {
                    throw new Error("Error al cargar los datos");
                }
            } catch (error) {
                console.error(error);
                toastError("Hubo un error al cagar los detalles del programa");
            }
        });
    });

    function llenarModalPrograma(data) {
        // Datos del programa
        document.getElementById('prog-cod').textContent = data.cod_prog;
        document.getElementById('prog-nom').textContent = data.nom;
        document.getElementById('prog-nomd').textContent = data.nomd;

        // Competencias
        const listaCompe = document.getElementById('prog-competencias');
        listaCompe.innerHTML = '';
        data.competencias.forEach(compe => {
            const li = document.createElement('li');
            li.className = 'list-group-item';
            const fases = compe.fase.map(f => f.charAt(0).toUpperCase() + f.slice(1)).join(', ');
            li.textContent = `${compe.nom} - Fase(s): ${fases}`;
            listaCompe.appendChild(li);
        });

        // Crear un mapa rápido para encontrar fases por competencia
        const fasesPorCompetencia = {};
        data.competencias.forEach(compe => {
            fasesPorCompetencia[compe.nom] = compe.fase;
        });

        // RAPs
        const listaRaps = document.getElementById('prog-raps');
        listaRaps.innerHTML = '';
        data.raps.forEach(rap => {
            const li = document.createElement('li');
            li.className = 'list-group-item';
            const fases = fasesPorCompetencia[rap.compe] || [];
            const fasesTexto = fases.length > 0 
                ? ' - Fase(s): ' + fases.map(f => f.charAt(0).toUpperCase() + f.slice(1)).join(', ')
                : '';
            li.textContent = `${rap.nom} - ${rap.compe}${fasesTexto}`;
            listaRaps.appendChild(li);
        });
    }


})