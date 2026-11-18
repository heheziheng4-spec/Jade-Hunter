"""The solar court, its processional stones and the suspended citadel."""
import math
import random
from panda3d.core import CardMaker, ColorBlendAttrib, DirectionalLight, Filename, TransparencyAttrib, Texture
from geometry import cone, mesh
from main import ROOT
from demo_v09 import QuarryBuilder

ASSETS = ROOT / 'assets' / 'skyrite'
TAU = math.tau
CITY = (22, 155, 35)
JASPER = (.19, .40, .37)
LIME = (.65, .58, .46)
BRONZE = (.60, .36, .14)

def image_card(game, parent, name, w, h, additive=False):
    card = CardMaker(name)
    card.setFrame(-w / 2, w / 2, -h / 2, h / 2)
    node = parent.attachNewNode(card.generate())
    node.setTexture(game.loader.loadTexture(Filename.fromOsSpecific(str(ASSETS / (name + '.png')))))
    node.setTwoSided(True)
    node.setLightOff()
    node.setShaderOff()
    node.setTransparency(TransparencyAttrib.MAlpha)
    node.setDepthWrite(False)
    if additive:
        node.setAttrib(ColorBlendAttrib.make(ColorBlendAttrib.MAdd, ColorBlendAttrib.OIncomingAlpha, ColorBlendAttrib.OOne))
    return node

def drum(parent, pos, radius, height, color, top=1, sides=64):
    node = cone(sides, top)
    node.reparentTo(parent)
    node.setPos(*pos)
    node.setScale(radius*2, radius*2, height)
    node.setColor(*color, 1)
    return node

