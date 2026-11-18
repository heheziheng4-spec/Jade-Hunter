import math
from panda3d.core import CardMaker, ColorBlendAttrib, Filename, GeomVertexReader, PNMImage, Texture, TransparencyAttrib, loadPrcFileData
from main import ROOT
from demo_v06 import RiverBuilder, RiverPassDemo, POINTS
from world_v03 import floor_height


class IslandBuilder(RiverBuilder):
    def place(self,kind,x,y,z,size,heading):
        node=super().place(kind,x,y,z,size,heading)
        if kind in ('ship','bridge'):
            return node
        # Isolated grass and stones can extend below the structural foot of a scanned asset.
        if not hasattr(self,'foot_levels'):
            self.foot_levels={}
        if kind not in self.foot_levels:
            heights=[]
            for geom in self.models[kind].findAllMatches('**/+GeomNode'):
                for i in range(geom.node().getNumGeoms()):
                    reader=GeomVertexReader(geom.node().getGeom(i).getVertexData(),'vertex')
                    while not reader.isAtEnd():
                        heights.append(reader.getData3().z)
            heights.sort()
            self.foot_levels[kind]=min(.065,heights[len(heights)//40]) if heights else 0
        node.setZ(z-size*self.foot_levels[kind]-.025)
        return node

    def canopy(self,x,y,*args,**kwargs):
        if (x,y)==(9,39):
            self.building('stall',x,y,5.1,180,4,3.5)
        elif (x,y)==(-33,48):
            self.building('shelf',x,y,3.15,0,2.7,2.5)
        else:
            super().canopy(x,y,*args,**kwargs)

    def building(self,kind,x,y,size,heading,width,depth):
        if kind=='stele':
            node=self.place(kind,-78,0,.1,18,0)
            self.obstruction(-78,0,13.4,14,14)
            return node
        return super().building(kind,x,y,size,heading,width,depth)

    def pillar(self,x,y,*args,**kwargs):
        if abs(x+76)<9 and abs(y)<9:
            return
        return super().pillar(x,y,*args,**kwargs)

    def taper(self,name,p,*args,**kwargs):
        if name=='island altar' and p[0]==-76:
            return
        return super().taper(name,p,*args,**kwargs)


class IslandDemo(RiverPassDemo):
    world_builder=IslandBuilder
    points=dict(POINTS,gateway=(POINTS['gateway'][0],'神树之门','前往西南星纹祭岛'),
                return_gate=((-69,0,.1),'西南星纹浮碑','返回神树'))

    def add_target(self,key,pos,label,verb):
        if key=='island0':pos=(-76,-9.5,.1)
        if key=='pottery_trade':label,verb='茅草市场','2 陶器换 4 粮食 · F 用 3 粮食换 1 材料'
        super().add_target(key,pos,label,verb)

    def world(self):
        super().world()
        self.accept('f',self.barter)
        self.sounds={name:self.loader.loadSfx(Filename.fromOsSpecific(str(ROOT/'assets'/'sounds'/(name+'.wav')))) for name in ('portal','trade','work','freight','hint')}
        img=PNMImage(64,64,4)
        for y in range(64):
            for x in range(64):
                r=((x-31.5)/32)**2+((y-31.5)/32)**2
                img.setXelA(x,y,.47,1,.87,max(0,1-r)**3)
        tex=Texture('jade mist');tex.load(img)
        card=CardMaker('luminous dust');card.setFrame(-1,1,-1,1)
        self.mist=[]
        for key in ('gateway','return_gate'):
            self.rings[key].hide()
            for i in range(25):
                n=self.effects.attachNewNode(card.generate())
                n.setTexture(tex);n.setBillboardPointEye();n.setLightOff();n.setShaderOff()
                n.setDepthWrite(False);n.setTransparency(TransparencyAttrib.MAlpha)
                n.setAttrib(ColorBlendAttrib.make(ColorBlendAttrib.MAdd,ColorBlendAttrib.OIncomingAlpha,ColorBlendAttrib.OOne))
                self.mist.append((key,i,n))

    def cue(self,name,label):
        self.sounds[name].play()
        self.toast+='  【音效】'+label
        self.toasting=5

    def barter(self):
        if self.near!='pottery_trade' or self.preview or self.dialog:return
        if self.state.food<3:
            self.toast='需要 3 粮食。';self.cue('hint','轻提示');return
        self.state.food-=3;self.state.material+=1
        self.toast='付出 3 粮食，换得 1 材料。'
        self.cue('trade','货物交接');self.sync_ui();self.save(True)

    def interact(self):
        key=self.near
        active=key and not self.dialog and not self.preview
        super().interact()
        if not active:return
        if key in ('gateway','return_gate'):
            self.yaw=90
            self.cue('portal','玉鸣回响')
        elif key in ('pottery_trade','wares','jadeshop'):
            self.cue('hint','轻提示') if '需要' in self.toast or '先到' in self.toast else self.cue('trade','货物交接')
        elif key in ('shipping','delivery'):self.cue('freight','码头应声')
        else:self.cue('work','聚落回应')

    def update(self,task):
        result=super().update(task)
        for key,i,n in self.mist:
            x,y,z=self.points[key][0]
            island=key=='return_gate'
            t=self.t
            pulse=self.flash[key]
            a=i*2.4+t*(.38+.03*(i%4))
            if i<4:
                n.setPos(x+.21*math.cos(a),y+.26*math.sin(a),z+1.6+.35*math.sin(a))
                n.setScale(1.3+pulse,1,2+.45*math.sin(a)+pulse)
                alpha=.14+.12*pulse
            else:
                u=(i*.137+t*.21)%1
                n.setPos(x+math.cos(a)*(.8+.45*u),y+math.sin(a)*(.8+.45*u),z+u*3.8)
                n.setScale(.045+.075*u+pulse*.09)
                alpha=.8*math.sin(math.pi*u)
            n.setAlphaScale(alpha)
        return result


if __name__=='__main__':
    loadPrcFileData('', 'window-title Sandlight 0.7 | Star Isle')
    IslandDemo().run()

