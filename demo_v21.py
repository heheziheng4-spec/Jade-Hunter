import math,random
from panda3d.core import Filename,loadPrcFileData
from direct.actor.Actor import Actor
from demo_v20 import GroundedDemo,GroundedBuilder
from main import ROOT
from sky_temple import image_card
class JadeBuilder(GroundedBuilder):
 def asset(self,kind,x,y,z,scale,heading=0):
  if kind=='border19' and abs(x)<45:return super().asset('jadepost',x,y,z,(scale[2]/1.456,)*3,-90)
  return super().asset(kind,x,y,z,scale,heading)
 def place(self,kind,x,y,z,size,heading=0):
  if kind=='ruin':heading=-90
  return super().place(kind,x,y,z,size,heading)
class JadeDemo(GroundedDemo):
 world_builder=JadeBuilder
 def world(self):
  super().world();self.jade_progress=[0,0];self.pick_until=0;self.jade_nodes=[];self.king_anim=''
  for child in self.player.getChildren():child.hide()
  self.king=Actor(Filename.fromOsSpecific(str(ROOT/'assets/frontier/king_rig21.bam')));self.king.reparentTo(self.player)
  self.king.setScale(.85);self.king.loop('idle');self.king_anim='idle'
  self.camLens.setFar(600)
  rng=random.Random(2116)
  for i in range(24):
   a=i*math.tau/24;x=245*math.cos(a);y=35+260*math.sin(a)
   self.builder.asset('mount21a' if i%2 else 'mount21b',x,y,-8,(95,80,140+i%4*15),i*37)
  for i in range(32):
   a=i*math.tau/32;r=1.55;x=83*r*math.cos(a);y=35+89*r*math.sin(a)
   self.builder.asset('tall21',x,y,self.height(x,y)-.03,(7,7,9),i*43)
  for q,(cx,cy,kind) in enumerate([(-95,-43,'jade21'),(95,-43,'orbit21')]):
   z=self.height(cx,cy);self.builder.asset(kind,cx,cy,z,(7,7,7),90)
   self.add_target('jade_start'+str(q),(cx,cy-6,self.height(cx,cy-6)),['西荒野 · 玉心','东荒野 · 玉旋环'][q],'E 唤醒 / 完成共鸣')
   for j in range(6):
    a=-math.pi/2+j*math.tau/6;x=cx+11*math.cos(a);y=cy+11*math.sin(a);zz=self.height(x,y)
    self.add_target(f'jade_node{q}_{j}',(x,y,zz),f'玉光节点 {j+1}','E 拾取玉光')
    gem=self.builder.asset('jade21',x,y,zz+.9,(.45,)*3,0)
    halo=image_card(self,self.effects,'disc',2,2,True);halo.setPos(x,y,zz+1.3);halo.setBillboardPointEye();halo.setColorScale(.2,1,.65,.6)
    frame=self.line('jade frame',[(x-1,y,zz),(x-1,y,zz+2.4),(x+1,y,zz+2.4),(x+1,y,zz)],(.3,.9,.7,1),3)
    self.jade_nodes.append((q,j,gem,halo,frame,zz))
   for i in range(5):
    a=i*math.tau/5;x=cx+17*math.cos(a);y=cy+17*math.sin(a)
    self.builder.asset('rock21' if i%2 else 'raw20',x,y,self.height(x,y)-.1,(2+i*.3,)*3,i*50)
 def extra_save_data(self):return dict(super().extra_save_data(),jade_progress=getattr(self,'jade_progress',[0,0]))
 def restore_extra_data(self,data):
  super().restore_extra_data(data);v=data.get('jade_progress',[0,0]);self.jade_progress=[max(0,min(8,int(x))) for x in v] if isinstance(v,list) and len(v)==2 else [0,0]
 def interact(self):
  key=self.near or ''
  if self.dialog:return super().interact()
  if key.startswith('jade_start'):
   q=int(key[-1]);p=self.jade_progress[q]
   if p==0:self.jade_progress[q]=1;self.toast='追随亮起的玉光，依次点亮六座环形框架。'
   elif p==7:self.jade_progress[q]=8;self.state.jade=True;self.state.material+=3;self.toast='玉石共鸣完成，获得祭祀玉器和 3 材料。';self.light_pulse=1;self.cue('portal','玉石共鸣')
   else:self.toast='玉光已完成共鸣。' if p==8 else '沿外围寻找下一个亮起的框架。'
   self.toasting=5;return
  if key.startswith('jade_node'):
   q,j=map(int,key[9:].split('_'))
   if self.jade_progress[q]==j+1:
    self.jade_progress[q]+=1;self.pick_until=self.t+1.4;self.king.play('pickup');self.king_anim='pickup';self.light_pulse=.5;self.cue('portal','拾取玉光');self.toast='玉光已拾取。'+('返回玉石中心完成共鸣。' if j==5 else '追逐下一个发光节点。')
   else:self.toast='先唤醒中心玉石，再沿亮起的节点前进。'
   self.toasting=4;return
  self.pick_until=self.t+1.4;self.king.play('pickup');self.king_anim='pickup';return super().interact()
 def update(self,task):
  before=self.player.getPos();r=super().update(task)
  if hasattr(self,'king'):
   moving=(self.player.getPos()-before).length()>.001
   act='pickup' if self.t<self.pick_until else ('run' if self.keys.get('shift') else 'walk') if moving else 'idle'
   if act!=self.king_anim:self.king.loop(act);self.king_anim=act
   for q,j,g,h,f,z in self.jade_nodes:
    active=self.jade_progress[q]==j+1;done=self.jade_progress[q]>j+1
    g.setZ(z+1+.15*math.sin(self.t*2+j));g.setH(self.t*35);g.show() if active else g.hide();h.show() if active else h.hide();f.setColorScale((.5 if done else .16),1 if done or active else .3,.7,1)
  return r
if __name__=='__main__':
 loadPrcFileData('','window-title Sandlight 0.21 | Jade King')
 JadeDemo().run()

