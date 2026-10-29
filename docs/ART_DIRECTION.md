# Art direction: the Gradius II (Famicom) style, measured (Phase 4)

Owner's rule (docs/DECISIONS.md, phase 4): the Gradius II Famicom assets are the art direction;
everything that does not come from Gradius II is standardised to the same graphic quality
(palette, shading, detail), player ships included. This guide is measured from the Gradius II
evidence (every sprite frame and palette the game shows, stage CIRAM dumps), not from taste.
Image and tool paths below refer to the private evidence folder (`art/`), never to git.

Result for the player ships (owner decision: Salamander FC ships recoloured to the Gradius II
palette): the Salamander FC P1 ship already uses exactly the Gradius II Vic Viper ramps (body
20/22/02, nose and exhaust 20/27/16) and P2 is the same palette swap Gradius II uses for its
own second player, so the recolour is the identity; only optional pixel work on the darker
hull is noted.


All numbers are counted over the Gradius II evidence (`/home/claude/work/evidence/gradius2_fc/`): 565 distinct sprite frames of 113 objects (tiles and palette RAM as the game showed them) and the stage CIRAM dumps. Colours are NES palette indices (hex). Tools: `art/tools/g2style.py`, `g2bg.py`, `build_style.py`; raw numbers in `style_measure.json`, `style_bg.json`, `style_guide.json`.

## 1. Palettes

### Sprite palettes

4 sprite palettes per stage: P0 = 20/22/02 (blue) and P1 = 20/27/16 (red-orange) in every stage and screen of play; P2 = 20/12/16 (stage 3: 20/12/26) two-hue blue+red; P3 = the stage material ramp (st1/st2 36/24/04 pink, st3 38/18/08 yellow then 34/14/04 purple, st4 20/10/00 grey, st5 10/00/06 grey-red, st6 20/00/0C grey-cyan metal, st7 36/15/06 flesh). Sprite colour 0 is transparent; slot 1 is the light, slot 3 the dark/outline colour (luminance order light-mid-dark in 75 % of the sprite palette-frames; the rest is the two-hue P2 20/12/16 whose blue slot 2 is darker than its red slot 3).

| stage | P0 | P1 | P2 | P3 (material) |
|---|---|---|---|---|
| 1 Artificial Sun | 20/22/02 | 20/27/16 | 20/12/16 | 36/24/04 |
| 2 Alien base (NES stage 2) | 20/22/02 | 20/27/16 | 20/12/16 | 36/24/04 |
| 3 Volcano - Crystal | 20/22/02 | 20/27/16 | 20/12/26 | 38/18/08 |
| 3 Volcano - Crystal | 20/22/02 | 20/27/16 | 20/12/16 | 34/14/04 |
| 4 Moai | 20/22/02 | 20/27/16 | 20/12/16 | 20/10/00 |
| 5 Boss rush | 20/22/02 | 20/27/16 | 20/12/16 | 10/00/06 |
| 6 Enemy base (fortress, high speed) | 20/22/02 | 20/27/16 | 20/12/16 | 20/00/0C |
| 7 Gofer's lair | 20/22/02 | 20/27/16 | 20/12/16 | 36/15/06 |

### BG palettes (sets held for >= 2 % of the stage frames, most used first; palette 0 = stars)

BG palette 0 = star field (0F/0F/0F -> 00/02/02 -> 10/12/12 -> 20/22/22 fade, 8 frames per step, held at 20/22/22 during play); palettes 1-3 = the stage theme ramps, ordered light/mid/dark in 79 % of the palette-frames (slot 3 darkest in 86 %); universal background 0F.

