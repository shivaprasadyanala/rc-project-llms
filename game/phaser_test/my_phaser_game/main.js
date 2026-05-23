import FarmScene  from './src/scenes/FarmScene.js';
const config = {
    type: Phaser.AUTO,
    title: 'farm game',
    description: '',
    parent: 'game-container',
    width: 1800,
    height: 1500,
    backgroundColor: '#000000',
    pixelArt: false,
    scene: [
        FarmScene
    ],
    scale: {
        // mode: Phaser.Scale.FIT,
        // autoCenter: Phaser.Scale.CENTER_BOTH
        mode: Phaser.Scale.FIT,
    autoCenter: Phaser.Scale.CENTER_HORIZONTALLY
    },
}

console.log("testing")

new Phaser.Game(config);
            