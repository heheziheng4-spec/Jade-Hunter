import os, sys, math, random, json, time
from pathlib import Path
from dataclasses import asdict
from panda3d.core import *
from direct.showbase.ShowBase import ShowBase
from direct.gui.OnscreenText import OnscreenText
from direct.gui.DirectGui import DirectFrame, DirectButton
from rules import Village
from geometry import cube, cone, terrain, mesh

ROOT=Path(getattr(sys,'_MEIPASS',Path(__file__).parent))
SAVE=Path(os.environ.get('LOCALAPPDATA',str(Path.home()))) / 'SandlightDemo'
SAVE.mkdir(parents=True,exist_ok=True)
SMOKE='--smoke' in sys.argv
loadPrcFileData('', 'window-title Sandlight | Liangzhu\nwin-size 1440 900\nsync-video true\nshow-frame-rate-meter false\ntextures-power-2 none\nframebuffer-multisample 1\nmultisamples 4\naudio-library-name p3openal_audio\nnotify-level warning')

class Demo(ShowBase):
    def __init__(self):
        super().__init__()
        self.disableMouse();self.setBackgroundColor(.87,.73,.51,1)
        self.camLens.setFov(66);self.camLens.setNearFar(.1,260)
        self.render.setAntialias(AntialiasAttrib.MAuto)
        self.state=Village();self.keys={};self.yaw=0.;self.pitch=18.;self.distance=7.3
        self.vertical=0.;self.ground=True;self.near=None;self.dialog=False;self.last_mouse=None
        self.t=0;self.ceremony=0;self.toasting=14;self.toast='沿石径走向营火，与长者交谈。按住鼠标右键转动视角。'
        self.obstacles=[];self.markers={};self.runes=[];self.npcs=[];self.cache_nodes={};self.intro=True
        self.unit=cube();self.stone=cone(7,.75);self.round=cone(12,.8)
        self.font=self.loader.loadFont(Filename.fromOsSpecific('C:/Windows/Fonts/msyh.ttc').getFullpath())
        self.font.setPixelsPerUnit(48)
        self.light();self.world();self.ui();self.controls()
        self.taskMgr.add(self.update,'game-update')
        if '--load' in sys.argv:self.load()
        if SMOKE:self.taskMgr.doMethodLater(1.2,self.smoke,'smoke-test')

    def light(self):
        ambient=AmbientLight('warm sky');ambient.setColor((.48,.43,.33,1))
        self.render.setLight(self.render.attachNewNode(ambient))
        self.sun=DirectionalLight('late afternoon');self.sun.setColor((1.15,.94,.64,1))
        self.sun.setShadowCaster(False)
        self.sunpath=self.render.attachNewNode(self.sun);self.sunpath.setPos(45,-45,65);self.sunpath.lookAt(0,12,0)
        self.render.setLight(self.sunpath);self.render.setShaderAuto()
        self.fog=Fog('golden dust');self.fog.setColor(.87,.73,.51);self.fog.setExpDensity(.009)
        self.render.setFog(self.fog)

    def block(self,name,pos,scale,color,parent=None,stone=False):
        obj=(self.stone if stone else self.unit).copyTo(parent or self.render)
        obj.setName(name);obj.setPos(*pos);obj.setScale(*scale);obj.setColor(*color,1)
        return obj

    def line(self,name,points,color=(1,.87,.4,1),thick=2,parent=None):
        ls=LineSegs(name);ls.setThickness(thick);ls.setColor(*color)
        ls.moveTo(*points[0])
        for p in points[1:]:ls.drawTo(*p)
        o=(parent or self.render).attachNewNode(ls.create());o.setLightOff();return o

    def world(self):
        rng=random.Random(54)
        land=terrain();land.reparentTo(self.render);land.setColor(.67,.47,.29,1)
        # Paths and courtyard, built to walk through rather than viewed overhead.
        self.block('central stone walk',(0,13,-.06),(5.2,69,.16),(.72,.56,.37))
        self.block('village plaza',(0,1,0),(17,14,.12),(.64,.48,.32))
        self.block('farm path',(-10,-1,.015),(18,2,.1),(.74,.57,.37))
        self.block('river path',(11,14,.015),(25,2,.1),(.74,.57,.37))
        for i in range(50):
            y=-19+i*1.24
            for x in (-2.7,2.7):self.block('path edging',(x,y,.06),(.17,.6,.16),(.87,.66,.4))
        # Desert landscape massing around an irrigated oasis.
        for i in range(55):
            side=rng.choice([-1,1]);x=side*rng.uniform(33,80);y=rng.uniform(-26,105)
            rock=self.block('eroded outcrop',(x,y,-.5),(rng.uniform(4,15),rng.uniform(4,12),rng.uniform(3,14)),(.65+rng.random()*.1,.49,.31),stone=True)
            rock.setH(rng.uniform(0,360))
        for x,y in [(-25,-16),(26,-10),(-25,22),(26,38)]:
            self.block('waystone',(x,y,0),(1.4,1.1,4.2),(.65,.48,.30),stone=True)
        # Houses and workshop.
        for x,y in [(-12,10),(12,7)]:
            self.house(x,y)
        self.block('workshop floor',(-10,2,.15),(5,4,.3),(.48,.34,.22))
        for x in (-12,-8):
            for y in (0,4):self.block('timber post',(x,y,1.5),(.18,.18,3),(.28,.22,.15))
        roof=self.block('canvas canopy',(-10,2,3.2),(5.8,4.8,.16),(.79,.70,.45));roof.setR(5)
        self.block('worktable',(-10,3,1),(3,1,.3),(.38,.27,.16))
        # Paddy, dry then flooded.
        self.field=self.render.attachNewNode('irrigated field')
        for x in (-20,-15):
            for y in (-8,-3):
                self.block('paddy',(x,y,0),(4.6,4.6,.16),(.36,.31,.19),parent=self.field)
                for edge in (-2.4,2.4):self.block('field bank',(x+edge,y,.12),(.2,4.9,.28),(.55,.4,.23))
        self.water=self.block('irrigation water',(-17.5,-5.5,.09),(10,10,.03),(.30,.58,.55))
        self.water.setTransparency(TransparencyAttrib.MAlpha);self.water.setColor(.30,.58,.55,.7)
        self.crops=self.render.attachNewNode('rice plants')
        for i in range(170):
            x=rng.uniform(-22,-13);y=rng.uniform(-10,-1)
            self.block('rice',(x,y,.12),(.10,.10,rng.uniform(.4,.8)),(.56,.65,.28),parent=self.crops,stone=True)
        self.block('canal bed',(-10,-7,.01),(6,1,.14),(.31,.45,.39))
        self.canalwater=self.block('canal flow',(-10,-7,.14),(6,.72,.04),(.34,.63,.60))
        self.blockage=self.render.attachNewNode('canal obstruction')
        for i in range(7):self.block('debris',(-8.1+rng.uniform(-.4,.4),-7+rng.uniform(-.3,.3),0),(.7,.7,.65),(.49,.37,.24),parent=self.blockage,stone=True)
        # River kept at boundary of walking region; safe flood demonstration.
        self.block('river',(25,23,-.01),(7,62,.1),(.28,.50,.50))
        self.block('jade sandbank',(27,20,-.01),(5,7,.14),(.72,.55,.34))
        self.block('bridge',(24,15,.20),(10,3,.35),(.47,.34,.22))
        for x in range(20,30):self.block('bridge plank',(x,15,.4),(.10,3.1,.08),(.76,.58,.34))
        self.damroot=self.render.attachNewNode('repaired dam')
        for y in (10,12,14,16,18):self.block('dam stones',(20,y,0),(1.5,2,1.8),(.65,.51,.35),parent=self.damroot,stone=True)
        self.block('dam stub',(20,8,0),(2,3,1.1),(.57,.42,.27),stone=True)
        self.flood=self.block('floodwater',(-17,-5,.22),(13,13,.10),(.31,.47,.48));self.flood.setTransparency(TransparencyAttrib.MAlpha);self.flood.setColor(.31,.47,.48,.65)
        # Stepped sandstone shrine.
        for i in range(12):
            self.block('altar stair',(0,22+i+.5,(i+1)*.1),(12,1,(i+1)*.2),(.74-i*.006,.56-i*.004,.35))
            self.block('step nose',(0,22+i+.08,(i+1)*.2+.015),(12,.12,.06),(.84,.66,.41))
        self.block('shrine platform',(0,39,1.2),(20,10,2.4),(.65,.46,.28))
        for side in (-1,1):
            for j in range(4):
                x=side*7;y=32+j*3
                height=[6.8,5.1,6.1,3.8][j]
                self.block('pillar foot',(x,y,2.65),(2.1,2.1,.5),(.63,.45,.27))
                p=self.block('eroded pillar',(x,y,2.9),(1.55,1.4,height),(.72,.53,.33),stone=True);p.setH(j*17+5)
                self.block('broken capital',(x,y,height+3),(2,1.7,.65),(.76,.57,.36))
                self.obstacles.append((x-1,x+1,y-1,y+1,height+3.5))
                z=5.0+j*.15
                r=self.line('luminous glyph',[(x,y-.78,z),(x-.25,y-.78,z+.35),(x,y-.78,z+.7),(x+.25,y-.78,z+.35),(x,y-.78,z),(x,y-.78,z-1),(x-.33,y-.78,z-1.4)],thick=3)
                self.runes.append(r)
            beam=self.block('broken entablature',(side*6.5,39.5,9),(3,9,.75),(.72,.52,.30));beam.setP(side*3)
        self.offer=self.block('offering stone',(0,39,3.0),(3,1.8,1.2),(.64,.47,.30))
        self.block('offering slab',(0,39,3.68),(3.6,2.1,.25),(.83,.64,.39))
        self.obstacles.append((-1.8,1.8,38,40,3.9))
        model_path=ROOT/'assets'/'sandstone_shrine.bam'
        if model_path.exists():
            for name in ['altar stair','step nose','shrine platform','pillar foot','eroded pillar','broken capital','broken entablature','offering stone','offering slab']:
                for obj in list(self.render.findAllMatches('**/'+name)):obj.removeNode()
            model=self.loader.loadModel(Filename.fromOsSpecific(str(model_path)));model.reparentTo(self.render)
        self.jadelight=self.block('jade relic',(26,18,.35),(.55,.55,.8),(.30,.86,.76),stone=True);self.jadelight.setLightOff()
        self.altarjade=self.block('offered jade',(0,39,3.98),(.45,.45,.55),(.45,.94,.8),stone=True);self.altarjade.setLightOff();self.altarjade.hide()
        for i,(x,y) in enumerate([(-5,-10),(8,-4),(-7,17)]):
            cache=self.render.attachNewNode('material cache');self.cache_nodes['cache'+str(i)]=cache
            for j in range(4):
                self.block('material bundle',(x+(j%2)*.5,y+(j//2)*.4,.18),(1,.36,.36),(.42,.29,.17),parent=cache)
        # Campfire is the only place where time and economy advance.
        self.block('campfire base',(0,2,0),(1.4,1.4,.25),(.28,.24,.20),stone=True)
        self.flame=self.block('campfire flame',(0,2,.2),(.5,.5,1.1),(1,.65,.18),stone=True);self.flame.setLightOff()
        for x,y,c in [(-2,3,(.56,.41,.24)),(-14,-2,(.52,.54,.28)),(-9,2,(.44,.33,.23)),(10,7,(.61,.51,.32))]:
            npc,parts=self.person(c);npc.setPos(x,y,0);npc.setH(rng.uniform(0,360));self.npcs.append((npc,parts))
        self.player,self.parts=self.person((.65,.25,.11));self.player.setPos(0,-14,0)
        self.shadow=self.render.attachNewNode('soft character shadow')
        for i in range(7):
            o=self.round.copyTo(self.shadow);radius=1.2-i*.12;o.setScale(radius,radius*.68,.003);o.setZ(.001*i)
            o.setColor(.16,.13,.10,.035);o.setTransparency(TransparencyAttrib.MAlpha);o.setLightOff();o.setDepthWrite(False)
        self.targets={
          'elder':((-2,3,0),'长者','与长者交谈'), 'rest':((0,2,0),'营火','休整并结算一天'),
          'canal':((-8,-7,0),'水渠','疏通水渠'), 'farm':((-14,-2,0),'稻田','增加 1 名农民'),
          'workshop':((-9,2,0),'工坊','增加 1 名手工者'), 'dam':((18,14,0),'堤坝','投入 10 材料修堤'),
          'jade':((26,18,0),'河滩','拾取玉器'), 'altar':((0,36.7,2.4),'祭坛','整修 / 献玉祭祀'),
          'cache0':((-5,-10,0),'材料','拾取材料 +4'), 'cache1':((8,-4,0),'材料','拾取材料 +4'), 'cache2':((-7,17,0),'材料','拾取材料 +4')}
        for key,(pos,name,verb) in self.targets.items():
            tn=TextNode(key);tn.setFont(self.font);tn.setText(name);tn.setAlign(TextNode.ACenter);tn.setTextColor(1,.91,.68,1)
            np=self.render.attachNewNode(tn);np.setPos(pos[0],pos[1],pos[2]+2.7);np.setScale(.32);np.setBillboardPointEye();np.setLightOff();self.markers[key]=np
        self.dust=[]
        for i in range(70):
            p=self.block('dust',(rng.uniform(-27,27),rng.uniform(-17,45),rng.uniform(.5,10)),(.035,.035,.035),(1,.83,.49));p.setLightOff();self.dust.append(p)
        self.rain=self.render.attachNewNode('rainfall')
        for i in range(100):
            x=rng.uniform(-28,28);y=rng.uniform(-20,45);z=rng.uniform(2,12)
            self.line('rain',[(x,y,z),(x+.08,y,z-.55)],(.74,.80,.76,.55),1,self.rain)
        self.refresh()

    def house(self,x,y):
        self.block('sandstone home',(x,y,1.5),(5,5,3),(.57,.40,.24))
        roof=self.block('roof',(x,y,3.15),(6,6,.4),(.36,.29,.20));roof.setR(4)
        self.block('door',(x,y-2.52,1.1),(1.3,.1,2.2),(.19,.17,.13))
        for dx in (-2,2):self.block('awning post',(x+dx,y-4,1.3),(.16,.16,2.6),(.31,.25,.18))
        self.block('awning',(x,y-3.5,2.7),(5,2.5,.12),(.76,.65,.41))
        self.obstacles.append((x-2.7,x+2.7,y-2.7,y+2.7,3.6))

    def person(self,color):
        root=self.render.attachNewNode('villager');parts={}
        parts['robe']=self.block('woven robe',(0,0,.18),(.78,.62,1.23),color,parent=root,stone=True)
        parts['head']=self.block('hood',(0,0,1.40),(.49,.46,.49),(.85,.72,.48),parent=root,stone=True)
        self.block('face',(0,.22,1.61),(.30,.035,.21),(.22,.19,.14),parent=root)
        for x in (-.08,.08):
            eye=self.block('eye',(x,.246,1.65),(.04,.025,.035),(1,.89,.6),parent=root);eye.setLightOff()
        for side in (-1,1):
            parts['arm'+str(side)]=self.block('sleeve',(side*.40,0,.92),(.19,.24,.65),color,parent=root)
            parts['foot'+str(side)]=self.block('foot',(side*.2,.05,.12),(.18,.32,.23),(.24,.19,.13),parent=root)
        scarf=mesh('ceremonial scarf',[(-.15,-.26,1.25),(.15,-.26,1.25),(.16,-.9,.96),(-.16,-.9,.96),(.12,-1.5,.78),(-.12,-1.5,.78)],[(0,1,2,3),(3,2,4,5)])
        scarf.reparentTo(root);scarf.setColor(.92,.80,.51,1);scarf.setTwoSided(True);parts['scarf']=scarf
        return root,parts

    def ui(self):
        self.top=DirectFrame(frameColor=(.14,.12,.09,.78),frameSize=(-1.6,1.6,.78,1))
        self.title=OnscreenText(text='沙光 · 良渚',font=self.font,pos=(-1.49,.90),align=TextNode.ALeft,scale=.052,fg=(1,.88,.61,1))
        self.stats=OnscreenText(text='',font=self.font,pos=(1.48,.90),align=TextNode.ARight,scale=.035,fg=(.96,.92,.79,1),mayChange=True)
        self.goal=OnscreenText(text='',font=self.font,pos=(-1.49,.805),align=TextNode.ALeft,scale=.035,fg=(1,.91,.70,1),mayChange=True)
        self.controls_text=OnscreenText(text='WASD 移动   Shift 奔跑   空格 跳跃   右键拖动 / 方向键 环视   滚轮 缩放\nE 互动   F5 保存   F9 读取   F12 截图   R 重开   Esc 暂停',font=self.font,pos=(-1.49,-.91),align=TextNode.ALeft,scale=.026,fg=(.95,.89,.73,1))
        self.prompt=OnscreenText(text='',font=self.font,pos=(0,-.64),scale=.047,fg=(1,.95,.77,1),mayChange=True)
        self.message=OnscreenText(text=self.toast,font=self.font,pos=(0,-.77),scale=.033,wordwrap=68,fg=(1,.89,.62,1),mayChange=True)
        self.economy=OnscreenText(text='',font=self.font,pos=(1.48,.735),scale=.028,align=TextNode.ARight,fg=(.96,.90,.73,1),mayChange=True)
        self.overlay=DirectFrame(frameColor=(.08,.09,.08,.90),frameSize=(-.85,.85,-.58,.58));self.overlay.hide()
        self.overlaytext=OnscreenText(parent=self.overlay,text='',font=self.font,pos=(0,.34),scale=.065,fg=(1,.87,.59,1),mayChange=True)
        self.overlaydetail=OnscreenText(parent=self.overlay,text='',font=self.font,pos=(0,.13),scale=.036,wordwrap=36,fg=(.92,.89,.78,1),mayChange=True)
        self.resume_button=DirectButton(parent=self.overlay,text='继续探索',text_font=self.font,scale=.06,pos=(-.38,0,-.38),command=self.pause,frameColor=(.28,.26,.20,1))
        DirectButton(parent=self.overlay,text='重新开始',text_font=self.font,scale=.06,pos=(0,0,-.38),command=self.reset,frameColor=(.28,.26,.20,1))
        DirectButton(parent=self.overlay,text='退出',text_font=self.font,scale=.06,pos=(.42,0,-.38),command=self.userExit,frameColor=(.28,.26,.20,1))
        self.sync_ui()

    def controls(self):
        for key in ['w','a','s','d','shift','arrow_left','arrow_right','arrow_up','arrow_down','mouse3']:
            self.accept(key,self.setkey,[key,True]);self.accept(key+'-up',self.setkey,[key,False])
        self.accept('space',self.jump);self.accept('e',self.interact);self.accept('escape',self.pause)
        self.accept('wheel_up',self.zoom,[-.6]);self.accept('wheel_down',self.zoom,[.6])
        self.accept('f5',self.save);self.accept('f9',self.load);self.accept('r',self.reset);self.accept('f12',self.screenshot)

    def setkey(self,key,value):self.keys[key]=value
    def zoom(self,delta):self.distance=max(3.3,min(11,self.distance+delta))
    def jump(self):
        if self.ground and not self.dialog:self.vertical=5.7;self.ground=False

    def height(self,x,y):
        if abs(x)<=6 and 22<=y<34:return .2*(int(y-22)+1)
        if abs(x)<=10 and 34<=y<=44:return 2.4
        if 19<x<30 and 13.5<y<16.5:return .40
        return .08

    def legal(self,x,y,z):
        if not (-29<x<30 and -22<y<46):return False
        # River can only be crossed over the bridge.
        if 21.5<x<28.5 and not 13.4<y<16.6:
            if not (x>24 and 16.5<y<21):return False
        for lo,hi,bottom,top,h in self.obstacles:
            if lo-.26<x<hi+.26 and bottom-.26<y<top+.26 and z<h:return False
        return self.height(x,y)-z<.4

    def interact(self):
        if self.dialog or not self.near:return
        self.toast=self.state.act(self.near);self.toasting=7
        self.refresh();self.sync_ui();self.save(quiet=True)
        if self.state.won:
            self.ceremony=7;self.dialog=True;self.keys.clear();self.altarjade.show()
            self.toast='玉光苏醒，风穿过断裂的柱廊。';self.toasting=7
        elif self.state.population<=0:self.end_screen()

    def refresh(self):
        for n,visible in [(self.water,self.state.canal),(self.canalwater,self.state.canal),(self.crops,self.state.canal),(self.blockage,not self.state.canal),(self.damroot,self.state.dam),(self.flood,self.state.day in (4,5) and not self.state.dam),(self.jadelight,self.state.day>=4 and not self.state.jade and not self.state.won)]:
            n.show() if visible else n.hide()
        for key,node in self.cache_nodes.items():node.hide() if key in self.state.caches else node.show()
        for r in self.runes:r.setColorScale(1,1,1,1) if self.state.shrine else r.setColorScale(.28,.25,.19,1)
        rainy=self.state.day in (3,4)
        self.rain.show() if rainy else self.rain.hide()
        self.altarjade.show() if self.state.won else self.altarjade.hide()
        self.fog.setColor(*((.57,.59,.56) if rainy else (.87,.73,.51)))
        self.setBackgroundColor(*((.57,.59,.56,1) if rainy else (.87,.73,.51,1)))
        self.sun.setColor((.56,.60,.60,1) if rainy else (1.15,.94,.64,1))

    def sync_ui(self):
        self.stats.setText(f'第 {self.state.day} 日    人口 {self.state.population}    粮食 {self.state.food}    材料 {self.state.material}    玉器 {int(self.state.jade)}')
        self.goal.setText('当前目标  /  '+self.state.objective())
        grain,meals,made=self.state.forecast()
        self.economy.setText(f'农民 {self.state.farmers} · 手工者 {self.state.population-self.state.farmers}   下次休整：粮食 {grain-meals:+d} / 材料 +{made}')

    def pause(self):
        if self.state.won or self.state.population<=0:return
        self.dialog=not self.dialog;self.keys.clear();self.last_mouse=None
        if self.dialog:
            self.overlaytext.setText('暂歇');self.overlaydetail.setText('疏通水渠，让村民开始生产。\n在营火推进时间，准备第 4 日的洪水。\n雨后拾玉，携 10 粮食登台完成祭祀。')
            self.resume_button.show();self.overlay.show()
        else:self.overlay.hide()

    def end_screen(self):
        self.dialog=True;self.keys.clear();self.overlay.show();self.resume_button.hide()
        self.overlaytext.setText('礼成 · 玉光苏醒' if self.state.won else '聚落沉寂')
        self.overlaydetail.setText(f'走过 {self.state.day} 日，守护 {self.state.population} 位村民。\n粮食剩余 {self.state.food}，材料剩余 {self.state.material}。\n'+('堤坝守住了稻田。' if self.state.dam else '聚落承受了洪水的考验。'))

    def reset(self):
        self.state=Village();self.ceremony=0;self.vertical=0;self.dialog=False;self.overlay.hide();self.player.setPos(0,-14,.08);self.yaw=0;self.pitch=18;self.keys.clear()
        self.toast='新的旅程开始。前往营火，与长者交谈。';self.toasting=8;self.refresh();self.sync_ui();self.save(quiet=True)

    def save(self,quiet=False):
        path=SAVE/'save.json';data={'version':1,'village':asdict(self.state),'position':list(self.player.getPos()),'yaw':self.yaw}
        temp=path.with_suffix('.tmp');temp.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8');temp.replace(path)
        if not quiet:self.toast='已保存旅程。按 F9 可继续。';self.toasting=4

    def load(self):
        try:
            data=json.loads((SAVE/'save.json').read_text(encoding='utf8'))
            if data['version']!=1:raise ValueError('version')
            self.state=Village(**data['village']);self.player.setPos(*data['position']);self.yaw=data['yaw']
            self.dialog=False;self.overlay.hide();self.refresh();self.sync_ui();self.toast='已恢复上次保存的旅程。';self.toasting=5
            if self.state.won or not self.state.population:self.end_screen()
        except (OSError,ValueError,TypeError,KeyError):self.toast='尚无可用存档。可以直接开始新的旅程。';self.toasting=5

    def screenshot(self):
        path=SAVE/f'Sandlight_{int(time.time())}.png';self.win.saveScreenshot(Filename.fromOsSpecific(str(path)))
        self.toast='截图已保存到 '+str(SAVE);self.toasting=5

    def update(self,task):
        dt=min(globalClock.getDt(),.045);self.t+=dt
        if self.ceremony>0:
            self.ceremony-=dt;self.yaw+=dt*3;self.pitch=12
            for r in self.runes:r.setColorScale(1.6+math.sin(self.t*3)*.4,1.4,1,1)
            if self.ceremony<=0:self.end_screen()
        if not self.dialog:
            self.yaw+=(int(self.keys.get('arrow_left',False))-int(self.keys.get('arrow_right',False)))*85*dt
            self.pitch+=(int(self.keys.get('arrow_up',False))-int(self.keys.get('arrow_down',False)))*40*dt
            if self.mouseWatcherNode.hasMouse():
                mouse=self.mouseWatcherNode.getMouse();point=(mouse.x,mouse.y)
                if self.keys.get('mouse3') and self.last_mouse:
                    self.yaw-=(point[0]-self.last_mouse[0])*100;self.pitch-=(point[1]-self.last_mouse[1])*70
                self.last_mouse=point
            self.pitch=max(-4,min(48,self.pitch))
            f=int(self.keys.get('w',False))-int(self.keys.get('s',False));r=int(self.keys.get('d',False))-int(self.keys.get('a',False))
            angle=math.radians(self.yaw);forward=Vec3(-math.sin(angle),math.cos(angle),0);right=Vec3(math.cos(angle),math.sin(angle),0)
            direction=forward*f+right*r;moving=direction.length()>.01
            pos=self.player.getPos()
            if moving:
                direction.normalize();speed=7 if self.keys.get('shift') else 4.1;step=direction*dt*speed
                if self.legal(pos.x+step.x,pos.y,pos.z):pos.x+=step.x
                if self.legal(pos.x,pos.y+step.y,pos.z):pos.y+=step.y
                self.player.setH(math.degrees(math.atan2(-direction.x,direction.y)))
            floor=self.height(pos.x,pos.y)
            self.vertical-=15*dt;pos.z+=self.vertical*dt
            if pos.z<=floor:pos.z=floor;self.vertical=0;self.ground=True
            self.player.setPos(pos)
            for side in (-1,1):
                self.parts['arm'+str(side)].setP(math.sin(self.t*11)*side*24 if moving else math.sin(self.t*2)*3)
                self.parts['foot'+str(side)].setY(.05+(math.sin(self.t*11)*side*.16 if moving else 0))
            self.parts['scarf'].setP(math.sin(self.t*4)*6+(12 if moving else 0))
        pos=self.player.getPos();self.shadow.setPos(pos.x+.25,pos.y-.20,self.height(pos.x,pos.y)+.025)
        angle=math.radians(self.yaw);elev=math.radians(self.pitch)
        target=pos+Vec3(0,0,1.35)
        offset=Vec3(math.sin(angle)*self.distance*math.cos(elev),-math.cos(angle)*self.distance*math.cos(elev),math.sin(elev)*self.distance)
        desired=target+offset
        # Sample the camera boom against buildings/pillars to avoid shooting through them.
        for i in range(1,21):
            probe=target+offset*(i/20)
            if any(lo-.2<probe.x<hi+.2 and b-.2<probe.y<t+.2 and probe.z<h+.3 for lo,hi,b,t,h in self.obstacles):
                desired=target+offset*max(.17,(i-2)/20);break
        desired.z=max(desired.z,self.height(desired.x,desired.y)+.35)
        self.camera.setPos(desired);self.camera.lookAt(target)
        nearest=None;dist=2.6
        for key,(xyz,name,verb) in self.targets.items():
            p=Vec3(*xyz);d=(pos-p).length()
            # 滞回：已显示的到 24 米才隐藏，未显示的 21.5 米才显示——避免边界抖动闪烁
            mk=self.markers[key]
            was_shown = not mk.isHidden()
            visible = (d<24) if was_shown else (d<21.5)
            if key.startswith('cache') and key in self.state.caches:visible=False
            mk.show() if visible else mk.hide()
            if d<dist and visible:nearest=key;dist=d
        self.near=nearest
        # 只有文本真的变化才 setText——避免每帧重建几何导致闪烁
        _ptxt='[ E ]  '+self.targets[nearest][2] if nearest and not self.dialog else ''
        if getattr(self,'_last_prompt',None)!=_ptxt:
            self.prompt.setText(_ptxt);self._last_prompt=_ptxt
        self.toasting-=dt
        _mtxt=self.toast if self.toasting>0 else ''
        if getattr(self,'_last_message',None)!=_mtxt:
            self.message.setText(_mtxt);self._last_message=_mtxt
        self.flame.setScale(.5+math.sin(self.t*7)*.06,.5,1+math.sin(self.t*5)*.15)
        for j,p in enumerate(self.dust):p.setX(p.getX()+dt*.17);p.setZ(p.getZ()+math.sin(self.t+j)*dt*.05)
        for j,(npc,parts) in enumerate(self.npcs):parts['arm1'].setP(math.sin(self.t*2+j)*15)
        self.jadelight.setH(self.t*20)
        self.rain.setZ(-(self.t*6)%5-2)
        return task.cont

    def smoke(self,task):
        # Exercises the same nearby-interaction path used by the keyboard.
        results=[]
        for key in ['elder','canal','cache0','cache1','cache2','dam','rest','rest','rest','rest','jade','altar','altar']:
            self.player.setPos(*self.targets[key][0]);self.near=key;self.interact();results.append({'action':key,'state':asdict(self.state),'message':self.toast})
        assert self.state.won and self.state.population==6
        assert self.state.food==16 and self.state.material==10
        # Check that every interaction can be reached by walking the real collision map.
        from collections import deque
        start=(0,-14);visited={start};q=deque([start])
        while q:
            x,y=q.popleft();z=self.height(x,y)
            for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
                n=(x+dx,y+dy)
                if n not in visited and self.legal(n[0],n[1],z):visited.add(n);q.append(n)
        for key,(xyz,name,verb) in self.targets.items():
            assert any((x-xyz[0])**2+(y-xyz[1])**2+(self.height(x,y)-xyz[2])**2<2.6**2 for x,y in visited),key
        report={'result':'PASS','actions':results,'walkable_cells':len(visited),'all_targets_reachable':True,'camera':'third-person','renderer':self.win.getGsg().getDriverRenderer()}
        (SAVE/'smoke_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
        self.reset();self.state.greeted=True;self.state.canal=True;self.refresh();self.sync_ui()
        self.player.setPos(0,15,.08);self.yaw=0;self.pitch=10;self.distance=7.3
        self.taskMgr.doMethodLater(1.5,self.capture_test,'capture-test')
        return task.done

    def capture_test(self,task):
        self.win.saveScreenshot(Filename.fromOsSpecific(str(SAVE/'smoke_shrine.png')))
        self.player.setPos(-5,-11,.08);self.yaw=20;self.pitch=19
        self.taskMgr.doMethodLater(1,self.capture_second,'capture-second')
        return task.done

    def capture_second(self,task):
        self.win.saveScreenshot(Filename.fromOsSpecific(str(SAVE/'smoke_village.png')))
        self.userExit();return task.done

if __name__=='__main__':
    try:Demo().run()
    except Exception:
        import traceback
        (SAVE/'error.log').write_text(traceback.format_exc(),encoding='utf8')
        raise
