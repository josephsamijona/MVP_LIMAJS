import WindowManager from '{% static "js/WindowManager.js" %}';

const t = THREE;
let camera, scene, renderer, world;
let near, far;
let pixR = window.devicePixelRatio ? window.devicePixelRatio : 1;
let galaxyParticles = [];
let sceneOffsetTarget = {x: 0, y: 0};
let sceneOffset = {x: 0, y: 0};

// Initialisation du temps
let today = new Date();
today.setHours(0);
today.setMinutes(0);
today.setSeconds(0);
today.setMilliseconds(0);
today = today.getTime();

let internalTime = getTime();
let windowManager;
let initialized = false;

// Configuration de la galaxie
const GALAXY_CONFIG = {
    particleCount: 1000,
    particleSize: 0.1,
    rotationSpeed: 0.001,
    spiralArms: 3,
    spiralTightness: 2.5
};

// Couleurs de la charte graphique
const BRAND_COLORS = {
    primaryOrange: new t.Color('#FF8C00'),
    secondaryBlue: new t.Color('#4169E1'),
    background: new t.Color('#090A0F')
};

function getTime() {
    return (new Date().getTime() - today) / 1000.0;
}

// Initialisation conditionnelle
if (new URLSearchParams(window.location.search).get("clear")) {
    localStorage.clear();
} else {
    document.addEventListener("visibilitychange", () => {
        if (document.visibilityState != 'hidden' && !initialized) {
            init();
        }
    });

    window.onload = () => {
        if (document.visibilityState != 'hidden') {
            init();
        }
    };
}

// Création des particules de la galaxie
function createGalaxyParticles() {
    const geometry = new t.BufferGeometry();
    const positions = [];
    const colors = [];
    const sizes = [];

    for (let i = 0; i < GALAXY_CONFIG.particleCount; i++) {
        // Position spirale
        const angle = (i / GALAXY_CONFIG.particleCount) * Math.PI * 2 * GALAXY_CONFIG.spiralArms;
        const radius = (i / GALAXY_CONFIG.particleCount) * 50;
        const spiralX = Math.cos(angle * GALAXY_CONFIG.spiralTightness) * radius;
        const spiralY = Math.sin(angle * GALAXY_CONFIG.spiralTightness) * radius;
        const spiralZ = (Math.random() - 0.5) * 10;

        positions.push(spiralX, spiralY, spiralZ);
        
        // Couleur dégradée
        const color = new t.Color();
        color.lerpColors(BRAND_COLORS.primaryOrange, BRAND_COLORS.secondaryBlue, Math.random());
        colors.push(color.r, color.g, color.b);
        
        // Taille variable
        sizes.push(Math.random() * GALAXY_CONFIG.particleSize);
    }

    geometry.setAttribute('position', new t.Float32BufferAttribute(positions, 3));
    geometry.setAttribute('color', new t.Float32BufferAttribute(colors, 3));
    geometry.setAttribute('size', new t.Float32BufferAttribute(sizes, 1));

    const material = new t.PointsMaterial({
        size: GALAXY_CONFIG.particleSize,
        vertexColors: true,
        transparent: true,
        opacity: 0.8,
        blending: t.AdditiveBlending
    });

    return new t.Points(geometry, material);
}

function init() {
    initialized = true;
    
    setTimeout(() => {
        setupScene();
        setupGalaxy();
        setupWindowManager();
        setupLogo();
        resize();
        updateWindowShape(false);
        render();
        window.addEventListener('resize', resize);
    }, 500);
}

function setupScene() {
    scene = new t.Scene();
    scene.background = BRAND_COLORS.background;
    
    camera = new t.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    camera.position.z = 50;
    
    renderer = new t.WebGLRenderer({
        antialias: true,
        alpha: true
    });
    renderer.setPixelRatio(pixR);
    renderer.setSize(window.innerWidth, window.innerHeight);
    
    document.body.appendChild(renderer.domElement);
    
    world = new t.Object3D();
    scene.add(world);
}

function setupGalaxy() {
    const galaxy = createGalaxyParticles();
    world.add(galaxy);
    galaxyParticles.push(galaxy);
}

function setupLogo() {
    // Chargement et configuration du logo
    const textureLoader = new t.TextureLoader();
    textureLoader.load('{% static "img/logo.png" %}', (texture) => {
        const material = new t.SpriteMaterial({ 
            map: texture,
            transparent: true,
            opacity: 0.8
        });
        const logo = new t.Sprite(material);
        logo.scale.set(10, 10, 1);
        world.add(logo);
    });
}

function setupWindowManager() {
    windowManager = new WindowManager();
    windowManager.setWinShapeChangeCallback(updateWindowShape);
    windowManager.setWinChangeCallback(windowsUpdated);
    windowManager.init({ galaxyState: GALAXY_CONFIG });
}

function windowsUpdated() {
    updateGalaxyState();
}

function updateGalaxyState() {
    const wins = windowManager.getWindows();
    // Synchronisation de l'état de la galaxie entre les fenêtres
    wins.forEach((win, index) => {
        if (galaxyParticles[index]) {
            galaxyParticles[index].rotation.y = internalTime * GALAXY_CONFIG.rotationSpeed;
        }
    });
}

function updateWindowShape(easing = true) {
    sceneOffsetTarget = {x: -window.screenX, y: -window.screenY};
    if (!easing) sceneOffset = sceneOffsetTarget;
}

function render() {
    const t = getTime();
    internalTime = t;

    windowManager.update();

    // Animation fluide
    const falloff = 0.05;
    sceneOffset.x = sceneOffset.x + ((sceneOffsetTarget.x - sceneOffset.x) * falloff);
    sceneOffset.y = sceneOffset.y + ((sceneOffsetTarget.y - sceneOffset.y) * falloff);

    world.position.x = sceneOffset.x;
    world.position.y = sceneOffset.y;

    // Animation de la galaxie
    galaxyParticles.forEach(galaxy => {
        galaxy.rotation.y += GALAXY_CONFIG.rotationSpeed;
    });

    // Animation du glow
    const glowIntensity = Math.sin(t * 2) * 0.5 + 0.5;
    scene.traverse(object => {
        if (object.isMesh || object.isPoints) {
            if (object.material.opacity !== undefined) {
                object.material.opacity = 0.5 + glowIntensity * 0.5;
            }
        }
    });

    renderer.render(scene, camera);
    requestAnimationFrame(render);
}

function resize() {
    const width = window.innerWidth;
    const height = window.innerHeight;
    
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
    renderer.setSize(width, height);
}

// Export des fonctions utiles pour l'interaction externe
export { GALAXY_CONFIG, updateGalaxyState };