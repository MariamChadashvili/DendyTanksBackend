const gameId = 123;  // Use any game_id you want to test
const ws = new WebSocket(`ws://localhost:8000/ws/game/${gameId}/`);

const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');

let gameData = null;

ws.onopen = function(event) {
    console.log("WebSocket is open now.");
};

ws.onmessage = function(event) {
    gameData = JSON.parse(event.data);
    drawGame();
};

ws.onclose = function(event) {
    console.log("WebSocket is closed now.");
};

ws.onerror = function(error) {
    console.log("WebSocket error: " + error);
};

function sendAction(action, playerId, direction = null) {
    ws.send(JSON.stringify({
        action: action,
        player_id: playerId,
        direction: direction
    }));
}

function drawGame() {
    if (!gameData) return;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Draw walls
    gameData.map.walls.forEach(wall => {
        ctx.fillStyle = wall.type === 'BRICK' ? 'brown' : 'gray';
        ctx.fillRect(wall.position.x_position, wall.position.y_position, gameData.map.block_size, gameData.map.block_size);
    });

    // Draw bases
    gameData.map.bases.forEach(base => {
        ctx.fillStyle = 'green';
        ctx.fillRect(base.position.x_position, base.position.y_position, gameData.map.block_size, gameData.map.block_size);
    });

    // Draw players
    Object.values(gameData.players).forEach(player => {
        ctx.fillStyle = player.color.toLowerCase();
        ctx.fillRect(player.position.x_position, player.position.y_position, gameData.map.block_size, gameData.map.block_size);
    });

    // Draw bullets
    Object.values(gameData.players).forEach(player => {
        if (player.bullet) {
            ctx.fillStyle = 'black';
            ctx.fillRect(player.bullet.position.x_position, player.bullet.position.y_position, gameData.map.bullet_size, gameData.map.bullet_size);
        }
    });
}

// Add event listeners for player controls
document.addEventListener('keydown', (event) => {
    const playerId = '1'; // Hardcoded for testing, should be dynamic
    switch (event.key) {
        case 'ArrowUp':
            sendAction('start_move', playerId, 'up');
            break;
        case 'ArrowDown':
            sendAction('start_move', playerId, 'down');
            break;
        case 'ArrowLeft':
            sendAction('start_move', playerId, 'left');
            break;
        case 'ArrowRight':
            sendAction('start_move', playerId, 'right');
            break;
        case ' ':
            sendAction('shoot', playerId);
            break;
    }
});

document.addEventListener('keyup', (event) => {
    const playerId = 'player1'; // Hardcoded for testing, should be dynamic
    if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(event.key)) {
        sendAction('stop_move', playerId);
    }
});


