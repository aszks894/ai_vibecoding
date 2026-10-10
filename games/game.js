const canvas = document.getElementById('game');
const ctx = canvas.getContext('2d');
const fishCountEl = document.getElementById('fishCount');
const levelLabelEl = document.getElementById('levelLabel');
const levelTimerEl = document.getElementById('levelTimer');
const achievementCountEl = document.getElementById('achievementCount');
const catSelectEl = document.getElementById('catSelect');
const startGameButton = document.getElementById('startGame');
const catOptionButtons = [...document.querySelectorAll('.cat-option')];
const musicFileInput = document.getElementById('musicFile');
const musicAudio = document.getElementById('musicAudio');
const musicStatus = document.getElementById('musicStatus');
const chiptuneToggle = document.getElementById('chiptuneToggle');
const chiptuneStatus = document.getElementById('chiptuneStatus');
const musicVolume = document.getElementById('musicVolume');
let musicObjectUrl = null;
let audioContext = null;
let musicGain = null;
let chiptuneTimer = null;
let chiptunePlaying = false;
let nextNoteTime = 0;
let stepIndex = 0;

const beatSeconds = 60 / 156;
const notePattern = [
  72, null, 75, 79, null, 75, 72, 70,
  67, null, 70, 75, null, 70, 67, 63,
  72, null, 75, 82, null, 79, 75, 72,
  70, null, 75, 79, 75, 70, 67, null
];
const bassPattern = [
  36, null, null, 36, 36, null, 39, null,
  32, null, 32, null, 32, null, 36, null,
  36, null, null, 36, 36, null, 39, null,
  34, null, 34, null, 34, null, 31, null
];
let noiseBuffer = null;

const achievementIds = ['fish-fan', 'clean-paws', 'speed-paws', 'nine-lives'];
const achievementCards = new Map(
  achievementIds.map((id) => [id, document.querySelector(`[data-achievement="${id}"]`)])
);
const achievementStorageKey = 'cat-platformer-achievements';
const unlockedAchievements = loadAchievements();
let gameStartedAt = 0;
let levelStartedAt = 0;
let gameStarted = false;
let knockouts = 0;
let selectedCat = 'white';
let levelIndex = 0;
let totalFishCollected = 0;
const speedLevelsCompleted = new Set();
let levelNoticeTimeout = null;

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

