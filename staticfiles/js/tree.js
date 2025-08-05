document.addEventListener("DOMContentLoaded", (event) => {
  // Obtener el ficha_id de la URL de la página
  const urlPath = window.location.pathname; // Obtener la ruta de la URL
  const fichaId = urlPath.split("/")[2]; // Obtener el ID (por ejemplo: "1" de "/fichas/1/")

  // Construir la URL dinámica para la fuente de los datos
  const apiUrl = `http://127.0.0.1:8000/api/carpetas/${fichaId}/`;

  // Inicializar Wunderbaum con la URL dinámica
  const tree = new mar10.Wunderbaum({
    element: document.getElementById("tree"),
    id: "demo",
    source: apiUrl, // Usar la URL construida dinámicamente
    types: {
      carpeta: { icon: "bi bi-folder" }, // Ícono para carpetas
      documento: { icon: "bi bi-file-text" }, // Ícono para documentos
      link: { icon: "bi bi-plus-circle" }, // Ícono para enlaces
    },
    columns: [
      {
        title: "Titulo",
        id: "*",
        width: "*",
        
      },
      {
        title: "Acciones",
        id: "acciones",
        width: "100px",
        classes: "wb-helper-end",
      }],
      columnsResizable: true,
      render: function(e){
        const node = e.node;
        const util = e.util;

        for (const col of Object.values(e.renderColInfosById)) {
          // Assumption: we named column.id === node.data.NAME
          const val = node.data[col.id] !== undefined ? node.data[col.id] : "";
          switch (col.id) {
            case "acciones":
              if (e.isNew){
                console.log(node.type)
                if (node.type == 'documento'){
                  // Crear el botón y añadir un evento click dinámicamente
                  const button = document.createElement("input");
                  button.type = "button";
                  button.value = "🗑️";
                  button.title = "Eliminar!";
                  button.className = "btn btn-danger btn-xs mx-auto d-block";
                  button.addEventListener("click", (event) => {
                    event.stopPropagation(); // Evitar que el clic en el botón active el nodo
                    eliminarDocumento(node);
                  });
                  // Agregar el botón al contenido de la columna
                  col.elem.appendChild(button);
                } else {
                  col.elem.innerHTML = ""; // Asegurarse de que esté vacío para otros tipos
                }
              } 
              util.setValueToElem(col.elem, val);
              break;
  
            default:
              col.elem.textContent = node.data[col.id];

              break;
          }
        }
      },
    // Controlar la activación del nodo
    activate: function (e) {
      const node = e.node; // El nodo activado
      const url = node.data.url; // Acceso al atributo "url" dentro de los datos del nodo
      if (url) {
          window.open(url, "_blank");
      }
    },
  });
});

function eliminarDocumento(node) {
  const documentoId = node.data.id; // Ajusta según el identificador único del documento
  const url = `/eliminar_documento/${documentoId}/`; // URL de la vista en Django

  fetch(url, {
    method: "DELETE",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCookie("csrftoken"), // Asegúrate de incluir el token CSRF
    },
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        console.log(data.message);
        node.remove(); // Eliminar el nodo del árbol
      } else {
        console.error(data.message);
      }
    })
    .catch((error) => console.error("Error al eliminar el documento:", error));
}

// Función para obtener el token CSRF de las cookies
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === name + "=") {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

document.addEventListener("DOMContentLoaded", (event) => {
  // Obtener el ficha_id de la URL de la página
  const urlPath = window.location.pathname;
  const fichaId = urlPath.split("/")[2]; // Obtener el ID de la ficha

  // Referencia al select para seleccionar estudiantes
  const estudianteSelect = document.getElementById("estudianteSelect");

  // Inicializar Wunderbaum
  let tree = null;

  function cargarArbol(estudianteId) {
    const apiUrl = `http://127.0.0.1:8000/api/carpetas/${fichaId}/${estudianteId}`;

    // Destruir el árbol existente si ya fue inicializado
    if (tree) {
      tree.destroy();
    }

    // Crear un nuevo árbol para el estudiante seleccionado
    tree = new mar10.Wunderbaum({
      element: document.getElementById("treeApre"),
      id: "demo",
      source: apiUrl,
      types: {
        carpeta: { icon: "bi bi-folder" },
        documento: { icon: "bi bi-file-text" },
        link: { icon: "bi bi-plus-circle" },
      },
      columns: [
        {
          title: "Titulo",
          id: "*",
          width: "*",
        },
        {
          title: "Acciones",
          id: "acciones",
          width: "100px",
          classes: "wb-helper-end",
        },
      ],
      columnsResizable: true,
      render: function (e) {
        const node = e.node;
        const util = e.util;

        for (const col of Object.values(e.renderColInfosById)) {
          const val = node.data[col.id] !== undefined ? node.data[col.id] : "";
          switch (col.id) {
            case "acciones":
              if (e.isNew) {
                if (node.type == "documento") {
                  const button = document.createElement("input");
                  button.type = "button";
                  button.value = "🗑️";
                  button.title = "Eliminar!";
                  button.className = "btn btn-danger btn-xs mx-auto d-block";
                  button.addEventListener("click", (event) => {
                    event.stopPropagation();
                    eliminarDocumento(node);
                  });
                  col.elem.appendChild(button);
                } else {
                  col.elem.innerHTML = "";
                }
              }
              util.setValueToElem(col.elem, val);
              break;

            default:
              col.elem.textContent = node.data[col.id];
              break;
          }
        }
      },
      activate: function (e) {
        const node = e.node;
        const url = node.data.url;
        if (url) {
          window.open(url, "_blank");
        }
      },
    });
  }

  // Manejar cambios en el select de estudiantes
  estudianteSelect.addEventListener("change", (event) => {
    const estudianteId = event.target.value;
    if (estudianteId) {
      cargarArbol(estudianteId);
    } else {
      // Limpiar el árbol si no hay un estudiante seleccionado
      if (tree) {
        tree.destroy();
        tree = null;
      }
    }
  });

  // Cargar los estudiantes dinámicamente
  fetch(`/api/estudiantes/${fichaId}/`)
    .then((response) => response.json())
    .then((data) => {
      // Rellenar el select con los estudiantes
      data.forEach((estudiante) => {
        const option = document.createElement("option");
        option.value = estudiante.id;
        option.textContent = `${estudiante.nombre} ${estudiante.apellido}`;
        estudianteSelect.appendChild(option);
      });
    })
    .catch((error) => {
      console.error("Error al cargar estudiantes:", error);
    });
});
