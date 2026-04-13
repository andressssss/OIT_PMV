function getCookie(name) {
  let v = null;
  document.cookie.split(";").forEach(c => {
    c = c.trim();
    if (c.startsWith(name + "=")) v = decodeURIComponent(c.substring(name.length + 1));
  });
  return v;
}

function apiCall(url, method, body) {
  const opts = {
    method,
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCookie("csrftoken"),
    },
  };
  if (body) opts.body = JSON.stringify(body);
  return fetch(url, opts).then(r => r.json());
}

document.addEventListener("DOMContentLoaded", function () {
  const modoSelect = document.getElementById("modoSeleccion");
  const campoCorte = document.getElementById("campoCorte");
  const campoListado = document.getElementById("campoListado");

  fetch("/plantillas/api/cortes/")
    .then(r => r.json())
    .then(cortes => {
      const sel = document.getElementById("selectCorte");
      cortes.forEach(c => {
        const opt = document.createElement("option");
        opt.value = c;
        opt.textContent = c;
        sel.appendChild(opt);
      });
    });

  modoSelect.addEventListener("change", function () {
    campoCorte.classList.toggle("d-none", this.value !== "corte");
    campoListado.classList.toggle("d-none", this.value !== "listado");
  });

  document.getElementById("btnPreview").addEventListener("click", function () {
    const modo = modoSelect.value;
    let valor = null;
    if (modo === "corte") valor = document.getElementById("selectCorte").value;
    if (modo === "listado") valor = document.getElementById("listadoFichas").value;

    const previewDiv = document.getElementById("previewResult");
    previewDiv.innerHTML = '<div class="text-center"><div class="spinner-border spinner-border-sm"></div> Calculando...</div>';

    apiCall("/plantillas/api/preview_aplicar/", "POST", {
      version_id: null,
      modo,
      valor,
    }).then(data => {
      if (data.error) {
        previewDiv.innerHTML = `<div class="alert alert-warning">${data.error}</div>`;
        return;
      }
      document.getElementById("btnAplicar").classList.remove("d-none");
      previewDiv.innerHTML = `
        <p><strong>Total fichas:</strong> ${data.total_fichas}</p>
        ${data.fichas_preview.map(f => `
          <div class="border rounded p-2 mb-2">
            <strong>Ficha ${f.ficha_num}</strong>
            <br><span class="text-success">Crear: ${f.nodos_a_crear.length ? f.nodos_a_crear.join(", ") : "ninguno"}</span>
            <br><span class="text-warning">Ocultar: ${f.nodos_a_ocultar.length ? f.nodos_a_ocultar.join(", ") : "ninguno"}</span>
            <br><span class="text-info">Sincronizar: ${f.nodos_a_sincronizar.length ? f.nodos_a_sincronizar.join(", ") : "ninguno"}</span>
          </div>
        `).join("")}
        ${data.total_fichas > 10 ? `<p class="text-muted">Mostrando 10 de ${data.total_fichas} fichas</p>` : ""}
      `;
    });
  });

  document.getElementById("btnAplicar").addEventListener("click", function () {
    if (!confirm("Estas seguro de aplicar los cambios? Esta accion es irreversible.")) return;

    const modo = modoSelect.value;
    let valor = null;
    if (modo === "corte") valor = document.getElementById("selectCorte").value;
    if (modo === "listado") valor = document.getElementById("listadoFichas").value;

    const resultDiv = document.getElementById("resultadoAplicacion");
    resultDiv.innerHTML = '<div class="text-center"><div class="spinner-border"></div> Aplicando...</div>';

    apiCall("/plantillas/api/ejecutar_aplicar/", "POST", {
      version_id: null,
      modo,
      valor,
    }).then(data => {
      const exitosos = data.resultados.filter(r => r.resultado === "exitoso").length;
      const errores = data.resultados.filter(r => r.resultado === "error").length;

      resultDiv.innerHTML = `
        <div class="alert alert-${errores ? 'warning' : 'success'}">
          <strong>Aplicacion completada</strong><br>
          Exitosos: ${exitosos} | Errores: ${errores}
        </div>
        ${data.resultados.map(r => `
          <div class="border rounded p-2 mb-1">
            <span class="badge bg-${r.resultado === 'exitoso' ? 'success' : 'danger'}">${r.resultado}</span>
            Ficha ${r.ficha_num}:
            ${r.detalle.creados ? r.detalle.creados.length + " creados" : ""}
            ${r.detalle.ocultados ? r.detalle.ocultados.length + " ocultados" : ""}
            ${r.detalle.sincronizados ? r.detalle.sincronizados.length + " sincronizados" : ""}
          </div>
        `).join("")}
      `;
    });
  });
});
