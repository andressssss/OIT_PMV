import { hideSpinner, resetForm, showSpinner, fetchData, setText, setFormDisabled, csrfToken, toastSuccess } from "/static/js/utils.js";

document.addEventListener("DOMContentLoaded", () => {
  // === 1️⃣ ENDPOINTS ===
  const BASE_URL = "/api/dashboard/novedades/";
  const novedadId = window.location.pathname.split("/").filter(Boolean).pop(); // obtiene el último segmento de la URL (id)
  
  const ENDPOINTS = {
    detalle: `${BASE_URL}${novedadId}/detalle/`,
    documentos: `${BASE_URL}${novedadId}/documentos/`,
    acciones: `${BASE_URL}${novedadId}/acciones/`,
    crearAccion: `${BASE_URL}${novedadId}/acciones/create/`,
    crearDocumento: `${BASE_URL}${novedadId}/documentos/create/`,
  };

  // === 2️⃣ SELECTORES ===
  const el = {
    codigo: document.getElementById("detalle-codigo"),
    tipo: document.getElementById("detalle-tipo"),
    estado: document.getElementById("detalle-estado"),
    fecha: document.getElementById("detalle-fecha"),
    cierre: document.getElementById("detalle-cierre"),
    responsable: document.getElementById("detalle-responsable"),
    usuario: document.getElementById("detalle-usuario"),
    descripcion: document.getElementById("detalle-descripcion"),
    tablaDocumentos: document.getElementById("tabla-documentos").querySelector("tbody"),
    listaAcciones: document.getElementById("lista-acciones"),
    btnGuardarAccion: document.getElementById("btn-guardar-accion"),
    formNuevaAccion: document.getElementById("form-nueva-accion"),
  };

  async function cargarDetalle() {
    try {
      const data = await fetchData(ENDPOINTS.detalle);
      el.codigo.textContent = data.num || "--";
      el.tipo.textContent = data.tipo || "--";
      el.estado.textContent = data.esta || "--";
      el.estado.className = `badge ${estadoColor(data.estado)}`;
      el.fecha.textContent = data.fecha_regi;
      el.cierre.textContent = data.fecha_venci;
      el.responsable.textContent = data.respo_nom || "--";
      el.usuario.textContent = data.soli_nom || "--";
      el.descripcion.textContent = data.descri || "--";
    } catch (err) {
      console.error("Error cargando detalle:", err);
    }
  }

  async function cargarDocumentos() {
    try {
      const documentos = await fetchData(ENDPOINTS.documentos);
      el.tablaDocumentos.innerHTML = "";

      if (documentos.length === 0) {
        el.tablaDocumentos.innerHTML = `<tr><td colspan="4" class="text-center text-muted">Sin documentos</td></tr>`;
        return;
      }

      documentos.forEach((doc) => {
        const fila = `
          <tr>
            <td>${doc.nombre}</td>
            <td>${doc.tipo || "--"}</td>
            <td>
              <a href="/media/${doc.url}/" target="_blank" class="btn btn-sm btn-outline-primary"><i class="bi bi-eye"></i></a>
            </td>
          </tr>`;
        el.tablaDocumentos.insertAdjacentHTML("beforeend", fila);
      });
    } catch (err) {
      console.error("Error cargando documentos:", err);
    }
  }

  async function cargarAcciones() {
    try {
      const acciones = await fetchData(ENDPOINTS.acciones);
      el.listaAcciones.innerHTML = "";

      if (acciones.length === 0) {
        el.listaAcciones.innerHTML = `<p class="text-muted text-center mb-0">Sin acciones registradas</p>`;
        return;
      }

      acciones.forEach((accion) => {
        const documentosHTML = accion.documentos?.length
          ? `<ul class="list-unstyled mb-0">${accion.documentos
              .map(
                (doc) =>
                  `<li><a href="${doc.url}" target="_blank" class="text-decoration-none"><i class="bi bi-file-earmark-text me-1"></i> ${doc.nombre}</a></li>`
              )
              .join("")}</ul>`
          : `<p class="text-muted small mb-0">Sin documentos</p>`;

        const card = `
          <div class="card shadow-sm border-0">
            <div class="card-body">
              <div class="d-flex justify-content-between">
                <div>
                  <h6 class="fw-bold mb-1">${accion.crea_por_nombre || "Sin usuario"}</h6>
                  <p class="text-muted small mb-2">${accion.fecha}</p>
                  <p class="mb-2">${accion.descri || "--"}</p>
                </div>
              </div>
              <div class="mt-2">
                <h6 class="text-muted small">Documentos adjuntos:</h6>
                ${documentosHTML}
              </div>
            </div>
          </div>`;
        el.listaAcciones.insertAdjacentHTML("beforeend", card);
      });
    } catch (err) {
      console.error("Error cargando acciones:", err);
    }
  }

  function estadoColor(estado) {
    const map = {
      pendiente: "bg-warning text-dark",
      gestion: "bg-primary",
      cerrada: "bg-success",
      cancelada: "bg-danger",
    };
    return map[estado] || "bg-secondary";
  }

  // === 5️⃣ EVENTOS ===
  el.btnGuardarAccion.addEventListener("click", async () => {
    const formData = new FormData(el.formNuevaAccion);
    try {
      const response = await fetch(ENDPOINTS.crearAccion, {
        method: "POST",
        body: formData,
      });
      if (!response.ok) throw new Error("Error creando acción");
      bootstrap.Modal.getInstance(document.getElementById("modalNuevaAccion")).hide();
      await cargarAcciones();
      el.formNuevaAccion.reset();
    } catch (err) {
      console.error(err);
      alert("No se pudo crear la acción.");
    }
  });

  // === 6️⃣ INICIALIZACIÓN ===
  cargarDetalle();
  cargarDocumentos();
  cargarAcciones();
});
