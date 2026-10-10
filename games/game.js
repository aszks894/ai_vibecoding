const canvas = document.getElementById('game');
const ctx = canvas.getContext('2d');
const fishCountEl = document.getElementById('fishCount');
const achievementCountEl = document.getElementById('achievementCount');
const catSelectEl = document.getElementById('catSelect');
const startGameButton = document.getElementById('startGame');
const catOptionButtons = [...document.querySelectorAll('.cat-option')];

const achievementIds = ['fish-fan', 'clean-paws', 'speed-paws', 'nine-lives'];
const achievementCards = new Map(
  achievementIds.map((id) => [id, document.querySelector(`[data-achievement="${id}"]`)])
);
const achievementStorageKey = 'cat-platformer-achievements';
const unlockedAchievements = loadAchievements();
let gameStartedAt = 0;
let gameStarted = false;
let knockouts = 0;
let selectedCat = 'white';

const catCoats = {
  white: { fur: '#f2f2f2', innerEar: '#686868', stripes: false },
  gray: { fur: '#929292', innerEar: '#4d4d4d', stripes: false },
  tiger: { fur: '#f2f2f2', innerEar: '#686868', stripes: true }
};

ctx.imageSmoothingEnabled = false;

const world = {
  width: 2100,
  height: 540
};

const keys = {};
let jumpQueued = false;
let cameraX = 0;

const player = {
  x: 84,
  y: 360,
  w: 30,
  h: 24,
  vx: 0,
  vy: 0,
  speed: 4.4,
  jumpForce: 12,
  onGround: false,
  facing: 1,
  invulnerable: 0
};

const platforms = [
  { x: 0, y: 500, w: 420, h: 40 },
  { x: 470, y: 420, w: 170, h: 20 },
  { x: 670, y: 340, w: 220, h: 20 },
  { x: 930, y: 410, w: 190, h: 20 },
  { x: 1180, y: 300, w: 180, h: 20 },
  { x: 1425, y: 360, w: 200, h: 20 },
  { x: 1690, y: 270, w: 150, h: 20 },
  { x: 1880, y: 500, w: 220, h: 40 },
  { x: 1030, y: 220, w: 70, h: 12 },
  { x: 1525, y: 220, w: 70, h: 12 }
];

const spikes = [
  { x: 380, y: 482, w: 70, h: 18 },
  { x: 1100, y: 482, w: 80, h: 18 },
  { x: 1560, y: 482, w: 120, h: 18 }
];

const saws = [
  { x: 770, y: 300, r: 16, minX: 700, maxX: 870, speed: 1.7, dir: 1 },
  { x: 1760, y: 240, r: 14, minX: 1710, maxX: 1828, speed: 1.5, dir: 1 }
];

const fish = [
  { x: 160, y: 454, collected: false },
  { x: 560, y: 384, collected: false },
  { x: 740, y: 304, collected: false },
  { x: 1240, y: 264, collected: false },
  { x: 1760, y: 234, collected: false }
];

const door = {
  x: 2010,
  y: 420,
  w: 32,
  h: 80
};

const particles = [];
let hasWon = false;

function loadAchievements() {
  try {
    const saved = JSON.parse(localStorage.getItem(achievementStorageKey) || '[]');
    if (!Array.isArray(saved)) return new Set();
    return new Set(saved.filter((id) => achievementIds.includes(id)));
  } catch (error) {
    console.warn('Could not load saved achievements:', error);
    return new Set();
  }
}

function saveAchievements() {
  try {
    localStorage.setItem(achievementStorageKey, JSON.stringify([...unlockedAchievements]));
  } catch (error) {
    console.warn('Could not save achievements:', error);
  }
}

function unlockAchievement(id) {
  if (unlockedAchievements.has(id)) return;
  unlockedAchievements.add(id);
  saveAchievements();
  renderAchievements();

  const card = achievementCards.get(id);
  if (card) {
    card.classList.remove('just-unlocked');
    void card.offsetWidth;
    card.classList.add('just-unlocked');
  }
}

