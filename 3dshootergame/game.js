import * as THREE from 'three';

// Game manager: owns level state, enemies, HUD, and restart flow.
const gameRoot = document.querySelector('#game');
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x98a0a1);
scene.fog = new THREE.Fog(0x98a0a1, 34, 75);
const camera = new THREE.PerspectiveCamera(76, innerWidth / innerHeight, 0.1, 100);
camera.rotation.order = 'YXZ';
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setPixelRatio(Math.min(devicePixelRatio, 1.75));
renderer.setSize(innerWidth, innerHeight);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.outputColorSpace = THREE.SRGBColorSpace;
gameRoot.prepend(renderer.domElement);

scene.add(new THREE.HemisphereLight(0xdce5e0, 0x343b3e, 2.15));
const sun = new THREE.DirectionalLight(0xffe9c7, 2.1);
sun.position.set(-9, 18, 11);
sun.castShadow = true;
sun.shadow.mapSize.set(1024, 1024);
sun.shadow.camera.left = sun.shadow.camera.bottom = -25;
sun.shadow.camera.right = sun.shadow.camera.top = 25;
scene.add(sun);

const materials = {
  floor: new THREE.MeshStandardMaterial({ color: 0x555b5d, roughness: 1 }),
  wall: new THREE.MeshStandardMaterial({ color: 0x788083, roughness: 1 }),
  cover: new THREE.MeshStandardMaterial({ color: 0x62696a, roughness: 1 }),
  red: new THREE.MeshStandardMaterial({ color: 0xc52f32, roughness: 0.78 }),
};
const obstacles = [];
const enemies = [];
const floor = new THREE.Mesh(new THREE.PlaneGeometry(40, 40), materials.floor);
floor.rotation.x = -Math.PI / 2;
floor.receiveShadow = true;
scene.add(floor);

function addBox(name, size, position, material, solid = true) {
  const mesh = new THREE.Mesh(new THREE.BoxGeometry(...size), material);
  mesh.name = name;
  mesh.position.set(...position);
  mesh.castShadow = true;
  mesh.receiveShadow = true;
  scene.add(mesh);
  if (solid) obstacles.push({ x: position[0], z: position[2], hx: size[0] / 2, hz: size[2] / 2 });
  return mesh;
}
addBox('North wall', [40, 6, 1], [0, 3, -20], materials.wall);
addBox('South wall', [40, 6, 1], [0, 3, 20], materials.wall);
addBox('West wall', [1, 6, 40], [-20, 3, 0], materials.wall);
addBox('East wall', [1, 6, 40], [20, 3, 0], materials.wall);
addBox('Cover box', [3, 2, 2], [-8, 1, -5], materials.cover);
addBox('Cover block', [4, 2.5, 1.5], [1, 1.25, 8], materials.cover);
const pillar = new THREE.Mesh(new THREE.CylinderGeometry(1.25, 1.25, 3, 12), materials.cover);
pillar.position.set(7, 1.5, -4);
pillar.castShadow = pillar.receiveShadow = true;
scene.add(pillar);
obstacles.push({ x: 7, z: -4, hx: 1.35, hz: 1.35 });

// Player controller: first-person look, movement, gravity, collision, and firing.
const player = { x: 0, z: 15, eye: 1.7, vy: 0, hp: 100, yaw: 0, pitch: 0, grounded: true, active: false };
const keys = new Set();
const playerRadius = 0.38;
const collidesAt = (x, z, radius = playerRadius) => obstacles.some(o =>
  x + radius > o.x - o.hx && x - radius < o.x + o.hx && z + radius > o.z - o.hz && z - radius < o.z + o.hz);
function damagePlayer(amount) {
  if (!player.active) return;
  player.hp = Math.max(0, player.hp - amount);
  document.querySelector('#health-value').textContent = String(Math.ceil(player.hp));
  document.querySelector('#health-fill').style.width = `${player.hp}%`;
  if (player.hp <= 30) document.querySelector('#health-fill').style.background = '#ff5b4f';
  if (player.hp <= 0) finish(false);
}
function setPlayerCamera() {
  camera.position.set(player.x, player.eye, player.z);
  camera.rotation.set(player.pitch, player.yaw, 0, 'YXZ');
}

