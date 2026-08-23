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
const UP = new THREE.Vector3(0, 1, 0);

const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, powerPreference: 'high-performance', logarithmicDepthBuffer: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, MAX_PIXEL_RATIO));
renderer.setSize(window.innerWidth, window.innerHeight, false);
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.0;

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x01030a);
const camera = new THREE.PerspectiveCamera(40, window.innerWidth / window.innerHeight, 0.05, 5000);
camera.position.set(0, RADIUS * 0.34, RADIUS * 2.25);
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.06;
controls.minDistance = RADIUS * 1.05;
controls.maxDistance = RADIUS * 7;
controls.enablePan = false;
controls.target.set(0, 0, 0);
scene.add(new THREE.HemisphereLight(0xa8ceff, 0x182016, 1.15));
const sun = new THREE.DirectionalLight(0xffffff, 3.0);
sun.position.set(160, 110, 100);
scene.add(sun);

const globe = new THREE.Group();
scene.add(globe);
const raycaster = new THREE.Raycaster();
const pointer = new THREE.Vector2();
let state = null;
let mapper = null;
let lastRenderTick = -1;
let playing = false;
let stepping = false;

const setStatus = (text) => { statusEl.textContent = text; };
const num = (value, fallback = 0) => { const n = Number(value); return Number.isFinite(n) ? n : fallback; };

