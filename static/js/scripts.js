$(document).ready(function () {
    new DataTable('#tasks');
    new DataTable('#aprendices', {
        language: {
            url: '//cdn.datatables.net/plug-ins/2.1.8/i18n/es-ES.json',
        }
    });
});

$(document).ready(function () {
    // Inicializa DataTables
    var table = $('#instructores').DataTable({
        language: {
            url: '//cdn.datatables.net/plug-ins/2.1.8/i18n/es-ES.json',
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
                    <p><strong>Nombre:</strong> ${data.info_adicional.perfil.nombre}</p>
                    <p><strong>Apellido:</strong> ${data.info_adicional.perfil.apelli}</p>
                    <p><strong>Direccion:</strong> ${data.info_adicional.perfil.dire}</p>
                    <p><strong>Telefono:</strong> ${data.info_adicional.perfil.tele}</p>
                    <p><strong>Usuario:</strong> ${data.info_adicional.perfil.user.username}</p>
                    <p><strong>Email Usuario:</strong> ${data.info_adicional.perfil.user.email}</p>
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
