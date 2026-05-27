const TILE_SIZE = 32;

class FarmScene extends Phaser.Scene {
  constructor() {
    super('FarmScene');
  }
  createInventoryPanel() {
  this.inventoryPanelVisible = false;

  // Container
  this.inventoryPanel = this.add.container(650, 40);
  this.inventoryPanel.setScrollFactor(0);
  this.inventoryPanel.setDepth(100);
  this.inventoryPanel.setVisible(false);
  this.lastApiCall = 0;
  this.apiInterval = 1000; // 5 seconds
  this.isFetching = false;

  // Background
  const bg = this.add.rectangle(0, 0, 180, 120, 0x000000, 0.7)
    .setOrigin(0.5,0.5);

  // Title
  const title = this.add.text(90, 8, 'Inventory', {
    font: '16px Arial',
    fill: '#ffffff'
  }).setOrigin(0.5, 0);

  // Item texts
  this.seedText = this.add.text(10, 40, '', {
    font: '14px Arial',
    fill: '#ffffff'
  });

  this.cropText = this.add.text(10, 70, '', {
    font: '14px Arial',
    fill: '#ffffff'
  });

  this.inventoryPanel.add([
    bg,
    title,
    this.seedText,
    this.cropText
  ]);

  // this.updateInventoryPanel();
  }
  preload() {
    this.load.image('grass', 'assets/tiles.png');
    // this.load.image('player', 'assets/player.png');
    // this.load.image('walls', 'assets/walls.png');

     this.load.spritesheet('player', 'assets/player.png', {
        frameWidth: 48,
        frameHeight: 48
    });
    this.load.spritesheet('waterani', 'assets/water2.png', {
        frameWidth: 48,
        frameHeight: 48
    });
   
    this.load.image('stone', 'assets/stone.png');
    this.load.spritesheet('tiles', 'assets/tiles.png', {
      frameWidth: 32,
      frameHeight: 32
    });
    this.load.spritesheet('crops', 'assets/crops.png', {
      frameWidth: 32,
      frameHeight: 32
    });
    this.load.spritesheet('walls_right', 'assets/walls_right.png', {
      frameWidth: 145,
      frameHeight: 100
    });
    this.load.image('water_tank', 'assets/water_tank.png');
    this.load.image('water_drop', 'assets/water.png');

  }

 create() {

  
  this.createInventoryPanel(); // ✅ FIRST
  this.createMap();
  this.createPlayer();
  this.createInput();
  this.plant_cords = [[1,2]];
  // this.crops = this.add.group();
  this.crops = {};

  // wall code 
  // const wall3 = this.add.sprite(200, 210, 'walls_right', 8);

  this.tank = this.add.image(80, 250, 'water_tank').setOrigin(0.5,0.5);
  this.tank.setScale(0.10); // adjust size if needed

 this.anims.create({
        key: 'w',
        frames: this.anims.generateFrameNumbers('waterani', {
            frames: [0,1,2,3]
        }),
        frameRate: 6,
        repeat: -1
    });
   
   this.anims.create({
        key: 'down',
        frames: this.anims.generateFrameNumbers('player', {
            frames: [0,4,8,12]
        }),
        frameRate: 3,
        repeat: -1
    });

    

    this.anims.create({
        key: 'left',
        frames: this.anims.generateFrameNumbers('player', {
            frames: [1,5,9,13]
        }),
        frameRate: 3,
        repeat: -1
    });

    this.anims.create({
        key: 'right',
        frames: this.anims.generateFrameNumbers('player', {
            frames: [3,7,11,15]
        }),
        frameRate: 3,
        repeat: -1
    });

    this.anims.create({
        key: 'up',
        frames: this.anims.generateFrameNumbers('player', {
            frames: [2,6,10,14]
        }),
        frameRate: 3,
        repeat: -1
    });
    this.anims.create({
        key: 'idle',
        frames: this.anims.generateFrameNumbers('player', {
            frames: [0]
        }),
        frameRate: 3,
        repeat: -1
    });


    //  const player = this.add.sprite(100, 100, 'player');

    // player.play('down');
    // console.log("player size:")
    // console.log(this.textures.get('player').frameTotal);
   
  }