| stage | share of frames | BG0 | BG1 | BG2 | BG3 |
|---|---|---|---|---|---|
| 1 Artificial Sun | 18 % | 20/22/22 | 37/26/06 | 10/1A/09 | 06/07/08 |
| 1 Artificial Sun | 16 % | 20/22/22 | 20/27/16 | 0F/0F/0F | 17/27/16 |
| 1 Artificial Sun | 12 % | 20/22/22 | 20/27/16 | 10/1A/09 | 16/17/07 |
| 1 Artificial Sun | 12 % | 20/22/22 | 20/26/17 | 10/1A/09 | 17/06/08 |
| 1 Artificial Sun | 11 % | 20/22/22 | 37/26/06 | 0F/0F/0F | 06/26/17 |
| 1 Artificial Sun | 11 % | 20/22/22 | 20/26/17 | 0F/0F/0F | 06/26/17 |
| 1 Artificial Sun | 8 % | 20/22/22 | 20/26/16 | 0F/0F/0F | 06/26/16 |
| 1 Artificial Sun | 6 % | 20/22/22 | 20/27/16 | 10/1A/09 | 16/16/06 |
| 1 Artificial Sun | 5 % | 20/22/22 | 37/26/06 | 0F/0F/0F | 07/26/06 |
| 2 Alien base (NES stage 2) | 71 % | 20/22/22 | 10/18/0A | 0C/18/0A | 0C/17/07 |
| 2 Alien base (NES stage 2) | 19 % | 20/22/22 | 10/18/0A | 20/00/06 | 20/00/0C |
| 2 Alien base (NES stage 2) | 8 % | 20/22/22 | 0F/0F/0F | 20/22/02 | 27/17/07 |
| 3 Volcano - Crystal | 50 % | 20/22/22 | 34/14/0C | 32/12/02 | 28/19/17 |
| 3 Volcano - Crystal | 28 % | 20/22/22 | 37/27/17 | 07/27/17 | 28/19/17 |
| 3 Volcano - Crystal | 11 % | 20/22/22 | 06/1C/0C | 32/1C/0C | 34/14/04 |
| 3 Volcano - Crystal | 5 % | 20/22/22 | 16/1C/0C | 32/1C/0C | 34/14/04 |
| 3 Volcano - Crystal | 5 % | 20/22/22 | 26/1C/0C | 32/1C/0C | 34/14/04 |
| 4 Moai | 40 % | 20/22/22 | 09/19/08 | 20/00/08 | 10/19/08 |
| 4 Moai | 36 % | 20/22/22 | 20/27/18 | 20/00/08 | 27/17/08 |
| 4 Moai | 23 % | 20/22/22 | 20/26/06 | 20/00/08 | 27/17/08 |
| 5 Boss rush | 39 % | 20/22/22 | 38/18/08 | 20/1C/02 | 20/16/07 |
| 5 Boss rush | 23 % | 20/22/22 | 20/00/06 | 20/10/12 | 32/22/12 |
| 5 Boss rush | 16 % | 20/22/22 | 20/10/00 | 20/10/17 | 32/22/12 |
| 5 Boss rush | 11 % | 20/22/22 | 27/16/07 | 27/16/20 | 32/22/12 |
| 5 Boss rush | 11 % | 20/22/22 | 26/16/07 | 26/16/20 | 20/16/07 |
| 6 Enemy base (fortress, high speed) | 20 % | 20/22/22 | 20/00/0C | 20/00/06 | 2B/00/0A |
| 6 Enemy base (fortress, high speed) | 17 % | 20/22/22 | 20/00/0C | 20/00/06 | 20/26/16 |
| 6 Enemy base (fortress, high speed) | 10 % | 20/22/22 | 20/00/0C | 20/00/16 | 2B/00/0A |
| 6 Enemy base (fortress, high speed) | 10 % | 20/22/22 | 20/00/0C | 20/00/26 | 2B/00/0A |
| 6 Enemy base (fortress, high speed) | 9 % | 20/22/22 | 20/00/0C | 20/00/26 | 20/26/16 |
| 6 Enemy base (fortress, high speed) | 9 % | 20/22/22 | 20/00/0C | 20/00/16 | 20/26/16 |
| 6 Enemy base (fortress, high speed) | 7 % | 20/22/22 | 20/00/0C | 06/00/0A | 2B/00/0A |
| 6 Enemy base (fortress, high speed) | 6 % | 20/22/22 | 20/00/0C | 20/00/06 | 20/25/16 |
| 6 Enemy base (fortress, high speed) | 4 % | 20/22/22 | 20/00/0C | 26/00/0A | 2B/00/0A |
| 6 Enemy base (fortress, high speed) | 3 % | 20/22/22 | 20/00/0C | 16/00/0A | 2B/00/0A |
| 6 Enemy base (fortress, high speed) | 3 % | 20/22/22 | 20/00/0C | 20/00/16 | 20/25/16 |
| 6 Enemy base (fortress, high speed) | 3 % | 20/22/22 | 20/00/0C | 20/00/26 | 20/25/16 |
| 7 Gofer's lair | 70 % | 20/22/22 | 36/25/16 | 25/16/07 | 27/16/07 |
| 7 Gofer's lair | 28 % | 20/22/22 | 27/16/06 | 20/16/06 | 27/16/07 |