function renderAchievements() {
  const collected = fish.filter((item) => item.collected).length;
  const elapsedSeconds = gameStarted ? (performance.now() - gameStartedAt) / 1000 : 0;
  const progress = {
    'fish-fan': `${collected} / 5`,
    'clean-paws': `${knockouts} knockouts`,
    'speed-paws': `${Math.max(0, Math.ceil(45 - elapsedSeconds))}s left`,
    'nine-lives': `${Math.min(knockouts, 3)} / 3`
  };

  for (const id of achievementIds) {
    const card = achievementCards.get(id);
    if (!card) continue;
    const unlocked = unlockedAchievements.has(id);
    card.classList.toggle('unlocked', unlocked);
    card.querySelector('.achievement-mark').textContent = unlocked ? '[*]' : '[ ]';
    card.querySelector('.achievement-progress').textContent = unlocked ? 'UNLOCKED' : progress[id];
  }
  achievementCountEl.textContent = `${unlockedAchievements.size} / ${achievementIds.length} UNLOCKED`;
}

function checkFinishAchievements() {
  const elapsedSeconds = (performance.now() - gameStartedAt) / 1000;
  if (knockouts === 0) unlockAchievement('clean-paws');
  if (elapsedSeconds < 45) unlockAchievement('speed-paws');
  if (knockouts >= 3) unlockAchievement('nine-lives');
}

function selectCat(cat) {
  selectedCat = cat;
  for (const button of catOptionButtons) {
    const selected = button.dataset.cat === cat;
    button.classList.toggle('selected', selected);
    button.setAttribute('aria-pressed', String(selected));
  }
}

function startGame() {
  if (gameStarted) return;
  gameStarted = true;
  gameStartedAt = performance.now();
  catSelectEl.hidden = true;
  renderAchievements();
}

function resetPlayer() {
  player.x = 84;
  player.y = 360;
  player.vx = 0;
  player.vy = 0;
  player.onGround = false;
  player.invulnerable = 60;
}

function isKeyPressed(key) {
  return !!keys[key];
}

function rectsOverlap(a, b) {
  return a.x < b.x + b.w && a.x + a.w > b.x && a.y < b.y + b.h && a.y + a.h > b.y;
}

function circleRectOverlap(circle, rect) {
  const closestX = Math.max(rect.x, Math.min(circle.x, rect.x + rect.w));
  const closestY = Math.max(rect.y, Math.min(circle.y, rect.y + rect.h));
  const dx = circle.x - closestX;
  const dy = circle.y - closestY;
  return dx * dx + dy * dy <= circle.r * circle.r;
}

function playerRect() {
  return { x: player.x, y: player.y, w: player.w, h: player.h };
}

function updatePlayer() {
  const moveLeft = isKeyPressed('arrowleft') || isKeyPressed('a');
  const moveRight = isKeyPressed('arrowright') || isKeyPressed('d');

  if (moveLeft && !moveRight) {
    player.vx = -player.speed;
    player.facing = -1;
  } else if (moveRight && !moveLeft) {
    player.vx = player.speed;
    player.facing = 1;
  } else {
    player.vx *= 0.72;
    if (Math.abs(player.vx) < 0.12) player.vx = 0;
  }

  if (jumpQueued && player.onGround) {
    player.vy = -player.jumpForce;
    player.onGround = false;
  }
  jumpQueued = false;

  player.vy += 0.6;
  player.vy = Math.min(player.vy, 14);

  const nextX = player.x + player.vx;
  player.x = nextX;
  for (const platform of platforms) {
    if (rectsOverlap(playerRect(), platform)) {
      if (player.vx > 0) player.x = platform.x - player.w;
      if (player.vx < 0) player.x = platform.x + platform.w;
      player.vx = 0;
    }
  }

  const nextY = player.y + player.vy;
  player.y = nextY;
  player.onGround = false;
  for (const platform of platforms) {
    if (rectsOverlap(playerRect(), platform)) {
      if (player.vy > 0) {
        player.y = platform.y - player.h;
        player.vy = 0;
        player.onGround = true;
      } else if (player.vy < 0) {
        player.y = platform.y + platform.h;
        player.vy = 0;
      }
    }
  }

  player.x = Math.max(0, Math.min(player.x, world.width - player.w));

  if (player.y > world.height + 120) {
    respawnPlayer();
  }
}

function respawnPlayer() {
  knockouts += 1;
  renderAchievements();
  resetPlayer();
  for (let i = 0; i < 28; i += 1) spawnSpark(player.x + player.w / 2, player.y + player.h / 2);
}

function checkCollectibles() {
  let collected = 0;
  fish.forEach((item) => {
    if (!item.collected) {
      const fishBox = { x: item.x - 10, y: item.y - 8, w: 20, h: 16 };
      if (rectsOverlap(playerRect(), fishBox)) {
        item.collected = true;
        for (let i = 0; i < 16; i += 1) spawnSpark(item.x, item.y);
      }
    }
    if (item.collected) collected += 1;
  });
  fishCountEl.textContent = String(collected);
  if (collected === fish.length) unlockAchievement('fish-fan');
  return collected;
}

