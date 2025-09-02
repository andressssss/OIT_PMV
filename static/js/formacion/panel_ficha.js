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

  function renderTree(nodes) {
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

        link.href = "/media/" + path + encodeURIComponent(filename);
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
      await handleDropOnFolder(folder, e, "ficha");
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
      uploadButton.addEventListener("click", () => uploadFile("ficha"));

    treeListenersInitialized = true;
  }

  async function handleDropOnFolder(folderElement, e, contexto) {
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
        await actualizarCarpeta(sourceFolderId, contexto);
        await actualizarCarpeta(folderId, contexto);
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
      await actualizarCarpeta(folderId, contexto);
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

  async function uploadFile(contexto) {
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
      await actualizarCarpeta(folderId, contexto);
      fileInputElement.value = "";
    } catch (error) {
      console.error("Error al subir el archivo:", error);
      toastError("Ocurrió un error inesperado.");
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
          await actualizarCarpeta(folderId, "ficha");
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

  async function actualizarCarpeta(folderId, contexto) {
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
        const hijos = renderFn(data);
        if (hijos) {
          subFolderContainer.appendChild(hijos);
        }
      }
      renderHistorial();
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
                row.estado.toLowerCase() !== "desertado"
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

      const portafolioTree = renderPortafolioTree(data);
      if (portafolioTree) {
        portafolioContainer.appendChild(portafolioTree);
      }

      agregarEventListenersPortafolio();
      cargarHistorial("aprendiz", aprendizId);
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

  let treeApreListenersInitialized = false;

  // Event listeners específicos para el portafolio
  function agregarEventListenersPortafolio() {
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

      const target2 = e.target.closest(".bi-trash");
      if (target2) {
        const li = target2.closest("li");
        const docId = li?.dataset.documentId;
        const folderId = li.dataset.folderId;
        if (!docId) return;

        const confirmed = await confirmToast("¿Eliminar este documento?");
        if (confirmed) deleteFileAprendiz(docId, folderId);
        return;
      }

      const target3 = e.target.closest(".upload-item");
      if (target3) {
        const folderId = target3.dataset.folderId;
        openUploadModalAprendiz(folderId);
        return;
      }
    });

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

    const uploadButton = document.getElementById("uploadButtonAprendiz");
    if (uploadButton)
      uploadButton.addEventListener("click", () => uploadFile("aprendiz"));

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
          await actualizarCarpeta(folderId, "aprendiz");
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
