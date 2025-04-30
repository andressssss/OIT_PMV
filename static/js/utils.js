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

export function confirmDeletion(message = '¿Está seguro de que desea eliminar este registro?') {
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

export function confirmAprove(message = '¿Está seguro de que desea aprobar este registro?') {
    return Swal.fire({
        title: 'Confirmar aprobacion',
        text: message,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonText: 'Sí, confirmar',
        cancelButtonText: 'Cancelar',
        reverseButtons: true,
        focusCancel: true
    }).then((result) => result.isConfirmed);
}

export function confirmAction(message = '¿Está seguro que desea hacer esta acción?') {
  return Swal.fire({
      title: 'Confirmar acción',
      text: message,
      icon: 'warning',
      showCancelButton: true,
      confirmButtonText: 'Sí, confirmar',
      cancelButtonText: 'Cancelar',
      reverseButtons: true,
      focusCancel: true
  }).then((result) => result.isConfirmed);
}

// Notificación base
function showToast(message, backgroundColor = "#333", duration = 3000, position = "right", gravity = "top") {
Toastify({
    text: message,
    duration: duration,
    gravity: gravity, // top or bottom
    position: position, // left, center, or right
    close: true,
    stopOnFocus: true,
    style: {
      background: backgroundColor
    }
}).showToast();
}

// Notificación de éxito
export function toastSuccess(message = "Operación exitosa") {
showToast(message, "#198754"); // Bootstrap green
}

// Notificación de error
export function toastError(message = "Ocurrió un error") {
showToast(message, "#dc3545"); // Bootstrap red
}

// Notificación de advertencia
export function toastWarning(message = "Atención") {
showToast(message, "#ffc107", 4000); // Bootstrap yellow
}

// Notificación de información
export function toastInfo(message = "Información") {
showToast(message, "#0dcaf0"); // Bootstrap info blue
}

// Notificación personalizada (opcional export si deseas)
export function toastCustom({ text, color, time, gravity = "top", position = "right" }) {
showToast(text, color, time, position, gravity);
  }

  export function confirmDialog(message = "¿Estás seguro?", title = "Confirmar acción") {
    return new Promise((resolve) => {
      const modalEl = document.getElementById("confirmModal");
      const messageEl = document.getElementById("confirmModalMessage");
      const titleEl = document.getElementById("confirmModalLabel");
      const acceptBtn = document.getElementById("acceptConfirmBtn");
      const cancelBtn = document.getElementById("cancelConfirmBtn");
  
      messageEl.textContent = message;
      titleEl.textContent = title;
  
      const bsModal = new bootstrap.Modal(modalEl, {
        backdrop: "static",
        keyboard: false,
      });
  
      // 🔼 Subir el z-index manualmente
      modalEl.style.zIndex = '1060';
  
      // 🧼 Opcional: ocultar otros backdrops para que no interfieran
      const backdrops = document.querySelectorAll('.modal-backdrop');
      backdrops.forEach(bd => bd.style.display = 'none');
  
      acceptBtn.onclick = () => {
        bsModal.hide();
        resolve(true);
      };
  
      cancelBtn.onclick = () => {
        bsModal.hide();
        resolve(false);
      };
  
      modalEl.addEventListener('hidden.bs.modal', () => {
        // Restaurar backdrops después de cerrar
        backdrops.forEach(bd => bd.style.display = '');
        modalEl.style.zIndex = ''; // Restaurar z-index
      }, { once: true });
  
      bsModal.show();
    });
  }

  export function confirmToast(message = "¿Confirmar acción?") {
    return new Promise((resolve) => {
      // Crear el backdrop que bloquea clics fuera del toast
      const backdrop = document.createElement("div");
      backdrop.style.position = "fixed";
      backdrop.style.top = "0";
      backdrop.style.left = "0";
      backdrop.style.width = "100vw";
      backdrop.style.height = "100vh";
      backdrop.style.backgroundColor = "rgba(0, 0, 0, 0.4)";
      backdrop.style.zIndex = "9998";
      document.body.appendChild(backdrop);
  
      // Crear el contenido del toast personalizado
      const toast = document.createElement("div");
      toast.innerHTML = `
        <div style="display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 8px;">
          <span style="flex: 1;">${message}</span>
          <div>
            <button class="btn btn-sm btn-success me-2">Sí</button>
            <button class="btn btn-sm btn-secondary">No</button>
          </div>
        </div>
      `;
  
      const toastify = Toastify({
        node: toast,
        gravity: "center",       // Centro vertical
        position: "center",      // Centro horizontal
        duration: -1,
        stopOnFocus: true,
        close: false,
        style: {
          zIndex: "9999",
          borderRadius: "8px",
          background: "#fff",
          boxShadow: "0 0 10px rgba(0,0,0,0.2)",
          color: "#000",
          minWidth: "300px"
        }
      });
  
      toastify.showToast();
  
      toast.querySelector(".btn-success").onclick = () => {
        toastify.hideToast();
        backdrop.remove();
        resolve(true);
      };
  
      toast.querySelector(".btn-secondary").onclick = () => {
        toastify.hideToast();
        backdrop.remove();
        resolve(false);
      };
    });
  }
  
  export function reiniciarTooltips() {
    // Quitar tooltips anteriores que estén activos en el DOM (flotantes)
    document.querySelectorAll('.tooltip').forEach(el => el.remove());

    // Buscar elementos con tooltip y destruir instancias anteriores si existen
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.forEach((el) => {
        const tooltip = bootstrap.Tooltip.getInstance(el);
        if (tooltip) {
            tooltip.dispose();
        }
    });

    // Crear nuevas instancias
    tooltipTriggerList.forEach((el) => {
        new bootstrap.Tooltip(el);
    });
}
