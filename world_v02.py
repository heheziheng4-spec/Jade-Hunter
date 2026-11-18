"""Walkable Liangzhu slice: lowland -> east/west river -> craft terrace -> ritual axis.

All architecture is editable geometry; no baked concept art or overhead camera.
Coordinates are metres, +Y is north. Keep floor_height and the visible stairs in sync.
"""
import math, random
from panda3d.core import Vec3, TransparencyAttrib, TextNode
from geometry import mesh, cone

SAND=(.66,.48,.29); EDGE=(.82,.65,.40); WOOD=(.28,.18,.10)
THATCH=(.65,.46,.22); JADE=(.29,.55,.43)

def floor_height(x,y):
    if y>=56 and abs(x)<38:
        if y<74 and abs(x)<6.5:
            return 2.4 + (int((y-56)*2)+1)*.1
        return 6.0
    if y>=24:
        if y<34 and any(abs(x-b)<4.1 for b in (-32,0,32)):
            return .9+(int((y-24)*2)+1)*.075
        return 2.4
    if 8<=y<24 and any(abs(x-b)<3.8 for b in (-32,0,32)):
        return .1+max(0,min(1,(y-8)/4))*.8
    if any(abs(x-b)<4 for b in (-30,-40)) and 2.5<y<9.5:return .4
    return .1

def zone_name(x,y):
    if y>=56:return '内圈 · 莫角山礼制高台'
    if y>=24:return '中圈 · 临水百工作坊' if x<-10 else '中圈 · 氏族台地与粮仓'
    if 12<y<24:return '水系 · 木桥与水门'
    if x>9:return '外圈 · 水渠与低地稻田'
    if x<-12:return '外圈 · 水运码头与集市'
    return '南门 · 先民聚落'

