# Mode C helper scripts

These scripts are optional helpers for the Mode C layer-compositing workflow.
Use them only after the user confirms the generated subject assets.

## `make_character_sheet.py`

Builds a numbered character sheet from separate subject images.

```powershell
python references\scripts\make_character_sheet.py `
  output\person-01.png output\person-02.png output\person-03.png `
  --out output\character-sheet.png
```

## `layer_composite.py`

Composites locked subject layers onto a clean background plate using a placement CSV.

Required CSV columns:

```csv
image,center_x,height,anchor_y,anchor_frac
output/person-01.png,218,450,1123,0.61
```

- `center_x`: horizontal center of the pasted layer on the background.
- `height`: target layer height after scaling.
- `anchor_y`: scene-space contact line, such as seat plane or ground line.
- `anchor_frac`: subject-space anchor, expressed as a fraction of layer height from the layer top.

```powershell
python references\scripts\layer_composite.py `
  --background output\clean-background-plate.png `
  --placements output\placements.csv `
  --out output\final-composite.png `
  --annotated-out output\final-composite-annotated.png `
  --defringe
```
