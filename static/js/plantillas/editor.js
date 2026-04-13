const ROLES = ["admin", "instructor", "aprendiz", "lider", "gestor", "consulta", "cuentas"];

let tree = null;

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
  tree = new mar10.Wunderbaum({
    element: document.getElementById("plantillaTree"),
    id: "plantillaEditor",
    source: { url: "/plantillas/api/nodos/" },
    types: {},
    dnd: {
      dragStart: () => true,
      dragEnter: () => true,
      drop: (e) => {
        const node = e.node;
        const targetNode = e.region === "over" ? e.targetNode : e.targetNode.parent;
        const parentId = targetNode ? targetNode.key : null;

        const siblings = targetNode ? targetNode.children : tree.root.children;
        const idx = siblings ? siblings.indexOf(node) : 0;

        apiCall(`/plantillas/api/nodo/${node.key}/mover/`, "POST", {
          parent_id: parentId ? parseInt(parentId) : null,
          orden: idx,
        });
      },
    },
    activate: (e) => {},
    render: (e) => {
      const node = e.node;
      if (node.data && !node.data.activo) {
        if (e.nodeElem) e.nodeElem.classList.add("nodo-inactivo");
      }
    },
  });

  // --- Toolbar actions ---

  document.getElementById("btnAgregar").addEventListener("click", function () {
    const node = tree.getActiveNode();
    if (!node) { alert("Selecciona un nodo primero"); return; }

    const nombre = prompt("Nombre de la nueva carpeta:");
    if (!nombre) return;

    apiCall("/plantillas/api/nodo/crear/", "POST", {
      parent_id: parseInt(node.key),
      name: nombre,
    }).then((data) => {
      node.addChildren({
        title: data.name,
        key: String(data.id),
        data: { id: data.id, orden: data.orden, activo: true, roles_visibles: null, roles_editables: null },
        expanded: true,
        children: [],
      });
      node.setExpanded(true);
    });
  });

  document.getElementById("btnRenombrar").addEventListener("click", function () {
    const node = tree.getActiveNode();
    if (!node) { alert("Selecciona un nodo primero"); return; }

    const nombre = prompt("Nuevo nombre:", node.title);
    if (!nombre || nombre === node.title) return;

    apiCall(`/plantillas/api/nodo/${node.key}/editar/`, "POST", { name: nombre })
      .then(() => {
        node.setTitle(nombre);
      });
  });

  document.getElementById("btnToggle").addEventListener("click", function () {
    const node = tree.getActiveNode();
    if (!node) { alert("Selecciona un nodo primero"); return; }

    apiCall(`/plantillas/api/nodo/${node.key}/toggle/`, "POST")
      .then((data) => {
        node.data.activo = data.activo;
        if (data.activo) {
          node.removeClass("nodo-inactivo");
        } else {
          node.addClass("nodo-inactivo");
        }
      });
  });

  // --- Visibilidad modal ---

  document.getElementById("btnVisibilidad").addEventListener("click", function () {
    const node = tree.getActiveNode();
    if (!node) { alert("Selecciona un nodo primero"); return; }

    document.getElementById("visNodoName").textContent = node.title;
    renderCheckboxes("checksVisibles", node.data.roles_visibles);
    renderCheckboxes("checksEditables", node.data.roles_editables);

    new bootstrap.Modal(document.getElementById("modalVisibilidad")).show();
  });

  document.getElementById("btnGuardarVisibilidad").addEventListener("click", function () {
    const node = tree.getActiveNode();
    const visibles = getCheckedRoles("checksVisibles");
    const editables = getCheckedRoles("checksEditables");

    apiCall(`/plantillas/api/nodo/${node.key}/visibilidad/`, "POST", {
      roles_visibles: visibles.length ? visibles : null,
      roles_editables: editables.length ? editables : null,
    }).then((data) => {
      node.data.roles_visibles = data.roles_visibles;
      node.data.roles_editables = data.roles_editables;
      bootstrap.Modal.getInstance(document.getElementById("modalVisibilidad")).hide();
    });
  });

  // --- Guardar version ---

  document.getElementById("btnGuardar").addEventListener("click", function () {
    new bootstrap.Modal(document.getElementById("modalGuardarVersion")).show();
  });

  document.getElementById("btnConfirmarGuardar").addEventListener("click", function () {
    const descripcion = document.getElementById("versionDescripcion").value;
    const autoAplicar = document.getElementById("versionAutoAplicar").checked;

    if (!descripcion.trim()) { alert("Ingresa una descripcion"); return; }

    apiCall("/plantillas/api/guardar_version/", "POST", {
      descripcion,
      auto_aplicar_nuevas: autoAplicar,
    }).then((data) => {
      bootstrap.Modal.getInstance(document.getElementById("modalGuardarVersion")).hide();
      document.getElementById("versionDescripcion").value = "";
      document.getElementById("versionAutoAplicar").checked = false;
      Toastify({
        text: `Version v${data.version} guardada`,
        duration: 3000,
        gravity: "top",
        position: "right",
        backgroundColor: "#198754",
      }).showToast();
    });
  });
});

function renderCheckboxes(containerId, selectedRoles) {
  const container = document.getElementById(containerId);
  container.innerHTML = ROLES.map(rol => {
    const checked = selectedRoles && selectedRoles.includes(rol) ? "checked" : "";
    return `<div class="form-check form-check-inline">
      <input class="form-check-input" type="checkbox" value="${rol}" ${checked} id="${containerId}_${rol}">
      <label class="form-check-label" for="${containerId}_${rol}">${rol}</label>
    </div>`;
  }).join("");
}

function getCheckedRoles(containerId) {
  const checks = document.querySelectorAll(`#${containerId} input:checked`);
  return Array.from(checks).map(c => c.value);
}
