"""Fetch the store's live listings using only PUBLIC data, for the scheduled site refresh.

Uses eBay's Browse API with an application token (client id + secret). That token can read
public listings and nothing else: it cannot see orders, change listings or touch the account,
so it is the safe thing to store in GitHub. Writes src/stock.json and downloads listing photos.

Credentials come from the environment:  EBAY_CLIENT_ID  EBAY_CLIENT_SECRET
  python3 fetch_stock.py [site_root]         (site_root defaults to the parent folder)
  python3 fetch_stock.py --local-test        (reads the keys from laptop-tools, prints only, writes nothing)
"""
import base64
import datetime as dt
import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path

SELLER = 'spanotechnologies'
# top-level eBay categories the store lists in: computers, cell phones/wearables, consumer electronics
CATEGORIES = ['58058', '15032', '293']


def app_token(client_id, client_secret):
    auth = base64.b64encode(f'{client_id}:{client_secret}'.encode()).decode()
    body = urllib.parse.urlencode({'grant_type': 'client_credentials',
                                   'scope': 'https://api.ebay.com/oauth/api_scope'}).encode()
    req = urllib.request.Request('https://api.ebay.com/identity/v1/oauth2/token', data=body, headers={
        'Authorization': f'Basic {auth}', 'Content-Type': 'application/x-www-form-urlencoded'})
    return json.load(urllib.request.urlopen(req, timeout=30))['access_token']


def listings(token):
    seen = {}
    for cat in CATEGORIES:
        offset = 0
        while True:
            q = urllib.parse.urlencode({'category_ids': cat, 'filter': f'sellers:{{{SELLER}}}', 'limit': 200, 'offset': offset})
            req = urllib.request.Request(f'https://api.ebay.com/buy/browse/v1/item_summary/search?{q}', headers={
                'Authorization': f'Bearer {token}', 'X-EBAY-C-MARKETPLACE-ID': 'EBAY_US'})
            data = json.load(urllib.request.urlopen(req, timeout=30))
            for it in data.get('itemSummaries', []):
                legacy = it.get('legacyItemId') or it['itemId'].split('|')[1]
                seen[legacy] = dict(id=legacy, title=it['title'].strip(), price=it['price']['value'],
                                    url=f'https://www.ebay.com/itm/{legacy}',
                                    image_url=(it.get('image') or {}).get('imageUrl', ''))
            offset += 200
            if offset >= data.get('total', 0):
                break
    return list(seen.values())


def main():
    if '--local-test' in sys.argv:
        sys.path.insert(0, '/Users/cole/laptop-tools')
        import ebay_auth
        creds = ebay_auth.load_creds()
        cid = creds.get('client_id') or creds.get('app_id')
        secret = creds.get('client_secret') or creds.get('cert_id')
        items = listings(app_token(cid, secret))
        print(len(items), 'public listing(s) found')
        for it in items:
            print(' ', it['id'], '|', it['price'], '|', it['title'][:70], '| photo:', bool(it['image_url']))
        return
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent
    items = listings(app_token(os.environ['EBAY_CLIENT_ID'], os.environ['EBAY_CLIENT_SECRET']))
    out_dir = root / 'site' / 'assets' / 'stock'
    out_dir.mkdir(parents=True, exist_ok=True)
    for it in items:
        it['image'] = ''
        url = it.pop('image_url')
        if url:
            big = url.replace('s-l225', 's-l800').replace('s-l1600', 's-l800')
            try:
                (out_dir / f'{it["id"]}.jpg').write_bytes(urllib.request.urlopen(
                    urllib.request.Request(big, headers={'User-Agent': 'Mozilla/5.0'}), timeout=30).read())
                it['image'] = f'assets/stock/{it["id"]}.jpg'
            except Exception as e:
                print('photo failed', it['id'], e)
    keep = {f'{i["id"]}.jpg' for i in items}
    for old in out_dir.glob('*.jpg'):
        if old.name not in keep:
            old.unlink()
    items.sort(key=lambda i: -float(i['price']))
    (root / 'src' / 'stock.json').write_text(json.dumps(dict(as_of=dt.date.today().isoformat(), items=items), indent=1))
    print(len(items), 'listing(s) written')


if __name__ == '__main__':
    main()
