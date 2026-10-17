#!/usr/bin/env python3
"""Render an offline comparison of work, authority and human reporting."""
from __future__ import annotations
import argparse
import base64
import html
import importlib.util
import json
import textwrap
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
_spec=importlib.util.spec_from_file_location('_org_record',Path(__file__).with_name('render_org_proposal.py'))
_base=importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_base)
INK='#191714';MUTED='#655F55';RULE='#D9D2C4';PAPER='#FFFDF9';ORANGE='#A84D24';TEAL='#08776E'
MODES={'human':'Human only','agent':'Agent only','hybrid':'Human + agent','unknown':'Split to confirm'}


def esc(value): return html.escape(str(value),quote=True)


def validate(data):
    errors=_base.validate(data)
    if not isinstance(data,dict):return errors
    people=data.get('people',[])
    ids={p.get('id') for p in people if isinstance(p,dict) and isinstance(p.get('id'),str)} if isinstance(people,list) else set()
    release=data.get('release')
    if not isinstance(release,dict):return errors+['release must be an object.']
    for field in ('rule_owner','maintainer'):
        if not isinstance(release.get(field),str) or release[field] not in ids:errors.append(f'release.{field} must reference a recorded human.')
    for field in ('eligible_label','checks_note'):
        if not isinstance(release.get(field),str) or not release[field].strip():errors.append(f'release.{field} must be non-empty text.')
    approvers=release.get('approvers')
    if not isinstance(approvers,list) or not approvers:errors.append('release.approvers must be a non-empty list of human IDs.')
    else:
        for ident in approvers:
            if not isinstance(ident,str) or ident not in ids:errors.append('Each release approver must reference a recorded human.')
        if all(isinstance(i,str) for i in approvers) and len(set(approvers))!=len(approvers):errors.append('Release approver IDs must be unique.')
    workflows=data.get('workflows',[])
    if not isinstance(workflows,list):errors.append('workflows must be a list.')
    else:
        for i,workflow in enumerate(workflows):
            if not isinstance(workflow,dict):errors.append(f'workflows[{i}] must be an object.');continue
            for field in ('title','note'):
                if not isinstance(workflow.get(field),str):errors.append(f'workflows[{i}].{field} must be text.')
            steps=workflow.get('steps')
            if not isinstance(steps,list) or not steps:errors.append(f'workflows[{i}].steps must be a non-empty list.');continue
            for j,step in enumerate(steps):
                if not isinstance(step,dict):errors.append(f'workflows[{i}].steps[{j}] must be an object.');continue
                if not isinstance(step.get('mode'),str) or step['mode'] not in MODES:errors.append('Workflow step mode is invalid.')
                for field in ('label','detail'):
                    if not isinstance(step.get(field),str):errors.append(f'Workflow step {field} must be text.')
                if 'handoff' in step and not isinstance(step['handoff'],str):errors.append('Workflow handoff must be text.')
                refs=step.get('person_ids')
                if not isinstance(refs,list) or any(not isinstance(ref,str) or ref not in ids for ref in refs):errors.append('Workflow step person_ids must reference recorded humans.')
    return errors


def wrap(value,width):
    result=[]
    for line in str(value).splitlines() or ['']:
        result.extend(textwrap.wrap(line,width=width,break_long_words=True,break_on_hyphens=False) or [''])
    return result


def text(value,x,y,width=50,size=18,colour=INK,weight=400,anchor='start',serif=False,lh=None):
    family='Georgia, serif' if serif else 'Avenir Next, Avenir, Arial, sans-serif'
    spans=''.join(f'<tspan x="{x}" dy="{0 if i==0 else (lh or size*1.35)}">{esc(line)}</tspan>' for i,line in enumerate(wrap(value,width)))
    return f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" font-weight="{weight}" text-anchor="{anchor}" fill="{colour}">{spans}</text>'


def icon(name,x,y,size=48,colour=ORANGE):
    svg=ET.fromstring((ROOT/'assets'/'sketchyicons'/f'{name}.svg').read_text())
    paths=''.join(f'<path d="{esc(child.attrib["d"])}"/>' for child in svg if child.tag.endswith('path'))
    return f'<g transform="translate({x} {y}) scale({size/24})" stroke="{colour}" stroke-width="1.65" stroke-linecap="round" stroke-linejoin="round" fill="none">{paths}</g>'


