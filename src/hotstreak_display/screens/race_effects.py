"""ローカルモックのカード解決と効果確認操作。通信には依存しない。"""
import json
from pathlib import Path
import pygame

COLORS=('blue','orange','yellow','salmon')
NAMES=('ダングル','ゴブラー','マム','ハーレー')
CATALOG=Path(__file__).resolve().parents[3]/'data/cards/catalog.json'

class EffectsMixin:
    def set_state(self,state):
        super().set_state(state)
        self.lanes=list(range(4)); self.visual_lanes=list(range(4))
        self.previous_lanes=list(range(4))
        self.picker=False; self.selection=0; self.scenario_index=-1
        self.catalog=[c for c in json.loads(CATALOG.read_text(encoding='utf-8'))['cards'] if c['kind']=='race']
        self.pending=None; self.targets=[]; self.old_fallen=self.fallen[:]
        self.tie_ranks={}; self.manual=False

    def scenario(self):
        index=(self.scenario_index+1)%5
        self.set_state('running'); self.scenario_index=index; self.manual=True; self.picker=True
        setups=[('自由に効果確認',(4,6,7,4),[1,1,2,3],[False]*4),
                ('衝突・再転倒',(4,6,7,4),[1,1,2,3],[False,True,False,False]),
                ('転倒・逆向き',(4,6,7,4),[0,1,2,3],[True,False,True,False]),
                ('ゴール・コース外',(11,10,1,2),[0,1,2,3],[False]*4),
                ('全員カード',(10,10,9,9),[1,1,2,3],[False,True,False,True])]
        title,positions,lanes,fallen=setups[index]
        self.positions=positions; self.visual_positions=list(positions); self.previous=positions
        self.lanes=lanes; self.visual_lanes=lanes[:]; self.previous_lanes=lanes[:]
        self.fallen=fallen; self.old_fallen=fallen[:]
        if index==2: self.facing=[-1,1,-1,1]
        self.label=title+' / ← →でカード選択'

    def apply_card(self,card_id,effect=None):
        if self.moving or self.state=='finish': return False
        card=next(c for c in self.catalog if c['id']==card_id)
        color=card['color']; action=card['effect']; group=color=='green'
        targets=[i for i in range(4) if self.status[i]=='racing'] if group else [COLORS.index(color)]
        self.targets=targets; self.active=targets[0] if targets else 0
        self.old_fallen=self.fallen[:]; self.previous=self.positions; self.previous_lanes=self.lanes[:]
        self.card_id=card_id; self.effect=effect or card['label']
        pos=list(self.positions); lanes=self.lanes[:]; fallen=self.fallen[:]
        outcomes={}; hits=set(); paths={}
        self.action='recover' if action.startswith('recover') else action
        for i in targets:
            if self.status[i]!='racing': continue
            start=pos[i]; lane=lanes[i]; path=[]
            if action=='turn': self.facing[i]*=-1
            elif action=='fall':
                if fallen[i]: outcomes[i]='dq'
                else: fallen[i]=True
            else:
                if action.startswith('recover'):
                    fallen[i]=False; self.facing[i]=1
                if action=='star':
                    stars=[x for x in (0,5,8,12) if (x-start)*self.facing[i]>0]
                    dest=(min(stars) if self.facing[i]>0 else max(stars)) if stars else start
                    delta=dest-start
                else:
                    amount=int(action.rsplit('_',1)[1])*(-1 if '_minus_' in action else 1)
                    delta=amount*self.facing[i]
                if fallen[i] and delta: delta=1 if delta>0 else -1
                dest=start+delta
                if group: dest=min(11,dest)
                direction=1 if dest>start else -1
                for x in range(start+direction,dest+direction,direction) if dest!=start else []:
                    path.append((x,lane))
                    if x>=12:
                        outcomes[i]='goal'; dest=12; break
                    if x<self.removed:
                        outcomes[i]='dq'; dest=x; break
                pos[i]=dest
                if action.startswith('swerve') and i not in outcomes:
                    side=-1 if color in ('blue','yellow') else 1
                    lanes[i]+=side*self.facing[i]
                    path.append((dest,lanes[i]))
                    if not 0<=lanes[i]<4: outcomes[i]='dq'
                paths[i]=path
            # Green effects never collide; individual movement hits every stationary racer passed.
            if not group:
                for j in range(4):
                    if j!=i and self.status[j]=='racing' and (self.positions[j],self.lanes[j]) in path:
                        hits.add(j)
        for j in hits:
            if fallen[j]: outcomes[j]='dq'
            else: fallen[j]=True
        self.positions=tuple(pos); self.lanes=lanes
        self.pending=(fallen,outcomes,hits)
        self.index+=1; self.deck_index+=1; self.remaining=max(0,15-self.deck_index)
        self.state='running'; self.progress=0.; self.moving=True
        self.label='カードの効果を表示中'
        return True

    def update(self,dt):
        self.elapsed+=dt
        if not self.moving: return
        self.progress=min(1.,self.progress+dt/(1.8 if self.action=='shorten' else 1.15))
        t=self.progress*self.progress*(3-2*self.progress)
        if self.action=='recover': t=max(0,(self.progress-.45)/.55)
        # Swerve moves along the lane first, then across it.
        lateral=self.action.startswith('swerve')
        forward=min(1,t/.7) if lateral else t
        sideways=max(0,(t-.7)/.3) if lateral else t
        self.visual_positions=[a+(b-a)*forward for a,b in zip(self.previous,self.positions)]
        self.visual_lanes=[a+(b-a)*sideways for a,b in zip(self.previous_lanes,self.lanes)]
        if self.progress<1: return
        self.moving=False
        if self.action=='shorten':
            self.removed=min(12,self.removed+3)
            outcomes={i:'dq' for i,x in enumerate(self.positions) if x<self.removed and self.status[i]=='racing'}
            self.remaining=15; self.deck_index=0; self.effect='再シャッフル・3枚バーン済み'
        else:
            self.fallen,outcomes,hits=self.pending
            self.pending=None
            self.label='衝突！ 停止中のキャラが転倒' if hits else '次のEnter待ち'
        dqs=[i for i,k in outcomes.items() if k=='dq']
        if len(dqs)>1:
            lowest=max(i for i,v in enumerate(self.standings) if v is None)+1
            self.tie_ranks.update({i:lowest for i in dqs})
        for i,kind in outcomes.items(): self.place(i,kind)
        if self.finish_if_ready(): return
        if self.remaining==0:
            self.action='shorten'; self.progress=0.; self.moving=True
            self.previous=self.positions; self.previous_lanes=self.lanes[:]
            self.targets=[]; self.card_id='card_back'; self.effect='山札切れ / コース短縮'
            self.label='左から3マス短縮しています'

    def handle_event(self,event):
        if event.type==pygame.WINDOWFOCUSLOST: self.enter_held=False
        if event.type==pygame.KEYUP and event.key in (pygame.K_RETURN,pygame.K_KP_ENTER): self.enter_held=False
        if event.type!=pygame.KEYDOWN or getattr(event,'repeat',False): return
        if self.moving: return
        if event.key not in (pygame.K_RETURN,pygame.K_KP_ENTER): return
        if self.enter_held: return
        self.enter_held=True
        if self.state=='finish':
            self.set_state('start'); self.enter_held=True; return
        if self.index<len(self.samples):
            card_id,label,*_=self.samples[self.index]
            self.apply_card(card_id,label)
