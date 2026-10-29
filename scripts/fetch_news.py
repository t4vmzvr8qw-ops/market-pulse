#!/usr/bin/env python3
"""Generate a static news feed from Google News RSS. No API keys or dependencies."""
import datetime as dt, email.utils, hashlib, html, json, re, urllib.parse, urllib.request, xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
QUERIES=[
 ('Earnings','USA','(earnings OR quarterly results) (NYSE OR Nasdaq OR S&P 500) when:3d','en-US','US','US:en'),
 ('Earnings','Europa','(earnings OR quarterly results OR results) (STOXX OR European companies OR London stocks) when:3d','en-GB','GB','GB:en'),
 ('Earnings','Europa','(Quartalszahlen OR Gewinnbericht) (DAX OR MDAX OR Europa) when:3d','de','DE','DE:de'),
 ('Guidance','USA','(raises guidance OR cuts outlook OR lowers guidance) stocks when:3d','en-US','US','US:en'),
 ('Guidance','Europa','(guidance OR Ausblick OR Prognose) Aktien Unternehmen when:3d','de','DE','DE:de'),
 ('Analysten','USA','(analyst upgrade OR analyst downgrade) stocks when:3d','en-US','US','US:en'),
 ('Makro','USA','(Fed OR CPI OR jobs report OR Treasury yields) stocks markets when:3d','en-US','US','US:en'),
 ('Makro','Europa','(EZB OR ECB OR Inflation Eurozone) Märkte when:3d','de','DE','DE:de'),
]
items={};errors=[]
for category,region,q,hl,gl,ceid in QUERIES:
 url='https://news.google.com/rss/search?'+urllib.parse.urlencode({'q':q,'hl':hl,'gl':gl,'ceid':ceid})
 try:
  req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 (compatible; MarketPulseFeed/1.0)'})
  with urllib.request.urlopen(req,timeout=18) as r: body=r.read(2_000_000)
  tree=ET.fromstring(body)
  for it in tree.findall('.//channel/item')[:45]:
   title=html.unescape(re.sub('<[^>]+>','',it.findtext('title',''))).strip()
   link=it.findtext('link','').strip()
   source=(it.findtext('source') or '').strip()
   dtstr=it.findtext('pubDate','')
   try: published=email.utils.parsedate_to_datetime(dtstr).astimezone(dt.timezone.utc)
   except Exception: continue
   if not title or not link or published<dt.datetime.now(dt.timezone.utc)-dt.timedelta(days=7):continue
   norm=re.sub(r'\W+','',title.lower().split(' - ')[0])[:135]
   if norm in items: continue
   k=hashlib.sha256((title+'|'+link).encode()).hexdigest()[:18]
   items[norm]={'id':k,'title':title,'url':link,'source':source,'published':published.isoformat(),'category':category,'region':region}
  print(f'Loaded {category}/{region}: {len(tree.findall(".//channel/item"))}')
 except Exception as ex:
  errors.append(f'{category}/{region}: {type(ex).__name__}: {ex}')
  print('Warning:',errors[-1])
defpath=ROOT/'data/news.json'
if items:
 out={'updated_at':dt.datetime.now(dt.timezone.utc).isoformat(),'items':sorted(items.values(),key=lambda x:x['published'],reverse=True)[:210]}
 defpath.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
 print('Wrote',len(out['items']),'items')
else:
 print('No feeds fetched; retaining previous JSON if any')
 if not defpath.exists(): defpath.write_text(json.dumps({'updated_at':None,'items':[]}),encoding='utf-8')
if errors: print('\n'.join(errors))
