# -*- coding: utf-8 -*-
"""COS Signature V5 client (stdlib only): list objects under chenpi-videos/."""
import hashlib, hmac, urllib.parse, urllib.request, winreg, xml.etree.ElementTree as ET

REGION = 'ap-guangzhou'
BUCKET = 'afeng-media-1455467655'
HOST = f'{BUCKET}.cos.{REGION}.myqcloud.com'

def creds():
    k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Environment')
    sid, _ = winreg.QueryValueEx(k, 'TENCENT_SECRET_ID')
    skey, _ = winreg.QueryValueEx(k, 'TENCENT_SECRET_KEY')
    winreg.CloseKey(k)
    return sid, skey

SID, SKEY = creds()

def sign(method, path, params=None, headers=None, sign_time=None):
    import time
    params = params or {}
    headers = headers or {}
    now = int(time.time())
    key_time = f'{now - 60};{now + 3600}'
    sign_time = sign_time or key_time

    # 需要簽名的 header（host 必簽），全部小寫
    hdrs = {k.lower(): str(v) for k, v in headers.items()}
    hdrs['host'] = HOST
    header_list = ';'.join(sorted(hdrs))
    header_str = '&'.join(f'{k}={urllib.parse.quote(hdrs[k], safe="-_.~")}' for k in sorted(hdrs))

    p = {k.lower(): str(v) for k, v in params.items()}
    url_param_list = ';'.join(sorted(p))
    url_param_str = '&'.join(f'{k}={urllib.parse.quote(p[k], safe="-_.~")}' for k in sorted(p))

    http_str = f'{method.lower()}\n{path}\n{url_param_str}\n{header_str}\n'
    string_to_sign = f'sha1\n{sign_time}\n{hashlib.sha1(http_str.encode()).hexdigest()}\n'
    sign_key = hmac.new(SKEY.encode(), sign_time.encode(), hashlib.sha1).hexdigest()
    sig = hmac.new(sign_key.encode(), string_to_sign.encode(), hashlib.sha1).hexdigest()

    auth = (f'q-sign-algorithm=sha1&q-ak={SID}&q-sign-time={sign_time}&q-key-time={key_time}'
            f'&q-header-list={header_list}&q-url-param-list={url_param_list}&q-signature={sig}')
    out = dict(headers)
    out['Host'] = HOST
    out['Authorization'] = auth
    return out

def list_objects(prefix='', max_keys=1000):
    path = '/'
    params = {'prefix': prefix, 'max-keys': str(max_keys)}
    hdrs = sign('get', path, params)
    qs = urllib.parse.urlencode(params)
    req = urllib.request.Request(f'https://{HOST}/?{qs}', headers=hdrs, method='GET')
    with urllib.request.urlopen(req, timeout=60) as r:
        body = r.read()
    root = ET.fromstring(body)
    ns = {'c': root.tag.split('}')[0].strip('{')}
    out = []
    for c in root.findall('c:Contents', ns):
        out.append({
            'Key': c.findtext('c:Key', '', ns),
            'Size': int(c.findtext('c:Size', '0', ns)),
            'LastModified': c.findtext('c:LastModified', '', ns),
        })
    return out, root.findtext('c:IsTruncated', 'false', ns)

if __name__ == '__main__':
    items, trunc = list_objects('chenpi-videos/')
    print(f'chenpi-videos/ 共 {len(items)} 個物件 (truncated={trunc})')
    for it in sorted(items, key=lambda x: x['Key']):
        print(f'  {it["Size"]/1048576:8.2f} MB  {it["Key"]}')
    print()
    items2, _ = list_objects('')
    vids = [i for i in items2 if i['Key'].lower().endswith(('.mp4', '.mov', '.avi', '.webm'))]
    print(f'整個 bucket 的影片檔（含其他目錄）共 {len(vids)} 個：')
    for it in sorted(vids, key=lambda x: x['Key']):
        print(f'  {it["Size"]/1048576:8.2f} MB  {it["Key"]}')