### Screens (BG 0-3 / sprites 0-3)

| screen | BG | sprites |
|---|---|---|
| g2.screen.intro | 20/26/17 20/10/00 00/26/17 10/28/16 | 20/22/02 20/27/16 20/27/12 36/24/04 |
| g2.screen.logo_animation | 39/0F/39 39/0F/39 39/39/39 0F/0F/0F | 0F/22/02 20/27/16 20/27/12 36/24/04 |
| g2.screen.title | 20/06/35 20/06/16 33/25/24 10/28/16 | 0F/22/02 20/06/16 20/27/12 36/24/04 |
| g2.screen.power_meter_select | 20/22/12 20/16/12 10/00/0C 10/07/0C | 20/22/02 20/27/16 20/27/12 36/24/04 |
| g2.screen.stage_start | 20/06/35 20/06/16 33/25/24 10/28/16 | 0F/22/02 20/06/16 20/27/12 36/24/04 |
| g2.screen.sound_mode | 20/06/35 20/06/16 33/25/24 10/28/16 | 0F/22/02 20/06/16 20/27/12 36/24/04 |
| g2.screen.pause | 20/22/22 37/26/06 10/1A/09 06/07/08 | 20/22/02 20/27/16 20/12/16 36/24/04 |
| g2.screen.game_over_continue | 20/06/35 20/06/16 33/25/24 10/28/16 | 0F/22/02 20/06/16 20/27/12 36/24/04 |
| g2.screen.two_player | 20/22/22 37/26/06 10/1A/09 06/07/08 | 20/22/02 20/27/16 20/12/16 36/24/04 |
| g2.screen.ending_escape | 20/0C/00 0F/0F/0F 10/1A/09 17/06/08 | 20/00/02 20/27/16 20/22/0C 36/24/04 |
| g2.screen.staff_roll | 20/00/19 0A/00/19 0A/00/06 0F/0F/0F | 20/00/02 20/27/16 20/22/0C 36/24/04 |

### Ramps (slot1/slot2/slot3 = light/mid/dark)

| ramp | hues | where | sprite uses (frames x occurrences) | classes |
|---|---|---|---|---|
| 20/27/16 | orange-brown, red | bg+sprite 1,2,3,4,5,6,7 | 678968 | option, player_missile, explosion, player_ship, capsule |
| 20/22/02 | blue | bg+sprite 1,2,3,4,5,6,7 | 603384 | player_shot, boss_beam, player_ship, enemy_bullet, enemy_craft |
| 10/00/06 | red | sprite 5 | 59960 | boss_sprite_part |
| 34/14/04 | magenta | bg+sprite 3 | 52126 | rock_crystal |
| 20/12/16 | blue, red | sprite 1,2,3,4,5,6 | 42927 | organic_enemy, enemy_craft |
| 20/12/26 | blue, red | sprite 1,3,4,6 | 8335 | enemy_craft |
| 20/10/00 | grey | bg+sprite 4,5 | 8010 | rock_crystal |
| 20/00/02 | blue | sprite  | 3086 | screen_sprite |
| 20/00/0C | cyan | bg+sprite 2,6 | 2929 | enemy_craft, boss_sprite_part |
| 20/22/0C | blue, cyan | sprite  | 1535 | screen_sprite |
| 36/24/04 | magenta, red | sprite 2 | 1145 | organic_enemy, enemy_craft |
| 36/15/06 | pink-red, red | sprite 7 | 663 | organic_enemy |
| 0F/22/02 | blue | sprite  | 575 | screen_sprite |
| 38/18/08 | yellow-brown | bg+sprite 3,4,5 | 234 | enemy_craft |
| 20/06/16 | red | sprite  | 98 | screen_sprite |
| 20/22/22 | blue | bg 1,2,3,4,5,6,7 | 0 |  |
| 37/26/06 | orange-brown, red | bg 1 | 0 |  |
| 10/1A/09 | green, olive-green | bg 1 | 0 |  |
| 06/07/08 | orange-brown, red, yellow-brown | bg 1 | 0 |  |
| 0F/0F/0F | grey | bg 1,2 | 0 |  |
| 17/27/16 | orange-brown, red | bg 1 | 0 |  |
| 16/17/07 | orange-brown, red | bg 1 | 0 |  |
| 20/26/17 | orange-brown, red | bg 1 | 0 |  |
| 17/06/08 | orange-brown, red, yellow-brown | bg 1 | 0 |  |
| 06/26/17 | orange-brown, red | bg 1 | 0 |  |
| 20/26/16 | red | bg 1,6 | 0 |  |
| 06/26/16 | red | bg 1 | 0 |  |
| 16/16/06 | red | bg 1 | 0 |  |
| 07/26/06 | orange-brown, red | bg 1 | 0 |  |
| 10/18/0A | green, yellow-brown | bg 2 | 0 |  |
| 0C/18/0A | cyan, green, yellow-brown | bg 2 | 0 |  |
| 0C/17/07 | cyan, orange-brown | bg 2 | 0 |  |
| 20/00/06 | red | bg 2,5,6 | 0 |  |
| 27/17/07 | orange-brown | bg 2 | 0 |  |
| 34/14/0C | cyan, magenta | bg 3 | 0 |  |
| 32/12/02 | blue | bg 3 | 0 |  |
| 28/19/17 | olive-green, orange-brown, yellow-brown | bg 3 | 0 |  |
| 37/27/17 | orange-brown | bg 3 | 0 |  |
| 07/27/17 | orange-brown | bg 3 | 0 |  |
| 06/1C/0C | cyan, red | bg 3 | 0 |  |

