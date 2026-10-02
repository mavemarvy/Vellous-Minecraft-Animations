#!/usr/bin/env python3
from __future__ import annotations

import math
from pathlib import Path

import bpy
from mathutils import Vector

FPS = 24
FRAME_END = 120
W = 540
H = 960
EXPORT_DIR = Path("projects/short-001-zombie-fight/exports")
EXPORT_DIR.mkdir(parents=True, exist_ok=True)

# ---------- helpers ----------
def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

def empty(name, loc=(0,0,0)):
    o = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(o)
    o.location = loc
    return o

def mat(name, color, roughness=0.65, metallic=0.0, emission=None):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    if bsdf:
        if 'Base Color' in bsdf.inputs:
            bsdf.inputs['Base Color'].default_value = (*color, 1.0)
        if 'Roughness' in bsdf.inputs:
            bsdf.inputs['Roughness'].default_value = roughness
        if 'Metallic' in bsdf.inputs:
            bsdf.inputs['Metallic'].default_value = metallic
        if emission:
            if 'Emission Color' in bsdf.inputs:
                bsdf.inputs['Emission Color'].default_value = (*emission, 1.0)
                bsdf.inputs['Emission Strength'].default_value = 1.8
            elif 'Emission' in bsdf.inputs:
                bsdf.inputs['Emission'].default_value = (*emission, 1.0)
    return m

def cube(name, loc, size, material=None, bevel=0.01):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o = bpy.context.object
    o.name = name
    o.scale = (size[0]/2, size[1]/2, size[2]/2)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if material:
        o.data.materials.append(material)
    if bevel > 0:
        mod = o.modifiers.new(name='Bevel', type='BEVEL')
        mod.width = bevel
        mod.segments = 1
    return o

def key(o, frame, loc=None, rot=None, scale=None):
    if loc is not None:
        o.location = loc
        o.keyframe_insert('location', frame=frame)
    if rot is not None:
        o.rotation_euler = rot
        o.keyframe_insert('rotation_euler', frame=frame)
    if scale is not None:
        o.scale = scale
        o.keyframe_insert('scale', frame=frame)

def parent(child, par):
    child.parent = par

# ---------- setup ----------
clear_scene()

MAT_GRASS = mat('Grass', (0.14, 0.42, 0.11), roughness=1.0)
MAT_PATH = mat('Path', (0.38, 0.31, 0.21), roughness=1.0)
MAT_WOOD = mat('Wood', (0.43, 0.25, 0.11), roughness=0.9)
MAT_PLANK = mat('Plank', (0.58, 0.39, 0.19), roughness=0.85)
MAT_ROOF = mat('Roof', (0.23, 0.09, 0.05), roughness=1.0)
MAT_SKIN = mat('Skin', (0.63, 0.40, 0.26))
MAT_SHIRT = mat('Shirt', (0.06, 0.57, 0.68))
MAT_PANTS = mat('Pants', (0.13, 0.20, 0.56))
MAT_HAIR = mat('Hair', (0.19, 0.10, 0.05))
MAT_ZSKIN = mat('ZombieSkin', (0.18, 0.52, 0.22))
MAT_ZSHIRT = mat('ZombieShirt', (0.06, 0.38, 0.43))
MAT_ZPANTS = mat('ZombiePants', (0.20, 0.14, 0.42))
MAT_WHITE = mat('White', (0.95, 0.95, 0.95))
MAT_BLUE = mat('Blue', (0.08, 0.28, 0.72))
MAT_DARK = mat('Dark', (0.03, 0.03, 0.03))
MAT_SWORD = mat('Sword', (0.70, 0.83, 0.90), roughness=0.25, metallic=0.45)
MAT_HILT = mat('Hilt', (0.12, 0.12, 0.12), roughness=0.5, metallic=0.2)
MAT_TORCH = mat('TorchGlow', (1.0, 0.42, 0.12), emission=(1.0, 0.35, 0.12))

cube('Ground', (0, 3, -0.5), (18, 20, 1), MAT_GRASS, bevel=0)
cube('Path', (0, 0.5, -0.02), (4.5, 12, 0.08), MAT_PATH, bevel=0)

# side houses to frame the shot
for prefix, x, y, sx, sy in [
    ('HouseL', -4.9, 2.2, 3.4, 3.2),
    ('HouseR', 4.9, 2.0, 3.8, 3.4),
    ('HouseBack', -4.1, 7.3, 3.0, 3.0),
]:
    cube(prefix+'_body', (x, y, 1.25), (sx, sy, 2.5), MAT_PLANK, bevel=0)
    cube(prefix+'_roof', (x, y, 3.0), (sx+0.6, sy+0.6, 0.45), MAT_ROOF, bevel=0)
    cube(prefix+'_door', (x, y-sy/2-0.02, 0.85), (0.8, 0.10, 1.7), MAT_WOOD, bevel=0)

