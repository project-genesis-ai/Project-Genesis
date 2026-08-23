import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.179.1/build/three.module.js';
import { OrbitControls } from 'https://cdn.jsdelivr.net/npm/three@0.179.1/examples/jsm/controls/OrbitControls.js';

const API_BASE = (window.GENESIS_API_BASE || window.location.origin).replace(/\/$/, '');
const canvas = document.querySelector('#genesis-canvas');
const statusEl = document.querySelector('#status');
const metricsEl = document.querySelector('#metrics');
const inspectorEl = document.querySelector('#inspector');
const playButton = document.querySelector('#play');
const pauseButton = document.querySelector('#pause');
const speedEl = document.querySelector('#speed');
const saveButton = document.querySelector('#save');

const RADIUS = 50;
const MAX_PIXEL_RATIO = 1.5;
const DEG = Math.PI / 180;

const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, powerPreference: 'high-performance', logarithmicDepthBuffer: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, MAX_PIXEL_RATIO));
renderer.setSize(window.innerWidth, window.innerHeight, false);
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.05;

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x01030a);
const camera = new THREE.PerspectiveCamera(38, window.innerWidth / window.innerHeight, 0.05, 5000);
camera.position.set(0, RADIUS * 0.55, RADIUS * 2.15);
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.055;
controls.minDistance = RADIUS * 1.04;
controls.maxDistance = RADIUS * 8;
controls.enablePan = false;
controls.target.set(0, 0, 0);
scene.add(new THREE.HemisphereLight(0x9fc9ff, 0x172014, 1.25));
const sun = new THREE.DirectionalLight(0xffffff, 3.2);
sun.position.set(120, 90, 80);
scene.add(sun);

const world = new THREE.Group();
const globe = new THREE.Group();
world.add(globe);
scene.add(world);
const raycaster = new THREE.Raycaster();
const pointer = new THREE.Vector2();
const clock = new THREE.Clock();
let state = null;
let mapper = null;
let lastRenderTick = -1;
let playing = false;
let stepping = false;

const setStatus = (text) => { statusEl.textContent = text; };
const num = (value, fallback = 0) => { const parsed = Number(value); return Number.isFinite(parsed) ? parsed : fallback; };