### Ramp per object class (share of sprite uses)

| class | ramps |
|---|---|
| player_ship | 20/22/02 50%, 20/27/16 50% |
| force_field | 20/22/02 84%, 20/27/16 16% |
| option | 20/27/16 100% |
| player_shot | 20/22/02 100%, 20/27/16 0% |
| player_missile | 20/27/16 100% |
| explosion | 20/27/16 100%, 20/22/02 0% |
| capsule | 20/27/16 98%, 20/22/02 2% |
| enemy_bullet | 20/22/02 95%, 20/27/16 5% |
| boss_beam | 20/22/02 92%, 20/27/16 8% |
| enemy_craft | 20/22/02 48%, 20/27/16 24%, 20/12/26 12%, 20/12/16 11% |
| organic_enemy | 20/12/16 54%, 20/22/02 43%, 20/27/16 1%, 36/24/04 1% |
| fire_creature | 20/27/16 100% |
| rock_crystal | 34/14/04 84%, 20/10/00 13%, 20/27/16 3% |
| boss_sprite_part | 10/00/06 86%, 20/27/16 13%, 20/22/02 1%, 20/00/0C 0% |
| screen_sprite | 20/27/16 38%, 20/00/02 36%, 20/22/0C 18%, 0F/22/02 7% |

Palette sheets: `png/g2_palettes_per_stage.png`, `png/g2_ramps_per_class.png`, `png/g2_palettes_screens.png`; class crops `png/g2_class_*.png`.

## 2. Shading and drawing rules

* **Outline**: Every sprite has a 1-pixel rim in the darkest colour of its own ramp (slot 3: 02, 16, 0C, 04, 06, 08...), on all four sides; it is a coloured shadow, not black. Edge pixels (opaque pixels next to transparency): 62.6 % darkest tone, 25.3 % mid, 12.1 % light; by side left/right/top/bottom dark = 66%/67%/62%/63%. Only 27 % of darkest-tone pixels are black-ish (lum < 40): the rim is the dark hue of the ramp. single-hue ramps: slot 3 carries 58-94 % of all edge pixels (20/22/02 64 %, 20/27/16 58 %, 38/18/08 94 %, 10/00/06 82 %); two-hue ramp 20/12/16: the blue slot 2 carries 57 % and the red slot 3 is an accent.
* **Light**: No global light direction: tones change symmetrically (pillow / centre-lit shading); highlights sit in the middle of each mass, rims dark all round. Only rock/crystal and BG bosses lean to light-from-above. Of all tone steps between neighbouring pixels, the lighter pixel is above in 50.4 % and left in 50.7 % (50 % = no direction). Rock: 57.7 % above; BG-drawn bosses 52.7 % above.
* **Tones**: One palette (3 colours) per 8x16 sprite; objects use exactly 3 colours of one ramp; only the player ship (and its 2P/ending variants) mixes two palettes per object. Colours per frame: {'6': 7, '3': 533, '2': 11, '1': 7, '4': 3, '5': 4}; palettes per frame: {'2': 14, '1': 551}.
* **Dithering**: Dithering is rare: 3.9 % of fully opaque 2x2 windows are checkerboards (mostly the ion rings, beams, crystals and BG bosses); surfaces are drawn with solid tone bands. Per material: metal 1.5%, organic 4.1%, rock 4.7%, crystal 6.8%, energy 6.3%, fire 2.9%.
* **Anti-aliasing**: No anti-aliasing against the background: silhouettes end on the dark rim (62.6 % of edge pixels dark, 25.3 % mid, 12.1 % light); mid tone is used inside to step from rim to highlight.