  createMap() {
    this.map = [];

    for (let y = 0; y < 45; y++) {      
      this.map[y] = [];
      for (let x = 0; x < 45; x++) {
        this.add.image(
          x * TILE_SIZE,
          y * TILE_SIZE,
          'grass'
        ).setOrigin(0);

        this.map[y][x] = {
          tilled: false,
          watered: false,
          crop: null,
          waterOverlay: null
        };
      }
    }

    // const tile = this.add.sprite(
    //   5 * TILE_SIZE + TILE_SIZE / 2,
    //   4 * TILE_SIZE + TILE_SIZE / 2,
    //   'tiles',
    //   5
    // );
    // console.log(tile)

    const map = this.make.tilemap({ key: 'map' });
    const tileset = map.addTilesetImage('tiles');
    const layer = map.createLayer('Ground', tileset);

    this.inventory = {
      seeds: 5,
      crops: 0,
      water_available: false 
    };

    this.inventoryText = this.add.text(10, 10, '', {
      font: '16px Arial',
      fill: '#ffffff'
    }).setScrollFactor(0);

    this.updateInventoryUI();
  }

  updateInventoryUI() {
  this.inventoryText.setText(
    `Seeds: ${this.inventory.seeds}\nCrops: ${this.inventory.crops}\n water_availabe : ${this.inventory.water_available}`
  );

  this.updateInventoryPanel();
 }

updateInventoryPanel() {
  if (!this.seedText || !this.cropText) return;

  this.seedText.setText(`🌱 Seeds: ${this.inventory.seeds}`);
  this.cropText.setText(`🥕 Crops: ${this.inventory.crops}`);
 }

  game_state(){
    farm_state = {"player":[10,12]}
    return farm_state
  }

  createPlayer() {
    this.player = this.physics.add.sprite(200, 100, 'player');
    this.player.setDepth(10);
    this.player.speed = 150;
    this.player.setCollideWorldBounds(true);
  }

  createInput() {
    this.cursors = this.input.keyboard.createCursorKeys();
    this.actionKey = this.input.keyboard.addKey(
      Phaser.Input.Keyboard.KeyCodes.SPACE
    );
    this.waterKey = this.input.keyboard.addKey(
      Phaser.Input.Keyboard.KeyCodes.W
    );
    this.inventoryKey = this.input.keyboard.addKey(
  Phaser.Input.Keyboard.KeyCodes.I
   );
  }  
  
