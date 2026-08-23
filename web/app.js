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
const MAX_PIXEL_RATIO = 1.75;
const DEG = Math.PI / 180;
const AXIAL_TILT = 23.4 * DEG;
const UP = new THREE.Vector3(0, 1, 0);
const clock = new THREE.Clock();

const renderer = new THREE.WebGLRenderer({
  canvas,
  antialias: true,
  powerPreference: 'high-performance',
  logarithmicDepthBuffer: true,
});
renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, MAX_PIXEL_RATIO));
renderer.setSize(window.innerWidth, window.innerHeight, false);
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.08;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x01030a);
const camera = new THREE.PerspectiveCamera(38, window.innerWidth / window.innerHeight, 0.05, 5000);
camera.position.set(0, RADIUS * 0.28, RADIUS * 2.35);
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.055;
controls.minDistance = RADIUS * 1.025;
controls.maxDistance = RADIUS * 7.5;
controls.enablePan = false;
controls.target.set(0, 0, 0);

scene.add(new THREE.HemisphereLight(0xb9d9ff, 0x182014, 1.15));
const sun = new THREE.DirectionalLight(0xfff5df, 3.7);
sun.position.set(140, 95, 85);
sun.castShadow = true;
sun.shadow.mapSize.set(1024, 1024);
scene.add(sun);
const fill = new THREE.DirectionalLight(0x6baeff, 0.55);
fill.position.set(-100, -30, -80);
scene.add(fill);

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
let animationFrame = 0;

const num = (value, fallback = 0) => {
  const n = Number(value);
  return Number.isFinite(n) ? n : fallback;
};
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
const setStatus = (text) => { statusEl.textContent = text; };

function disposeObject(object) {
  object.traverse((node) => {
    node.geometry?.dispose();
    if (Array.isArray(node.material)) node.material.forEach((m) => m.dispose());
    else node.material?.dispose();
  });
}

function clearWorld() {
  while (globe.children.length) {
    const child = globe.children.pop();
    disposeObject(child);
  }
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
  const landElevations = cells.filter((c) => c.terrain?.land).map((c) => num(c.terrain.elevation_m));
  const minElevation = landElevations.length ? Math.min(...landElevations) : 0;
  const maxElevation = landElevations.length ? Math.max(...landElevations) : 1;
  const span = Math.max(1, maxElevation - Math.min(0, minElevation));
  const elevationRadius = Math.min(RADIUS * 0.16, Math.max(0.55, RADIUS * 0.13));

  function spherical(x, y, elevation = 0, lift = 0) {
    const lon = ((x - minX) / width) * Math.PI * 2 - Math.PI;
    const lat = Math.PI * 0.5 - ((y - minY) / height) * Math.PI;
    const normalized = clamp((num(elevation) - Math.min(0, minElevation)) / span, 0, 1);
    const radius = RADIUS + normalized * elevationRadius + lift;
    const cosLat = Math.cos(lat);
    const normal = new THREE.Vector3(cosLat * Math.cos(lon), Math.sin(lat), cosLat * Math.sin(lon)).normalize();
    return { normal, position: normal.clone().multiplyScalar(radius), lon, lat };
  }

  return { minX, maxX, minY, maxY, width, height, cellMap, minElevation, maxElevation, elevationRadius, spherical };
}

function biomeName(cell) {
  return String(cell?.biome?.name || '').toLowerCase();
}

function biomeColor(cell) {
  const name = biomeName(cell);
  const productivity = clamp(num(cell?.biome?.vegetation_productivity), 0, 1);
  if (name.includes('desert')) return new THREE.Color().setHSL(0.105, 0.48, 0.54 + productivity * 0.08);
  if (name.includes('tundra') || name.includes('ice') || name.includes('snow')) return new THREE.Color().setHSL(0.57, 0.18, 0.78);
  if (name.includes('forest') || name.includes('wood')) return new THREE.Color().setHSL(0.33, 0.54, 0.25 + productivity * 0.10);
  if (name.includes('savanna')) return new THREE.Color().setHSL(0.17, 0.45, 0.43 + productivity * 0.08);
  if (name.includes('grass')) return new THREE.Color().setHSL(0.25, 0.48, 0.38 + productivity * 0.10);
  if (name.includes('wetland')) return new THREE.Color().setHSL(0.43, 0.44, 0.31);
  if (name.includes('mountain')) return new THREE.Color().setHSL(0.09, 0.18, 0.45);
  return new THREE.Color().setHSL(0.27, 0.38, 0.36 + productivity * 0.08);
}

