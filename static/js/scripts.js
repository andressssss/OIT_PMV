$(document).ready(function () {
    new DataTable('#tasks');

    new DataTable('#ofertas_table', {
        language: {
            url: 'https://cdn.datatables.net/plug-ins/2.1.8/i18n/es-ES.json',
            deferRender: true
        }
    });
    new DataTable('#usuarios_table', {
        language: {
            url: 'https://cdn.datatables.net/plug-ins/2.1.8/i18n/es-ES.json',
            deferRender: true
        }
    });
    new DataTable('#cuentas_table', {
        language: {
            url: 'https://cdn.datatables.net/plug-ins/2.1.8/i18n/es-ES.json',
            deferRender: true
        }
    });
    new DataTable('#instructores_table', {
        language: {
            url: 'https://cdn.datatables.net/plug-ins/2.1.8/i18n/es-ES.json',
            deferRender: true
        }
    });
    new DataTable('#municipios_table', {
        language: {
            url: 'https://cdn.datatables.net/plug-ins/2.1.8/i18n/es-ES.json',
            deferRender: true
        }
    });

    new DataTable('#departamentos_table', {
        language: {
            url: 'https://cdn.datatables.net/plug-ins/2.1.8/i18n/es-ES.json',
            deferRender: true
        }
    });
    new DataTable('#gestores_table', {
        language: {
            url: 'https://cdn.datatables.net/plug-ins/2.1.8/i18n/es-ES.json',
            deferRender: true
        }
    });
    new DataTable('#prematriculas', {
        language: {
            url: 'https://cdn.datatables.net/plug-ins/2.1.8/i18n/es-ES.json',
            deferRender: true
        }
    });
    new DataTable('#fichas_prematricula', {
        language: {
            url: 'https://cdn.datatables.net/plug-ins/2.1.8/i18n/es-ES.json',
        }
    });
    new DataTable('#novedades', {
        language: {
            url: 'https://cdn.datatables.net/plug-ins/2.1.8/i18n/es-ES.json',
        }
    });
    // Inicializa DataTables
    var table = $('#instructores').DataTable({
        language: {
            url: 'https://cdn.datatables.net/plug-ins/2.1.8/i18n/es-ES.json',
        },
    });

});