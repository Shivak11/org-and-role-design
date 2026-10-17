#!/usr/bin/env python3
"""Render current and proposed work on the same human reporting baseline."""
from __future__ import annotations
import argparse
import base64
import html
import json
import textwrap
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
MODES = {'human':'Human only','agent':'Agent only','hybrid':'Human + agent','unknown':'Split to confirm'}
INK, MUTED, ORANGE, TEAL = '#20354b','#607083','#be632b','#137977'


def esc(value):
    return html.escape(str(value),quote=True)


def strings(value):
    return isinstance(value,list) and all(isinstance(item,str) for item in value)


def validate(data):
    if not isinstance(data,dict):
        return ['Input must be an object.']
    errors=[]
    for key in ('title','subtitle','scope'):
        if not isinstance(data.get(key),str):
            errors.append(f'{key} must be text.')
    for key in ('outcomes','scope_notes','unresolved'):
        if not strings(data.get(key)):
            errors.append(f'{key} must be a list of text.')
    people=data.get('people')
    if not isinstance(people,list):
        return errors+['people must be a list.']
    ids=set(); parents={}
    for i,person in enumerate(people):
        if not isinstance(person,dict):
            errors.append(f'people[{i}] must be an object.'); continue
        ident=person.get('id')
        if not isinstance(ident,str) or not ident.strip():
            errors.append(f'people[{i}].id must be non-empty text.')
        elif ident in ids:
            errors.append(f'Duplicate person ID: {ident}.')
        else:
            ids.add(ident); parents[ident]=person.get('reports_to')
        for key in ('name','role'):
            if not isinstance(person.get(key),str):
                errors.append(f'people[{i}].{key} must be text.')
        if person.get('reports_to') is not None and not isinstance(person['reports_to'],str):
            errors.append(f'people[{i}].reports_to must be a person ID or null.')
    for ident,parent in parents.items():
        if isinstance(parent,str) and parent not in ids:
            errors.append(f'{ident} reports to an unknown person: {parent}.')
        seen=set(); current=ident
        while isinstance(current,str) and current in parents:
            if current in seen:
                errors.append(f'Reporting cycle includes {current}.'); break
            seen.add(current); current=parents[current]
    views=data.get('views')
    if not isinstance(views,dict):
        errors.append('views must be an object.')
    else:
        for key in ('current','proposed'):
            view=views.get(key)
            if not isinstance(view,dict):
                errors.append(f'views.{key} must be an object.'); continue
            for field in ('human_actions','agent_work'):
                values=view.get(field)
                if not isinstance(values,dict):
                    errors.append(f'views.{key}.{field} must be an object.'); continue
                for ident,items in values.items():
                    if ident not in ids:
                        errors.append(f'views.{key}.{field} references unknown person {ident}.')
                    if not strings(items):
                        errors.append(f'views.{key}.{field}.{ident} must be a list of text.')
    for field in ('allocations','ownership','exception_routes'):
        if not isinstance(data.get(field),list):
            errors.append(f'{field} must be a list.'); continue
        for i,item in enumerate(data[field]):
            if not isinstance(item,dict):
                errors.append(f'{field}[{i}] must be an object.'); continue
            keys={'allocations':('activity','human_work','agent_work','why','basis'),'ownership':('responsibility','description'),'exception_routes':('issue',)}[field]
            for key in keys:
                if not isinstance(item.get(key),str):
                    errors.append(f'{field}[{i}].{key} must be text.')
            if field=='allocations':
                if not isinstance(item.get('mode'),str) or item['mode'] not in MODES:
                    errors.append(f'{field}[{i}].mode must be human, agent, hybrid or unknown.')
            else:
                ident=item.get('person_id')
                if not isinstance(ident,str) or ident not in ids:
                    errors.append(f'{field}[{i}].person_id must reference a recorded human.')
    return errors


def wrap(value,width):
    result=[]
    for line in str(value).splitlines() or ['']:
        result.extend(textwrap.wrap(line,width=width,break_long_words=True,break_on_hyphens=False) or [''])
    return result


def text(value,x,y,width=40,size=16,colour=INK,weight=400,anchor='start',line_height=None):
    lh=line_height or size*1.32
    content=''.join(f'<tspan x="{x}" dy="{0 if i==0 else lh}">{esc(line)}</tspan>' for i,line in enumerate(wrap(value,width)))
    return f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-family="Arial, sans-serif" font-size="{size}" font-weight="{weight}" fill="{colour}">{content}</text>'


