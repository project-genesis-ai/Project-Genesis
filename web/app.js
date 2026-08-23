import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.179.1/build/three.module.js';
import { OrbitControls } from 'https://cdn.jsdelivr.net/npm/three@0.179.1/examples/jsm/controls/OrbitControls.js';
import { mergeGeometries } from 'https://cdn.jsdelivr.net/npm/three@0.179.1/examples/jsm/utils/BufferGeometryUtils.js';

const API_BASE = (window.GENESIS_API_BASE || window.location.origin).replace(/\/$/, '');
const canvas = document.querySelector('#genesis-canvas');
const statusEl = document.querySelector('#status');
const metricsEl = document.querySelector('#metrics');
const inspectorEl = document.querySelector('#inspector');
const playButton = document.querySelector('#play');
const speedEl = document.querySelector('#speed');
const saveButton = document.querySelector('#save');

const RADIUS = 50;
const MAX_PIXEL_RATIO = 1.6;
const AXIAL_TILT = THREE.MathUtils.degToRad(23.4);
const UP = new THREE.Vector3(0, 1, 0);
const clock = new THREE.Clock();

const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, powerPreference: 'high-performance' });
renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, MAX_PIXEL_RATIO));
renderer.setSize(window.innerWidth, window.innerHeight, false);
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.05;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x01040b);
const camera = new THREE.PerspectiveCamera(38, window.innerWidth / window.innerHeight, 0.05, 4000);
camera.position.set(0, RADIUS * 0.22, RADIUS * 2.55);
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.055;
controls.minDistance = RADIUS * 1.03;
controls.maxDistance = RADIUS * 7;
controls.enablePan = false;
controls.target.set(0, 0, 0);

scene.add(new THREE.HemisphereLight(0xbcd8ff, 0x162116, 1.25));
const sun = new THREE.DirectionalLight(0xfff3d6, 3.4);
sun.position.set(160, 100, 90);
sun.castShadow = true;
sun.shadow.mapSize.set(1024, 1024);
scene.add(sun);
scene.add(new THREE.DirectionalLight(0x6baeff, 0.45));

const globe = new THREE.Group();
globe.rotation.z = AXIAL_TILT;
scene.add(globe);

const raycaster = new THREE.Raycaster();
const pointer = new THREE.Vector2();
let state = null;
let mapper = null;
let playing = false;
let stepping = false;
let lastRenderTick = -1;
let cloudMaterial = null;
let stepAccumulator = 0;

const num = (value, fallback = 0) => {
  const n = Number(value);
  return Number.isFinite(n) ? n : fallback;
};
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
const setStatus = (text) => { statusEl.textContent = text; };

