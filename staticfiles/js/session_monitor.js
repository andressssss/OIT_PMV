// // Verificar si el usuario está autenticado
// fetch('/api/check-auth/')
//     .then(response => response.json())
//     .then(data => {
//         const userLoggedIn = data.isAuthenticated;
//         console.log(userLoggedIn ? "Usuario autenticado" : "Usuario no autenticado");

//         // Si el usuario está autenticado, crear el WebSocket
//         if (userLoggedIn) {
//             console.log("Usuario autenticado, creando WebSocket...");
//             createSocket();
//         } else {
//             console.log("El usuario no está autenticado, no se crea el WebSocket.");
//         }
//     })
//     .catch(error => {
//         console.error('Error al verificar autenticación:', error);
//         Swal.fire({
//             title: "Error",
//             text: "Hubo un problema al verificar tu autenticación. Intenta recargar la página.",
//             icon: "error"
//         });
//     });

// let socket;
// let sessionExpired = false;
// let intervalId;

// function createSocket() {
//     if (socket && (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING)) {
//         console.log("El WebSocket ya está conectado o conectándose.");
//         return;
//     }
//     console.log("Creando WebSocket...");
//     socket = new WebSocket('ws://127.0.0.1:8001/ws/session_expiration/');

//     socket.onopen = function(event) {
//         console.log('WebSocket está abierto, podemos enviar mensajes.');
//         intervalId = setInterval(function () {
//             if (socket && socket.readyState === WebSocket.OPEN) {
//                 console.log("Enviando solicitud para verificar la sesión...");
//                 socket.send(JSON.stringify({ check_session: true }));
//             }
//         }, 60000);
//     };

//     socket.onmessage = function(event) {
//         const message = JSON.parse(event.data);
//         console.log('Mensaje recibido:', message);

//         if (message.status === 'session_expired' && !sessionExpired) {
//             socket.close();

//             Swal.fire({
//                 title: "Sesión Expirada",
//                 text: "Tu sesión ha expirado. Serás redirigido al login.",
//                 icon: "warning"
//             }).then(function() {
//                 window.location.href = '/signin/';
//             });
//             sessionExpired = true;
//         } else if (message.status === 'session_active') {
//             console.log('La sesión sigue activa');
//             sessionExpired = false;
//         } else if (message.status === 'session_inactive') {
//             console.log('El usuario no está autenticado');
//         }
//     };

//     socket.onerror = function(event) {
//         console.error('Error en WebSocket:', event);
//     };

//     socket.onclose = function(event) {
//         console.log('WebSocket cerrado:', event);
//         clearInterval(intervalId);
//         socket = null;

//         if (!sessionExpired) {
//             console.log('Intentando reconectar WebSocket en 5 segundos...');
//             setTimeout(createSocket, 5000);
//         }
//     };
// }
