// game.js - FULL VERSION with health, enemies, double jump, multiple attacks
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');

const game = {
  player: {
    x: 100, y: 240, vx: 0, vy: 0,
    width: 32, height: 48,
    onGround: false, jumpsLeft: 2, // Double jump support
    facing: 1, attacking: false, attackType: 0, attackTimer: 0,
    health: 100, maxHealth: 100
  },

  enemies: [
    { x: 500, y: 240, vx: -1.5, vy: 0, width: 32, height: 48, health: 80, maxHealth: 80, patrolRange: 150, patrolCenter: 500 },
    { x: 300, y: 240, vx: 1.2, vy: 0, width: 32, height: 48, health: 60, maxHealth: 60, patrolRange: 100, patrolCenter: 300 }
  ],

  keys: { left: false, right: false, up: false, down: false, attack: false },
  gravity: 0.65, jumpPower: -13, moveSpeed: 4.2,
  api: {}
};

// ─── ATTACK TYPES ──────────────────────────────────────────────────────────
const ATTACKS = {
  0: { name: 'punch',   damage: 25, range: 45,  color: '#ffffff', cooldown: 18 },
  1: { name: 'kick',    damage: 35, range: 50,  color: '#ffaa00', cooldown: 25 },
  2: { name: 'fireball',damage: 50, range: 200, color: '#ff4444', cooldown: 40, isProjectile: true }
};

// ─── API (unchanged + new attack selection) ────────────────────────────────
// function setKey(k, value) { if (k in game.keys) game.keys[k] = !!value; }
function setKey(k, value) {
  if (!(k in game.keys)) return;

  if (k === 'up' && value === true) {
    game.keys.upPressed = true; // one-time trigger
  }

  game.keys[k] = !!value;
}

game.api = {
  up()     { setKey('up', true); },
  down()   { setKey('down', true); },
  left()   { setKey('left', true); },
  right()  { setKey('right', true); },
  attack() { setKey('attack', true); },

  punch()   { game.player.attackType = 0; setKey('attack', true); },
  kick()    { game.player.attackType = 1; setKey('attack', true); },
  fireball(){ game.player.attackType = 2; setKey('attack', true); },

  press(key) {
    if (['up','down','left','right','attack'].includes(key)) setKey(key, true);
  },
  release(key) { if (key) setKey(key, false); else Object.keys(game.keys).forEach(k => game.keys[k] = false); },
  releaseAll() { game.api.release(); }
};

['up','down','left','right','attack'].forEach(dir => {
  const original = game.api[dir];
  game.api[dir] = function(v) {
    if (arguments.length === 0 || v === true) original.call(game.api);
    else if (v === false) game.api.release(dir);
  };
});

// ─── POSTMESSAGE HANDLER (for HTTP API server) ─────────────────────────────
window.addEventListener('message', (event) => {
  const cmd = event.data;
  if (!cmd || typeof cmd !== 'object') return;
  const api = window.game?.api;
  if (!api) return;

  switch (cmd.action) {
    case 'press':
      api.press(cmd.key || 'attack');
      if (cmd.key === 'punch') api.punch();
      if (cmd.key === 'kick') api.kick();
      if (cmd.key === 'fireball') api.fireball();
      break;
    case 'release': case 'release-all': api.release(cmd.key); break;
    case 'punch': api.punch(); break;
    case 'kick': api.kick(); break;
    case 'fireball': api.fireball(); break;
  }
});

// ─── GAME LOGIC ───────────────────────────────────────────────────────────
function update() {
  const p = game.player;

  // ─── PLAYER MOVEMENT ───
  // p.vx = 0;
  // if (game.keys.left)  p.vx -= game.moveSpeed;
  // if (game.keys.right) p.vx += game.moveSpeed;
  // if (p.vx !== 0) p.facing = Math.sign(p.vx);
  const STEP_SIZE = 20;

  if (game.keys.left && !game.keys.right) {
    p.x -= STEP_SIZE;
    p.facing = -1;
    // Optional: consume the key press so it doesn't repeat every frame
    game.keys.left = false;
  }

  if (game.keys.right && !game.keys.left) {
    p.x += STEP_SIZE;
    p.facing = 1;
    game.keys.right = false;
  }

  // ─── DOUBLE JUMP ───
  // if (game.keys.up && (p.onGround || p.jumpsLeft > 0)) {
  //   p.vy = game.jumpPower;
  //   if (!p.onGround) p.jumpsLeft--;
  //   p.onGround = true;
  // }
  if (game.keys.upPressed && (p.onGround || p.jumpsLeft > 0)) {
  p.vy = game.jumpPower;

  if (!p.onGround) {
    p.jumpsLeft--;
  }

  p.onGround = false;

  // consume the jump press
  game.keys.upPressed = false;
}

  // ─── PHYSICS ───
  p.vy += game.gravity;
  p.x += p.vx;
  p.y += p.vy;

  // ─── COLLISION (FLOOR) ───
  if (p.y + p.height > 240) {
    p.y = 240 - p.height;
    p.vy = 0;
    p.onGround = true;
    p.jumpsLeft = 2; // Reset double jump
  }

  // ─── ATTACKS ───
  if (game.keys.attack && !p.attacking) {
    p.attacking = true;
    p.attackTimer = ATTACKS[p.attackType].cooldown;
  }
  if (p.attacking) {
    p.attackTimer--;
    if (p.attackTimer <= 0) p.attacking = false;
  }

  // ─── BOUNDARIES ───
  p.x = Math.max(0, Math.min(canvas.width - p.width, p.x));

  // ─── ENEMY AI & COLLISIONS ───
  game.enemies.forEach((enemy, i) => {
    updateEnemy(enemy);
    checkHit(p, enemy, true);  // Player hits enemy
    checkHit(enemy, p, false); // Enemy hits player
  });

  // Clean up dead enemies
  game.enemies = game.enemies.filter(e => e.health > 0);
}

