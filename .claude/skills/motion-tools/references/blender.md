# Blender piloté par script (non testé dans ce conteneur)

À utiliser pour la vraie 3D : tissu, lumière, ombres douces, profondeur de champ, flou de mouvement
physique. Blender 4.x se lance sans interface : `blender -b -P scene.py -- --out build/blender/`.

## Installation
- Linux : télécharger l'archive officielle (blender.org), ou `snap install blender --classic`.
  `apt install blender` fournit souvent une version ancienne.
- Le module `bpy` sur PyPI suit une version précise de Python (par exemple 3.11). Il ne s'installe pas
  sur d'autres versions : vérifier `python3 --version` avant de compter dessus.
- Le rendu Cycles sur CPU est lent. EEVEE est rapide mais demande un GPU/EGL ; en conteneur sans GPU,
  préférer Cycles avec peu d'échantillons et le débruitage.

## Squelette (sticker texturé qui entre en ressort, 9:16, 30 i/s)
```python
import bpy, math, os, sys
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
out = argv[argv.index("--out") + 1] if "--out" in argv else "/tmp/blender/"

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.resolution_x, sc.render.resolution_y = 1080, 1920
sc.render.fps = 30
sc.frame_start, sc.frame_end = 1, 60
sc.render.engine = "CYCLES"
sc.cycles.samples = 32
sc.cycles.use_denoising = True
sc.render.use_motion_blur = True                  # flou de mouvement physique
sc.render.motion_blur_shutter = 0.5               # obturateur à 180°, comme le moteur Python

# plan texturé avec un PNG détouré (transparence)
bpy.ops.mesh.primitive_plane_add(size=2)
plane = bpy.context.active_object
plane.scale = (1024 / 1536, 1, 1)
mat = bpy.data.materials.new("sticker"); mat.use_nodes = True
nt = mat.node_tree; bsdf = nt.nodes["Principled BSDF"]
tex = nt.nodes.new("ShaderNodeTexImage")
tex.image = bpy.data.images.load(os.path.abspath("build/cutouts/article_02.png"))
nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
nt.links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
if hasattr(mat, "blend_method"):                 # EEVEE < 4.2 ; ignoré par Cycles
    mat.blend_method = "BLEND"
plane.data.materials.append(mat)
plane.rotation_euler = (math.radians(90), 0, 0)

# animation : keyframes + interpolation « BACK » (dépassement) ou « ELASTIC »
for f, s in ((1, 0.55), (11, 1.0)):
    plane.scale = (s * 1024 / 1536, s, s); plane.keyframe_insert("scale", frame=f)
for fc in plane.animation_data.action.fcurves:   # Blender ≥ 4.4 : actions « slotted », voir la doc si erreur
    for kp in fc.keyframe_points:
        kp.interpolation = "BACK"; kp.easing = "EASE_OUT"

# caméra et lumière
bpy.ops.object.camera_add(location=(0, -6, 0), rotation=(math.radians(90), 0, 0))
sc.camera = bpy.context.active_object
sc.camera.data.lens = 50
bpy.ops.object.light_add(type="AREA", location=(2, -4, 3)); bpy.context.active_object.data.energy = 600
sc.world = bpy.data.worlds.new("w"); sc.world.color = (0.98, 0.96, 0.94)

sc.render.image_settings.file_format = "PNG"
sc.render.filepath = out + "f_"
bpy.ops.render.render(animation=True)
```
Puis encoder avec ffmpeg (`-framerate 30 -i f_%04d.png -c:v libx264 -pix_fmt yuv420p`) et relire avec
`motion-review`. L'API change entre les versions majeures (noms des entrées de nœuds, `blend_method`) :
en cas d'erreur, lire le message, puis la doc de la version installée (`blender --version`).

## Bonnes pratiques
- Tester sur 5 à 10 images (`sc.frame_end = 10`) et peu d'échantillons, puis monter.
- Garder le BPM : une image Blender = une image vidéo, donc un temps = 15 images à 120 BPM.
- Le grain papier, le tremblé stop-motion et le collage restent plus simples à ajouter en
  post-production (Python/ffmpeg) qu'en 3D.