# wall, with only a few debris pieces animated
static_wall = []
debris = []
for ix in range(-2, 3):
    for iz in range(0, 4):
        loc = (ix * 0.75, 2.60, 0.38 + iz * 0.75)
        if abs(ix) <= 1 and iz <= 2:
            debris.append((cube(f'Debris_{ix}_{iz}', loc, (0.68, 0.55, 0.68), MAT_WOOD), ix, iz))
        else:
            static_wall.append(cube(f'Wall_{ix}_{iz}', loc, (0.68, 0.55, 0.68), MAT_WOOD))

for piece, ix, iz in debris:
    start = Vector(piece.location)
    key(piece, 1, loc=start)
    key(piece, 12, loc=(start.x + ix * 0.32, start.y - 1.4 - 0.15*iz, start.z + 0.8 - 0.12*iz), rot=(0.8, 0.35*ix, 0.9*ix))
    key(piece, 28, loc=(start.x + ix * 0.56, start.y - 2.1 - 0.20*iz, max(0.05, start.z - 0.35)), rot=(1.4, 0.6*ix, 1.8*ix))

# torches
for x, y in [(-2.8, 4.5), (2.8, 4.5), (-3.2, 0.3), (3.2, 0.3)]:
    cube('TorchPost', (x, y, 0.65), (0.10, 0.10, 1.2), MAT_WOOD, bevel=0)
    cube('TorchFlame', (x, y, 1.35), (0.24, 0.24, 0.28), MAT_TORCH, bevel=0)

# ---------- characters ----------
def add_face(head_pivot, zombie=False):
    pupil = MAT_DARK if zombie else MAT_BLUE
    for sx in (-0.18, 0.18):
        ew = cube('EyeWhite', (sx, -0.415, 0.09), (0.15, 0.03, 0.12), MAT_WHITE, bevel=0)
        parent(ew, head_pivot)
        ep = cube('EyePupil', (sx, -0.438, 0.09), (0.06, 0.018, 0.06), pupil, bevel=0)
        parent(ep, head_pivot)
    mouth = cube('Mouth', (0, -0.438, -0.16), (0.18, 0.016, 0.05), MAT_DARK, bevel=0)
    parent(mouth, head_pivot)

def character(name, root_loc, zombie=False):
    root = empty(name+'_Root', root_loc)
    skin = MAT_ZSKIN if zombie else MAT_SKIN
    torso_mat = MAT_ZSHIRT if zombie else MAT_SHIRT
    leg_mat = MAT_ZPANTS if zombie else MAT_PANTS

    torso = cube(name+'_Torso', (0,0,1.47), (0.86,0.44,1.12), torso_mat)
    parent(torso, root)

    head_p = empty(name+'_HeadPivot', (0,0,2.28))
    parent(head_p, root)
    head = cube(name+'_Head', (0,0,0), (0.84,0.84,0.84), skin)
    parent(head, head_p)
    add_face(head_p, zombie=zombie)
    if not zombie:
        hair = cube(name+'_Hair', (0,0.02,0.27), (0.85,0.84,0.28), MAT_HAIR, bevel=0.005)
        parent(hair, head_p)

    parts = {'root': root, 'head': head_p}
    for side, sx in [('L', -0.62), ('R', 0.62)]:
        ap = empty(name+f'_{side}ArmPivot', (sx,0,1.93)); parent(ap, root)
        arm = cube(name+f'_{side}Arm', (0,0,-0.47), (0.34,0.40,1.06), skin if zombie else torso_mat)
        parent(arm, ap)
        lp = empty(name+f'_{side}LegPivot', (sx*0.36,0,0.92)); parent(lp, root)
        leg = cube(name+f'_{side}Leg', (0,0,-0.50), (0.37,0.42,1.05), leg_mat)
        parent(leg, lp)
        parts[side+'Arm'] = ap
        parts[side+'Leg'] = lp
    return parts

steve = character('Steve', (0.1, 1.8, 0), zombie=False)
z1 = character('Zombie1', (-0.2, 4.8, 0), zombie=True)
z2 = character('Zombie2', (0.95, 5.7, 0), zombie=True)
z3 = character('Zombie3', (1.85, 6.4, 0), zombie=True)

# sword
blade = cube('SwordBlade', (0.0, -0.08, -1.08), (0.18, 0.08, 1.50), MAT_SWORD)
hilt = cube('SwordHilt', (0.0, -0.08, -0.35), (0.58, 0.12, 0.12), MAT_HILT)
parent(blade, steve['RArm']); parent(hilt, steve['RArm'])

