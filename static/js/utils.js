// utils.js

// =====================
// Animaciones comunes
// =====================

export function fadeIn(element) {
    element.classList.remove('hide');
    element.classList.add('show');
}

export function fadeOut(element) {
    element.classList.remove('show');
    element.classList.add('hide');
    setTimeout(() => {
        element.style.display = '';
    }, 500); // Ajusta este tiempo si cambias la duración en CSS
}

export function fadeInElement(element) {
    element.classList.add('fade-transition', 'show');
}

export function fadeOutElement(element) {
    element.classList.remove('show');
    element.classList.add('fade-transition');
}

// =====================
// Spinner para botones
// =====================

export function showSpinner(element) {
    element.innerHTML = `<span class="spinner-grow spinner-grow-sm" role="status" aria-hidden="true"></span>`;
    element.disabled = true;
}

export function hideSpinner(element, originalContent) {
    element.innerHTML = originalContent;
    element.disabled = false;
}

// =====================
// CSRF Token (Django)
// =====================

export function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.startsWith(name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

export const csrfToken = getCookie('csrftoken');

// =====================
// SweetAlert2 Helpers
// =====================

export function showSuccessToast(message) {
    Swal.fire({
        icon: 'success',
        title: 'Éxito',
        text: message,
        timer: 2000,
        showConfirmButton: false
    });
}

export function showErrorToast(message) {
    Swal.fire({
        icon: 'error',
        title: 'Error',
        text: message || 'Ocurrió un error.'
    });
}

export function confirmDeletion(message = '¿Estás seguro de que deseas eliminar este registro?') {
    return Swal.fire({
        title: 'Confirmar eliminación',
        text: message,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonText: 'Sí, eliminar',
        cancelButtonText: 'Cancelar',
        reverseButtons: true,
        focusCancel: true
    }).then((result) => result.isConfirmed);
}