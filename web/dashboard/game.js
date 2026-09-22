class GameEngine {
    constructor() {
        this.canvas = document.getElementById('game-map');
        this.ctx = this.canvas.getContext('2d');
        this.avatar = document.getElementById('ayaka-pixel-avatar');
        this.chatBubble = document.getElementById('ayaka-chat-bubble');
        
        // Map settings
        this.mapData = null;
        this.collisionLayer = null; // To store collision data
        this.tilesetImage = new Image();
        this.tilesetImage.src = '/assets/minigame/samplemap.png';
        
        // Tileset constants
        this.TILE_SIZE = 32;
        this.TILESET_COLUMNS = 60; // samplemap is 1920px wide (1920/32 = 60)

        // Player state
        this.player = {
            x: 400, // Starting X
            y: 300, // Starting Y
            width: 32,
            height: 48,
            speed: 3,
            vx: 0,
            vy: 0,
            isWalking: false
        };

        // Keyboard state
        this.keys = {
            w: false, a: false, s: false, d: false
        };

        this.init();
    }

    async init() {
        // Wait for tileset image to load
        await new Promise((resolve, reject) => {
            if (this.tilesetImage.complete) {
                resolve();
            } else {
                this.tilesetImage.onload = resolve;
                this.tilesetImage.onerror = reject;
            }
        });

        // Load map JSON
        try {
            const res = await fetch('/assets/minigame/yashiro_map.json');
            this.mapData = await res.json();

            // Extract collision layer if exists
            this.collisionLayer = this.mapData.layers.find(l => l.name.toLowerCase() === 'collision');
            console.log("Map Loaded:", this.mapData);
            
            // Adjust canvas size to map size if needed
            this.canvas.width = this.mapData.width * this.TILE_SIZE;
            this.canvas.height = this.mapData.height * this.TILE_SIZE;
            
            // Render the static map once
            this.renderMap();
        } catch (e) {
            console.error("Failed to load map JSON", e);
        }

        // Setup input listeners
        this.setupInput();

        // Start game loop for player movement
        requestAnimationFrame(() => this.gameLoop());
    }

    renderMap() {
        if (!this.mapData || !this.ctx) return;

        // Clear canvas
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        // Draw each tile layer
        this.mapData.layers.forEach(layer => {
            if (layer.type === 'tilelayer' && layer.visible) {
                for (let i = 0; i < layer.data.length; i++) {
                    let tileId = layer.data[i];
                    if (tileId === 0) continue; // 0 means empty tile

                    // Calculate source X, Y on the tileset image
                    let localId = tileId - 1; // Assuming firstgid is 1
                    let srcX = (localId % this.TILESET_COLUMNS) * this.TILE_SIZE;
                    let srcY = Math.floor(localId / this.TILESET_COLUMNS) * this.TILE_SIZE;

                    // Calculate destination X, Y on the canvas
                    let destX = (i % layer.width) * this.TILE_SIZE;
                    let destY = Math.floor(i / layer.width) * this.TILE_SIZE;

                    this.ctx.drawImage(
                        this.tilesetImage, 
                        srcX, srcY, this.TILE_SIZE, this.TILE_SIZE, 
                        destX, destY, this.TILE_SIZE, this.TILE_SIZE
                    );
                }
            }
        });
    }

    setupInput() {
        window.addEventListener('keydown', (e) => {
            let key = e.key.toLowerCase();
            if (this.keys.hasOwnProperty(key)) {
                this.keys[key] = true;
            }
        });

        window.addEventListener('keyup', (e) => {
            let key = e.key.toLowerCase();
            if (this.keys.hasOwnProperty(key)) {
                this.keys[key] = false;
            }
        });
    }

    updatePlayer() {
        this.player.vx = 0;
        this.player.vy = 0;

        if (this.keys.w) this.player.vy = -this.player.speed;
        if (this.keys.s) this.player.vy = this.player.speed;
        if (this.keys.a) this.player.vx = -this.player.speed;
        if (this.keys.d) this.player.vx = this.player.speed;

        if (!this.mapData) return;

        // Calculate potential new position
        let newX = this.player.x + this.player.vx;
        let newY = this.player.y + this.player.vy;

        // Simple map boundaries check
        const mapPixelWidth = this.mapData.width * this.TILE_SIZE;
        const mapPixelHeight = this.mapData.height * this.TILE_SIZE;

        if (newX < 0) newX = 0;
        if (newY < 0) newY = 0;
        if (newX > mapPixelWidth - this.player.width) newX = mapPixelWidth - this.player.width;
        if (newY > mapPixelHeight - this.player.height) newY = mapPixelHeight - this.player.height;

        // Collision Check using Tiled 'Collision' layer
        let canMove = true;
        if (this.collisionLayer) {
            // Check all 4 corners of the player's bounding box
            const corners = [
                {x: newX, y: newY}, // Top-Left
                {x: newX + this.player.width, y: newY}, // Top-Right
                {x: newX, y: newY + this.player.height}, // Bottom-Left
                {x: newX + this.player.width, y: newY + this.player.height} // Bottom-Right
            ];

            for (let corner of corners) {
                let tileX = Math.floor(corner.x / this.TILE_SIZE);
                let tileY = Math.floor(corner.y / this.TILE_SIZE);
                
                if (tileX >= 0 && tileX < this.mapData.width && tileY >= 0 && tileY < this.mapData.height) {
                    let tileIndex = tileY * this.mapData.width + tileX;
                    let tileId = this.collisionLayer.data[tileIndex];
                    // If tileId is > 0, it means there is a collision block there
                    if (tileId > 0) {
                        canMove = false;
                        break;
                    }
                }
            }
        }

        if (canMove) {
            this.player.x = newX;
            this.player.y = newY;
        }

        // Update DOM elements
        this.avatar.style.left = `${this.player.x}px`;
        this.avatar.style.top = `${this.player.y}px`;
        
        this.chatBubble.style.left = `${this.player.x}px`;
        this.chatBubble.style.top = `${this.player.y - 50}px`; // Bubble floats above

        // Handle animation state
        let isMoving = this.player.vx !== 0 || this.player.vy !== 0;
        if (isMoving && !this.player.isWalking) {
            this.avatar.classList.add('walking');
            this.player.isWalking = true;
        } else if (!isMoving && this.player.isWalking) {
            this.avatar.classList.remove('walking');
            this.player.isWalking = false;
        }

        // Flip character if moving left
        if (this.player.vx < 0) {
            this.avatar.style.transform = 'scaleX(-1)';
        } else if (this.player.vx > 0) {
            this.avatar.style.transform = 'scaleX(1)';
        }

        // Call camera update
        this.updateCamera();
    }

    updateCamera() {
        const camera = document.getElementById('game-camera');
        const wrapper = document.getElementById('pixel-art-wrapper');
        if (!camera || !wrapper || !this.mapData) return;

        // Configuration
        const scale = 2; // Zoom 2x

        // Calculate center of player
        const playerCenterX = this.player.x + (this.player.width / 2);
        const playerCenterY = this.player.y + (this.player.height / 2);

        // Calculate camera offset so player is in center of wrapper
        let cameraX = (wrapper.offsetWidth / 2) - (playerCenterX * scale);
        let cameraY = (wrapper.offsetHeight / 2) - (playerCenterY * scale);

        // Map bounds check
        const mapPixelWidth = this.mapData.width * this.TILE_SIZE;
        const mapPixelHeight = this.mapData.height * this.TILE_SIZE;
        
        const minCameraX = wrapper.offsetWidth - (mapPixelWidth * scale);
        const minCameraY = wrapper.offsetHeight - (mapPixelHeight * scale);

        // Clamp camera to map boundaries
        if (mapPixelWidth * scale > wrapper.offsetWidth) {
            if (cameraX > 0) cameraX = 0; 
            if (cameraX < minCameraX) cameraX = minCameraX; 
        } else {
            cameraX = (wrapper.offsetWidth - (mapPixelWidth * scale)) / 2;
        }

        if (mapPixelHeight * scale > wrapper.offsetHeight) {
            if (cameraY > 0) cameraY = 0; 
            if (cameraY < minCameraY) cameraY = minCameraY; 
        } else {
            cameraY = (wrapper.offsetHeight - (mapPixelHeight * scale)) / 2;
        }

        camera.style.transform = `translate(${cameraX}px, ${cameraY}px) scale(${scale})`;
    }

    gameLoop() {
        this.updatePlayer();
        requestAnimationFrame(() => this.gameLoop());
    }
}

// Initialize the game engine when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Only init if we are on the companion tab
    const wrapper = document.getElementById('pixel-art-wrapper');
    if (wrapper) {
        window.gameEngine = new GameEngine();
    }
});
