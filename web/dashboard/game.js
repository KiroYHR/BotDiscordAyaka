class GameEngine {
    constructor() {
        this.canvas = document.getElementById('game-map');
        this.ctx = this.canvas.getContext('2d');
        this.avatar = document.getElementById('ayaka-pixel-avatar');
        this.chatBubble = document.getElementById('ayaka-chat-bubble');
        
        // Map settings
        this.mapData = null;
        this.tilesetImage = new Image();
        this.tilesetImage.src = '/assets/minigame/samplemap.png';
        
        // Tileset constants
        this.TILE_SIZE = 32;
        this.TILESET_COLUMNS = 60; // samplemap is 1920px wide (1920/32 = 60)

        // Player state
        this.player = {
            x: 400, // Starting X
            y: 300, // Starting Y
            width: 128,
            height: 192,
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

        // Update position
        this.player.x += this.player.vx;
        this.player.y += this.player.vy;

        // Clamp to map boundaries
        this.player.x = Math.max(0, Math.min(this.player.x, this.canvas.width - this.player.width));
        this.player.y = Math.max(0, Math.min(this.player.y, this.canvas.height - this.player.height));

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
            this.avatar.style.transform = 'scaleX(-1.2) scaleY(1.2)';
        } else if (this.player.vx > 0) {
            this.avatar.style.transform = 'scaleX(1.2) scaleY(1.2)';
        }
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
