# HERO – Seedance image-to-video prompts

How to use (Seedance, image-to-video mode):

1. For each shot upload `shots/NN.png` as the **first frame**.
2. Aspect ratio **9:16**, highest resolution available, shortest duration offered (usually 4–5 s).
3. Paste the shot prompt. If there is a separate negative-prompt field, paste the negative prompt there; otherwise append it to the end.
4. Download each clip as `clips/01.mp4 … clips/12.mp4`. Only the best ~1 second of each clip is used in the final 12-second edit.

The can is already in the first frame, so never describe the label again in detail – just tell the model to keep it unchanged.

**Negative prompt (all shots):**
`warped text, changing letters, morphing logo, extra logos, wrong can shape, blurry product, cartoon, watermark, subtitles, extra fingers, deformed hands`

---

**01 – Shards** (`shots/01.png`)
`Slow motion. Gold-tinted glass shards fly outward and tumble through the air, water crown splashes up around the base of the can and droplets rain down on the wet black mirror floor. The can stays perfectly still, its label and lettering unchanged. Slow low-angle push-in, shallow depth of field, anamorphic flare flickers. Cinematic, photorealistic.`

**02 – Macro tilt** (`shots/02.png`)
`Extreme macro. Camera slowly tilts upward along the can. Cold condensation beads slide down the matte black surface, a gold rim light sweeps across the wolf emblem and lettering. The can itself does not move, label and lettering unchanged. Photorealistic, shallow depth of field.`

**03 – Tab pull** (`shots/03.png`)
`The taped fighter's finger pulls the tab and the can cracks open, a burst of cold mist and fine spray shoots from the opening and drifts away. The gripping hand tightens slightly. Fog moves through the dark pine forest behind. Handheld micro-shake, label and lettering unchanged, photorealistic.`

**04 – Wolf strides** (`shots/04.png`)
`The wolf made of golden lightning strides powerfully straight toward the camera, shoulders rolling, head low, eyes glowing. Electric arcs crawl along its fur, embers and sparks stream upward, the beam of fiery light from above pulses. Its reflection moves on the wet black floor. Slow dolly back, photorealistic VFX.`

**05 – Wolf prowls** (`shots/05.png`)
`Fast side tracking shot. The lightning wolf runs low and fast across the glossy black floor, legs galloping, trailing streaks of golden light and floating particles behind it, crackling electricity along its body, reflection racing beneath. Motion blur, photorealistic VFX.`

**06 – Start block** (`shots/06.png`)
`Extreme close-up. The calf muscle tenses, the shoe presses into the starting block, then explodes forward out of frame. Gold sparks burst from under the sole, water droplets spray off the wet track. Slight slow motion, then a fast release. Photorealistic.`

**07 – Runner** (`shots/07.png`)
`Low-angle tracking shot moving backward in front of the runner as he sprints hard down the wet asphalt road toward camera, arms pumping, water spraying from every footstrike, a gold flare flashing at the shoe. Mist drifts over the pine mountains and the distant crane. Motion blur, overcast cold light, photorealistic.`

**08 – Wolf leap** (`shots/08.png`)
`Dramatic slow motion. The glowing golden wolf leaps over the can toward the camera, snarling, jaws opening, claws of light reaching forward, lightning crackling off its fur, raindrops hanging in the air. The can stays still on the wet road, lettering unchanged. Fog drifts through the pines. Photorealistic VFX.`

**09 – Skates** (`shots/09.png`)
`Slow motion. The skate blade carves hard across the ice in a sharp stop, a fan of ice spray and gold sparks bursts toward the camera, stadium spotlights flare and streak in the background. Low tracking camera, photorealistic.`

**10 – Rowing pull** (`shots/10.png`)
`The chalked hand pulls the handle hard toward the body, forearm muscles and veins tensing, chalk dust bursting off the grip, sweat drops flying. Arena lights streak behind with heavy motion blur. Quick camera follow, photorealistic.`

**11 – Can + wolf** (`shots/11.png`)
`The giant lightning wolf behind the can throws its head back and roars, lightning swirling around it, burning light streaks and sparks rush outward from the center. Fast push-in toward the can. The can stays perfectly still and sharp, label and lettering unchanged. Reflections flicker on the wet black floor. Photorealistic VFX.`

**12 – Final hero shot** (`shots/12.png`)
`Slow, smooth push-in on the can. Gold dust floats gently through the air, a soft light sweep glides across the can, one condensation drop slides down. The can stays perfectly still, label and lettering unchanged, calm glossy reflection on the wet black floor. Clean, elegant ending. Photorealistic.`

---

## Alternative: one multi-shot generation

If your Seedance version supports multi-shot prompts with a reference image, upload `shots/12.png` as the product reference and use:

`12-second vertical 9:16 energy drink commercial, fast cuts of about one second each, dark moody look, teal-black shadows and gold highlights, wet reflective surfaces, anamorphic flares. The black-and-gold HERO can from the reference image must stay identical in every shot. Shot 1: the can on a wet black mirror floor, gold shards exploding in slow motion with water splashing. Shot 2: macro tilt up the can, condensation, gold wolf emblem. Shot 3: a fighter's taped hand pulls the tab, cold mist hisses out. Shot 4: a wolf made of golden lightning strides toward camera under a beam of fiery light. Shot 5: the lightning wolf sprints across a glossy black floor. Shot 6: close-up of a shoe launching from a sprint starting block with a gold flash. Shot 7: a runner bursts down a wet road, misty pine mountains behind. Shot 8: the golden wolf leaps over the can lying on the wet road. Shot 9: ice-skate blades carve ice with ice spray and gold sparks. Shot 10: a chalked hand pulls a rowing handle, arena lights streaking. Shot 11: the upright can with a huge lightning wolf roaring behind it, light streaks rushing outward. Shot 12: final centered can, slow push-in, gold dust, clean reflection. Sound: whooshes, heavy impacts on every cut, can-opening hiss, electric crackle.`

The per-shot route above gives much better control over the can's label.