function makeEnemy(x, z, index) {
  const root = new THREE.Group();
  root.position.set(x, 0, z);
  const body = new THREE.Mesh(new THREE.CapsuleGeometry(0.45, 0.9, 4, 8), materials.red);
  body.position.y = 0.9;
  body.castShadow = true;
  body.userData.enemy = root;
  root.add(body);
  const eyeMat = new THREE.MeshBasicMaterial({ color: 0xffd4c7 });
  for (const side of [-1, 1]) {
    const eye = new THREE.Mesh(new THREE.SphereGeometry(0.045, 8, 6), eyeMat);
    eye.position.set(side * 0.16, 1.15, -0.39);
    root.add(eye);
  }
  root.userData = { hp: 100, speed: 2.15 + (index % 2) * 0.3, attackTimer: 0, idleSeed: index * 1.7 };
  root.userData.takeDamage = amount => {
    root.userData.hp = Math.max(0, root.userData.hp - amount);
    console.log(`Enemy ${index + 1} hit for ${amount}; ${root.userData.hp} HP remaining`);
    body.material = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.7 });
    setTimeout(() => { if (body.parent) body.material = materials.red; }, 80);
    showHitMarker();
    if (root.userData.hp <= 0) {
      scene.remove(root);
      enemies.splice(enemies.indexOf(root), 1);
      updateEnemyCount();
      if (enemies.length === 0) finish(true);
    }
  };
  scene.add(root);
  enemies.push(root);
}

function updateEnemyCount() { document.querySelector('#enemy-count').textContent = String(enemies.length); }
function showHitMarker() {
  const marker = document.querySelector('#hit-marker');
  marker.classList.remove('show');
  void marker.offsetWidth;
  marker.classList.add('show');
}

function makeTracer(start, end, hit) {
  const line = new THREE.Line(new THREE.BufferGeometry().setFromPoints([start, end]), new THREE.LineBasicMaterial({ color: hit ? 0xffe47a : 0xffc95c, transparent: true, opacity: 0.95 }));
  scene.add(line);
  setTimeout(() => { scene.remove(line); line.geometry.dispose(); line.material.dispose(); }, 75);
}
const raycaster = new THREE.Raycaster();
function fire() {
  if (!player.active) return;
  const weapon = document.querySelector('#weapon');
  weapon.classList.remove('firing');
  void weapon.offsetWidth;
  weapon.classList.add('firing');
  setTimeout(() => weapon.classList.remove('firing'), 75);
  raycaster.setFromCamera(new THREE.Vector2(0, 0), camera);
  raycaster.far = 100;
  const hits = raycaster.intersectObjects(scene.children, true).filter(hit => hit.object !== floor);
  const hit = hits[0];
  const start = camera.position.clone();
  const end = hit ? hit.point : start.clone().add(raycaster.ray.direction.clone().multiplyScalar(100));
  makeTracer(start, end, Boolean(hit));
  if (hit) {
    const enemy = hit.object.userData.enemy;
    console.log(`Hitscan hit: ${enemy ? 'enemy' : hit.object.name || 'arena object'}`, hit.point);
    if (enemy?.userData.takeDamage) enemy.userData.takeDamage(25);
  } else console.log('Hitscan miss');
}

const stateScreen = document.querySelector('#start-screen');
const endScreen = document.querySelector('#end-screen');
const toast = document.querySelector('#toast');
let toastTimer;
function showToast(message) {
  toast.textContent = message;
  toast.style.opacity = '1';
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { toast.style.opacity = '0'; }, 1700);
}
function finish(won) {
  if (!player.active) return;
  player.active = false;
  document.exitPointerLock?.();
  document.querySelector('#end-title').textContent = won ? 'VICTORY' : 'GAME OVER';
  document.querySelector('#end-copy').textContent = won ? 'All hostiles eliminated.' : 'You were overwhelmed.';
  endScreen.classList.remove('hidden');
}
function resetGame() {
  for (const enemy of [...enemies]) scene.remove(enemy);
  enemies.length = 0;
  makeEnemy(-12, -12, 0);
  makeEnemy(12, -10, 1);
  makeEnemy(9, 12, 2);
  player.x = 0; player.z = 15; player.eye = 1.7; player.vy = 0; player.hp = 100; player.pitch = 0; player.yaw = 0; player.grounded = true;
  document.querySelector('#health-value').textContent = '100';
  document.querySelector('#health-fill').style.width = '100%';
  document.querySelector('#health-fill').style.background = 'var(--acid)';
  updateEnemyCount();
  setPlayerCamera();
  endScreen.classList.add('hidden');
  stateScreen.classList.add('hidden');
  player.active = true;
  renderer.domElement.requestPointerLock?.();
}