let platforms = [
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

let spikes = [
  { x: 380, y: 482, w: 70, h: 18 },
  { x: 1100, y: 482, w: 80, h: 18 },
  { x: 1560, y: 482, w: 120, h: 18 }
];

let saws = [
  { x: 770, y: 300, r: 16, minX: 700, maxX: 870, speed: 1.7, dir: 1 },
  { x: 1760, y: 240, r: 14, minX: 1710, maxX: 1828, speed: 1.5, dir: 1 }
];

let fish = [
  { x: 160, y: 454, collected: false },
  { x: 560, y: 384, collected: false },
  { x: 740, y: 304, collected: false },
  { x: 1240, y: 264, collected: false },
  { x: 1760, y: 234, collected: false }
];

let door = {
  x: 2010,
  y: 420,
  w: 32,
  h: 80
};

const particles = [];
let hasWon = false;
const firstLevel = {
  width: world.width,
  platforms,
  spikes,
  saws,
  fish,
  door: { ...door },
  start: { x: 84, y: 360 }
};
const nextLevels = [
  {
    name: 'SKYLINE SPRINT',
    width: 2200,
    platforms: [
      { x: 0, y: 500, w: 350, h: 40 }, { x: 390, y: 440, w: 180, h: 20 },
      { x: 610, y: 370, w: 190, h: 20 }, { x: 840, y: 430, w: 190, h: 20 },
      { x: 1070, y: 350, w: 190, h: 20 }, { x: 1300, y: 280, w: 170, h: 20 },
      { x: 1510, y: 360, w: 190, h: 20 }, { x: 1740, y: 290, w: 180, h: 20 },
      { x: 1960, y: 460, w: 240, h: 40 }, { x: 900, y: 300, w: 65, h: 12 },
      { x: 1600, y: 230, w: 70, h: 12 }
    ],
    spikes: [
      { x: 310, y: 482, w: 60, h: 18 }, { x: 1020, y: 412, w: 48, h: 18 },
      { x: 1685, y: 342, w: 45, h: 18 }
    ],
    saws: [
      { x: 700, y: 330, r: 15, minX: 630, maxX: 785, speed: 2, dir: 1 },
      { x: 1810, y: 250, r: 16, minX: 1750, maxX: 1900, speed: 2.1, dir: -1 }
    ],
    fish: [
      { x: 170, y: 455 }, { x: 485, y: 405 }, { x: 1130, y: 315 },
      { x: 1360, y: 245 }, { x: 1790, y: 255 }
    ],
    door: { x: 2155, y: 380, w: 32, h: 80 },
    start: { x: 70, y: 460 }
  },
  {
    name: 'NEON FOUNDRY',
    width: 2300,
    platforms: [
      { x: 0, y: 500, w: 300, h: 40 }, { x: 350, y: 435, w: 165, h: 20 },
      { x: 565, y: 365, w: 165, h: 20 }, { x: 780, y: 300, w: 170, h: 20 },
      { x: 1000, y: 370, w: 170, h: 20 }, { x: 1220, y: 295, w: 170, h: 20 },
      { x: 1440, y: 355, w: 170, h: 20 }, { x: 1660, y: 275, w: 170, h: 20 },
      { x: 1880, y: 350, w: 160, h: 20 }, { x: 2090, y: 460, w: 210, h: 40 },
      { x: 1080, y: 245, w: 65, h: 12 }, { x: 1750, y: 215, w: 65, h: 12 }
    ],
    spikes: [
      { x: 290, y: 482, w: 55, h: 18 }, { x: 730, y: 482, w: 45, h: 18 },
      { x: 1170, y: 482, w: 50, h: 18 }, { x: 1608, y: 482, w: 48, h: 18 },
      { x: 1830, y: 482, w: 55, h: 18 }
    ],
    saws: [
      { x: 645, y: 325, r: 16, minX: 580, maxX: 715, speed: 2.3, dir: 1 },
      { x: 1300, y: 255, r: 15, minX: 1230, maxX: 1380, speed: 2.5, dir: -1 },
      { x: 1735, y: 235, r: 16, minX: 1670, maxX: 1810, speed: 2.4, dir: 1 }
    ],
    fish: [
      { x: 145, y: 455 }, { x: 600, y: 335 }, { x: 840, y: 270 },
      { x: 1260, y: 265 }, { x: 1710, y: 245 }
    ],
    door: { x: 2250, y: 380, w: 32, h: 80 },
    start: { x: 65, y: 460 }
  }
];

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
  const secondsLeft = gameStarted
    ? Math.max(0, Math.ceil(45 - (performance.now() - levelStartedAt) / 1000))
    : 45;
  const progress = {
    'fish-fan': `${totalFishCollected} / 15`,
    'clean-paws': `${knockouts} knockouts`,
    'speed-paws': `${speedLevelsCompleted.size} / 3 stages`,
    'nine-lives': `${Math.min(knockouts, 3)} / 3`
  };

  levelTimerEl.textContent = secondsLeft > 0 ? `${secondsLeft}s` : 'TIME UP';
  levelTimerEl.classList.toggle('timer-expired', secondsLeft === 0);
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
  if (knockouts === 0) unlockAchievement('clean-paws');
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
  levelStartedAt = gameStartedAt;
  catSelectEl.hidden = true;
  renderAchievements();
}

function midiFrequency(note) {
  return 440 * Math.pow(2, (note - 69) / 12);
}

