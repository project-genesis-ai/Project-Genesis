import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.179.1/build/three.module.js';
import { OrbitControls } from 'https://cdn.jsdelivr.net/npm/three@0.179.1/examples/jsm/controls/OrbitControls.js';

const API_BASE = (window.GENESIS_API_BASE || window.location.origin).replace(/\/$/, '');
const canvas = document.querySelector('#genesis-canvas');
const statusEl = document.querySelector('#status');
const metricsEl = document.querySelector('#metrics');
const inspectorEl = document.querySelector('#inspector');
const playButton = document.querySelector('#play');
const speedEl = document.querySelector('#speed');
const saveButton = document.querySelector('#save');

const RADIUS = 50;
const MAX_PIXEL_RATIO = 1.5;
const DEG = Math.PI / 180;
const AXIAL_TILT = 23.4 * DEG;
const UP = new THREE.Vector3(0, 1, 0);

const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, powerPreference: 'high-performance', logarithmicDepthBuffer: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, MAX_PIXEL_RATIO));
renderer.setSize(window.innerWidth, window.innerHeight, false);
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.05;

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x01030a);
const camera = new THREE.PerspectiveCamera(38, window.innerWidth / window.innerHeight, 0.05, 5000);
camera.position.set(0, RADIUS * 0.28, RADIUS * 2.35);
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.055;
controls.minDistance = RADIUS * 1.04;
controls.maxDistance = RADIUS * 7;
controls.enablePan = false;
controls.target.set(0, 0, 0);

scene.add(new THREE.HemisphereLight(0xb9d9ff, 0x1a2018, 1.2));
const sun = new THREE.DirectionalLight(0xffffff, 3.4);
sun.position.set(140, 100, 90);
scene.add(sun);

const globe = new THREE.Group();
globe.rotation.z = AXIAL_TILT;
scene.add(globe);

const raycaster = new THREE.Raycaster();
const pointer = new THREE.Vector2();
let state = null;
let mapper = null;
let lastRenderTick = -1;
let playing = false;
let stepping = false;

const num = (value, fallback = 0) => { const n = Number(value); return Number.isFinite(n) ? n : fallback; };
const setStatus = (text) => { statusEl.textContent = text; };

