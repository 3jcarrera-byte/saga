const scenes = {};
const cameras = {};
const renderers = {};
const updateRegistries = {};

// CORRECCIÓN: Lista numérica explícita para activar tus 7 pantallas 3D independientes
const active3DCanvasNumbers =;

// SEGURO ANTI-ERRORES: Espera a que el HTML esté completamente listo en memoria
document.addEventListener("DOMContentLoaded", () => {
    
    active3DCanvasNumbers.forEach(num => {
        const id = `canvas-${num}`;
        const container = document.getElementById(id);
        
        // Si por alguna razón el HTML cambia y no encuentra el contenedor, se lo salta en vez de romper todo
        if (!container) return; 

        const scene = new THREE.Scene();
        scenes[id] = scene;

        // Proporción matemática inicial
        const camera = new THREE.PerspectiveCamera(60, container.clientWidth / container.clientHeight, 0.1, 100);
        camera.position.z = 4;
        cameras[id] = camera;

        const renderer = new THREE.WebGLRenderer({ antialias: true });
        renderer.setSize(container.clientWidth, container.clientHeight);
        renderer.setPixelRatio(window.devicePixelRatio); // Añadido para mejor nitidez en pantallas de alta resolución
        container.appendChild(renderer.domElement);
        renderers[id] = renderer;

        // Iluminación integrada para cada cuadrante
        scene.add(new THREE.AmbientLight(0xffffff, 0.6));
        const dirLight = new THREE.DirectionalLight(0xffffff, 0.5);
        dirLight.position.set(2, 4, 2);
        scene.add(dirLight);

        updateRegistries[id] = [];
    });

    // Encendemos el bucle maestro una vez creados los entornos
    masterRenderLoop();
});

// El bucle de renderizado se ejecuta de forma externa y continua
function masterRenderLoop() {
    requestAnimationFrame(masterRenderLoop);

    active3DCanvasNumbers.forEach(num => {
        const id = `canvas-${num}`;
        if (!scenes[id]) return;

        // Ejecutar las funciones de movimiento inyectadas por la IA
        updateRegistries[id].forEach(animationFn => {
            try { animationFn(); } catch (e) { console.error(`Error en animación de ${id}:`, e); }
        });

        renderers[id].render(scenes[id], cameras[id]);
    });
}

// Auto-ajuste de tamaño adaptativo optimizado para el CSS Grid
window.addEventListener('resize', () => {
    active3DCanvasNumbers.forEach(num => {
        const id = `canvas-${num}`;
        const container = document.getElementById(id);
        if (!container || !renderers[id]) return;

        // Restablecemos las dimensiones basándonos en el redimensionamiento del contenedor Grid
        const width = container.clientWidth;
        const height = container.clientHeight;

        cameras[id].aspect = width / height;
        cameras[id].updateProjectionMatrix();
        renderers[id].setSize(width, height);
    });
});
