// server.js
const express = require('express');
const path = require('path');

let gameState ={
            "grid_size": [5, 5],
            "player_pos": [200,100],
            "crops": {
                "crop1":{"pos":[400,275],"needs_water":true,"planted":false},
                "crop2":{"pos":[300,200],"needs_water":true,"planted":false},
                // "crop3":{"pos":[200,475],"needs_water":true,"planted":false},
                // "crop4":{"pos":[150,300],"needs_water":true,"planted":false},
                // "crop5":{"pos":[275,325],"needs_water":true,"planted":false},
            },
            "obstacles": [250,100],
            "water_available":false,
            "water_tank": [75,250],
            "goal_completed": false
        };

 ""
const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.json());

// Serve static files from the "public" folder
app.use(express.static(path.join(__dirname, 'public')));

// Default route
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'public','index.html'));
});


app.get('/get_game_state', (req, res) => {
  return res.json(gameState);
});

app.post('/post_game_state', (req, res) => {
  if (req.body.player_pos) {
        gameState.player_pos = req.body.player_pos;
    }
    gameState = req.body
    console.log('Updated gameState:', gameState);
    res.json(gameState);
});

// Error handling middleware
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).send('Something went wrong!');
});

// Start server
app.listen(PORT, () => {
  console.log(`Phaser game server running at http://localhost:${PORT}`);
});


// {
//     "grid_size": (5, 5),
//     "player_pos": [1, 2], 
//     "crops": {
//         (4, 2): {"needs_water": True},
//         (2, 1): {"needs_water": True},
//     },
//     "obstacles": {(3, 2)},
//     "goal_completed": False
// }