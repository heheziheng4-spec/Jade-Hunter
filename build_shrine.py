"""Blender-built editable shrine, aligned to the runtime's walkable steps."""
import bpy, math, random
from pathlib import Path
ROOT=Path(__file__).parent
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
rng=random.Random(73)
def mat(name,c):
 m=bpy.data.materials.new(name);m.diffuse_color=(*c,1);m.use_nodes=True
 p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Roughness'].default_value=.92
 return m
sand=mat('Warm eroded sandstone',(.64,.47,.29));edge=mat('Fresh stone edges',(.75,.58,.37));dark=mat('Old strata',(.48,.34,.22))
def block(name,pos,size,material,bevel=.10):
 bpy.ops.mesh.primitive_cube_add(size=1,location=pos);o=bpy.context.object;o.name=name;o.dimensions=size
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(material)
 b=o.modifiers.new('Soft wind erosion','BEVEL');b.width=min(bevel,min(size)*.22);b.segments=2
 bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=b.name)
 return o
for i in range(12):block('Stair_%02d'%i,(0,22+i+.5,(i+1)*.1),(12,1,(i+1)*.2),edge,.08)
block('Half buried platform',(0,39,1.2),(20,10,2.4),sand,.30)
for side in (-1,1):
 for j,h in enumerate([6.8,5.1,6.1,3.8]):
  x=side*7;y=32+j*3
  block('Pedestal',(x,y,2.65),(2.1,2.1,.5),dark,.14)
  # Individually irregular corners, tapered shaft, eroded bevels.
  verts=[]
  for z,k in [(2.9,1),(2.9+h,.72)]:
   for xx,yy in [(-1,-1),(1,-1),(1,1),(-1,1)]:verts.append((x+xx*.76*k+rng.uniform(-.11,.11),y+yy*.67*k+rng.uniform(-.09,.09),z+rng.uniform(-.07,.07)))
  me=bpy.data.meshes.new('pillar_mesh');me.from_pydata(verts,[],[(0,3,2,1),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)]);me.update()
  o=bpy.data.objects.new('Eroded pillar',me);bpy.context.collection.objects.link(o);o.data.materials.append(sand)
  b=o.modifiers.new('Worn edges','BEVEL');b.width=.16;b.segments=3
  block('Broken capital',(x,y,h+3),(2.1,1.8,.6),edge,.15)
 # Two longitudinal lintels with deliberate gaps.
 for y,z,l in [(34.1,9.4,4.4),(40.1,8.8,3.0)]:
  o=block('Fractured entablature',(side*7,y,z),(2.4,l,.8),sand,.18);o.rotation_euler[1]=side*.04
 # Tilted fragments and half-buried rubble.
 for j in range(5):
  o=block('Buried stone fragment',(side*rng.uniform(9,12),rng.uniform(28,44),rng.uniform(0,.35)),(rng.uniform(.8,2),rng.uniform(1,2.4),rng.uniform(.5,1.2)),sand,.14)
  o.rotation_euler=(rng.uniform(-.15,.15),rng.uniform(-.2,.2),rng.uniform(-1,1))
block('Offering pedestal',(0,39,3),(3,1.8,1.2),dark,.18)
block('Offering slab',(0,39,3.68),(3.6,2.1,.25),edge,.10)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'assets'/'sandstone_shrine.blend'))
bpy.ops.export_scene.gltf(filepath=str(ROOT/'assets'/'sandstone_shrine.glb'),export_format='GLB')
print('SHRINE_EXPORTED')