function checkSpikesAndSaws() {
  for (const spike of spikes) {
    if (rectsOverlap(playerRect(), spike)) {
      respawnPlayer();
      return;
    }
  }

  for (const saw of saws) {
    const circle = { x: saw.x, y: saw.y, r: saw.r };
    if (circleRectOverlap(circle, playerRect())) {
      respawnPlayer();
      return;
    }
  }
}

function updateSaws() {
  for (const saw of saws) {
    saw.x += saw.speed * saw.dir;
    if (saw.x < saw.minX || saw.x > saw.maxX) {
      saw.dir *= -1;
      saw.x = Math.max(saw.minX, Math.min(saw.maxX, saw.x));
    }
  }
}

function spawnSpark(x, y) {
  particles.push({
    x,
    y,
    vx: (Math.random() - 0.5) * 3.4,
    vy: (Math.random() - 0.5) * 3.4,
    life: 18 + Math.random() * 12,
    size: 2 + Math.random() * 2
  });
}

function updateParticles() {
  for (const particle of particles) {
    particle.x += particle.vx;
    particle.y += particle.vy;
    particle.vy += 0.12;
    particle.life -= 1;
  }
  for (let i = particles.length - 1; i >= 0; i -= 1) {
    if (particles[i].life <= 0) particles.splice(i, 1);
  }
}

function showWinScreen() {
  const overlay = document.createElement('div');
  overlay.className = 'win-overlay';

  const flash = document.createElement('div');
  flash.className = 'win-flash';

  const confettiLayer = document.createElement('div');
  confettiLayer.className = 'confetti-layer';

  for (let i = 0; i < 72; i += 1) {
    const piece = document.createElement('span');
    piece.className = 'confetti-piece';
    const dx = (Math.random() - 0.5) * 660;
    const dy = -120 - Math.random() * 240;
    const rot = (Math.random() - 0.5) * 720;
    const delay = (Math.random() * 0.28).toFixed(2);
    const duration = (1.1 + Math.random() * 0.9).toFixed(2);
    const width = 6 + Math.random() * 12;
    const height = 14 + Math.random() * 26;
    piece.style.setProperty('--dx', `${dx}px`);
    piece.style.setProperty('--dy', `${dy}px`);
    piece.style.setProperty('--rot', `${rot}deg`);
    piece.style.setProperty('--delay', `${delay}s`);
    piece.style.setProperty('--duration', `${duration}s`);
    piece.style.width = `${width}px`;
    piece.style.height = `${height}px`;
    piece.style.left = '50%';
    piece.style.top = '50%';
    confettiLayer.appendChild(piece);
  }

  const panel = document.createElement('div');
  panel.className = 'win-panel';
  panel.innerHTML = '<div class="win-title">YOU WIN</div><div class="win-subtitle">CAT ESCAPED</div>';

  overlay.appendChild(flash);
  overlay.appendChild(confettiLayer);
  overlay.appendChild(panel);
  document.body.appendChild(overlay);
  document.body.style.pointerEvents = 'none';

  setTimeout(() => {
    if (document.body.contains(overlay)) {
      document.body.removeChild(overlay);
    }
    location.reload();
  }, 2200);
}

function checkWin() {
  if (hasWon) return true;

  const collected = checkCollectibles();
  if (collected >= 5) {
    const doorRect = { x: door.x, y: door.y, w: door.w, h: door.h };
    if (rectsOverlap(playerRect(), doorRect)) {
      hasWon = true;
      player.vx = 0;
      player.vy = 0;
      checkFinishAchievements();
      showWinScreen();
      return true;
    }
  }
  return false;
}

function drawBackground() {
  ctx.fillStyle = '#000000';
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  for (let i = 0; i < 60; i += 1) {
    const x = ((i * 173 + cameraX * 0.12) % (canvas.width + 80)) - 40;
    const y = (i * 67) % (canvas.height - 80);
    ctx.fillStyle = i % 2 === 0 ? '#e8e8e8' : '#a1a1a1';
    ctx.fillRect(x, y, 2, 2);
  }

  ctx.fillStyle = '#201f1f';
  for (let x = -40; x < canvas.width + 80; x += 160) {
    ctx.fillRect(x + (cameraX * 0.15) % 160, 20, 2, canvas.height - 60);
  }
}

