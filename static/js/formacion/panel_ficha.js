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

  const userRole = document.body.dataset.userRole;

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

  verTree();

  async function verTree() {
    const container = document.getElementById("folderTree");
    if (!container) return;
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

      container.appendChild(renderTree(data.nodos, data.can_edit));

      // Agregar listeners después de renderizar el árbol
      addEventListeners(data.can_edit);
      renderAlertas();
      cargarHistorial("fichaG", fichaId);
      cargarHistorial("ficha", fichaId);
    } catch (error) {
      console.error("Error al cargar la estructura del árbol:", error);
      container.innerHTML = "<p>Error al cargar el árbol</p>";
    }
  }

  async function cargarHistorial(contexto, id) {
    let containerId =
      contexto === "ficha"
        ? "historialFicha"
        : contexto === "aprendiz"
        ? "historialAprendiz"
        : "historialGeneralFicha";
    const container = document.getElementById(containerId);
    const historialTitle = document.getElementById("historial-tab");

    container.innerHTML = "";

    if (contexto === "fichaG") {
      historialTitle.textContent = "Historial";

      const spinner = document.createElement("span");
      spinner.className = "spinner-border spinner-border-sm ms-2";
      spinner.role = "status";
      spinner.style.width = "1rem";
      spinner.style.height = "1rem";
      spinner.innerHTML = `<span class="visually-hidden">Loading...</span>`;

      historialTitle.appendChild(spinner);

      // guardamos referencia para remover después
      historialTitle.dataset.spinnerId = "spinner-historial";
      spinner.id = historialTitle.dataset.spinnerId;
    }

    // Mensaje de carga
    const loadingMessage = document.createElement("li");
    loadingMessage.classList.add("list-group-item", "text-center");
    loadingMessage.innerHTML = `
        <div class="d-flex justify-content-center align-items-center">
            <div class="spinner-border text-dark me-2" role="status">
                <span class="visually-hidden">Cargando...</span>
            </div>
        </div>
    `;
    container.appendChild(loadingMessage);

    try {
      const response = await fetch(
        `/api/formacion/fichas/historial/?contexto=${encodeURIComponent(
          contexto
        )}&id=${encodeURIComponent(id)}`
      );
      if (!response.ok) throw new Error("Error en la respuesta del servidor");
      const data = await response.json();

      container.innerHTML = "";

      if (data.length === 0) {
        container.innerHTML =
          '<li class="list-group-item">No hay historial disponible</li>';
        return;
      }

      data.forEach((log) => {
        const li = document.createElement("li");
        li.classList.add("list-group-item");
        li.innerHTML = `
                <strong>${log.usuario}</strong> 
                <span class="text-muted">[${log.fecha}]</span>: 
                ${log.detalle} <em>(${log.accion})</em>
            `;
        container.appendChild(li);
      });
    } catch (error) {
      console.error("Error al cargar el historial:", error);
      container.innerHTML =
        '<li class="list-group-item text-danger">Error al cargar el historial</li>';
    } finally {
      if (contexto === "fichaG" && historialTitle) {
        const spinner = document.getElementById("spinner-historial");
        if (spinner) spinner.remove();
      }
    }
  }

  function renderTree(nodes, can_edit) {
    if (!nodes || nodes.length === 0) return null;

    const ul = document.createElement("ul");
    ul.classList.add("folder-list");

    nodes.forEach((node) => {
      if (
        userRole === "instructor" &&
        node.name === "LINK DE PORTAFOLIO APRENDICES 2024"
      )
        return null;

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

        if (node.name === "LINK DE PORTAFOLIO APRENDICES 2024") {
          span.dataset.portafolioLink = "true";
        }

        // Contenedor de subelementos (solo para carpetas)
        const subFolderContainer = document.createElement("ul");
        subFolderContainer.classList.add("folder-children");
        subFolderContainer.id = `folder-${node.id}`;

        if (
          can_edit &&
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
          subFolderContainer.appendChild(renderTree(node.children, can_edit));
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

        link.href = "/media/" + path + encodeURIComponent(filename);
        link.target = "_blank";
        link.appendChild(icon);
        link.appendChild(span);
        li.appendChild(link);

        if (can_edit && userRole != "instructor") {
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
  function addEventListeners(can_edit) {
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
        if (confirmed) deleteFile(docId, folderId, can_edit);
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

    if (can_edit) {
      // Dragover delegado
      folderTree.addEventListener("dragover", (e) => {
        const folder = e.target.closest(
          "[data-folder-id][data-droppable='true']"
        );
        if (folder) {
          e.preventDefault();
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
        await handleDropOnFolder(folder, e, "ficha", can_edit);
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
      if (uploadButton)
        uploadButton.addEventListener("click", () =>
          uploadFile("ficha", can_edit)
        );
    }
    treeListenersInitialized = true;
  }

  async function handleDropOnFolder(folderElement, e, contexto, can_edit) {
    const folderId = folderElement.dataset.folderId;
    const type = e.dataTransfer.getData("type");

    // --- 1) Mover documento existente ---
    if (type === "document") {
      const documentId = e.dataTransfer.getData("documentId");
      const sourceFolderId = e.dataTransfer.getData("sourceFolderId");
      if (!documentId) return;
      if (String(folderId) === String(sourceFolderId)) return;

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
            contexto: contexto,
          }),
        });

        const data = await resp.json();
        if (!resp.ok) {
          toastError(data.message || "Error al mover el documento.");
          return;
        }

        toastSuccess(data.message || "Documento movido con éxito.");
        // Recargar carpeta origen y destino
        await actualizarCarpeta(sourceFolderId, contexto, can_edit);
        await actualizarCarpeta(folderId, contexto, can_edit);
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
      "pptx",
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
      "txt",
      "gif",
      "svg",
      "avi",
      "wav",
      "flac",
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
        ? 1000 * 1024 * 1024
        : 50 * 1024 * 1024;

      if (file.size > maxSize) {
        toastError(
          `El archivo "${file.name}" supera el tamaño máximo permitido (${
            maxSize === 1000 * 1024 * 1024 ? "1GB" : "50MB"
          }).`
        );
        continue;
      }

      validFiles.push(file);
    }

    if (validFiles.length === 0) return;

    const subFolderContainer = document.getElementById(
      contexto === "ficha"
        ? `folder-${folderId}`
        : `portafolio-folder-${folderId}`
    );

    if (!subFolderContainer) {
      console.error("No se encontró el contenedor de la carpeta");
      return;
    }

    try {
      const uploadTasks = validFiles.map((file) => {
        const li = document.createElement("li");
        li.className = "upload-item";
        li.innerHTML = `
        <div class="upload-progress">
          <i class="bi bi-file-earmark-arrow-up"></i>
          <span class="file-name">${file.name}</span>
          <div class="progress mt-1">
            <div class="progress-bar" role="progressbar" style="width: 0%">0%</div>
          </div>
        </div>
        `;
        subFolderContainer.appendChild(li);

        const progressBar = li.querySelector(".progress-bar");

        return new Promise((resolve) => {
          const formData = new FormData();
          formData.append("documento", file);
          formData.append("folder_id", folderId);
          formData.append("contexto", contexto);

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
      await actualizarCarpeta(folderId, contexto, can_edit);
    } catch (err) {
      console.error("Error en la subida por drag & drop:", err);
      toastError("Error al subir los documentos: " + err.message);
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

  async function uploadFile(contexto, can_edit) {
    const config = {
      ficha: {
        uploadButton: "uploadButton",
        fileInput: "fileInput",
        modalId: "uploadModal",
      },
      aprendiz: {
        uploadButton: "uploadButtonAprendiz",
        fileInput: "fileInputAprendiz",
        modalId: "uploadModalAprendiz",
      },
    };

    const { uploadButton, fileInput, modalId } = config[contexto];

    const folderId = document.getElementById(uploadButton).dataset.folderId;
    const fileInputElement = document.getElementById(fileInput);
    const uploadModal = document.getElementById(modalId);

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
      "pptx",
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
      "txt",
      "gif",
      "svg",
      "avi",
      "wav",
      "flac",
    ];

    const modal = bootstrap.Modal.getInstance(uploadModal);
    if (modal) modal.hide();

    const subFolderContainer = document.getElementById(
      contexto === "ficha"
        ? `folder-${folderId}`
        : `portafolio-folder-${folderId}`
    );

    if (!subFolderContainer) {
      console.error("No se encontró el contenedor de la carpeta");
      return;
    }

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
          ? 1000 * 1024 * 1024
          : 50 * 1024 * 1024;

        if (file.size > maxSize) {
          toastError(
            `El archivo "${file.name}" supera el tamaño máximo permitido (${
              maxSize === 1000 * 1024 * 1024 ? "1GB" : "50MB"
            }).`
          );
          continue;
        }

        const li = document.createElement("li");
        li.className = "upload-item";
        li.innerHTML = `
        <div class="upload-progress">
          <i class="bi bi-file-earmark-arrow-up"></i>
          <span class="file-name">${file.name}</span>
          <div class="progress mt-1">
            <div class="progress-bar" role="progressbar" style="width: 0%">0%</div>
          </div>
        </div>
        `;
        subFolderContainer.appendChild(li);

        const progressBar = li.querySelector(".progress-bar");

        const uploadPromise = new Promise((resolve) => {
          const formData = new FormData();
          formData.append("file", file);
          formData.append("folder_id", folderId);
          formData.append("contexto", contexto);

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
      await actualizarCarpeta(folderId, contexto, can_edit);
      fileInputElement.value = "";
    } catch (error) {
      console.error("Error al subir el archivo:", error);
      toastError("Ocurrió un error inesperado.");
    }
  }

  async function deleteFile(fileId, folderId, can_edit) {
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
          await actualizarCarpeta(folderId, "ficha", can_edit);
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

  async function actualizarCarpeta(folderId, contexto, can_edit) {
    let aprendizId = null;

    if (contexto === "aprendiz")
      aprendizId = document.getElementById("portafolioAprendizModal").dataset
        .aprendizId;

    try {
      const config = {
        ficha: {
          url: `/api/tree/obtener_hijos_carpeta/${folderId}`,
          containerId: `folder-${folderId}`,
          renderFn: renderTree,
          renderHistorial: () => cargarHistorial("ficha", fichaId),
        },
        aprendiz: {
          url: `/api/tree/obtener_hijos_carpeta_aprendiz/${folderId}`,
          containerId: `portafolio-folder-${folderId}`,
          renderFn: renderPortafolioTree,
          renderHistorial: () => cargarHistorial("aprendiz", aprendizId),
        },
      };

      if (!config[contexto]) {
        console.error(`Contexto no válido: ${contexto}`);
        return;
      }

      const { url, containerId, renderFn, renderHistorial } = config[contexto];

      const response = await fetch(url);
      const data = await response.json();

      const subFolderContainer = document.getElementById(containerId);
      if (!subFolderContainer) {
        console.error(`No se encontró el contenedor ${containerId}`);
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
        const hijos = renderFn(data, can_edit);
        if (hijos) {
          subFolderContainer.appendChild(hijos);
        }
      }
      renderHistorial();
      if (contexto === "ficha") {
        renderAlertas();
      }
    } catch (error) {
      console.error("Error al actualizar la carpeta:", error);
    }
  }

  function findEmptyFolders(nodes, path = []) {
    let emptyNodes = [];

    nodes.forEach((n) => {
      if (n.tipo === "carpeta") {
        const newPath = [...path, n.name];

        if (!n.children || n.children.length === 0) {
          // Carpeta sin nada → final y vacía
          emptyNodes.push({ id: n.id, path: newPath });
        } else {
          // Revisar si tiene subcarpetas
          const hasChildFolders = n.children.some((c) => c.tipo === "carpeta");

          if (hasChildFolders) {
            // Recorremos hijos
            const childEmpty = findEmptyFolders(n.children, newPath);
            if (childEmpty.length > 0) {
              emptyNodes = emptyNodes.concat(childEmpty);
            }
          } else {
            // No tiene subcarpetas, pero sí podría tener documentos
            const hasDocuments = n.children.some((c) => c.tipo === "documento");
            if (!hasDocuments) {
              // Es carpeta final y está vacía
              emptyNodes.push({ id: n.id, path: newPath });
            }
          }
        }
      }
    });

    return emptyNodes;
  }

  let alertasEnProceso = false;
  async function renderAlertas() {
    if (alertasEnProceso) return;

    alertasEnProceso = true;

    const alertasList = document.getElementById("alertasList");
    const alertasTab = document.getElementById("alertas-tab");

    // limpiar contenido previo
    alertasList.innerHTML = "";
    alertasTab.querySelectorAll(".badge").forEach((b) => b.remove());

    // crear spinner
    const spinner = document.createElement("span");
    spinner.className = "spinner-border spinner-border-sm ms-2";
    spinner.role = "status";
    spinner.style.width = "1rem";
    spinner.style.height = "1rem";
    spinner.innerHTML = `<span class="visually-hidden">Loading...</span>`;
    spinner.id = "spinner-alertas"; // id único

    alertasTab.appendChild(spinner);

    try {
      const response = await fetch(`/api/tree/obtener_carpetas/${fichaId}/`);
      const data = await response.json();

      // calcular carpetas vacías
      const emptyNodes = findEmptyFolders(data.nodos);

      // quitar spinner al terminar
      const removeSpinner = () => {
        const sp = document.getElementById("spinner-alertas");
        if (sp) sp.remove();
      };

      if (emptyNodes.length > 0) {
        emptyNodes.forEach((n) => {
          const li = document.createElement("li");
          li.classList.add("alerta-item", "alerta-warning");
          li.innerHTML = `
      <i class="bi bi-exclamation-triangle-fill me-2"></i>
      La carpeta <strong>"${n.path.join(" > ")}"</strong> no tiene documentación
    `;
          alertasList.appendChild(li);
        });

        removeSpinner();

        const badge = document.createElement("span");
        badge.classList.add("badge", "bg-danger", "ms-2");
        badge.textContent = emptyNodes.length;
        alertasTab.appendChild(badge);
      } else {
        removeSpinner();

        const li = document.createElement("li");
        li.classList.add("alerta-item", "alerta-success");
        li.innerHTML = `
    <i class="bi bi-check-circle-fill me-2"></i>
    Todas las carpetas tienen documentación
  `;
        alertasList.appendChild(li);
      }
    } finally {
      alertasEnProceso = false;
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

  const tableAprendicesElement = document.getElementById(
    "tabla_aprendices_ficha"
  );

  // ======= Inicialización de DataTables =======
  const tableAprendices = new DataTable(tableAprendicesElement, {
    serverSide: false,
    processing: true,
    ajax: {
      url: `/api/usuarios/aprendices/por_ficha/?ficha_id=${fichaId}`,
      type: "GET",
      dataSrc: "",
    },
    columns: [
      { data: "nombre" },
      { data: "apellido" },
      { data: "dni" },
      {
        data: "estado",
        render: function (data, type, row) {
          let badge = "";
          switch (data.toLowerCase()) {
            case "activo":
              badge = '<span class="badge bg-success">Activo</span>';
              break;
            case "desertado":
              badge = '<span class="badge bg-danger">Desertado</span>';
              break;
            case "en_formacion":
              badge = '<span class="badge bg-primary">En formación</span>';
              break;
            case "prematricula":
              badge = '<span class="badge bg-primary">Prematrícula</span>';
              break;
            case "aplazado":
              badge =
                '<span class="badge bg-warning text-dark">Aplazado</span>';
              break;
            default:
              badge = `<span class="badge bg-secondary">${data}</span>`;
          }
          return badge;
        },
      },
      {
        data: null,
        orderable: false,
        render: function (data, type, row) {
          return `
            <div class="btn-group btn-group-sm mb-1" role="group">
              <button class="btn btn-outline-secondary ver-portafolio" data-id="${
                row.id
              }" data-nombre="${row.nombre} ${
            row.apellido
          }" title="Subir portafolio">
                <i class="bi bi-folder"></i>
              </button>
              <button class="btn btn-outline-info perfil-btn" data-id="${
                row.id
              }" title="Ver Perfil">
                <i class="bi bi-plus-lg"></i>
              </button>
              ${
                row.can_edit === true
                  ? row.estado.toLowerCase() !== "desertado"
                    ? `
                <button class="btn btn-outline-danger desertar-aprendiz" data-id="${row.id}" title="Marcar como desertado">
                  <i class="bi bi-person-dash"></i>
                </button>
                <button class="btn btn-outline-dark desasociar-aprendiz" data-id="${row.id}" title="Eliminar de la ficha">
                  <i class="bi bi-x-circle"></i>
                </button>
                <button class="btn btn-outline-primary editar-aprendiz" data-id="${row.id}" title="Editar">
                  <i class="bi bi-pencil"></i>
                </button>`
                    : `
                <button class="btn btn-outline-success activar-aprendiz" data-id="${row.id}" title="Activar">
                  <i class="bi bi-person-check"></i>
                </button>`
                  : ``
              }
            </div>
          `;
        },
      },
    ],
    language: {
      url: "https://cdn.datatables.net/plug-ins/2.1.8/i18n/es-ES.json",
      emptyTable: "Sin aprendices registrados",
    },
  });

  const validarAprendizBtn = document.getElementById("validateBtn");

  if (validarAprendizBtn) {
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

            const modalCrearApre =
              document.getElementById("modalCrearAprendiz");
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
  }
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
      const modalEL = document.getElementById("modalAgregarAprendiz");
      const modal = bootstrap.Modal.getInstance(modalEL);
      modal.hide();
      cargarHistorial("fichaG", fichaId);
      tableAprendices.ajax.reload(null, false);
    } catch (error) {
      toastError(error);
    }
  }

  const formCrearApre = document.getElementById("formCrearApre");

  if (formCrearApre) {
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
        const response = await fetch(
          `/api/usuarios/aprendices/crear_un_apre/`,
          {
            method: "POST",
            body: formData,
            headers: {
              "X-CSRFToken": csrfToken,
            },
          }
        );

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
        const modalCrearApre = document.getElementById("modalCrearAprendiz");
        const modalCrearApreI = bootstrap.Modal.getInstance(modalCrearApre);
        modalCrearApreI.hide();
        cargarHistorial("fichaG", fichaId);
        tableAprendices.ajax.reload(null, false);
      } catch (error) {
        console.error(error);
        toastError("Error inesperado");
      } finally {
        setFormDisabled(formCrearApre, false);
        hideSpinner(btn, originalBtnContent);
      }
    });
  }

  if (tableAprendicesElement) {
    tableAprendicesElement.addEventListener("click", async (e) => {
      //== Boton ver portafolio aprendiz
      const target = e.target.closest(".ver-portafolio");
      if (target) {
        const aprendizId = target.getAttribute("data-id");
        const aprendizNombre = target.getAttribute("data-nombre");

        document.getElementById(
          "portafolioAprendizModalLabel"
        ).textContent = `Portafolio de ${aprendizNombre}`;

        document.getElementById("folderTreeAprendiz").innerHTML = "";

        cargarPortafolio(aprendizId);

        const modalEl = document.getElementById("portafolioAprendizModal");
        modalEl.dataset.aprendizId = aprendizId;
        modalEl.removeAttribute("aria-hidden");
        new bootstrap.Modal(modalEl).show();

        modalEl.addEventListener("hidden.bs.modal", function () {
          document.getElementById("folderTreeAprendiz").innerHTML = "";
          modalEl.setAttribute("aria-hidden", "true");

          if (
            document.activeElement &&
            modalEl.contains(document.activeElement)
          ) {
            document.activeElement.blur();
          }

          const btnAbrir = document.querySelector(".ver-portafolio");
          if (btnAbrir) btnAbrir.focus();
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

      const target5 = e.target.closest(".activar-aprendiz");
      if (target5) {
        const confirm = await confirmAction({
          message:
            "¿Esta seguro que desea activar al aprendiz?, quedara activo en la actual ficha",
          title: "Activar aprendiz",
          icon: "warning",
        });
        if (!confirm) return;
        const originalBtnContent = target5.innerHTML;
        showSpinner(target5);
        const aprendizId = target5.getAttribute("data-id");

        try {
          await activarAprendiz(aprendizId);
        } finally {
          hideSpinner(target5, originalBtnContent);
        }
      }
    });
  }
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

  if (formEditarAprendiz) {
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
          tele: sanitize(
            formEditarAprendiz.querySelector('[name="tele"]').value
          ),
          dire: sanitize(
            formEditarAprendiz.querySelector('[name="dire"]').value
          ),
          gene: sanitize(
            formEditarAprendiz.querySelector('[name="gene"]').value
          ),
          mail: sanitize(
            formEditarAprendiz.querySelector('[name="mail"]').value
          ),
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
        const modalEl = document.getElementById("editAprendizModal");
        const modalInstance = bootstrap.Modal.getInstance(modalEl);
        modalInstance.hide();
        cargarHistorial("fichaG", fichaId);
        tableAprendices.ajax.reload(null, false);
      } catch (e) {
        toastError(e);
      } finally {
        hideSpinner(btn, originalBtnContent);
        setFormDisabled(formEditarAprendiz, false);
      }
    });
  }

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
      cargarHistorial("fichaG", fichaId);
      tableAprendices.ajax.reload(null, false);
    } catch (error) {
      toastError(error);
    }
  }

  async function activarAprendiz(aprendizId) {
    try {
      const response = await fetch(`/api/usuarios/aprendices/${aprendizId}/`, {
        method: "PATCH",
        headers: {
          "X-CSRFToken": csrfToken,
          "X-Requested-With": "XMLHttpRequest",
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ esta: "activo" }),
      });

      const data = await response.json();
      if (validarErrorDRF(response, data)) return;
      toastSuccess(data.message);
      cargarHistorial("fichaG", fichaId);
      tableAprendices.ajax.reload(null, false);
    } catch (e) {
      toastError(e);
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
      tableAprendices.ajax.reload(null, false);
      cargarHistorial("fichaG", fichaId);
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

      const portafolioTree = renderPortafolioTree(data.nodos, data.can_edit);
      if (portafolioTree) {
        portafolioContainer.appendChild(portafolioTree);
      }

      agregarEventListenersPortafolio(data.can_edit);
      cargarHistorial("aprendiz", aprendizId);
    } catch (error) {
      console.error("Error cargando los nodos:", error);
      document.getElementById("folderTreeAprendiz").innerHTML =
        '<tr><td colspan="4" class="text-center text-danger">Error al cargar nodos.</td></tr>';
    } finally {
      fadeOut(loadingDiv);
    }
  }

  const carpetasRestringidasCohorte1 = [
    "4. EVIDENCIAS DE APRENDIZAJE > 1. ANÁLISIS",
    "4. EVIDENCIAS DE APRENDIZAJE > 2. PLANEACIÓN",
  ];

  const fichasCohorte1 = [
    3018230, 3063704, 3032252, 3032208, 3034030, 3068220, 3032278, 3032301,
    3032333, 3068233, 3032236, 3069103, 3024914, 3024807, 3036816, 3033216,
    3032568, 3033179, 3036817, 2924929, 3038052, 3034256, 3002707, 3001897,
    3005640, 3005636, 3002528, 3068214, 3068217, 3068219, 3006543, 3006555,
    3005469, 3005470, 3006151, 3005244, 3040711, 2932504, 3011155, 3030187,
    3047197, 3047182, 3040773, 3009268, 3011154, 3010899, 3010861, 3010077,
    3010097, 3011151, 3011164, 3010930, 3011181, 3010797, 3011097, 3011108,
    3047145, 3010895, 3010917, 3011175, 3030190, 3030191, 3032139, 3019773,
    3019785, 3019772, 2941076, 3009855, 3081786, 3081813, 3029011, 3029177,
    3029014, 2926869, 3024473, 3024475, 3024478, 3024481, 3024483, 3024495,
    2951235, 2947592, 3024703, 3035071, 3028995, 2926879, 3035089, 2941828,
    2941832, 2951667, 2951756, 2926873, 3029163, 3029197, 3029053, 3029193,
    3029078, 3093337, 3093340, 3093332, 3093348, 3093345, 2926840, 3024092,
    3028722, 3028737, 3029109, 3027789, 2974200, 2974186, 3007865, 3007856,
    3007401, 3007404, 3007657, 3007399, 3007654, 3007870, 3007833, 3007858,
    3007859, 3007857, 3009669, 3009668, 3007866, 3007871, 3007872, 3007834,
    3007855, 3135466, 3135472, 3007407, 3007409, 3007411, 3007424, 3007426,
    3007428, 3007431, 3007432, 3007433, 2991742, 3023792, 3023725, 2904012,
    2904013, 3025253, 3025290, 3025286, 2980763, 2904205, 2904206, 2904322,
    2904321, 3008217, 3027059, 3006969, 3019992, 3027087, 2982974, 2982983,
    3039214, 3039190, 3039216, 3039409, 3039411, 3027390, 3027454, 3027532,
    3011937, 3009594, 3009597, 3005046, 3005108, 3005125, 3005140, 3007040,
    3004827, 3011602, 3009539, 3009546, 3009553, 2940967, 2941168, 2941362,
    3029469, 2952000, 2951983, 2951997, 2943165, 2941548, 3007083, 3012499,
    3023471, 2951995, 2982525, 2982916, 2982903, 3025619, 3067743, 3025628,
    3001467, 3016022, 3016024, 2982523, 2982509, 2981692, 2982491, 2982521,
    2982634, 2982508, 2981760, 2981761, 2992833, 2992834, 2992855, 3010341,
    3010320, 2988377, 3002732, 3027389, 2992673, 3010309, 2982513, 3010316,
    3011544, 2982514, 3002220, 3002221, 3004533, 3004538, 3010342, 3010318,
    2997341, 2997342, 2992640, 2992326, 2982630, 3002295, 3002296, 3010292,
    3002289, 3027428, 3002293, 3018748, 3018751, 3000575, 3000579, 3000595,
    3001102, 3018745, 3001100, 3001101, 2973260, 2973265, 2973269, 2973271,
    3009169, 3018229, 3018228, 2981440, 2981461, 2981479, 2931137, 3022332,
    3022331, 3022336, 3022300, 3022318, 3022299, 3022283, 3022301, 3022315,
    3022294, 3022297, 3022316, 2993023, 3033772, 2996704, 3001082, 3001103,
    3008958, 3008915, 3010686, 3015576, 3009211, 3015578, 3031985, 3069177,
    3037316, 3008971, 3009381, 3036249, 3036252, 3009240, 3009326, 3009072,
    3009081, 3029523, 3029525, 3029526, 3069546, 2979109, 3004036, 3004038,
    2979113, 2979050, 2979137, 2979114, 2982471, 2982486, 3020633, 3020637,
    3020638, 2989215, 2989217, 2989204, 3005538, 3005560, 3005570, 3005540,
    3009140, 3009161, 3005583, 3005584, 3005603, 3009144, 3005616, 3005536,
    3005523, 3005535, 3004804, 3036260, 3009138, 3009139, 3009130, 3008758,
    3007139, 3007141, 3007142, 3011216, 3011217, 3011218, 3007180, 3006184,
    3006183, 3005575, 3005610, 3005605, 3005573, 3005590, 3005593, 3005596,
    3004812, 3004814, 3004820, 3004815, 3005606, 3005612, 3005607, 3005608,
    3036253, 3027021, 3027022, 3027024, 3027023, 3012068, 3027020, 3024427,
    3018861, 3018862, 3034337, 3004030, 3004031, 3024416, 3027040, 3012082,
    3012083, 3016094, 3016091, 3016093, 3027001, 3016074, 3018874, 3018869,
    3018872, 3012057, 3012058, 3012067, 3024448, 3024423, 3024445, 3003057,
    3003058, 3016028, 3016030, 3016034, 3004413, 3004415, 3004416, 3012069,
    3004005, 3004007, 3012084, 3021826, 3021827, 3027019, 3027015, 3027016,
    3027018, 3011105, 3011125, 3011107, 3011130, 3068677, 3068678, 3011119,
    3011148, 3011149, 3011113, 3011114, 3028729, 3011132, 3011127, 2985150,
    2985209, 2985269, 2989531, 2989546, 2989547, 2989518, 2989516, 2989522,
    3006711, 2989548, 2989535, 2989521, 2989500, 2989503, 2989498, 3025292,
    3006747, 2989497, 3013600, 3006732, 3006748, 2989508, 2989515, 2954043,
    3013598, 3013597, 3015495, 3015497, 3097265, 3097270, 3013586, 2954073,
    3106298, 2954022, 2954042, 3039786, 3059211, 3013580, 3013581, 3006733,
    3006676, 3026816, 3027264, 3027322, 3006682, 3006714, 3006710, 2989496,
    2988860, 3097269, 2954047, 3013612, 3006663, 3006664, 3006705, 3006707,
    3006726, 3006729, 3006740, 2989527, 3026747, 3086060, 3087380, 2989482,
    2989506, 3004752, 3004758, 2990939, 3020865, 3013613, 3006754, 3008807,
    3011221, 3009396, 3008805, 3013482, 3008791, 3009403, 3009392, 3036841,
    3036819, 3049915, 3062896, 2990168, 3018153, 3018149, 3031738, 3016465,
    3016467, 3016463, 3005720, 3005724, 3005736, 3005722, 3005738, 3005739,
    3007462, 3006504, 3006505, 3007237, 3005171, 3005178, 3005179, 3005735,
    3005740, 3005723, 3006500, 3006501, 3006502, 3010495, 3010490, 3010453,
    3087218, 3016437, 3016441, 3016443, 3109249, 3007463, 3010683, 3010696,
    3010697, 3010699, 3010702, 3010704, 3024020, 3025331, 3025422, 3025367,
    3025358, 3025327, 3025686, 3025536, 3025621, 3025605, 3025440, 3025522,
    3027101, 3027104, 3027103, 3026885, 3026872, 3026873, 3027100, 3047640,
    3047574, 2988969, 2989044, 3007521, 3007450, 3007474, 3029589, 3029600,
    2989730, 2989743, 2989744, 2989729, 2989722, 3007707, 2988885, 2980826,
    2980814, 2980813, 2919084, 2918935, 2924859, 2988965, 2988964, 2922781,
    2922596, 2917113, 2917115, 2904477, 2904458, 2904467, 2905998, 2906017,
    2906069, 2906034, 3005681, 3005661, 2982923, 2982936, 2982939, 2982972,
    2982973, 2982970, 2982941, 2982965, 2982969, 2924548, 2987558, 2987563,
    3024718, 3022693, 3036275, 3000068, 3001193, 3003475, 3002440, 2924909,
    2939889, 3010204, 3010220, 3026397, 3026436, 3007862, 3007863, 2991731,
    3030239, 3007419, 3007421, 3007423, 2904333, 2980724, 3009619, 3012102,
    3008462, 3010432, 2983006, 3039415, 3113036, 3007077, 2941391, 2941612,
    3012127, 3012163, 2982516, 2982512, 2997281, 2982473, 2981778, 2982489,
    2987058, 2987060, 2982515, 2982494, 2988373, 3002298, 3010330, 3010344,
    2982518, 2982659, 2982632, 3010311, 3010314, 3002283, 2982492, 2982633,
    2982629, 3010308, 3026772, 3027367, 3027299, 3022969, 3064732, 3027332,
    3027440, 2992327, 2992329, 2992331, 3010332, 3010333, 3029612, 3016027,
    3027398, 3027363, 3067742, 3025626, 3004708, 3002240, 3002287, 3002290,
    3002237, 3002241, 3002297, 3025693, 3004602, 2982532, 2931127, 3001106,
    3001111, 3001109, 3019115, 3019116, 2973266, 3013004, 3018550, 3018956,
    3018989, 3018226, 2902464, 3009331, 2913876, 3018742, 3001107, 3033768,
    3037266, 3009298, 3008890, 3009270, 3009728, 3009031, 3028512, 3069202,
    3069209, 3037706, 3037708, 3037716, 3008875, 3009156, 3020553, 2988332,
    2982474, 2996030, 2996212, 2982488, 2982490, 3020636, 3006200, 3006199,
    3005579, 3005595, 3005576, 3005525, 3005614, 3005543, 3005532, 3005533,
    3009071, 3008759, 3009115, 3006203, 3005599, 3011219, 3006260, 3005561,
    3004798, 3004800, 3007679, 3004801, 3004803, 3006186, 3006189, 3007177,
    3007179, 3006198, 3006196, 3006197, 3007189, 3007183, 3010942, 3015499,
    3005625, 3005613, 3004824, 3004808, 3004809, 3007163, 3013274, 3004819,
    3004823, 3004821, 3004810, 3006603, 3006608, 3004818, 3004822, 3004817,
    3007167, 3006607, 3027035, 3027037, 3027036, 3018867, 3004340, 3027038,
    3004337, 3004339, 3016076, 3027003, 3027002, 3027004, 3011110, 3011146,
    3011147, 3004650, 3011103, 3004409, 3027039, 3011104, 3024457, 3028730,
    3011136, 3011140, 3011135, 3012428, 3012427, 3012429, 3011137, 3011117,
    3011118, 3011138, 3011139, 3011150, 3004653, 3004654, 3011106, 3011129,
    3011133, 3011120, 3027058, 3011142, 3011144, 3011145, 3011101, 3011122,
    3011134, 3011102, 3011123, 3028733, 3028732, 3028731, 3011116, 3011115,
    3028735, 3011141, 3011128, 3011109, 3034466, 3068679, 3039765, 3039748,
    3090062, 3005424, 3034326, 3005428, 3006684, 2989524, 2989480, 2989539,
    2989529, 3006692, 2989517, 2989545, 2989532, 2989541, 2989538, 2989533,
    3006757, 2989513, 3017619, 3017617, 3017608, 3013593, 3013605, 3015494,
    3097273, 3097259, 3013682, 3106044, 3013602, 3013603, 3013604, 3006721,
    3013579, 3017162, 3059210, 3006739, 3006769, 3027376, 3097263, 3017159,
    3006736, 3006737, 3006695, 3006712, 3006724, 3006741, 2989483, 3006756,
    2989507, 3027423, 3006677, 3008816, 3008810, 3014878, 3008814, 3008792,
    3014880, 2985991, 2985992, 2985988, 3087226, 3087116, 3010486, 3010485,
    3010498, 3010492, 3010493, 3010496, 3007464, 3006503, 3010506, 3016456,
    3016459, 3025515, 3025743, 3027098, 3027099, 3027089, 3027091, 3027090,
    2989176, 2989072, 2989726, 2989723, 2989696, 2989709, 2919085, 2919080,
    2918938, 2918939, 2924855, 3005727, 2984645, 3002455, 2984648, 2984634,
    2984659, 2984656, 2938709, 3038297, 3038323, 3068221, 3024774, 3003571,
    3002844, 3011160, 3024167, 3024162, 3024165, 3019286, 3019296, 3019298,
    3030186, 3030184, 3030185, 3012862, 2933639, 3011143, 3017781, 3010151,
    3011173, 3019740, 3019606, 3019607, 3011180, 3047175, 3047153, 3025945,
    3025940, 3035303, 3024471, 3035392, 3028990, 3029174, 2985345, 2985214,
    3024783, 3024088, 3024459, 3024467, 3035090, 2951752, 3088744, 3028693,
    3088766, 3035075, 3035087, 3026286, 3026559, 3090704, 3022970, 3022973,
    3088741, 3090715, 3008616, 3095846, 3095848, 3093333, 3093335, 3088743,
    3029008, 3029002, 3090697, 3024090, 3024091, 3069624, 3007830, 3007831,
    3007861, 3007864, 3007874, 3007390, 3007391, 3007393, 3007396, 3007398,
    3007395, 3007832, 3034338, 3034350, 3034339, 3004797, 3009567, 3004857,
    3009491, 3009588, 3038975, 3007064, 3000820, 3025807, 2973267, 2973272,
    2996714, 3013186, 3013081, 3013114, 3013033, 3013041, 3009335, 2996711,
    3022328, 3022330, 3022320, 3022321, 3022327, 3022324, 3022325, 3022323,
    3001108, 3001074, 3025271, 3000599, 3054260, 3028513, 3037161, 3010554,
    3010605, 2979071, 3004022, 2979128, 2979097, 3020635, 3020639, 3020431,
    2998124, 2998135, 2998140, 3005565, 3005615, 3005551, 3005526, 2998138,
    2998141, 3005618, 3007190, 3004802, 3007166, 3005600, 3005602, 3005604,
    3024420, 3024442, 3024444, 3016023, 3012071, 3012072, 3034346, 3034459,
    3028734, 3028736, 3006688, 2989536, 2989540, 2990930, 3013609, 3013610,
    3013611, 3008772, 3008788, 3008793, 3010685, 3010710, 3010711, 3025965,
    3027088, 3025289, 3027105, 2988968, 2988966, 2988967, 3047325, 3047414,
    2988738, 3017169, 3019552, 2989708, 2988760, 2987753, 2989707, 2980812,
    2980830, 2980828, 2988961, 3003375, 3007860, 3061052, 3038253, 3009141,
    2979078, 3013296, 3013300, 3027000, 3028727, 3028728, 3011124, 3006709,
    2989702, 2988809, 2988844, 2988862, 2981499, 2982884, 2981335, 3032628,
    3003390, 3028511, 3076031, 3013588, 3030237, 3019714, 3019684, 3019695,
    3003070, 3002398, 3002397, 3004811, 3022983, 3022975, 2940855, 3007405,
    3007412,
  ];

  // Función de renderizado optimizada para portafolios
  function renderPortafolioTree(nodes, can_edit, ruta = "") {
    if (!nodes || nodes.length === 0) return null;

    const ul = document.createElement("ul");
    ul.classList.add("folder-list", "portafolio-tree");

    nodes.forEach((node) => {
      const li = document.createElement("li");
      li.classList.add("folder-item", "portafolio-item");

      const icon = document.createElement("i");
      const span = document.createElement("span");
      span.textContent = node.name;

      const rutaActual = ruta ? `${ruta} > ${node.name}` : node.name;

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

        if (carpetasRestringidasCohorte1.includes(rutaActual)) {
          const fichaActual = parseInt(
            document.getElementById("fichaNumActual").textContent.trim()
          );

          if (fichasCohorte1.includes(fichaActual)) {
            // 🔹 Solo en este caso aplicamos el cursor tipo pointer
            span.style.cursor = "pointer";

            span.addEventListener("click", () => {
              // 🔹 Cerrar modal aprendiz
              const modalAprendiz = bootstrap.Modal.getInstance(
                document.getElementById("portafolioAprendizModal")
              );
              if (modalAprendiz) modalAprendiz.hide();

              // 🔹 Cambiar a tab ficha
              const tabFicha = document.querySelector("#portfolioFicha-tab");
              if (tabFicha) new bootstrap.Tab(tabFicha).show();

              // 🔹 Cambiar al subtab "Portafolio" dentro de portfolioFicha
              const subTabPortafolio =
                document.querySelector("#portafolio-tab");
              if (subTabPortafolio) new bootstrap.Tab(subTabPortafolio).show();

              Toastify({
                text:
                  "Las evidencias de formación de las etapas de análisis y planeación, " +
                  "para las fichas de cohorte 1, se alojan en la carpeta 'LINK DE PORTAFOLIO APRENDICES 2024'\n" +
                  "dentro del portafolio general de la ficha.",
                duration: 6000,
                close: true,
                gravity: "top",
                position: "center",
                stopOnFocus: true,
                style: {
                  background: "#1E2DBE",
                  color: "#fff",
                  fontSize: "14px",
                  lineHeight: "1.5",
                  padding: "12px 20px",
                  borderRadius: "8px",
                  maxWidth: "500px",
                  whiteSpace: "pre-line",
                },
              }).showToast();

              // 🔹 Resaltar carpeta especial
              setTimeout(() => {
                const carpetaSpan = document.querySelector(
                  'span[data-portafolio-link="true"]'
                );
                if (carpetaSpan) {
                  carpetaSpan.scrollIntoView({
                    behavior: "smooth",
                    block: "center",
                  });
                  carpetaSpan.classList.add("blink-highlight");
                  setTimeout(
                    () => carpetaSpan.classList.remove("blink-highlight"),
                    3000
                  );
                }
              }, 2000);
            });
          }
        }

        if (
          can_edit &&
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
        if (node.children && node.children.length > 0) {
          subFolderContainer.appendChild(
            renderPortafolioTree(node.children, can_edit, rutaActual)
          );
        }

        li.appendChild(icon);
        li.appendChild(span);
        li.appendChild(subFolderContainer);
      } else if (node.tipo === "documento") {
        // Documentos con colores según tipo
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

        link.href = "/media/" + path + encodeURIComponent(filename);
        link.target = "_blank";
        link.append(icon, span);
        li.appendChild(link);

        if (can_edit && userRole != "instructor") {
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

  let treeApreListenersInitialized = false;

  // Event listeners específicos para el portafolio
  function agregarEventListenersPortafolio(can_edit) {
    if (treeApreListenersInitialized) return;

    const treeContainer = document.getElementById("folderTreeAprendiz");
    if (!treeContainer) return;

    // Crear nuevo listener
    treeContainer.addEventListener("click", async (e) => {
      const target = e.target.closest(".folder-item > i, .folder-item > span");
      if (target) {
        const folderId = target.dataset.folderId;
        const icon =
          target.tagName === "I" ? target : target.previousElementSibling;
        togglePortafolioFolder(folderId, icon);
        return;
      }
      if (can_edit) {
        const target2 = e.target.closest(".bi-trash");
        if (target2) {
          const li = target2.closest("li");
          const docId = li?.dataset.documentId;
          const folderId = li.dataset.folderId;
          if (!docId) return;

          const confirmed = await confirmToast("¿Eliminar este documento?");
          if (confirmed) deleteFileAprendiz(docId, folderId, can_edit);
          return;
        }

        const target3 = e.target.closest(".upload-item");
        if (target3) {
          const folderId = target3.dataset.folderId;
          openUploadModalAprendiz(folderId);
          return;
        }
      }
    });

    if (can_edit) {
      treeContainer.addEventListener("dragover", (e) => {
        const folder = e.target.closest(
          "[data-folder-id][data-droppable='true']"
        );

        if (folder) {
          e.preventDefault();
          folder.classList.add("dragover-highlight");
        }
      });

      treeContainer.addEventListener("dragleave", (e) => {
        const folder = e.target.closest(
          "[data-folder-id][data-droppable='true']"
        );

        if (folder) {
          e.preventDefault();
          folder.classList.remove("dragover-highlight");
        }
      });

      treeContainer.addEventListener("drop", async (e) => {
        const folder = e.target.closest(
          "[data-folder-id][data-droppable='true']"
        );
        if (!folder) return;
        e.preventDefault();
        folder.classList.remove("dragover-highlight");
        await handleDropOnFolder(folder, e, "aprendiz");
      });

      treeContainer.addEventListener("dragstart", (e) => {
        const docItem = e.target.closest("li[data-document-id");
        if (!docItem) return;
        e.dataTransfer.setData("type", "document");
        e.dataTransfer.setData("documentId", docItem.dataset.documentId);
        e.dataTransfer.setData("sourceFolderId", docItem.dataset.folderId);
        // Opcional: indicar el efecto
        e.dataTransfer.effectAllowed = "move";
      });
    }
    const uploadButton = document.getElementById("uploadButtonAprendiz");
    if (uploadButton)
      uploadButton.addEventListener("click", () =>
        uploadFile("aprendiz", can_edit)
      );

    treeApreListenersInitialized = true;
  }

  // *Toggle portafolio
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

  async function deleteFileAprendiz(fileId, folderId, can_edit) {
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
          await actualizarCarpeta(folderId, "aprendiz", can_edit);
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

  // *******************************************************************
  // *                                                                 *
  // *        ¡ADVERTENCIA! ZONA DE CÓDIGO JUICIOS EVALUATIVOS         *
  // *                                                                 *
  // *******************************************************************

  const tablaJuiciosActuEl = document.getElementById("tabla-juicios-actuales");

  const tablaJuiciosActu = new DataTable(tablaJuiciosActuEl, {
    serverSide: true,
    processing: false,
    ajax: {
      url: "/api/formacion/juicios/filtrar/",
      type: "GET",
      data: function (d) {
        d.id_ficha = fichaId;
      },
    },
    columns: [
      { data: "fecha_repor" },
      { data: "apre_nom" },
      { data: "rap_nom" },
      { data: "eva" },
      { data: "fecha" },
      { data: "instru_nom" },
    ],
    language: {
      url: "https://cdn.datatables.net/plug-ins/2.1.8/i18n/es-ES.json",
      emptyTable: "Sin historial",
    },
  });

  const tablaJuiciosHistoEl = document.getElementById(
    "tabla-juicios-historial"
  );

  const tablaJuiciosHisto = new DataTable(tablaJuiciosHistoEl, {
    serverSide: true,
    processing: false,
    ajax: {
      url: "/api/formacion/juiciosHistorial/filtrar/",
      type: "GET",
      data: function (d) {
        d.ficha_id = fichaId;
      },
    },
    columns: [
      {
        data: "fecha_diff",
        render: function (data, type, row) {
          if (!data) return "Sin registro";
          const date = new Date(data);
          const day = String(date.getDate()).padStart(2, "0");
          const month = String(date.getMonth() + 1).padStart(2, "0");
          const year = date.getFullYear();
          return `${year}-${month}-${day}`;
        },
      },
      { data: "apre_nom" },
      { data: "descri" },
      { data: "tipo_cambi" },
      { data: "jui_desc" },
      { data: "instru_nom" },
    ],
    language: {
      url: "https://cdn.datatables.net/plug-ins/2.1.8/i18n/es-ES.json",
      emptyTable: "Sin historial",
    },
  });
});
