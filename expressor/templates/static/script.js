        const socket = io('http://127.0.0.1:5000/', {
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
        });