function makeOcean() {
  const geometry = new THREE.SphereGeometry(RADIUS, 192, 128);
  const material = new THREE.MeshPhysicalMaterial({
    color: 0x07518e,
    roughness: 0.22,
    metalness: 0.02,
    clearcoat: 0.9,
    clearcoatRoughness: 0.12,
    transmission: 0.02,
  });
  const ocean = new THREE.Mesh(geometry, material);
  ocean.userData = { type: 'ocean' };
  globe.add(ocean);
}

function makeAtmosphere() {
  const material = new THREE.ShaderMaterial({
    transparent: true,
    depthWrite: false,
    side: THREE.BackSide,
    blending: THREE.AdditiveBlending,
    uniforms: { glowColor: { value: new THREE.Color(0x49a7ff) }, strength: { value: 0.72 } },
    vertexShader: `varying vec3 vNormal; varying vec3 vWorld; void main(){vNormal=normalize(normalMatrix*normal);vec4 p=modelMatrix*vec4(position,1.0);vWorld=p.xyz;gl_Position=projectionMatrix*viewMatrix*p;}`,
    fragmentShader: `uniform vec3 glowColor; uniform float strength; varying vec3 vNormal; varying vec3 vWorld; void main(){vec3 viewDir=normalize(cameraPosition-vWorld);float rim=pow(1.0-max(dot(vNormal,viewDir),0.0),3.15);gl_FragColor=vec4(glowColor,rim*strength);}`,
  });
  globe.add(new THREE.Mesh(new THREE.SphereGeometry(RADIUS * 1.045, 192, 128), material));
}

function makeStars() {
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
  scene.add(new THREE.Points(geometry, new THREE.PointsMaterial({ color: 0xbad7ff, size: 1.2, sizeAttenuation: true, transparent: true, opacity: 0.65 })));
}

function mulberry32(seed) {
  return function random() {
    let t = seed += 0x6D2B79F5;
    t = Math.imul(t ^ t >>> 15, t | 1);
    t ^= t + Math.imul(t ^ t >>> 7, t | 61);
    return ((t ^ t >>> 14) >>> 0) / 4294967296;
  };
}

function vertexElevation(cellMap, x, y) {
  const values = [];
  for (let oy = -1; oy <= 0; oy += 1) {
    for (let ox = -1; ox <= 0; ox += 1) {
      const cell = cellMap.get(`${x + ox}:${y + oy}`);
      if (cell?.terrain?.land) values.push(num(cell.terrain.elevation_m));
    }
  }
  if (!values.length) return 0;
  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function buildTerrain(planet) {
  const cells = flattenCells(planet);
  if (!cells.length) throw new Error('Authoritative Genesis planet has no cells');
  mapper = makeMapper(cells);
  const { cellMap } = mapper;
  const positions = [];
  const indices = [];
  const vertexIds = new Map();

  function getVertexId(x, y) {
    const key = `${x}:${y}`;
    const existing = vertexIds.get(key);
    if (existing !== undefined) return existing;
    const mapped = mapper.spherical(x, y, vertexElevation(cellMap, x, y));
    const id = positions.length / 3;
    positions.push(mapped.position.x, mapped.position.y, mapped.position.z);
    vertexIds.set(key, id);
    return id;
  }

  for (const cell of cells) {
    if (!cell.terrain?.land) continue;
    const a = getVertexId(cell.x, cell.y);
    const b = getVertexId(cell.x + 1, cell.y);
    const c = getVertexId(cell.x, cell.y + 1);
    const d = getVertexId(cell.x + 1, cell.y + 1);
    indices.push(a, c, b, b, c, d);
  }

  const vertexColors = new Float32Array(positions.length);
  const colorCounts = new Float32Array(positions.length / 3);
  for (const cell of cells) {
    if (!cell.terrain?.land) continue;
    const color = biomeColor(cell);
    for (const [vx, vy] of [[cell.x, cell.y], [cell.x + 1, cell.y], [cell.x, cell.y + 1], [cell.x + 1, cell.y + 1]]) {
      const id = vertexIds.get(`${vx}:${vy}`);
      if (id === undefined) continue;
      vertexColors[id * 3] += color.r;
      vertexColors[id * 3 + 1] += color.g;
      vertexColors[id * 3 + 2] += color.b;
      colorCounts[id] += 1;
    }
  }
  for (let i = 0; i < colorCounts.length; i += 1) {
    const count = Math.max(1, colorCounts[i]);
    vertexColors[i * 3] /= count;
    vertexColors[i * 3 + 1] /= count;
    vertexColors[i * 3 + 2] /= count;
  }

  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
  geometry.setAttribute('color', new THREE.Float32BufferAttribute(vertexColors, 3));
  geometry.setIndex(indices);
  geometry.computeVertexNormals();
  const terrain = new THREE.Mesh(geometry, new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.86, metalness: 0, flatShading: false, side: THREE.FrontSide }));
  terrain.castShadow = true;
  terrain.receiveShadow = true;
  terrain.userData = { type: 'terrain', cellMap };
  globe.add(terrain);

  addTerrainDetail(cells);
  addRivers(planet);
}

