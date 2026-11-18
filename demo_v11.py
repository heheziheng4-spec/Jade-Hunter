"""The November frontier assets, integrated with the existing village routes."""
import math
from panda3d.core import Filename, Texture, PNMImage, loadPrcFileData
from demo_v10 import SkyDemo
from sky_temple import SolarBuilder, image_card
from main import ROOT


class FrontierBuilder(SolarBuilder):
    def asset(self, kind, x, y, z, scale, heading=0):
        key='frontier_'+kind
        if key not in self.models:
            self.models[key]=self.g.loader.loadModel(Filename.fromOsSpecific(str(ROOT/'assets'/'frontier'/(kind+'.bam'))))
            for tex in self.models[key].findAllTextures():
                tex.setFormat(Texture.FRgb8 if tex.getNumComponents()==3 else Texture.FRgba8)
        node=self.instances.attachNewNode(key)
        node.setPos(x,y,z)
        node.setH(heading)
        node.setScale(*scale)
        self.models[key].instanceTo(node)
        return node

    def bridge_span(self,x,ground):
        # Normalized deck occupies the central half of the supplied scanned asset.
        self.asset('span',x,18,.9-.099*6,(17,15.6,6))
        # A concealed timber bed closes the small holes in the scanned boards.
        self.box('bridge structural bed',(x,18,.74),(6.3,12,.24),(.31,.21,.13),ground)
        for side in (-1,1):
            self.obstruction(x+side*3.45,18,.25,12,3.0)


class FrontierDemo(SkyDemo):
    world_builder=FrontierBuilder

    def world(self):
        super().world()
        self.frontier_fires=[]
        glow=PNMImage(64,64,4)
        for row in range(64):
            for col in range(64):
                radius=((col-31.5)**2+(row-31.5)**2)/992
                glow.setXelA(col,row,1,1,1,max(0,1-radius)**3)
        glow_texture=Texture('soft fire glow')
        glow_texture.load(glow)
        # South wall sentries, then the two outer ring approaches.
        for x,y in [(-5.2,-25),(5.2,-25),(-30,-24.7),(30,-24.7),(-82,30),(82,30)]:
            z=self.height(x,y)
            self.builder.asset('beacon',x,y,z-.035,(2.3,2.3,2.3),x*3)
            self.builder.obstruction(x,y,1.9,1.9,z+1.15)
            halo=image_card(self,self.effects,'disc',2.2,2.2,True)
            halo.setTexture(glow_texture)
            halo.setPos(x,y,z+.8)
            halo.setBillboardPointEye()
            halo.setColorScale(1,.33,.055,.42)
            pool=image_card(self,self.effects,'disc',5,5,True)
            pool.setTexture(glow_texture)
            pool.setP(-90)
            pool.setTexture(glow_texture)
            pool.setPos(x,y,z+.025)
            pool.setColorScale(1,.35,.06,.32)
            sparks=[]
            for i in range(9):
                n=self.unit.copyTo(self.effects)
                n.setLightOff()
                n.setShaderOff()
                n.setColor(1,.66,.17,1)
                sparks.append(n)
            self.frontier_fires.append((x,y,z,halo,pool,sparks))

    def update(self,task):
        result=super().update(task)
        for x,y,z,halo,pool,sparks in self.frontier_fires:
            flicker=.86+.09*math.sin(self.t*9+x)+.05*math.sin(self.t*17+y)
            halo.setScale(flicker)
            pool.setAlphaScale(flicker)
            for i,n in enumerate(sparks):
                t=(self.t*.34+i/9)%1
                n.setPos(x+.25*math.sin(i*2.4+t*3)+t*.4,y+.2*math.cos(i*2.4+t),z+.55+t*2)
                n.setScale(.027*(1-t),.027*(1-t),.065*(1-t))
        return result


if __name__=='__main__':
    loadPrcFileData('', 'window-title Sandlight 0.11a | Restored Stone Pillars')
    FrontierDemo().run()
