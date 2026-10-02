#!/usr/bin/env python3
"""Build and render the first Vellous Minecraft motion preview in Blender."""

import math
from pathlib import Path
import bpy
from mathutils import Vector

FPS = 24
END = 240
OUT = Path("projects/short-001-zombie-fight/exports")
OUT.mkdir(parents=True, exist_ok=True)

def clean():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

def material(name, rgb, emission=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*rgb, 1)
        bsdf.inputs["Roughness"].default_value = 0.75
        if emission and "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = (*rgb, 1)
            bsdf.inputs["Emission Strength"].default_value = emission
    return m

def cube(name, loc, dims, mat, bevel=0.015):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o = bpy.context.object
    o.name = name
    o.dimensions = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if mat:
        o.data.materials.append(mat)
    if bevel:
        mod = o.modifiers.new("TinyBevel", "BEVEL")
        mod.width = bevel
        mod.segments = 1
    return o

def empty(name, loc=(0,0,0)):
    o = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(o)
    o.location = loc
    return o

def add_child(parent, child):
    child.parent = parent

def kf(o, frame, loc=None, rot=None):
    if loc is not None:
        o.location = loc
        o.keyframe_insert("location", frame=frame)
    if rot is not None:
        o.rotation_euler = rot
        o.keyframe_insert("rotation_euler", frame=frame)

def cam_key(cam, frame, loc, target):
    cam.location = Vector(loc)
    cam.rotation_euler = (Vector(target)-cam.location).to_track_quat("-Z","Y").to_euler()
    cam.keyframe_insert("location", frame=frame)
    cam.keyframe_insert("rotation_euler", frame=frame)

def character(name, zombie=False):
    root = empty(name+"_Root")
    skin = ZSKIN if zombie else SKIN
    shirt = ZSHIRT if zombie else SHIRT
    pants = ZPANTS if zombie else PANTS

    torso = cube(name+"_Torso", (0,0,1.45), (0.86,0.44,1.12), shirt)
    add_child(root, torso)

    head = empty(name+"_HeadPivot", (0,0,2.30))
    add_child(root, head)
    h = cube(name+"_Head", (0,0,0), (0.82,0.82,0.82), skin)
    add_child(head, h)

    # Face details on the -Y side.
    eye_mat = DARK if zombie else BLUE
    for x in (-0.18,0.18):
        e = cube(name+"_Eye"+str(x), (x,-0.42,0.10), (0.13,0.03,0.11), eye_mat, 0)
        add_child(head, e)
    mouth = cube(name+"_Mouth", (0,-0.425,-0.17), (0.22,0.025,0.06), DARK, 0)
    add_child(head, mouth)

    if not zombie:
        hair = cube(name+"_Hair", (0,0.02,0.25), (0.84,0.84,0.30), HAIR)
        add_child(head, hair)

    parts = {"root":root, "head":head}
    for side, x in (("L",-0.62),("R",0.62)):
        ap = empty(name+"_"+side+"Arm", (x,0,1.92))
        add_child(root, ap)
        a = cube(name+"_"+side+"ArmMesh", (0,0,-0.48), (0.34,0.40,1.08), shirt if not zombie else skin)
        add_child(ap, a)
        parts[side+"Arm"] = ap

        lp = empty(name+"_"+side+"Leg", (x*0.36,0,0.92))
        add_child(root, lp)
        l = cube(name+"_"+side+"LegMesh", (0,0,-0.49), (0.37,0.42,1.02), pants)
        add_child(lp, l)
        parts[side+"Leg"] = lp
    return parts

clean()

# Materials
GRASS = material("Grass",(0.10,0.38,0.07))
PATH = material("Path",(0.34,0.30,0.22))
WOOD = material("Wood",(0.35,0.16,0.055))
WOOD2 = material("Wood2",(0.52,0.27,0.08))
ROOF = material("Roof",(0.20,0.07,0.035))
SKIN = material("SteveSkin",(0.61,0.36,0.20))
SHIRT = material("SteveShirt",(0.02,0.53,0.62))
PANTS = material("StevePants",(0.08,0.15,0.44))
HAIR = material("SteveHair",(0.15,0.055,0.02))
ZSKIN = material("ZombieSkin",(0.10,0.43,0.13))
ZSHIRT = material("ZombieShirt",(0.02,0.37,0.38))
ZPANTS = material("ZombiePants",(0.16,0.09,0.35))
DARK = material("Dark",(0.01,0.01,0.01))
BLUE = material("EyeBlue",(0.02,0.20,0.60))
BLADE = material("Blade",(0.55,0.78,0.85))
HILT = material("Hilt",(0.08,0.08,0.09))
FIRE = material("Fire",(1.0,0.20,0.015),3.0)

# Environment
cube("Ground",(0,2,-0.55),(18,20,1),GRASS,0)
cube("VillagePath",(0,-0.2,-0.02),(4.1,14,0.12),PATH,0)