def person(x,y,r=40):
    return f'<circle cx="{x}" cy="{y}" r="{r}" fill="#F9E9DB" stroke="{ORANGE}" stroke-width="1.2"/>'+icon('user-round',x-r*.58,y-r*.62,r*1.16)


def bot(x,y,size=58):return icon('bot',x-size/2,y-size/2,size,TEAL)


def hybrid(x,y):
    return person(x-34,y,34)+text('+',x+12,y+7,size=26,colour=MUTED,anchor='middle')+bot(x+62,y,54)


def clipped(x,y,w,h,fill='#E6F2ED',stroke=TEAL,sw=1.5):
    cut=17
    return f'<path d="M{x+cut} {y} H{x+w-cut} L{x+w} {y+cut} V{y+h-cut} L{x+w-cut} {y+h} H{x+cut} L{x} {y+h-cut} V{y+cut} Z" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'


def arrow(path,prefix,colour=INK,width=1.7,dashed=False,dotted=False):
    marker='teal' if colour==TEAL else 'orange' if colour==ORANGE else 'ink'
    dash=' stroke-dasharray="2 6"' if dotted else ' stroke-dasharray="6 6"' if dashed else ''
    return f'<path d="{path}" fill="none" stroke="{colour}" stroke-width="{width}" stroke-linejoin="round" stroke-linecap="round" marker-end="url(#{prefix}-{marker})"{dash}/>'


def group(body,**attributes):
    attrs=' '.join(f'{key.replace("_","-")}="{esc(value)}"' for key,value in attributes.items())
    return f'<g {attrs}>{body}</g>'


def document(prefix,title,desc,height):
    notices=_base.provenance()+'\nStyle reference: Editorial Magazine Interface, StyleRef.io. https://styleref.io/share/cn3z318f-03d09f649c58. Adapted under the local STYLE.md contract.'
    defs=''.join(f'<marker id="{prefix}-{name}" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M1 1 L9 5 L1 9" fill="none" stroke="{colour}" stroke-width="1.5"/></marker>' for name,colour in [('ink',INK),('teal',TEAL),('orange',ORANGE)])
    return [f'<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="{height}" viewBox="0 0 1400 {height}" role="img" aria-labelledby="{prefix}-title {prefix}-desc"><title id="{prefix}-title">{esc(title)}</title><desc id="{prefix}-desc">{esc(desc)}</desc><metadata>{esc(notices)}</metadata><defs>{defs}</defs><rect width="1400" height="{height}" fill="{PAPER}"/><text x="1355" y="{height-8}" text-anchor="end" font-family="Avenir Next, Avenir, Arial, sans-serif" font-size="14" fill="{MUTED}">Prepared by Dr. Shiva Kakkar</text>']


def legend(y):
    return icon('user-round',44,y-22,31)+text('Human',86,y,width=10,size=18)+icon('bot',203,y-22,31,TEAL)+text('Agent work / role',245,y,size=18)+icon('user-round',462,y-22,31)+text('+',501,y,size=22,colour=MUTED)+icon('bot',524,y-22,31,TEAL)+text('Human + agent',568,y,size=18)+text('Agent counts are not specified.',940,y,size=18,colour=MUTED)


def checked(data):
    errors=validate(data)
    if errors:raise ValueError('\n'.join(errors))
    return {p['id']:p for p in data['people']}


