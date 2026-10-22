#!/usr/bin/env python3
"""Validate stories.json against stories.schema.json plus FNN writer rules. Exit 1 on any error."""
import json,re,sys
from jsonschema import Draft202012Validator, FormatChecker
feed=json.load(open('stories.json')); sch=json.load(open('stories.schema.json'))
errs=[f"schema: {'/'.join(map(str,e.path))}: {e.message}" for e in Draft202012Validator(sch,format_checker=FormatChecker()).iter_errors(feed)]
BANNED=r'\b(satire|satirical|parody|Kern|Chado|Mak|Stu|Rayb|H[1-5]|edge|lean|sidecar|prototype)\b'
CAPS=r'\b(NEEDS|TODO|EXAMPLE)\b'
slugs=[s['slug'] for s in feed['stories']]
if len(slugs)!=len(set(slugs)): errs.append('duplicate slugs')
if feed.get('lead') and feed['lead'] not in slugs: errs.append('lead not in stories')
for s in feed['stories']:
    p=s['slug']; wc=len(s['body'].split())
    if not 80<=wc<=100: errs.append(f'{p}: body {wc} words')
    if re.search(r'https?://|www\.|\]\(|Sources:',s['body']): errs.append(f'{p}: link in body')
    roles=[r.get('role') for r in s['record']]
    if 'then' in s:
        if roles[:2]!=['then','now']: errs.append(f'{p}: record must start then, now')
    elif any(roles): errs.append(f'{p}: then/now roles without then/now')
    for m in re.finditer(BANNED,json.dumps(s,ensure_ascii=False),re.I): errs.append(f'{p}: banned word {m.group(0)!r}')
    for m in re.finditer(CAPS,json.dumps(s,ensure_ascii=False)): errs.append(f'{p}: internal marker {m.group(0)!r}')
    if re.search(r'grok\.me',json.dumps(s)): errs.append(f'{p}: grok.me URL')
for e in errs: print('ERROR',e)
print(f"{len(feed['stories'])} stories, {sum('then' in s for s in feed['stories'])} THEN|NOW, {len(errs)} errors")
sys.exit(1 if errs else 0)
