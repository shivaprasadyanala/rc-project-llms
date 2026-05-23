// // remote-control.js
// const BASE = 'http://localhost:3000/api';

// async function send(cmd) {
//   const res = await fetch(`${BASE}/${cmd}`, { method: 'POST' });
//   console.log(`✓ ${cmd}`);
// }

// async function demoSequence() {
//   console.log('🕹️  Full demo starting...');
  
//   await send('right');  await new Promise(r=>setTimeout(r,800));
//   await send('punch');  await new Promise(r=>setTimeout(r,400)); await send('stop');
  
//   await new Promise(r=>setTimeout(r,600));
//   await send('left');   await new Promise(r=>setTimeout(r,400));
//   await send('kick');   await new Promise(r=>setTimeout(r,500)); await send('stop');
  
//   await new Promise(r=>setTimeout(r,800));
//   await send('right');  await new Promise(r=>setTimeout(r,600));
//   await send('up');     await new Promise(r=>setTimeout(r,300)); // Double jump!
//   await send('up');     await new Promise(r=>setTimeout(r,400));
//   await send('fireball');await new Promise(r=>setTimeout(r,800)); 
//   await send('stop');
  
//   console.log('🎉 Demo complete! Try your own commands.');
// }

// demoSequence();

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Window Game Example</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            text-align: center;
            margin-top: 50px;
        }
        #output {
            font-size: 20px;
            margin-top: 20px;
            color: green;
        }
        button {
            padding: 10px 20px;
            font-size: 16px;
        }
    </style>
</head>
<body>

    <h1>Simple Window Game</h1>
    <button onclick="window.game.start()">Start Game</button>
    <div id="output"></div>

    <script>
        // Define global game object
        window.game = {
            score: 0,

            init: function () {
                console.log("Game initialized");
                this.score = 0;
                document.getElementById("output").innerText = "Game Ready!";
            },

            start: function () {
                this.score++;
                document.getElementById("output").innerText =
                    "Game Started! Score: " + this.score;
            }
        };

        // Run when page loads
        window.onload = function () {
            window.game.init();
        };
    </script>

</body>
</html>