function playSynthNote(frequency, startTime, duration, type, peakGain) {
  const oscillator = audioContext.createOscillator();
  const envelope = audioContext.createGain();
  const filter = audioContext.createBiquadFilter();
  oscillator.type = type;
  oscillator.frequency.setValueAtTime(frequency, startTime);
  envelope.gain.setValueAtTime(0.0001, startTime);
  envelope.gain.exponentialRampToValueAtTime(peakGain, startTime + 0.008);
  envelope.gain.exponentialRampToValueAtTime(0.0001, startTime + duration + 0.025);
  filter.type = 'lowpass';
  filter.frequency.setValueAtTime(type === 'sawtooth' ? 1800 : 2800, startTime);
  oscillator.connect(envelope);
  envelope.connect(filter);
  filter.connect(musicGain);
  oscillator.start(startTime);
  oscillator.stop(startTime + duration + 0.02);
}

function playKick(startTime) {
  const oscillator = audioContext.createOscillator();
  const envelope = audioContext.createGain();
  oscillator.type = 'sine';
  oscillator.frequency.setValueAtTime(145, startTime);
  oscillator.frequency.exponentialRampToValueAtTime(43, startTime + 0.16);
  envelope.gain.setValueAtTime(0.2, startTime);
  envelope.gain.exponentialRampToValueAtTime(0.0001, startTime + 0.19);
  oscillator.connect(envelope);
  envelope.connect(musicGain);
  oscillator.start(startTime);
  oscillator.stop(startTime + 0.2);
}

function playNoiseHit(startTime, duration, peakGain, cutoff, resonance = 0.7) {
  if (!noiseBuffer) {
    const bufferSize = audioContext.sampleRate;
    noiseBuffer = audioContext.createBuffer(1, bufferSize, audioContext.sampleRate);
    const data = noiseBuffer.getChannelData(0);
    for (let i = 0; i < bufferSize; i += 1) {
      data[i] = Math.random() * 2 - 1;
    }
  }

  const source = audioContext.createBufferSource();
  const filter = audioContext.createBiquadFilter();
  const envelope = audioContext.createGain();
  source.buffer = noiseBuffer;
  filter.type = 'highpass';
  filter.frequency.setValueAtTime(cutoff, startTime);
  filter.Q.value = resonance;
  envelope.gain.setValueAtTime(peakGain, startTime);
  envelope.gain.exponentialRampToValueAtTime(0.0001, startTime + duration);
  source.connect(filter);
  filter.connect(envelope);
  envelope.connect(musicGain);
  source.start(startTime);
  source.stop(startTime + duration);
}

function scheduleChiptuneStep(startTime, step) {
  const note = notePattern[step];
  if (note !== null) {
    playSynthNote(midiFrequency(note), startTime, beatSeconds * 0.34, 'square', 0.038);
    if (step % 4 === 2) {
      playSynthNote(midiFrequency(note - 12), startTime, beatSeconds * 0.28, 'sawtooth', 0.022);
    }
  }

  const bassNote = bassPattern[step];
  if (bassNote !== null) {
    playSynthNote(midiFrequency(bassNote), startTime, beatSeconds * 0.72, 'sawtooth', 0.085);
  }

  if (step % 4 === 0) playKick(startTime);
  if (step % 8 === 4) playNoiseHit(startTime, 0.11, 0.045, 900, 0.8);
  if (step % 2 === 1) playNoiseHit(startTime, 0.035, 0.012, 6500, 0.5);
}

function scheduleChiptune() {
  while (nextNoteTime < audioContext.currentTime + 0.12) {
    scheduleChiptuneStep(nextNoteTime, stepIndex);
    nextNoteTime += beatSeconds / 2;
    stepIndex = (stepIndex + 1) % notePattern.length;
  }
}