| material | rule | edge dark/mid/light | interior dark/mid/light | lighter above / left | checkerboard |
|---|---|---|---|---|---|
| metal | blue (20/22/02) or grey ramps; light core bands, dark rim; 3 tones, banded, dither 1.5 % | 0.56/0.27/0.17 | 0.25/0.38/0.38 | 0.50 / 0.51 | 0.015 |
| organic | pink/flesh/blue ramps; heavier dark rim (73 % of edges dark), rounded highlight blobs | 0.73/0.19/0.07 | 0.30/0.40/0.30 | 0.50 / 0.49 | 0.041 |
| rock | grey ramp 00/10/20; light from above (58 % of tone steps lighter above), mottled (dither 4.7 %) | 0.67/0.26/0.07 | 0.41/0.32/0.28 | 0.58 / 0.50 | 0.047 |
| crystal | purple 04/14/34 or blue; facets in bands, highlight up-left, dither 6.8 % | 0.75/0.20/0.05 | 0.38/0.40/0.22 | 0.51 / 0.51 | 0.068 |
| energy | shots/beams/rings: dark rim + white core, mostly 8x16 single sprites; force field and options = 3-tone ellipses | 0.71/0.22/0.06 | 0.16/0.45/0.40 | 0.51 / 0.55 | 0.063 |
| fire | red-orange 16/27/20; dark-red rim 72 %, white-hot core | 0.71/0.24/0.05 | 0.42/0.34/0.24 | 0.50 / 0.50 | 0.029 |

### Sizes and layouts

8x16 sprites; small enemies, capsules, explosions and options = a 16x16 pair (2 sprites side by side, code $01-$7F pair tables); ship 24x32 = 6 sprites (3x2); big sprites by metasprite lists; bosses: 15 of 15 boss/sub-boss bodies are BG tiles (3 of them with sprite parts).

| class | median size px | range | 8x16 sprites per frame |
|---|---|---|---|
| player_ship | [25, 32] | [[24, 32], [25, 35]] | {'6': 3, '4': 1, '5': 1} |
| force_field | [24, 16] | [[24, 16], [24, 16]] | {'3': 4} |
| option | [8, 16] | [[8, 16], [16, 16]] | {'2': 1, '1': 2} |
| player_shot | [8, 16] | [[8, 16], [32, 32]] | {'1': 8, '2': 3, '8': 1} |
| player_missile | [8, 16] | [[8, 16], [8, 16]] | {'1': 8} |
| explosion | [16, 16] | [[8, 16], [48, 48]] | {'2': 4, '17': 1, '8': 1, '6': 1, '5': 1, '1': 5, '4': 2} |
| capsule | [16, 16] | [[16, 16], [16, 16]] | {'2': 4} |
| enemy_bullet | [8, 16] | [[8, 16], [16, 16]] | {'1': 19, '2': 11} |
| boss_beam | [16, 16] | [[8, 16], [24, 32]] | {'4': 2, '6': 1, '3': 8, '1': 5, '2': 14} |
| enemy_craft | [16, 16] | [[8, 16], [32, 32]] | {'2': 256, '1': 6, '8': 12, '3': 7} |
| organic_enemy | [16, 16] | [[8, 16], [24, 32]] | {'2': 63, '3': 4, '6': 12, '1': 2} |
| fire_creature | [24, 21] | [[15, 16], [32, 32]] | {'2': 15, '3': 3, '5': 1, '7': 2, '8': 6, '6': 7} |
| rock_crystal | [16, 16] | [[8, 16], [32, 32]] | {'2': 8, '4': 1, '3': 1, '1': 1, '8': 1} |
| boss_sprite_part | [16, 16] | [[8, 16], [32, 48]] | {'2': 17, '1': 3, '6': 3, '7': 1, '4': 1} |
| screen_sprite | [46, 43] | [[8, 16], [64, 64]] | {'1': 3, '10': 3, '3': 1, '4': 1, '6': 1, '2': 3, '29': 3, '30': 1, '31': 2, '14': 1, '13': 1, '9': 1} |