class SolarBuilder(QuarryBuilder):
    def pillar(self,x,y,*args,**kwargs):
        if abs(x)==8 and y in (79,90):
            return
        return super().pillar(x,y,*args,**kwargs)

    def court_gate(self,sacred):
        gate = self.gate.copyTo(sacred)
        gate.setPos(0, 90, 6.5)
        for x in (-4.05,4.05):
            self.obstruction(x,90,2.9,2.7,18.4)

    def court_column(self,sacred,x,y,h,j,side):
        g=self.g
        self.box('dressed plinth',(x,y,6.31),(2.15,2.1,.62),JASPER,sacred)
        for layer in range(4):
            section=h/4
            self.box('jointed standing stone',(x,y,6.6+(layer+.5)*section),(1.46,1.64,section-.017),(.51+.013*layer,.465+.01*layer,.39),sacred)
        for dx in (-.50,.50):
            self.box('jade inlaid flute',(x+dx,y-.823,6.82+h*.47),(.046,.035,h*.86),JASPER,sacred)
        for n in range(3):
            self.box('bronze heel moulding',(x,y,6.62+n*.105),(1.72-.07*n,1.91-.08*n,.09),BRONZE,sacred)
        self.obstruction(x,y,2.15,2.1,6.6+h)
        self.box('gilt collar',(x,y,6.45+h),(1.6,1.78,.16),BRONZE,sacred)
        rune=image_card(g,sacred,f'mark{36+(j+(side>0)*2)%6:02}',1.28,1.6)
        rune.setPos(x,y-.83,5.6+h)

    def offering_altar(self, sacred):
        g = self.g
        g.suspended = []
        g.builder = self
        self.gate = g.loader.loadModel(Filename.fromOsSpecific(str(ASSETS / 'gate.bam')))
        # The legacy renderer writes directly to a display-space framebuffer.
        for texture in self.gate.findAllTextures():
            texture.setFormat(Texture.FRgb8 if texture.getNumComponents()==3 else Texture.FRgba8)
        bounce=DirectionalLight('sky reflected from limestone')
        bounce.setColor((.56,.62,.60,1))
        source=g.render.attachNewNode(bounce);source.setHpr(-24,-27,0)
        self.gate.setLight(source)
        self.court_gate(sacred)
        for r,z,h,c in [(9.6,6,.14,BRONZE),(9.25,6.14,.18,LIME),(8.55,6.32,.17,(.42,.42,.37))]:
            drum(sacred,(0,90,z),r,h,c)
        for r in (5.2,7.75,8.3):
            points=[(r*math.cos(i*TAU/120),90+r*math.sin(i*TAU/120),6.506) for i in range(121)]
            g.line('hammered solar inlay',points,(.94,.74,.40,1),2,sacred)
        for i in range(48):
            a=i*TAU/48
            inlay=self.box('calendar notch',(7.99*math.sin(a),90+7.99*math.cos(a),6.512),(.042,.24 if i%4 else .47,.018),BRONZE,sacred)
            inlay.setH(-math.degrees(a))
        for side in (-1,1):
            for j,(y,h) in enumerate([(79,5.7),(84,7.2),(91,8.7),(96,9.8)]):
                x=side*(8.5 if j%2==0 else 7.6)
                self.court_column(sacred,x,y,h,j,side)
                tile=self.box('levitating sacred tablet',(x,y,11+h),(1.18,.95,4.7+j*.38),(.35,.37,.33),g.effects)
                self.box('suspended gilt foot',(0,0,-.49),(1.01,1.01,.022),BRONZE,tile)
                for dx in (-.34,.34):
                    self.box('tablet edge gilding',(dx,-.505,0),(.026,.012,.88),BRONZE,tile)
                stamp=image_card(g,tile,f'mark{(j*6+(side>0)*3):02}',.71,.19)
                stamp.setPos(0,-.516,-.23)
                g.suspended.append((tile,11+h,j*.7+side))
        g.offer=drum(sacred,(-1.9,83.5,6.32),.73,.75,LIME)
        g.altarjade=self.taper('jade offering',(-1.9,83.5,7.08),(.6,.6,.8),(.48,.9,.7),1,g.effects)
        self.obstruction(-1.9,83.5,1.45,1.45,7.2)
        self.building('stele',-18,73,5.5,-70,4.2,4.7)
        g.wheel=image_card(g,g.effects,'disc',19,19,True)
        g.wheel.setPos(0,94,18.2)
        g.shafts=[]
        for i in range(7):
            n=image_card(g,g.effects,'shaft',3.2+i%3,16+i%4,True)
            n.setPos(-7+i*2.3,89+i%3,14.3+i%3)
            n.setR(-17+i*.9)
            g.shafts.append(n)

    def island(self, root, x,y,z,r,seed):
        rng=random.Random(seed)
        verts=[]
        sides=44
        for i in range(sides):
            a=i*TAU/sides
            rim=r*(1+rng.uniform(0,.075))
            for size,zz in [(rim,z),(rim*1.015,z-rng.uniform(.7,1.6)),(rim*.84,z-r*rng.uniform(.37,.53)),(rim*.34,z-r*rng.uniform(.66,.87))]:
                verts.append((x+size*math.cos(a),y+size*math.sin(a),zz))
        for tier,color in enumerate([(.33,.43,.33),(.51,.45,.42),(.31,.36,.40)]):
            faces=[(i*4+tier, i*4+tier+1,((i+1)%sides)*4+tier+1,((i+1)%sides)*4+tier) for i in range(sides)]
            node=mesh('exposed hanging strata',verts,faces)
            node.reparentTo(root);node.setColor(*color,1);node.setTwoSided(True)
        node=mesh('island meadow and keel',verts,[tuple(range(0,4*sides,4)),tuple(reversed(range(3,4*sides,4)))])
        node.reparentTo(root);node.setColor(.40,.55,.39,1)
        for i in range(12):
            a=rng.random()*TAU
            node=self.box('hanging basalt',(x+.88*r*math.cos(a),y+.88*r*math.sin(a),z-r*.30),(r*.13,r*.14,r*rng.uniform(.55,.92)),(.38,.41,.38),root)
            node.setH(rng.randrange(40))

    def cloud_arch(self,root,x,y,z,j):
        arch=self.gate.copyTo(root);arch.setPos(x,y+4,z);arch.setScale(1 if not j else .68)
        if not j:
            for dx in (-4,4):self.obstruction(x+dx,y+4,3.1,3.2,z+12)

    def cloud_tower(self,root,xx,yy,z,tall,j):
        self.taper('tower footing',(xx,yy,z),(4.3,4.3,.75),LIME,1,root)
        self.taper('faceted watchtower',(xx,yy,z+.7),(3.8,3.8,tall),LIME,.8,root)
        for h in (.24,.72,.95):
            self.taper('jade tower band',(xx,yy,z+.7+tall*h),(3.61,3.61,.21),JASPER,.99,root)
        self.roof(xx,yy,z+tall+.85,4.4,4.4,1.6,root,(.48,.31,.17))
        if not j:self.obstruction(xx,yy,4.2,4.2,z+tall+2)

    def cloud_house(self,root,xx,yy,z):
        self.box('cloud dwelling',(xx,yy,z+1.07),(3.35,3.1,2.12),(.68,.55,.39),root)
        self.roof(xx,yy,z+2.22,4.25,3.95,1.83,root,(.57,.31,.175))
        for win in (-.79,.79):
            self.box('deep window',(xx+win,yy-1.57,z+1.33),(.54,.09,.76),(.15,.205,.20),root)
        if z==35:self.obstruction(xx,yy,3.4,3.15,z+3.6)

    def build_city(self):
        g=self.g
        root=g.render.attachNewNode('city above the cloudbank')
        skylight=DirectionalLight('clear cloud light')
        skylight.setColor((.39,.47,.53,1))
        source=g.render.attachNewNode(skylight);source.setHpr(-23,-43,0);root.setLight(source)
        for j,(x,y,z,r) in enumerate([(*CITY,18),(-19,166,43,13),(56,180,47,15),(-50,193,55,8),(81,161,34,6)]):
            self.island(root,x,y,z,r,12+j)
            self.cloud_arch(root,x,y,z,j)
            for k in range(3 if r>10 else 1):
                dx=(-1 if k%2 else 1)*r*(.45+.12*(k==2))
                yy=y+r*(k*.42-.45)
                tall=(6.4+3.7*k)*(1+.15*j)
                self.cloud_tower(root,x+dx,yy,z,tall,j)
            for k in range(5):
                a=k*TAU/5+.67
                self.place('oak',x+.84*r*math.cos(a),y+.84*r*math.sin(a),z,3.6+(k%3),k*71)
        for k in range(3):
            drum(root,(22,155,35+k*.075),4.4-k*.5,.075, JASPER if k==1 else LIME)
        # Human-scale galleries sit against the high towers. A paved promenade
        # keeps a clear sightline from the south landing through to the arch.
        for x,y,z,r in [(22,155,35,18),(-19,166,43,13),(56,180,47,15)]:
            for side in (-1,1):
                for row in range(2):
                    xx=x+side*(r*.48+row*1.1); yy=y+2.2+row*4.1
                    self.cloud_house(root,xx,yy,z)
            for col in range(-1,2):
                for row in range(9):
                    yy=y-r*.82+row*1.24
                    self.box('travertine paving',(x+col*1.22,yy,z+.025),(1.19,1.21,.05),(.65+.02*(row%3),.61,.48),root)
            for k in range(23):
                a=k*TAU/24
                if math.cos(a)<-.87:continue
                pos=(x+(r-.6)*math.sin(a),y+(r-.6)*math.cos(a),z+.38)
                wall=self.box('low carved parapet',pos,(r*.24,.35,.76),LIME,root);wall.setH(-math.degrees(a))
        g.skyseal=image_card(g,g.effects,'disc',5.2,5.2,True)
        g.skyseal.setPos(22,155.8,37.1)
        root.flattenStrong()
        rng=random.Random(55)
        for i in range(57):
            x=rng.uniform(-122,142);y=rng.uniform(150,225)
            z=rng.choice([19,23,26,55,74])+rng.uniform(-3,3)
            n=image_card(g,g.render,f'cloud{i%3}',rng.uniform(26,53),rng.uniform(8,17))
            n.setPos(x,y,z);n.setBillboardPointEye();n.setColorScale(1,1,1,.89)