  async fetchData(){
    try {
        // Example API call

        const response = await fetch('http://localhost:3000/get_game_state');
        // this.waterani.anims.play('up', true);
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        const data = await response.json();
        console.log('Fetched data:', data);

       const [x, y] = data.player_pos;
       const crops = data.crops;
       console.log("water water_available")
       this.inventory.water_available = data.water_available
       this.updateInventoryUI()
       // console.log(crops["crop1"]["pos"])
       // console.log(Object.entries(crops))

      if (crops) {
        for (const [cropName, cropData] of Object.entries(crops)) {


        console.log(`${cropName} position: X=${cropData.pos[0]}, Y=${cropData.pos[1]}`);
        console.log("plant cords")
        console.log(`${this.plant_cords}`)
        const exists = this.plant_cords.some(
          ([a, b]) => a === cropData.pos[0] && b === cropData.pos[1]
        );
        console.log(`${exists}`)
        if(cropData.planted == true && !exists){
          this.plant_cords.push([cropData.pos[0],cropData.pos[1]])

         this.plantCrop(Math.round(cropData.pos[0] / TILE_SIZE)+1, Math.round(cropData.pos[1] / TILE_SIZE)-1) 

        }else if(cropData.planted == false & this.inventory.crops > 0){
            this.removeCrop(cropData.pos[0],cropData.pos[1])
          }

        }
    }

       const crop1_pos = crops["crop1"]["pos"]
       const crop2_pos = crops["crop2"]["pos"]
       const needWater1 = crops["crop1"]["needs_water"];
       // console.log("needWater1 state....")
       // console.log(needWater1)
       // this.watering = this.physics.add.sprite(x, y, 'waterani');
       this.waterText = ""
      if(needWater1 == false){
        this.waterText = this.add.text(crop1_pos[0], crop1_pos[1]-50, "adding water", { fontSize: '10px', fill: 'blue' });
        if (!this.watering) {
              this.watering = this.physics.add.sprite(x, y, 'waterani');
               this.watering.setDepth(100);
               this.watering.setScale(0.7);
          }
          this.watering.setPosition(x+40, y-20);
          this.watering.anims.play('w', true);
       }else if(needWater1 == true || (x == 200 && y == 100)){
        this.waterText = null
       }
      //  if (needWater1 == false) {

      //     if (!this.waterText) {
      //         this.waterText = this.add.text(
      //             crop1_pos[0],
      //             crop1_pos[1] - 50,
      //             "adding water",
      //             { fontSize: '10px', fill: 'blue' }
      //         );
      //     }

      //     if (!this.watering) {
      //         this.watering = this.physics.add.sprite(x, y, 'waterani');
      //         this.watering.setDepth(100);
      //         this.watering.setScale(0.7);
      //     }

      //     this.watering.setPosition(x + 40, y - 20);
      //     this.watering.anims.play('w', true);
      // }
      // else if (needWater1 == true || (x == 200 && y == 100)) {
      //     if (this.waterText) {
      //         this.waterText.destroy();   // or .setVisible(false)
      //         this.waterText = null;
      //     }

      //     if (this.watering) {
      //         this.watering.anims.stop();
      //         this.watering.setFrame(2);
      //     }
      // }
      
       const needWater2 = crops["crop2"]["needs_water"];
       console.log("water states....")
       console.log(needWater1,needWater2)
       

       if(needWater2 == false){
          this.add.text(crop2_pos[0], crop2_pos[1]-50, "adding water", { fontSize: '10px', fill: 'blue' });

          if (!this.watering) {
              this.watering = this.physics.add.sprite(x, y, 'waterani');
               this.watering.setDepth(100);
               this.watering.setScale(0.7);
          }
          this.watering.setPosition(x+40, y-20);
          this.watering.anims.play('w', true);

       }else if((needWater2 == true) || (x == 200 && y == 100)){
        this.waterText = null
        // this.watering.setFrame(2);
       }

       
      //  this.crop1 = this.add.sprite(
      // 5 * TILE_SIZE + TILE_SIZE / 2,
      // 4 * TILE_SIZE + TILE_SIZE / 2,
      // 'tiles',
      // 5).setOrigin(0,0);
      //  this.crop1.setPosition(crop2_pos[0]+25,crop2_pos[1]-25)

       const [xobs,yobs] = data.obstacles;
       console.log(data.obstacles)
       this.add.image(xobs, yobs, 'stone').setOrigin(0.5,0.5);

       
        // Stop any existing movement
         this.player.setScale(2);
        this.player.setVelocity(0);
        // this.player.setOrigin(0.5,1)
        this.player.setOrigin(0.5,0.8)
        // Set player position
        this.player.setPosition(x, y);

        if (x > this.prevPlayerX) {
        // this.player.flipX = false;
        this.player.anims.play('right', true);
        } else if (x < this.prevPlayerX) {
            // this.player.flipX = true;
            this.player.anims.play('left', true);
        } else if(y > this.prevPlayerY) {
            this.player.anims.play('down', true);
        } else if (y < this.prevPlayerY) {
            this.player.anims.play('up', true);
        }else if(x == 200 && y == 100){
          this.player.anims.play('idle', true);
        }

        this.player.setPosition(x, y);

        this.prevPlayerX = x;
        this.prevPlayerY = y;
        // this.add.text(x, y, `x: ${x}, y: ${y}`, { fontSize: '10px', fill: '#000' });
            // Use the data in your game

    } catch (error) {
        console.error('Error fetching data:', error);
        this.add.text(100, 100, 'Failed to load data', { fontSize: '20px', fill: '#f00' });
    }
  }
    