function disposeObject(object) {
  object.traverse((node) => {
    node.geometry?.dispose();
    if (Array.isArray(node.material)) node.material.forEach((material) => material.dispose());
    else node.material?.dispose();
  });
}
function clearWorld() {
  while (globe.children.length) disposeObject(globe.remove(globe.children[0]));
}
function flattenCells(planet) {
  const result = [];
  const rows = Array.isArray(planet?.cells) ? planet.cells : [];
  for (let rowIndex = 0; rowIndex < rows.length; rowIndex += 1) {
    const row = Array.isArray(rows[rowIndex]) ? rows[rowIndex] : [];
    for (let colIndex = 0; colIndex < row.length; colIndex += 1) {
      const cell = row[colIndex];
      if (cell?.terrain) result.push({ ...cell, x: num(cell.terrain.x, colIndex), y: num(cell.terrain.y, rowIndex) });
    }
  }
  return result;
}
function makeMapper(cells) {
  const xs = cells.map((cell) => cell.x); const ys = cells.map((cell) => cell.y);
  const minX = Math.min(...xs); const maxX = Math.max(...xs); const minY = Math.min(...ys); const maxY = Math.max(...ys);
  const width = Math.max(1, maxX - minX + 1); const height = Math.max(1, maxY - minY + 1);
  const elevations = cells.filter((cell) => cell.terrain?.land).map((cell) => num(cell.terrain?.elevation_m)).filter(Number.isFinite);
  const minElevation = elevations.length ? Math.min(...elevations) : 0;
  const maxElevation = elevations.length ? Math.max(...elevations) : minElevation;
  const elevationSpan = Math.max(1, maxElevation - minElevation);
  const cellMap = new Map(cells.map((cell) => [`${cell.x}:${cell.y}`, cell]));
  const toWorld = (x, y, elevation = 0, lift = 0) => {
    const nx = (num(x) - minX) / width;
    const ny = (num(y) - minY) / Math.max(1, height - 1);
    const lon = nx * Math.PI * 2 - Math.PI;
    const lat = Math.PI * 0.5 - ny * Math.PI;
    const terrainRatio = Math.max(0, Math.min(1, (num(elevation) - minElevation) / elevationSpan));
    const radius = RADIUS + terrainRatio * RADIUS * 0.075 + lift;
    const cosLat = Math.cos(lat);
    const normal = new THREE.Vector3(cosLat * Math.cos(lon), Math.sin(lat), cosLat * Math.sin(lon)).normalize();
    return { position: normal.clone().multiplyScalar(radius), normal, lon, lat, radius };
  };
  return { minX, maxX, minY, maxY, width, height, cellMap, toWorld };
}
function biomeColor(cell) {
  const name = String(cell?.biome?.name || '').toLowerCase();
  const productivity = Math.max(0, Math.min(1, num(cell?.biome?.vegetation_productivity)));
  if (!cell?.terrain?.land) return new THREE.Color(0x123f72);
  if (name.includes('desert')) return new THREE.Color().setHSL(0.10, 0.48, 0.58);
  if (name.includes('forest') || name.includes('wood')) return new THREE.Color().setHSL(0.34, 0.48, 0.27 + productivity * 0.08);
  if (name.includes('tundra') || name.includes('ice')) return new THREE.Color().setHSL(0.54, 0.22, 0.72);
  if (name.includes('grass') || name.includes('savanna')) return new THREE.Color().setHSL(0.24, 0.42, 0.40 + productivity * 0.08);
  if (name.includes('wetland')) return new THREE.Color().setHSL(0.43, 0.38, 0.35);
  return new THREE.Color().setHSL(0.25, 0.34, 0.38 + productivity * 0.07);
}
function makeOcean() {
  const mesh = new THREE.Mesh(new THREE.SphereGeometry(RADIUS * 0.999, 96, 64), new THREE.MeshPhysicalMaterial({ color: 0x0b477a, roughness: 0.32, metalness: 0.03, clearcoat: 0.55, clearcoatRoughness: 0.22 }));
  mesh.userData = { type: 'ocean' };
  globe.add(mesh);
}
function makeAtmosphere() {
  const material = new THREE.ShaderMaterial({
    transparent: true,
    depthWrite: false,
    side: THREE.BackSide,
    blending: THREE.AdditiveBlending,
    uniforms: { glowColor: { value: new THREE.Color(0x3d9cff) }, strength: { value: 0.7 } },
    vertexShader: `varying vec3 vNormal; varying vec3 vWorldPosition; void main(){vNormal=normalize(normalMatrix*normal);vec4 wp=modelMatrix*vec4(position,1.0);vWorldPosition=wp.xyz;gl_Position=projectionMatrix*viewMatrix*wp;}`,
    fragmentShader: `uniform vec3 glowColor;uniform float strength;varying vec3 vNormal;varying vec3 vWorldPosition;void main(){vec3 viewDir=normalize(cameraPosition-vWorldPosition);float rim=pow(1.0-max(dot(vNormal,viewDir),0.0),3.2);gl_FragColor=vec4(glowColor,rim*strength);}`,
  });
  globe.add(new THREE.Mesh(new THREE.SphereGeometry(RADIUS * 1.035, 96, 64), material));
}
function buildTerrain(planet) {
  const cells = flattenCells(planet);
  if (!cells.length) throw new Error('Authoritative Genesis planet has no cells');
  mapper = makeMapper(cells);
  const step = Math.max(1, Math.ceil(Math.max(mapper.width, mapper.height) / 128));
  const sampled = cells.filter((cell) => step === 1 || ((cell.x - mapper.minX) % step === 0 && (cell.y - mapper.minY) % step === 0));
  const positions = []; const colors = []; const indices = []; const indexMap = new Map();
  sampled.forEach((cell, index) => {
    const mapped = mapper.toWorld(cell.x, cell.y, cell.terrain?.elevation_m, cell.terrain?.land ? 0.055 : 0);
    positions.push(mapped.position.x, mapped.position.y, mapped.position.z);
    const color = biomeColor(cell); colors.push(color.r, color.g, color.b); indexMap.set(`${cell.x}:${cell.y}`, index);
  });
  for (const cell of sampled) {
    const a = indexMap.get(`${cell.x}:${cell.y}`);
    const nextX = cell.x + step <= mapper.maxX ? cell.x + step : mapper.minX;
    const b = indexMap.get(`${nextX}:${cell.y}`);
    const c = indexMap.get(`${cell.x}:${cell.y + step}`);
    const d = indexMap.get(`${nextX}:${cell.y + step}`);
    const nextA = mapper.cellMap.get(`${nextX}:${cell.y}`); const nextC = mapper.cellMap.get(`${cell.x}:${cell.y + step}`); const nextD = mapper.cellMap.get(`${nextX}:${cell.y + step}`);
    if (a == null || b == null || c == null || d == null || !cell.terrain?.land || !nextA?.terrain?.land || !nextC?.terrain?.land || !nextD?.terrain?.land) continue;
    indices.push(a, b, c, b, d, c);
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
  geometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));
  geometry.setIndex(indices); geometry.computeVertexNormals();
  const terrainMesh = new THREE.Mesh(geometry, new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.86, metalness: 0.01 }));
  terrainMesh.userData = { type: 'terrain', cellMap: mapper.cellMap };
  globe.add(terrainMesh);

  const riverPositions = [];
  for (const river of planet.rivers || []) {
    const downstream = Array.isArray(river.downstream) ? river.downstream : [];
    if (downstream.length < 2) continue;
    const startCell = mapper.cellMap.get(`${river.x}:${river.y}`); const endCell = mapper.cellMap.get(`${downstream[0]}:${downstream[1]}`);
    if (!startCell || !endCell) continue;
    const start = mapper.toWorld(river.x, river.y, startCell.terrain?.elevation_m, 0.13).position;
    const end = mapper.toWorld(downstream[0], downstream[1], endCell.terrain?.elevation_m, 0.13).position;
    riverPositions.push(start.x, start.y, start.z, end.x, end.y, end.z);
  }
  if (riverPositions.length) {
    const riverGeometry = new THREE.BufferGeometry(); riverGeometry.setAttribute('position', new THREE.Float32BufferAttribute(riverPositions, 3));
    globe.add(new THREE.LineSegments(riverGeometry, new THREE.LineBasicMaterial({ color: 0x66c9ff, transparent: true, opacity: 0.9 })));
  }

  const vegetation = sampled.filter((cell) => cell.terrain?.land && num(cell.biome?.vegetation_productivity) > 0.45);
  if (vegetation.length) {
    const count = vegetation.length;
    const unit = RADIUS / Math.max(mapper.width, mapper.height);
    const trees = new THREE.InstancedMesh(new THREE.ConeGeometry(Math.max(0.11, unit * 0.42), Math.max(0.35, unit * 2.2), 6), new THREE.MeshStandardMaterial({ color: 0x2d7549, roughness: 0.92 }), count);
    const matrix = new THREE.Matrix4(); const quaternion = new THREE.Quaternion(); const scale = new THREE.Vector3();
    vegetation.forEach((cell, index) => {
      const mapped = mapper.toWorld(cell.x, cell.y, cell.terrain?.elevation_m, 0.11); const productivity = Math.max(0, Math.min(1, num(cell.biome?.vegetation_productivity)));
      scale.setScalar(0.55 + productivity * 0.9); quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), mapped.normal); matrix.compose(mapped.position, quaternion, scale); trees.setMatrixAt(index, matrix);
    });
    trees.instanceMatrix.needsUpdate = true; trees.userData = { type: 'vegetation', count }; globe.add(trees);
  }
}
function localFrame(mapped) {
  const tangent = new THREE.Vector3(0, 1, 0);
  if (Math.abs(mapped.normal.dot(tangent)) > 0.92) tangent.set(1, 0, 0);
  tangent.projectOnPlane(mapped.normal).normalize();
  return { tangent, bitangent: new THREE.Vector3().crossVectors(mapped.normal, tangent).normalize() };
}
function addSettlements(visual) {
  const group = new THREE.Group(); group.userData = { type: 'settlements' };
  for (const settlement of visual.settlements || []) {
    const location = Array.isArray(settlement.location) ? settlement.location : null; if (!location || location.length < 2) continue;
    const cell = mapper.cellMap.get(`${location[0]}:${location[1]}`); const mapped = mapper.toWorld(location[0], location[1], cell?.terrain?.elevation_m || 0, 0.28); const frame = localFrame(mapped);
    const population = Math.max(0, num(settlement.population)); const radius = Math.max(0.34, Math.min(1.8, 0.42 + Math.log10(1 + population) * 0.34));
    const marker = new THREE.Mesh(new THREE.CylinderGeometry(radius, radius * 0.92, Math.max(0.18, radius * 0.55), 12), new THREE.MeshStandardMaterial({ color: 0xe0a55d, roughness: 0.75 }));
    marker.position.copy(mapped.position); marker.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), mapped.normal); marker.userData = { type: 'settlement', data: settlement }; group.add(marker);
    for (const [index, building] of (settlement.buildings || []).entries()) {
      const angle = index * 2.3999632297; const distance = radius * (1.25 + (index % 3) * 0.5);
      const position = mapped.position.clone().addScaledVector(frame.tangent, Math.cos(angle) * distance).addScaledVector(frame.bitangent, Math.sin(angle) * distance).normalize().multiplyScalar(RADIUS + 0.42);
      const size = Math.max(0.12, radius * 0.22); const height = Math.max(size * 1.4, size + Math.abs(num(building.capacity)) * 0.006);
      const mesh = new THREE.Mesh(new THREE.BoxGeometry(size, height, size), new THREE.MeshStandardMaterial({ color: 0xb8aa91, roughness: 0.84 }));
      mesh.position.copy(position); mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), position.clone().normalize()); mesh.userData = { type: 'building', data: building, settlement }; group.add(mesh);
    }
  }
  globe.add(group);
}
function addAgents(visual) {
  const agents = Array.isArray(visual.agents) ? visual.agents : []; if (!agents.length) return;
  const size = Math.max(0.08, RADIUS / Math.max(mapper.width, mapper.height) * 0.5);
  const mesh = new THREE.InstancedMesh(new THREE.SphereGeometry(size, 8, 6), new THREE.MeshStandardMaterial({ color: 0xffd166, roughness: 0.65 }), agents.length);
  const matrix = new THREE.Matrix4();
  agents.forEach((agent, index) => {
    const position = Array.isArray(agent.position) ? agent.position : null; if (!position || position.length < 2) return;
    const cell = mapper.cellMap.get(`${position[0]}:${position[1]}`); const mapped = mapper.toWorld(position[0], position[1], cell?.terrain?.elevation_m || 0, 0.5);
    matrix.setPosition(mapped.position.x, mapped.position.y, mapped.position.z); mesh.setMatrixAt(index, matrix);
  });
  mesh.instanceMatrix.needsUpdate = true; mesh.userData = { type: 'agents', data: agents, total: agents.length }; globe.add(mesh);
}
function extractWildlifePosition(item) {
  if (Array.isArray(item?.position) && item.position.length >= 2) return item.position;
  if (Array.isArray(item?.location) && item.location.length >= 2) return item.location;
  if (Number.isFinite(Number(item?.x)) && Number.isFinite(Number(item?.y))) return [Number(item.x), Number(item.y)];
  return null;
}
function addWildlife(visual) {
  const wildlife = (Array.isArray(visual.wildlife) ? visual.wildlife : []).map((item) => ({ item, position: extractWildlifePosition(item) })).filter((entry) => entry.position);
  if (!wildlife.length) return;
  const size = Math.max(0.07, RADIUS / Math.max(mapper.width, mapper.height) * 0.34);
  const mesh = new THREE.InstancedMesh(new THREE.SphereGeometry(size, 7, 5), new THREE.MeshStandardMaterial({ color: 0xa8d18b, roughness: 0.9 }), wildlife.length);
  const matrix = new THREE.Matrix4();
  wildlife.forEach((entry, index) => { const [x, y] = entry.position; const cell = mapper.cellMap.get(`${x}:${y}`); const mapped = mapper.toWorld(x, y, cell?.terrain?.elevation_m || 0, 0.38); matrix.setPosition(mapped.position.x, mapped.position.y, mapped.position.z); mesh.setMatrixAt(index, matrix); });
  mesh.instanceMatrix.needsUpdate = true; mesh.userData = { type: 'wildlife', data: wildlife.map((entry) => entry.item), total: wildlife.length }; globe.add(mesh);
}
function renderMetrics(visual) {
  const metrics = visual.metrics || {}; const cells = flattenCells(visual.planet); const land = cells.filter((cell) => cell.terrain?.land).length;
  const people = Array.isArray(visual.agents) ? visual.agents.length : 0; const wildlife = Array.isArray(visual.wildlife) ? visual.wildlife.length : 0;
  const settlements = Array.isArray(visual.settlements) ? visual.settlements.length : 0; const buildings = (visual.settlements || []).reduce((sum, item) => sum + (item.buildings?.length || 0), 0);
  const resourceText = visual.resources && typeof visual.resources === 'object' ? Object.entries(visual.resources).filter(([, value]) => ['number', 'string'].includes(typeof value)).slice(0, 5).map(([key, value]) => `${key}=${value}`).join(', ') : '';
  metricsEl.textContent = [`tick ${num(visual.tick)} · land ${land}/${cells.length}`, `people ${people} · wildlife ${wildlife}`, `settlements ${settlements} · buildings ${buildings}`, resourceText ? `resources: ${resourceText}` : 'resources: persistent state available', metrics.population != null ? `engine population ${metrics.population}` : ''].filter(Boolean).join('\n');
}
function inspect(hit) {
  const object = hit?.object; if (!object) return;
  if (object.userData.type === 'settlement') { const data = object.userData.data; inspectorEl.textContent = `${data.name || 'Settlement'} · ${data.kind || 'settlement'} · population ${num(data.population)} · buildings ${data.buildings?.length || 0}`; return; }
  if (object.userData.type === 'building') { const building = object.userData.data; inspectorEl.textContent = `Building ${building.kind || 'structure'} · condition ${(num(building.condition) * 100).toFixed(0)}% · capacity ${num(building.capacity)}`; return; }
  if (object.userData.type === 'agents') { const agent = object.userData.data[hit.instanceId ?? 0]; if (agent) inspectorEl.textContent = `${agent.name || 'Citizen'} · ${agent.life_state || 'citizen'} · health ${(num(agent.health) * 100).toFixed(0)}% · wealth ${num(agent.wealth).toFixed(2)}`; return; }
  if (object.userData.type === 'wildlife') { const item = object.userData.data[hit.instanceId ?? 0]; if (item) inspectorEl.textContent = `Wildlife ${item.species_id || item.species || item.organism_id || 'organism'}`; return; }
  if (object.userData.type === 'terrain') { const point = hit.point.clone().normalize(); inspectorEl.textContent = `Planet surface · latitude ${(Math.asin(point.y) / DEG).toFixed(2)}° · longitude ${(Math.atan2(point.z, point.x) / DEG).toFixed(2)}°`; }
}
function rebuild(visual) { clearWorld(); makeOcean(); buildTerrain(visual.planet); addSettlements(visual); addAgents(visual); addWildlife(visual); makeAtmosphere(); renderMetrics(visual); lastRenderTick = num(visual.tick); }
async function fetchState() { const response = await fetch(`${API_BASE}/world/state`, { headers: { Accept: 'application/json' }, cache: 'no-store' }); if (!response.ok) throw new Error(`world/state ${response.status}`); return response.json(); }
async function refresh(force = false) { const visual = await fetchState(); state = visual; if (force || num(visual.tick) !== lastRenderTick) rebuild(visual); else renderMetrics(visual); const backend = visual.persistence?.configured ? 'PostgreSQL persistent' : 'in-memory'; const accelerator = navigator.gpu ? 'WebGPU available · WebGL active' : 'WebGL active'; setStatus(`Genesis LIVE · tick ${visual.tick} · ${backend} · ${accelerator}`); }
async function initialize() { setStatus('Checking authoritative Genesis backend…'); const health = await fetch(`${API_BASE}/health`, { cache: 'no-store' }); if (!health.ok) throw new Error(`health ${health.status}`); const healthJson = await health.json(); if (healthJson.status !== 'ok') throw new Error('Genesis backend is not ready'); await refresh(true); }
async function stepOnce() { if (stepping) return; stepping = true; try { const count = Number(speedEl.value); const response = await fetch(`${API_BASE}/step?count=${count}`, { method: 'POST' }); if (!response.ok) throw new Error(`step ${response.status}`); await refresh(true); } catch (error) { console.error(error); setStatus(`Simulation error: ${error.message}`); } finally { stepping = false; } }
playButton.addEventListener('click', () => { playing = true; });
pauseButton.addEventListener('click', async () => { playing = false; try { await fetch(`${API_BASE}/checkpoint`, { method: 'POST' }); } catch (error) { console.error(error); } });
saveButton.addEventListener('click', async () => { try { const response = await fetch(`${API_BASE}/checkpoint`, { method: 'POST' }); if (!response.ok) throw new Error(`checkpoint ${response.status}`); setStatus(`Genesis checkpoint saved · tick ${state?.tick ?? 'unknown'}`); } catch (error) { setStatus(`Save failed: ${error.message}`); } });
canvas.addEventListener('pointerdown', (event) => { const rect = canvas.getBoundingClientRect(); pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1; pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1; raycaster.setFromCamera(pointer, camera); const hits = raycaster.intersectObjects(globe.children, true); if (hits.length) inspect(hits[0]); });
window.addEventListener('resize', () => { camera.aspect = window.innerWidth / window.innerHeight; camera.updateProjectionMatrix(); renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, MAX_PIXEL_RATIO)); renderer.setSize(window.innerWidth, window.innerHeight, false); });
setInterval(() => { if (playing) stepOnce(); }, 900);
renderer.setAnimationLoop(() => { globe.rotation.y = clock.getElapsedTime() * 0.012; controls.update(); sun.position.set(RADIUS * 4.0, RADIUS * 3.0, RADIUS * 2.5); renderer.render(scene, camera); });
initialize().catch((error) => { console.error(error); setStatus(`3D world unavailable: ${error.message}`); metricsEl.textContent = 'The authoritative Genesis backend could not be loaded.'; });