# ---------- animation ----------
# Steve root: crash -> roll -> crouch -> rise slash -> settle
key(steve['root'], 1,   loc=(0.15, 1.85, 1.55), rot=(math.radians(15), 0, math.radians(-10)))
key(steve['root'], 10,  loc=(0.00, 0.55, 1.00), rot=(math.radians(34), math.radians(4), math.radians(-20)))
key(steve['root'], 20,  loc=(-0.25, -0.75, 0.18), rot=(math.radians(70), math.radians(14), math.radians(-55)))
key(steve['root'], 32,  loc=(-0.55, -1.38, 0.03), rot=(math.radians(88), math.radians(4), math.radians(-108)))
key(steve['root'], 45,  loc=(-0.25, -1.55, 0.00), rot=(math.radians(22), 0, math.radians(-165)))
key(steve['root'], 54,  loc=(-0.05, -1.60, -0.12), rot=(math.radians(12), 0, math.radians(-180)))  # duck
key(steve['root'], 66,  loc=(0.05, -1.40, 0.02), rot=(0, 0, math.radians(-150)))
key(steve['root'], 78,  loc=(0.28, -1.05, 0.00), rot=(0, 0, math.radians(-90)))
key(steve['root'], 94,  loc=(0.55, -0.82, 0.00), rot=(0, 0, math.radians(-18)))
key(steve['root'], 120, loc=(0.65, -0.35, 0.00), rot=(0, 0, math.radians(18)))

# Steve limbs
for p in ('LArm','RArm','LLeg','RLeg'):
    key(steve[p], 1, rot=(0,0,0))
key(steve['LArm'], 10, rot=(math.radians(45), 0, math.radians(-18)))
key(steve['RArm'], 10, rot=(math.radians(-55), 0, math.radians(22)))
key(steve['LLeg'], 16, rot=(math.radians(-40), 0, 0))
key(steve['RLeg'], 16, rot=(math.radians(42), 0, 0))
key(steve['LArm'], 38, rot=(math.radians(-38), 0, math.radians(-24)))
key(steve['RArm'], 38, rot=(math.radians(42), 0, math.radians(26)))
key(steve['head'], 45, rot=(math.radians(10), 0, math.radians(18)))
key(steve['RArm'], 48, rot=(math.radians(-55), 0, math.radians(-15)))   # sword drawn
key(steve['LArm'], 48, rot=(math.radians(18), 0, math.radians(12)))
key(steve['head'], 54, rot=(math.radians(16), 0, math.radians(-8)))
key(steve['RArm'], 54, rot=(math.radians(-108), 0, math.radians(-18)))  # duck under lunge
key(steve['RArm'], 68, rot=(math.radians(-132), 0, math.radians(30)))   # anticipation
key(steve['RArm'], 76, rot=(math.radians(8), 0, math.radians(-78)))     # strike
key(steve['LArm'], 76, rot=(math.radians(52), 0, math.radians(-25)))
key(steve['head'], 76, rot=(0, 0, math.radians(10)))
key(steve['RArm'], 94, rot=(math.radians(-40), 0, math.radians(35)))    # recovery
key(steve['LArm'], 94, rot=(math.radians(24), 0, math.radians(-18)))

# zombies movement
# Zombie1: clean lunge then launched away
for p in ('LArm','RArm','LLeg','RLeg'):
    key(z1[p], 1, rot=(0,0,0))
key(z1['root'], 1,  loc=(-0.15, 4.8, 0), rot=(0,0,math.radians(180)))
key(z1['root'], 34, loc=(-0.15, 2.1, 0), rot=(0,0,math.radians(180)))
key(z1['root'], 48, loc=(-0.05, 0.15, 0), rot=(0,0,math.radians(180)))
key(z1['root'], 54, loc=(-0.05, -0.30, 0), rot=(0,0,math.radians(176)))
key(z1['RArm'], 48, rot=(math.radians(-105), 0, math.radians(-10)))
key(z1['RArm'], 56, rot=(math.radians(68), 0, math.radians(8)))         # lunge swing
key(z1['root'], 78, loc=(-0.25, -0.25, 0), rot=(0,0,math.radians(172))) # contact
key(z1['root'], 88, loc=(-1.65, 0.55, 0.58), rot=(math.radians(28), math.radians(14), math.radians(108)))
key(z1['root'], 108, loc=(-3.10, 1.28, 0.14), rot=(math.radians(72), math.radians(28), math.radians(198)))