function addTerrainDetail(cells) {
  const forestCells = cells.filter((cell) => {
    const name = biomeName(cell);
    return cell.terrain?.land && (name.includes('forest') || name.includes('wood'));
  });
  if (!forestCells.length) return;

  const maxInstances = Math.min(9000, forestCells.length * 4);
  const trees = new THREE.InstancedMesh(makeTreeGeometry(), new THREE.MeshStandardMaterial({ color: 0x2f6f3b, roughness: 0.9 }), maxInstances);
  trees.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
  const matrix = new THREE.Matrix4();
  const rng = mulberry32(hashCells(forestCells));
  let index = 0;
  for (const cell of forestCells) {
    const base = mapper.spherical(cell.x + 0.5, cell.y + 0.5, num(cell.terrain.elevation_m), 0.35);
    const frame = localFrame(base.normal);
    const count = 1 + Math.floor(rng() * 5);
    for (let i = 0; i < count && index < maxInstances; i += 1) {
      const angle = rng() * Math.PI * 2;
      const distance = (rng() * 0.42 + 0.08) * (RADIUS / Math.max(mapper.width, mapper.height)) * 2.4;
      const pos = base.position.clone().addScaledVector(frame.tangent, Math.cos(angle) * distance).addScaledVector(frame.bitangent, Math.sin(angle) * distance).normalize().multiplyScalar(base.position.length() + 0.34);
      const scale = 0.42 + rng() * 0.55;
      const quaternion = new THREE.Quaternion().setFromUnitVectors(UP, pos.clone().normalize());
      matrix.compose(pos, quaternion, new THREE.Vector3(scale, scale * (1.15 + rng() * 0.4), scale));
      trees.setMatrixAt(index, matrix);
      index += 1;
    }
  }
  trees.count = index;
  trees.instanceMatrix.needsUpdate = true;
  trees.userData = { type: 'vegetation', biome: 'forest' };
  globe.add(trees);
}

function hashCells(cells) {
  let hash = 2166136261;
  for (const cell of cells) {
    hash ^= (cell.x * 73856093) ^ (cell.y * 19349663);
    hash = Math.imul(hash, 16777619);
  }
  return hash >>> 0;
}

function makeTreeGeometry() {
  const trunk = new THREE.CylinderGeometry(0.07, 0.10, 0.52, 6);
  const crown = new THREE.ConeGeometry(0.34, 0.82, 7);
  crown.translate(0, 0.58, 0);
  trunk.translate(0, 0.26, 0);
  const merged = mergeGeometries([trunk, crown]);
  trunk.dispose();
  crown.dispose();
  return merged;
}

function mergeGeometries(geometries) {
  const positions = [];
  const normals = [];
  const indices = [];
  let offset = 0;
  for (const geometry of geometries) {
    const position = geometry.getAttribute('position');
    const normal = geometry.getAttribute('normal');
    for (let i = 0; i < position.count; i += 1) {
      positions.push(position.getX(i), position.getY(i), position.getZ(i));
      normals.push(normal.getX(i), normal.getY(i), normal.getZ(i));
    }
    const index = geometry.getIndex();
    if (index) for (let i = 0; i < index.count; i += 1) indices.push(index.getX(i) + offset);
    else for (let i = 0; i < position.count; i += 1) indices.push(i + offset);
    offset += position.count;
  }
  const result = new THREE.BufferGeometry();
  result.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
  result.setAttribute('normal', new THREE.Float32BufferAttribute(normals, 3));
  result.setIndex(indices);
  return result;
}

function addRivers(planet) {
  const segments = Array.isArray(planet?.rivers) ? planet.rivers : [];
  if (!segments.length) return;
  const points = [];
  for (const river of segments) {
    const downstream = Array.isArray(river.downstream) ? river.downstream : [];
    if (downstream.length < 2) continue;
    const aCell = mapper.cellMap.get(`${river.x}:${river.y}`);
    const bCell = mapper.cellMap.get(`${downstream[0]}:${downstream[1]}`);
    if (!aCell || !bCell) continue;
    points.push(
      mapper.spherical(river.x + 0.5, river.y + 0.5, num(aCell.terrain?.elevation_m), 0.28).position,
      mapper.spherical(downstream[0] + 0.5, downstream[1] + 0.5, num(bCell.terrain?.elevation_m), 0.28).position,
    );
  }
  if (!points.length) return;
  const positions = new Float32Array(points.length * 3);
  points.forEach((p, i) => { positions[i * 3] = p.x; positions[i * 3 + 1] = p.y; positions[i * 3 + 2] = p.z; });
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  const rivers = new THREE.LineSegments(geometry, new THREE.LineBasicMaterial({ color: 0x69c8ff, transparent: true, opacity: 0.78 }));
  rivers.userData = { type: 'rivers' };
  globe.add(rivers);
}

