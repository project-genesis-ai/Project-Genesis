import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.179.1/build/three.module.js';
import { OrbitControls } from 'https://cdn.jsdelivr.net/npm/three@0.179.1/examples/jsm/controls/OrbitControls.js';

const API_BASE = window.GENESIS_API_BASE || 'https://project-genesis-caat.onrender.com';
const canvas = document.querySelector('#genesis-canvas');
const statusEl = document.querySelector('#status');
const metricsEl = document.querySelector('#metrics');

const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, powerPreference: 'high-performance' });
renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.75));
renderer.setSize(window.innerWidth, window.innerHeight, false);
renderer.outputColorSpace = THREE.SRGBColorSpace;

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x02040a);
const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 2000);
camera.position.set(110, 105, 150);
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.08;
controls.minDistance = 45;
controls.maxDistance = 520;
controls.maxPolarAngle = Math.PI * 0.49;

scene.add(new THREE.HemisphereLight(0x9ec5ff, 0x182016, 1.8));
const sun = new THREE.DirectionalLight(0xffffff, 2.4);
sun.position.set(80, 160, 80);
scene.add(sun);

const world = new THREE.Group();
scene.add(world);
const raycaster = new THREE.Raycaster();
const pointer = new THREE.Vector2();
let terrainMesh = null;
let terrainCells = [];
let selected = null;
let latestSnapshot = null;

function setStatus(text) { statusEl.textContent = text; }
function finiteNumber(v, fallback = 0) { return Number.isFinite(Number(v)) ? Number(v) : fallback; }
function clamp(v, lo, hi) { return Math.min(hi, Math.max(lo, v)); }

function flattenCells(snapshot) {
  const rows = Array.isArray(snapshot?.cells) ? snapshot.cells : [];
  const cells = [];
  for (let y = 0; y < rows.length; y += 1) {
    const row = Array.isArray(rows[y]) ? rows[y] : [];
    for (let x = 0; x < row.length; x += 1) {
      const cell = row[x];
      const terrain = cell?.terrain;
      if (!terrain) continue;
      cells.push({ ...cell, _row: y, _col: x, x: finiteNumber(terrain.x, x), y: finiteNumber(terrain.y, y) });
    }
  }
  return cells;
}

function clearWorld() {
  while (world.children.length) {
    const child = world.children.pop();
    child.geometry?.dispose();
    if (Array.isArray(child.material)) child.material.forEach((m) => m.dispose());
    else child.material?.dispose();
  }
  terrainMesh = null;
  terrainCells = [];
}

function colorForCell(cell) {
  const terrain = cell.terrain || {};
  if (!terrain.land) return new THREE.Color(0x173b69);
  const biomeName = String(cell.biome?.name || '').toLowerCase();
  if (biomeName.includes('desert')) return new THREE.Color(0xc9a86b);
  if (biomeName.includes('forest')) return new THREE.Color(0x236b4e);
  if (biomeName.includes('tundra')) return new THREE.Color(0xa8c2ce);
  if (biomeName.includes('grass')) return new THREE.Color(0x5a8c45);
  return new THREE.Color(0x6c8d50);
}

