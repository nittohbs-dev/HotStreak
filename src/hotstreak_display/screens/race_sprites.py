"""採用済みのキャラクター画像を使うレース用スプライト。"""
from functools import lru_cache
from pathlib import Path
import pygame

ATLAS=Path(__file__).resolve().parents[3]/'assets/images/characters/racers-approved.png'

@lru_cache(maxsize=1)
def frames():
    atlas=pygame.image.load(str(ATLAS))
    source=pygame.Surface(atlas.get_size(),pygame.SRCALPHA)
    source.blit(atlas,(0,0))
    w,h=source.get_size()
    result={}
    for col,color in enumerate(('orange','blue','yellow','salmon')):
        pair=[]
        for row in range(2):
            x0,x1=round(col*w/4),round((col+1)*w/4)
            y0,y1=(0,round(h*.522)) if row==0 else (round(h*.522),h)
            cell=source.subsurface((x0,y0,x1-x0,y1-y0)).copy()
            bounds=cell.get_bounding_rect(min_alpha=20)
            if not bounds.width or not bounds.height:
                raise ValueError('Empty racer sprite')
            cell=cell.subsurface(bounds).copy()
            # The second row faces left; normalize both animation frames to right.
            if row: cell=pygame.transform.flip(cell,True,False)
            scale=min(90/cell.get_width(),96/cell.get_height())
            cell=pygame.transform.smoothscale(cell,(round(cell.get_width()*scale),round(cell.get_height()*scale)))
            pair.append(cell)
        result[color]=pair
    return result


def sprite(color,frame=0,pose='idle',facing=1,tilt=0):
    phase=(frame//2)%2 if pose=='run' else 0
    image=frames()[color][phase]
    canvas=pygame.Surface((100,102),pygame.SRCALPHA)
    bob=2 if pose=='run' and phase else 0
    canvas.blit(image,image.get_rect(midbottom=(50,100-bob)))
    if facing<0: canvas=pygame.transform.flip(canvas,True,False)
    if pose=='fallen': canvas=pygame.transform.rotate(canvas,90*facing)
    elif tilt: canvas=pygame.transform.rotate(canvas,tilt*facing)
    return canvas
