// utils.js

// =====================
// Animaciones comunes
// =====================

export function fadeIn(element) {
  element.classList.remove("hide");
  element.classList.add("show");
}

export function fadeOut(element) {
  element.classList.remove("show");
  element.classList.add("hide");
  setTimeout(() => {
    element.style.display = "";
  }, 500); // Ajusta este tiempo si cambias la duración en CSS
}

export function fadeInElement(element) {
  element.classList.add("fade-transition", "show");
}

export function fadeOutElement(element) {
  element.classList.remove("show");
  element.classList.add("fade-transition");
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
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.startsWith(name + "=")) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

export const csrfToken = getCookie("csrftoken");

// =====================
// SweetAlert2 Helpers
// =====================

export function showSuccessToast(message) {
  Swal.fire({
    icon: "success",
    title: "Éxito",
    text: message,
    timer: 2000,
    showConfirmButton: false,
  });
}

export function showErrorToast(message) {
  Swal.fire({
    icon: "error",
    title: "Error",
    text: message || "Ocurrió un error.",
  });
}

export function confirmDeletion(
  message = "¿Está seguro de que desea eliminar este registro?"
) {
  return Swal.fire({
    title: "Confirmar eliminación",
    text: message,
    icon: "warning",
    showCancelButton: true,
    confirmButtonText: "Sí, eliminar",
    cancelButtonText: "Cancelar",
    reverseButtons: true,
    focusCancel: true,
  }).then((result) => result.isConfirmed);
}

export function confirmAprove(
  message = "¿Está seguro de que desea aprobar este registro?"
) {
  return Swal.fire({
    title: "Confirmar aprobacion",
    text: message,
    icon: "warning",
    showCancelButton: true,
    confirmButtonText: "Sí, confirmar",
    cancelButtonText: "Cancelar",
    reverseButtons: true,
    focusCancel: true,
  }).then((result) => result.isConfirmed);
}

export function confirmAction({
  message = "¿Está seguro que desea hacer esta acción?",
  title = "Confirmar acción",
  icon = "warning",
  confirmButtonText = "Sí, confirmar",
  cancelButtonText = "Cancelar",
  confirmButtonColor = "#1E2DBE", // Azul corporativo
  cancelButtonColor = "#6c757d", // Gris
} = {}) {
  return Swal.fire({
    title: title,
    text: message,
    icon: icon,
    showCancelButton: true,
    confirmButtonText: confirmButtonText,
    cancelButtonText: cancelButtonText,
    confirmButtonColor: confirmButtonColor,
    cancelButtonColor: cancelButtonColor,
    reverseButtons: true,
    focusCancel: true,
    customClass: {
      popup: "custom-swal-popup",
      title: "custom-swal-title",
      confirmButton: "custom-swal-confirm",
      cancelButton: "custom-swal-cancel",
    },
  }).then((result) => result.isConfirmed);
}