  update(time, delta) {
    this.movePlayer();

    if (Phaser.Input.Keyboard.JustDown(this.actionKey)) {
      this.handleAction();
    }
    //  this.player.anims.play('up', true);

   
    if (Phaser.Input.Keyboard.JustDown(this.inventoryKey)) {
     this.inventoryPanelVisible = !this.inventoryPanelVisible;
     this.inventoryPanel.setVisible(this.inventoryPanelVisible);
   }
    if (!this.isFetching && time - this.lastApiCall > this.apiInterval) {
        this.lastApiCall = time;
        this.fetchData(); // call async function
    }

    if (Phaser.Input.Keyboard.JustDown(this.waterKey)) {
     if (!this.watering) {
        this.watering = this.physics.add.sprite(
            this.player.x,
            this.player.y,
            'waterani'
        );
         this.watering.setDepth(100);
    }

    // this.watering.setPosition(this.player.x+40, this.player.y-10);
    // this.watering.anims.play('w', true);
}
 
  }
//200 100 -> 430 100 (1st crop)
// 200 100 -> 350 175 (2nd crop)
// 200 100 -> 350 175 (2nd crop)
  movePlayer() {
    const speed = this.player.speed;

    this.player.setVelocity(0);

    if (this.cursors.left.isDown) {
      this.player.setVelocityX(-speed);
    }
    if (this.cursors.right.isDown) {
      this.player.setVelocityX(speed);
    }
    if (this.cursors.up.isDown) {
      this.player.setVelocityY(-speed);
    }
    if (this.cursors.down.isDown) {
      this.player.setVelocityY(speed);
    }

    let playerX = this.player.x;
    let playerY = this.player.y;

    console.log(playerX, playerY);
  }

  waterTile() {
    const x = Math.floor(this.player.x / TILE_SIZE);
    const y = Math.floor(this.player.y / TILE_SIZE);

    const tile = this.map[y]?.[x];
    if (!tile || !tile.tilled) return;

    tile.watered = true;

    if (!tile.waterOverlay) {
      tile.waterOverlay = this.add.rectangle(
        x * TILE_SIZE,
        y * TILE_SIZE,
        TILE_SIZE,
        TILE_SIZE,
        0x0000ff,
        0.3
      ).setOrigin(0);
    }
  }

  handleAction() {
    const x = Math.floor(this.player.x / TILE_SIZE);
    const y = Math.floor(this.player.y / TILE_SIZE);

    const tile = this.map[y]?.[x];
    if (!tile) return;

    if (!tile.tilled  && this.inventory.seeds > 0) {
      tile.tilled = true;
      this.add.rectangle(
        x * TILE_SIZE,
        y * TILE_SIZE,
        TILE_SIZE,
        TILE_SIZE,
        0x8b4513
      ).setOrigin(0);
    }
    else if (!tile.crop && this.inventory.seeds > 0) {
      this.inventory.seeds--;
      this.updateInventoryUI();
      this.plantCrop(x, y);
    }
    else if (tile.crop && tile.crop.isReady) {
      tile.crop.destroy();
      tile.crop = null;

      this.inventory.crops++;
      this.updateInventoryUI();
    }
    else{
      // this.add.text(x, y-50, "", { fontSize: '10px', fill: 'blue' });
      alert("you are out of inventory");
    }
  }

  plantCrop(x, y) {
    const key = `${x},${y}`;
    this.inventory.seeds--;
    this.inventory.crops++;
    this.updateInventoryUI()
    this.crop = this.add.sprite(
      x * TILE_SIZE + TILE_SIZE / 2,
      y * TILE_SIZE + TILE_SIZE / 2,
      'tiles',
      5
    );

    this.crop.growth = 5;
    this.crop.isReady = false;

    this.time.addEvent({
      delay: 4000,
      repeat: 13,
      callback: () => {
        this.crop.growth++;
        if(this.crop.growth != 6){
            this.crop.setFrame(this.crop.growth);
          }
        if (this.crop.growth === 19) {
          this.crop.isReady = true;
        }
      }
    });


    this.map[y][x].crop = this.crop;
    this.crops[key] = this.crop;
  }


removeCrop(x, y) {
    this.inventory.seeds++;
    this.inventory.crops--;
    this.updateInventoryUI()
    const key = `${x},${y}`;

    if (this.crops[key]) {
      this.crops[key].destroy();
      delete this.crops[key];
    }

  }

 
 }

 const config = {
  type: Phaser.AUTO,
  width: 1400,
  height: 600,
  physics: {
    default: 'arcade',
    arcade: {
      debug: false
    }
  },
  scene: FarmScene,
  scale:{
    mode: Phaser.Scale.FIT,
    autoCenter: Phaser.Scale.CENTER_BOTH
  }
 };

new Phaser.Game(config);