class Builder:
    def __init__(self,game):
        self.g=game;self.r=random.Random(218);self.root=game.render.attachNewNode('architecture / reusable modules')
        self.groups={};self.cylinder=cone(12,1);self.point=cone(12,0)

    def group(self,name):
        root=self.root.attachNewNode(name);self.groups[name]=root;return root

    def box(self,name,p,s,c=WOOD,parent=None):return self.g.block(name,p,s,c,parent if parent is not None else self.root)

    def taper(self,name,p,s,c=SAND,top=.76,parent=None):
        node=cone(8,top);node.reparentTo(parent if parent is not None else self.root)
        node.setName(name);node.setPos(*p);node.setScale(*s);node.setColor(*c,1);return node

    def beam(self,a,b,width=.16,c=WOOD,parent=None):
        a,b=Vec3(*a),Vec3(*b);d=b-a
        obj=self.box('timber joint',tuple((a+b)*.5),(width,width,d.length()),c,parent)
        obj.lookAt(b);obj.setP(obj.getP()+90)
        return obj

    def obstruction(self,x,y,w,d,h):self.g.obstacles.append((x-w/2,x+w/2,y-d/2,y+d/2,h))

    def roof(self,x,y,z,w,d,h,parent=None,c=THATCH):
        v=[(-w/2,-d/2,0),(w/2,-d/2,0),(w/2,d/2,0),(-w/2,d/2,0),(-w*.29,0,h),(w*.29,0,h)]
        obj=mesh('hipped thatch roof',v,[(0,1,5,4),(1,2,5),(2,3,4,5),(3,0,4)])
        obj.reparentTo(parent if parent is not None else self.root);obj.setPos(x,y,z);obj.setColor(*c,1);obj.setTwoSided(True)
        self.beam((x-w*.34,y,z+h),(x+w*.34,y,z+h),.20,WOOD,parent)
        # Individual thatch ribs retain a readable silhouette at person height.
        for i in range(int(w*2)):
            dx=-w*.45+i*.5
            for side in (-1,1):
                self.beam((x+dx*.65,y,z+h+.035),(x+dx,y+side*d*.51,z+.02),.055,(.76,.57,.29),parent)
        return obj

    def blob(self,x,y,z,w,d,parent=None):
        obj=self.taper('contact shadow',(x,y,z),(w,d,.008),(.27,.23,.14),1,parent)
        obj.setLightOff();obj.setTransparency(TransparencyAttrib.MAlpha);obj.setColor(.22,.18,.12,.19)

    def house(self,x,y,w=5,d=4,base=None,grand=False,parent=None):
        z=floor_height(x,y) if base is None else base;deck=z+1.5
        self.blob(x,y,z+.015,w+2,d+2,parent)
        for dx in (-w/2+.3,w/2-.3):
            for dy in (-d/2+.2,d/2-.2):self.box('stilt post',(x+dx,y+dy,z+1.7),(.24,.24,3.4),WOOD,parent)
        self.box('raised timber deck',(x,y,deck),(w+.65,d+.9,.22),(.40,.27,.14),parent)
        for i in range(9):
            zz=deck+.19+i*.26
            c=(.40+(i%3)*.023,.28+(i%3)*.015,.16)
            self.box('stacked log wall',(x,y+d/2,zz),(w,.28,.24),c,parent)
            for side in (-1,1):
                self.box('side log wall',(x+side*w/2,y,zz),(.28,d+.25,.24),c,parent)
                self.box('front log pier',(x+side*w*.34,y-d/2,zz),(w*.32,.28,.24),c,parent)
        self.box('deep doorway',(x,y-d/2+.10,deck+1.1),(w*.26,.16,2.2),(.13,.10,.065),parent)
        self.roof(x,y,deck+2.6,w+1.4,d+1.2,2.0 if grand else 1.5,parent)
        for i in range(8):
            self.box('house ladder tread',(x,y-d/2-.4-i*.24,z+.12+(7-i)*.18),(1.1,.30,.16),(.47,.32,.17),parent)
        self.obstruction(x,y,w+.6,d+.6,deck+5)
        for side in (-1,1):self.box('warm window',(x+side*w*.32,y-d/2-.16,deck+1.1),(.38,.015,.56),(.96,.68,.26),parent)

    def canopy(self,x,y,w=6,d=4,z=None,parent=None):
        z=floor_height(x,y) if z is None else z
        for dx in (-w/2+.3,w/2-.3):
            for dy in (-d/2+.2,d/2-.2):
                self.box('workshop post',(x+dx,y+dy,z+1.6),(.18,.18,3.2),WOOD,parent)
        self.roof(x,y,z+3.2,w+.7,d+.7,1.3,parent)
        self.box('craft table',(x,y+.3,z+1.05),(w*.68,1.2,.18),WOOD,parent)
        for dx in (-w*.27,w*.27):self.box('table leg',(x+dx,y+.3,z+.52),(.15,.6,1.04),WOOD,parent)
        self.obstruction(x,y+.3,w*.68,1.2,z+1.2)

    def pot(self,x,y,z,s=.55,parent=None):
        c=self.r.choice([(.56,.31,.16),(.70,.48,.26),(.45,.32,.22)])
        self.taper('fired pottery',(x,y,z),(s,s,s*.85),c,.70,parent)
        self.taper('pot lip',(x,y,z+s*.81),(s*.74,s*.74,s*.12),c,1,parent)
        self.taper('dark pot mouth',(x,y,z+s*.94),(s*.54,s*.54,.015),(.18,.14,.09),1,parent)

    def mask(self,x,y,z,w=.9,parent=None,glowing=False):
        col=(.36,.28,.15,1) if not glowing else (.9,.83,.46,1)
        for side in (-1,1):
            cx=x+side*w*.27
            pts=[(cx-w*.18,y,z+w*.20),(cx+w*.18,y,z+w*.20),(cx+w*.18,y,z-w*.1),(cx-w*.18,y,z-w*.1),(cx-w*.18,y,z+w*.20)]
            line=self.g.line('paired eye glyph',pts,col,3,parent or self.root)
            if glowing:self.g.runes.append(line)
            self.g.line('glyph eye',[(cx-.04,y,z+.04),(cx+.04,y,z+.04)],col,3,parent or self.root)
        line=self.g.line('nose and jaw glyph',[(x,y,z+.30*w),(x,y,z-.28*w),(x-.15*w,y,z-.28*w),(x-.15*w,y,z-.48*w),(x+.3*w,y,z-.48*w)],col,2,parent or self.root)
        if glowing:self.g.runes.append(line)

    def pillar(self,x,y,h=7,w=1.65,z=None,glow=False,parent=None):
        z=floor_height(x,y) if z is None else z
        self.box('pillar plinth',(x,y,z+.16),(w*1.4,w*1.3,.32),SAND,parent)
        self.taper('eroded monolith',(x,y,z+.3),(w,w,h),SAND,.76,parent)
        self.box('stone capital',(x,y,z+h+.3),(w*1.22,w*1.1,.38),EDGE,parent)
        glyphroot=self.g.render.attachNewNode('living jade glyph') if glow else parent
        self.mask(x,y-w*.48-.012,z+h*.65,w*.8,glyphroot,glow)
        self.obstruction(x,y,w,w,z+h+.5)

    def banner(self,x,y,z=None,parent=None):
        z=floor_height(x,y) if z is None else z
        self.box('banner pole',(x,y,z+3.1),(.11,.11,6.2),WOOD,parent)
        self.box('banner arm',(x+.45,y,z+5.9),(1.4,.1,.1),WOOD,parent)
        self.box('jade cloth',(x+.5,y,z+4.6),(1.05,.04,2.3),(.35,.42,.29),parent)
        self.mask(x+.5,y-.03,z+4.8,.70,parent)

    def kiln(self,x,y,parent=None):
        z=floor_height(x,y)
        self.taper('clay kiln base',(x,y,z),(3.6,3.6,1.5),(.62,.36,.18),.90,parent)
        self.taper('kiln dome',(x,y,z+1.5),(3.24,3.24,1.4),(.73,.46,.24),.42,parent)
        self.taper('kiln chimney opening',(x,y,z+2.91),(1.35,1.35,.04),(.18,.14,.1),1,parent)
        self.box('kiln firebox',(x,y-1.65,z+.62),(1.1,.09,.9),(.18,.09,.04),parent)
        fire=self.box('living kiln fire',(x,y-1.72,z+.52),(.65,.035,.65),(1,.46,.10),self.g.effects)
        fire.setLightOff();self.g.kilnfires.append(fire)
        self.obstruction(x,y,3.7,3.7,z+3)
        for i in range(5):self.pot(x-2+i*.9,y-2.4,z,.55,parent)
        for i in range(6):
            p=self.taper('kiln smoke',(x,y,z+3+i*.58),(1,1,1),(.71,.68,.55),.3,self.g.effects)
            p.setLightOff();p.setTransparency(TransparencyAttrib.MAlpha);p.setDepthWrite(False)
            self.g.smokepuffs.append((p,x,y,z+3,i))

    def boat(self,x,y,s=1,heading=0):
        root=self.g.render.attachNewNode('dugout canoe')
        # Open hull: inner floor, raised gunwales, high curved bow and stern.
        stations=[(-3.7,.02,1.35),(-2.8,.65,.60),(-1.7,1,.35),(0,1.05,.32),(1.7,1,.35),(2.8,.65,.60),(3.7,.02,1.35)]
        v=[]
        for yy,w,z in stations:v.extend([(-w,yy,z),(w,yy,z),(-w*.65,yy,.04),(w*.65,yy,.04)])
        f=[]
        for i in range(6):
            a=i*4;b=(i+1)*4;f.extend([(a,b,b+2,a+2),(a+1,a+3,b+3,b+1),(a+2,b+2,b+3,a+3)])
        obj=mesh('hollow carved hull',v,f);obj.reparentTo(root);obj.setColor(.30,.17,.075,1);obj.setTwoSided(True)
        for yy in (-1.5,1):self.box('canoe seat',(0,yy,.35),(1.65,.28,.12),(.46,.30,.14),root)
        self.beam((-.5,-1,.5),(2,2,.65),.09,WOOD,root)
        self.box('paddle blade',(2,2,.65),(.35,.8,.08),WOOD,root)
        root.setPos(x,y,-.12);root.setScale(s);root.setH(heading);root.flattenStrong()
        self.g.boats.append((root,x,y,-.12));return root

    def tree(self,x,y,z=None,s=1,parent=None):
        z=floor_height(x,y) if z is None else z
        self.taper('tree trunk',(x,y,z),(.38*s,.38*s,3.5*s),WOOD,.6,parent)
        for dx,dy,dz in [(0,0,3.2),(.8,.1,3.8),(-.8,.3,3.6),(0,-.7,4.2)]:
            self.taper('faceted canopy',(x+dx*s,y+dy*s,z+dz*s),(3.1*s,2.8*s,1.35*s),self.r.choice([(.34,.39,.19),(.42,.44,.21),(.29,.35,.22)]),.4,parent)

    def build(self):
        g=self.g;r=self.r
        g.effects=g.render.attachNewNode('animated effects');g.boats=[];g.smokepuffs=[];g.kilnfires=[];g.resident_homes=[]
        ground=self.group('01 terrain and river banks')
        self.box('south alluvial plain',(0,-7,-.55),(108,38,1.3),(.57,.47,.29),ground)
        self.box('middle rammed-earth terrace',(0,45,1.0),(100,22,2.8),SAND,ground)
        for a,b in [(-50,-36.1),(-27.9,-4.1),(4.1,27.9),(36.1,50)]:
            self.box('terrace beside river stairs',((a+b)/2,29,1),(b-a,10,2.8),SAND,ground)
        self.box('sacred upper terrace',(0,87,3.2),(76,26,5.6),(.63,.45,.27),ground)
        for x in (-22.25,22.25):self.box('upper terrace stair wings',(x,65,3.2),(31.5,18,5.6),(.63,.45,.27),ground)
        self.box('procession stair foundation',(0,65,1.2),(13,18,2.4),SAND,ground)
        for x in (-47,47):self.box('river banks',(x,18,-1),(5,12,2),SAND,ground)
        # All three crossings have identical ramps and physical walking heights.
        for x in (-32,0,32):
            for i in range(8):self.box('approach step',(x,8+i*.5+.25,.1+(i+1)*.05),(7.6,.5,(i+1)*.1),(.43,.30,.16),ground)
            self.box('bridge deck',(x,18,.73),(7.6,12,.34),WOOD,ground)
            for j in range(36):self.box('bridge boards',(x,12+j/3,.89),(7.7,.27,.06),(.50+(j%3)*.025,.35,.19),ground)
            for side in (-1,1):
                for y in (12,15,18,21,24):self.box('bridge railing post',(x+side*3.7,y,1.5),(.16,.16,2.0),WOOD,ground)
                for z in (1.45,2.2):self.box('bridge handrail',(x+side*3.7,18,z),(.14,12,.14),WOOD,ground)
                g.obstacles.append((x+side*3.7-.09,x+side*3.7+.09,11.9,24.1,2.35))
            for i in range(20):
                z=.9+(i+1)*.075
                self.box('terrace river stairs',(x,24+i*.5+.25,(z+.1)/2),(8.2,.5,z-.1),SAND,ground)
                self.box('stair stone lip',(x,24+i*.5+.04,z+.005),(8.2,.08,.045),EDGE,ground)
        for i in range(36):
            z=2.4+(i+1)*.1
            self.box('great ceremonial stair',(0,56+i*.5+.25,(z+2.4)/2),(13,.5,z-2.4),SAND,ground)
            self.box('sunlit stair edge',(0,56+i*.5+.045,z+.006),(13,.08,.05),EDGE,ground)
        # Long central procession route, borders, and breaks in the enclosure.
        for y0,y1,z in [(-22,8,.1),(34,56,2.4),(74,97,6)]:
            self.box('processional paving',(0,(y0+y1)/2,z-.015),(7,y1-y0,.03),(.74,.58,.36),ground)
            for y in range(y0,y1,2):
                for x in (-3.6,3.6):self.box('walkway edge',(x,y,z+.06),(.17,1.3,.12),EDGE,ground)
        for x in (-46,46):
            for ya,yb,z in [(-21,11,.1),(25,55,2.4)]:self.box('outer earth wall',(x,(ya+yb)/2,z+1.1),(2,yb-ya,2.2),(.56,.40,.24),ground)
        for x in (-26,26):self.box('south gate wall',(x,-22,1.2),(39,1.8,2.4),SAND,ground)
        for x in (-6,6):self.pillar(x,-21,5,1.6,.1,parent=ground)
        for side in (-1,1):
            self.box('inner terrace edge',(side*24,56,5.9),(35,1.3,.35),EDGE,ground)
            self.pillar(side*8,55,7,2.1,2.4,parent=ground)
        g.river=self.box('main east-west river',(0,18,-.15),(142,12,.08),(.28,.48,.46),g.effects)
        g.river.setTransparency(TransparencyAttrib.MAlpha);g.river.setColor(.30,.50,.47,.91)
        g.waterlines=g.effects.attachNewNode('river glints')
        for i in range(80):
            x=r.uniform(-67,67);y=r.uniform(12.5,23.5)
            self.box('soft water ripple',(x,y,-.095),(r.uniform(.5,2.5),.04,.01),(.55,.67,.53),g.waterlines)
        # Paddy/canal layout follows the east and south lowlands in the source script.
        farms=self.group('02 lowland rice and canals')
        g.crops=g.render.attachNewNode('living rice');g.water=g.render.attachNewNode('irrigated paddies')
        for x in (18,26,34):
            for y in (-15,-6,3):
                self.box('rice field mud',(x,y,.11),(7.4,7.4,.10),(.31,.30,.18),farms)
                self.box('paddy water',(x,y,.175),(7.2,7.2,.035),(.36,.53,.40),g.water)
                for side in (-1,1):
                    self.box('field bank',(x+side*3.9,y,.22),(.35,8.1,.35),(.51,.40,.22),farms)
                    self.box('field bank',(x,y+side*3.9,.22),(8.1,.35,.35),(.51,.40,.22),farms)
                for xx in range(6):
                    for yy in range(6):
                        px=x-2.9+xx*1.15;py=y-2.9+yy*1.15
                        self.taper('rice clump',(px,py,.18),(.16,.16,.65+r.random()*.25),(.58,.62,.28),.1,g.crops)
                        self.beam((px,py,.36),(px+.24,py,.72),.055,(.72,.67,.29),g.crops)
        g.crops.flattenStrong();g.water.flattenStrong()
        g.canalwater=g.render.attachNewNode('three irrigation channels')
        for x in (-11,10,41):
            self.box('irrigation trench',(x,-5,.10),(1.2,31,.06),(.27,.33,.24),farms)
            self.box('irrigation flow',(x,-5,.14),(.9,31,.05),(.34,.58,.50),g.canalwater)
        self.box('canal crossing',(10,-4,.20),(2.8,2,.18),WOOD,farms)
        g.blockage=g.render.attachNewNode('clogged channel')
        for i in range(6):self.taper('debris',(10+r.uniform(-.4,.4),-6+r.uniform(-.8,.8),.1),(.7,.6,.6),(.46,.37,.23),.5,g.blockage)
        g.flood=self.box('lowland overflow',(26,-5,.10),(25,29,.06),(.30,.43,.40),g.effects)
        g.flood.setTransparency(TransparencyAttrib.MAlpha);g.flood.setColor(.30,.43,.40,.78)
        # Harbor, raised houses, wood piles and canoes: image 1.
        harbor=self.group('03 stilt settlement and harbor')
        for x,y,w in [(-19,-12,5),(-30,-11,6),(-39,0,5),(-20,4,5),(-10,4,4.5),(-39,36,5),(19,39,6),(32,47,5),(14,49,5)]:
            self.house(x,y,w=w,parent=harbor)
        for x,y in [(-30,6),(-40,7)]:
            self.box('harbor deck',(x,y,.25),(8,7,.3),(.42,.28,.15),harbor)
            for i in range(17):self.box('dock plank seam',(x-3.8+i*.46,y,.42),(.03,7,.02),(.26,.18,.10),harbor)
            for side in (-1,1):self.box('dock mooring',(x+side*3.7,y+3,1.1),(.28,.28,2.4),WOOD,harbor)
        self.boat(-22,17,1.05,65);self.boat(-42,19,.8,90);self.boat(18,18,.9,-70);self.boat(43,20,1.2,-70)
        self.canopy(-24,-1,5,3,parent=harbor);self.canopy(-10,-13,4,3,parent=harbor)
        for x,y in [(-33,0),(-17,-5),(-29,42)]:
            z=floor_height(x,y)
            for j in range(9):self.box('stacked logs',(x+(j%3)*.35,y,z+.22+(j//3)*.3),(.32,3,.3),(.42,.28,.14),harbor)
        # Western craft terraces: image 3.
        craft=self.group('04 pottery stone and jade workshops')
        for x,y in [(-20,37),(-33,48),(-12,48)]:
            self.canopy(x,y,7,4,parent=craft)
            z=floor_height(x,y)
            for j in range(7):self.pot(x-2.3+j*.73,y+.2,z+1.15,.48,craft)
        self.kiln(-26,40,craft);self.kiln(-24,49,craft)
        for i in range(24):
            x=r.uniform(-42,-37);y=r.uniform(44,51)
            self.taper('jade boulder',(x,y,2.4),(.9,1.2,r.uniform(.4,1.1)),(.40,.52,.37),.6,craft)
        for i in range(15):
            x=-15+(i%5)*.8;y=36+(i//5)*.8
            self.box('dressed stone',(x,y,2.7),(.65,.65,.65),(.63,.60,.44),craft)
        for x,y in [(-37,29),(-9,40),(39,30)]:self.pillar(x,y,5,1.8,parent=craft)
        # Governor's plaza / storage is on the middle level, not in the floodplain.
        civic=self.group('05 clan square and raised granaries')
        self.house(24,51,8,6,grand=True,parent=civic)
        self.canopy(9,39,5,4,parent=civic)
        for x in (20,25,30):
            for j in range(3):self.pot(x+j*.7,44,2.4,.9,civic)
        for x,y in [(6,35),(-6,35),(8,51),(-8,51)]:self.banner(x,y,parent=civic)
        # Three major roof silhouettes on the elevated ritual axis: image 2.
        sacred=self.group('06 ritual high ground')
        for x in (-23,23):self.house(x,84,11,9,6,True,sacred)
        g.palace=g.render.attachNewNode('rebuilt ritual hall')
        for x in (-6,-3,3,6):
            for y in (86,94):self.box('hall timber column',(x,y,9.4),(.42,.42,6.8),WOOD,g.palace)
        self.roof(0,90,12.8,17,12,5,g.palace)
        self.roof(0,90,10.3,18.5,13,1.4,g.palace)
        self.box('hall rear wall',(0,95,9.5),(14,.4,6),(.40,.29,.17),g.palace)
        self.obstruction(0,95,14,.6,16)
        # Initial unbuilt core is a low foundation; repair reveals the roof and luminous carvings.
        self.box('hall foundation',(0,90,6.15),(17,12,.3),(.60,.43,.26),sacred)
        for side in (-1,1):
            for y,h in [(61,8),(70,7),(79,8),(90,9)]:self.pillar(side*8,y,h,2.0,6,True,sacred)
            for y in range(74,94,4):
                self.box('ritual corridor post',(side*12,y,8.7),(.3,.3,5.4),WOOD,sacred)
                self.box('ritual corridor rail',(side*12,y,7),( .25,4,.2),WOOD,sacred)
            self.box('ritual corridor lintel',(side*12,84,11.5),(2.5,24,.7),SAND,sacred)
            for y in (77,84,91):self.banner(side*10,y,6,sacred)
        g.offer=self.box('offering altar',(0,85,6.6),(3.4,2,1.2),SAND,sacred)
        self.box('altar cap',(0,85,7.25),(4,2.4,.2),EDGE,sacred)
        self.obstruction(0,85,4,2.4,7.4)
        g.altarjade=self.taper('jade cong on altar',(0,85,7.4),(.65,.65,.9),(.46,.94,.77),1,g.effects);g.altarjade.setLightOff()
        # Water gate and relief on east edge; dam feedback must be visible from the safe shore.
        g.damroot=g.render.attachNewNode('repaired east water gate')
        for j in range(7):self.taper('dam infill',(38,12+j*.9,-.6),(2,1.1,2.0),(.52,.46,.32),.82,g.damroot)
        for x,y in [(38,11),(38,23)]:self.pillar(x,y,4,2,0,parent=ground)
        g.jadelight=self.taper('jade on washed shore',(41,6,.25),(.7,.7,.9),(.33,.91,.78),.6,g.effects);g.jadelight.setLightOff()
        for i,(x,y) in enumerate([(-6,-10),(-27,3),(-15,30)]):
            root=g.render.attachNewNode('supplies');g.cache_nodes['cache'+str(i)]=root;z=floor_height(x,y)
            for j in range(5):self.box('collectable wood',(x+(j%2)*.4,y+(j//2)*.3,z+.3),(.36,1,.4),(.45,.29,.14),root)
        self.taper('hearth ring',(0,0,.1),(1.8,1.8,.3),(.33,.28,.20),1,harbor)
        g.flame=self.taper('campfire',(0,0,.35),(.6,.6,1.1),(1,.58,.16),0,g.effects);g.flame.setLightOff()
        # Layered horizon: quiet mountains, ruined arch silhouettes, river reeds.
        scenery=self.group('07 distant scenery')
        for i in range(45):
            x=r.choice([-1,1])*r.uniform(57,125);y=r.uniform(-40,180)
            self.taper('sandstone ridge',(x,y,-4),(r.uniform(10,30),r.uniform(10,30),r.uniform(18,58)),(.60,.49,.33),r.uniform(.08,.5),scenery)
        for x in range(-100,110,18):self.taper('far mountain',(x,160,-1),(30,35,r.uniform(24,50)),(.62,.57,.41),.10,scenery)
        for x,y in [(-60,45),(-60,65),(-60,85)]:self.pillar(x,y,22,6,0,parent=scenery)
        self.box('distant broken lintel',(-60,64,22),(6,45,2),(.63,.48,.29),scenery)
        for i in range(65):
            x=r.choice([-1,1])*r.uniform(39,55);y=r.uniform(-20,100)
            if 10<y<25:continue
            self.tree(x,y,s=r.uniform(.7,1.5),parent=scenery)
        for x,y in [(-35,54),(35,55),(18,28),(-40,-18),(37,-21),(-20,97),(20,97)]:self.tree(x,y,s=1.3,parent=scenery)
        for i in range(140):
            x=r.uniform(-48,48);y=r.choice([11.0,24.1])+r.uniform(-.4,.4)
            if any(abs(x-b)<4.5 for b in (-32,0,32)):continue
            z=.1 if y<12 else 2.4
            self.taper('river reed',(x,y,z),(.07,.07,r.uniform(.4,1.3)),(.42,.47,.24),.15,scenery)
        for root in self.groups.values():root.flattenStrong()
        g.palace.flattenStrong()
        # Characters and signposts stay separate from static geometry.
        people=[(-3,0), (18,-9), (30,-4), (-23,35), (-29,45),(-21,-2),(-36,3),(13,40),(27,43),(22,78),(-21,79)]
        for i,(x,y) in enumerate(people):
            npc,parts=g.person(r.choice([(.56,.40,.23),(.44,.46,.26),(.61,.50,.32),(.39,.31,.22)]))
            pos=(x,y,floor_height(x,y));npc.setPos(*pos);npc.setH(r.uniform(0,360));g.npcs.append((npc,parts));g.resident_homes.append(pos)
        g.player,g.parts=g.person((.68,.27,.13));g.player.setPos(0,-17,.1)
        g.shadow=g.render.attachNewNode('player contact shadow')
        for i in range(6):
            obj=self.cylinder.copyTo(g.shadow);obj.setScale(1.1-i*.12,.8-i*.08,.003);obj.setZ(i*.002)
            obj.setColor(.16,.13,.10,.045);obj.setTransparency(TransparencyAttrib.MAlpha);obj.setLightOff();obj.setDepthWrite(False)
        g.targets={
            'elder':((-3,0,.1),'长者','交谈 · 了解聚落'), 'rest':((0,0,.1),'营火','休整 · 推进一天'),
            'canal':((10,-6,.1),'水渠','疏通水渠'), 'farm':((18,-9,.1),'稻田','增派 1 名农民'),
            'workshop':((-23,35,2.4),'百工作坊','增派 1 名手工者'), 'dam':((36,9,.1),'东水门','投入 10 材料修堤'),
            'jade':((41,6,.1),'河滩玉石','拾取雨水冲出的玉器'), 'altar':((0,82.5,6),'莫角山祭坛','整修 / 献玉祭祀'),
            'cache0':((-6,-10,.1),'木料','收集材料 +4'), 'cache1':((-27,3,.1),'木料','收集材料 +4'), 'cache2':((-15,30,2.4),'石料','收集材料 +4')}
        for key,(pos,name,verb) in g.targets.items():
            tn=TextNode(key);tn.setFont(g.font);tn.setText(name);tn.setAlign(TextNode.ACenter);tn.setTextColor(1,.93,.72,1)
            obj=g.render.attachNewNode(tn);obj.setPos(pos[0],pos[1],pos[2]+2.8);obj.setScale(.34);obj.setBillboardPointEye();obj.setLightOff();g.markers[key]=obj
        g.dust=[]
        for i in range(65):
            p=self.box('golden dust',(r.uniform(-45,45),r.uniform(-18,94),r.uniform(1,12)),(.04,.04,.04),(1,.84,.50),g.effects);p.setLightOff();g.dust.append(p)
        g.rain=g.render.attachNewNode('local rainfall')
        for i in range(190):
            x=r.uniform(-18,18);y=r.uniform(-18,18);z=r.uniform(1,20)
            g.line('rain streak',[(x,y,z),(x+.15,y+.02,z-.8)],(.66,.76,.76,.55),1,g.rain)
        g.rain.flattenStrong();g.rain.setTransparency(TransparencyAttrib.MAlpha)
        # Distant sun is geometry, softened with transparent rings and atmospheric fog.
        g.sunorb=g.render.attachNewNode('sun through haze')
        for i in range(7):
            disk=self.cylinder.copyTo(g.sunorb);disk.setScale(16+i*2,16+i*2,.02);disk.setP(90)
            disk.setY(i*.03);disk.setColor(1,.87,.50,1 if i==0 else .045)
            disk.setLightOff();disk.setFogOff();disk.setTransparency(TransparencyAttrib.MAlpha);disk.setDepthWrite(False)
        g.sunorb.setPos(0,148,44)
        g.refresh()