function disposeObject(object) {
  object.traverse((node) => {
    node.geometry?.dispose();
    if (Array.isArray(node.material)) node.material.forEach((m) => m.dispose());
    else node.material?.dispose();
  });
}
function clearWorld() { while (globe.children.length) disposeObject(globe.remove(globe.children[0])); }
function flattenCells(planet) {
  const out = [];
  const rows = Array.isArray(planet?.cells) ? planet.cells : [];
  for (let y = 0; y < rows.length; y += 1) {
    const row = Array.isArray(rows[y]) ? rows[y] : [];
    for (let x = 0; x < row.length; x += 1) {
      const cell = row[x];
      if (cell?.terrain) out.push({ ...cell, x: num(cell.terrain.x, x), y: num(cell.terrain.y, y) });
    }
  }
  return out;
}
function createMapper(cells) {
  const xs = cells.map((c) => c.x); const ys = cells.map((c) => c.y);
  const minX = Math.min(...xs); const maxX = Math.max(...xs); const minY = Math.min(...ys); const maxY = Math.max(...ys);
  const width = Math.max(1, maxX - minX + 1); const height = Math.max(1, maxY - minY + 1);
  const elevations = cells.filter((c) => c.terrain?.land).map((c) => num(c.terrain?.elevation_m));
  const minElevation = elevations.length ? Math.min(...elevations) : 0; const maxElevation = elevations.length ? Math.max(...elevations) : minElevation;
  const elevationSpan = Math.max(1, maxElevation - minElevation);
  const cellMap = new Map(cells.map((c) => [`${c.x}:${c.y}`, c]));
  const point = (x, y, elevation = 0, lift = 0) => {
    const lon = (((num(x) - minX) + 0.5) / width) * Math.PI * 2 - Math.PI;
    const lat = Math.PI * 0.5 - (((num(y) - minY) + 0.5) / height) * Math.PI;
    const ratio = Math.max(0, Math.min(1, (num(elevation) - minElevation) / elevationSpan));
    const radius = RADIUS + ratio * RADIUS * 0.065 + lift;
    const cosLat = Math.cos(lat);
    const normal = new THREE.Vector3(cosLat * Math.cos(lon), Math.sin(lat), cosLat * Math.sin(lon)).normalize();
    return { normal, position: normal.clone().multiplyScalar(radius), lon, lat };
  };
  const corner = (x, y, elevation = 0, lift = 0) => {
    const lon = ((x - minX) / width) * Math.PI * 2 - Math.PI;
    const lat = Math.PI * 0.5 - ((y - minY) / height) * Math.PI;
    const ratio = Math.max(0, Math.min(1, (num(elevation) - minElevation) / elevationSpan));
    const radius = RADIUS + ratio * RADIUS * 0.065 + lift;
    const cosLat = Math.cos(lat);
    const normal = new THREE.Vector3(cosLat * Math.cos(lon), Math.sin(lat), cosLat * Math.sin(lon)).normalize();
    return { normal, position: normal.clone().multiplyScalar(radius) };
  };
  return { minX, maxX, minY, maxY, width, height, cellMap, point, corner };
}
function biomeColor(cell) {
  if (!cell?.terrain?.land) return new THREE.Color(0x0b3e70);
  const name = String(cell.biome?.name || '').toLowerCase(); const productivity = Math.max(0, Math.min(1, num(cell.biome?.vegetation_productivity)));
  if (name.includes('desert')) return new THREE.Color().setHSL(0.105, 0.52, 0.58);
  if (name.includes('forest') || name.includes('wood')) return new THREE.Color().setHSL(0.34, 0.48, 0.30 + productivity * 0.08);
  if (name.includes('tundra') || name.includes('ice')) return new THREE.Color().setHSL(0.54, 0.20, 0.72);
  if (name.includes('grass') || name.includes('savanna')) return new THREE.Color().setHSL(0.235, 0.42, 0.40 + productivity * 0.08);
  if (name.includes('wetland')) return new THREE.Color().setHSL(0.43, 0.38, 0.35);
  return new THREE.Color().setHSL(0.255, 0.34, 0.39 + productivity * 0.07);
}
function makeOcean() {
  const material = new THREE.MeshPhysicalMaterial({ color: 0x0a4476, roughness: 0.28, metalness: 0.02, clearcoat: 0.7, clearcoatRoughness: 0.18 });
  const mesh = new THREE.Mesh(new THREE.SphereGeometry(RADIUS * 0.998, 128, 96), material);
  mesh.userData = { type: 'ocean' }; globe.add(mesh);
}
function makeAtmosphere() {
  const material = new THREE.ShaderMaterial({
    transparent: true, depthWrite: false, side: THREE.BackSide, blending: THREE.AdditiveBlending,
    uniforms: { glowColor: { value: new THREE.Color(0x4ba7ff) }, strength: { value: 0.62 } },
    vertexShader: 'varying vec3 vNormal; varying vec3 vWorld; void main(){vNormal=normalize(normalMatrix*normal);vec4 wp=modelMatrix*vec4(position,1.0);vWorld=wp.xyz;gl_Position=projectionMatrix*viewMatrix*wp;}',
    fragmentShader: 'uniform vec3 glowColor;uniform float strength;varying vec3 vNormal;varying vec3 vWorld;void main(){vec3 viewDir=normalize(cameraPosition-vWorld);float rim=pow(1.0-max(dot(vNormal,viewDir),0.0),3.0);gl_FragColor=vec4(glowColor,rim*strength);}',
  });
  globe.add(new THREE.Mesh(new THREE.SphereGeometry(RADIUS * 1.035, 128, 96), material));
}
function buildTerrain(planet) {
  const cells = flattenCells(planet); if (!cells.length) throw new Error('Authoritative Genesis planet has no cells');
  mapper = createMapper(cells);
  const positions = []; const colors = []; const indices = []; const vertexMap = new Map();
  const landCells = cells.filter((cell) => cell.terrain?.land);
  const addVertex = (x, y, elevation, color) => {
    const key = `${x}:${y}`; let index = vertexMap.get(key);
    if (index == null) {
      const mapped = mapper.corner(x, y, elevation, 0.075); index = positions.length / 3;
      positions.push(mapped.position.x, mapped.position.y, mapped.position.z); colors.push(color.r, color.g, color.b); vertexMap.set(key, index);
    }
    return index;
  };
  for (const cell of landCells) {
    const color = biomeColor(cell); const e = num(cell.terrain?.elevation_m); const x = cell.x; const y = cell.y;
    const a = addVertex(x, y, e, color); const b = addVertex(x + 1, y, e, color); const c = addVertex(x, y + 1, e, color); const d = addVertex(x + 1, y + 1, e, color);
    indices.push(a, b, c, b, d, c);
  }
  const geometry = new THREE.BufferGeometry(); geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3)); geometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3)); geometry.setIndex(indices); geometry.computeVertexNormals();
  const terrain = new THREE.Mesh(geometry, new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.9, metalness: 0.01 }));
  terrain.userData = { type: 'terrain', cellMap: mapper.cellMap }; globe.add(terrain);
  const riverPositions = [];
  for (const river of Array.isArray(planet.rivers) ? planet.rivers : []) {
    const downstream = Array.isArray(river.downstream) ? river.downstream : []; if (downstream.length < 2) continue;
    const aCell = mapper.cellMap.get(`${river.x}:${river.y}`); const bCell = mapper.cellMap.get(`${downstream[0]}:${downstream[1]}`); if (!aCell || !bCell) continue;
    const a = mapper.point(river.x, river.y, aCell.terrain?.elevation_m || 0, 0.16).position; const b = mapper.point(downstream[0], downstream[1], bCell.terrain?.elevation_m || 0, 0.16).position;
    riverPositions.push(a.x, a.y, a.z, b.x, b.y, b.z);
  }
  if (riverPositions.length) { const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(riverPositions, 3)); globe.add(new THREE.LineSegments(g, new THREE.LineBasicMaterial({ color: 0x72d3ff, transparent: true, opacity: 0.72 }))); }
}
function localFrame(normal) { let tangent = new THREE.Vector3(0, 1, 0); if (Math.abs(normal.dot(tangent)) > 0.92) tangent = new THREE.Vector3(1, 0, 0); tangent.projectOnPlane(normal).normalize(); return { tangent, bitangent: new THREE.Vector3().crossVectors(normal, tangent).normalize() }; }
function addSettlements(visual) {
  const group = new THREE.Group();
  for (const settlement of Array.isArray(visual.settlements) ? visual.settlements : []) {
    const location = Array.isArray(settlement.location) ? settlement.location : null; if (!location || location.length < 2) continue;
    const cell = mapper.cellMap.get(`${location[0]}:${location[1]}`); const mapped = mapper.point(location[0], location[1], cell?.terrain?.elevation_m || 0, 0.42); const frame = localFrame(mapped.normal);
    const population = Math.max(0, num(settlement.population)); const radius = Math.max(0.35, Math.min(1.8, 0.42 + Math.log10(1 + population) * 0.34));
    const marker = new THREE.Mesh(new THREE.CylinderGeometry(radius, radius * 0.9, radius * 0.55, 14), new THREE.MeshStandardMaterial({ color: 0xe2a65f, roughness: 0.7 })); marker.position.copy(mapped.position); marker.quaternion.setFromUnitVectors(UP, mapped.normal); marker.userData = { type: 'settlement', data: settlement }; group.add(marker);
    for (const [index, building] of (settlement.buildings || []).entries()) {
      const angle = index * 2.3999632297; const distance = radius * (1.2 + (index % 3) * 0.45); const position = mapped.position.clone().addScaledVector(frame.tangent, Math.cos(angle) * distance).addScaledVector(frame.bitangent, Math.sin(angle) * distance).normalize().multiplyScalar(RADIUS + 0.52);
      const size = Math.max(0.12, radius * 0.22); const height = Math.max(size * 1.4, size + Math.abs(num(building.capacity)) * 0.006); const mesh = new THREE.Mesh(new THREE.BoxGeometry(size, height, size), new THREE.MeshStandardMaterial({ color: 0xc3b59b, roughness: 0.82 }));
      mesh.position.copy(position); mesh.quaternion.setFromUnitVectors(UP, position.clone().normalize()); mesh.userData = { type: 'building', data: building, settlement }; group.add(mesh);
    }
  }
  globe.add(group);
}
function addAgents(visual) {
  const agents = Array.isArray(visual.agents) ? visual.agents : []; if (!agents.length) return;
  const size = Math.max(0.08, RADIUS / Math.max(mapper.width, mapper.height) * 0.42); const mesh = new THREE.InstancedMesh(new THREE.SphereGeometry(size, 8, 6), new THREE.MeshStandardMaterial({ color: 0xffd166, roughness: 0.65 }), agents.length); const matrix = new THREE.Matrix4();
  agents.forEach((agent, index) => { const position = Array.isArray(agent.position) ? agent.position : null; if (!position || position.length < 2) return; const cell = mapper.cellMap.get(`${position[0]}:${position[1]}`); const mapped = mapper.point(position[0], position[1], cell?.terrain?.elevation_m || 0, 0.7); matrix.setPosition(mapped.position.x, mapped.position.y, mapped.position.z); mesh.setMatrixAt(index, matrix); });
  mesh.instanceMatrix.needsUpdate = true; mesh.userData = { type: 'agents', data: agents, total: agents.length }; globe.add(mesh);
}
function extractWildlifePosition(item) { if (Array.isArray(item?.position) && item.position.length >= 2) return item.position; if (Array.isArray(item?.location) && item.location.length >= 2) return item.location; if (Number.isFinite(Number(item?.x)) && Number.isFinite(Number(item?.y))) return [Number(item.x), Number(item.y)]; return null; }
function addWildlife(visual) {
  const wildlife = (Array.isArray(visual.wildlife) ? visual.wildlife : []).map((item) => ({ item, position: extractWildlifePosition(item) })).filter((x) => x.position); if (!wildlife.length) return;
  const size = Math.max(0.07, RADIUS / Math.max(mapper.width, mapper.height) * 0.3); const mesh = new THREE.InstancedMesh(new THREE.SphereGeometry(size, 7, 5), new THREE.MeshStandardMaterial({ color: 0xa8d18b, roughness: 0.9 }), wildlife.length); const matrix = new THREE.Matrix4();
  wildlife.forEach((entry, index) => { const [x, y] = entry.position; const cell = mapper.cellMap.get(`${x}:${y}`); const mapped = mapper.point(x, y, cell?.terrain?.elevation_m || 0, 0.52); matrix.setPosition(mapped.position.x, mapped.position.y, mapped.position.z); mesh.setMatrixAt(index, matrix); });
  mesh.instanceMatrix.needsUpdate = true; mesh.userData = { type: 'wildlife', data: wildlife.map((x) => x.item), total: wildlife.length }; globe.add(mesh);
}
function renderMetrics(visual) {
  const metrics = visual.metrics || {}; const cells = flattenCells(visual.planet); const land = cells.filter((cell) => cell.terrain?.land).length; const people = Array.isArray(visual.agents) ? visual.agents.length : 0; const wildlife = Array.isArray(visual.wildlife) ? visual.wildlife.length : 0; const settlements = Array.isArray(visual.settlements) ? visual.settlements.length : 0; const buildings = (visual.settlements || []).reduce((sum, item) => sum + (item.buildings?.length || 0), 0);
  const resourceText = visual.resources && typeof visual.resources === 'object' ? Object.entries(visual.resources).filter(([, v]) => ['number', 'string'].includes(typeof v)).slice(0, 5).map(([k, v]) => `${k}=${v}`).join(', ') : '';
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
renderer.setAnimationLoop(() => { controls.update(); renderer.render(scene, camera); });
initialize().catch((error) => { console.error(error); setStatus(`3D world unavailable: ${error.message}`); metricsEl.textContent = 'The authoritative Genesis backend could not be loaded.'; });