document.querySelector('#start-button').addEventListener('click', resetGame);
document.querySelector('#restart-button').addEventListener('click', resetGame);
document.addEventListener('pointerlockchange', () => {
  if (document.pointerLockElement === renderer.domElement) { player.active = true; stateScreen.classList.add('hidden'); }
  else if (player.active && endScreen.classList.contains('hidden')) { player.active = false; stateScreen.classList.remove('hidden'); }
});
document.addEventListener('mousemove', event => {
  if (!player.active || document.pointerLockElement !== renderer.domElement) return;
  player.yaw -= event.movementX * 0.0022;
  player.pitch = THREE.MathUtils.clamp(player.pitch - event.movementY * 0.0022, -Math.PI / 2 + 0.04, Math.PI / 2 - 0.04);
});
document.addEventListener('keydown', event => {
  keys.add(event.code);
  if (event.code === 'Space') event.preventDefault();
});
document.addEventListener('keyup', event => keys.delete(event.code));
document.addEventListener('mousedown', event => { if (event.button === 0 && player.active) fire(); });
renderer.domElement.addEventListener('click', () => {
  if (!player.active && endScreen.classList.contains('hidden') && stateScreen.classList.contains('hidden')) renderer.domElement.requestPointerLock?.();
});

function updatePlayer(delta) {
  if (!player.active) return;
  const forward = (keys.has('KeyW') ? 1 : 0) - (keys.has('KeyS') ? 1 : 0);
  const strafe = (keys.has('KeyD') ? 1 : 0) - (keys.has('KeyA') ? 1 : 0);
  const magnitude = Math.hypot(forward, strafe) || 1;
  const speed = 6.0 * delta / magnitude;
  const dx = (Math.sin(player.yaw) * forward + Math.cos(player.yaw) * strafe) * speed;
  const dz = (-Math.cos(player.yaw) * forward + Math.sin(player.yaw) * strafe) * speed;
  if (!collidesAt(player.x + dx, player.z)) player.x += dx;
  if (!collidesAt(player.x, player.z + dz)) player.z += dz;
  if (keys.has('Space') && player.grounded) { player.vy = 5.5; player.grounded = false; }
  player.vy -= 14 * delta;
  player.eye += player.vy * delta;
  if (player.eye <= 1.7) { player.eye = 1.7; player.vy = 0; player.grounded = true; }
  setPlayerCamera();
}

function updateEnemies(delta, elapsed) {
  for (const enemy of [...enemies]) {
    const dx = player.x - enemy.position.x;
    const dz = player.z - enemy.position.z;
    const distance = Math.hypot(dx, dz);
    if (distance > 16 || !player.active) continue;
    if (distance > 1.55) {
      const step = Math.min(enemy.userData.speed * delta, distance - 1.45);
      const nx = enemy.position.x + dx / distance * step;
      const nz = enemy.position.z + dz / distance * step;
      const blocked = obstacles.some(o => nx + 0.48 > o.x-o.hx && nx-0.48 < o.x+o.hx && nz+0.48 > o.z-o.hz && nz-0.48 < o.z+o.hz);
      if (!blocked) enemy.position.set(nx, 0, nz);
      enemy.rotation.y = Math.atan2(dx, dz);
    } else {
      enemy.userData.attackTimer += delta;
      if (enemy.userData.attackTimer >= 1) { enemy.userData.attackTimer -= 1; damagePlayer(10); }
    }
    // Subtle idle motion until the player is detected.
    if (distance > 16) enemy.position.y = Math.sin(elapsed * 1.3 + enemy.userData.idleSeed) * 0.025;
  }
}

let previousTime = performance.now();
function animate(now) {
  requestAnimationFrame(animate);
  const delta = Math.min((now - previousTime) / 1000, 0.05);
  previousTime = now;
  updatePlayer(delta);
  updateEnemies(delta, now / 1000);
  renderer.render(scene, camera);
}
function onResize() {
  camera.aspect = innerWidth / innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(innerWidth, innerHeight);
}
window.addEventListener('resize', onResize);
resetGame();
player.active = false;
stateScreen.classList.remove('hidden');
requestAnimationFrame(animate);
