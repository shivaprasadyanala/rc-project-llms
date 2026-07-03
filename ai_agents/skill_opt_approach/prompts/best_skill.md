# Farm Skill

## Goal Priority

1. Plant every unplanted crop.
2. If water is unavailable, collect water first.
3. Continue planting.

## Navigation

- Move exactly one grid cell (25 px).
- Never move through obstacles.
- Crops are valid destinations.

## Planting

Before planting:

- Check crop is not planted.
- Check water is available.

After planting:

- Verify crop became planted.

## Water

If water_available == False

Go to the water tank.
Collect water.
Resume planting.