def render_release_svg(data):
    people=checked(data);release=data['release'];names='One of: '+', '.join(people[i]['name'] for i in release['approvers']);p='release'
    parts=document(p,'How release authority would change','Matched preparation steps lead to current independent human approval or a proposed split. Only an eligible change with passing agreed checks may be released by an agent without per-release human approval. Other changes keep independent approval. Failed or uncertain checks and uncertain eligibility hold automatic release and route the issue separately.',1250)
    parts += [text('Release authority',45,55,size=35,serif=True),text('Agents would release eligible wording and styling changes after agreed checks pass.',45,91,width=115,size=20,colour=MUTED),f'<path d="M45 120 H1355 M470 145 V1085" stroke="{RULE}" fill="none"/>',text('Current',245,165,size=30,serif=True,anchor='middle'),text('Proposed',950,165,size=30,serif=True,anchor='middle')]
    current=[]
    current += [group(hybrid(228,235)+text('Prepare the change',245,307,size=22,anchor='middle')+text('Human + agent',245,337,size=18,colour=MUTED,anchor='middle'),data_step='prepare'),arrow('M245 359 V483',p)]
    current += [group(person(245,540,47)+text('Independent approval',245,617,width=27,size=26,anchor='middle',serif=True)+text(names,245,652,width=29,size=20,anchor='middle')+text('Someone other than the maker',245,725,width=28,size=18,colour=ORANGE,anchor='middle'),data_step='human-approval'),arrow('M245 752 V805',p)]
    current += [group(f'<rect x="104" y="822" width="282" height="107" fill="none" stroke="{MUTED}" stroke-dasharray="6 6"/>'+text('Release',245,862,size=26,serif=True,anchor='middle')+text('Executor not established',245,896,width=25,size=18,colour=MUTED,anchor='middle'),data_step='unknown-release-executor')]
    parts.append(group(''.join(current),data_view='current'))
    proposed=[]
    proposed += [group(hybrid(933,235)+text('Prepare the change',950,307,size=22,anchor='middle')+text('Human + agent',950,337,size=18,colour=MUTED,anchor='middle'),data_step='prepare'),arrow('M950 352 V376',p),f'<path d="M950 384 L1051 442 L950 500 L849 442 Z" fill="#F6F2EA" stroke="{MUTED}" stroke-width="1.2"/>',text('Eligible type?',950,449,width=18,size=20,anchor='middle')]
    eligible=arrow('M849 442 H662 V518',p,TEAL,2.5)+text('Within the boundary',685,485,width=24,size=18,colour=TEAL)+f'<path d="M662 528 L757 585 L662 642 L567 585 Z" fill="#EDF5F0" stroke="{TEAL}" stroke-width="1.3"/>'+text('Checks pass?',662,590,width=18,size=20,colour=TEAL,anchor='middle')+arrow('M662 642 V767',p,TEAL,3.2)+text('Yes',684,694,size=19,colour=TEAL)
    eligible += group(clipped(524,782,276,152,sw=2.4)+bot(662,825,63)+text('Agent release',662,893,width=20,size=30,colour=TEAL,serif=True,anchor='middle'),data_step='agent-release')
    eligible += text('No per-release human approval',662,974,width=28,size=21,colour=TEAL,weight=600,anchor='middle')+text(release['eligible_label'],662,1037,width=37,size=18,colour=MUTED,anchor='middle')
    proposed.append(group(eligible,data_route='eligible-pass'))
    outside=arrow('M1051 442 H1236 V483',p)+text('Other changes',1203,411,width=22,size=18,anchor='middle')
    outside += group(person(1236,540,47)+text('Independent',1236,614,width=20,size=24,serif=True,anchor='middle')+text('approval',1236,644,width=20,size=24,serif=True,anchor='middle')+text(names,1236,680,width=22,size=19,anchor='middle')+text('Someone other than the maker',1236,735,width=22,size=18,colour=ORANGE,anchor='middle'),data_step='human-approval')
    outside += arrow('M1236 786 V810',p)+group(f'<rect x="1115" y="822" width="241" height="107" fill="none" stroke="{MUTED}" stroke-dasharray="6 6"/>'+text('Release',1236,862,size=26,serif=True,anchor='middle')+text('Executor not established',1236,896,width=23,size=18,colour=MUTED,anchor='middle'),data_step='unknown-release-executor')
    proposed.append(group(outside,data_route='outside-boundary'))
    failed=f'<path d="M757 585 H950 M950 500 V585" fill="none" stroke="{INK}" stroke-width="1.7" stroke-dasharray="6 6"/>'+arrow('M950 585 V810',p,dashed=True)+text('Failed or',846,542,width=18,size=18,colour=MUTED,anchor='middle')+text('uncertain checks',846,567,width=18,size=18,colour=MUTED,anchor='middle')+text('Type uncertain',973,539,width=15,size=18,colour=MUTED)
    failed += group(f'<rect x="858" y="822" width="184" height="107" fill="#F6F2EA" stroke="{MUTED}"/>'+f'<path d="M939 840 V863 M958 840 V863" stroke="{MUTED}" stroke-width="5"/>'+text('Hold automatic',950,892,width=18,size=19,anchor='middle')+text('release',950,917,width=18,size=19,anchor='middle'),data_step='held-release')
    failed += text('Route by issue type',950,976,width=20,size=18,anchor='middle')+text('This is not permission to release.',950,1026,width=21,size=18,colour=MUTED,anchor='middle')
    proposed.append(group(failed,data_route='failed-or-uncertain'))
    parts.append(group(''.join(proposed),data_view='proposed'))
    parts += [f'<path d="M45 1111 H1355" stroke="{RULE}"/>',text('Before automatic release: '+release['checks_note'],45,1147,width=125,size=18,colour=MUTED),legend(1214),'</svg>']
    return ''.join(parts)


