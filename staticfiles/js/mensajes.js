// Script Listener de mensajes!
document.addEventListener("DOMContentLoaded", function () {
    const messagesContainer = document.getElementById("messages-container");
    const messagesData = messagesContainer.dataset.messages;

    if (messagesData) {
        const messages = JSON.parse(`[${messagesData.slice(0, -1)}]`); // Quita la coma final
        messages.forEach((msg) => {
            Swal.fire({
                icon: msg.icon || "info",
                title: msg.title || "",
                showConfirmButton: false,
                timer: 3000
            });
        });
    }
});