// Notificación base
function showToast(
  message,
  backgroundColor = "#333",
  duration = 5000,
  position = "right",
  gravity = "top"
) {
  Toastify({
    text: message,
    duration: duration,
    gravity: gravity, // top or bottom
    position: position, // left, center, or right
    close: true,
    stopOnFocus: true,
    style: {
      background: backgroundColor,
    },
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
export function toastCustom({
  text,
  color,
  time,
  gravity = "top",
  position = "right",
}) {
  showToast(text, color, time, position, gravity);
}

export function confirmDialog(
  message = "¿Estás seguro?",
  title = "Confirmar acción"
) {
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
    modalEl.style.zIndex = "1060";

    // 🧼 Opcional: ocultar otros backdrops para que no interfieran
    const backdrops = document.querySelectorAll(".modal-backdrop");
    backdrops.forEach((bd) => (bd.style.display = "none"));

    acceptBtn.onclick = () => {
      bsModal.hide();
      resolve(true);
    };

    cancelBtn.onclick = () => {
      bsModal.hide();
      resolve(false);
    };

    modalEl.addEventListener(
      "hidden.bs.modal",
      () => {
        // Restaurar backdrops después de cerrar
        backdrops.forEach((bd) => (bd.style.display = ""));
        modalEl.style.zIndex = ""; // Restaurar z-index
      },
      { once: true }
    );

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
      gravity: "center", // Centro vertical
      position: "center", // Centro horizontal
      duration: -1,
      stopOnFocus: true,
      close: false,
      style: {
        zIndex: "9999",
        borderRadius: "8px",
        background: "#fff",
        boxShadow: "0 0 10px rgba(0,0,0,0.2)",
        color: "#000",
        minWidth: "300px",
      },
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
  document.querySelectorAll(".tooltip").forEach((el) => el.remove());

  // Buscar elementos con tooltip y destruir instancias anteriores si existen
  const tooltipTriggerList = [].slice.call(
    document.querySelectorAll('[data-bs-toggle="tooltip"]')
  );
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

// ======= Cargar opciones dinámicas para filtros =======
export async function cargarOpciones(
  url,
  selector,
  placeholderTexto = "Seleccione una opción"
) {
  const container = document.querySelector(selector).parentElement;
  const originalSelect = document.querySelector(selector);
  const placeholderId = `ph-${selector.replace("#", "")}`;

  // Ocultar el select original temporalmente
  originalSelect.style.display = "none";

  // Crear el placeholder de carga
  const placeholderDiv = document.createElement("div");
  placeholderDiv.id = placeholderId;
  placeholderDiv.className = "placeholder-glow";
  placeholderDiv.innerHTML = `
        <span class="placeholder col-12 rounded"></span>
    `;

  container.appendChild(placeholderDiv);

  try {
    const response = await fetch(url);
    const data = await response.json();

    // Limpiar opciones y mostrar placeholder por defecto
    originalSelect.innerHTML = `<option value="" disabled selected>${placeholderTexto}</option>`;

    data.forEach((item) => {
      const option = document.createElement("option");
      option.value = item;
      option.textContent = item;
      originalSelect.appendChild(option);
    });

    // Eliminar placeholder y mostrar select
    placeholderDiv.remove();
    originalSelect.style.display = "";

    // Inicializar TomSelect
    new TomSelect(originalSelect, {
      placeholder: placeholderTexto,
      allowEmptyOption: true,
      plugins: ["remove_button"],
      persist: false,
      create: false,
      closeAfterSelect: true,
      sortField: {
        field: "text",
        direction: "asc",
      },
    });
  } catch (error) {
    console.error(`Error al cargar las opciones para ${selector}`, error);
    placeholderDiv.innerHTML = `<div class="text-danger small">Error al cargar opciones</div>`;
  }
}

export function showPlaceholder(
  container,
  placeholderId = "placeholder-loader"
) {
  if (container.querySelector(`#${placeholderId}`)) return;

  const placeholder = document.createElement("div");
  placeholder.id = placeholderId;
  placeholder.innerHTML = `
      <div class="placeholder-glow my-2">
          <span class="placeholder col-12" style="height: 2rem;"></span>
      </div>
      <div class="placeholder-glow my-2">
          <span class="placeholder col-10"></span>
      </div>
      <div class="placeholder-glow my-2">
          <span class="placeholder col-8"></span>
      </div>
  `;
  container.appendChild(placeholder);
}

export function hidePlaceholder(
  container,
  placeholderId = "placeholder-loader"
) {
  const el = container.querySelector(`#${placeholderId}`);
  if (el) el.remove();
}
export async function crearSelectForm({
  id,
  nombre,
  url,
  placeholderTexto = "Seleccione una opción",
  contenedor,
  multiple = false,
  disabled = false,
  required = false,
}) {
  const contenedorEl = document.querySelector(contenedor);
  if (!contenedorEl) return;
  contenedorEl.innerHTML = `
        <div class="placeholder-glow">
            <span class="placeholder col-12 rounded"></span>
        </div>
    `;

  try {
    const response = await fetch(url);
    const data = await response.json();

    // Crear el elemento <select>
    const select = document.createElement("select");
    select.id = id;
    select.name = nombre;
    select.className = "form-select";

    // 👇 Agregar el placeholder como atributo en el <select>
    select.setAttribute("placeholder", placeholderTexto);

    if (multiple) select.multiple = true;
    if (disabled) select.disabled = true;
    if (required) select.required = true;

    if (!multiple) {
      const defaultOption = document.createElement("option");
      defaultOption.value = "";
      defaultOption.selected = true;
      defaultOption.textContent = placeholderTexto;
      select.appendChild(defaultOption);
    }

    // Agregar opciones desde { id, nom }
    data.forEach((item) => {
      const option = document.createElement("option");
      option.value = item.id;
      option.textContent = item.nom;
      select.appendChild(option);
    });

    // Reemplazar placeholder por el <select>
    contenedorEl.innerHTML = "";
    contenedorEl.appendChild(select);

    // Inicializar TomSelect
    new TomSelect(select, {
      placeholder: placeholderTexto,
      allowEmptyOption: true,
      plugins: multiple ? ["remove_button"] : [],
      persist: false,
      create: false,
      closeAfterSelect: true,
    });
  } catch (error) {
    console.error(`Error al cargar las opciones para ${id}`, error);
    contenedorEl.innerHTML = `<div class="text-danger small">Error al cargar opciones</div>`;
  }
}

export async function crearSelect({
  id,
  nombre,
  url,
  placeholderTexto = "Seleccione una opción",
  contenedor,
}) {
  const contenedorEl = document.querySelector(contenedor);
  if (!contenedorEl) {
    return;
  }
  contenedorEl.innerHTML = `
        <div class="placeholder-glow">
            <span class="placeholder col-12 rounded"></span>
        </div>
    `;

  try {
    const response = await fetch(url);
    const data = await response.json();

    // Crear el elemento select
    const select = document.createElement("select");
    select.id = id;
    select.name = nombre;
    select.multiple = true;
    select.className = "form-select";

    // Agregar opciones
    data.forEach((item) => {
      const option = document.createElement("option");
      option.value = item;
      option.textContent = item;
      select.appendChild(option);
    });

    // Reemplazar placeholder por el select
    contenedorEl.innerHTML = "";
    contenedorEl.appendChild(select);

    // Inicializar TomSelect
    const ts = new TomSelect(select, {
      placeholder: placeholderTexto,
      allowEmptyOption: true,
      plugins: ["remove_button"],
      persist: false,
      create: false,
      closeAfterSelect: true,
      sortField: {
        field: "text",
        direction: "asc",
      },
    });

    return ts;
  } catch (error) {
    console.error(`Error al cargar las opciones para ${id}`, error);
    contenedorEl.innerHTML = `<div class="text-danger small">Error al cargar opciones</div>`;
  }
}

export function validarArchivo(file, extensionesPermitidas = [], maxMB = 2) {
  if (!file) {
    return { valido: false, mensaje: "No se seleccionó ningún archivo." };
  }

  const extension = file.name.split(".").pop().toLowerCase();
  const esExtensionValida = extensionesPermitidas
    .map((ext) => ext.toLowerCase())
    .includes(extension);
  const esTamanoValido = file.size <= maxMB * 1024 * 1024;

  if (!esExtensionValida) {
    return {
      valido: false,
      mensaje: `Extensión no permitida. Solo se permiten: ${extensionesPermitidas.join(
        ", "
      )}.`,
    };
  }

  if (!esTamanoValido) {
    return {
      valido: false,
      mensaje: `El archivo supera el tamaño máximo de ${maxMB}MB.`,
    };
  }

  return { valido: true, mensaje: "" };
}

export function setFormDisabled(form, disabled) {
  // Deshabilitar todos los inputs, selects y textareas normales
  form.querySelectorAll("input, select, textarea").forEach((el) => {
    el.disabled = disabled;
  });

  // Deshabilitar/activar TomSelects correctamente
  form.querySelectorAll("select").forEach((select) => {
    if (select.tomselect) {
      if (disabled) {
        select.tomselect.disable();
      } else {
        select.tomselect.enable();
      }
    }
  });
}

export function setSelectValue(selectId, value) {
  const select = document.querySelector(`#${selectId}`);

  if (!select) {
    console.warn(`Select con ID #${selectId} no encontrado.`);
    return;
  }

  const isMultiple = select.multiple || Array.isArray(value);

  if (select.tomselect) {
    const tomSelect = select.tomselect;

    // Asegurarse de que todos los valores existan como opciones
    if (isMultiple) {
      value.forEach((val) => {
        if (!tomSelect.options[val]) {
          console.warn(
            `Valor ${val} no encontrado en el select #${selectId} (TomSelect).`
          );
        }
      });

      tomSelect.setValue(value, true);
    } else {
      if (tomSelect.options[value]) {
        tomSelect.setValue(value, true);
      } else {
        console.warn(
          `Valor ${value} no encontrado en el select #${selectId} (TomSelect).`
        );
      }
    }
  } else {
    if (isMultiple) {
      for (let option of select.options) {
        option.selected = value.includes(option.value);
      }
    } else {
      select.value = value;
    }

    select.dispatchEvent(new Event("change"));
  }
}

export function validarErrorDRF(response, data) {
  if (response.ok) return false;

  let mensaje = "Ocurrió un error.";

  if (data?.message) {
    mensaje = data.message;
  } else if (data?.detail) {
    mensaje = data.detail;
  } else if (typeof data === "object") {
    mensaje = extraerMensajesDeError(data).join("\n");
  }

  toastError(mensaje);
  return true;
}

function extraerMensajesDeError(obj, path = "") {
  const mensajes = [];

  for (const key in obj) {
    const value = obj[key];
    const currentPath = path ? `${path}.${key}` : key;

    if (Array.isArray(value)) {
      value.forEach((msg) => {
        mensajes.push(`${currentPath}: ${msg}`);
      });
    } else if (typeof value === "object" && value !== null) {
      mensajes.push(...extraerMensajesDeError(value, currentPath));
    } else if (typeof value === "string") {
      mensajes.push(`${currentPath}: ${value}`);
    }
  }

  return mensajes;
}

export function resetForm(element) {
  if (element.tagName === "FORM") {
    element.reset();
  }

  if (element.tagName === "SELECT" && element.tomselect) {
    element.tomselect.clear();
  }

  element.childNodes.forEach((child) => {
    if (child.nodeType === Node.ELEMENT_NODE) {
      resetForm(child);
    }
  });
}




/**
 * @description
 * @author Andrés Sanabria
 * @date 17-10-2025
 * @export
 * @param {*} url
 * @param {*} [{ method = "GET", body = null, headers = {} }={}]
 * @returns {*}  
 */
export async function fetchData(
  url,
  { method = "GET", body = null, headers = {} } = {}
) {
  try {
    const options = {
      method,
      headers: { ...headers },
    };

    if (body) {
      if (body instanceof FormData) {
        options.body = body;
      } else if (typeof body === "string") {
        options.body = body;
        options.headers["Content-Type"] = "text/plain";
      } else {
        options.body = JSON.stringify(body);
        options.headers["Content-Type"] = "application/json";
      }
    }

    const response = await fetch(url, options);

    const data = response.status !== 204 ? await response.json() : null;

    if (validarErrorDRF(response, data)) {
      throw new Error("Error en el request");
    }

    return data;
  } catch (error) {
    console.error("❌ Error al cargar:", url, error);
    return null;
  }
}

export function setText(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = value;
}