def icon(name,x,y,size=38,colour=ORANGE):
    svg=ET.fromstring((ROOT/'assets'/'sketchyicons'/f'{name}.svg').read_text())
    paths=''.join(f'<path d="{esc(child.attrib["d"])}"/>' for child in svg if child.tag.endswith('path'))
    return f'<g transform="translate({x} {y}) scale({size/24})" stroke="{colour}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none">{paths}</g>'


def provenance():
    return (ROOT/'assets'/'sketchyicons'/'NOTICE').read_text()+'\n'+(ROOT/'assets'/'sketchyicons'/'LICENSE').read_text()


def layout(people):
    children={p['id']:[] for p in people};roots=[]
    for p in people:
        if p['reports_to'] is None: roots.append(p['id'])
        else: children[p['reports_to']].append(p['id'])
    positions={};leaf=0;deepest=0
    for root in roots:
        stack=[(root,0,False)]
        while stack:
            ident,depth,visited=stack.pop();deepest=max(deepest,depth)
            if children[ident] and not visited:
                stack.append((ident,depth,True))
                stack.extend((child,depth+1,False) for child in reversed(children[ident]))
            else:
                if children[ident]:
                    xs=[positions[child][0] for child in children[ident]];x=(xs[0]+xs[-1])/2
                else:
                    x=37+leaf*614;leaf+=1
                positions[ident]=(x,184+depth*286)
        leaf+=.12
    width=max(1250,max((x+586 for x,y in positions.values()),default=1250))
    height=max(500,(deepest+1)*286+240)
    return positions,width,height


def summary(items,max_items,width,max_lines):
    result=[];abridged=False
    for item in items[:max_items]:
        item_lines=wrap(item,width)
        if len(item_lines)>max_lines:
            item_lines=item_lines[:max_lines]
            item_lines[-1]=item_lines[-1].rstrip(' .,;')+'…'
            abridged=True
        result.append(item_lines)
    return result,abridged or len(items)>max_items


