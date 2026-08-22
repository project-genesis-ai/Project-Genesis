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
const setStatus = (text) => { statusEl.textContent = text; };

const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, powerPreference: 'high-performance' });
renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.5));
renderer.setSize(window.innerWidth, window.innerHeight, false);
renderer.outputColorSpace = THREE.SRGBColorSpace;

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x02040a);
const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 4000);
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.08;
controls.minDistance = 8;
controls.maxDistance = 1800;
controls.maxPolarAngle = Math.PI * 0.49;
scene.add(new THREE.HemisphereLight(0x9ec5ff, 0x182016, 1.7));
const sun = new THREE.DirectionalLight(0xffffff, 2.3);
sun.position.set(80, 180, 80);
scene.add(sun);

const world = new THREE.Group();
scene.add(world);
const raycaster = new THREE.Raycaster();
const pointer = new THREE.Vector2();
let state = null;
let bounds = null;
let playing = false;
let stepping = false;
let lastRenderTick = -1;
let mapper = null;

function disposeObject(object) {
  object.traverse((node) => {
    node.geometry?.dispose();
    if (Array.isArray(node.material)) node.material.forEach((material) => material.dispose());
    else node.material?.dispose();
  });
}
function clearWorld() { while (world.children.length) disposeObject(world.remove(world.children[0])); }
function num(value, fallback = 0) { const parsed = Number(value); return Number.isFinite(parsed) ? parsed : fallback; }
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
function biomeColor(cell) {
  if (!cell?.terrain?.land) return new THREE.Color(0x173b69);
  const name = String(cell.biome?.name || '').toLowerCase();
  if (name.includes('desert')) return new THREE.Color(0xc9a86b);
  if (name.includes('forest') || name.includes('wood')) return new THREE.Color(0x236b4e);
  if (name.includes('tundra') || name.includes('ice')) return new THREE.Color(0xa8c2ce);
  if (name.includes('grass') || name.includes('savanna')) return new THREE.Color(0x5a8c45);
  if (name.includes('wetland')) return new THREE.Color(0x477b63);
  return new THREE.Color(0x6c8d50);
}
function makeCoordMapper(cells) {
  const xs = cells.map((cell) => cell.x); const ys = cells.map((cell) => cell.y);
  const minX = Math.min(...xs); const maxX = Math.max(...xs); const minY = Math.min(...ys); const maxY = Math.max(...ys);
  const width = Math.max(1, maxX - minX + 1); const height = Math.max(1, maxY - minY + 1);
  const scale = 72 / Math.max(width, height);
  bounds = { minX, maxX, minY, maxY, width, height, scale };
  return (x, y, elevation = 0) => [(num(x) - (minX + maxX) / 2) * scale, num(elevation) * 0.012, (num(y) - (minY + maxY) / 2) * scale];
}
function buildTerrain(planet) {
  const cells = flattenCells(planet);
  if (!cells.length) throw new Error('Authoritative Genesis planet has no cells');
  const toWorld = makeCoordMapper(cells);
  const cellMap = new Map(cells.map((cell) => [`${cell.x}:${cell.y}`, cell]));
  const step = Math.max(1, Math.ceil(Math.max(bounds.width, bounds.height) / 96));
  const sampled = cells.filter((cell) => step === 1 || ((cell.x - bounds.minX) % step === 0 && (cell.y - bounds.minY) % step === 0));
  const positions = []; const colors = []; const indices = []; const indexMap = new Map();
  sampled.forEach((cell, index) => { const [x, y, z] = toWorld(cell.x, cell.y, cell.terrain?.elevation_m); positions.push(x, y, z); const color = biomeColor(cell); colors.push(color.r, color.g, color.b); indexMap.set(`${cell.x}:${cell.y}`, index); });
  for (const cell of sampled) { const a = indexMap.get(`${cell.x}:${cell.y}`); const b = indexMap.get(`${cell.x + step}:${cell.y}`); const c = indexMap.get(`${cell.x}:${cell.y + step}`); const d = indexMap.get(`${cell.x + step}:${cell.y + step}`); if (a != null && b != null && c != null && d != null) indices.push(a, b, c, b, d, c); }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
  geometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));
  geometry.setIndex(indices); geometry.computeVertexNormals();
  const terrainMesh = new THREE.Mesh(geometry, new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.94, metalness: 0.02 }));
  terrainMesh.userData = { type: 'terrain', cellMap }; world.add(terrainMesh);
  const waterPositions = [];
  sampled.filter((cell) => !cell.terrain?.land).forEach((cell) => { const [x, y, z] = toWorld(cell.x, cell.y, 0); waterPositions.push(x, y + 0.05, z); });
  if (waterPositions.length) { const waterGeometry = new THREE.BufferGeometry(); waterGeometry.setAttribute('position', new THREE.Float32BufferAttribute(waterPositions, 3)); world.add(new THREE.Points(waterGeometry, new THREE.PointsMaterial({ color: 0x3a89d6, size: Math.max(0.55, bounds.scale * 1.6), transparent: true, opacity: 0.5 }))); }
  const riverMaterial = new THREE.LineBasicMaterial({ color: 0x55b8ff, transparent: true, opacity: 0.85 });
  for (const river of planet.rivers || []) { const downstream = river.downstream || []; const c1 = cellMap.get(`${river.x}:${river.y}`); const c2 = cellMap.get(`${downstream[0]}:${downstream[1]}`); const [x1, y1, z1] = toWorld(river.x, river.y, c1?.terrain?.elevation_m || 0); const [x2, y2, z2] = toWorld(downstream[0], downstream[1], c2?.terrain?.elevation_m || 0); const riverGeometry = new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(x1, y1 + 0.15, z1), new THREE.Vector3(x2, y2 + 0.15, z2)]); world.add(new THREE.Line(riverGeometry, riverMaterial)); }
  const vegetationCells = sampled.filter((cell) => cell.terrain?.land && num(cell.biome?.vegetation_productivity) > 0.45);
  if (vegetationCells.length) { const count = Math.min(2000, vegetationCells.length); const mesh = new THREE.InstancedMesh(new THREE.ConeGeometry(Math.max(0.18, bounds.scale * 0.18), Math.max(0.7, bounds.scale * 0.9), 5), new THREE.MeshStandardMaterial({ color: 0x2d7a4f, roughness: 1 }), count); const matrix = new THREE.Matrix4(); for (let i = 0; i < count; i += 1) { const cell = vegetationCells[i]; const [x, y, z] = toWorld(cell.x, cell.y, cell.terrain?.elevation_m); const scale = 0.55 + Math.min(1, num(cell.biome?.vegetation_productivity)) * 0.9; matrix.compose(new THREE.Vector3(x, y + bounds.scale * 0.4, z), new THREE.Quaternion(), new THREE.Vector3(scale, scale, scale)); mesh.setMatrixAt(i, matrix); } mesh.instanceMatrix.needsUpdate = true; mesh.userData = { type: 'vegetation', count: vegetationCells.length }; world.add(mesh); }
  controls.target.set(0, 0, 0);
  const distance = Math.max(90, Math.max(bounds.width, bounds.height) * bounds.scale * 1.9);
  camera.position.set(distance * 0.8, distance * 0.85, distance); controls.update();
  return { toWorld, cellMap };
}
function addSettlements(visual, localMapper) {
  const group = new THREE.Group();
  for (const settlement of visual.settlements || []) { const location = settlement.location || [0, 0]; const cell = localMapper.cellMap.get(`${location[0]}:${location[1]}`); const [x, y, z] = localMapper.toWorld(location[0], location[1], cell?.terrain?.elevation_m || 0); const radius = Math.max(0.45, Math.min(2.2, 0.45 + Math.log10(1 + num(settlement.population)) * 0.55)); const marker = new THREE.Mesh(new THREE.CylinderGeometry(radius, radius * 0.85, 0.8, 10), new THREE.MeshStandardMaterial({ color: 0xd39b55, roughness: 0.8 })); marker.position.set(x, y + 0.45, z); marker.userData = { type: 'settlement', data: settlement }; group.add(marker); (settlement.buildings || []).forEach((building, index) => { const angle = index * 2.399963; const distance = radius * (1.5 + (index % 3) * 0.55); const size = Math.max(0.18, bounds.scale * 0.22); const mesh = new THREE.Mesh(new THREE.BoxGeometry(size, size * 1.7, size), new THREE.MeshStandardMaterial({ color: 0xb7a184, roughness: 0.95 })); mesh.position.set(x + Math.cos(angle) * distance, y + size * 0.85, z + Math.sin(angle) * distance); mesh.userData = { type: 'building', data: building, settlement }; group.add(mesh); }); }
  world.add(group);
}
function addAgents(visual, localMapper) {
  const agents = visual.agents || []; if (!agents.length) return; const count = Math.min(3000, agents.length); const size = Math.max(0.12, bounds.scale * 0.16); const mesh = new THREE.InstancedMesh(new THREE.SphereGeometry(size, 6, 5), new THREE.MeshStandardMaterial({ color: 0xffd166, roughness: 0.7 }), count); const matrix = new THREE.Matrix4();
  for (let i = 0; i < count; i += 1) { const agent = agents[i]; const position = agent.position || [0, 0]; const cell = localMapper.cellMap.get(`${position[0]}:${position[1]}`); const [x, y, z] = localMapper.toWorld(position[0], position[1], cell?.terrain?.elevation_m || 0); matrix.setPosition(x, y + size, z); mesh.setMatrixAt(i, matrix); }
  mesh.instanceMatrix.needsUpdate = true; mesh.userData = { type: 'agents', data: agents.slice(0, count), total: agents.length }; world.add(mesh);
}
function extractWildlifePosition(item) { if (Array.isArray(item?.position) && item.position.length >= 2) return item.position; if (Array.isArray(item?.location) && item.location.length >= 2) return item.location; if (Number.isFinite(Number(item?.x)) && Number.isFinite(Number(item?.y))) return [Number(item.x), Number(item.y)]; return null; }
function addWildlife(visual, localMapper) {
  const wildlife = (visual.wildlife || []).map((item) => ({ item, position: extractWildlifePosition(item) })).filter((entry) => entry.position); if (!wildlife.length) return; const count = Math.min(2500, wildlife.length); const size = Math.max(0.09, bounds.scale * 0.11); const mesh = new THREE.InstancedMesh(new THREE.SphereGeometry(size, 5, 4), new THREE.MeshStandardMaterial({ color: 0xa6d189, roughness: 1 }), count); const matrix = new THREE.Matrix4();
  for (let i = 0; i < count; i += 1) { const [wx, wz] = wildlife[i].position; const cell = localMapper.cellMap.get(`${wx}:${wz}`); const [x, y, z] = localMapper.toWorld(wx, wz, cell?.terrain?.elevation_m || 0); matrix.setPosition(x, y + size, z); mesh.setMatrixAt(i, matrix); }
  mesh.instanceMatrix.needsUpdate = true; mesh.userData = { type: 'wildlife', data: wildlife.slice(0, count).map((entry) => entry.item), total: wildlife.length }; world.add(mesh);
}
function formatResources(resources) { if (!resources || typeof resources !== 'object') return 'resources: n/a'; const values = Object.entries(resources).filter(([, value]) => ['number', 'string'].includes(typeof value)).slice(0, 5); return values.length ? `resources: ${values.map(([key, value]) => `${key}=${value}`).join(', ')}` : 'resources: persistent state available'; }
function renderMetrics(visual) { const metrics = visual.metrics || {}; const cells = flattenCells(visual.planet); const land = cells.filter((cell) => cell.terrain?.land).length; const people = Array.isArray(visual.agents) ? visual.agents.length : 0; const wildlife = Array.isArray(visual.wildlife) ? visual.wildlife.length : 0; const settlements = Array.isArray(visual.settlements) ? visual.settlements.length : 0; const buildings = (visual.settlements || []).reduce((sum, item) => sum + (item.buildings?.length || 0), 0); metricsEl.textContent = `tick ${num(visual.tick)} · land ${land}/${cells.length}\npeople ${people} · wildlife ${wildlife}\nsettlements ${settlements} · buildings ${buildings}\n${formatResources(visual.resources)}${metrics.population != null ? `\nengine population ${metrics.population}` : ''}`; }
function inspect(hit) {
  if (!hit?.object) return; const object = hit.object;
  if (object.userData.type === 'settlement') { const data = object.userData.data; inspectorEl.textContent = `${data.name} · ${data.kind} · population ${data.population} · buildings ${data.buildings?.length || 0}`; return; }
  if (object.userData.type === 'building') { const building = object.userData.data; inspectorEl.textContent = `Building ${building.kind} · condition ${(num(building.condition) * 100).toFixed(0)}% · capacity ${building.capacity}`; return; }
  if (object.userData.type === 'agents') { const agent = object.userData.data[hit.instanceId ?? 0]; if (agent) inspectorEl.textContent = `${agent.name} · ${agent.life_state || 'citizen'} · health ${(num(agent.health) * 100).toFixed(0)}% · wealth ${num(agent.wealth).toFixed(2)}`; return; }
  if (object.userData.type === 'wildlife') { const item = object.userData.data[hit.instanceId ?? 0]; if (item) inspectorEl.textContent = `Wildlife ${item.species_id || item.species || item.organism_id || 'organism'}`; return; }
  if (object.userData.type === 'terrain') { const point = hit.point; let best = null; let bestDistance = Infinity; for (const cell of object.userData.cellMap.values()) { const [x, , z] = mapper.toWorld(cell.x, cell.y, cell.terrain?.elevation_m || 0); const distance = (x - point.x) ** 2 + (z - point.z) ** 2; if (distance < bestDistance) { bestDistance = distance; best = cell; } } if (best) inspectorEl.textContent = `Terrain ${best.x},${best.y} · elevation ${num(best.terrain?.elevation_m).toFixed(1)}m · ${best.biome?.name || 'unknown biome'} · ${best.terrain?.land ? 'land' : 'water'}`; }
}
function rebuild(visual) { clearWorld(); mapper = buildTerrain(visual.planet); addSettlements(visual, mapper); addAgents(visual, mapper); addWildlife(visual, mapper); renderMetrics(visual); lastRenderTick = num(visual.tick); }
async function fetchState() { const response = await fetch(`${API_BASE}/world/state`, { headers: { Accept: 'application/json' }, cache: 'no-store' }); if (!response.ok) throw new Error(`world/state ${response.status}`); return response.json(); }
async function refresh(force = false) { const visual = await fetchState(); state = visual; if (force || num(visual.tick) !== lastRenderTick) rebuild(visual); else renderMetrics(visual); const backend = visual.persistence?.configured ? 'PostgreSQL persistent' : 'in-memory'; const accelerator = navigator.gpu ? 'WebGPU available · WebGL active' : 'WebGL active'; setStatus(`Genesis LIVE · tick ${visual.tick} · ${backend} · ${accelerator}`); }
async function initialize() { setStatus('Checking authoritative Genesis backend…'); const health = await fetch(`${API_BASE}/health`, { cache: 'no-store' }); if (!health.ok) throw new Error(`health ${health.status}`); const healthJson = await health.json(); if (healthJson.status !== 'ok') throw new Error('Genesis backend is not ready'); await refresh(true); }
async function stepOnce() { if (stepping) return; stepping = true; try { const count = Number(speedEl.value); const response = await fetch(`${API_BASE}/step?count=${count}`, { method: 'POST' }); if (!response.ok) throw new Error(`step ${response.status}`); await refresh(true); } catch (error) { console.error(error); setStatus(`Simulation error: ${error.message}`); } finally { stepping = false; } }
playButton.addEventListener('click', () => { playing = true; });
pauseButton.addEventListener('click', async () => { playing = false; try { await fetch(`${API_BASE}/checkpoint`, { method: 'POST' }); } catch (error) { console.error(error); } });
saveButton.addEventListener('click', async () => { try { const response = await fetch(`${API_BASE}/checkpoint`, { method: 'POST' }); if (!response.ok) throw new Error(`checkpoint ${response.status}`); setStatus(`Genesis checkpoint saved · tick ${state?.tick ?? 'unknown'}`); } catch (error) { setStatus(`Save failed: ${error.message}`); } });
canvas.addEventListener('pointerdown', (event) => { const rect = canvas.getBoundingClientRect(); pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1; pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1; raycaster.setFromCamera(pointer, camera); const hits = raycaster.intersectObjects(world.children, true); if (hits.length) inspect(hits[0]); });
window.addEventListener('resize', () => { camera.aspect = window.innerWidth / window.innerHeight; camera.updateProjectionMatrix(); renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.5)); renderer.setSize(window.innerWidth, window.innerHeight, false); });
setInterval(() => { if (playing) stepOnce(); }, 900);
renderer.setAnimationLoop(() => { controls.update(); const tick = num(state?.tick); const phase = (tick % 240) / 240; const angle = phase * Math.PI * 2; sun.position.set(Math.cos(angle) * 160, Math.sin(angle) * 160 + 30, Math.sin(angle) * 100); sun.intensity = Math.max(0.25, 1.2 + Math.sin(angle) * 1.0); renderer.render(scene, camera); });
initialize().catch((error) => { console.error(error); setStatus(`3D world unavailable: ${error.message}`); metricsEl.textContent = 'The authoritative Genesis backend could not be loaded.'; });