function disposeObject(object) {
  object.traverse((node) => {
    node.geometry?.dispose();
    if (Array.isArray(node.material)) node.material.forEach((m) => m.dispose());
    else node.material?.dispose();
  });
}
function clearWorld() {
  while (globe.children.length) disposeObject(globe.remove(globe.children[0]));
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
  const xs = cells.map((c) => c.x); const ys = cells.map((c) => c.y);
  const minX = Math.min(...xs); const maxX = Math.max(...xs); const minY = Math.min(...ys); const maxY = Math.max(...ys);
  const width = Math.max(1, maxX - minX + 1); const height = Math.max(1, maxY - minY + 1);
  const landElevations = cells.filter((c) => c.terrain?.land).map((c) => num(c.terrain.elevation_m));
  const minElevation = landElevations.length ? Math.min(...landElevations) : 0;
  const maxElevation = landElevations.length ? Math.max(...landElevations) : minElevation;
  const elevationSpan = Math.max(1, maxElevation - minElevation);
  const cellMap = new Map(cells.map((c) => [`${c.x}:${c.y}`, c]));
  const elevationAt = (x, y, fallback) => {
    const c = cellMap.get(`${x}:${y}`);
    return c?.terrain?.land ? num(c.terrain.elevation_m, fallback) : fallback;
  };
  const spherical = (x, y, elevation = 0, lift = 0) => {
    const lon = ((x - minX) / width) * Math.PI * 2 - Math.PI;
    const lat = Math.PI * 0.5 - ((y - minY) / height) * Math.PI;
    const ratio = Math.max(0, Math.min(1, (num(elevation) - minElevation) / elevationSpan));
    const radius = RADIUS + ratio * RADIUS * 0.11 + lift;
    const cosLat = Math.cos(lat);
    const normal = new THREE.Vector3(cosLat * Math.cos(lon), Math.sin(lat), cosLat * Math.sin(lon)).normalize();
    return { normal, position: normal.clone().multiplyScalar(radius), lon, lat };
  };
  const cellCorner = (cell, dx, dy) => {
    const x = cell.x + dx; const y = cell.y + dy;
    const base = num(cell.terrain?.elevation_m);
    const neighbours = [
      elevationAt(x - (dx ? 1 : 0), y - (dy ? 1 : 0), base),
      elevationAt(x - (dx ? 1 : 0), y, base),
      elevationAt(x, y - (dy ? 1 : 0), base),
      elevationAt(x, y, base),
    ];
    const elevation = neighbours.reduce((sum, value) => sum + value, 0) / neighbours.length;
    return spherical(x, y, elevation, 0.085);
  };
  return { minX, maxX, minY, maxY, width, height, cellMap, spherical, cellCorner };
}
function biomeColor(cell) {
  const name = String(cell?.biome?.name || '').toLowerCase();
  const productivity = Math.max(0, Math.min(1, num(cell?.biome?.vegetation_productivity)));
  if (!cell?.terrain?.land) return new THREE.Color(0x0b477d);
  if (name.includes('desert')) return new THREE.Color().setHSL(0.105, 0.52, 0.57);
  if (name.includes('tundra') || name.includes('ice') || name.includes('snow')) return new THREE.Color().setHSL(0.56, 0.12, 0.78);
  if (name.includes('forest') || name.includes('wood')) return new THREE.Color().setHSL(0.34, 0.58, 0.25 + productivity * 0.08);
  if (name.includes('savanna')) return new THREE.Color().setHSL(0.18, 0.48, 0.43 + productivity * 0.07);
  if (name.includes('grass')) return new THREE.Color().setHSL(0.25, 0.5, 0.39 + productivity * 0.08);
  if (name.includes('wetland')) return new THREE.Color().setHSL(0.43, 0.46, 0.31);
  return new THREE.Color().setHSL(0.24, 0.40, 0.36 + productivity * 0.09);
}
function makeOcean() {
  const ocean = new THREE.Mesh(
    new THREE.SphereGeometry(RADIUS, 128, 96),
    new THREE.MeshPhysicalMaterial({ color: 0x063f7a, roughness: 0.24, metalness: 0.01, clearcoat: 0.72, clearcoatRoughness: 0.16 })
  );
  ocean.userData = { type: 'ocean' };
  globe.add(ocean);
}
function makeAtmosphere() {
  const material = new THREE.ShaderMaterial({
    transparent: true, depthWrite: false, side: THREE.BackSide, blending: THREE.AdditiveBlending,
    uniforms: { glowColor: { value: new THREE.Color(0x4aa7ff) }, strength: { value: 0.65 } },
    vertexShader: 'varying vec3 vNormal; varying vec3 vWorld; void main(){vNormal=normalize(normalMatrix*normal);vec4 p=modelMatrix*vec4(position,1.0);vWorld=p.xyz;gl_Position=projectionMatrix*viewMatrix*p;}',
    fragmentShader: 'uniform vec3 glowColor;uniform float strength;varying vec3 vNormal;varying vec3 vWorld;void main(){vec3 viewDir=normalize(cameraPosition-vWorld);float rim=pow(1.0-max(dot(vNormal,viewDir),0.0),3.2);gl_FragColor=vec4(glowColor,rim*strength);}',
  });
  globe.add(new THREE.Mesh(new THREE.SphereGeometry(RADIUS * 1.035, 128, 96), material));
}
function buildTerrain(planet) {
  const cells = flattenCells(planet);
  if (!cells.length) throw new Error('Authoritative Genesis planet has no cells');
  mapper = makeMapper(cells);

  // Render each authoritative land cell as its own spherical quad. Never bridge
  // across missing/water cells; this prevents the radial spikes seen previously.
  const land = cells.filter((cell) => cell.terrain?.land);
  const positions = []; const colors = []; const indices = [];
  for (const cell of land) {
    const base = positions.length / 3;
    const corners = [mapper.cellCorner(cell, 0, 0), mapper.cellCorner(cell, 1, 0), mapper.cellCorner(cell, 0, 1), mapper.cellCorner(cell, 1, 1)];
    for (const corner of corners) positions.push(corner.position.x, corner.position.y, corner.position.z);
    const color = biomeColor(cell);
    for (let i = 0; i < 4; i += 1) colors.push(color.r, color.g, color.b);
    indices.push(base, base + 1, base + 2, base + 1, base + 3, base + 2);
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
  geometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));
  geometry.setIndex(indices);
  geometry.computeVertexNormals();
  const terrain = new THREE.Mesh(geometry, new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.88, metalness: 0.01, side: THREE.FrontSide }));
  terrain.userData = { type: 'terrain', cellMap: mapper.cellMap };
  globe.add(terrain);

  const riverPositions = [];
  for (const river of Array.isArray(planet.rivers) ? planet.rivers : []) {
    const downstream = Array.isArray(river.downstream) ? river.downstream : [];
    if (downstream.length < 2) continue;
    const aCell = mapper.cellMap.get(`${river.x}:${river.y}`);
    const bCell = mapper.cellMap.get(`${downstream[0]}:${downstream[1]}`);
    if (!aCell || !bCell) continue;
    const a = mapper.spherical(river.x + 0.5, river.y + 0.5, aCell.terrain?.elevation_m || 0, 0.20).position;
    const b = mapper.spherical(downstream[0] + 0.5, downstream[1] + 0.5, bCell.terrain?.elevation_m || 0, 0.20).position;
    riverPositions.push(a.x, a.y, a.z, b.x, b.y, b.z);
  }
  if (riverPositions.length) {
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.Float32BufferAttribute(riverPositions, 3));
    globe.add(new THREE.LineSegments(g, new THREE.LineBasicMaterial({ color: 0x66caff, transparent: true, opacity: 0.72 })));
  }
}
function localFrame(normal) {
  let tangent = new THREE.Vector3(0, 1, 0);
  if (Math.abs(normal.dot(tangent)) > 0.92) tangent = new THREE.Vector3(1, 0, 0);
  tangent.projectOnPlane(normal).normalize();
  return { tangent, bitangent: new THREE.Vector3().crossVectors(normal, tangent).normalize() };
}
function addSettlements(visual) {
  const group = new THREE.Group();
  for (const settlement of Array.isArray(visual.settlements) ? visual.settlements : []) {
    const location = Array.isArray(settlement.location) ? settlement.location : null;
    if (!location || location.length < 2) continue;
    const cell = mapper.cellMap.get(`${location[0]}:${location[1]}`);
    const mapped = mapper.spherical(location[0] + 0.5, location[1] + 0.5, cell?.terrain?.elevation_m || 0, 0.35);
    const frame = localFrame(mapped.normal);
    const population = Math.max(0, num(settlement.population));
    const radius = Math.max(0.32, Math.min(1.65, 0.38 + Math.log10(1 + population) * 0.30));
    const marker = new THREE.Mesh(new THREE.CylinderGeometry(radius, radius * 0.88, radius * 0.5, 12), new THREE.MeshStandardMaterial({ color: 0xe2a65f, roughness: 0.72 }));
    marker.position.copy(mapped.position); marker.quaternion.setFromUnitVectors(UP, mapped.normal); marker.userData = { type: 'settlement', data: settlement }; group.add(marker);
    for (const [index, building] of (settlement.buildings || []).entries()) {
      const angle = index * 2.3999632297; const distance = radius * (1.15 + (index % 3) * 0.42);
      const position = mapped.position.clone().addScaledVector(frame.tangent, Math.cos(angle) * distance).addScaledVector(frame.bitangent, Math.sin(angle) * distance).normalize().multiplyScalar(RADIUS + 0.48);
      const size = Math.max(0.10, radius * 0.20); const height = Math.max(size * 1.35, size + Math.abs(num(building.capacity)) * 0.005);
      const mesh = new THREE.Mesh(new THREE.BoxGeometry(size, height, size), new THREE.MeshStandardMaterial({ color: 0xc1b399, roughness: 0.82 }));
      mesh.position.copy(position); mesh.quaternion.setFromUnitVectors(UP, position.clone().normalize()); mesh.userData = { type: 'building', data: building, settlement }; group.add(mesh);
    }
  }
  globe.add(group);
}
function addAgents(visual) {
  const agents = Array.isArray(visual.agents) ? visual.agents : [];
  if (!agents.length) return;
  const size = Math.max(0.07, RADIUS / Math.max(mapper.width, mapper.height) * 0.38);
  const mesh = new THREE.InstancedMesh(new THREE.SphereGeometry(size, 8, 6), new THREE.MeshStandardMaterial({ color: 0xffd166, roughness: 0.68 }), agents.length);
  const matrix = new THREE.Matrix4();
  agents.forEach((agent, index) => {
    const position = Array.isArray(agent.position) ? agent.position : null;
    if (!position || position.length < 2) return;
    const cell = mapper.cellMap.get(`${position[0]}:${position[1]}`);
    const mapped = mapper.spherical(position[0] + 0.5, position[1] + 0.5, cell?.terrain?.elevation_m || 0, 0.65);
    matrix.setPosition(mapped.position.x, mapped.position.y, mapped.position.z); mesh.setMatrixAt(index, matrix);
  });
  mesh.instanceMatrix.needsUpdate = true; mesh.userData = { type: 'agents', data: agents }; globe.add(mesh);
}
function extractWildlifePosition(item) {
  if (Array.isArray(item?.position) && item.position.length >= 2) return item.position;
  if (Array.isArray(item?.location) && item.location.length >= 2) return item.location;
  if (Number.isFinite(Number(item?.x)) && Number.isFinite(Number(item?.y))) return [Number(item.x), Number(item.y)];
  return null;
}
function addWildlife(visual) {
  const wildlife = (Array.isArray(visual.wildlife) ? visual.wildlife : []).map((item) => ({ item, position: extractWildlifePosition(item) })).filter((x) => x.position);
  if (!wildlife.length) return;
  const size = Math.max(0.06, RADIUS / Math.max(mapper.width, mapper.height) * 0.28);
  const mesh = new THREE.InstancedMesh(new THREE.SphereGeometry(size, 7, 5), new THREE.MeshStandardMaterial({ color: 0xb3d88d, roughness: 0.9 }), wildlife.length);
  const matrix = new THREE.Matrix4();
  wildlife.forEach((entry, index) => {
    const [x, y] = entry.position; const cell = mapper.cellMap.get(`${x}:${y}`);
    const mapped = mapper.spherical(x + 0.5, y + 0.5, cell?.terrain?.elevation_m || 0, 0.48);
    matrix.setPosition(mapped.position.x, mapped.position.y, mapped.position.z); mesh.setMatrixAt(index, matrix);
  });
  mesh.instanceMatrix.needsUpdate = true; mesh.userData = { type: 'wildlife', data: wildlife.map((x) => x.item) }; globe.add(mesh);
}
function renderMetrics(visual) {
  const metrics = visual.metrics || {};
  const cells = flattenCells(visual.planet); const land = cells.filter((cell) => cell.terrain?.land).length;
  const people = Array.isArray(visual.agents) ? visual.agents.length : 0; const wildlife = Array.isArray(visual.wildlife) ? visual.wildlife.length : 0;
  const settlements = Array.isArray(visual.settlements) ? visual.settlements.length : 0; const buildings = (visual.settlements || []).reduce((sum, item) => sum + (item.buildings?.length || 0), 0);
  const resources = visual.resources && typeof visual.resources === 'object' ? Object.entries(visual.resources).filter(([, v]) => ['number', 'string'].includes(typeof v)).slice(0, 4).map(([k, v]) => `${k}=${v}`).join(', ') : '';
  metricsEl.textContent = [`tick ${num(visual.tick)} · land ${land}/${cells.length}`, `people ${people} · wildlife ${wildlife}`, `settlements ${settlements} · buildings ${buildings}`, resources ? `resources: ${resources}` : 'resources: persistent state available', metrics.population != null ? `engine population ${metrics.population}` : ''].filter(Boolean).join('\n');
}
function inspect(hit) {
  const object = hit?.object; if (!object) return;
  if (object.userData.type === 'settlement') { const d = object.userData.data; inspectorEl.textContent = `${d.name || 'Settlement'} · ${d.kind || 'settlement'} · population ${num(d.population)} · buildings ${d.buildings?.length || 0}`; return; }
  if (object.userData.type === 'building') { const d = object.userData.data; inspectorEl.textContent = `Building ${d.kind || 'structure'} · condition ${(num(d.condition) * 100).toFixed(0)}% · capacity ${num(d.capacity)}`; return; }
  if (object.userData.type === 'agents') { const d = object.userData.data[hit.instanceId ?? 0]; if (d) inspectorEl.textContent = `${d.name || 'Citizen'} · ${d.life_state || 'citizen'} · health ${(num(d.health) * 100).toFixed(0)}% · wealth ${num(d.wealth).toFixed(2)}`; return; }
  if (object.userData.type === 'wildlife') { const d = object.userData.data[hit.instanceId ?? 0]; if (d) inspectorEl.textContent = `Wildlife ${d.species_id || d.species || d.organism_id || 'organism'}`; return; }
  if (object.userData.type === 'terrain') { const p = hit.point.clone().normalize(); inspectorEl.textContent = `Planet surface · latitude ${(Math.asin(p.y) / DEG).toFixed(2)}° · longitude ${(Math.atan2(p.z, p.x) / DEG).toFixed(2)}°`; }
}
function rebuild(visual) { clearWorld(); makeOcean(); buildTerrain(visual.planet); addSettlements(visual); addAgents(visual); addWildlife(visual); makeAtmosphere(); renderMetrics(visual); lastRenderTick = num(visual.tick); }
async function fetchState() { const response = await fetch(`${API_BASE}/world/state`, { headers: { Accept: 'application/json' }, cache: 'no-store' }); if (!response.ok) throw new Error(`world/state ${response.status}`); return response.json(); }
async function refresh(force = false) {
  const visual = await fetchState(); state = visual;
  if (force || num(visual.tick) !== lastRenderTick) rebuild(visual); else renderMetrics(visual);
  const backend = visual.persistence?.configured ? 'PostgreSQL persistent' : 'in-memory';
  const accelerator = navigator.gpu ? 'WebGPU available · WebGL active' : 'WebGL active';
  setStatus(`Genesis LIVE · tick ${visual.tick} · ${backend} · ${accelerator}`);
}
async function initialize() {
  setStatus('Checking authoritative Genesis backend…');
  const health = await fetch(`${API_BASE}/health`, { cache: 'no-store' });
  if (!health.ok) throw new Error(`health ${health.status}`);
  const healthJson = await health.json();
  if (healthJson.status !== 'ok') throw new Error('Genesis backend is not ready');
  await refresh(true);
}
async function stepOnce() {
  if (stepping) return;
  stepping = true;
  try {
    const count = Number(speedEl.value);
    const response = await fetch(`${API_BASE}/step?count=${count}`, { method: 'POST' });
    if (!response.ok) throw new Error(`step ${response.status}`);
    await refresh(true);
  } catch (error) {
    console.error(error); playing = false; updatePlayButton(); setStatus(`Simulation error: ${error.message}`);
  } finally { stepping = false; }
}
function updatePlayButton() {
  playButton.textContent = playing ? 'Ⅱ Pause' : '▶ Play';
  playButton.setAttribute('aria-pressed', String(playing));
}
playButton.addEventListener('click', () => { playing = !playing; updatePlayButton(); if (playing) stepOnce(); });
saveButton.addEventListener('click', async () => {
  try {
    const response = await fetch(`${API_BASE}/checkpoint`, { method: 'POST' });
    if (!response.ok) throw new Error(`checkpoint ${response.status}`);
    setStatus(`Genesis checkpoint saved · tick ${state?.tick ?? 'unknown'}`);
  } catch (error) { setStatus(`Save failed: ${error.message}`); }
});
canvas.addEventListener('pointerdown', (event) => {
  const rect = canvas.getBoundingClientRect(); pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1; pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
  raycaster.setFromCamera(pointer, camera); const hits = raycaster.intersectObjects(globe.children, true); if (hits.length) inspect(hits[0]);
});
window.addEventListener('resize', () => { camera.aspect = window.innerWidth / window.innerHeight; camera.updateProjectionMatrix(); renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, MAX_PIXEL_RATIO)); renderer.setSize(window.innerWidth, window.innerHeight, false); });
setInterval(() => { if (playing) stepOnce(); }, 900);
updatePlayButton();
renderer.setAnimationLoop(() => { controls.update(); renderer.render(scene, camera); });
initialize().catch((error) => { console.error(error); setStatus(`3D world unavailable: ${error.message}`); metricsEl.textContent = 'The authoritative Genesis backend could not be loaded.'; });
