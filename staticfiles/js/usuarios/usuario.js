import { toastSuccess, toastError, confirmToast, confirmDeletion, fadeIn, fadeOut, fadeInElement, fadeOutElement, showSpinner, hideSpinner, csrfToken, showSuccessToast, showErrorToast } from '/static/js/utils.js';

document.addEventListener('DOMContentLoaded', () => {
    
    const tableEl = document.getElementById('usuarios_table');

    const table = new DataTable(tableEl, {
        serverSide: true,
        processing: false,
        ajax: {
            url: '/api/usuarios/perfiles/filtrar/',
            type: 'GET',
        },
        columns: [
            { data: 'nom' },
            { data: 'apelli' },
            { data: 'tipo_dni' },
            { data: 'dni' },
            { data: 'username' },
            { data: 'last_login', defaultContent: 'No registrado' },
            { data: 'rol' },
            {
                data: null,
                orderable: false,
                render: function (data, type, row) {
                    return `
                        <a class="btn btn-outline-warning btn-sm mb-1 btn-establecer-contra"
                            data-id="${row.id}"
                            data-usuario="${row.nom} ${row.apelli}"
                            data-toggle="tooltip"
                            data-placement="top"
                            title="Establecer contraseña"
                            data-bs-toggle="modal"
                            data-bs-target="#modalReset">
                            <i class="bi bi-asterisk"></i>
                        </a>
                    `;
                }
            }
        ],
        language: {
            url: 'https://cdn.datatables.net/plug-ins/2.1.8/i18n/es-ES.json'
        },
        drawCallback: () => {
            document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(el => {
                new bootstrap.Tooltip(el);
            });
        }
    });

    function mostrarPlaceholdersTabla() {
        const tbody = document.querySelector('#usuarios_table tbody');
        if (!tbody) return;

        tbody.innerHTML = '';

        const tr = document.createElement('tr');

        const placeholders = [
            'col-10', 'col-10', 'col-8', 'col-6',
            'col-6', 'col-6', 'col-6', 'col-4'
        ];

        placeholders.forEach(colClass => {
            const td = document.createElement('td');
            td.innerHTML = `<span class="placeholder ${colClass} placeholder-glow placeholder-wave rounded"></span>`;
            tr.appendChild(td);
        });

        tbody.appendChild(tr);
    }

    table.on('preXhr.dt', function () {
        mostrarPlaceholdersTabla();
    });

    table.on('processing.dt', function (e, settings, processing) {
        const tbody = document.querySelector('#usuarios_table tbody');
        if (!tbody) return;

        if (processing) {
            mostrarPlaceholdersTabla();
        }
    });

    tableEl.addEventListener('click', function (e) {
        if (e.target.closest('.btn-establecer-contra')) {
            const btn = e.target.closest('.btn-establecer-contra');
            const userId = btn.dataset.id;
            const nombre = btn.dataset.usuario;
            document.getElementById('user-id-reset').value = userId;
            document.getElementById('nombre-usr-restablecer').innerHTML = nombre;
            document.getElementById('new-password').value = '';
        }
    });


    const passwordInput = document.getElementById('new-password');

    if (passwordInput) {
        passwordInput.addEventListener('input', () => {
            const value = passwordInput.value;
    
            toggleRule('rule-length', value.length >= 8);
            toggleRule('rule-uppercase', /[A-Z]/.test(value));
            toggleRule('rule-lowercase', /[a-z]/.test(value));
            toggleRule('rule-number', /\d/.test(value));
            toggleRule('rule-special', /[!@#$%^&*(),.?":{}|<>_\-+=/\\[\]`~%$]/.test(value));
        });
    }
    
    function toggleRule(id, isValid) {
        const element = document.getElementById(id);
        if (!element) return;
        
        if (isValid) {
            element.classList.remove('text-danger');
            element.classList.add('text-success');
            element.textContent = element.textContent.replace('🔴', '🟢');
        } else {
            element.classList.remove('text-success');
            element.classList.add('text-danger');
            element.textContent = element.textContent.replace('🟢', '🔴');
        }
    }

    document.getElementById('form-reset').addEventListener('submit', async (e) =>{
        e.preventDefault();
        
        const userId = document.getElementById('user-id-reset').value;
        const password = document.getElementById('new-password').value;
        const btn = document.getElementById('btn-submit-contra');
        const originalBtnContent = btn.innerHTML;
        showSpinner(btn);
        try {
            const response = await fetch(`/api/usuario/restablecer_contrasena/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({
                    user_id: userId,
                    new_password: password
                })
            });

            const data = await response.json();
            if(response.ok){
                toastSuccess(data.message);
                const modal = bootstrap.Modal.getInstance(document.getElementById('modalReset'));
                modal.hide();
            } else {
                toastError(`Error: ${data.message || data.error || 'No se pudo cambiar la contraseña'}`);
            }

        } catch (error) {
            console.error(error);
            toastError('Error inesperado');
        } finally {
            hideSpinner(btn, originalBtnContent);
        }
    });

});