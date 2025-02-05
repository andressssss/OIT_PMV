$(document).ready(function () {
    new DataTable('#tasks');
    

    new DataTable('#competencias_table', {
        language: {
            url: 'https://cdn.datatables.net/plug-ins/2.1.8/i18n/es-ES.json',
            deferRender: true
        }
    });
    new DataTable('#ofertas_table', {
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
    new DataTable('#represantesLegales', {
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
    new DataTable('#centrosformacion_table', {
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
    new DataTable('#encuentros_ficha', {
        language: {
            url: 'https://cdn.datatables.net/plug-ins/2.1.8/i18n/es-ES.json',
        }
    });
    new DataTable('#listado_fichas', {
        language: {
            url: 'https://cdn.datatables.net/plug-ins/2.1.8/i18n/es-ES.json',
        }
    });
    new DataTable('#actividades_ficha', {
        language: {
            url: 'https://cdn.datatables.net/plug-ins/2.1.8/i18n/es-ES.json',
        }
    });
    new DataTable('#novedades', {
        language: {
            url: 'https://cdn.datatables.net/plug-ins/2.1.8/i18n/es-ES.json',
        }
    });
    
});
// <<<<Desplegable de informacion para el modulo instructores>>>

$(document).ready(function () {
    // Inicializa DataTables
    var table = $('#instructores').DataTable({
        language: {
            url: 'https://cdn.datatables.net/plug-ins/2.1.8/i18n/es-ES.json',
        },
    });

    // Define la función para mostrar información adicional
    function format(tr) {
        var registroId = tr.data('id');
        console.log(registroId)
        var contenido = '<p>Cargando...</p>'; // Placeholder mientras se obtiene la información

        // Llama a la API Django para obtener los detalles
        $.ajax({
            url: `/obtener_detalles/${registroId}/`,
            method: 'GET',
            async: false, // Debe ser síncrono para actualizar inmediatamente
            success: function (data) {
                contenido = `
                    <div>
                    <p><strong>Nombre:</strong> ${data.info_adicional.perfil.nom}</p>
                    <p><strong>Apellido:</strong> ${data.info_adicional.perfil.apelli}</p>
                    <p><strong>Direccion:</strong> ${data.info_adicional.perfil.dire}</p>
                    <p><strong>Telefono:</strong> ${data.info_adicional.perfil.tele}</p>
                    <p><strong>Usuario:</strong> ${data.info_adicional.perfil.user.username}</p>
                    <p><strong>Email Usuario:</strong> ${data.info_adicional.perfil.user.email}</p>
                    </div>
                    <div id="tree" class="wb-skeleton wb-initializing wb-fade-expander"></div>
                    `;
            },
            error: function () {
                contenido = '<p>Error al cargar los detalles.</p>';
            },
        });

        return contenido;
    }

    // Listener para expandir/cerrar filas
    $('#instructores tbody').on('click', 'td.details-control', function () {
        var tr = $(this).closest('tr'); // Encuentra la fila
        var row = table.row(tr); // Encuentra la fila en DataTables
        var icon = $(this).find('i');

        if (row.child.isShown()) {
            // Si ya está expandido, ciérralo
            row.child.hide();
            tr.removeClass('shown');
            icon.removeClass('bi-chevron-down').addClass('bi-chevron-right');

        } else {
            // Si está colapsado, expándelo
            row.child(format(tr)).show();
            tr.addClass('shown');
            icon.removeClass('bi-chevron-right').addClass('bi-chevron-down');

        }
    });
});



// <<<<Desplegable de informacion para el modulo aprendices >>>

// $(document).ready(function () {
//     // Inicializa DataTables
//     var table = $('#aprendices').DataTable({
//         language: {
//             url: 'https://cdn.datatables.net/plug-ins/2.1.8/i18n/es-ES.json',
//         },
//     });

//     // Define la función para mostrar información adicional
//     function format(tr) {
//         var registroId = tr.data('id');
//         console.log(registroId)
//         var contenido = '<p>Cargando...</p>'; // Placeholder mientras se obtiene la información

//         // Llama a la API Django para obtener los detalles
//         $.ajax({
//             url: `/obtener_detalles_aprendiz/${registroId}/`,
//             method: 'GET',
//             async: false, // Debe ser síncrono para actualizar inmediatamente
//             success: function (data) {
//                 contenido = `
//                     <div>
//                     <p><strong>Nombre:</strong> ${data.info_adicional.aprendiz.perfil.nom}</p>
//                     <p><strong>Apellido:</strong> ${data.info_adicional.aprendiz.perfil.apelli}</p>
//                     <p><strong>telefono:</strong> ${data.info_adicional.aprendiz.perfil.tele}</p>
//                     </div>
//                     `;
//             },
//             error: function () {
//                 contenido = '<p>Error al cargar los detalles.</p>';
//             },
//         });

//         return contenido;
//     }

//     // Listener para expandir/cerrar filas
//     $('#aprendices tbody').on('click', 'td.details-control', function () {
//         var tr = $(this).closest('tr'); // Encuentra la fila
//         var row = table.row(tr); // Encuentra la fila en DataTables
//         var icon = $(this).find('i');

//         if (row.child.isShown()) {
//             // Si ya está expandido, ciérralo
//             row.child.hide();
//             tr.removeClass('shown');
//             icon.removeClass('bi-chevron-down').addClass('bi-chevron-right');

//         } else {
//             // Si está colapsado, expándelo
//             row.child(format(tr)).show();
//             tr.addClass('shown');
//             icon.removeClass('bi-chevron-right').addClass('bi-chevron-down');

//         }
//     });
// });


/// <<<<Desplegable de informacion para el modulo administradores>>>

$(document).ready(function () {
    // Inicializa DataTables
    var table = $('#administradores').DataTable({
        language: {
            url: 'https://cdn.datatables.net/plug-ins/2.1.8/i18n/es-ES.json',
        },
    });

    // Define la función para mostrar información adicional
    function format(tr) {
        var registroId = tr.data('id');
        console.log(registroId)
        var contenido = '<p>Cargando...</p>'; // Placeholder mientras se obtiene la información

        // Llama a la API Django para obtener los detalles
        $.ajax({
            url: `/obtener_detalles_admin/${registroId}/`,
            method: 'GET',
            async: false, // Debe ser síncrono para actualizar inmediatamente
            success: function (data) {
                contenido = `
                    <div>
                     <p><strong>Area:</strong> ${data.info_adicional.admin.area}</p>
                    <p><strong>Nombre:</strong> ${data.info_adicional.admin.perfil.nom}</p>
                    <p><strong>Apellido:</strong> ${data.info_adicional.admin.perfil.apelli}</p>
                    <p><strong>Tipo de DNI:</strong> ${data.info_adicional.admin.perfil.tipo_dni}</p>
                    <p><strong>Telefono:</strong> ${data.info_adicional.admin.perfil.tele}</p>
                    <p><strong>Usuario:</strong> ${data.info_adicional.admin.perfil.user.username}</p>
                    <p><strong>Email Usuario:</strong> ${data.info_adicional.admin.perfil.user.email}</p>
                    </div>
                    `;
            },
            error: function () {
                contenido = '<p>Error al cargar los detalles.</p>';
            },
        });

        return contenido;
    }

    // Listener para expandir/cerrar filas
    $('#administradores tbody').on('click', 'td.details-control', function () {
        var tr = $(this).closest('tr'); // Encuentra la fila
        var row = table.row(tr); // Encuentra la fila en DataTables
        var icon = $(this).find('i');

        if (row.child.isShown()) {
            // Si ya está expandido, ciérralo
            row.child.hide();
            tr.removeClass('shown');
            icon.removeClass('bi-chevron-down').addClass('bi-chevron-right');

        } else {
            // Si está colapsado, expándelo
            row.child(format(tr)).show();
            tr.addClass('shown');
            icon.removeClass('bi-chevron-right').addClass('bi-chevron-down');

        }
    });
});


/// <<<<Desplegable de informacion para el modulo lideres>>>

$(document).ready(function () {
    // Inicializa DataTables
    var table = $('#lideres').DataTable({
        language: {
            url: 'https://cdn.datatables.net/plug-ins/2.1.8/i18n/es-ES.json',
        },
    });

    // Define la función para mostrar información adicional
    function format(tr) {
        var registroId = tr.data('id');
        console.log(registroId)
        var contenido = '<p>Cargando...</p>'; // Placeholder mientras se obtiene la información

        // Llama a la API Django para obtener los detalles
        $.ajax({
            url: `/detalle_lider/${registroId}/`,
            method: 'GET',
            async: false, // Debe ser síncrono para actualizar inmediatamente
            success: function (data) {
                contenido = `
                    <div>
                    <p><strong>Nombre:</strong> ${data.info_adicional.lider.perfil.nom}</p>
                    <p><strong>Apellido:</strong> ${data.info_adicional.lider.perfil.apelli}</p>
                    <p><strong>Telefono:</strong> ${data.info_adicional.lider.perfil.tele}</p>
                    <p><strong>Usuario:</strong> ${data.info_adicional.lider.perfil.user.username}</p>
                    <p><strong>Email Usuario:</strong> ${data.info_adicional.lider.perfil.user.email}</p>
                    </div>
                    `;
            },
            error: function () {
                contenido = '<p>Error al cargar los detalles.</p>';
            },
        });

        return contenido;
    }

    // Listener para expandir/cerrar filas
    $('#lideres tbody').on('click', 'td.details-control', function () {
        var tr = $(this).closest('tr'); // Encuentra la fila
        var row = table.row(tr); // Encuentra la fila en DataTables
        var icon = $(this).find('i');

        if (row.child.isShown()) {
            // Si ya está expandido, ciérralo
            row.child.hide();
            tr.removeClass('shown');
            icon.removeClass('bi-chevron-down').addClass('bi-chevron-right');

        } else {
            // Si está colapsado, expándelo
            row.child(format(tr)).show();
            tr.addClass('shown');
            icon.removeClass('bi-chevron-right').addClass('bi-chevron-down');

        }
    });
});




$(document).ready(function() {
    $('.select2').select2({
        width: '100%',
        theme: 'bootstrap-5'
    });
});

document.addEventListener('DOMContentLoaded', function() {
    const departamentoSelect = document.getElementById('id_depa');
    const municipioSelect = document.getElementById('id_muni');

    departamentoSelect.addEventListener('change', function() {
        const departamentoId = this.value;

        // Limpiar municipios previos
        municipioSelect.innerHTML = '<option value="">Seleccione un municipio</option>';

        if (departamentoId) {
            fetch(`/obtener-municipios/?departamento_id=${departamentoId}`)
                .then(response => response.json())
                .then(data => {
                    data.forEach(municipio => {
                        const option = document.createElement('option');
                        option.value = municipio.id;
                        option.textContent = municipio.nom_munici;
                        municipioSelect.appendChild(option);
                    });
                })
                .catch(error => console.error('Error:', error));
        }
    });
});

$(document).ready(function(){
    $('[data-toggle="tooltip"]').tooltip();   
  });