function drawPlatforms() {
  for (const platform of platforms) {
    const screenX = platform.x - cameraX;
    ctx.fillStyle = '#f2f2f2';
    ctx.fillRect(screenX, platform.y, platform.w, platform.h);
    ctx.fillStyle = '#050505';
    ctx.fillRect(screenX + 4, platform.y + 4, platform.w - 8, platform.h - 8);
  }
}

function drawSpikes() {
  for (const spike of spikes) {
    const x = spike.x - cameraX;
    const height = spike.h;
    ctx.fillStyle = '#f2f2f2';
    for (let px = 0; px < spike.w; px += 12) {
      ctx.beginPath();
      ctx.moveTo(x + px, spike.y + height);
      ctx.lineTo(x + px + 6, spike.y);
      ctx.lineTo(x + px + 12, spike.y + height);
      ctx.closePath();
      ctx.fill();
    }
  }
}

function drawSaws() {
  for (const saw of saws) {
    const x = saw.x - cameraX;
    const y = saw.y;
    ctx.beginPath();
    ctx.strokeStyle = '#f2f2f2';
    ctx.lineWidth = 3;
    ctx.arc(x, y, saw.r, 0, Math.PI * 2);
    ctx.stroke();

    ctx.beginPath();
    ctx.moveTo(x - saw.r, y);
    ctx.lineTo(x + saw.r, y);
    ctx.moveTo(x, y - saw.r);
    ctx.lineTo(x, y + saw.r);
    ctx.stroke();
  }
}

function drawFish() {
  for (const item of fish) {
    if (item.collected) continue;
    const x = item.x - cameraX;
    ctx.fillStyle = '#f4f4f4';
    ctx.beginPath();
    ctx.moveTo(x, item.y);
    ctx.lineTo(x + 15, item.y - 7);
    ctx.lineTo(x + 18, item.y);
    ctx.lineTo(x + 15, item.y + 7);
    ctx.closePath();
    ctx.fill();
    ctx.fillRect(x + 18, item.y - 2, 6, 4);
    ctx.beginPath();
    ctx.moveTo(x + 18, item.y);
    ctx.lineTo(x + 24, item.y - 5);
    ctx.lineTo(x + 24, item.y + 5);
    ctx.closePath();
    ctx.fill();
    ctx.fillStyle = '#050505';
    ctx.fillRect(x + 8, item.y - 1, 2, 2);
  }
}

function drawDoor() {
  const screenX = door.x - cameraX;
  const doorClosed = fish.filter((item) => item.collected).length < 5;
  ctx.strokeStyle = '#f4f4f4';
  ctx.lineWidth = 3;
  ctx.strokeRect(screenX, door.y, door.w, door.h);
  ctx.fillStyle = doorClosed ? '#111111' : '#f4f4f4';
  ctx.fillRect(screenX + 8, door.y + 8, door.w - 16, door.h - 16);
  ctx.fillStyle = doorClosed ? '#f4f4f4' : '#111111';
  ctx.fillRect(screenX + 12, door.y + 12, 8, 8);
}

