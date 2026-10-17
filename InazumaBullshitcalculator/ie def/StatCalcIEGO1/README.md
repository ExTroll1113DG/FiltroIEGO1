# StatCalcIEGO1

Calculate Inazuma Eleven GO Light player stats by level, search players and rank them by position. Python 3.8+; the app uses only the standard library. Tkinter is needed for the GUI (on Debian/Ubuntu: `sudo apt install python3-tk`).

Download **StatCalcIEGO1.zip**, extract it and run:

```sh
python StatCalcIEGO1.py ie_a.fa
```

For text mode: `python StatCalcIEGO1.py --cli ie_a.fa`. The `programa.py` launcher remains available for compatibility. Supply your own game data; it is not included.

## Settings and save training

The included `calibracion.json` is clean: no player base corrections or training. The app also works without this file. Keep it beside the script when using settings.

- **Import training...** reads `game.ie4` exported with Checkpoint/JKSM, validates its CRC and saves the imported training to `calibracion.json`. Use the game data matching that save. Re-importing replaces the matching database's training snapshot; it does not accumulate bonuses. Equipment and passive bonuses are excluded.
- **Calibration → Create base JSON** (text menu option 7) creates `calibracion.json` without base corrections. If a save was imported during the current session, its training is retained. Otherwise the JSON has no player changes, even if an older JSON was read at startup. This replaces the active settings file and immediately applies it.
- **Reset to defaults** removes settings, clears the session's imported training and returns to natural stats. Import the save again to restore its training.


## Empty Excel template

Use **StatCalcIEGO1_template.xlsx** with **Choose table and calibrate...**. It contains headers only, with no example players. Enter one observed player/level per row, starting at row 2. Keep all 14 columns in this order:

| Name | Position | Level | FP | TP | Element | Kick | Dribbling | Technique | Block | Speed | Stamina | Catch | Luck |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

Use the exact player name shown in the app. **Fill every column**, including Position and Element: the existing importer requires those fields. Position choices: Forward, Midfielder, Defender, Goalkeeper. Elements: Wind, Wood, Fire, Earth. Level is 1–99; all stats are whole numbers. FP/TP are the maximum values, not the remaining points.

Spanish stat equivalents, in the same order: PE, PT, Tiro, Regate, Tecnica, Defensa, Rapidez, Aguante, Control, Suerte. You can enter multiple observed levels for the same player on separate rows. Record observations without equipment and disclose any training used when comparing natural stats. The reference comparison deducts supported passive jumps; it does not invent curves to fit observations. Do not add title rows or rearrange columns. An untouched, empty template is not a calibration dataset.

The Excel is for **reference comparison**, not for importing save training; training requires `game.ie4`.