function localFrame(normal) {
  let tangent = new THREE.Vector3(0, 1, 0);
  if (Math.abs(normal.dot(tangent)) > 0.92) tangent = new THREE.Vector3(1, 0, 0);
  tangent.projectOnPlane(normal).normalize();
  return { tangent, bitangent: new THREE.Vector3().crossVectors(normal, tangent).normalize() };
}

function addSettlements(visual) {
  const group = new THREE.Group();
  group.userData = { type: 'civilization' };
  for (const settlement of Array.isArray(visual.settlements) ? visual.settlements : []) {
    const location = Array.isArray(settlement.location) ? settlement.location : null;
    if (!location || location.length < 2) continue;
    const cell = mapper.cellMap.get(`${location[0]}:${location[1]}`);
    const mapped = mapper.spherical(location[0] + 0.5, location[1] + 0.5, num(cell?.terrain?.elevation_m), 0.48);
    const frame = localFrame(mapped.normal);
    const population = Math.max(0, num(settlement.population));
    const radius = clamp(0.28 + Math.log10(1 + population) * 0.26, 0.32, 1.35);
    const marker = new THREE.Mesh(new THREE.CylinderGeometry(radius, radius * 0.92, radius * 0.42, 16), new THREE.MeshStandardMaterial({ color: 0xd59b5e, roughness: 0.75 }));
    marker.position.copy(mapped.position);
    marker.quaternion.setFromUnitVectors(UP, mapped.normal);
    marker.userData = { type: 'settlement', data: settlement };
    group.add(marker);

    const buildings = Array.isArray(settlement.buildings) ? settlement.buildings : [];
    for (let index = 0; index < buildings.length; index += 1) {
      const building = buildings[index];
      const angle = index * 2.3999632297;
      const distance = radius * (1.05 + (index % 4) * 0.38);
      const position = mapped.position.clone().addScaledVector(frame.tangent, Math.cos(angle) * distance).addScaledVector(frame.bitangent, Math.sin(angle) * distance).normalize().multiplyScalar(RADIUS + 0.52);
      const size = Math.max(0.08, radius * 0.17);
      const height = Math.max(size * 1.3, size + Math.abs(num(building.capacity)) * 0.004);
      const mesh = new THREE.Mesh(new THREE.BoxGeometry(size, height, size), new THREE.MeshStandardMaterial({ color: 0xc5b99e, roughness: 0.82 }));
      mesh.position.copy(position);
      mesh.quaternion.setFromUnitVectors(UP, position.clone().normalize());
      mesh.userData = { type: 'building', data: building, settlement };
      group.add(mesh);
    }
  }
  globe.add(group);
}

function addAgents(visual) {
  const agents = Array.isArray(visual.agents) ? visual.agents : [];
  if (!agents.length) return;
  const size = Math.max(0.055, RADIUS / Math.max(mapper.width, mapper.height) * 0.32);
  const mesh = new THREE.InstancedMesh(new THREE.SphereGeometry(size, 8, 6), new THREE.MeshStandardMaterial({ color: 0xffd166, roughness: 0.7 }), agents.length);
  const matrix = new THREE.Matrix4();
  agents.forEach((agent, index) => {
    const position = Array.isArray(agent.position) ? agent.position : null;
    if (!position || position.length < 2) return;
    const cell = mapper.cellMap.get(`${position[0]}:${position[1]}`);
    const mapped = mapper.spherical(position[0] + 0.5, position[1] + 0.5, num(cell?.terrain?.elevation_m), 0.66);
    matrix.compose(mapped.position, new THREE.Quaternion().setFromUnitVectors(UP, mapped.normal), new THREE.Vector3(1, 1, 1));
    mesh.setMatrixAt(index, matrix);
  });
  mesh.instanceMatrix.needsUpdate = true;
  mesh.userData = { type: 'agents', data: agents };
  globe.add(mesh);
}

function renderWorld(visual) {
  if (!visual?.planet) throw new Error('Authoritative visualization payload missing planet');
  clearWorld();
  makeOcean();
  buildTerrain(visual.planet);
  addSettlements(visual);
  addAgents(visual);
  makeAtmosphere();
}

