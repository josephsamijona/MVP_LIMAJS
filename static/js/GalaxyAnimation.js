class GalaxyAnimation {
    constructor(scene, config = {}) {
        this.scene = scene;
        this.particles = [];
        this.clock = new THREE.Clock();
        
        // Configuration par défaut avec les couleurs de Limajs
        this.config = {
            particleCount: config.particleCount || 15000,
            particleSize: config.particleSize || 0.1,
            galaxyRadius: config.galaxyRadius || 100,
            spiralArms: config.spiralArms || 5,
            rotationSpeed: config.rotationSpeed || 0.5,
            particleSpread: config.particleSpread || 0.2,
            colors: {
                primary: new THREE.Color(0xFF8C00),    // Orange
                secondary: new THREE.Color(0x4169E1),   // Bleu
                accent: new THREE.Color(0xFFD700)      // Or pour les étoiles brillantes
            }
        };

        this.init();
    }

    init() {
        // Création de la géométrie pour les particules de la galaxie
        this.createGalaxyParticles();
        // Création des étoiles de fond
        this.createBackgroundStars();
        // Création des points lumineux spéciaux (étoiles brillantes)
        this.createGlowingStars();
    }

    createGalaxyParticles() {
        const positions = new Float32Array(this.config.particleCount * 3);
        const colors = new Float32Array(this.config.particleCount * 3);
        const sizes = new Float32Array(this.config.particleCount);

        for(let i = 0; i < this.config.particleCount; i++) {
            const i3 = i * 3;
            // Calcul de la position dans la spirale
            const radius = Math.random() * this.config.galaxyRadius;
            const spinAngle = radius * this.config.spiralArms;
            const branchAngle = (i % this.config.spiralArms) * ((2 * Math.PI) / this.config.spiralArms);

            const x = Math.cos(spinAngle + branchAngle) * radius;
            const y = (Math.random() - 0.5) * radius * this.config.particleSpread;
            const z = Math.sin(spinAngle + branchAngle) * radius;

            positions[i3] = x;
            positions[i3 + 1] = y;
            positions[i3 + 2] = z;

            // Couleur basée sur la distance au centre
            const mixRatio = radius / this.config.galaxyRadius;
            const color = new THREE.Color();
            color.lerpColors(
                this.config.colors.primary,
                this.config.colors.secondary,
                mixRatio
            );

            colors[i3] = color.r;
            colors[i3 + 1] = color.g;
            colors[i3 + 2] = color.b;

            // Taille variable des particules
            sizes[i] = Math.random() * this.config.particleSize;
        }

        const geometry = new THREE.BufferGeometry();
        geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
        geometry.setAttribute('size', new THREE.BufferAttribute(sizes, 1));

        // Shader personnalisé pour les particules
        const material = new THREE.ShaderMaterial({
            uniforms: {
                time: { value: 0 },
                pixelRatio: { value: window.devicePixelRatio }
            },
            vertexShader: `
                attribute float size;
                uniform float time;
                uniform float pixelRatio;
                varying vec3 vColor;

                void main() {
                    vColor = color;
                    vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
                    gl_PointSize = size * pixelRatio * (300.0 / -mvPosition.z);
                    gl_Position = projectionMatrix * mvPosition;
                }
            `,
            fragmentShader: `
                varying vec3 vColor;

                void main() {
                    if (length(gl_PointCoord - vec2(0.5)) > 0.5) discard;
                    gl_FragColor = vec4(vColor, 1.0);
                }
            `,
            vertexColors: true,
            transparent: true,
            depthWrite: false,
            blending: THREE.AdditiveBlending
        });

        this.galaxyPoints = new THREE.Points(geometry, material);
        this.scene.add(this.galaxyPoints);
    }

    createBackgroundStars() {
        const starsGeometry = new THREE.BufferGeometry();
        const starsCount = 2000;
        const positions = new Float32Array(starsCount * 3);
        const colors = new Float32Array(starsCount * 3);

        for(let i = 0; i < starsCount; i++) {
            const i3 = i * 3;
            positions[i3] = (Math.random() - 0.5) * 2000;
            positions[i3 + 1] = (Math.random() - 0.5) * 2000;
            positions[i3 + 2] = (Math.random() - 0.5) * 2000;

            colors[i3] = 1;
            colors[i3 + 1] = 1;
            colors[i3 + 2] = 1;
        }

        starsGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        starsGeometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

        const starsMaterial = new THREE.PointsMaterial({
            size: 2,
            vertexColors: true,
            transparent: true,
            opacity: 0.8
        });

        this.backgroundStars = new THREE.Points(starsGeometry, starsMaterial);
        this.scene.add(this.backgroundStars);
    }

    createGlowingStars() {
        const glowingStarsGeometry = new THREE.BufferGeometry();
        const glowingStarsCount = 50;
        const positions = new Float32Array(glowingStarsCount * 3);

        for(let i = 0; i < glowingStarsCount; i++) {
            const i3 = i * 3;
            const radius = Math.random() * this.config.galaxyRadius * 0.7;
            const theta = Math.random() * Math.PI * 2;
            const phi = Math.random() * Math.PI * 2;

            positions[i3] = radius * Math.sin(theta) * Math.cos(phi);
            positions[i3 + 1] = radius * Math.sin(theta) * Math.sin(phi);
            positions[i3 + 2] = radius * Math.cos(theta);
        }

        glowingStarsGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));

        const glowingStarsMaterial = new THREE.PointsMaterial({
            size: 4,
            color: this.config.colors.accent,
            transparent: true,
            opacity: 0.8,
            blending: THREE.AdditiveBlending
        });

        this.glowingStars = new THREE.Points(glowingStarsGeometry, glowingStarsMaterial);
        this.scene.add(this.glowingStars);
    }

    update(deltaTime = 0.016) {
        if (this.galaxyPoints) {
            this.galaxyPoints.rotation.y += this.config.rotationSpeed * deltaTime;
            this.galaxyPoints.material.uniforms.time.value += deltaTime;
        }

        if (this.backgroundStars) {
            this.backgroundStars.rotation.y += this.config.rotationSpeed * deltaTime * 0.1;
        }

        if (this.glowingStars) {
            this.glowingStars.rotation.y += this.config.rotationSpeed * deltaTime * 0.2;
            // Effet de pulsation pour les étoiles brillantes
            const pulseFactor = Math.sin(this.clock.getElapsedTime() * 2) * 0.2 + 0.8;
            this.glowingStars.material.opacity = pulseFactor;
        }
    }

    // Méthode pour synchroniser l'état avec d'autres fenêtres
    syncState(state) {
        if (this.galaxyPoints) {
            this.galaxyPoints.rotation.y = state.rotation || this.galaxyPoints.rotation.y;
        }
    }

    // Méthode pour récupérer l'état actuel
    getState() {
        return {
            rotation: this.galaxyPoints ? this.galaxyPoints.rotation.y : 0,
            timestamp: Date.now()
        };
    }

    // Méthode pour redimensionner la galaxie
    resize(width, height) {
        if (this.galaxyPoints) {
            this.galaxyPoints.material.uniforms.pixelRatio.value = window.devicePixelRatio;
        }
    }
}

export default GalaxyAnimation;