function buildTerrain(snapshot) {
  clearWorld();
  const cells = flattenCells(snapshot);
  if (!cells.length) throw new Error('Genesis snapshot contains no terrain cells');
  terrainCells = cells;
  const xs = cells.map((c) => c.x); const ys = cells.map((c) => c.y);
  const minX = Math.min(...xs); const maxX = Math.max(...xs);
  const minY = Math.min(...ys); const maxY = Math.max(...ys);
  const width = maxX - minX + 1; const height = maxY - minY + 1;
  const step = Math.max(1, Math.ceil(Math.max(width, height) / 96));
  const sampled = cells.filter((c) => c.x % step === 0 && c.y % step === 0 || step === 1);
  const spacing = 2.0;
  const geom = new THREE.BufferGeometry();
  const positions = []; const colors = [];
  const indices = [];
  const columns = new Map();
  const scale = 0.012;
  sampled.forEach((cell, i) => {
    const px = (cell.x - (minX + maxX) / 2) * spacing * step / Math.max(1, width / 64);
    const pz = (cell.y - (minY + maxY) / 2) * spacing * step / Math.max(1, height / 64);
    const elevation = finiteNumber(cell.terrain?.elevation_m) * scale;
    positions.push(px, elevation, pz);
    const c = colorForCell(cell); colors.push(c.r, c.g, c.b);
    columns.set(`${cell.x}:${cell.y}`, i);
  });
  const sampledLookup = new Map(sampled.map((c, i) => [`${c.x}:${c.y}`, i]));
  for (const cell of sampled) {
    const a = sampledLookup.get(`${cell.x}:${cell.y}`);
    const b = sampledLookup.get(`${cell.x + step}:${cell.y}`);
    const c = sampledLookup.get(`${cell.x}:${cell.y + step}`);
    const d = sampledLookup.get(`${cell.x + step}:${cell.y + step}`);
    if (a == null || b == null || c == null || d == null) continue;
    indices.push(a, b, c, b, d, c);
  }
  geom.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
  geom.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));
  geom.setIndex(indices);
  geom.computeVertexNormals();
  terrainMesh = new THREE.Mesh(geom, new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.94, metalness: 0.02, flatShading: false }));
  world.add(terrainMesh);

  const waterCells = sampled.filter((c) => !(c.terrain?.land));
  if (waterCells.length) {
    const waterGeom = new THREE.BufferGeometry(); const p = [];
    for (const cell of waterCells) {
      const px = (cell.x - (minX + maxX) / 2) * spacing * step / Math.max(1, width / 64);
      const pz = (cell.y - (minY + maxY) / 2) * spacing * step / Math.max(1, height / 64);
      p.push(px, 0, pz);
    }
    waterGeom.setAttribute('position', new THREE.Float32BufferAttribute(p, 3));
    world.add(new THREE.Points(waterGeom, new THREE.PointsMaterial({ color: 0x3a89d6, size: 1.8, sizeAttenuation: true, transparent: true, opacity: 0.38 })));
  }

  controls.target.set(0, 0, 0);
  camera.position.set(Math.max(width, height) * 0.95, Math.max(width, height) * 0.9, Math.max(width, height) * 1.25);
  controls.update();
}

function renderMetrics(snapshot) {
  const rows = Array.isArray(snapshot?.cells) ? snapshot.cells : [];
  const cells = flattenCells(snapshot);
  const land = cells.filter((c) => c.terrain?.land).length;
  const ocean = cells.length - land;
  const agents = Number(snapshot?.metrics?.agents ?? snapshot?.agents_count ?? NaN);
  const tick = finiteNumber(snapshot?.tick, 0);
  metricsEl.textContent = `tick ${tick} · terrain ${rows.length}×${rows[0]?.length || 0}\nland ${land} · ocean ${ocean}${Number.isFinite(agents) ? `\nagents ${agents}` : ''}`;
}

function normalizeSnapshot(payload) {
  if (payload?.snapshot) return payload.snapshot;
  if (payload?.planet_snapshot) return payload.planet_snapshot;
  if (payload?.data?.snapshot) return payload.data.snapshot;
  if (payload?.cells) return payload;
  throw new Error('Genesis API returned no recognized PlanetSnapshot payload');
}

async function fetchGenesis() {
  const urls = [`${API_BASE}/world`, `${API_BASE}/snapshot`, `${API_BASE}/genesis`, `${API_BASE}/planet`];
  let lastError = null;
  for (const url of urls) {
    try {
      const response = await fetch(url, { headers: { Accept: 'application/json' } });
      if (!response.ok) { lastError = new Error(`${response.status} ${response.statusText}`); continue; }
      return normalizeSnapshot(await response.json());
    } catch (error) { lastError = error; }
  }
  throw lastError || new Error('Genesis API is unavailable');
}

async function initialize() {
  setStatus('Checking Genesis backend…');
  const health = await fetch(`${API_BASE}/health`, { headers: { Accept: 'application/json' } });
  if (!health.ok) throw new Error(`Health check failed: ${health.status}`);
  const healthJson = await health.json();
  if (healthJson?.status !== 'ok') throw new Error('Genesis backend is not ready');
  setStatus('Loading authoritative Genesis world…');
  latestSnapshot = await fetchGenesis();
  buildTerrain(latestSnapshot);
  renderMetrics(latestSnapshot);
  setStatus(`Genesis world live · tick ${latestSnapshot.tick}`);
}

canvas.addEventListener('pointerdown', (event) => {
  const rect = canvas.getBoundingClientRect();
  pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
  pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
  if (!terrainMesh) return;
  raycaster.setFromCamera(pointer, camera);
  const hit = raycaster.intersectObject(terrainMesh, false)[0];
  if (!hit || hit.instanceId != null) return;
  selected?.material?.emissive?.setHex?.(0x000000);
  selected = hit.object;
});

window.addEventListener('resize', () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.75));
  renderer.setSize(window.innerWidth, window.innerHeight, false);
});

renderer.setAnimationLoop(() => {
  controls.update();
  renderer.render(scene, camera);
});

initialize().catch((error) => {
  console.error(error);
  setStatus(`3D world unavailable: ${error.message}`);
  metricsEl.textContent = 'Backend health is reachable, but no existing world-data endpoint is exposed yet.';
});