## 3. Background rules

* one BG layer; horizontal mirroring, scrolled map of 32x30 tiles per screen (vertical sections scroll into the second nametable)
* mid-screen CHR splits instead of parallax: IRQ #1 can shift CHR4/5 by -5 banks ($03C1=1, stage 1 solar flares) or map $6D-$6F (title); the HUD is a second split at line 205 with its own banks
* tile animation by CHR bank cycling (table $EB1D: stage 1 sun/flares CHR5/CHR6 every 7 frames through 4 banks; second record CHR5 $12-$15)
* star field = palette-0 BG tiles; palette faded in/out in 8-frame steps, no twinkle
* attribute (16x16) colour changes are rare except in stage 1 and 4 (28-31 % of neighbouring 16x16 blocks change palette); elsewhere 8-13 %: large areas of one ramp
* BG tiles use 2-3 colours (3 colours in 50-74 % of the filled tiles of a stage) with the darkest slot on the edges of shapes, as in the sprites
* reuse: a screen shows 28-85 distinct filled tiles; reuse factor 1.1 (stage 5 boss rush, unique boss art) to 6.0 (stage 6 fortress panels)

| stage | filled cells / screen (of 768) | distinct filled tiles / screen | reuse | 16x16 palette changes | tiles under 2+ palettes | colours per tile (1/2/3) | checkerboard |
|---|---|---|---|---|---|---|---|
| 1 Artificial Sun | 83 | 64 | 1.22 | 0.279 | 128 of 1323 | 119/446/758 | 0.044 |
| 2 Alien base (NES stage 2) | 227 | 54 | 3.62 | 0.084 | 31 of 427 | 13/98/316 | 0.042 |
| 3 Volcano - Crystal | 112 | 44 | 2.25 | 0.088 | 41 of 383 | 5/117/261 | 0.044 |
| 4 Moai | 179 | 75 | 1.85 | 0.314 | 15 of 497 | 21/194/282 | 0.045 |
| 5 Boss rush | 85 | 85 | 1.07 | 0.080 | 3 of 1002 | 71/425/506 | 0.062 |
| 6 Enemy base (fortress, high speed) | 175 | 28 | 6.02 | 0.106 | 53 of 332 | 20/77/235 | 0.050 |
| 7 Gofer's lair | 283 | 56 | 4.26 | 0.126 | 71 of 400 | 6/108/286 | 0.049 |

Star palette (BG palette 0) sequence: 0F/0F/0F -> 00/02/02 -> 10/12/12 -> 20/22/22 -> 10/12/12, step [12, 8, 8] frames.

## 4. Recolour of the NES visuals that are not from Gradius II

`manifests/recolour_plan.json`: 51 assets (Salamander FC 24, Gradius 25, Life Force 2). 14 already
use the Gradius II ramps (identity, incl. the player ships, options pending the P1/P2 palette
exchange), 29 are recoloured slot by slot to the ramp of their class, 8 screens colour by colour;
22 Gradius assets need their CHR re-indexed (their palettes store the dark colour first); 29 have an
incomplete dark rim and 7 are flat, noted as pixel work.

## 5. Conversion of MSX-only drawings (phase 5 method, first sample)

A converter (private evidence, `art/tools/convert_msx.py`) keeps silhouette, size and design,
picks one Gradius II palette per object by class and hue, puts the darkest tone on the rim, the
mid tone on the body and centre-lit highlights, keeps MSX inner detail as tone changes, and
outputs 8x16 sprite tiles with OAM layouts or BG tiles with 16x16 attributes. First sample (8
assets): compact craft (Nemesis 2 and 3) and round organic sprites reach a usable first pass;
1-pixel line drawings (Salamander), spiky bosses and stage art do not reach Gradius II quality
automatically (highlights placed by quota, dither from MSX holes, hue shifts, attribute limits)
and need a pixel-art pass per asset on top of the converter output.
