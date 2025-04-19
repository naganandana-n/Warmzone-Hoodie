import * as THREE from 'https://unpkg.com/three@0.126.1/build/three.module.js';
import { GLTFLoader } from 'https://unpkg.com/three@0.126.1/examples/jsm/loaders/GLTFLoader.js';
import { OrbitControls } from 'https://unpkg.com/three@0.126.1/examples/jsm/controls/OrbitControls.js';

let scene, camera, renderer, model, controls;

let currentModelIndex = 0;
const modelFiles = ['hoodie1.gltf', 'hoodie2.gltf']; // Add more as needed

// Only compute these once
let fixedCameraZ = null;
let fixedTargetY = null;

init();
loadModel(modelFiles[currentModelIndex]);

function init() {
  scene = new THREE.Scene();
  scene.background = new THREE.Color(0xf0f0f0);

  camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 100);
  camera.position.set(0, 1.5, 3);

  const canvas = document.getElementById('threeCanvas');
  renderer = new THREE.WebGLRenderer({ canvas: canvas, antialias: true });
  renderer.setSize(canvas.clientWidth, canvas.clientHeight, false);

  controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.05;
  controls.enableZoom = false;
  controls.minPolarAngle = Math.PI / 2;
  controls.maxPolarAngle = Math.PI / 2;

  controls.enabled = false;

  // Lighting
  const hemiLight = new THREE.HemisphereLight(0xffffff, 0x444444, 1);
  scene.add(hemiLight);

  const dirLight = new THREE.DirectionalLight(0xffffff, 1.5);
  dirLight.position.set(5, 10, 7.5);
  scene.add(dirLight);

  const ambientLight = new THREE.AmbientLight(0xffffff, 0.3);
  scene.add(ambientLight);

  window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
  });

  // Hook up the model switch button
  const btn = document.getElementById('switchModelBtn');
  if (btn) {
    btn.addEventListener('click', () => {
      const prevRotation = model ? model.rotation.y : 0;
      currentModelIndex = (currentModelIndex + 1) % modelFiles.length;
      loadModel(modelFiles[currentModelIndex], prevRotation);
    });
  }

  animate();
}

function loadModel(file = 'hoodie1.gltf', preserveRotation = 0) {
  const loader = new GLTFLoader();

  loader.load(file, (gltf) => {
    const newModel = gltf.scene;

    if (model) scene.remove(model);
    model = newModel;

    // Fix: reset scale and transforms
    model.scale.set(1, 1, 1);
    model.rotation.set(0, preserveRotation, 0);
    model.updateMatrixWorld(true);

    scene.add(model);
    model.rotation.y = preserveRotation;

    const box = new THREE.Box3().setFromObject(model);
    const size = box.getSize(new THREE.Vector3());
    const center = box.getCenter(new THREE.Vector3());

    model.position.x += (model.position.x - center.x);
    model.position.y += (model.position.y - center.y);
    model.position.z += (model.position.z - center.z);

    // Only compute camera distance and Y-target once
    if (fixedCameraZ === null) {
      const maxDim = Math.max(size.x, size.y, size.z);
      const fov = camera.fov * (Math.PI / 180);
      fixedCameraZ = maxDim / (2 * Math.tan(fov / 2)) * 1.5;
    }
    if (fixedTargetY === null) {
      fixedTargetY = size.y * 0.001;
    }

    camera.position.z = fixedCameraZ;
    camera.position.y = fixedTargetY;
    controls.target.set(0, fixedTargetY, 0);
    controls.update();
  });
  console.log('Loading model:', file);
}

function animate() {
  requestAnimationFrame(animate);
  if (model) {
    model.rotation.y += 0.005;
  }
  controls.update();
  renderer.render(scene, camera);
}