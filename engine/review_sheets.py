"""Generate full-duration and frame-by-frame transition contact sheets for human visual review."""
from __future__ import annotations
import math
from pathlib import Path
import cv2
from PIL import Image, ImageDraw

WHITE=(255,255,255)


def make_sheet(video: Path, destination: Path, frames: list[int], columns: int, tile_w: int, tile_h: int) -> None:
    cap=cv2.VideoCapture(str(video))
    if not cap.isOpened(): raise RuntimeError(f"Cannot open review video: {video}")
    tiles=[]
    for n in frames:
        cap.set(cv2.CAP_PROP_POS_FRAMES,n); ok,bgr=cap.read()
        if not ok: continue
        rgb=cv2.cvtColor(bgr,cv2.COLOR_BGR2RGB)
        im=Image.fromarray(rgb); im.thumbnail((tile_w-12,tile_h-28),Image.Resampling.LANCZOS)
        tile=Image.new('RGB',(tile_w,tile_h),(13,18,29))
        tile.paste(im,((tile_w-im.width)//2,4))
        ImageDraw.Draw(tile).text((5,tile_h-20),f'{n/30:.2f}s · f{n}',fill=WHITE)
        tiles.append(tile)
    cap.release()
    rows=math.ceil(len(tiles)/columns)
    gutter=8
    sheet=Image.new('RGB',(columns*tile_w+(columns+1)*gutter,rows*tile_h+(rows+1)*gutter),(4,8,15))
    for i,tile in enumerate(tiles): sheet.paste(tile,(gutter+(i%columns)*tile_w,gutter+(i//columns)*tile_h))
    destination.parent.mkdir(parents=True,exist_ok=True)
    sheet.save(destination,optimize=True)


def create_review_sheets(video: Path, root: Path, cuts: list[int], suffix: str = "v2") -> tuple[Path,Path]:
    timeline=root/f'planche_temps_{suffix}.png'
    transition=root/f'transitions_{suffix}.png'
    make_sheet(video,timeline,list(range(0,900,15)),6,120,216)
    all_transition=[n for cut in cuts for n in range(cut-4,cut+8)]
    make_sheet(video,transition,all_transition,6,132,239)
    return timeline,transition