function drawPlayer() {
  const x = player.x - cameraX;
  const y = player.y;

  if (player.invulnerable > 0 && Math.floor(player.invulnerable / 4) % 2 === 0) {
    return;
  }

  ctx.save();
  if (player.facing === -1) {
    ctx.translate(x + player.w + 5, 0);
    ctx.scale(-1, 1);
  } else {
    ctx.translate(x - 5, 0);
  }
  ctx.translate(0, y - 5);
  ctx.scale(0.38, 0.38);
  const coat = catCoats[selectedCat];

  ctx.lineCap = 'round';
  ctx.lineJoin = 'round';

  // Use the selection-screen silhouette so both views share the same cat design.
  ctx.beginPath();
  ctx.moveTo(31, 54);
  ctx.bezierCurveTo(15, 68, 18, 44, 28, 43);
  ctx.moveTo(34, 51);
  ctx.bezierCurveTo(34, 37, 38, 31, 47, 28);
  ctx.lineTo(45, 11);
  ctx.lineTo(62, 23);
  ctx.bezierCurveTo(66, 22, 71, 22, 75, 23);
  ctx.lineTo(92, 11);
  ctx.lineTo(90, 30);
  ctx.bezierCurveTo(97, 35, 100, 42, 100, 51);
  ctx.lineTo(100, 64);
  ctx.lineTo(35, 64);
  ctx.closePath();
  ctx.fillStyle = '#050505';
  ctx.strokeStyle = '#f3f3f3';
  ctx.lineWidth = 2;
  ctx.fill();
  ctx.stroke();

  ctx.beginPath();
  ctx.moveTo(35, 52);
  ctx.bezierCurveTo(35, 39, 40, 32, 49, 30);
  ctx.lineTo(48, 18);
  ctx.lineTo(60, 27);
  ctx.bezierCurveTo(65, 26, 69, 26, 74, 27);
  ctx.lineTo(86, 18);
  ctx.lineTo(85, 32);
  ctx.bezierCurveTo(91, 36, 94, 43, 94, 51);
  ctx.lineTo(94, 63);
  ctx.lineTo(35, 63);
  ctx.closePath();
  ctx.fillStyle = coat.fur;
  ctx.fill();

  ctx.fillStyle = coat.innerEar;
  ctx.beginPath();
  ctx.moveTo(46, 20);
  ctx.lineTo(45, 19);
  ctx.lineTo(50, 23);
  ctx.lineTo(48, 23);
  ctx.closePath();
  ctx.fill();
  ctx.beginPath();
  ctx.moveTo(83, 23);
  ctx.lineTo(87, 19);
  ctx.lineTo(86, 24);
  ctx.closePath();
  ctx.fill();

  if (coat.stripes) {
    ctx.strokeStyle = '#303030';
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(51, 32);
    ctx.lineTo(56, 39);
    ctx.moveTo(69, 32);
    ctx.lineTo(64, 39);
    ctx.moveTo(39, 54);
    ctx.lineTo(48, 56);
    ctx.moveTo(84, 54);
    ctx.lineTo(93, 52);
    ctx.moveTo(53, 59);
    ctx.lineTo(58, 55);
    ctx.moveTo(71, 59);
    ctx.lineTo(66, 55);
    ctx.stroke();
  }

  ctx.fillStyle = '#050505';
  ctx.fillRect(48, 42, 4, 6);
  ctx.fillRect(68, 42, 4, 6);
  ctx.beginPath();
  ctx.moveTo(58, 51);
  ctx.lineTo(64, 51);
  ctx.lineTo(61, 54);
  ctx.closePath();
  ctx.fill();
  ctx.fillRect(47, 53, 5, 1);
  ctx.fillRect(42, 55, 8, 1);
  ctx.fillRect(69, 53, 6, 1);
  ctx.fillRect(70, 55, 8, 1);

  ctx.restore();
}

function drawParticles() {
  for (const particle of particles) {
    ctx.fillStyle = '#f3f3f3';
    ctx.fillRect(particle.x - cameraX, particle.y, particle.size, particle.size);
  }
}

function drawGoalText() {
  const collected = fish.filter((item) => item.collected).length;
  ctx.fillStyle = '#f4f4f4';
  ctx.font = '16px "Segoe UI", sans-serif';
  ctx.fillText(`fish: ${collected}/5`, 20, 34);

  if (collected < 5) {
    ctx.fillStyle = '#a4a4a4';
    ctx.fillText('door locked', door.x - cameraX - 12, 370);
  } else {
    ctx.fillStyle = '#f4f4f4';
    ctx.fillText('door open', door.x - cameraX - 12, 370);
  }
}

function update() {
  if (!gameStarted) return;
  if (hasWon) return;
  updatePlayer();
  updateSaws();
  checkSpikesAndSaws();
  checkWin();
  updateParticles();
  renderAchievements();

  const targetCamera = Math.max(0, Math.min(player.x - canvas.width * 0.42, world.width - canvas.width));
  cameraX += (targetCamera - cameraX) * 0.12;
}

function draw() {
  drawBackground();
  drawPlatforms();
  drawSpikes();
  drawDoor();
  drawFish();
  drawSaws();
  drawPlayer();
  drawParticles();
  drawGoalText();
}

function gameLoop() {
  update();
  draw();
  requestAnimationFrame(gameLoop);
}

window.addEventListener('keydown', (event) => {
  const key = event.key.toLowerCase();
  if ([' ', 'arrowup', 'arrowdown', 'arrowleft', 'arrowright'].includes(key) || event.code === 'Space') {
    event.preventDefault();
  }

  keys[key] = true;

  if (key === 'arrowup' || key === 'w' || event.code === 'Space') {
    jumpQueued = true;
  }
});

window.addEventListener('keyup', (event) => {
  const key = event.key.toLowerCase();
  keys[key] = false;
  if (key === ' ') keys['space'] = false;
});

for (const button of catOptionButtons) {
  button.addEventListener('click', () => selectCat(button.dataset.cat));
}
startGameButton.addEventListener('click', startGame);

resetPlayer();
renderAchievements();
requestAnimationFrame(gameLoop);
