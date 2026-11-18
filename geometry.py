"""Simple editable mesh vocabulary, centimetre-free world units in metres."""
import math, random
from panda3d.core import Geom,GeomNode,GeomTriangles,GeomVertexData,GeomVertexFormat,GeomVertexWriter,NodePath

def mesh(name, vertices, faces):
    data=GeomVertexData(name,GeomVertexFormat.getV3n3(),Geom.UHStatic)
    v=GeomVertexWriter(data,'vertex');n=GeomVertexWriter(data,'normal')
    tris=GeomTriangles(Geom.UHStatic); idx=0
    from panda3d.core import Vec3
    for face in faces:
        a,b,c=(Vec3(*vertices[i]) for i in face[:3]); normal=(b-a).cross(c-a)
        normal.normalize()
        for i in face:v.addData3(*vertices[i]);n.addData3(normal)
        for j in range(1,len(face)-1):tris.addVertices(idx,idx+j,idx+j+1)
        idx+=len(face)
    geom=Geom(data);geom.addPrimitive(tris);node=GeomNode(name);node.addGeom(geom)
    return NodePath(node)

def cube():
    v=[(-.5,-.5,-.5),(.5,-.5,-.5),(.5,.5,-.5),(-.5,.5,-.5),(-.5,-.5,.5),(.5,-.5,.5),(.5,.5,.5),(-.5,.5,.5)]
    return mesh('block',v,[(0,3,2,1),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)])

def cone(sides=8, top=.65):
    v=[(math.cos(i*math.tau/sides)*.5,math.sin(i*math.tau/sides)*.5,z) for z in (0,1) for i in range(sides)]
    v=[(x*(top if z else 1),y*(top if z else 1),z) for x,y,z in v]
    f=[tuple(reversed(range(sides))),tuple(range(sides,sides*2))]
    f += [(i,(i+1)%sides,(i+1)%sides+sides,i+sides) for i in range(sides)]
    return mesh('tapered_stone',v,f)

def terrain():
    rng=random.Random(26);v=[];w=25
    for iy in range(w):
        for ix in range(w):
            x=(ix-12)*8;y=(iy-8)*8
            z=-.17 if abs(x)<37 and -24<y<53 else -.17+max(0,abs(x)-30)*.14+rng.uniform(-.7,.9)
            v.append((x,y,z))
    f=[]
    for y in range(w-1):
        for x in range(w-1):
            k=y*w+x;f.extend([(k,k+1,k+w+1),(k,k+w+1,k+w)])
    return mesh('dunes',v,f)