# run cycles for z2 and z3
for z, delay, xt in [(z2, 6, 0.85), (z3, 12, 1.65)]:
    key(z['root'], 1, loc=tuple(z['root'].location), rot=(0,0,math.radians(180)))
    key(z['root'], 42+delay, loc=(z['root'].location.x, 3.5, 0), rot=(0,0,math.radians(180)))
    key(z['root'], 90+delay, loc=(xt, 0.8, 0), rot=(0,0,math.radians(182)))
    key(z['root'], 120, loc=(xt-0.1, -0.25, 0), rot=(0,0,math.radians(184)))
    for f, s in [(30+delay,1),(40+delay,-1),(50+delay,1),(60+delay,-1),(70+delay,1),(80+delay,-1)]:
        key(z['LArm'], f, rot=(math.radians(45*s), 0, 0))
        key(z['RArm'], f, rot=(math.radians(-45*s), 0, 0))
        key(z['LLeg'], f, rot=(math.radians(-38*s), 0, 0))
        key(z['RLeg'], f, rot=(math.radians(38*s), 0, 0))

# ---------- camera ----------
bpy.ops.object.camera_add(location=(0,-8,3.0))
cam = bpy.context.object
cam.name = 'ActionCamera'
cam.data.lens = 34
cam.data.sensor_width = 32
bpy.context.scene.camera = cam

def cam_pose(frame, loc, target):
    cam.location = Vector(loc)
    d = Vector(target) - cam.location
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    cam.keyframe_insert('location', frame=frame)
    cam.keyframe_insert('rotation_euler', frame=frame)

cam_pose(1,   (0.35, -8.6, 3.6), (0.1, 1.2, 1.7))
cam_pose(14,  (0.10, -7.2, 2.7), (0.0, -0.1, 1.35))
cam_pose(30,  (1.25, -6.0, 1.8), (-0.5, -1.1, 1.05))
cam_pose(46,  (1.10, -5.3, 1.65), (-0.2, -1.35, 1.2))
cam_pose(58,  (-1.35, -4.85, 1.55), (-0.05, -0.65, 1.35))
cam_pose(76,  (1.55, -4.05, 1.70), (0.0, -0.6, 1.35))
cam_pose(92,  (2.35, -3.15, 2.20), (0.10, -0.35, 1.25))
cam_pose(120, (2.25, -4.15, 3.05), (0.70, -0.15, 1.35))

# ---------- lighting/world ----------
world = bpy.context.scene.world
world.use_nodes = True
bg = world.node_tree.nodes.get('Background')
if bg:
    bg.inputs['Color'].default_value = (0.010, 0.015, 0.040, 1)
    bg.inputs['Strength'].default_value = 0.32

bpy.ops.object.light_add(type='AREA', location=(0,-2,7))
keylight = bpy.context.object
keylight.data.energy = 1000
keylight.data.size = 7
keylight.rotation_euler = (math.radians(22), 0, 0)

bpy.ops.object.light_add(type='AREA', location=(-5,-1,3))
fill = bpy.context.object
fill.data.energy = 460
fill.data.color = (0.22, 0.36, 1.0)
fill.data.size = 5
fill.rotation_euler = (math.radians(68), 0, math.radians(-58))

bpy.ops.object.light_add(type='POINT', location=(3.2,1.0,2.8))
rim = bpy.context.object
rim.data.energy = 740
rim.data.color = (1.0, 0.34, 0.12)
rim.data.shadow_soft_size = 1.2

# ---------- render ----------
scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = FRAME_END
scene.render.fps = FPS
scene.render.resolution_x = W
scene.render.resolution_y = H
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'FFMPEG'
scene.render.ffmpeg.format = 'MPEG4'
scene.render.ffmpeg.codec = 'H264'
scene.render.ffmpeg.constant_rate_factor = 'MEDIUM'
scene.render.filepath = str((EXPORT_DIR / 'short-001-v2-silent.mp4').resolve())
try:
    scene.render.engine = 'BLENDER_EEVEE_NEXT'
except Exception:
    scene.render.engine = 'BLENDER_EEVEE'
if hasattr(scene.render, 'use_motion_blur'):
    try:
        scene.render.use_motion_blur = True
    except Exception:
        pass
if hasattr(scene, 'eevee') and hasattr(scene.eevee, 'taa_render_samples'):
    scene.eevee.taa_render_samples = 32
scene.render.film_transparent = False

blend_path = (EXPORT_DIR / 'short-001-v2-scene.blend').resolve()
bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
print('Rendering Short 001 V2 preview...')
bpy.ops.render.render(animation=True)
print(f'Rendered to {scene.render.filepath}')