def house(prefix,x,y,w=3.4,d=3.0):
    cube(prefix+"_Body",(x,y,1.25),(w,d,2.5),WOOD2,0)
    cube(prefix+"_Roof",(x,y,2.80),(w+0.45,d+0.45,0.42),ROOF,0)
    cube(prefix+"_Door",(x,y-d/2-0.03,0.85),(0.72,0.10,1.70),WOOD,0)

house("HouseL",-4.5,1.7)
house("HouseR",4.5,1.4,3.7,3.1)
house("HouseBack",-4.0,7.0,3.2,2.9)

# Destructible wooden wall.
debris=[]
for ix in range(-2,3):
    for iz in range(4):
        o = cube("Wall_%s_%s"%(ix,iz),(ix*0.72,2.35,0.34+iz*0.70),(0.68,0.52,0.66),WOOD)
        if abs(ix)<=1 and iz<=2:
            debris.append((o,ix,iz))

for o,ix,iz in debris:
    s=Vector(o.location)
    kf(o,1,loc=s,rot=(0,0,0))
    kf(o,16,loc=(s.x+ix*0.25,s.y-2.0,s.z+1.0+(2-iz)*0.20),
       rot=(0.7+iz*0.15,ix*0.50,ix*0.65))
    kf(o,48,loc=(s.x+ix*0.55,s.y-3.1,max(0.12,s.z-0.35)),
       rot=(1.8,ix*1.0,ix*1.8))

# Small glowing torch markers.
for x,y in [(-2.4,4.0),(2.4,4.0),(-3.0,-0.4),(3.0,-0.4)]:
    cube("TorchPost",(x,y,0.58),(0.09,0.09,1.05),WOOD)
    cube("TorchFlame",(x,y,1.22),(0.20,0.20,0.30),FIRE)

# Characters
steve=character("Steve",False)
z1=character("Zombie1",True)
z2=character("Zombie2",True)
z3=character("Zombie3",True)

# Sword on right arm
blade=cube("SwordBlade",(0,-0.05,-1.13),(0.16,0.10,1.48),BLADE)
hilt=cube("SwordHilt",(0,-0.05,-0.37),(0.58,0.12,0.12),HILT)
add_child(steve["RArm"],blade)
add_child(steve["RArm"],hilt)
blade.hide_render=True; hilt.hide_render=True
blade.keyframe_insert("hide_render",frame=1); hilt.keyframe_insert("hide_render",frame=1)
blade.hide_render=False; hilt.hide_render=False
blade.keyframe_insert("hide_render",frame=98); hilt.keyframe_insert("hide_render",frame=98)

# Steve: crash -> roll -> dodge -> counter combo.
for f,loc,rot in [
    (1,(0,1.55,1.42),(math.radians(15),0,math.radians(-8))),
    (16,(-0.08,0.30,1.02),(math.radians(35),math.radians(8),math.radians(-20))),
    (32,(-0.28,-0.82,0.20),(math.radians(70),math.radians(18),math.radians(-58))),
    (46,(-0.72,-1.42,0.04),(math.radians(95),0,math.radians(-112))),
    (64,(-0.52,-1.63,0),(math.radians(35),0,math.radians(-160))),
    (84,(-0.15,-1.60,0),(0,0,math.radians(-180))),
    (100,(0,-1.50,0),(0,0,math.radians(-180))),
    (116,(-0.45,-1.46,-0.14),(math.radians(16),0,math.radians(-195))),
    (134,(-0.15,-1.32,0),(0,0,math.radians(-158))),
    (150,(0.05,-1.08,0),(0,0,math.radians(-112))),
    (168,(0.35,-0.90,0.05),(math.radians(-5),0,math.radians(-32))),
    (184,(0.58,-0.78,0),(0,0,math.radians(28))),
    (210,(0.62,-0.43,0),(0,0,math.radians(68))),
    (240,(0.72,-0.18,0),(0,0,math.radians(105)))
]:
    kf(steve["root"],f,loc,rot)

for p in ("LArm","RArm","LLeg","RLeg"):
    kf(steve[p],1,rot=(0,0,0))
kf(steve["LArm"],15,rot=(math.radians(55),0,math.radians(-20)))
kf(steve["RArm"],15,rot=(math.radians(-65),0,math.radians(25)))
kf(steve["LLeg"],22,rot=(math.radians(-42),0,0))
kf(steve["RLeg"],22,rot=(math.radians(45),0,0))
kf(steve["RArm"],100,rot=(math.radians(-70),0,math.radians(-20)))
kf(steve["LArm"],100,rot=(math.radians(18),0,math.radians(14)))
kf(steve["head"],116,rot=(math.radians(18),0,math.radians(-10)))
kf(steve["RArm"],116,rot=(math.radians(-112),0,math.radians(-25)))
kf(steve["RArm"],145,rot=(math.radians(-120),0,math.radians(58)))
kf(steve["RArm"],155,rot=(math.radians(42),0,math.radians(-72)))
kf(steve["RArm"],166,rot=(math.radians(78),0,math.radians(-42)))
kf(steve["RArm"],177,rot=(math.radians(-98),0,math.radians(72)))
kf(steve["LArm"],177,rot=(math.radians(52),0,math.radians(-32)))
kf(steve["RArm"],240,rot=(math.radians(-82),0,math.radians(24)))