function updateHud(visual) {
  const metrics = visual?.metrics || {};
  const tick = num(visual?.tick);
  const population = num(metrics.population ?? visual?.agents?.length);
  const settlements = Array.isArray(visual?.settlements) ? visual.settlements.length : 0;
  const buildings = Array.isArray(visual?.settlements) ? visual.settlements.reduce((sum, settlement) => sum + (Array.isArray(settlement.buildings) ? settlement.buildings.length : 0), 0) : 0;
  const wildlife = Array.isArray(visual?.wildlife) ? visual.wildlife.length : 0;
  const database = visual?.persistence?.configured ? 'PostgreSQL persistent' : 'memory only';
  metricsEl.textContent = [
    `tick ${tick} · ${database} · WebGL2 ${renderer.capabilities.isWebGL2 ? 'active' : 'fallback'}`,
    `people ${population.toLocaleString()} · wildlife ${wildlife.toLocaleString()}`,
    `settlements ${settlements.toLocaleString()} · buildings ${buildings.toLocaleString()}`,
    `resources ${visual?.resources ? 'authoritative state available' : '—'}`,
  ].join('\n');
}

function inspectObject(object) {
  const data = object?.userData || {};
  if (!data.type) return;
  if (data.type === 'terrain') inspectorEl.textContent = 'Terrain surface reconstructed from authoritative elevation and biome cells. No visible simulation grid or hardcoded geography.';
  else if (data.type === 'ocean') inspectorEl.textContent = 'Ocean · continuous spherical water surface derived from the authoritative planet mask.';
  else if (data.type === 'settlement') {
    const settlement = data.data || {};
    inspectorEl.textContent = `Settlement ${settlement.name || settlement.id || 'unknown'} · population ${num(settlement.population).toLocaleString()} · buildings ${(settlement.buildings || []).length}`;
  } else if (data.type === 'building') {
    const building = data.data || {};
    inspectorEl.textContent = `Building ${building.id || 'unknown'} · kind ${building.kind || 'unknown'} · capacity ${num(building.capacity)} · condition ${num(building.condition).toFixed(2)}`;
  } else if (data.type === 'agents') {
    inspectorEl.textContent = `Citizens rendered from authoritative agent state · ${data.data?.length || 0} active agents in payload.`;
  }
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
  state = visual;
  updateHud(visual);
  setStatus(`Genesis LIVE · tick ${tick} · ${visual.persistence?.configured ? 'PostgreSQL persistent' : 'persistence unavailable'}`);
  return visual;
}

async function stepSimulation(count) {
  if (stepping) return;
  stepping = true;
  try {
    await fetchJson(`/step?count=${encodeURIComponent(count)}`, { method: 'POST' });
    await refreshWorld();
  } catch (error) {
    setStatus(`Simulation error: ${error.message}`);
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

playButton.addEventListener('click', () => setPlaying(!playing));
saveButton.addEventListener('click', async () => {
  try {
    const result = await fetchJson('/checkpoint', { method: 'POST' });
    setStatus(`Saved authoritative checkpoint · tick ${result.tick}`);
  } catch (error) {
    setStatus(`Save failed: ${error.message}`);
  }
});

canvas.addEventListener('pointerdown', (event) => {
  const rect = canvas.getBoundingClientRect();
  pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
  pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
  raycaster.setFromCamera(pointer, camera);
  const hits = raycaster.intersectObjects(globe.children, true);
  const hit = hits.find((item) => item.object?.userData?.type);
  if (hit) inspectObject(hit.object);
});

window.addEventListener('resize', () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight, false);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, MAX_PIXEL_RATIO));
});

async function boot() {
  setStatus('Checking authoritative Genesis backend…');
  try {
    const health = await fetchJson('/health');
    if (health.status !== 'ok') throw new Error('Genesis backend health check failed');
    await refreshWorld(true);
  } catch (error) {
    setStatus(`Backend connection failed · ${error.message}`);
  }
}

function animate() {
  animationFrame = requestAnimationFrame(animate);
  const delta = Math.min(clock.getDelta(), 0.1);
  controls.update();
  if (playing && !stepping) {
    const ticksPerSecond = speedValue() * 2;
    const expected = delta * ticksPerSecond;
    if (expected >= 1) void stepSimulation(Math.min(1000, Math.max(1, Math.floor(expected))));
  }
  renderer.render(scene, camera);
}

makeStars();
setPlaying(false);
animate();
void boot();
window.addEventListener('beforeunload', () => cancelAnimationFrame(animationFrame));
