"""Textured Liangzhu buildings and kiln smoke for the Windows demo."""
import math
import random
from panda3d.core import CardMaker, ClockObject, Filename, PNMImage, Texture, TransparencyAttrib, loadPrcFileData
from demo_v03 import ExpandedDemo
from world_v03 import Builder, floor_height
from main import ROOT


class WorkshopBuilder(Builder):
    def __init__(self, game):
        super().__init__(game)
        self.models = {}
        self.instances = game.render.attachNewNode('Tripo village buildings')
        self.g.vents = []

    def place(self, kind, x, y, z, size, heading):
        if kind not in self.models:
            path = ROOT / 'assets' / 'tripo' / (kind + '.bam')
            self.models[kind] = self.g.loader.loadModel(Filename.fromOsSpecific(str(path)))
        node = self.instances.attachNewNode(kind)
        node.setPos(x, y, z)
        node.setH(heading)
        node.setScale(size)
        self.models[kind].instanceTo(node)
        return node

    def house(self, x, y, w=5, d=4, base=None, grand=False, parent=None):
        if grand or (x,y) in {(-39,36),(14,49)}:
            return super().house(x,y,w,d,base,grand,parent)
        z = floor_height(x,y) if base is None else base
        tree = (x,y) in {(-39,0),(-20,4),(32,47)} or abs(x)>50
        self.place('tree' if tree else 'wood', x,y,z,w+.8, 0 if x < -25 else -90)
        self.obstruction(x,y,w+.3,d+.5,z+w)

    def canopy(self,x,y,w=6,d=4,z=None,parent=None):
        if y >= 0 and abs(x)<50:
            return super().canopy(x,y,w,d,z,parent)
        base = floor_height(x,y) if z is None else z
        self.place('stall',x,y,base,w,180 if y>-10 else 0)
        self.obstruction(x,y,w*.78,w*.60,base+w*.83)

    def kiln(self,x,y,parent=None):
        z = floor_height(x,y)
        oven = self.place('oven',x,y,z,3.9,-48)
        vent = oven.attachNewNode('chimney')
        vent.setPos(-.125,.14,.92)
        self.g.vents.append(vent.getPos(self.g.render))
        self.obstruction(x,y,3.6,3.6,z+3.6)
        for i in range(4):
            self.pot(x+2.15,y-.9+i*.65,z,.43,parent)


def make_smoke_texture():
    image = PNMImage(96,96,4)
    for y in range(96):
        for x in range(96):
            u,v = (x-47.5)/46,(y-47.5)/46
            angle = math.atan2(v,u)
            radius = math.hypot(u,v) / (.84+.068*math.sin(5*angle)+.042*math.cos(3*angle))
            density = max(0,1-radius*radius)
            shade = .43+.15*v+.08*density
            image.setXelA(x,y,shade,shade,shade*1.02,density**1.25)
    texture = Texture('rolling ash')
    texture.load(image)
    return texture


class WorkshopDemo(ExpandedDemo):
    world_builder = WorkshopBuilder

    def world(self):
        super().world()
        self.clouds = []
        self.emission = 0.
        self.smoke_random = random.Random(504)
        card = CardMaker('kiln exhaust')
        card.setFrame(-1,1,-1,1)
        texture = make_smoke_texture()
        for _ in range(52):
            node = self.effects.attachNewNode(card.generate())
            node.setTexture(texture)
            node.setTransparency(TransparencyAttrib.MAlpha)
            node.setDepthWrite(False)
            node.setBillboardPointEye()
            node.setLightOff()
            node.setShaderOff()
            node.setTwoSided(True)
            node.hide()
            self.clouds.append([node, None, 0., 0.])

    def update(self,task):
        result = super().update(task)
        dt = min(ClockObject.getGlobalClock().getDt(),.045)
        if self.dialog:
            return result
        firing = self.kiln_remaining>0 and self.phase() not in ('rain','flood') and not self.preview
        self.emission = self.emission+dt if firing else 0
        if self.emission >= .17:
            self.emission -= .17
            for vent,cloud in zip(self.vents,(c for c in self.clouds if c[1] is None)):
                cloud[1:] = [vent,0.,self.smoke_random.uniform(0,math.tau)]
                cloud[0].show()
        for cloud in self.clouds:
            node, vent, age, seed = cloud
            if vent is None:
                continue
            age += dt
            if age >= 4:
                node.hide()
                cloud[1] = None
                continue
            cloud[2] = age
            curl = .095+.12*age
            node.setPos(vent.x+.13*age**2+curl*math.sin(seed+age*1.7),
                        vent.y+curl*math.cos(seed+age*1.4),vent.z+1.25*age)
            radius = .21+age*(.29+.04*math.sin(seed))
            node.setScale(radius)
            node.setColorScale(1,1,1,min(1,age*8)*(1-age/4)**.72*.85)
        return result


if __name__=='__main__':
    loadPrcFileData('', 'window-title Sandlight 0.4 | Liangzhu Workshops')
    WorkshopDemo().run()