function updateEnemy(enemy) {
  // Simple patrol AI
  enemy.vy += game.gravity;
  enemy.x += enemy.vx;
  enemy.y += enemy.vy;

  // Patrol boundaries
  if (enemy.x < enemy.patrolCenter - enemy.patrolRange || enemy.x > enemy.patrolCenter + enemy.patrolRange) {
    enemy.vx *= -1;
  }

  // Floor collision
  if (enemy.y + enemy.height > 240) {
    enemy.y = 240 - enemy.height;
    enemy.vy = 0;
  }

  // Face player
  const p = game.player;
  if (Math.abs(p.x - enemy.x) < 200) {
    enemy.vx += (p.x > enemy.x ? 0.5 : -0.5); // Chase player lightly
  }
}

function checkHit(attacker, defender, isPlayerAttacking) {
  if (!attacker.attacking) return;

  const attack = ATTACKS[attacker.attackType];
  const distX = defender.x - attacker.x;
  const distY = Math.abs(defender.y - attacker.y);
  const range = Math.abs(distX) < attack.range && distY < 40;

  if (range) {
    defender.health -= attack.damage;
    defender.health = Math.max(0, defender.health);
    
    // Knockback
    const knockForce = isPlayerAttacking ? -3 : 3;
    defender.vx += attacker.facing * knockForce;
    
    console.log(`${isPlayerAttacking ? 'Player' : 'Enemy'} hit for ${attack.damage}! Enemy HP: ${defender.health}`);
  }
}

// ─── RENDER ────────────────────────────────────────────────────────────────
function render() {
  ctx.fillStyle = "#0d1117";
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  // Floor
  ctx.fillStyle = "#21262d";
  ctx.fillRect(0, 240, canvas.width, canvas.height - 240);

  const p = game.player;

  // ─── PLAYER ───
  renderEntity(p, p.attacking ? ATTACKS[p.attackType].color : "#f0883f");

  // ─── ENEMIES ───
  game.enemies.forEach(enemy => {
    renderEntity(enemy, enemy.health < enemy.maxHealth * 0.3 ? "#ff4444" : "#58a6ff");
  });

  // ─── HEALTH BARS ───
  renderHealthBar(p, 10, 20, "#f0883f");
  game.enemies.forEach((e, i) => {
    renderHealthBar(e, canvas.width - 100, 20 + i * 25, "#58a6ff");
  });

  // ─── UI ───
  ctx.fillStyle = "#ffffff";
  ctx.font = "16px monospace";
  ctx.fillText(`Jumps: ${p.jumpsLeft} | Attack: ${ATTACKS[p.attackType].name}`, 10, canvas.height - 20);
}

function renderEntity(entity, color) {
  // Shadow
  ctx.fillStyle = "rgba(0,0,0,0.4)";
  ctx.fillRect(entity.x + 4, 245, entity.width - 8, 10);

  // Body
  ctx.fillStyle = color;
  ctx.fillRect(entity.x, entity.y, entity.width, entity.height);

  // Eyes (face direction)
  ctx.fillStyle = "#000";
  const eyeX = entity.x + (entity.facing > 0 ? 20 : 8);
  ctx.fillRect(eyeX, entity.y + 12, 6, 6);

  // ─── ATTACK VISUALS ───
  if (entity.attacking) {
    const attack = ATTACKS[entity.attackType];
    if (attack.isProjectile) {
      // Fireball projectile
      const projX = entity.x + (entity.facing > 0 ? entity.width : -20);
      ctx.fillStyle = attack.color;
      ctx.beginPath();
      ctx.arc(projX + 15 * entity.facing, entity.y + 24, 8, 0, Math.PI * 2);
      ctx.fill();
    } else {
      // Melee (punch/kick)
      const atkX = entity.x + (entity.facing > 0 ? entity.width : -25);
      ctx.fillStyle = attack.color;
      ctx.fillRect(atkX, entity.y + (attack.name === 'kick' ? 28 : 12), 25, attack.name === 'kick' ? 16 : 16);
    }
  }
}

function renderHealthBar(entity, x, y, color) {
  const barWidth = 80;
  const healthPct = entity.health / entity.maxHealth;
  
  // Background
  ctx.fillStyle = "#333";
  ctx.fillRect(x, y, barWidth, 8);
  
  // Health
  ctx.fillStyle = healthPct > 0.6 ? color : healthPct > 0.3 ? "#ffaa00" : "#ff4444";
  ctx.fillRect(x, y, barWidth * healthPct, 8);
  
  // Border
  ctx.strokeStyle = "#fff";
  ctx.lineWidth = 1;
  ctx.strokeRect(x, y, barWidth, 8);
}

function loop() {
  update();
  render();
  requestAnimationFrame(loop);
}

loop();
window.game = game;

console.log("%cFULL GAME READY! 🎮", "color:lime;font-size:18px;font-weight:bold");
console.log("New API methods:");
console.log("  game.api.punch()");
console.log("  game.api.kick()");
console.log("  game.api.fireball()");
console.log("  game.api.up()  // double jump!");