async function toggleChiptune() {
  if (chiptunePlaying) {
    chiptunePlaying = false;
    window.clearInterval(chiptuneTimer);
    chiptuneTimer = null;
    musicGain.gain.setTargetAtTime(0, audioContext.currentTime, 0.06);
    chiptuneToggle.textContent = 'PLAY CHIPTUNE';
    chiptuneToggle.setAttribute('aria-pressed', 'false');
    chiptuneStatus.textContent = 'PAUSED';
    return;
  }

  try {
    const AudioContextType = window.AudioContext || window.webkitAudioContext;
    if (!AudioContextType) throw new Error('Web Audio API is unavailable in this browser.');
    if (!audioContext) {
      audioContext = new AudioContextType();
      musicGain = audioContext.createGain();
      musicGain.gain.value = Number(musicVolume.value) / 100;
      musicGain.connect(audioContext.destination);
    }
    await audioContext.resume();
    chiptunePlaying = true;
    stepIndex = 0;
    nextNoteTime = audioContext.currentTime + 0.05;
    musicGain.gain.setTargetAtTime(Number(musicVolume.value) / 100, audioContext.currentTime, 0.04);
    scheduleChiptune();
    chiptuneTimer = window.setInterval(scheduleChiptune, 25);
    chiptuneToggle.textContent = 'STOP CHIPTUNE';
    chiptuneToggle.setAttribute('aria-pressed', 'true');
    chiptuneStatus.textContent = 'PLAYING: 156 BPM ARCADE RUN';
  } catch (error) {
    console.error('Could not start the chiptune:', error);
    chiptuneStatus.textContent = 'AUDIO UNAVAILABLE: TRY A MODERN BROWSER';
  }
}

function resetPlayer() {
  const start = levelIndex === 0 ? firstLevel.start : nextLevels[levelIndex - 1].start;
  player.x = start.x;
  player.y = start.y;
  player.vx = 0;
  player.vy = 0;
  player.onGround = false;
  player.invulnerable = 60;
}

function loadLevel(index) {
  levelIndex = index;
  hasWon = false;
  cameraX = 0;
  particles.length = 0;
  fishCountEl.textContent = '0';

  if (index > 0) {
    const level = nextLevels[index - 1];
    world.width = level.width;
    platforms = level.platforms;
    spikes = level.spikes;
    saws = level.saws.map((saw) => ({ ...saw }));
    fish = level.fish.map((item) => ({ ...item, collected: false }));
    door = level.door;
    levelLabelEl.textContent = `LEVEL ${index + 1} / 3 - ${level.name}`;
  } else {
    world.width = firstLevel.width;
    platforms = firstLevel.platforms;
    spikes = firstLevel.spikes;
    saws = firstLevel.saws.map((saw) => ({ ...saw }));
    fish = firstLevel.fish.map((item) => ({ ...item, collected: false }));
    door = { ...firstLevel.door };
    levelLabelEl.textContent = 'LEVEL 1 / 3 - MOONLIT ROOFTOPS';
  }

  resetPlayer();
  levelStartedAt = performance.now();
  renderAchievements();
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
  const levelData = levelIndex === 0 ? firstLevel : nextLevels[levelIndex - 1];
  saws = levelData.saws.map((saw) => ({ ...saw }));
  cameraX = 0;
  levelStartedAt = performance.now();
  if (levelNoticeTimeout !== null) window.clearTimeout(levelNoticeTimeout);
  levelLabelEl.textContent = `KNOCKOUT ${knockouts} - RESTARTING LEVEL ${levelIndex + 1}`;
  levelNoticeTimeout = window.setTimeout(() => {
    const currentLevel = levelIndex === 0 ? 'MOONLIT ROOFTOPS' : nextLevels[levelIndex - 1].name;
    levelLabelEl.textContent = `LEVEL ${levelIndex + 1} / 3 - ${currentLevel}`;
    levelNoticeTimeout = null;
  }, 1100);
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
        totalFishCollected += 1;
        for (let i = 0; i < 16; i += 1) spawnSpark(item.x, item.y);
      }
    }
    if (item.collected) collected += 1;
  });
  fishCountEl.textContent = String(collected);
  if (totalFishCollected === 15) unlockAchievement('fish-fan');
  return collected;
}