def zombie_run(ch,start,x0,targetx):
    kf(ch["root"],1,loc=(x0,5.7+start*0.02,0),rot=(0,0,math.radians(180)))
    kf(ch["root"],48+start,loc=(x0,4.1,0),rot=(0,0,math.radians(180)))
    kf(ch["root"],92+start,loc=(targetx,0.35,0),rot=(0,0,math.radians(180)))
    for j,f in enumerate(range(50+start,102+start,10)):
        s=1 if j%2==0 else -1
        kf(ch["LArm"],f,rot=(math.radians(48*s),0,0))
        kf(ch["RArm"],f,rot=(math.radians(-48*s),0,0))
        kf(ch["LLeg"],f,rot=(math.radians(-40*s),0,0))
        kf(ch["RLeg"],f,rot=(math.radians(40*s),0,0))

zombie_run(z1,0,-0.70,-0.45)
zombie_run(z2,8,0.55,0.50)
zombie_run(z3,14,1.45,1.35)

# Zombie 1 attack then gets launched.
kf(z1["root"],112,loc=(-0.45,-0.30,0),rot=(0,0,math.radians(180)))
kf(z1["RArm"],112,rot=(math.radians(-135),0,math.radians(-10)))
kf(z1["RArm"],126,rot=(math.radians(70),0,math.radians(8)))
kf(z1["root"],150,loc=(-0.20,-0.48,0),rot=(0,0,math.radians(170)))
kf(z1["root"],168,loc=(-1.75,0.22,0.72),rot=(math.radians(32),math.radians(20),math.radians(118)))
kf(z1["root"],194,loc=(-3.35,1.15,0.18),rot=(math.radians(78),math.radians(35),math.radians(220)))

kf(z2["root"],190,loc=(0.65,-0.05,0),rot=(0,0,math.radians(180)))
kf(z2["root"],240,loc=(0.45,-0.95,0),rot=(0,0,math.radians(180)))
kf(z3["root"],198,loc=(1.60,0.18,0),rot=(0,0,math.radians(185)))
kf(z3["root"],240,loc=(1.20,-0.65,0),rot=(0,0,math.radians(185)))

# Camera choreography.
bpy.ops.object.camera_add()
cam=bpy.context.object
cam.name="ActionCamera"
cam.data.lens=36
bpy.context.scene.camera=cam
for f,loc,target in [
    (1,(0.3,-8.8,3.5),(0,1.2,1.8)),
    (20,(-0.2,-7.4,2.8),(-0.1,0.1,1.7)),
    (48,(1.4,-6.0,1.6),(-0.6,-1.3,1.1)),
    (84,(1.0,-5.1,2.0),(-0.1,-1.3,1.5)),
    (116,(-1.8,-4.6,1.35),(-0.1,-0.8,1.4)),
    (150,(1.7,-4.1,1.65),(0.0,-0.6,1.45)),
    (177,(2.7,-3.2,2.2),(0.2,-0.45,1.35)),
    (205,(2.0,-4.4,3.3),(0.5,-0.25,1.45)),
    (240,(-2.5,-4.0,2.7),(0.7,-0.15,1.55))
]:
    cam_key(cam,f,loc,target)

# Lighting/world.
scene=bpy.context.scene
scene.world.use_nodes=True
bg=scene.world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value=(0.008,0.015,0.05,1)
bg.inputs["Strength"].default_value=0.30

bpy.ops.object.light_add(type="AREA",location=(0,-2,7))
keylight=bpy.context.object
keylight.data.energy=850
keylight.data.shape="DISK"
keylight.data.size=7

bpy.ops.object.light_add(type="AREA",location=(-5,-1,3))
fill=bpy.context.object
fill.data.energy=420
fill.data.color=(0.18,0.30,1.0)
fill.data.size=5

bpy.ops.object.light_add(type="POINT",location=(3,1,2.8))
rim=bpy.context.object
rim.data.energy=650
rim.data.color=(1.0,0.22,0.05)
rim.data.shadow_soft_size=1.0

# Render settings: fast motion-validation preview.
scene.frame_start=1
scene.frame_end=END
scene.render.fps=FPS
scene.render.resolution_x=360
scene.render.resolution_y=640
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="FFMPEG"
scene.render.ffmpeg.format="MPEG4"
scene.render.ffmpeg.codec="H264"
scene.render.ffmpeg.constant_rate_factor="MEDIUM"
scene.render.filepath=str(OUT/"animation-silent.mp4")
try:\n    scene.render.engine = "BLENDER_EEVEE_NEXT"\nexcept (TypeError, ValueError):\n    scene.render.engine = "BLENDER_EEVEE"

if hasattr(scene.render,"use_motion_blur"):
    try:
        scene.render.use_motion_blur=True
    except Exception:
        pass

bpy.ops.wm.save_as_mainfile(filepath=str((OUT/"generated-preview-scene.blend").resolve()))
print("Rendering Vellous Short 001...")
bpy.ops.render.render(animation=True)
print("Render complete:", scene.render.filepath)
