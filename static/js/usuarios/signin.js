import { confirmToast, confirmDialog, confirmDeletion, toastSuccess, toastError, toastWarning, toastInfo, fadeIn, fadeOut, fadeInElement, fadeOutElement, showSpinner, hideSpinner, csrfToken, showSuccessToast, showErrorToast } from '/static/js/utils.js';

document.addEventListener('DOMContentLoaded', e => {
    const consultarUserForm = document.getElementById('consultarUserForm');
    const usernameDiv = document.getElementById('usernameres');
    const submitBtn = document.getElementById('submitBtn');

    consultarUserForm.addEventListener('submit', async e => {
        e.preventDefault();

        const cedula = document.getElementById('cedula').value;
        const originalBtnContent = submitBtn.innerHTML;
        showSpinner(submitBtn);
        try {
            const response = await fetch(`/api/consultar_usuario_por_cedula/?cedula=${encodeURIComponent(cedula)}`, {
                method: 'GET',
                headers: {
                    'X-CSRFToken': csrfToken
                }
            });

            const data = await response.json();
            console.log('Respuesta:', data);  // Para depurar

            if (response.ok) {
                usernameDiv.textContent = `Su nombre de usuario es: ${data.username}`;
                usernameDiv.classList.remove('alert-danger');
                usernameDiv.classList.add('alert-info');
                usernameDiv.style.display = 'block';
            } else {
                usernameDiv.textContent = data.error || 'Ocurrió un error';
                usernameDiv.classList.remove('alert-info');
                usernameDiv.classList.add('alert-danger');
                usernameDiv.style.display = 'block';
                Toastify({
                    text: "Si no encuentra su documento de identidad, por favor contacte al equipo de soporte: soporte@OIT.com",
                    duration: 15000,
                    close: true,
                    gravity: "bottom",
                    position: "center",
                    backgroundColor: "#1E2DBE",
                    stopOnFocus: true,
                    className: "custom-toast"
                }).showToast();
            }

        } catch (error) {
            usernameDiv.textContent = 'Error de red o del servidor.';
            usernameDiv.classList.remove('alert-info');
            usernameDiv.classList.add('alert-danger');
            usernameDiv.style.display = 'block';
        }finally{
            hideSpinner(submitBtn, originalBtnContent);
        }
    });

    const btnForget = document.getElementById('passForget');

    btnForget.addEventListener('click', () => {
        Toastify({
            text: "Si no puede ingresar con su documento de identidad, por favor contacte al equipo de soporte: soporte@OIT.com",
            duration: 15000,
            close: true,
            gravity: "bottom",
            position: "center",
            backgroundColor: "#1E2DBE",
            stopOnFocus: true,
            className: "custom-toast"
        }).showToast();
    });
});;