def render_svg(data,view='proposed'):
    errors=validate(data)
    if errors: raise ValueError('\n'.join(errors))
    if view not in ('current','proposed'): raise ValueError('view must be current or proposed.')
    people=data['people'];positions,width,height=layout(people)
    label='Proposed work and responsibilities' if view=='proposed' else 'Current work and responsibilities'
    description='Human reporting is the current baseline, not a confirmed reporting redesign. Reporting arrows point to the manager. The works-with link records an association with AI tools and agents and does not alone establish supervision. Agent counts are unknown.'
    parts=[f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="org-title org-desc"><title id="org-title">{esc(label)}: {esc(data['title'])}</title><desc id="org-desc">{esc(description)}</desc><metadata>{esc(provenance())}</metadata><defs><marker id="report-arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M1 1 L9 5 L1 9" fill="none" stroke="{INK}" stroke-width="1.5"/></marker><marker id="work-arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M1 1 L9 5 L1 9" fill="none" stroke="{TEAL}" stroke-width="1.5"/></marker></defs><rect width="{width}" height="{height}" fill="#fffdf9"/>''',text(label,37,47,width=70,size=29,weight=700),text('Scope: '+data['scope'],37,82,width=117,size=16,colour=MUTED),text('Human reporting is the current baseline; a reporting redesign has not been confirmed.',37,124,width=118,size=14,colour=MUTED),f'<path d="M37 150 H{width-37}" stroke="#dce2e5" fill="none"/>']
    for p in people:
        if p['reports_to'] is not None:
            x,y=positions[p['id']];px,py=positions[p['reports_to']]
            start_x=x+108;end_x=px+108;end_y=py+244;middle=(y+end_y)/2
            parts.append(f'<path d="M{start_x} {y-2} V{middle} H{end_x} V{end_y+4}" fill="none" stroke="{INK}" stroke-width="1.8" stroke-linejoin="round" marker-end="url(#report-arrow)"/>')
    for p in people:
        x,y=positions[p['id']]
        actions=data['views'][view]['human_actions'].get(p['id'],[])
        agent_work=data['views'][view]['agent_work'].get(p['id'],[])
        action_lines,action_more=summary(actions,2,25,2)
        ai_lines,ai_more=summary(agent_work,3,29,2)
        parts += [f'<rect x="{x}" y="{y}" width="216" height="244" rx="22" fill="#fff2e7" stroke="#d8a47f" stroke-width="1.4"/>',icon('user-round',x+15,y+15,38),text(p['name'],x+64,y+39,width=15,size=20,weight=700),text(p['role'],x+15,y+76,width=26,size=14,colour=MUTED),f'<path d="M{x+15} {y+111} H{x+201}" stroke="#e4c9b3" fill="none"/>']
        ty=y+138
        if not action_lines: parts.append(text('Human actions to confirm',x+15,ty,width=25,size=14,colour=MUTED))
        for item in action_lines:
            parts.append(text('\n'.join(item),x+15,ty,width=25,size=14));ty+=len(item)*18.5+10
        if action_more: parts.append(text('Full work listed below',x+15,y+234,width=28,size=14,colour=MUTED))
        # Association is deliberately distinct from formal employment reporting.
        parts += [text('works',x+251,y+81,size=14,colour=TEAL,anchor='middle'),text('with',x+251,y+100,size=14,colour=TEAL,anchor='middle'),f'<path d="M{x+223} {y+120} H{x+278}" stroke="{TEAL}" stroke-width="1.6" fill="none" marker-end="url(#work-arrow)"/>']
        ax=x+287
        parts += [f'<rect x="{ax}" y="{y}" width="270" height="244" rx="19" fill="#eef8f5" stroke="#79aaa4" stroke-width="1.5"/><rect x="{ax+5}" y="{y+5}" width="260" height="234" rx="15" fill="none" stroke="#c2dcd6"/>',icon('bot',ax+14,y+14,34,TEAL),text('AI tools and agents',ax+58,y+37,width=24,size=16,colour=TEAL,weight=700)]
        ty=y+74
        if not ai_lines: parts.append(text('Agent work to confirm',ax+16,ty,width=29,size=14,colour=MUTED))
        for item in ai_lines:
            parts.append(text('\n'.join(item),ax+16,ty,width=29,size=14));ty+=len(item)*18.5+10
        parts.append(text('Agent count not yet specified',ax+16,y+217,width=33,size=14,colour=MUTED))
        if ai_more: parts.append(text('Full work listed below',ax+16,y+238,width=33,size=14,colour=MUTED))
    footer=height-42
    parts += [f'<path d="M37 {footer-25} H{width-37}" stroke="#dce2e5" fill="none"/>',icon('user-round',37,footer-14,24),text('Human',70,footer+5,size=14),icon('bot',153,footer-14,24,TEAL),text('AI group; not one agent',186,footer+5,size=14),text('↑ Reports to the human at the arrowhead',419,footer+5,width=56,size=14),text('→ Works with; see stated responsibilities',795,footer+5,width=63,size=14,colour=TEAL),text('Prepared by Dr. Shiva Kakkar',width-267,height-12,width=37,size=14,colour=MUTED),'</svg>']
    return ''.join(parts)


def render(data):
    proposed=render_svg(data,'proposed');current=render_svg(data,'current')
    css=(ROOT/'assets'/'org-proposal.css').read_text()
    by_id={p['id']:p for p in data['people']}
    uri=lambda svg:'data:image/svg+xml;base64,'+base64.b64encode(svg.encode()).decode()
    outcomes=''.join(f'<li>{esc(value)}</li>' for value in data['outcomes'])
    notes=''.join(f'<li>{esc(value)}</li>' for value in data['scope_notes'])
    unknowns=''.join(f'<li>{esc(value)}</li>' for value in data['unresolved'])
    allocations=[]
    for a in data['allocations']:
        visual=icon('user-round',0,0,22) if a['mode']=='human' else icon('bot',0,0,22,TEAL) if a['mode']=='agent' else icon('user-round',0,0,22)+icon('bot',27,0,22,TEAL) if a['mode']=='hybrid' else ''
        width=49 if a['mode']=='hybrid' else 22
        badge=f'<svg width="{width}" height="24" viewBox="0 0 {width} 24" aria-hidden="true">{visual}</svg>' if visual else '<span aria-hidden="true">?</span>'
        allocations.append(f'<article class="allocation"><div class="allocation-title"><h3>{esc(a["activity"])}</h3><span class="mode {a["mode"]}">{badge}{MODES[a["mode"]]}</span></div><dl>'+''.join(f'<div><dt>{label}</dt><dd>{esc(a[field]) or "To confirm"}</dd></div>' for field,label in [('human_work','Human contribution'),('agent_work','Agent contribution'),('why','Why this division'),('basis','What this is based on')])+'</dl></article>')
    ownership=''.join(f'<tr><th scope="row">{esc(o["responsibility"])}</th><td>{esc(by_id[o["person_id"]]["name"])}</td><td>{esc(o["description"])}</td></tr>' for o in data['ownership'])
    exceptions=''.join(f'<li><strong>{esc(e["issue"])}</strong><span>{esc(by_id[e["person_id"]]["name"])}</span></li>' for e in data['exception_routes'])
    full=[]
    for p in data['people']:
        sections=[]
        for view in ('current','proposed'):
            v=data['views'][view]
            human=''.join(f'<li>{esc(value)}</li>' for value in v['human_actions'].get(p['id'],[])) or '<li>To confirm</li>'
            agent=''.join(f'<li>{esc(value)}</li>' for value in v['agent_work'].get(p['id'],[])) or '<li>To confirm</li>'
            sections.append(f'<section><h4>{view.capitalize()}</h4><p>Human work</p><ul>{human}</ul><p>AI work</p><ul>{agent}</ul></section>')
        full.append(f'<article class="person-work"><h3>{esc(p["name"])} · {esc(p["role"])}</h3><div class="work-columns">{"".join(sections)}</div></article>')
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(data['title'])}</title><style>{css}</style></head><body><main><header><h1>{esc(data['title'])}</h1><p>{esc(data['subtitle'])}</p></header><section class="outcomes"><h2>Outcomes in scope</h2><ul>{outcomes}</ul></section><div class="main-chart" tabindex="0" aria-label="Proposed work on the current reporting baseline">{proposed}</div><p class="chart-note">Reporting lines use your confirmed current structure. The chart and details record the proposed decision and operating responsibilities.</p><details><summary>Scope and assumptions</summary><ul class="scope-notes">{notes}</ul></details><details><summary>Compare current and proposed work</summary><p>Both views use the same human reporting geometry. The associated work and responsibilities are shown separately.</p><div class="comparison" tabindex="0"><figure><figcaption>Current</figcaption><img src="{uri(current)}" alt="Current work and AI groups on the recorded human reporting structure"></figure><figure><figcaption>Proposed</figcaption><img src="{uri(proposed)}" alt="Proposed work and AI groups on the same human reporting structure"></figure></div></details><details open><summary>Human and agent work, with the reason for each division</summary><p>Human only refers to the specified action or decision. Whether AI prepares its inputs must be read from the contribution details; unexamined support is not ruled out.</p><div class="allocations">{''.join(allocations)}</div></details><details><summary>Named responsibilities and exception routes</summary><div class="table-scroll"><table><thead><tr><th>Responsibility</th><th>Human owner</th><th>What this includes</th></tr></thead><tbody>{ownership}</tbody></table></div><h3>Issue routing</h3><ul class="routes">{exceptions or '<li>No routes have been established yet.</li>'}</ul></details><details><summary>Full current and proposed work by person</summary>{''.join(full)}</details><details open><summary>What remains unresolved</summary><ul>{unknowns or '<li>No unresolved items supplied.</li>'}</ul></details><footer><p>Prepared by Dr. Shiva Kakkar</p><details><summary>Icon provenance and licence</summary><pre>{esc(provenance())}</pre></details></footer></main></body></html>'''


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input',type=Path);parser.add_argument('output',type=Path)
    parser.add_argument('--proposed-svg',type=Path);parser.add_argument('--current-svg',type=Path)
    args=parser.parse_args()
    try:
        paths=[p for p in (args.input,args.output,args.proposed_svg,args.current_svg) if p]
        for i,left in enumerate(paths):
            for right in paths[i+1:]:
                if left.resolve()==right.resolve() or (left.exists() and right.exists() and left.samefile(right)):
                    raise ValueError('Input and output paths must identify different files.')
        data=json.loads(args.input.read_text(encoding='utf-8'))
        page=render(data);proposed=render_svg(data,'proposed');current=render_svg(data,'current')
        args.output.write_text(page,encoding='utf-8')
        if args.proposed_svg:args.proposed_svg.write_text(proposed,encoding='utf-8')
        if args.current_svg:args.current_svg.write_text(current,encoding='utf-8')
        print(args.output)
    except (OSError,ValueError) as exc:
        parser.exit(2,f'{exc}\n')

if __name__=='__main__':main()
