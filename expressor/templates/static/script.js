// Define the port variable before using it
let port = 8585; // or any other value you set in your Flask app
//const socketUrl = {{ socket_url }};
//const socket = io('ws://127.0.0.1:' + port + '/', {
//const socket = io(socketUrl[0]}, {
const socket = io(window.location.origin + '/get_socket_url,
  transport: ['websocket', 'polling'],
  reconnectionDelayMax: 10000,
  reconnectionInterval: 500
});


document.getElementById('sendMessage').addEventListener('click', () => {
  const message = document.getElementById('messageInput').value;
  socket.emit('message', message);
  document.getElementById('messageInput').value = '';
});

socket.on('connect', () => {
  console.log('Connected to the server');
});

socket.on('disconnect', () => {
  console.log('Disconnected from the server');
});

socket.on('message', (data) => {
  console.log(`Received message: ${data}`);
  if (typeof data === 'string' && data.startsWith('video.mp4')) {
    const newSrc = data;
    document.getElementById('video').src = newSrc;
  }
});
