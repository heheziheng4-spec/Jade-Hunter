from panda3d.core import loadPrcFileData
from demo_v22 import NaturalDemo
class PeopleDemo(NaturalDemo):
 def world(self):
  super().world()
  for side in ('L','R'):self.king.releaseJoint('modelRoot','upper_arm.'+side)
  self.arm_controls={}
  self.people23=[]
  for n in list(self.render.findAllMatches('**/villager')):
   if n==self.player:continue
   p=n.getPos(self.render)
   role='elder23' if abs(p.x+3)<1 and abs(p.y)<1 else 'farmer23' if p.y<12 else 'noble23' if p.y>65 else 'artisan23' if p.x<0 else 'villager23'
   for child in n.getChildren():child.hide()
   model=self.spawn_person(role,p.x,p.y,p.z,2.0)
   model.wrtReparentTo(n)
  for role,x,y,h in [('miner23',-72,84,2.1),('miner23',-64,87,2),('artisan23',-20,34,2),('noble23',23,83,2.2),('warrior23',-6,-24,2.4),('warrior23',6,-24,2.4),('warrior23',-115,53,2.4),('priest23',-4,83,2.3),('farmer23',18,-32,2),('farmer23',-18,-34,2),('villager23',63,80,2),('deer23',103,85,2.8),('deer23',108,88,2.3),('totem23',100,91,1.2),('totem23',-109,33,1.3)]:
   self.spawn_person(role,x,y,self.height(x,y),h)
  for old in list(self.render.findAllMatches('**/forest spruce')):
   p=old.getPos(self.render);scale=old.getSz();old.hide()
   self.builder.place('grove',p.x,p.y,self.height(p.x,p.y),scale*.65,0)
 def spawn_person(self,role,x,y,z,height):
  node=self.builder.asset(role,x,y,z,(1,1,1),-90);lo,hi=node.getTightBounds();s=height/(hi.z-lo.z);node.setScale(s)
  lo,hi=node.getTightBounds(self.render);node.setZ(node.getZ()+z-lo.z);self.people23.append((role,node));return node
if __name__=='__main__':
 loadPrcFileData('','window-title Sandlight 0.23 | Liangzhu People')
 PeopleDemo().run()
