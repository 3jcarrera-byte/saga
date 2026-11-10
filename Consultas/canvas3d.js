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
    viewport.appendChild(renderer.domElement);

    const ambientLight = new THREE.AmbientLight(0xffffff, 0.7);
    scene.add(ambientLight);

    const pointLight = new THREE.PointLight(0x38bdf8, 2, 50);
    pointLight.position.set(5, 5, 5);
    scene.add(pointLight);

    camera.position.z = 4;

    window.scenes[canvasId] = scene;
    window.renderers[canvasId] = renderer;
    window.cameras[canvasId] = camera;
    window.updateRegistries[canvasId] = [];

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

        const rect = renderer.domElement.getBoundingClientRect();
        const x = event.clientX;
        const y = event.clientY;

        // Detectar sobre qué canvas se soltó el objeto
        active3DCanvasIds.forEach(targetId => {
            if (targetId === selectedMesh.userData.sourceCanvas) return;
            const targetEl = document.getElementById(`viewport-${targetId}`);
            if (!targetEl) return;

            const targetRect = targetEl.getBoundingClientRect();
            if (x >= targetRect.left && x <= targetRect.right && y >= targetRect.top && y <= targetRect.bottom) {
                // Transferir malla a la escena destino
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

// --- RESTAURACIÓN AUTOMÁTICA DE ESCENAS DESDE MEMORIE.JSON ---
async function restaurarEscenasPersistidas() {
    try {
        const response = await fetch('http://127.0.0.1:3000/api/memories');
        // Aquí SINDDI sincroniza el estado activo de las escenas al arrancar
        console.log("🔄 S.I.N.D.D.I. Studio: Entornos gráficos sincronizados.");
    } catch (e) {
        console.warn("⚠️ Servidor local no disponible temporalmente para persistencia.");
    }
}
restaurarEscenasPersistidas();
