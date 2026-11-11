#!/usr/bin/env python3
"""Refresh GitHub profile panels and embed them as PNGs into the SVG."""
import base64, io, os, urllib.request
import xml.etree.ElementTree as ET
import cairosvg
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
SVG=ROOT/'matrix-github-profile.svg'
USER='iliyahaddad'
URLS={
 'gitshine': f'https://gitshine.com/badges/{USER}',
 'stats': f'https://github-readme-stats.vercel.app/api?username={USER}&show_icons=true&hide_border=true&rank_icon=github',
 'langs': f'https://github-readme-stats.vercel.app/api/top-langs/?username={USER}&layout=compact&hide_border=true',
 'stars': f'https://img.shields.io/github/stars/{USER}?label=Stars&style=social',
 'followers': f'https://img.shields.io/github/followers/{USER}?label=Followers&style=social',
 'views': f'https://komarev.com/ghpvc/?username={USER}',
 'streak': f'https://github-readme-streak-stats.herokuapp.com/?user={USER}&theme=meta-light',
}
ET.register_namespace('', 'http://www.w3.org/2000/svg')
S='{http://www.w3.org/2000/svg}'

def fetch_png(url):
    req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 (GitHub profile SVG updater)'})
    with urllib.request.urlopen(req,timeout=45) as r: data=r.read()
    if data.startswith(b'\x89PNG\r\n\x1a\n'): return data
    # Convert remote SVG badges/cards to PNG so GitHub can render them as embedded images.
    return cairosvg.svg2png(bytestring=data,output_width=None)

def img(parent, key, x,y,w,h, assets):
    data=assets[key]
    el=ET.SubElement(parent,S+'image',{'x':str(x),'y':str(y),'width':str(w),'height':str(h),'preserveAspectRatio':'xMidYMid meet','href':'data:image/png;base64,'+base64.b64encode(data).decode('ascii')})
    return el

tree=ET.parse(SVG); root=tree.getroot()
nested=next(e for e in root.iter(S+'svg') if e is not root and e.get('viewBox')=='40 262 1520 760')
groups={g.get('clip-path'):g for g in nested if g.tag==S+'g' and g.get('clip-path','').startswith('url(#win')}
assets={k:fetch_png(v) for k,v in URLS.items()}
# Explorer: GitShine's own badge image.
g=groups['url(#win2)']; g.clear(); g.set('clip-path','url(#win2)')
img(g,'gitshine',880,315,630,285,assets)
# Programming panel: GitHub stats and compact language chart side-by-side.
g=groups['url(#win3)']; g.clear(); g.set('clip-path','url(#win3)')
img(g,'stats',55,715,365,260,assets); img(g,'langs',430,715,355,260,assets)
# Activity panel: social counters across the top, contribution streak below.
g=groups['url(#win4)']; g.clear(); g.set('clip-path','url(#win4)')
img(g,'stars',865,715,205,55,assets); img(g,'followers',1080,715,225,55,assets); img(g,'views',1320,715,200,55,assets)
img(g,'streak',860,785,675,210,assets)
tree.write(SVG,encoding='utf-8',xml_declaration=True)
print('Updated',SVG)
