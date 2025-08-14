import {
  setFormDisabled,
  setSelectValue,
  validarErrorDRF,
  reiniciarTooltips,
  confirmToast,
  confirmAction,
  confirmDialog,
  confirmDeletion,
  toastSuccess,
  toastError,
  toastWarning,
  toastInfo,
  fadeIn,
  fadeOut,
  fadeInElement,
  fadeOutElement,
  showSpinner,
  hideSpinner,
  csrfToken,
  showSuccessToast,
  showErrorToast,
} from "/static/js/utils.js";

document.addEventListener("DOMContentLoaded", function () {
  const fichaId = getFichaIdFromUrl();
  const loadingDiv = document.getElementById("loading");
  const tableAprendicesElement = document.getElementById(
    "tabla_aprendices_ficha"
  );

  const userRole = document.body.dataset.userRole;

  // ======= Inicialización de DataTables =======
  const table = new DataTable(tableAprendicesElement, {
    language: {
      url: "https://cdn.datatables.net/plug-ins/2.1.8/i18n/es-ES.json",
    },
  });

  // const tomSelectMultiple = new TomSelect(".tomselect-multiple", {
  //     plugins: ['remove_button'],
  //     maxItems: null,
  //     persist: false,
  //     create: false,
  //     placeholder: 'Seleccione tipos de actividad'
  // });

  // const tomSelectRaps = new TomSelect(".tomselect-raps", {
  //     plugins: ['remove_button'],
  //     maxItems: null,
  //     placeholder: 'Seleccione los RAPs asociados'
  // });

  // *******************************************************************
  // *                                                                 *
  // *        ¡ADVERTENCIA! ZONA DE CÓDIGO PORTAFOLIO FICHA            *
  // *                                                                 *
  // *******************************************************************

  if (!fichaId) {
    console.error("No se pudo obtener el ID de la ficha.");
    return;
  }

  document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach((el) => {
    new bootstrap.Tooltip(el);
  });

  async function verTree() {
    const container = document.getElementById("folderTree");

    const loadingMessage = document.createElement("p");
    loadingMessage.innerHTML = `
        <div class="d-flex justify-content-center align-items-center">
            <div class="spinner-border text-dark me-2" role="status">
                <span class="visually-hidden">Cargando...</span>
            </div>
        </div>
        `;
    container.appendChild(loadingMessage);

    try {
      const apiUrl = `/api/tree/obtener_carpetas/${fichaId}/`;
      const response = await fetch(apiUrl);
      const data = await response.json();

      container.innerHTML = "";

      container.appendChild(renderTree(data));

      // Agregar listeners después de renderizar el árbol
      addEventListeners();
    } catch (error) {
      console.error("Error al cargar la estructura del árbol:", error);
      container.innerHTML = "<p>Error al cargar el árbol</p>";
    }
  }

  verTree();

  function renderTree(nodes) {
    if (!nodes || nodes.length === 0) return null;

    const ul = document.createElement("ul");
    ul.classList.add("folder-list");

    nodes.forEach((node) => {
      const li = document.createElement("li");
      li.classList.add("folder-item");

      // Elementos comunes a todos los nodos
      const icon = document.createElement("i");
      const span = document.createElement("span");
      span.textContent = node.name;

      // Usamos dataset para almacenar el ID según el tipo
      const dataId = node.tipo === "carpeta" ? "folderId" : "documentId";
      icon.dataset[dataId] = node.id;
      span.dataset[dataId] = node.id;

      if (node.tipo === "carpeta") {
        // Configuración para carpetas
        icon.classList.add("bi", "bi-folder2");

        // Contenedor de subelementos (solo para carpetas)
        const subFolderContainer = document.createElement("ul");
        subFolderContainer.classList.add("folder-children");
        subFolderContainer.id = `folder-${node.id}`;

        if (
          (userRole === "instructor" || userRole === "admin") &&
          (!node.children ||
            node.children.length === 0 ||
            node.children.every((child) => child.tipo === "documento"))
        ) {
          // Botón de carga (solo para carpetas)
          const uploadLi = document.createElement("li");
          uploadLi.classList.add("upload-item");
          uploadLi.style.listStyle = "none";
          uploadLi.dataset.folderId = node.id;

          li.dataset.folderId = node.id;
          li.dataset.droppable = "true";

          const uploadIcon = document.createElement("i");
          uploadIcon.classList.add("bi", "bi-plus-circle");

          const uploadSpan = document.createElement("span");
          uploadSpan.textContent = "Cargar documento";

          uploadLi.appendChild(uploadIcon);
          uploadLi.appendChild(uploadSpan);
          subFolderContainer.appendChild(uploadLi);
        }
        // Procesar hijos recursivamente si existen
        if (node.children && node.children.length > 0) {
          subFolderContainer.appendChild(renderTree(node.children));
        }

        // Ensamblar elementos de carpeta
        li.appendChild(icon);
        li.appendChild(span);
        li.appendChild(subFolderContainer);
      } else if (node.tipo === "documento") {
        // Configuración para documentos
        const extension = node.documento_nombre.split(".").pop().toLowerCase();
        // Determinar icono según extensión
        const extensionIcons = {
          pdf: "bi-file-earmark-pdf",
          xlsx: "bi-file-earmark-spreadsheet",
          csv: "bi-file-earmark-spreadsheet",
          jpg: "bi-image",
          jpeg: "bi-image",
          png: "bi-image",
          ppt: "bi-file-earmark-easel",
          docx: "bi-file-earmark-richtext",
          doc: "bi-file-earmark-richtext",
          dotm: "bi-file-earmark-richtext",
          dotx: "bi-file-earmark-richtext",
          docm: "bi-file-earmark-richtext",
          mp3: "bi-file-earmark-music",
          mp4: "bi-file-earmark-play",
          xls: "file-earmark-spreadsheet",
          psc: "bi-file-earmark-code",
          sql: "bi-database",
          zip: "bi-file-earmark-zip-fill",
          rar: "bi-file-earmark-zip-fill",
          "7z": "bi-file-earmark-zip-fill",
        };
        icon.classList.add(
          "bi",
          extensionIcons[extension] || "bi-file-earmark"
        );

        const link = document.createElement("a");

        const lastSlashIndex = node.url.lastIndexOf("/");
        const path = node.url.substring(0, lastSlashIndex + 1);
        const filename = node.url.substring(lastSlashIndex + 1);


        link.href = "/media/" + path + encodeURIComponent(filename)
        link.target = "_blank";
        link.appendChild(icon);
        link.appendChild(span);
        li.appendChild(link);

        if (userRole === "instructor" || userRole === "admin") {
          const deleteBtn = document.createElement("button");
          deleteBtn.innerHTML = '<i class="bi bi-trash"></i>';
          deleteBtn.title = "Eliminar documento";
          deleteBtn.style.cssText = `
                        background: none;
                        border: none;
                        color: #dc3545;
                        padding: 2px 8px;
                        margin-left: auto;
                        transition: opacity 0.2s;
                    `;

          // Efecto hover para mejor feedback visual
          deleteBtn.addEventListener("mouseenter", () => {
            deleteBtn.style.opacity = "0.8";
            deleteBtn.style.cursor = "pointer";
          });
          deleteBtn.addEventListener("mouseleave", () => {
            deleteBtn.style.opacity = "1";
          });

          li.dataset.folderId = node.parent_id;
          li.dataset.documentId = node.id;
          li.draggable = true;
          li.appendChild(deleteBtn);
        }
      }

      ul.appendChild(li);
    });

    return ul;
  }

  let treeListenersInitialized = false;

  // Agregar event listeners después de renderizar el árbol
  function addEventListeners() {
    if (treeListenersInitialized) return;
    const folderTree = document.getElementById("folderTree");
    if (!folderTree) return;

    // Click delegado: toggle, borrar, abrir modal upload
    folderTree.addEventListener("click", async (e) => {
      // Toggle carpetas (i o span dentro de .folder-item)
      const target = e.target.closest(".folder-item > i, .folder-item > span");
      if (target) {
        const folderId = target.dataset.folderId;
        const icon =
          target.tagName === "I" ? target : target.previousElementSibling;
        toggleFolder(folderId, icon);
        return;
      }

      // Botón eliminar documento
      const trash = e.target.closest(".bi-trash");
      if (trash) {
        const li = trash.closest("li");
        const docId = li?.dataset.documentId;
        const folderId = li?.dataset.folderId;
        if (!docId) return;
        const confirmed = await confirmDeletion("¿Eliminar este documento?");
        if (confirmed) deleteFile(docId, folderId);
        return;
      }

      // Cargar documento (upload-item)
      const uploadItem = e.target.closest(".upload-item");
      if (uploadItem) {
        const folderId = uploadItem.dataset.folderId;
        openUploadModal(folderId);
        return;
      }
    });

    // Dragover delegado
    folderTree.addEventListener("dragover", (e) => {
      const folder = e.target.closest(
        "[data-folder-id][data-droppable='true']"
      );
      if (folder) {
        e.preventDefault(); // necesario para permitir drop
        folder.classList.add("dragover-highlight");
      }
    });

    // Dragleave delegado
    folderTree.addEventListener("dragleave", (e) => {
      const folder = e.target.closest(
        "[data-folder-id][data-droppable='true']"
      );
      if (folder) folder.classList.remove("dragover-highlight");
    });

    // Drop delegado
    folderTree.addEventListener("drop", async (e) => {
      const folder = e.target.closest(
        "[data-folder-id][data-droppable='true']"
      );
      if (!folder) return;
      e.preventDefault();
      folder.classList.remove("dragover-highlight");
      await handleDropOnFolder(folder, e);
    });

    // Dragstart delegado (se propaga)
    folderTree.addEventListener("dragstart", (e) => {
      const docItem = e.target.closest("li[data-document-id]");
      if (!docItem) return;
      e.dataTransfer.setData("type", "document");
      e.dataTransfer.setData("documentId", docItem.dataset.documentId);
      e.dataTransfer.setData("sourceFolderId", docItem.dataset.folderId);
      // Opcional: indicar el efecto
      e.dataTransfer.effectAllowed = "move";
    });

    // Botón subir (fuera del árbol)
    const uploadButton = document.getElementById("uploadButton");
    if (uploadButton) uploadButton.addEventListener("click", uploadFile);

    treeListenersInitialized = true;
  }

  function handleDragOver(event) {
    event.preventDefault();
    event.currentTarget.classList.add("dragover-highlight");
  }

  function handleDragLeave(event) {
    event.currentTarget.classList.remove("dragover-highlight");
  }
  async function handleDropOnFolder(folderElement, e) {
    const folderId = folderElement.dataset.folderId;
    const type = e.dataTransfer.getData("type");

    // --- 1) Mover documento existente ---
    if (type === "document") {
      const documentId = e.dataTransfer.getData("documentId");
      const sourceFolderId = e.dataTransfer.getData("sourceFolderId");
      if (!documentId) return;
      if (String(folderId) === String(sourceFolderId)) return; // mismo lugar: no hacer nada

      const sourceFolderEl = document.querySelector(
        `[data-folder-id="${sourceFolderId}"]`
      );
      const targetFolderEl = folderElement;

      targetFolderEl.classList.add("loading");
      if (sourceFolderEl) sourceFolderEl.classList.add("loading");

      try {
        const resp = await fetch("/api/tree/mover_documento/", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken,
          },
          body: JSON.stringify({
            document_id: documentId,
            target_folder_id: folderId,
          }),
        });

        const data = await resp.json();
        if (!resp.ok) {
          toastError(data.message || "Error al mover el documento.");
          return;
        }

        toastSuccess(data.message || "Documento movido con éxito.");
        // Recargar carpeta origen y destino
        await actualizarCarpeta(sourceFolderId);
        await actualizarCarpeta(folderId);
      } catch (err) {
        console.error("Error moviendo documento:", err);
        toastError("Error al mover el documento.");
      } finally {
        targetFolderEl.classList.remove("loading");
        if (sourceFolderEl) sourceFolderEl.classList.remove("loading");
      }
      return;
    }

    // --- 2) Subir archivos arrastrados ---
    const files = e.dataTransfer.files;
    if (!files || files.length === 0) return;

    const allowedExtensions = [
      "pdf",
      "jpg",
      "jpeg",
      "png",
      "ppt",
      "mp3",
      "mp4",
      "xls",
      "psc",
      "sql",
      "zip",
      "rar",
      "7z",
      "docx",
      "doc",
      "dotx",
      "dotm",
      "docm",
      "dot",
      "htm",
      "html",
      "mht",
      "mhtml",
      "xlt",
      "xltx",
      "xltm",
      "xml",
      "xlsb",
      "xlsx",
      "csv",
      "pptm",
      "pps",
      "ppsx",
      "ppsm",
      "pot",
      "potx",
      "potm",
      "sldx",
      "sldm",
      "pst",
      "ost",
      "msg",
      "eml",
      "mdb",
      "accdb",
      "accde",
      "accdt",
      "accdr",
      "one",
      "pub",
      "vsd",
      "vsdx",
      "xps",
    ];

    const validFiles = [];
    for (let file of files) {
      const extension = file.name.split(".").pop().toLowerCase();

      if (!allowedExtensions.includes(extension)) {
        toastError(
          `El archivo "${file.name}" tiene una extensión no permitida.`
        );
        continue;
      }

      const maxSize = ["zip", "rar", "7z"].includes(extension)
        ? 200 * 1024 * 1024
        : 15 * 1024 * 1024;

      if (file.size > maxSize) {
        toastError(
          `El archivo "${file.name}" supera el tamaño máximo permitido (${
            maxSize === 200 * 1024 * 1024 ? "200MB" : "15MB"
          }).`
        );
        continue;
      }

      validFiles.push(file);
    }

    if (validFiles.length === 0) return;

    const modalDndEl = document.getElementById("uploadModalDnd");
    const modalDnd = new bootstrap.Modal(modalDndEl);
    modalDnd.show();

    const progressContainer =
      document.getElementById("uploadProgressListDnd") ||
      (() => {
        const div = document.createElement("div");
        div.id = "uploadProgressListDnd";
        div.style.marginTop = "10px";
        document.body.appendChild(div);
        return div;
      })();
    progressContainer.innerHTML = "";

    // efecto visual
    folderElement.classList.add("loading");

    try {
      const uploadTasks = validFiles.map((file) => {
        const progressItem = document.createElement("div");
        progressItem.classList.add("mb-2");
        progressItem.innerHTML = `
          <strong>${file.name}</strong>
          <div class="progress" style="height: 20px;">
            <div class="progress-bar" style="width: 0%">0%</div>
          </div>
        `;

        progressContainer.appendChild(progressItem);

        const progressBar = progressItem.querySelector(".progress-bar");

        return new Promise((resolve) => {
          const formData = new FormData();
          formData.append("documento", file);
          formData.append("folder_id", folderId);

          const xhr = new XMLHttpRequest();
          xhr.open("POST", `/api/formacion/fichas/cargar_documentos_ficha/`);
          xhr.setRequestHeader("X-CSRFToken", csrfToken);

          xhr.upload.onprogress = (event) => {
            if (event.lengthComputable) {
              const percent = Math.round((event.loaded / event.total) * 100);
              progressBar.style.width = `${percent}%`;
              progressBar.textContent = `${percent}%`;
            }
          };

          xhr.onload = () => {
            if (xhr.status >= 200 && xhr.status < 300) {
              progressBar.classList.add("bg-success");
              progressBar.textContent = "Completado";
              toastSuccess(`Carga completada para "${file.name}".`);
            } else {
              progressBar.classList.add("bg-danger");
              progressBar.textContent = "Error";
              toastError(`Error al subir "${file.name}".`);
            }
            resolve();
          };

          xhr.onerror = () => {
            progressBar.classList.add("bg-danger");
            progressBar.textContent = "Error conexión ❌";
            toastError(`Error de conexión para "${file.name}".`);
            resolve();
          };

          xhr.send(formData);
        });
      });

      await Promise.all(uploadTasks);
      modalDnd.hide();
      await actualizarCarpeta(folderId);
    } catch (err) {
      console.error("Error en la subida por drag & drop:", err);
      toastError("Error al subir los documentos: " + err.message);
    } finally {
      folderElement.classList.remove("loading");
    }
  }

  function toggleFolder(folderId, icon) {
    const subfolder = document.getElementById(`folder-${folderId}`);

    if (subfolder) {
      const isOpening = !subfolder.classList.contains("visible");

      // Animación y visual
      if (isOpening) {
        // Mostrar antes de animar
        subfolder.style.display = "block";
        // Forzar reflow para activar la transición
        void subfolder.offsetHeight;
        subfolder.classList.add("visible");
      } else {
        subfolder.classList.remove("visible");
        // Ocultar después de la animación
        setTimeout(() => {
          subfolder.style.display = "none";
        }, 300); // Coincide con la duración de la transición CSS
      }

      icon.classList.toggle("bi-folder2-open", isOpening);
      icon.classList.toggle("bi-folder2", !isOpening);
    } else {
      console.error(`No se encontró la carpeta con ID: folder-${folderId}`);
    }
  }

  function openUploadModal(folderId) {
    // Asignar el folderId al botón del modal
    document.getElementById("uploadButton").dataset.folderId = folderId;

    // Mostrar el modal de Bootstrap
    const modal = new bootstrap.Modal(document.getElementById("uploadModal"));
    modal.show();
  }

  async function uploadFile() {
    const folderId = document.getElementById("uploadButton").dataset.folderId;
    const fileInputElement = document.getElementById("fileInput");
    const btnElement = document.getElementById("uploadButton");
    const uploadModal = document.getElementById("uploadModal");
    const inputs = uploadModal.querySelectorAll("input, select, button");

    const files = Array.from(fileInputElement.files);
    if (!files.length) {
      toastError("Seleccione al menos un archivo para subir.");
      return;
    }

    const allowedExtensions = [
      "pdf",
      "jpg",
      "jpeg",
      "png",
      "ppt",
      "mp3",
      "mp4",
      "xls",
      "psc",
      "sql",
      "zip",
      "rar",
      "7z",
      "docx",
      "doc",
      "dotx",
      "dotm",
      "docm",
      "dot",
      "htm",
      "html",
      "mht",
      "mhtml",
      "xlt",
      "xltx",
      "xltm",
      "xml",
      "xlsb",
      "xlsx",
      "csv",
      "pptm",
      "pps",
      "ppsx",
      "ppsm",
      "pot",
      "potx",
      "potm",
      "sldx",
      "sldm",
      "pst",
      "ost",
      "msg",
      "eml",
      "mdb",
      "accdb",
      "accde",
      "accdt",
      "accdr",
      "one",
      "pub",
      "vsd",
      "vsdx",
      "xps",
    ];

    const progressContainer =
      document.getElementById("uploadProgressList") ||
      (() => {
        const div = document.createElement("div");
        div.id = "uploadProgressList";
        div.style.marginTop = "10px";
        uploadModal.querySelector(".modal-body").appendChild(div);
        return div;
      })();

    progressContainer.innerHTML = "";

    inputs.forEach((el) => (el.disabled = true));
    const originalBtnContent = btnElement.innerHTML;
    showSpinner(btnElement);

    try {
      const uploadTasks = [];

      for (const file of files) {
        const extension = file.name.split(".").pop().toLowerCase();
        if (!allowedExtensions.includes(extension)) {
          toastError(
            `El archivo "${file.name}" tiene una extensión no permitida.`
          );
          continue;
        }

        const maxSize = ["zip", "rar"].includes(extension)
          ? 200 * 1024 * 1024
          : 15 * 1024 * 1024;

        if (file.size > maxSize) {
          toastError(
            `El archivo "${file.name}" supera el tamaño máximo permitido (${
              maxSize === 200 * 1024 * 1024 ? "200MB" : "15MB"
            }).`
          );
          continue;
        }

        const progressItem = document.createElement("div");
        progressItem.classList.add("mb-2");
        progressItem.innerHTML = `
        <strong>${file.name}</strong>
        <div class="progress" style="height: 20px;">
          <div class="progress-bar" style="width: 0%">0%</div>
        </div>
      `;
        progressContainer.appendChild(progressItem);
        const progressBar = progressItem.querySelector(".progress-bar");

        const uploadPromise = new Promise((resolve) => {
          const formData = new FormData();
          formData.append("file", file);
          formData.append("folder_id", folderId);

          const xhr = new XMLHttpRequest();
          xhr.open("POST", "/api/tree/cargar_doc/");
          xhr.setRequestHeader("X-CSRFToken", csrfToken);

          xhr.upload.onprogress = (event) => {
            if (event.lengthComputable) {
              const percent = Math.round((event.loaded / event.total) * 100);
              progressBar.style.width = `${percent}%`;
              progressBar.textContent = `${percent}%`;
            }
          };

          xhr.onload = () => {
            if (xhr.status >= 200 && xhr.status < 300) {
              progressBar.classList.add("bg-success");
              progressBar.textContent = "Completado";
              toastSuccess(`Carga completada para "${file.name}".`);
            } else {
              progressBar.classList.add("bg-danger");
              progressBar.textContent = "Error";
              toastError(`Error al subir "${file.name}".`);
            }
            resolve();
          };

          xhr.onerror = () => {
            progressBar.classList.add("bg-danger");
            progressBar.textContent = "Error de conexión ❌";
            toastError(`Error de conexión para "${file.name}".`);
            resolve();
          };

          xhr.send(formData);
        });

        uploadTasks.push(uploadPromise);
      }

      await Promise.all(uploadTasks);

      setTimeout(() => {
        progressContainer.innerHTML = "";
        const modal = bootstrap.Modal.getInstance(
          document.getElementById("uploadModal")
        );
        modal.hide();
        fileInputElement.value = "";
      }, 1500);

      await actualizarCarpeta(folderId);
    } catch (error) {
      console.error("Error al subir el archivo:", error);
      toastError("Ocurrió un error inesperado.");
    } finally {
      inputs.forEach((el) => (el.disabled = false));
      hideSpinner(btnElement, originalBtnContent);
    }
  }

  async function deleteFile(fileId, folderId) {
    try {
      const response = await fetch(`/api/tree/eliminar_documento/${fileId}`, {
        method: "DELETE",
        headers: {
          "X-CSRFToken": csrfToken,
          "Content-Type": "application/json",
        },
      });

      if (response.ok) {
        toastSuccess("Documento eliminado.");

        if (folderId) {
          await actualizarCarpeta(folderId);
        } else {
          verTree();
        }
      } else {
        toastError("Error al eliminar el archivo");
      }
    } catch (error) {
      console.error("Error al borrar el archivo:", error);
    }
  }

  async function actualizarCarpeta(folderId) {
    try {
      const response = await fetch(
        `/api/tree/obtener_hijos_carpeta/${folderId}`
      );
      const data = await response.json();

      const subFolderContainer = document.getElementById(`folder-${folderId}`);
      if (!subFolderContainer) {
        console.error(
          `No se encontró el contenedor para la carpeta: folder-${folderId}`
        );
        return;
      }

      subFolderContainer.innerHTML = "";

      // Botón de carga
      const uploadLi = document.createElement("li");
      uploadLi.classList.add("upload-item");
      uploadLi.style.listStyle = "none";
      uploadLi.dataset.folderId = folderId;

      const uploadIcon = document.createElement("i");
      uploadIcon.classList.add("bi", "bi-plus-circle");

      const uploadSpan = document.createElement("span");
      uploadSpan.textContent = "Cargar documento";

      uploadLi.appendChild(uploadIcon);
      uploadLi.appendChild(uploadSpan);
      subFolderContainer.appendChild(uploadLi);

      // Renderizar hijos
      if (data.length > 0) {
        const hijos = renderTree(data);
        if (hijos) {
          subFolderContainer.appendChild(hijos);
        }
      }
    } catch (error) {
      console.error("Error al actualizar la carpeta:", error);
    }
  }

  function getFichaIdFromUrl() {
    const pathSegments = window.location.pathname
      .split("/")
      .filter((segment) => segment);
    const fichaIndex = pathSegments.indexOf("ficha");

    return fichaIndex !== -1 && pathSegments[fichaIndex + 1]
      ? pathSegments[fichaIndex + 1]
      : null;
  }

  // *******************************************************************
  // *                                                                 *
  // *        ¡ADVERTENCIA! ZONA DE CÓDIGO PORTAFOLIO APRENDIZ         *
  // *                                                                 *
  // *******************************************************************

  const validarAprendizBtn = document.getElementById("validateBtn");

  validarAprendizBtn.addEventListener("click", async (e) => {
    const aprendizDniEl = document.getElementById("aprendizDni");
    const aprendizDni = aprendizDniEl.value.trim();
    const originalBtnContent = validarAprendizBtn.innerHTML;
    showSpinner(validarAprendizBtn);

    try {
      const response = await fetch(
        `/api/usuarios/aprendices/validar_dni/?dni=${aprendizDni}`
      );
      const data = await response.json();

      if (validarErrorDRF(response, data)) return;

      if (data.existe === false) {
        if (
          await confirmAction({
            message: "¿Desea crear un nuevo aprendiz?",
            title: "Aprendiz no encontrado",
            icon: "question",
          })
        ) {
          const modalEl = document.getElementById("modalAgregarAprendiz");
          const modalInstance = bootstrap.Modal.getOrCreateInstance(modalEl);
          modalInstance.hide();

          const modalCrearApre = document.getElementById("modalCrearAprendiz");
          const modalCrearApreI = new bootstrap.Modal(modalCrearApre);
          modalCrearApreI.show();
        }
        return;
      }

      if (data.existe === true && data.asociado === false) {
        if (
          await confirmAction({
            message:
              "El aprendiz existe pero no esta asociado a ninguna ficha, ¿Desea asociarlo a esta?",
            title: "Aprendiz sin ficha",
            icon: "question",
          })
        ) {
          asociarAprendiz(aprendizDni);
        }
        return;
      }

      if (data.existe === true && data.asociado === true) {
        confirmAction({
          message: `El aprendiz ya esta asociado a la ficha ${
            data.message.split("ficha")[1]
          }. Primero gestione el retiro con el instructor responsable.`,
          title: "Aprendiz ya asociado",
          icon: "info",
          confirmButtonText: "Aceptar",
        });
        return;
      }
    } catch (error) {
      toastError("Error al validar aprendiz");
      console.error(error);
    } finally {
      hideSpinner(validarAprendizBtn, originalBtnContent);
      aprendizDniEl.value = "";
    }
  });

  async function asociarAprendiz(aprendizDni) {
    try {
      const response = await fetch(
        `/api/usuarios/aprendices/${aprendizDni}/asociar_ficha/?ficha_id=${fichaId}`,
        {
          method: "POST",
          headers: {
            "X-CSRFToken": csrfToken,
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "application/json",
          },
        }
      );
      const data = await response.json();
      if (validarErrorDRF(response, data)) return;
      toastSuccess(data.message);
      location.reload();
    } catch (error) {
      toastError(error);
    }
  }

  const formCrearApre = document.getElementById("formCrearApre");

  formCrearApre.addEventListener("submit", async (e) => {
    e.preventDefault();
    const btn = document.getElementById("btnCrear");
    const originalBtnContent = btn.innerHTML;
    const alertError = document.getElementById("errores");
    const alertSuccess = document.getElementById("resumen");
    const archivoInput = document.getElementById("archivoAprendiz");

    alertError.classList.add("d-none");
    alertSuccess.classList.add("d-none");
    alertError.textContent = "";
    alertSuccess.textContent = "";

    const archivo = archivoInput.files[0];
    if (!archivo) {
      toastError("Debe seleccionar un archivo.");
      return;
    }

    if (!archivo.name.endsWith(".csv")) {
      toastError("Solo se permiten archivos .csv");
      return;
    }

    const formData = new FormData();
    formData.append("archivo", archivo);
    formData.append("ficha_id", fichaId);

    setFormDisabled(formCrearApre, true);
    showSpinner(btn);

    try {
      const response = await fetch(`/api/usuarios/aprendices/crear_un_apre/`, {
        method: "POST",
        body: formData,
        headers: {
          "X-CSRFToken": csrfToken,
        },
      });

      const data = await response.json();

      if (!response.ok) {
        if (data.errores) {
          alertError.textContent = data.errores.join("\n");
          alertError.classList.remove("d-none");
        }
        toastError(data.message || "Error desconocido");
        return;
      }

      alertSuccess.innerHTML = `<strong>Resultado:</strong> ${data.message}`;
      alertSuccess.classList.remove("d-none");
      toastSuccess(data.message);
      formCrearApre.reset();
      archivoInput.value = "";
      location.reload();
    } catch (error) {
      console.error(error);
      toastError("Error inesperado");
    } finally {
      setFormDisabled(formCrearApre, false);
      hideSpinner(btn, originalBtnContent);
    }
  });

  tableAprendicesElement.addEventListener("click", async (e) => {
    //== Boton ver portafolio aprendiz
    const target = e.target.closest(".ver-portafolio");
    // if (target) {
    //     const aprendizId = target.getAttribute("data-id");
    //     const aprendizNombre = target.getAttribute("data-nombre");

    //     document.getElementById("portafolioAprendizModalLabel").textContent = `Portafolio de ${aprendizNombre}`;

    //     document.getElementById("folderTreeAprendiz").innerHTML = "";
    //     //document.getElementById("historial-body").innerHTML = "Pendiente desarrollo!";

    //     cargarPortafolio(aprendizId);
    //     // cargarTablaHistorial(aprendizId);

    //     const modalEl = document.getElementById("portafolioAprendizModal");
    //     modalEl.removeAttribute('aria-hidden');
    //     new bootstrap.Modal(modalEl).show();

    //     modalEl.addEventListener("hidden.bs.modal", function () {
    //         document.getElementById("folderTreeAprendiz").innerHTML = "";
    //         modalEl.setAttribute('aria-hidden', 'true');

    //         if (document.activeElement && modalEl.contains(document.activeElement)) {
    //             document.activeElement.blur();
    //         }

    //         const btnAbrir = document.querySelector('.ver-portafolio');
    //         if (btnAbrir) btnAbrir.focus();
    //     });
    // }
    if (target) {
      Swal.fire({
        icon: "info",
        title: "Función inhabilitada temporalmente",
        text: "Esta acción estará inhabilitada temporalmente debido a procesos de mejora.",
        confirmButtonText: "Ok",
      });
    }
    //== Boton ver perfil aprendiz
    const target1 = e.target.closest(".perfil-btn");

    if (target1) {
      const contenidoPerfil = document.getElementById("contenidoPerfil");
      contenidoPerfil.innerHTML = "<p>Cargando perfil...</p>";
      fadeIn(loadingDiv);
      const aprendizId = target1.dataset.id;

      const modalElement = document.getElementById("modalVerPerfil");
      const modalInstance = new bootstrap.Modal(modalElement);
      modalInstance.show();

      fetch(`/api/aprendices/modal/ver_perfil_aprendiz/${aprendizId}`)
        .then((response) => {
          if (!response.ok) {
            throw new Error("Error en la respuesta del servidor");
          }
          return response.text();
        })
        .then((data) => {
          contenidoPerfil.innerHTML = data;
        })
        .catch((error) => {
          console.error("Error al cargar perfil:", error);
          contenidoPerfil.innerHTML =
            '<p class="text-danger">Error al cargar el perfil</p>';
        })
        .finally(() => {
          fadeOut(loadingDiv);
        });
    }

    const target2 = e.target.closest(".desertar-aprendiz");
    if (target2) {
      const confirm = await confirmAction({
        message:
          "¿Esta seguro de marcar como desertado al aprendiz?, esta acción no se puede deshacer",
        title: "Desertar aprendiz",
        icon: "warning",
      });
      if (!confirm) return;
      const originalBtnContent = target2.innerHTML;
      showSpinner(target2);
      const aprendizId = target2.getAttribute("data-id");

      try {
        await desertarAprendiz(aprendizId);
      } finally {
        hideSpinner(target2, originalBtnContent);
      }
    }

    const target3 = e.target.closest(".desasociar-aprendiz");
    if (target3) {
      const confirm = await confirmAction({
        message:
          "¿Esta seguro que desea desasociar al aprendiz?, quedara habilitado para su registro en otra ficha",
        title: "Eliminar de la ficha",
        icon: "warning",
      });
      if (!confirm) return;
      const originalBtnContent = target3.innerHTML;
      showSpinner(target3);
      const aprendizId = target3.getAttribute("data-id");

      try {
        await desasociarAprendiz(aprendizId);
      } finally {
        hideSpinner(target3, originalBtnContent);
      }
    }

    const target4 = e.target.closest(".editar-aprendiz");
    if (target4) {
      const originalBtnContent = target4.innerHTML;
      const aprendizId = target4.getAttribute("data-id");
      showSpinner(target4);

      const modalEl = document.getElementById("editAprendizModal");
      const modalInstance = new bootstrap.Modal(modalEl);
      modalInstance.show();

      try {
        await fillDataAprendiz(aprendizId);
      } finally {
        hideSpinner(target4, originalBtnContent);
      }
    }
  });

  const formEditarAprendiz = document.getElementById("formEditarAprendiz");

  async function fillDataAprendiz(aprendizId) {
    setFormDisabled(formEditarAprendiz, true);
    try {
      const response = await fetch(`/api/usuarios/aprendices/${aprendizId}/`);
      const data = await response.json();

      if (data.perfil) {
        document.querySelector("#nom").value = data.perfil.nom || "";
        document.querySelector("#apelli").value = data.perfil.apelli || "";
        document.querySelector("#dni").value = data.perfil.dni || "";
        document.querySelector("#tele").value = data.perfil.tele || "";
        document.querySelector("#dire").value = data.perfil.dire || "";
        document.querySelector("#mail").value = data.perfil.mail || "";
        document.querySelector("#fecha_naci").value =
          data.perfil.fecha_naci || "";
        setSelectValue("tipo_dni", data.perfil.tipo_dni || "");
        setSelectValue("gene", data.perfil.gene || "");
      }

      if (data.repre_legal) {
        document.querySelector("#nom_repre").value = data.repre_legal.nom || "";
        document.querySelector("#dni_repre").value = data.repre_legal.dni || "";
        document.querySelector("#tele_repre").value =
          data.repre_legal.tele || "";
        document.querySelector("#dire_repre").value =
          data.repre_legal.dire || "";
        document.querySelector("#mail_repre").value =
          data.repre_legal.mail || "";
        setSelectValue("paren_repre", data.repre_legal.paren || "");
      } else {
        document.querySelector("#nom_repre").value = "";
        document.querySelector("#dni_repre").value = "";
        document.querySelector("#tele_repre").value = "";
        document.querySelector("#dire_repre").value = "";
        document.querySelector("#mail_repre").value = "";
        setSelectValue("paren_repre", "");
      }

      formEditarAprendiz.dataset.action = `/api/usuarios/aprendices/${data.id}/`;
    } catch (e) {
      toastError(e);
    } finally {
      setFormDisabled(formEditarAprendiz, false);
    }
  }

  formEditarAprendiz.addEventListener("submit", async (e) => {
    e.preventDefault();

    const btn = document.getElementById("btnSubmit");
    const originalBtnContent = btn.innerHTML;

    showSpinner(btn);
    setFormDisabled(formEditarAprendiz, true);

    const sanitize = (value) => (value.trim() === "" ? null : value);
    const repreLegalPayload = {
      nom: sanitize(
        formEditarAprendiz.querySelector('[name="nom_repre"]').value
      ),
      dni: sanitize(
        formEditarAprendiz.querySelector('[name="dni_repre"]').value
      ),
      tele: sanitize(
        formEditarAprendiz.querySelector('[name="tele_repre"]').value
      ),
      dire: sanitize(
        formEditarAprendiz.querySelector('[name="dire_repre"]').value
      ),
      mail: sanitize(
        formEditarAprendiz.querySelector('[name="mail_repre"]').value
      ),
      paren: sanitize(
        formEditarAprendiz.querySelector('[name="paren_repre"]').value
      ),
    };

    const tieneDatosRepre = Object.values(repreLegalPayload).some(
      (val) => val !== null
    );

    const payload = {
      perfil: {
        nom: sanitize(formEditarAprendiz.querySelector('[name="nom"]').value),
        apelli: sanitize(
          formEditarAprendiz.querySelector('[name="apelli"]').value
        ),
        tipo_dni: sanitize(
          formEditarAprendiz.querySelector('[name="tipo_dni"]').value
        ),
        dni: sanitize(formEditarAprendiz.querySelector('[name="dni"]').value),
        tele: sanitize(formEditarAprendiz.querySelector('[name="tele"]').value),
        dire: sanitize(formEditarAprendiz.querySelector('[name="dire"]').value),
        gene: sanitize(formEditarAprendiz.querySelector('[name="gene"]').value),
        mail: sanitize(formEditarAprendiz.querySelector('[name="mail"]').value),
        fecha_naci: sanitize(
          formEditarAprendiz.querySelector('[name="fecha_naci"]').value
        ),
      },
    };

    if (tieneDatosRepre) {
      payload.repre_legal = repreLegalPayload;
    } else {
      payload.repre_legal = null;
    }

    try {
      const response = await fetch(formEditarAprendiz.dataset.action, {
        method: "PATCH",
        headers: {
          "X-CSRFToken": csrfToken,
          "X-Requested-With": "XMLHttpRequest",
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      const data = await response.json();
      if (validarErrorDRF(response, data)) return;

      toastSuccess(data.message);
      location.reload();
    } catch (e) {
      toastError(e);
    } finally {
      hideSpinner(btn, originalBtnContent);
      setFormDisabled(formEditarAprendiz, false);
    }
  });

  async function desasociarAprendiz(aprendizId) {
    try {
      const response = await fetch(`/api/usuarios/aprendices/${aprendizId}/`, {
        method: "PATCH",
        headers: {
          "X-CSRFToken": csrfToken,
          "X-Requested-With": "XMLHttpRequest",
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ ficha: null }),
      });

      const data = await response.json();

      if (validarErrorDRF(response, data)) return;

      toastSuccess(data.message);
      location.reload();
    } catch (error) {
      toastError(error);
    }
  }

  async function desertarAprendiz(aprendizId) {
    try {
      const response = await fetch(`/api/usuarios/aprendices/${aprendizId}/`, {
        method: "PATCH",
        headers: {
          "X-CSRFToken": csrfToken,
          "X-Requested-With": "XMLHttpRequest",
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ esta: "desertado" }),
      });
      const data = await response.json();

      if (validarErrorDRF(response, data)) return;

      toastSuccess(data.message);
      location.reload();
    } catch (error) {
      toastError(error);
    }
  }

  async function cargarPortafolio(aprendizId) {
    fadeIn(loadingDiv);
    try {
      const apiUrl = `/api/tree/obtener_carpetas_aprendiz/${aprendizId}/`;
      const response = await fetch(apiUrl);
      const data = await response.json();

      const portafolioContainer = document.getElementById("folderTreeAprendiz");
      portafolioContainer.innerHTML = "";

      const portafolioTree = renderPortafolioTree(data);
      if (portafolioTree) {
        portafolioContainer.appendChild(portafolioTree);
      }

      agregarEventListenersPortafolio();
    } catch (error) {
      console.error("Error cargando los nodos:", error);
      document.getElementById("folderTreeAprendiz").innerHTML =
        '<tr><td colspan="4" class="text-center text-danger">Error al cargar nodos.</td></tr>';
    } finally {
      fadeOut(loadingDiv);
    }
  }

  // Función de renderizado optimizada para portafolios
  function renderPortafolioTree(nodes) {
    if (!nodes || nodes.length === 0) return null;

    const ul = document.createElement("ul");
    ul.classList.add("folder-list", "portafolio-tree");

    nodes.forEach((node) => {
      const li = document.createElement("li");
      li.classList.add("folder-item", "portafolio-item");

      const icon = document.createElement("i");
      const span = document.createElement("span");
      span.textContent = node.name;

      // Usamos dataset para almacenar el ID según el tipo
      const dataId = node.tipo === "carpeta" ? "folderId" : "documentId";
      icon.dataset[dataId] = node.id;
      span.dataset[dataId] = node.id;

      // Configuración específica para portafolio
      if (node.tipo === "carpeta") {
        icon.classList.add("bi", "bi-folder2");

        const subFolderContainer = document.createElement("ul");
        subFolderContainer.classList.add("folder-children");
        subFolderContainer.id = `portafolio-folder-${node.id}`;

        if (
          userRole === "instructor" &&
          (!node.children ||
            node.children.length === 0 ||
            node.children.every((child) => child.tipo === "documento"))
        ) {
          // Botón de carga (solo para carpetas)
          const uploadLi = document.createElement("li");
          uploadLi.classList.add("upload-item");
          uploadLi.style.listStyle = "none";
          uploadLi.dataset.folderId = node.id;

          const uploadIcon = document.createElement("i");
          uploadIcon.classList.add("bi", "bi-plus-circle");

          const uploadSpan = document.createElement("span");
          uploadSpan.textContent = "Cargar documento";

          uploadLi.appendChild(uploadIcon);
          uploadLi.appendChild(uploadSpan);
          subFolderContainer.appendChild(uploadLi);
        }
        if (node.children && node.children.length > 0) {
          subFolderContainer.appendChild(renderPortafolioTree(node.children));
        }

        li.appendChild(icon);
        li.appendChild(span);
        li.appendChild(subFolderContainer);
      } else if (node.tipo === "documento") {
        // Documentos con colores según tipo
        const extension = node.documento_nombre.split(".").pop().toLowerCase();
        // Determinar icono según extensión
        const extensionIcons = {
          jpg: "bi-image",
          png: "bi-image",
          jpeg: "bi-image",
          pdf: "bi-file-earmark-pdf",
          xlsx: "bi-file-earmark-spreadsheet",
          csv: "bi-file-earmark-spreadsheet",
          docx: "bi-file-earmark-richtext",
        };
        icon.classList.add(
          "bi",
          extensionIcons[extension] || "bi-file-earmark"
        );

        const link = document.createElement("a");
        link.href = "/media/" + node.url;
        link.target = "_blank";
        link.append(icon, span);
        li.appendChild(link);

        if (userRole === "instructor") {
          const deleteBtn = document.createElement("button");
          deleteBtn.innerHTML = '<i class="bi bi-trash"></i>';
          deleteBtn.title = "Eliminar documento";
          deleteBtn.style.cssText = `
                        background: none;
                        border: none;
                        color: #dc3545;
                        padding: 2px 8px;
                        margin-left: auto;
                        transition: opacity 0.2s;
                    `;

          // Efecto hover para mejor feedback visual
          deleteBtn.addEventListener("mouseenter", () => {
            deleteBtn.style.opacity = "0.8";
            deleteBtn.style.cursor = "pointer";
          });
          deleteBtn.addEventListener("mouseleave", () => {
            deleteBtn.style.opacity = "1";
          });

          li.dataset.folderId = node.parent_id;
          li.appendChild(deleteBtn);
        }
      }

      ul.appendChild(li);
    });

    return ul;
  }

  let portafolioClickListener = null;

  // Event listeners específicos para el portafolio
  function agregarEventListenersPortafolio() {
    const treeContainer = document.getElementById("folderTreeAprendiz");

    // Eliminar listener anterior si existe
    if (portafolioClickListener) {
      treeContainer.removeEventListener("click", portafolioClickListener);
    }

    // Crear nuevo listener
    portafolioClickListener = async function (e) {
      const target = e.target.closest(".folder-item > i, .folder-item > span");
      if (target) {
        const folderId = target.dataset.folderId;
        const icon =
          target.tagName === "I" ? target : target.previousElementSibling;
        togglePortafolioFolder(folderId, icon);
      }

      const target2 = e.target.closest(".bi-trash");
      if (target2) {
        const li = target2.closest("li");
        const docId =
          li.querySelector("[data-document-id]")?.dataset.documentId;
        const folderId = li.dataset.folderId;
        if (!docId) return;

        const confirmed = await confirmToast("¿Eliminar este documento?");
        if (confirmed) deleteFileAprendiz(docId, folderId);
      }

      const target3 = e.target.closest(".upload-item");
      if (target3) {
        const folderId = target3.dataset.folderId;
        openUploadModalAprendiz(folderId);
      }
    };

    treeContainer.addEventListener("click", portafolioClickListener);
    document
      .getElementById("uploadButtonAprendiz")
      .addEventListener("click", uploadFileAprendiz);
  }

  // Toggle adaptado para portafolio
  function togglePortafolioFolder(folderId, icon) {
    const subfolder = document.getElementById(`portafolio-folder-${folderId}`);

    if (subfolder) {
      const isOpening = !subfolder.classList.contains("visible");

      // Forzar cierre de cualquier animación pendiente
      subfolder.style.transition = "none";

      if (isOpening) {
        subfolder.style.display = "block";
        void subfolder.offsetHeight; // Reflow
        subfolder.style.transition = "";
        subfolder.classList.add("visible");
      } else {
        subfolder.classList.remove("visible");
        subfolder.style.display = "none"; // Cierre inmediato
      }

      icon.classList.toggle("bi-folder2-open", isOpening);
      icon.classList.toggle("bi-folder2", !isOpening);
    }
  }

  function openUploadModalAprendiz(folderId) {
    // Asignar el folderId al botón del modal
    document.getElementById("uploadButtonAprendiz").dataset.folderId = folderId;

    // Mostrar el modal de Bootstrap
    const modal = new bootstrap.Modal(
      document.getElementById("uploadModalAprendiz")
    );
    modal.show();
  }

  async function uploadFileAprendiz() {
    const folderId = document.getElementById("uploadButtonAprendiz").dataset
      .folderId;
    const fileInputElement = document.getElementById("fileInputAprendiz");
    const btnElement = document.getElementById("uploadButtonAprendiz");
    const uploadModal = document.getElementById("uploadModalAprendiz");
    const inputs = uploadModal.querySelectorAll("input, select, button");

    const file = fileInputElement.files[0];
    if (!file) {
      toastError("Seleccione un archivo para subir.");
      return;
    }

    // Validación de tipo de archivo
    const allowedExtensions = ["pdf", "xlsx", "csv", "jpg", "jpeg", "png"];
    const extension = file.name.split(".").pop().toLowerCase();
    if (!allowedExtensions.includes(extension)) {
      toastError(
        "Tipo de archivo no permitido. Solo se permiten PDF, Excel o imágenes."
      );
      return;
    }

    // Validación de tamaño
    const maxSize = 7 * 1024 * 1024; // 7MB
    if (file.size > maxSize) {
      toastError("El archivo supera el tamaño máximo permitido (7 MB).");
      return;
    }

    inputs.forEach((el) => (el.disabled = true));
    const originalBtnContent = btnElement.innerHTML;
    showSpinner(btnElement);

    const formData = new FormData();
    formData.append("file", file);
    formData.append("folder_id", folderId);

    try {
      const response = await fetch("/api/tree/cargar_doc_aprendiz/", {
        method: "POST",
        headers: { "X-CSRFToken": csrfToken },
        body: formData,
      });

      if (response.ok) {
        toastSuccess("Documento subido con éxito.");
        const modal = bootstrap.Modal.getInstance(
          document.getElementById("uploadModalAprendiz")
        );
        modal.hide();
        fileInputElement.value = "";

        await actualizarCarpetaAprendiz(folderId);
      } else {
        toastError("Error al subir el documento.");
      }
    } catch (error) {
      console.error("Error al subir el archivo:", error);
      toastError("Ocurrió un error inesperado.");
    } finally {
      inputs.forEach((el) => (el.disabled = false));
      hideSpinner(btnElement, originalBtnContent);
    }
  }

  async function deleteFileAprendiz(fileId, folderId) {
    try {
      const response = await fetch(
        `/api/tree/eliminar_documento_aprendiz/${fileId}`,
        {
          method: "DELETE",
          headers: {
            "X-CSRFToken": csrfToken,
            "Content-Type": "application/json",
          },
        }
      );

      if (response.ok) {
        toastSuccess("Documento eliminado.");

        if (folderId) {
          await actualizarCarpetaAprendiz(folderId);
        } else {
          verTree();
        }
      } else {
        toastError("Error al eliminar el archivo");
      }
    } catch (error) {
      console.error("Error al borrar el archivo:", error);
    }
  }

  async function actualizarCarpetaAprendiz(folderId) {
    try {
      const response = await fetch(
        `/api/tree/obtener_hijos_carpeta_aprendiz/${folderId}`
      );
      const data = await response.json();

      const subFolderContainer = document.getElementById(
        `portafolio-folder-${folderId}`
      );
      if (!subFolderContainer) {
        console.error(
          `No se encontró el contenedor para la carpeta: folder-${folderId}`
        );
        return;
      }

      subFolderContainer.innerHTML = "";

      // Botón de carga
      const uploadLi = document.createElement("li");
      uploadLi.classList.add("upload-item");
      uploadLi.style.listStyle = "none";
      uploadLi.dataset.folderId = folderId;

      const uploadIcon = document.createElement("i");
      uploadIcon.classList.add("bi", "bi-plus-circle");

      const uploadSpan = document.createElement("span");
      uploadSpan.textContent = "Cargar documento";

      uploadLi.appendChild(uploadIcon);
      uploadLi.appendChild(uploadSpan);
      subFolderContainer.appendChild(uploadLi);

      // Renderizar hijos si hay
      if (data.length > 0) {
        const hijos = renderPortafolioTree(data);
        if (hijos) {
          subFolderContainer.appendChild(hijos);
        }
      }
    } catch (error) {
      console.error("Error al actualizar la carpeta:", error);
    }
  }

  // *******************************************************************
  // *                                                                 *
  // *        ¡ADVERTENCIA! ZONA DE CÓDIGO CRONOGRAMA                  *
  // *                                                                 *
  // *******************************************************************

  // const btnCrearActividad = document.getElementById('btnCrearActividad');
  // const formCrearActividad = document.getElementById('formCrearActividad');
  // const errorDiv = document.getElementById('errorCrearActividad');
  // const tableCaliElement = document.getElementById('actividades_ficha');
  // const formEditarActividad = document.getElementById('formEditarActividad');
  // const btnEditarActividad = document.getElementById('btnEditarActividad');

  // // ======= Inicialización de DataTables =======
  // const tableCronograma = new DataTable(tableCaliElement, {
  //     language: {
  //         url: 'https://cdn.datatables.net/plug-ins/2.1.8/i18n/es-ES.json',
  //     }
  // });

  // cargarDatosTablaCronograma();

  // //== LLamar a la API Actividades
  // async function cargarDatosTablaCronograma(){
  //     fadeIn(loadingDiv);
  //     try {
  //         const response = await fetch(`/api/ficha/actividades/${fichaId}/`);
  //         const data = await response.json();
  //         actualizarTabla(data);
  //         actualizarEstadoFase();
  //     } catch (error) {
  //         console.error('Error al cargar actividades:', error);
  //     } finally {
  //         fadeOut(loadingDiv);
  //         reiniciarTooltips();
  //     }
  // }

  // //== Poblar tabla Cronograma
  // function actualizarTabla(data) {
  //     tableCronograma.clear();

  //     data.forEach(item => {
  //         let botones = `
  //             <button class="btn btn-outline-primary btn-sm btn-detalle-actividad mb-1"
  //                 data-id="${item.id}"
  //                 data-bs-toggle="tooltip"
  //                 data-bs-placement="top"
  //                 title="Detalle">
  //                 <i class="bi bi-plus-lg"></i>
  //             </button>
  //             <button class="btn btn-outline-success btn-sm btn-calificar mb-1"
  //                 data-actividad-id="${item.id}"
  //                 data-nombre="${item.nom}"
  //                 data-fase="${item.fase}"
  //                 data-fecha-inicio="${item.fecha_ini_acti}"
  //                 data-fecha-fin="${item.fecha_fin_acti}"
  //                 data-fecha-inicio-cali="${item.fecha_ini_cali}"
  //                 data-fecha-fin-cali="${item.fecha_fin_cali}"
  //                 data-bs-toggle="tooltip"
  //                 data-bs-placement="top"
  //                 title="Calificar">
  //                 <i class="bi bi-clipboard-check"></i>
  //             </button>`;

  //         // Verifica si la fase del item es igual a la fase actual para permitir botón Editar
  //         if (item.fase.toLowerCase() === item.fase_ficha.toLowerCase()) {
  //             botones += `
  //             <button class="btn btn-outline-warning btn-sm btn-editar-actividad mb-1"
  //                 data-id="${item.id}"
  //                 data-bs-toggle="tooltip"
  //                 data-bs-placement="top"
  //                 title="Editar">
  //                 <i class="bi bi-pencil-square"></i>
  //             </button>`;
  //         }

  //         tableCronograma.row.add([
  //             item.nom,
  //             item.fecha_ini_acti,
  //             item.fecha_fin_acti,
  //             item.fecha_ini_cali,
  //             item.fecha_fin_cali,
  //             item.fase,
  //             botones
  //         ]);
  //     });

  //     tableCronograma.draw();

  //     document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(el => {
  //         const tooltipInstance = bootstrap.Tooltip.getInstance(el);
  //         if (tooltipInstance) {
  //             tooltipInstance.dispose();
  //         }
  //     });

  //     document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(el => {
  //         new bootstrap.Tooltip(el);
  //     });

  // }

  // async function actualizarEstadoFase() {
  //     fadeIn(loadingDiv);
  //     try {
  //         const response = await fetch(`/api/ficha/obtener_estado_fase/${fichaId}`, {
  //             method: 'GET',
  //             headers: {
  //                 'Accept': 'application/json'
  //             }
  //         });

  //         if (!response.ok) {
  //             throw new Error('Error en la solicitud');
  //         }

  //         const data = await response.json();

  //         // Construir HTML de botones
  //         let botonesHtml = '';

  //         if (data.raps_count == 0) {
  //             botonesHtml += `<button class="btn btn-warning btn-sm btn-cerrar-fase">Cerrar fase</button> `;
  //         }

  //         // Validar si el usuario es admin
  //         if (userRole == 'admin') {
  //             botonesHtml += `<button class="btn btn-danger btn-sm btn-devolver-fase">Devolver fase</button>`;
  //         }

  //         // Construir HTML del estado
  //         let estadoHtml = '';

  //         if (data.raps_count > 0) {
  //             estadoHtml += `<span class="text-danger fw-bold"
  //                                 style="cursor: pointer; text-decoration: underline dotted;"
  //                                 data-bs-toggle="popover"
  //                                 data-bs-html="true"
  //                                 data-bs-placement="top"
  //                                 data-bs-content="${data.raps_pendientes}">
  //                                 <i class="bi bi-info-circle" style="color: #0d6efd;"></i>
  //                                 Faltan ${data.raps_count} RAPS para la fase ${data.fase}
  //                         </span><br>`;
  //         }

  //         estadoHtml += `<span class="${data.raps_count == 0 ? 'text-success' : 'text-danger'}">
  //                         Estado: ${data.raps_count == 0 ? 'Completo' : 'Incompleto'}
  //                     </span>`;

  //         // Actualizar los contenedores
  //         document.getElementById('botones-fase').innerHTML = botonesHtml;
  //         document.getElementById('estado-fase').innerHTML = estadoHtml;

  //         // Inicializar o reinicializar popovers
  //         const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
  //         popoverTriggerList.map(function (popoverTriggerEl) {
  //             // Si ya hay un popover anterior, lo destruimos
  //             const existingPopover = bootstrap.Popover.getInstance(popoverTriggerEl);
  //             if (existingPopover) {
  //                 existingPopover.dispose();
  //             }
  //             // Luego, creamos uno nuevo
  //             return new bootstrap.Popover(popoverTriggerEl);
  //         });

  //     } catch (error) {
  //         console.error('Hubo un error:', error);
  //     } finally {
  //         fadeOut(loadingDiv);
  //     }
  // }

  // //== Boton crear actividad
  // btnCrearActividad.addEventListener('click', async () => {
  //     const formData = new FormData(formCrearActividad);
  //     const originalBtnContent = btnCrearActividad.innerHTML;
  //     formCrearActividad.querySelectorAll('input, select, button').forEach(el => el.disabled = true);
  //     showSpinner(btnCrearActividad)
  //     try {
  //         const response = await fetch(`/api/ficha/crear_actividad/${fichaId}/`, {
  //             method: "POST",
  //             headers: { 'X-CSRFToken': csrfToken },
  //             body: formData
  //         });

  //         if (response.ok) {
  //             toastSuccess("Actividad creada con éxito.");
  //             bootstrap.Modal.getInstance(document.getElementById("crearActividadModal")).hide();
  //             formCrearActividad.reset();
  //             tomSelectMultiple.clear();
  //             tomSelectRaps.clear();
  //             cargarDatosTablaCronograma();
  //         } else {
  //             const data = await response.json();
  //             console.warn("Respuesta del servidor:", data);
  //             toastError(data.message)
  //             errorDiv.innerHTML = data.errors || "Error desconocido al crear la actividad.";
  //         }
  //     } catch (error) {
  //         console.error("Error al crear la actividad (catch):", error);
  //         errorDiv.innerHTML = "Ocurrió un error inesperado.";
  //     } finally {
  //         hideSpinner(btnCrearActividad, originalBtnContent);
  //         formCrearActividad.querySelectorAll('input, select, button').forEach(el => el.disabled = false);
  //     }
  // });

  // //== Boton ver calendario
  // const calendarModal = document.getElementById('calendarioActividadModal');
  // let calendar = null;

  // calendarModal.addEventListener('shown.bs.modal', async()=> {
  //     const calendarElement = document.getElementById('calendario');
  //     calendarElement.innerHTML = `
  //         <div class="d-flex justify-content-center align-items-center" style="height: 300px;">
  //         <div class="spinner-border text-primary" role="status">
  //             <span class="visually-hidden">Cargando...</span>
  //         </div>
  //         </div>
  //     `;
  //     if (calendar !== null) {
  //         calendar.destroy();
  //         calendar = null;
  //     }

  //     try {
  //         const response = await fetch(`/api/ficha/ver_cronograma/${fichaId}`);
  //         const data = await response.json();

  //         const faseColors = {
  //             analisis: '#0d6efd',      // azul
  //             planeacion: '#ffc107',    // amarillo
  //             ejecucion: '#dc3545',     // rojo
  //             evaluacion: '#20c997',    // verde azulado
  //         };

  //         const eventos = data.flatMap(item => {
  //             const colorFase = faseColors[item.fase] || '#6c757d'; // gris por defecto si no se reconoce

  //             return [
  //                 {
  //                     title: item.title,
  //                     start: item.start,
  //                     end: item.end,
  //                     color: colorFase,
  //                 },
  //                 {
  //                     title: `${item.title} (Revisión)`,
  //                     start: item.start_check,
  //                     end: item.end_check,
  //                     color: '#198754', // verde para el rango de revisión
  //                 }
  //             ];
  //         });

  //         calendarElement.innerHTML ="";
  //         calendar = new FullCalendar.Calendar(calendarElement, {
  //             initialView: 'dayGridMonth',
  //             locale: 'es',
  //             height: 600,
  //             events: eventos,
  //             headerToolbar: {
  //                 left: 'prev,next today',
  //                 center: 'title',
  //                 right: 'dayGridMonth,timeGridWeek'
  //             },
  //             eventColor: '#0d6efd',
  //             eventDisplay: 'block',
  //         });

  //         calendar.render();
  //     } catch (error) {
  //         console.error('Error al cargar el calendario:', error);
  //         calendarElement.innerHTML = `<div class="alert alert-danger">No se pudo cargar el calendario.</div>`;
  //     }
  // });

  // tableCaliElement.addEventListener('click', async (e) => {
  //     const btn = e.target.closest('button');

  //     if (!btn) return;

  //     if (btn.classList.contains('btn-editar-actividad')){
  //         const originalBtnContent = btn.innerHTML;
  //         showSpinner(btn);
  //         tableCaliElement.querySelectorAll('button').forEach(el => el.disabled = true);
  //         const actividadId = btn.dataset.id;

  //         try {
  //             const response = await fetch(`/api/ficha/actividad/${actividadId}`);
  //             if (!response.ok) throw new Error("Error al obtener la actividad.");
  //             const result = await response.json();
  //             const data = result.data;
  //             const modal = new bootstrap.Modal(document.getElementById("editarActividadModal"));
  //             modal.show();

  //             // Cargar los datos en el modal
  //             formEditarActividad.querySelector('#id_nom').value = data.nom;
  //             formEditarActividad.querySelector('#id_tipo').value = data.tipo;
  //             formEditarActividad.querySelector('#id_descri').value = data.descri;
  //             formEditarActividad.querySelector('#id_horas_auto').value = data.horas_auto;
  //             formEditarActividad.querySelector('#id_horas_dire').value = data.horas_dire;
  //             formEditarActividad.querySelector('#id_fecha_ini_acti').value = data.fecha_ini_acti;
  //             formEditarActividad.querySelector('#id_fecha_fin_acti').value = data.fecha_fin_acti;
  //             formEditarActividad.querySelector('#id_fecha_ini_cali').value = data.fecha_ini_cali;
  //             formEditarActividad.querySelector('#id_fecha_fin_cali').value = data.fecha_fin_cali;
  //             formEditarActividad.querySelector('#id_nove').value = data.nove;

  //             // Inicializar TomSelect y guardar las instancias
  //             const rapsSelectEl = formEditarActividad.querySelector('.tomselect-raps');
  //             const tipoSelectEl = formEditarActividad.querySelector('.tomselect-multiple');

  //             if (rapsSelectEl.tomselect){
  //                 rapsSelectEl.tomselect.destroy();
  //             }
  //             const rapsTomSelect = new TomSelect(rapsSelectEl, {
  //                 plugins: ['remove_button'],
  //                 maxItems: null,
  //                 placeholder: 'Seleccione los RAPs asociados'
  //             });
  //             if (tipoSelectEl.tomselect){
  //                 tipoSelectEl.tomselect.destroy();
  //             }
  //             const tipoTomSelect = new TomSelect(tipoSelectEl, {
  //                 plugins: ['remove_button'],
  //                 maxItems: null,
  //                 persist: false,
  //                 create: false,
  //                 placeholder: 'Seleccione tipos de actividad'
  //             });

  //             // Luego, cargar los valores directamente en las instancias TomSelect
  //             rapsTomSelect.setValue(data.raps); // <- Aquí colocas los valores correctamente
  //             tipoTomSelect.setValue(data.tipo); // <- Si tipo es múltiple, asegúrate de que sea un array

  //             // Guardar el ID para enviarlo al backend después
  //             formEditarActividad.dataset.id = actividadId;
  //             formEditarActividad.setAttribute('action', `/api/ficha/actividad/editar/${actividadId}/`);

  //         } catch (error) {
  //             toastError("No se pudo cargar la actividad.");
  //             console.error(error);
  //         } finally {
  //             hideSpinner(btn, originalBtnContent);
  //             tableCaliElement.querySelectorAll('button').forEach(el => el.disabled = false);
  //         }
  //     } else if (btn.classList.contains('btn-detalle-actividad')){
  //         const actividadId = btn.dataset.id;
  //         const modalElement = document.getElementById('detalleActividadModal');
  //         const contenido = document.getElementById('contenidoDetalleActividad');
  //         const modal = new bootstrap.Modal(modalElement);
  //         const originalBtnContent = btn.innerHTML;
  //         showSpinner(btn);
  //         tableCaliElement.querySelectorAll('button').forEach(el => el.disabled = true);

  //         try {
  //             const response  = await fetch (`/api/ficha/detalle_actividad/${actividadId}`);
  //             if (response.ok) {
  //                 const data = await response.json();

  //                 document.getElementById('act-nombre').textContent = data.nombre;
  //                 document.getElementById('act-descripcion').textContent = data.descripcion;
  //                 document.getElementById('act-tipo').textContent = data.tipo_actividad.join(', ');
  //                 document.getElementById('act-fase').textContent = data.fase;

  //                 document.getElementById('act-horas-directas').textContent = data.horas_directas;
  //                 document.getElementById('act-horas-autonomas').textContent = data.horas_autonomas;

  //                 document.getElementById('cron-inicio').textContent = formatFecha(data.cronograma.fecha_inicio_actividad);
  //                 document.getElementById('cron-fin').textContent = formatFecha(data.cronograma.fecha_fin_actividad);
  //                 document.getElementById('cron-inicio-cali').textContent = formatFecha(data.cronograma.fecha_inicio_calificacion);
  //                 document.getElementById('cron-fin-cali').textContent = formatFecha(data.cronograma.fecha_fin_calificacion);
  //                 document.getElementById('cron-novedades').textContent = data.cronograma.novedades;

  //                 const listaRaps = document.getElementById('act-raps');
  //                 listaRaps.innerHTML = "";
  //                 data.raps.forEach(rap => {
  //                     const li = document.createElement('li');
  //                     li.classList.add('list-group-item');
  //                     li.innerHTML = `<strong>${rap.rap__rap__nom}</strong> (${rap.rap__rap__compe__fase__nom})<br><em>${rap.rap__rap__compe__nom}</em>`;
  //                     listaRaps.appendChild(li);
  //                 });

  //                 modal.show();
  //                 reiniciarTooltips();
  //             } else {
  //                 throw new Error ("Error al cargar los datos.")
  //             }
  //         } catch (error) {
  //             contenido.innerHTML = `<div class="alert alert-danger">No se pudo cargar el detalle de la actividad.</div>`;
  //             console.error(error);
  //         } finally {
  //             hideSpinner(btn, originalBtnContent);
  //             tableCaliElement.querySelectorAll('button').forEach(el => el.disabled = false);
  //         }
  //     } else if (btn.classList.contains('btn-calificar')){
  //         const originalBtnContent = btn.innerHTML;
  //         tableCaliElement.querySelectorAll('button').forEach(el => el.disabled = true);
  //         showSpinner(btn);

  //         const actividadId = btn.dataset.actividadId;
  //         const nombre = btn.dataset.nombre;
  //         const fase = btn.dataset.fase;
  //         const fechaInicio = btn.dataset.fechaInicio;
  //         const fechaFin = btn.dataset.fechaFin;
  //         const fechaInicioCali = btn.dataset.fechaInicioCali;
  //         const fechaFinCali = btn.dataset.fechaFinCali;

  //         document.getElementById('modalNombre').innerText = nombre;
  //         document.getElementById('modalFase').innerText = fase;
  //         document.getElementById('modalFechaInicio').innerText = fechaInicio;
  //         document.getElementById('modalFechaFin').innerText = fechaFin;
  //         document.getElementById('modalFechaInicioCali').innerText = fechaInicioCali;
  //         document.getElementById('modalFechaFinCali').innerText = fechaFinCali;

  //         document.getElementById('inputActividadId').value = actividadId;

  //         await renderTablaCalificaciones(fichaId, actividadId);

  //         const modalCali = new bootstrap.Modal(document.getElementById('modalCalificacion'));
  //         modalCali.show();

  //         hideSpinner(btn, originalBtnContent);
  //         tableCaliElement.querySelectorAll('button').forEach(el => el.disabled = false);
  //     }
  // });

  // //== Enviar formulario editar actividad
  // document.getElementById("formEditarActividad").addEventListener("submit", async function (e) {
  //     e.preventDefault();

  //     const form = this;
  //     const actividadId = form.dataset.id;
  //     const formData = new FormData(form);
  //     const originalBtnContent = btnEditarActividad.innerHTML;

  //     showSpinner(btnEditarActividad)
  //     form.querySelectorAll('button, input, textarea, select').forEach(el => el.disabled = true);

  //     try {
  //         const response = await fetch(`/api/ficha/actividad/editar/${actividadId}/`, {
  //             method: "POST",
  //             headers: { "X-CSRFToken": csrfToken },
  //             body: formData,
  //         });

  //         if (!response.ok) throw new Error("Error al editar la actividad.");

  //         toastSuccess("Actividad actualizada correctamente.");
  //         bootstrap.Modal.getInstance(document.getElementById("editarActividadModal")).hide();
  //         form.reset();
  //         cargarDatosTablaCronograma();
  //         // Actualizar tabla o vista si es necesario
  //     } catch (error) {
  //         toastError("Error al guardar los cambios.");
  //         console.error(error);
  //     } finally {
  //         hideSpinner(btnEditarActividad, originalBtnContent);
  //         form.querySelectorAll('button, input, textarea, select').forEach(el => el.disabled = false);
  //     }
  // });

  // //== renderizar tabla con estudiantes a calificar
  // async function renderTablaCalificaciones(fichaId, actividad_id) {
  //     try {
  //         const response = await fetch(`/api/ficha/obtener_aprendices_calificacion/${fichaId}/${actividad_id}/`);

  //         if (response.ok) {
  //             const data = await response.json();
  //             const tbody = document.getElementById('tablaAprendicesCali');
  //             tbody.innerHTML = '';

  //             data.forEach((estudiante) => {
  //                 const row = document.createElement('tr');
  //                 row.innerHTML = `
  //                     <td>
  //                         ${estudiante.nombre} ${estudiante.apellido}
  //                         <input type="hidden" name="aprendiz_id[]" value="${estudiante.id}">
  //                     </td>
  //                     <td class="text-center">
  //                         <div class="form-check form-switch">
  //                             <input
  //                                 class="form-check-input"
  //                                 type="checkbox"
  //                                 name="nota_${estudiante.id}"
  //                                 value="1"
  //                                 ${estudiante.nota == 1 ? 'checked' : ''}
  //                             >
  //                             <label class="form-check-label">
  //                                 ${estudiante.nota == 1 ? 'Aprobó' : 'No aprobó'}
  //                             </label>
  //                         </div>
  //                     </td>
  //                 `;
  //                 tbody.appendChild(row);
  //             });

  //         } else {
  //             toastError("Error al cargar los aprendices.");
  //         }
  //     } catch (error) {
  //         console.error("Error al cargar los aprendices:", error);
  //     }
  // }

  // //== Boton guardar calificaciones
  // const formularioCalificacion = document.getElementById('formularioCalificacion');
  // const tabla_cali = document.getElementById('tabla_cali');

  // formularioCalificacion.addEventListener('submit', async (e) =>{
  //     e.preventDefault();
  //     const form = e.target;
  //     const submitBtn = document.getElementById('guardarCaliBtn');
  //     const originalBtnContent = submitBtn.innerHTML;
  //     showSpinner(submitBtn);

  //     const formData = new FormData(form);
  //     tabla_cali.querySelectorAll('input').forEach(el => el.disabled = true);

  //     try {
  //         const response = await fetch(`/api/ficha/calificar_actividad/`,{
  //             method: 'POST',
  //             headers: { 'X-CSRFToken': csrfToken },
  //             body: formData
  //         });

  //         if (response.ok){
  //             const data = await response.json();
  //             toastSuccess(data.message)
  //             await renderTablaCalificaciones(fichaId, data.actividad_id);
  //         } else {
  //             const error =  await response.json();
  //             toastError("Error al guardar: "+ error.message);
  //         }

  //     } catch (error) {
  //         console.error("Error al enviar formulario:", error);
  //         toastError("Ocurrió un error al guardar.");
  //     } finally {
  //         hideSpinner(submitBtn, originalBtnContent);
  //         tabla_cali.querySelectorAll('input').forEach(el => el.disabled = false);
  //     }
  // });

  // // Formato de fecha
  // function formatFecha(fechaISO) {
  //     const fecha = new Date(fechaISO);
  //     return fecha.toLocaleDateString();
  // }

  // //== Boton cerrar ficha
  // document.addEventListener('click', async function(e) {
  //     if (e.target && e.target.classList.contains('btn-cerrar-fase')) {
  //         const confirmed = await confirmAction("¿Cerrar la fase?");
  //         const btnFase = e.target;
  //         if (confirmed) {
  //             const originalBtnContent = btnFase.innerHTML;
  //             showSpinner(btnFase);
  //             try {
  //                 const response = await fetch(`/api/ficha/cerrar_fase/${fichaId}/`);
  //                 const data = await response.json();

  //                 if (response.ok) {
  //                     toastSuccess(data.message || "Fase actualizada");
  //                     location.reload();
  //                 } else {
  //                     toastError(data.message || "Error al cerrar la fase.");
  //                 }
  //             } catch (error) {
  //                 console.error("Error de red:", error);
  //                 toastError("Ocurrió un error al cerrar la fase.");
  //             } finally {
  //                 hideSpinner(btnFase, originalBtnContent);
  //             }
  //         }
  //     } else if (e.target && e.target.classList.contains('btn-devolver-fase')){
  //         const confirmed = await confirmAction("¿devolver la fase?");
  //         const btnDevolverFase = e.target;
  //         if(confirmed){
  //             const originalBtnContent = btnDevolverFase.innerHTML;
  //             showSpinner(btnDevolverFase);
  //             try {
  //                 const response = await fetch(`/api/ficha/devolver_fase/${fichaId}/`, {
  //                     method: "POST",
  //                     headers: {
  //                         "X-CSRFToken": csrfToken,
  //                     }
  //                 });

  //                 const data = await response.json();

  //                 if (data.success) {
  //                     toastSuccess(data.message);
  //                     this.location.reload();
  //                 } else {
  //                     toastError(data.message || "Error al devolver la fase.");
  //                 }
  //             } catch (error) {
  //                 toastError("Error al conectar con el servidor.");
  //                 console.error(error);
  //             } finally {
  //                 hideSpinner(btnDevolverFase, originalBtnContent);
  //             }
  //         }
  //     }
  // });

  // *******************************************************************
  // *                                                                 *
  // *        ¡ADVERTENCIA! ZONA DE INASISTENCIA                       *
  // *                                                                 *
  // *******************************************************************

  // const modalAsistenciaElement = document.getElementById('detalleEncuentroModal');
  // const modalAsistencia = new bootstrap.Modal(modalAsistenciaElement);
  // const tablaAsistencia = document.getElementById('encuentros_ficha');
  // const formCrearEncuentro = document.getElementById('formCrearEncuentro');
  // const formEditarEncuentro = document.getElementById('formEditarEncuentro');

  // cargarDatosTablaEncuentros();

  // ======= Inicialización de DataTables =======
  // const tableEncuentros = new DataTable(tablaAsistencia, {
  //     language: {
  //         url: 'https://cdn.datatables.net/plug-ins/2.1.8/i18n/es-ES.json',
  //         drawCallback: () => {
  //         document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(el => {
  //             new bootstrap.Tooltip(el);
  //         });
  //     }
  //     }
  // });

  //== Enviar formulario crear encuentro
  // formCrearEncuentro.addEventListener('submit', async (e) => {
  //     e.preventDefault();

  //     const form = e.target;
  //     const submitBtn = document.getElementById('btnCrearEncuentro');
  //     const originalBtnContent = submitBtn.innerHTML;
  //     const errorDiv = document.getElementById('errorCrearEncuentro');

  //     const formData = new FormData(form);
  //     for (let pair of formData.entries()) {
  //         console.log(`${pair[0]}: ${pair[1]}`);
  //     }
  //     showSpinner(submitBtn);
  //     form.querySelectorAll('select, button, input').forEach(el => el.disabled = true);

  //     try {
  //         const response = await fetch(`/api/ficha/crear_encuentro/${fichaId}/`, {
  //             method: 'POST',
  //             headers: { 'X-CSRFToken': csrfToken, 'X-Requested-With': 'XMLHttpRequest' },
  //             body: formData
  //         });

  //         if (response.ok ){
  //             const data = await response.json();
  //             toastSuccess(data.message);
  //             form.reset()
  //             bootstrap.Modal.getInstance(document.getElementById('crearEncuentroModal')).hide();
  //             cargarDatosTablaEncuentros();
  //         } else {
  //             const data = await response.json();
  //             toastError("Error al guardar: "+ data.message)
  //             errorDiv.innerHTML = data.errors || "Error desconocido al crear la actividad.";
  //         }
  //     } catch (error) {
  //         toastError("Error al guardar el formulario.");
  //         errorDiv.innerHTML = error || "Error desconocido al crear la actividad.";
  //     } finally {
  //         hideSpinner(submitBtn, originalBtnContent);
  //         form.querySelectorAll('select, button, input').forEach(el => el.disabled = false);
  //     }
  // });

  //== Listeners tabla encuentros
  // tablaAsistencia.addEventListener('click', async (e) => {
  //     const btn = e.target.closest('button');

  //     if (!btn) return;

  //== Boton ver detalle encuentro
  // if  (btn.classList.contains('btn-detalle-encuentro')){
  //     const encuentroId = btn.getAttribute('data-id');
  //     const originalBtnContent = btn.innerHTML;
  //     showSpinner(btn);
  //     tablaAsistencia.querySelectorAll('button').forEach(el => el.disabled = true);
  //     try {
  //         const response = await fetch(`/api/ficha/encuentro_detalle/${encuentroId}`);
  //         if (response.ok){
  //             const data = await response.json();
  //             cargarDetalleEncuentro(data);
  //             modalAsistencia.show();
  //         } else {
  //             throw new Error("Error al cargar la data");

  //         }
  //     } catch (error) {
  //         console.error("Error de red:", error);
  //         toastError("Ocurrió un error al cargar la data.");
  //     } finally {
  //         hideSpinner(btn, originalBtnContent);
  //         tablaAsistencia.querySelectorAll('button').forEach(el => el.disabled = false);
  //     }

  // };

  //== Boton editar encuentro
  //     if (btn.classList.contains('btnEditarEncuentro')){
  //         const encuentroId = btn.getAttribute('data-id');
  //         const originalBtnContent = btn.innerHTML;
  //         showSpinner(btn);

  //         const modalEl = document.getElementById('editarEncuentroModal');
  //         const modalInstance = new bootstrap.Modal(modalEl);
  //         modalInstance.show();

  //         await cargarDatosEditarEncuentro(encuentroId);
  //         hideSpinner(btn, originalBtnContent);

  //     };

  // });

  //== Poblar formulario para editar encuentro
  // async function cargarDatosEditarEncuentro(encuentroId) {
  //     formEditarEncuentro.querySelectorAll('input, select, button').forEach(el => el.disabled=true);

  //     try {
  //         const response = await fetch(`/api/ficha/encuentro/${encuentroId}/`);
  //         const data = await response.json();

  //         formEditarEncuentro.querySelector('input[name="tema"]').value = data.tema;
  //         formEditarEncuentro.querySelector('input[name="lugar"]').value = data.lugar;
  //         formEditarEncuentro.querySelector('input[name="fecha"]').value = data.fecha;

  //         const checkboxes = formEditarEncuentro.querySelectorAll('input[type="checkbox"][name="aprendices"]');
  //         checkboxes.forEach(cb => {
  //             cb.checked = data.ausentes.includes(parseInt(cb.value));
  //         });

  //         formEditarEncuentro.setAttribute('action', `/api/ficha/encuentro/editar/${encuentroId}/`);
  //     } catch (error) {
  //         toastError(error)
  //     } finally {
  //         formEditarEncuentro.querySelectorAll('input, select, button').forEach(el => el.disabled=false);
  //     }
  // };

  // formEditarEncuentro.addEventListener('submit', async e => {
  //     e.preventDefault();

  //     const formData = new FormData(formEditarEncuentro);
  //     const btn = document.getElementById('btnEditarEncuentro');
  //     const originalBtnContent = btn.innerHTML;
  //     showSpinner(btn);

  //     formEditarEncuentro.querySelectorAll('button, select, input').forEach(el => el.disabled=true);
  //     try {
  //         const response = await fetch(formEditarEncuentro.action, {
  //             method: 'POST',
  //             headers: {'X_CSRFToken': csrfToken, 'X-Requested-With': 'XMLHttpRequest'},
  //             body: formData
  //         });
  //         const data = await response.json();
  //         if (!response.ok){
  //             toastError(data.message);
  //             return
  //         }

  //         toastSuccess(data.message);
  //         const modalEl = document.getElementById('editarEncuentroModal');
  //         const modalInstance = bootstrap.Modal.getInstance(modalEl);
  //         modalInstance.hide();
  //         cargarDatosTablaEncuentros();
  //     } catch (error) {
  //         toastError(error)
  //     } finally {
  //         hideSpinner(btn, originalBtnContent);
  //         formEditarEncuentro.querySelectorAll('button, select, input').forEach(el => el.disabled=false);
  //     }

  // });

  //==Cargar detalle encuentro
  // function cargarDetalleEncuentro(encuentroData){
  //     reiniciarTooltips();
  //     document.getElementById('modal-lugar'). textContent = encuentroData.data.lugar;
  //     document.getElementById('modal-fecha'). textContent = encuentroData.data.fecha;
  //     document.getElementById('modal-participantes'). textContent = encuentroData.data.participantes;

  //     //Asistieron:
  //     const listaAsistieron = document.getElementById('modal-aprendices-asistieron');
  //     listaAsistieron.innerHTML = '';

  //     encuentroData.data.aprendicesAsistieron.forEach(apre => {
  //         const li = document.createElement('li');
  //         li.textContent = apre.nombre;
  //         listaAsistieron.appendChild(li);
  //     });

  //     //Faltaron
  //     const listaFaltaron = document.getElementById('modal-aprendices-faltaron');
  //     listaFaltaron.innerHTML = '';

  //     encuentroData.data.aprendicesFaltaron.forEach(apre => {
  //         const li = document.createElement('li');
  //         li.textContent = apre.nombre;
  //         listaFaltaron.appendChild(li);
  //     });
  // }

  //== LLamar API encuentros
  // async function cargarDatosTablaEncuentros(){
  //     fadeIn(loadingDiv);
  //     try {
  //         const response = await fetch(`/api/ficha/encuentros/${fichaId}/`);
  //         const data = await response.json();
  //         actualizarTablaEncuentros(data);
  //     } catch (error){
  //         toastError("Error al cargar las actividades: ", error);
  //     } finally {
  //         fadeOut(loadingDiv);
  //     }
  // }

  //== Poblar tabla encuentros
  // function actualizarTablaEncuentros(data){
  //     tableEncuentros.clear();

  //     data.forEach(item => {
  //         const fecha = new Date(item.fecha);
  //         const fechaFormateada = fecha.toLocaleDateString('es-CO', {
  //             year: 'numeric',
  //             month: '2-digit',
  //             day: '2-digit'
  //         });
  //         let botones =`
  //             <button class="btn btn-outline-primary btn-sm btn-detalle-encuentro"
  //                     data-id="${item.id}"
  //                     data-bs-toggle="tooltip"
  //                     data-bs-placement="top"
  //                     title="Detalle">
  //                 <i class="bi bi-plus-lg"></i>
  //             </button>
  //             <button class="btn btn-outline-warning btn-sm btnEditarEncuentro"
  //                     data-id="${item.id}"
  //                     data-bs-toggle="tooltip"
  //                     data-bs-placement="top"
  //                     title="Editar Encuentro">
  //                 <i class="bi bi-pencil-square"></i>
  //             </button>
  //         `;
  //         tableEncuentros.row.add([
  //             fechaFormateada,
  //             item.tema,
  //             item.lugar,
  //             botones
  //         ]);
  //     });

  //     tableEncuentros.draw();

  //     document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(el => {
  //         const tooltipInstance = bootstrap.Tooltip.getInstance(el);
  //         if (tooltipInstance) {
  //             tooltipInstance.dispose();
  //         }
  //     });

  //     document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(el => {
  //         new bootstrap.Tooltip(el);
  //     });

  // }

  // *******************************************************************
  // *                                                                 *
  // *        ¡ADVERTENCIA! ZONA DE REPORTES                           *
  // *                                                                 *
  // *******************************************************************
});