function checkSpikesAndSaws() {
  if (player.invulnerable > 0) return;

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

function showWinScreen(hasNextLevel) {
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
  const title = document.createElement('div');
  title.className = 'win-title';
  title.textContent = hasNextLevel ? 'LEVEL CLEAR' : 'YOU WIN';
  const subtitle = document.createElement('div');
  subtitle.className = 'win-subtitle';
  subtitle.textContent = hasNextLevel ? 'GET READY FOR THE NEXT STAGE' : 'ALL THREE LEVELS CLEARED';
  panel.appendChild(title);
  panel.appendChild(subtitle);

  overlay.appendChild(flash);
  overlay.appendChild(confettiLayer);
  overlay.appendChild(panel);
  document.body.appendChild(overlay);

  if (hasNextLevel) {
    window.setTimeout(() => {
      if (document.body.contains(overlay)) document.body.removeChild(overlay);
      loadLevel(levelIndex + 1);
    }, 1800);
    return;
  }

  const replayButton = document.createElement('button');
  replayButton.className = 'start-button replay-button';
  replayButton.type = 'button';
  replayButton.textContent = 'PLAY AGAIN';
  replayButton.addEventListener('click', () => {
    totalFishCollected = 0;
    knockouts = 0;
    speedLevelsCompleted.clear();
    gameStartedAt = performance.now();
    loadLevel(0);
    overlay.remove();
  });
  panel.appendChild(replayButton);
}

function checkWin() {
  if (hasWon) return true;

  const collected = checkCollectibles();
  if (collected === fish.length) {
    const doorRect = { x: door.x, y: door.y, w: door.w, h: door.h };
    if (rectsOverlap(playerRect(), doorRect)) {
      hasWon = true;
      player.vx = 0;
      player.vy = 0;
      const hasNextLevel = levelIndex < 2;
      if ((performance.now() - levelStartedAt) / 1000 < 45) {
        speedLevelsCompleted.add(levelIndex);
        if (speedLevelsCompleted.size === 3) unlockAchievement('speed-paws');
      }
      renderAchievements();
      if (!hasNextLevel) checkFinishAchievements();
      showWinScreen(hasNextLevel);
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
  if (player.invulnerable > 0) player.invulnerable -= 1;
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

chiptuneToggle.addEventListener('click', toggleChiptune);
musicVolume.addEventListener('input', () => {
  if (musicGain && chiptunePlaying) {
    musicGain.gain.setTargetAtTime(Number(musicVolume.value) / 100, audioContext.currentTime, 0.03);
  }
  musicAudio.volume = Number(musicVolume.value) / 100;
});

musicFileInput.addEventListener('change', () => {
  const [file] = musicFileInput.files;
  if (!file) return;

  if (musicObjectUrl) URL.revokeObjectURL(musicObjectUrl);
  musicObjectUrl = URL.createObjectURL(file);
  musicAudio.src = musicObjectUrl;
  musicAudio.hidden = false;
  musicAudio.load();
  musicAudio.volume = Number(musicVolume.value) / 100;
  musicStatus.textContent = `READY: ${file.name} - PRESS PLAY`;
});

musicAudio.addEventListener('error', () => {
  musicStatus.textContent = 'Could not play this audio file. Try another supported format.';
});

musicAudio.addEventListener('play', () => {
  musicStatus.textContent = 'PLAYING';
});

musicAudio.addEventListener('pause', () => {
  if (musicAudio.currentSrc && !musicAudio.ended) musicStatus.textContent = 'PAUSED';
});

resetPlayer();
renderAchievements();
requestAnimationFrame(gameLoop);