function mulberry32(seed) {
  return () => {
    let t = seed += 0x6D2B79F5;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function hashCell(x, y, seed = 0x9e3779b9) {
  let h = (seed ^ Math.imul(x + 374761393, 668265263) ^ Math.imul(y + 1442695041, 2246822519)) >>> 0;
  h ^= h >>> 13;
  h = Math.imul(h, 1274126177) >>> 0;
  return h >>> 0;
}

function biomeName(cell) {
  return String(cell?.biome?.name || '').toLowerCase();
}

function biomeColor(cell) {
  const name = biomeName(cell);
  const productivity = clamp(num(cell?.biome?.vegetation_productivity), 0, 1);
  if (name.includes('desert')) return [0.72, 0.57, 0.32];
  if (name.includes('tundra') || name.includes('ice') || name.includes('snow')) return [0.84, 0.88, 0.86];
  if (name.includes('forest') || name.includes('wood')) return [0.15, 0.36 + productivity * 0.10, 0.16];
  if (name.includes('savanna')) return [0.52, 0.55, 0.22];
  if (name.includes('grass')) return [0.28, 0.50 + productivity * 0.08, 0.20];
  if (name.includes('wetland')) return [0.16, 0.39, 0.27];
  if (name.includes('mountain')) return [0.42, 0.39, 0.34];
  return [0.30, 0.48, 0.25];
}

function flattenCells(planet) {
  const result = [];
  const rows = Array.isArray(planet?.cells) ? planet.cells : [];
  for (let row = 0; row < rows.length; row += 1) {
    const cells = Array.isArray(rows[row]) ? rows[row] : [];
    for (let col = 0; col < cells.length; col += 1) {
      const cell = cells[col];
      if (cell?.terrain) result.push({ ...cell, x: num(cell.terrain.x, col), y: num(cell.terrain.y, row) });
    }
  }
  return result;
}

function makeMapper(cells) {
  const xs = cells.map((c) => c.x);
  const ys = cells.map((c) => c.y);
  const minX = Math.min(...xs);
  const maxX = Math.max(...xs);
  const minY = Math.min(...ys);
  const maxY = Math.max(...ys);
  const width = Math.max(2, maxX - minX + 1);
  const height = Math.max(2, maxY - minY + 1);
  const cellMap = new Map(cells.map((c) => [`${c.x}:${c.y}`, c]));
  const elevations = cells.filter((c) => c.terrain?.land).map((c) => num(c.terrain.elevation_m));
  const minElevation = elevations.length ? Math.min(...elevations) : 0;
  const maxElevation = elevations.length ? Math.max(...elevations) : 1;
  return { minX, maxX, minY, maxY, width, height, cellMap, minElevation, maxElevation };
}

function spherical(x, y, elevation = 0, lift = 0) {
  const { minX, minY, width, height, minElevation, maxElevation } = mapper;
  const lon = ((x - minX + 0.5) / width) * Math.PI * 2 - Math.PI;
  const lat = Math.PI * 0.5 - ((y - minY + 0.5) / height) * Math.PI;
  const normalizedElevation = clamp((elevation - minElevation) / Math.max(1, maxElevation - minElevation), 0, 1);
  const radius = RADIUS + normalizedElevation * 3.0 + lift;
  const cosLat = Math.cos(lat);
  const normal = new THREE.Vector3(cosLat * Math.cos(lon), Math.sin(lat), cosLat * Math.sin(lon)).normalize();
  return { normal, position: normal.clone().multiplyScalar(radius), lon, lat };
}

function localFrame(normal) {
  let tangent = new THREE.Vector3(0, 1, 0);
  if (Math.abs(normal.dot(tangent)) > 0.92) tangent.set(1, 0, 0);
  tangent.projectOnPlane(normal).normalize();
  return { tangent, bitangent: new THREE.Vector3().crossVectors(normal, tangent).normalize() };
}

function clearGlobe() {
  while (globe.children.length) {
    const child = globe.children.pop();
    child.traverse((node) => {
      node.geometry?.dispose();
      if (Array.isArray(node.material)) node.material.forEach((m) => m.dispose());
      else node.material?.dispose();
      node.material?.map?.dispose();
    });
  }
  cloudMaterial = null;
}

function makeStars() {
  if (scene.getObjectByName('stars')) return;
  const count = 1800;
  const positions = new Float32Array(count * 3);
  const rng = mulberry32(0x91e10da);
  for (let i = 0; i < count; i += 1) {
    const radius = 900 + rng() * 1200;
    const theta = rng() * Math.PI * 2;
    const phi = Math.acos(2 * rng() - 1);
    positions[i * 3] = radius * Math.sin(phi) * Math.cos(theta);
    positions[i * 3 + 1] = radius * Math.cos(phi);
    positions[i * 3 + 2] = radius * Math.sin(phi) * Math.sin(theta);
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  const stars = new THREE.Points(geometry, new THREE.PointsMaterial({ color: 0xbdd9ff, size: 1.15, transparent: true, opacity: 0.7 }));
  stars.name = 'stars';
  scene.add(stars);
}

function makeAtmosphere() {
  const material = new THREE.ShaderMaterial({
    transparent: true,
    depthWrite: false,
    side: THREE.BackSide,
    blending: THREE.AdditiveBlending,
    uniforms: { color: { value: new THREE.Color(0x58a9ff) }, strength: { value: 0.7 } },
    vertexShader: 'varying vec3 vNormal; void main(){vNormal=normalize(normalMatrix*normal);gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);}',
    fragmentShader: 'uniform vec3 color; uniform float strength; varying vec3 vNormal; void main(){float rim=pow(1.0-max(vNormal.z,0.0),2.6);gl_FragColor=vec4(color,rim*strength);}',
  });
  globe.add(new THREE.Mesh(new THREE.SphereGeometry(RADIUS * 1.055, 128, 64), material));
}

function makeOcean() {
  const ocean = new THREE.Mesh(
    new THREE.SphereGeometry(RADIUS, 128, 64),
    new THREE.MeshPhysicalMaterial({ color: 0x07558f, roughness: 0.2, metalness: 0.02, clearcoat: 0.85, clearcoatRoughness: 0.12 })
  );
  ocean.userData = { type: 'ocean' };
  ocean.receiveShadow = true;
  globe.add(ocean);
}

function makeLandTexture(cells) {
  const width = 2048;
  const height = 1024;
  const canvas2d = document.createElement('canvas');
  canvas2d.width = width;
  canvas2d.height = height;
  const ctx = canvas2d.getContext('2d');
  ctx.fillStyle = '#07558f';
  ctx.fillRect(0, 0, width, height);

  for (const cell of cells) {
    if (!cell.terrain?.land) continue;
    const x = ((cell.x - mapper.minX) / mapper.width) * width;
    const y = ((cell.y - mapper.minY) / mapper.height) * height;
    const w = width / mapper.width + 1.5;
    const h = height / mapper.height + 1.5;
    const [r, g, b] = biomeColor(cell);
    const elevation = clamp(num(cell.terrain.elevation_m), mapper.minElevation, mapper.maxElevation);
    const relief = clamp((elevation - mapper.minElevation) / Math.max(1, mapper.maxElevation - mapper.minElevation), 0, 1);
    const shade = 0.84 + relief * 0.26;
    ctx.fillStyle = `rgb(${Math.round(r * 255 * shade)},${Math.round(g * 255 * shade)},${Math.round(b * 255 * shade)})`;
    ctx.fillRect(x, y, w, h);
  }

  const softened = document.createElement('canvas');
  softened.width = width;
  softened.height = height;
  const soft = softened.getContext('2d');
  soft.filter = 'blur(0.7px)';
  soft.drawImage(canvas2d, 0, 0);
  const texture = new THREE.CanvasTexture(softened);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.wrapS = THREE.RepeatWrapping;
  texture.anisotropy = Math.min(8, renderer.capabilities.getMaxAnisotropy());
  return texture;
}

function makeLand(cells) {
  const material = new THREE.MeshStandardMaterial({ map: makeLandTexture(cells), roughness: 0.94, metalness: 0 });
  const land = new THREE.Mesh(new THREE.SphereGeometry(RADIUS * 1.002, 160, 96), material);
  land.castShadow = true;
  land.receiveShadow = true;
  land.userData = { type: 'terrain' };
  globe.add(land);
}

function makeClouds() {
  cloudMaterial = new THREE.ShaderMaterial({
    transparent: true,
    depthWrite: false,
    uniforms: { time: { value: 0 } },
    vertexShader: 'varying vec2 vUv; void main(){vUv=uv;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);}',
    fragmentShader: `uniform float time; varying vec2 vUv; float n(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);} void main(){vec2 p=vUv*7.0; float a=n(floor(p)); float b=n(floor(p+vec2(time*0.025,0.0))); float cloud=smoothstep(0.42,0.72,a*0.72+b*0.28); gl_FragColor=vec4(vec3(0.92,0.96,1.0),cloud*0.16);}`,
  });
  const clouds = new THREE.Mesh(new THREE.SphereGeometry(RADIUS * 1.018, 128, 64), cloudMaterial);
  globe.add(clouds);
}

function makeTreeGeometry() {
  const trunk = new THREE.CylinderGeometry(0.055, 0.09, 0.42, 7);
  trunk.translate(0, 0.21, 0);
  const crown1 = new THREE.SphereGeometry(0.25, 8, 6);
  crown1.scale(1, 1.25, 1);
  crown1.translate(0, 0.48, 0);
  const crown2 = new THREE.SphereGeometry(0.18, 8, 6);
  crown2.translate(0, 0.72, 0);
  const merged = mergeGeometries([trunk, crown1, crown2]);
  trunk.dispose(); crown1.dispose(); crown2.dispose();
  return merged;
}

function addForests(cells) {
  const forest = cells.filter((cell) => {
    const name = biomeName(cell);
    return cell.terrain?.land && (name.includes('forest') || name.includes('wood'));
  });
  if (!forest.length) return;
  const maxInstances = Math.min(7000, forest.length * 3);
  const mesh = new THREE.InstancedMesh(makeTreeGeometry(), new THREE.MeshStandardMaterial({ color: 0x2c6d36, roughness: 0.92 }), maxInstances);
  const matrix = new THREE.Matrix4();
  let index = 0;
  for (const cell of forest) {
    const rng = mulberry32(hashCell(cell.x, cell.y));
    const count = 1 + Math.floor(rng() * 4);
    const base = spherical(cell.x, cell.y, num(cell.terrain.elevation_m), 0.55);
    const frame = localFrame(base.normal);
    for (let i = 0; i < count && index < maxInstances; i += 1) {
      const angle = rng() * Math.PI * 2;
      const distance = 0.10 + rng() * 0.65;
      const position = base.position.clone()
        .addScaledVector(frame.tangent, Math.cos(angle) * distance)
        .addScaledVector(frame.bitangent, Math.sin(angle) * distance)
        .normalize()
        .multiplyScalar(base.position.length() + 0.2);
      const scale = 0.65 + rng() * 0.75;
      matrix.compose(position, new THREE.Quaternion().setFromUnitVectors(UP, base.normal), new THREE.Vector3(scale, scale, scale));
      mesh.setMatrixAt(index++, matrix);
    }
  }
  mesh.count = index;
  mesh.instanceMatrix.needsUpdate = true;
  globe.add(mesh);
}

function addMountains(cells) {
  const candidates = cells.filter((cell) => cell.terrain?.land && (biomeName(cell).includes('mountain') || num(cell.terrain.elevation_m) > mapper.minElevation + (mapper.maxElevation - mapper.minElevation) * 0.72));
  if (!candidates.length) return;
  const selected = candidates.slice(0, Math.min(900, candidates.length));
  const mesh = new THREE.InstancedMesh(new THREE.IcosahedronGeometry(0.75, 1), new THREE.MeshStandardMaterial({ color: 0x6f6659, roughness: 1 }), selected.length);
  const matrix = new THREE.Matrix4();
  selected.forEach((cell, index) => {
    const mapped = spherical(cell.x, cell.y, num(cell.terrain.elevation_m), 0.5);
    const scale = 0.55 + clamp((num(cell.terrain.elevation_m) - mapper.minElevation) / Math.max(1, mapper.maxElevation - mapper.minElevation), 0, 1) * 1.4;
    matrix.compose(mapped.position, new THREE.Quaternion().setFromUnitVectors(UP, mapped.normal), new THREE.Vector3(scale * 0.85, scale * 1.35, scale * 0.85));
    mesh.setMatrixAt(index, matrix);
  });
  mesh.instanceMatrix.needsUpdate = true;
  globe.add(mesh);
}

function addRivers(planet) {
  const rivers = Array.isArray(planet?.rivers) ? planet.rivers : [];
  for (const river of rivers.slice(0, 500)) {
    const downstream = Array.isArray(river.downstream) ? river.downstream : [];
    if (downstream.length < 2) continue;
    const a = mapper.cellMap.get(`${river.x}:${river.y}`);
    const b = mapper.cellMap.get(`${downstream[0]}:${downstream[1]}`);
    if (!a || !b) continue;
    const p1 = spherical(river.x, river.y, num(a.terrain?.elevation_m), 0.35).position;
    const p2 = spherical(downstream[0], downstream[1], num(b.terrain?.elevation_m), 0.35).position;
    const mid = p1.clone().add(p2).multiplyScalar(0.5).normalize().multiplyScalar((p1.length() + p2.length()) * 0.5 + 0.05);
    const curve = new THREE.CatmullRomCurve3([p1, mid, p2]);
    const tube = new THREE.Mesh(new THREE.TubeGeometry(curve, 8, 0.055, 5, false), new THREE.MeshStandardMaterial({ color: 0x54bff2, roughness: 0.18, metalness: 0.05 }));
    tube.userData = { type: 'river', data: river };
    globe.add(tube);
  }
}

function addSettlements(visual) {
  const settlements = Array.isArray(visual?.settlements) ? visual.settlements : [];
  for (const settlement of settlements) {
    const location = Array.isArray(settlement.location) ? settlement.location : null;
    if (!location || location.length < 2) continue;
    const cell = mapper.cellMap.get(`${location[0]}:${location[1]}`);
    const mapped = spherical(location[0], location[1], num(cell?.terrain?.elevation_m), 0.62);
    const frame = localFrame(mapped.normal);
    const population = Math.max(0, num(settlement.population));
    const cityScale = clamp(0.35 + Math.log10(1 + population) * 0.25, 0.35, 1.35);

    const hub = new THREE.Mesh(new THREE.CylinderGeometry(cityScale, cityScale * 1.08, 0.28, 18), new THREE.MeshStandardMaterial({ color: 0xd49a57, roughness: 0.7 }));
    hub.position.copy(mapped.position);
    hub.quaternion.setFromUnitVectors(UP, mapped.normal);
    hub.userData = { type: 'settlement', data: settlement };
    globe.add(hub);

    const buildings = Array.isArray(settlement.buildings) ? settlement.buildings : [];
    for (let i = 0; i < buildings.length && i < 80; i += 1) {
      const building = buildings[i];
      const angle = i * 2.3999632297;
      const distance = cityScale * (1.25 + (i % 5) * 0.42);
      const position = mapped.position.clone()
        .addScaledVector(frame.tangent, Math.cos(angle) * distance)
        .addScaledVector(frame.bitangent, Math.sin(angle) * distance)
        .normalize()
        .multiplyScalar(RADIUS + 0.72);
      const height = 0.28 + clamp(num(building.capacity, 1) / 100, 0, 1) * 0.8;
      const box = new THREE.Mesh(new THREE.BoxGeometry(0.22, height, 0.22), new THREE.MeshStandardMaterial({ color: 0xb9a27c, roughness: 0.8 }));
      box.position.copy(position);
      box.quaternion.setFromUnitVectors(UP, mapped.normal);
      box.userData = { type: 'building', data: building };
      globe.add(box);
    }
  }
}

function renderWorld(visual) {
  if (!visual?.planet) throw new Error('Authoritative Genesis visualization payload missing planet');
  const cells = flattenCells(visual.planet);
  if (!cells.length) throw new Error('Authoritative Genesis planet has no cells');
  mapper = makeMapper(cells);
  clearGlobe();
  makeOcean();
  makeLand(cells);
  addMountains(cells);
  addForests(cells);
  addRivers(visual.planet);
  addSettlements(visual);
  makeClouds();
  makeAtmosphere();
  state = visual;
  updateHud(visual);
}

function updateHud(visual) {
  const metrics = visual?.metrics || {};
  const population = num(metrics.population ?? visual?.agents?.length);
  const settlements = Array.isArray(visual?.settlements) ? visual.settlements.length : 0;
  const buildings = Array.isArray(visual?.settlements) ? visual.settlements.reduce((sum, s) => sum + (Array.isArray(s.buildings) ? s.buildings.length : 0), 0) : 0;
  const wildlife = Array.isArray(visual?.wildlife) ? visual.wildlife.length : 0;
  const persistence = visual?.persistence?.configured ? 'PostgreSQL persistent' : 'memory only';
  metricsEl.textContent = `tick ${num(visual?.tick)} · ${persistence} · WebGL2 ${renderer.capabilities.isWebGL2 ? 'active' : 'fallback'}\npeople ${population.toLocaleString()} · wildlife ${wildlife.toLocaleString()}\nsettlements ${settlements.toLocaleString()} · buildings ${buildings.toLocaleString()}`;
  setStatus(`Genesis LIVE · tick ${num(visual?.tick)} · real-time procedural Earth`);
}

async function fetchJson(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, { cache: 'no-store', ...options });
  const payload = await response.json();
  if (!response.ok) throw new Error(payload?.error || `${response.status} ${response.statusText}`);
  return payload;
}

async function refreshWorld(force = false) {
  const visual = await fetchJson('/world/state');
  const tick = num(visual?.tick, -1);
  if (force || tick !== lastRenderTick) {
    renderWorld(visual);
    lastRenderTick = tick;
  }
}

async function stepSimulation(count) {
  if (stepping) return;
  stepping = true;
  try {
    await fetchJson(`/step?count=${encodeURIComponent(count)}`, { method: 'POST' });
    await refreshWorld();
  } catch (error) {
    setStatus(`Simulation error · ${error.message}`);
    setPlaying(false);
  } finally {
    stepping = false;
  }
}

function speedValue() { return Math.max(0.5, num(speedEl.value, 1)); }
function setPlaying(next) {
  playing = Boolean(next);
  playButton.textContent = playing ? 'Ⅱ Pause' : '▶ Play';
  playButton.setAttribute('aria-pressed', String(playing));
}

function inspectAt(clientX, clientY) {
  const rect = renderer.domElement.getBoundingClientRect();
  pointer.x = ((clientX - rect.left) / rect.width) * 2 - 1;
  pointer.y = -((clientY - rect.top) / rect.height) * 2 + 1;
  raycaster.setFromCamera(pointer, camera);
  const hits = raycaster.intersectObjects(globe.children, true);
  if (!hits.length) return;
  const hit = hits[0];
  let object = hit.object;
  while (object && !object.userData?.type && object.parent) object = object.parent;
  const data = object?.userData || {};
  if (data.type === 'settlement') {
    const s = data.data || {};
    inspectorEl.textContent = `Settlement ${s.name || s.id || 'unknown'} · population ${num(s.population).toLocaleString()} · buildings ${(s.buildings || []).length}`;
    return;
  }
  if (data.type === 'building') {
    const b = data.data || {};
    inspectorEl.textContent = `Building ${b.id || 'unknown'} · kind ${b.kind || 'unknown'} · capacity ${num(b.capacity)} · condition ${num(b.condition).toFixed(2)}`;
    return;
  }
  if (data.type === 'river') {
    inspectorEl.textContent = 'River · rendered as a smooth water channel from authoritative hydrology.';
    return;
  }
  const local = globe.worldToLocal(hit.point.clone()).normalize();
  const lon = Math.atan2(local.z, local.x);
  const lat = Math.asin(clamp(local.y, -1, 1));
  const x = Math.floor(mapper.minX + ((lon + Math.PI) / (Math.PI * 2)) * mapper.width);
  const y = Math.floor(mapper.minY + ((Math.PI * 0.5 - lat) / Math.PI) * mapper.height);
  const cell = mapper.cellMap.get(`${x}:${y}`);
  if (cell) {
    const terrain = cell.terrain || {};
    inspectorEl.textContent = `Terrain · ${biomeName(cell) || 'natural biome'} · elevation ${num(terrain.elevation_m).toFixed(1)} m · ${terrain.land ? 'land' : 'ocean'}`;
  } else {
    inspectorEl.textContent = data.type === 'ocean' ? 'Ocean · continuous spherical water surface derived from authoritative planet state.' : 'Planet surface · authoritative Genesis terrain.';
  }
}

playButton.addEventListener('click', () => setPlaying(!playing));
saveButton.addEventListener('click', async () => {
  try {
    const result = await fetchJson('/checkpoint', { method: 'POST' });
    setStatus(`Saved authoritative checkpoint · tick ${result.tick}`);
  } catch (error) {
    setStatus(`Save failed · ${error.message}`);
  }
});

renderer.domElement.addEventListener('pointerup', (event) => {
  if (event.pointerType === 'mouse' && event.button !== 0) return;
  inspectAt(event.clientX, event.clientY);
});

window.addEventListener('resize', () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, MAX_PIXEL_RATIO));
  renderer.setSize(window.innerWidth, window.innerHeight, false);
});

async function bootstrap() {
  makeStars();
  try {
    await refreshWorld(true);
  } catch (error) {
    setStatus(`Backend connection failed · ${error.message}`);
    inspectorEl.textContent = 'The visual engine requires the authoritative Genesis backend. No fallback world is generated.';
  }
}

function animate() {
  requestAnimationFrame(animate);
  const delta = Math.min(clock.getDelta(), 0.1);
  controls.update();
  if (cloudMaterial) cloudMaterial.uniforms.time.value += delta;
  if (playing && !stepping) {
    stepAccumulator += delta * speedValue() * 2;
    if (stepAccumulator >= 1) {
      const count = Math.min(5, Math.floor(stepAccumulator));
      stepAccumulator -= count;
      void stepSimulation(count);
    }
  }
  renderer.render(scene, camera);
}

void bootstrap();
animate();
