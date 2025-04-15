import { toastSuccess, toastError, confirmToast, confirmDeletion, fadeIn, fadeOut, fadeInElement, fadeOutElement, showSpinner, hideSpinner, csrfToken, showSuccessToast, showErrorToast } from '/static/js/utils.js';

document.addEventListener('DOMContentLoaded', () => {
    
    document.querySelectorAll('.btn-establecer-contra').forEach(btn => {
        btn.addEventListener('click', () => {
            const userId = btn.dataset.id;
            const nombre = btn.dataset.usuario;
            document.getElementById('user-id-reset').value = userId;
            document.getElementById('nombre-usr-restablecer').innerHTML = nombre;
            document.getElementById('new-password').value = '';

        });
    })

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
                toastError(`Error: ${data.message || 'No se pudo cambiar la contraseña'}`);
            }

        } catch (error) {
            console.error(error);
            toastError('Error inesperado');
        } finally {
            hideSpinner(btn, originalBtnContent);
        }
    });

});