def render_division_svg(data):
    people=checked(data);r=data['release'];owner=people[r['rule_owner']]['name'];maintainer=people[r['maintainer']]['name'];p='division'
    routes=data['exception_routes'];height=max(1160,1020+((len(routes)+2)//3-1)*170)
    parts=document(p,'Who owns the rules, maintenance and release work','Proposed responsibilities distinguish human rule ownership, human maintenance accountability, agent execution within the boundary, and issue-specific recipients. Maintenance does not establish day-to-day agent supervision.',height)
    parts += [text('Division of release responsibilities',45,56,size=35,serif=True),text('Links show who sets rules, maintains automation and receives blocked release cases.',45,94,width=120,size=20,colour=MUTED),f'<path d="M45 125 H1355" stroke="{RULE}"/>']
    parts += [person(302,237,49),text(owner,302,320,width=30,size=31,serif=True,anchor='middle'),text('Owns the release rules',302,358,width=32,size=21,colour=ORANGE,anchor='middle'),text('Permitted changes and required checks',302,391,width=34,size=18,colour=MUTED,anchor='middle')]
    parts += [person(1098,237,49),text(maintainer,1098,320,width=30,size=31,serif=True,anchor='middle'),text('Maintains the automation',1098,358,width=32,size=21,colour=ORANGE,anchor='middle'),text('Checks, agent instructions and process',1098,391,width=35,size=18,colour=MUTED,anchor='middle')]
    parts += [group(arrow('M302 423 V513 H497',p,ORANGE,1.9)+text('sets the boundary',324,473,width=24,size=18,colour=ORANGE),data_relation='rule-ownership'),group(arrow('M1098 423 V513 H903',p,dotted=True)+text('maintains the system',918,473,width=24,size=18,colour=MUTED),data_relation='maintenance')]
    parts += [group(clipped(514,436,372,196)+bot(700,486,68)+text('Bounded release work',700,554,width=30,size=28,serif=True,colour=TEAL,anchor='middle')+text('Agent only at the release step',700,590,width=33,size=20,colour=TEAL,anchor='middle')+text('Agent count not specified',700,619,width=30,size=18,colour=MUTED,anchor='middle'),data_step='agent-release')]
    parts += [text('A blocked or uncertain release is routed by issue type.',700,681,width=69,size=21,anchor='middle'),arrow('M700 700 V743',p,dashed=True)]
    for i,route in enumerate(routes):
        col=i%3;row=i//3;x=230+col*470;y=825+row*170
        issue=route['issue'].replace('Blocked or uncertain release: ','')
        body=arrow(f'M700 743 H{x} V{y-44}',p,dashed=True)+person(x,y,35)+text(people[route['person_id']]['name'],x,y+64,width=30,size=25,serif=True,anchor='middle')+text(issue,x,y+96,width=31,size=18,colour=MUTED,anchor='middle')
        parts.append(group(body,data_relation='exception',data_person=route['person_id']))
    parts += [f'<path d="M45 {height-157} H105" stroke="{ORANGE}" stroke-width="2"/>',text('Sets permissions',119,height-151,size=17,colour=MUTED),f'<path d="M403 {height-157} H463" stroke="{INK}" stroke-width="2" stroke-dasharray="2 6"/>',text('Maintains automation',477,height-151,size=17,colour=MUTED),f'<path d="M835 {height-157} H895" stroke="{INK}" stroke-width="2" stroke-dasharray="6 6"/>',text('Routes blocked cases',909,height-151,size=17,colour=MUTED),text('Day-to-day supervision remains unresolved. Maintaining the automation does not establish that role.',45,height-101,width=117,size=18,colour=MUTED),f'<path d="M45 {height-66} H1355" stroke="{RULE}"/>',legend(height-26),'</svg>']
    return ''.join(parts)


def render_reporting_svg(data):
    people=checked(data);p='reporting';children={ident:[] for ident in people};roots=[]
    for person_data in data['people']:
        ident=person_data['id'];parent=person_data['reports_to']
        if parent is None:roots.append(ident)
        else:children[parent].append(ident)
    positions={};leaf=0;depth_max=0
    for root in roots:
        stack=[(root,0,False)]
        while stack:
            ident,depth,seen=stack.pop();depth_max=max(depth_max,depth)
            if children[ident] and not seen:
                stack.append((ident,depth,True));stack.extend((c,depth+1,False) for c in reversed(children[ident]))
            else:
                if children[ident]:x=sum(positions[c][0] for c in children[ident])/len(children[ident])
                else:x=leaf;leaf+=1
                positions[ident]=(x,depth)
        leaf+=.3
    span=max((v[0] for v in positions.values()),default=0);height=max(670,470+depth_max*235)
    points={ident:(700 if not span else 320+x/span*760,226+depth*235) for ident,(x,depth) in positions.items()}
    parts=document(p,'Current human reporting baseline','Confirmed human reporting only. Arrows point from a person to their manager. A reporting redesign has not been established.',height)
    parts += [text('Human reporting remains the current baseline',45,56,size=35,serif=True),text('The work-allocation proposal does not establish a change to these reporting relationships.',45,95,width=122,size=20,colour=MUTED),f'<path d="M45 126 H1355" stroke="{RULE}"/>']
    for person_data in data['people']:
        ident=person_data['id'];parent=person_data['reports_to'];x,y=points[ident]
        if parent is not None:
            px,py=points[parent];mid=(y-46+py+119)/2
            parts.append(group(arrow(f'M{x} {y-46} V{mid} H{px} V{py+119}',p),data_relation='reports-to',data_person=ident,data_manager=parent))
    for person_data in data['people']:
        x,y=points[person_data['id']]
        parts += [person(x,y,43),text(person_data['name'],x,y+76,width=25,size=28,serif=True,anchor='middle'),text(person_data['role'],x,y+107,width=33,size=18,colour=MUTED,anchor='middle')]
    parts += [f'<path d="M45 {height-73} H1355" stroke="{RULE}"/>',text('↑ Reports to the human at the arrowhead',45,height-34,size=18),text('Only recorded human reporting lines are shown.',640,height-34,width=78,size=18,colour=MUTED),'</svg>']
    return ''.join(parts)


def render_workflow_svg(data,index):
    people=checked(data)
    workflows=data.get('workflows',[])
    if not isinstance(index,int) or isinstance(index,bool) or index<0 or index>=len(workflows):raise ValueError('Workflow index is out of range.')
    workflow=workflows[index];steps=workflow['steps'];prefix=f'workflow-{index}';count=len(steps)
    cell=1260/count
    detail_width=max(17,int((cell-70)/9))
    detail_lines=max(len(wrap(step['detail'],detail_width)) for step in steps)
    label_lines=max(len(wrap(step['label'],max(16,int((cell-55)/10)))) for step in steps)
    detail_y=345+label_lines*27
    height=max(510,detail_y+detail_lines*25+88)
    parts=document(prefix,workflow['title'],workflow['note'],height)
    parts += [text(workflow['title'],45,52,width=87,size=31,serif=True),text(workflow['note'],45,90,width=119,size=18,colour=MUTED),f'<path d="M45 131 H1355" stroke="{RULE}"/>']
    for i,step in enumerate(steps):
        x=70+cell*(i+.5);y=215
        symbol=person(x,y,37) if step['mode']=='human' else bot(x,y,62) if step['mode']=='agent' else hybrid(x-12,y) if step['mode']=='hybrid' else text('?',x,y+11,size=42,colour=MUTED,anchor='middle')
        names=', '.join(people[ident]['name'] for ident in step['person_ids'])
        actor=(names+' + agent') if names and step['mode']=='hybrid' else names or MODES[step['mode']]
        mode_line=text(MODES[step['mode']],x,309,size=16,colour=ORANGE if step['mode']=='human' else MUTED,anchor='middle') if names else ''
        body=symbol+text(actor,x,282,width=max(18,int((cell-40)/12)),size=24,serif=True,anchor='middle')+mode_line+text(step['label'],x,350,width=max(16,int((cell-55)/10)),size=20,weight=500,anchor='middle')+text(step['detail'],x,detail_y+32,width=detail_width,size=18,colour=MUTED,anchor='middle')
        parts.append(group(body,data_step=f'workflow-{i}',data_mode=step['mode']))
        if i<count-1:
            parts.append(arrow(f'M{x+84} {y} H{70+cell*(i+1.5)-84}',prefix,INK))
            if step.get('handoff'):
                parts.append(text(step['handoff'],x+cell/2,y-22,width=max(16,int((cell-65)/10)),size=17,colour=MUTED,anchor='middle'))
    parts += [text('Agent symbols describe work; the number of agents is not specified.',45,height-44,width=95,size=18,colour=MUTED),'</svg>']
    return ''.join(parts)


def render_svg(data,view='release'):
    renderers={'release':render_release_svg,'division':render_division_svg,'reporting':render_reporting_svg}
    if view not in renderers:raise ValueError('Unknown diagram view.')
    return renderers[view](data)


def mode_icon(mode):
    body=icon('user-round',0,0,24) if mode=='human' else icon('bot',0,0,24,TEAL) if mode=='agent' else icon('user-round',0,0,24)+text('+',28,19,size=16,colour=MUTED)+icon('bot',41,0,24,TEAL) if mode=='hybrid' else text('?',6,20,size=22,colour=MUTED)
    width=66 if mode=='hybrid' else 25
    return f'<svg width="{width}" height="25" viewBox="0 0 {width} 25" aria-hidden="true">{body}</svg>'


def render(data):
    people=checked(data);svgs={key:render_svg(data,key) for key in ('release','division','reporting')}
    css=(ROOT/'assets'/'change-map.css').read_text();js=(ROOT/'assets'/'change-map.js').read_text()
    favicon='data:image/svg+xml;base64,'+base64.b64encode(('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">'+icon('bot',0,0,24,TEAL)+'</svg>').encode()).decode()
    controls=''.join(f'<button type="button" class="view-button" data-view-target="{key}" aria-controls="view-{key}" aria-pressed="{str(key=="release").lower()}">{label}</button>' for key,label in [('release','Release change'),('division','Division of work'),('reporting','Reporting')])
    workflow_charts=''.join(f'<div class="workflow-diagram diagram-scroll" tabindex="0">{render_workflow_svg(data,i)}</div>' for i in range(len(data.get('workflows',[]))))
    panels=''.join(f'<section id="view-{key}" class="view-panel" data-view-panel="{key}" aria-label="{label}"><h2 class="view-heading">{label}</h2><div class="diagram-scroll" tabindex="0">{svgs[key]}</div>{workflow_charts if key=="division" else ""}</section>' for key,label in [('release','Release change'),('division','Division of work'),('reporting','Reporting')])
    shape_key='<div class="shape-key" aria-label="Diagram shape key"><span><svg width="29" height="29" viewBox="0 0 29 29" aria-hidden="true"><path d="M14.5 2 L27 14.5 L14.5 27 L2 14.5 Z" fill="none" stroke="#655F55"/></svg>Diamond: a condition to establish</span><span><svg width="40" height="25" viewBox="0 0 40 25" aria-hidden="true"><rect x="2" y="2" width="36" height="21" fill="none" stroke="#655F55" stroke-dasharray="4 3"/></svg>Dashed enclosure: executor remains unknown</span></div>'
    allocations=[]
    for a in data['allocations']:
        allocations.append(f'<details class="allocation"><summary><span>{esc(a["activity"])}</span><span class="execution {a["mode"]}">{mode_icon(a["mode"])}{MODES[a["mode"]]}</span></summary><dl>'+''.join(f'<div><dt>{label}</dt><dd>{esc(a[field])}</dd></div>' for field,label in [('human_work','Human contribution'),('agent_work','Agent contribution'),('why','Why this division'),('basis','What this is based on')])+'</dl></details>')
    routes=''.join(f'<tr><th scope="row">{esc(route["issue"])}</th><td>{esc(people[route["person_id"]]["name"])}</td></tr>' for route in data['exception_routes'])
    owners=''.join(f'<tr><th scope="row">{esc(o["responsibility"])}</th><td>{esc(people[o["person_id"]]["name"])}</td><td>{esc(o["description"])}</td></tr>' for o in data['ownership'])
    work=[]
    for person_data in data['people']:
        ident=person_data['id'];sections=[]
        for view in ('current','proposed'):
            sections.append(f'<section><h4>{view.capitalize()}</h4><h5>Human work</h5><ul>'+''.join(f'<li>{esc(t)}</li>' for t in data['views'][view]['human_actions'].get(ident,[]))+'</ul><h5>AI work</h5><ul>'+''.join(f'<li>{esc(t)}</li>' for t in data['views'][view]['agent_work'].get(ident,[]))+'</ul></section>')
        work.append(f'<details><summary>{esc(person_data["name"])} · {esc(person_data["role"])}</summary><div class="work-columns">{"".join(sections)}</div></details>')
    notes=''.join(f'<li>{esc(v)}</li>' for v in data['scope_notes']);unknown=''.join(f'<li>{esc(v)}</li>' for v in data['unresolved']);outcomes=''.join(f'<li>{esc(v)}</li>' for v in data['outcomes'])
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(data['title'])}</title><link rel="icon" type="image/svg+xml" href="{favicon}"><style>{css}</style></head><body><main><header><h1>{esc(data['title'])}</h1><p>{esc(data['subtitle'])}</p></header><nav class="view-controls" aria-label="Choose an organisation view" hidden>{controls}</nav>{panels}{shape_key}<section class="supporting"><h2>Work and responsibility record</h2><p>Human only describes the specified decision or action. Any AI preparation of its inputs is recorded separately.</p>{''.join(allocations)}<details><summary>Named owners and release-issue recipients</summary><div class="table-scroll"><table><thead><tr><th>Responsibility</th><th>Human owner</th><th>What this includes</th></tr></thead><tbody>{owners}</tbody></table><table><thead><tr><th>Release issue</th><th>Recipient</th></tr></thead><tbody>{routes}</tbody></table></div><p>Receiving an issue does not confer release-approval authority. Maintenance does not establish day-to-day supervision.</p></details><details><summary>Full current and proposed work by person</summary>{''.join(work)}</details><details open><summary>What remains unresolved</summary><ul>{unknown}</ul></details><details><summary>Scope and evidence</summary><h3>Outcomes in scope</h3><ul>{outcomes}</ul><ul>{notes}</ul></details></section><footer><p>Prepared by <a href="https://www.shivakakkar.com/">Dr. Shiva Kakkar</a></p><details><summary>Design and icon provenance</summary><p>Editorial Magazine Interface by <a href="https://styleref.io/share/cn3z318f-03d09f649c58">@styleref</a>, adapted to the exercise’s human and agent symbols.</p><pre>{esc(_base.provenance())}</pre></details></footer></main><script>{js}</script></body></html>'''


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input',type=Path);parser.add_argument('output',type=Path)
    for key in ('release','division','reporting'):parser.add_argument(f'--{key}-svg',type=Path)
    args=parser.parse_args()
    try:
        paths=[p for p in [args.input,args.output,args.release_svg,args.division_svg,args.reporting_svg] if p]
        for i,left in enumerate(paths):
            for right in paths[i+1:]:
                if left.resolve()==right.resolve() or (left.exists() and right.exists() and left.samefile(right)):raise ValueError('Input and output files must differ.')
        data=json.loads(args.input.read_text(encoding='utf-8'));page=render(data)
        exports={key:render_svg(data,key) for key in ('release','division','reporting')}
        args.output.write_text(page,encoding='utf-8')
        for key,svg in exports.items():
            destination=getattr(args,key+'_svg')
            if destination:destination.write_text(svg,encoding='utf-8')
        print(args.output)
    except (OSError,ValueError) as exc:parser.exit(2,f'{exc}\n')

if __name__=='__main__':main()
