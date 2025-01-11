class WindowManager {
    #windows;
    #count;
    #id;
    #winData;
    #winShapeChangeCallback;
    #winChangeCallback;
    #galaxyState;
    
    constructor() {
        let that = this;

        // Écouteur pour les changements dans localStorage
        addEventListener("storage", (event) => {
            if (event.key == "windows") {
                let newWindows = JSON.parse(event.newValue);
                let winChange = that.#didWindowsChange(that.#windows, newWindows);

                that.#windows = newWindows;

                if (winChange) {
                    this.#updateGalaxyState();
                    if (that.#winChangeCallback) that.#winChangeCallback();
                }
            }
        });

        // Gestion de la fermeture de fenêtre
        window.addEventListener('beforeunload', function(e) {
            let index = that.getWindowIndexFromId(that.#id);
            that.#windows.splice(index, 1);
            that.updateWindowsLocalStorage();
        });

        // État initial de la galaxie
        this.#galaxyState = {
            particlePositions: [],
            rotationState: 0,
            lastUpdateTime: Date.now()
        };
    }

    #didWindowsChange(prevWins, newWins) {
        if (prevWins?.length !== newWins?.length) {
            return true;
        }
        return prevWins.some((win, index) => 
            win.id !== newWins[index].id || 
            !this.#areShapesEqual(win.shape, newWins[index].shape)
        );
    }

    #areShapesEqual(shape1, shape2) {
        return shape1.x === shape2.x &&
               shape1.y === shape2.y &&
               shape1.w === shape2.w &&
               shape1.h === shape2.h;
    }

    #updateGalaxyState() {
        const now = Date.now();
        const deltaTime = now - this.#galaxyState.lastUpdateTime;
        
        // Mettre à jour l'état de la galaxie
        this.#galaxyState.rotationState += deltaTime * 0.0001;
        this.#galaxyState.lastUpdateTime = now;

        // Synchroniser avec les autres fenêtres
        let galaxyData = {
            rotation: this.#galaxyState.rotationState,
            timestamp: now
        };

        localStorage.setItem('galaxyState', JSON.stringify(galaxyData));
    }

    init(metaData = {}) {
        // Initialiser ou récupérer les fenêtres existantes
        this.#windows = JSON.parse(localStorage.getItem("windows")) || [];
        this.#count = parseInt(localStorage.getItem("count")) || 0;
        this.#count++;

        // Configuration de la fenêtre actuelle
        this.#id = this.#count;
        let shape = this.getWinShape();
        this.#winData = {
            id: this.#id,
            shape: shape,
            metaData: {
                ...metaData,
                galaxyState: this.#galaxyState
            }
        };

        // Ajouter la fenêtre à la liste
        this.#windows.push(this.#winData);

        // Mettre à jour localStorage
        localStorage.setItem("count", this.#count);
        this.updateWindowsLocalStorage();

        // Récupérer l'état de la galaxie
        const savedGalaxyState = localStorage.getItem('galaxyState');
        if (savedGalaxyState) {
            const parsedState = JSON.parse(savedGalaxyState);
            this.#galaxyState = {
                ...this.#galaxyState,
                rotationState: parsedState.rotation,
                lastUpdateTime: parsedState.timestamp
            };
        }
    }

    getWinShape() {
        return {
            x: window.screenX,
            y: window.screenY,
            w: window.innerWidth,
            h: window.innerHeight
        };
    }

    getWindowIndexFromId(id) {
        return this.#windows.findIndex(win => win.id === id);
    }

    updateWindowsLocalStorage() {
        localStorage.setItem("windows", JSON.stringify(this.#windows));
    }

    update() {
        let winShape = this.getWinShape();
        
        if (!this.#areShapesEqual(this.#winData.shape, winShape)) {
            this.#winData.shape = winShape;
            
            let index = this.getWindowIndexFromId(this.#id);
            this.#windows[index].shape = winShape;

            if (this.#winShapeChangeCallback) this.#winShapeChangeCallback();
            this.updateWindowsLocalStorage();
            this.#updateGalaxyState();
        }
    }

    setWinShapeChangeCallback(callback) {
        this.#winShapeChangeCallback = callback;
    }

    setWinChangeCallback(callback) {
        this.#winChangeCallback = callback;
    }

    getWindows() {
        return this.#windows;
    }

    getThisWindowData() {
        return this.#winData;
    }

    getThisWindowID() {
        return this.#id;
    }

    getGalaxyState() {
        return this.#galaxyState;
    }

    // Méthode pour synchroniser l'état de la galaxie entre les fenêtres
    syncGalaxyState(newState) {
        this.#galaxyState = {
            ...this.#galaxyState,
            ...newState
        };
        this.#updateGalaxyState();
    }
}

export default WindowManager;