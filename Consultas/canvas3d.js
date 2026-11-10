// ==========================================
// MOTOR 3D MULTI-ESTACIÓN DE S.I.N.D.D.I. (Three.js) - PERFECCIONADO
// ==========================================

const active3DCanvasIds = ['canvas-2', 'canvas-4', 'canvas-7'];

window.scenes = window.scenes || {};
window.renderers = window.renderers || {};
window.cameras = window.cameras || {};
window.updateRegistries = window.updateRegistries || {};

let selectedMesh = null;
const raycaster = new THREE.Raycaster();
const mouse = new THREE.Vector2();

active3DCanvasIds.forEach(canvasId => {
    const container = document.getElementById(canvasId);
    if (!container) return;

    const existingViewport = document.getElementById(`viewport-${canvasId}`);
    if (existingViewport) existingViewport.remove();

    const viewport = document.createElement('div');
    viewport.id = `viewport-${canvasId}`;
    viewport.style.width = '100%';
    viewport.style.height = canvasId === 'canvas-4' ? 'calc(100% - 30px)' : 'calc(100% - 65px)';
    viewport.style.background = '#000';
    viewport.style.position = 'relative';
    viewport.style.borderRadius = '4px';
    viewport.style.overflow = 'hidden';
    viewport.setAttribute('data-canvas-id', canvasId);
    container.appendChild(viewport);

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(75, viewport.clientWidth / viewport.clientHeight || 1, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'high-performance' });

    renderer.setSize(viewport.clientWidth, viewport.clientHeight);
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    viewport.appendChild(renderer.domElement);

    // --- INTEGRACIÓN DE ORBIT CONTROLS ---
    let controls = null;
    if (THREE.OrbitControls) {
        controls = new THREE.OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true;
        controls.dampingFactor = 0.05;
        controls.maxDistance = 50;
        controls.minDistance = 0.5;
    }

    const ambientLight = new THREE.AmbientLight(0xffffff, 0.7);
    scene.add(ambientLight);

    const pointLight = new THREE.PointLight(0x38bdf8, 2, 50);
    pointLight.position.set(5, 5, 5);
    pointLight.castShadow = true;
    scene.add(pointLight);

    camera.position.z = 4;

    window.scenes[canvasId] = scene;
    window.renderers[canvasId] = renderer;
    window.cameras[canvasId] = camera;
    window.updateRegistries[canvasId] = [];

    if (controls) {
        window.updateRegistries[canvasId].push(() => controls.update());
    }

    // --- INTERACCIÓN DRAG & DROP Y RAYCASTING ENTRE CANVAS ---
    renderer.domElement.addEventListener('pointerdown', (event) => {
        const rect = renderer.domElement.getBoundingClientRect();
        mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
        mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

        raycaster.setFromCamera(mouse, camera);
        const intersects = raycaster.intersectObjects(scene.children, true);

        if (intersects.length > 0) {
            selectedMesh = intersects[0].object;
            selectedMesh.userData.sourceCanvas = canvasId;
            console.log(`🎯 Objeto seleccionado en ${canvasId}:`, selectedMesh);
        }
    });

    renderer.domElement.addEventListener('pointerup', (event) => {
        if (!selectedMesh) return;

        const x = event.clientX;
        const y = event.clientY;

        active3DCanvasIds.forEach(targetId => {
            if (targetId === selectedMesh.userData.sourceCanvas) return;
            const targetEl = document.getElementById(`viewport-${targetId}`);
            if (!targetEl) return;

            const targetRect = targetEl.getBoundingClientRect();
            if (x >= targetRect.left && x <= targetRect.right && y >= targetRect.top && y <= targetRect.bottom) {
                const sourceScene = window.scenes[selectedMesh.userData.sourceCanvas];
                const targetScene = window.scenes[targetId];

                if (sourceScene && targetScene) {
                    sourceScene.remove(selectedMesh);
                    targetScene.add(selectedMesh);
                    console.log(`✨ Objeto transferido de ${selectedMesh.userData.sourceCanvas} a ${targetId}`);
                }
            }
        });

        selectedMesh = null;
    });

    function animate() {
        requestAnimationFrame(animate);
        window.updateRegistries[canvasId].forEach(fn => fn());
        renderer.render(scene, camera);
    }
    animate();

    const resizeObserver = new ResizeObserver(entries => {
        for (let entry of entries) {
            const width = entry.contentRect.width;
            const height = entry.contentRect.height;
            if (width > 0 && height > 0) {
                camera.aspect = width / height;
                camera.updateProjectionMatrix();
                renderer.setSize(width, height);
            }
        }
    });
    resizeObserver.observe(viewport);
});

// --- CARGADOR AUTOMÁTICO DE ASSETS 3D DE BLENDER (.GLB) ---
function cargarAssetSinddiBlender(targetCanvasId = 'canvas-4') {
    const targetScene = window.scenes[targetCanvasId];
    if (!targetScene) {
        console.warn(`⚠️ Escena destino '${targetCanvasId}' no encontrada.`);
        return;
    }

    if (!THREE.GLTFLoader) {
        console.warn("⚠️ GLTFLoader no está disponible en el entorno.");
        return;
    }

    const loader = new THREE.GLTFLoader();
    loader.load(
        './asset_sinddi.glb',
        (gltf) => {
            const model = gltf.scene;
            model.position.set(0, 0, 0);
            model.scale.set(1, 1, 1);

            model.traverse((child) => {
                if (child.isMesh) {
                    child.castShadow = true;
                    child.receiveShadow = true;
                }
            });

            targetScene.add(model);
            console.log(`✨ S.I.N.D.D.I. Studio: 'asset_sinddi.glb' renderizado en ${targetCanvasId}.`);
        },
        (xhr) => {
            if (xhr.total > 0) {
                const porcentaje = (xhr.loaded / xhr.total) * 100;
                console.log(`Cargando asset 3D: ${porcentaje.toFixed(0)}%`);
            }
        },
        (error) => {
            console.warn("ℹ️ Archivo 'asset_sinddi.glb' no encontrado aún. Ejecuta Blender para generarlo.");
        }
    );
}

// --- RESTAURACIÓN AUTOMÁTICA DE ESCENAS DESDE MEMORIE.JSON ---
async function restaurarEscenasPersistidas() {
    try {
        const response = await fetch('http://127.0.0.1:3000/api/memories');
        if (response.ok) {
            console.log("🔄 S.I.N.D.D.I. Studio: Entornos gráficos sincronizados.");
            cargarAssetSinddiBlender('canvas-4');
        }
    } catch (e) {
        console.warn("⚠️ Servidor local no disponible temporalmente para persistencia.");
    }
}
restaurarEscenasPersistidas();
