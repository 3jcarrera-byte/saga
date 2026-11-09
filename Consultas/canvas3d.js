// ==========================================
// MOTOR 3D MULTI-ESTACIÓN DE S.I.N.D.D.I. (Three.js)
// ==========================================

const active3DCanvasIds = ['canvas-2', 'canvas-4', 'canvas-7'];

// Exponer globalmente para permitir inyección de código de S.I.N.D.D.I.
window.scenes = window.scenes || {};
window.renderers = window.renderers || {};
window.cameras = window.cameras || {};
window.updateRegistries = window.updateRegistries || {};

active3DCanvasIds.forEach(canvasId => {
    const container = document.getElementById(canvasId);
    if (!container) return;

    // Evitar duplicados si el script se recarga
    const existingViewport = document.getElementById(`viewport-${canvasId}`);
    if (existingViewport) existingViewport.remove();

    // Crear un visor independiente dentro de cada panel
    const viewport = document.createElement('div');
    viewport.id = `viewport-${canvasId}`;
    viewport.style.width = '100%';
    viewport.style.height = 'calc(100% - 30px)';
    viewport.style.background = '#000';
    viewport.style.position = 'relative';
    viewport.style.borderRadius = '4px';
    viewport.style.overflow = 'hidden';
    container.appendChild(viewport);

    // Inicializar Escena, Cámara y Renderizador WebGL
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(75, viewport.clientWidth / viewport.clientHeight || 1, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'high-performance' });

    renderer.setSize(viewport.clientWidth, viewport.clientHeight);
    viewport.appendChild(renderer.domElement);

    // Iluminación estándar de estudio profesional
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.7);
    scene.add(ambientLight);

    const pointLight = new THREE.PointLight(0x38bdf8, 2, 50);
    pointLight.position.set(5, 5, 5);
    scene.add(pointLight);

    camera.position.z = 4;

    // Asignar referencias globales
    window.scenes[canvasId] = scene;
    window.renderers[canvasId] = renderer;
    window.cameras[canvasId] = camera;
    window.updateRegistries[canvasId] = [];

    // Objetos iniciales representativos por cada estación de trabajo
    if (canvasId === 'canvas-4') {
        // Núcleo flotante / Avatar de S.I.N.D.D.I.
        const geometry = new THREE.IcosahedronGeometry(1.2, 0);
        const material = new THREE.MeshStandardMaterial({ 
            color: 0xec4899, 
            wireframe: true,
            roughness: 0.3 
        });
        const coreMesh = new THREE.Mesh(geometry, material);
        scene.add(coreMesh);
        
        window.updateRegistries[canvasId].push(() => {
            coreMesh.rotation.x += 0.005;
            coreMesh.rotation.y += 0.01;
        });
    } else if (canvasId === 'canvas-2') {
        // Estación de Modelado y Materiales PBR
        const geometry = new THREE.BoxGeometry(1.5, 1.5, 1.5);
        const material = new THREE.MeshStandardMaterial({ 
            color: 0x3b82f6, 
            roughness: 0.2, 
            metalness: 0.8 
        });
        const boxMesh = new THREE.Mesh(geometry, material);
        scene.add(boxMesh);

        window.updateRegistries[canvasId].push(() => {
            boxMesh.rotation.x += 0.005;
            boxMesh.rotation.y += 0.005;
        });
    } else if (canvasId === 'canvas-7') {
        // Estación de Rigging y Animación (Estructura articulada simulada)
        const geometry = new THREE.ConeGeometry(0.8, 2, 4);
        const material = new THREE.MeshStandardMaterial({ 
            color: 0x10b981, 
            wireframe: true 
        });
        const boneMesh = new THREE.Mesh(geometry, material);
        scene.add(boneMesh);

        window.updateRegistries[canvasId].push(() => {
            boneMesh.rotation.z += 0.01;
        });
    }

    // Bucle de renderizado independiente por estación
    function animate() {
        requestAnimationFrame(animate);
        window.updateRegistries[canvasId].forEach(fn => fn());
        renderer.render(scene, camera);
    }
    animate();

    // ResizeObserver avanzado para detectar cambios de tamaño en el panel del grid sin depender solo de window.resize
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
