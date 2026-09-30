# -*- coding: utf-8 -*-
"""Quét văn bản mới từ các nguồn công khai, ghi ra data/vanban-moi.json.
Chạy trên GitHub Actions. Nguồn nào lỗi thì bỏ qua, không làm hỏng các nguồn khác.
Cấu hình nguồn trong data/nguon-quet.json."""
import json, re, os, datetime, requests
from bs4 import BeautifulSoup

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data')
os.makedirs(DATA, exist_ok=True)
UA = {'User-Agent': 'Mozilla/5.0 (compatible; DATA96-TayNinh/1.0; +https://tranhuudat1204.github.io/DATA96-TayNinh/)'}

# số hiệu kiểu 57-NQ/TW, 1383/KH-UBND, 150/2025/NĐ-CP, 35-KH/TU
SOHIEU = re.compile(r'\b\d{1,5}(?:/\d{4})?(?:-[A-ZĐa-zđ]+)?/[A-ZĐ][A-ZĐa-z0-9]*(?:-[A-ZĐa-z0-9]+)*|\b\d{1,5}-[A-ZĐ]{1,4}[a-z]?/[A-ZĐ]+')
NGAY = re.compile(r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})')
LOAI = ['Nghị quyết','Kết luận','Chỉ thị','Quy định','Hướng dẫn','Chương trình','Kế hoạch','Quyết định','Nghị định','Thông tư','Công văn','Thông báo','Công điện','Luật']

def load_sources():
    p = os.path.join(DATA, 'nguon-quet.json')
    if os.path.exists(p):
        return json.load(open(p, encoding='utf-8'))
    return []

def scan(src):
    out = []
    try:
        r = requests.get(src['url'], headers=UA, timeout=45)
        r.raise_for_status()
        r.encoding = r.apparent_encoding or 'utf-8'
    except Exception as e:
        print('BO QUA', src.get('ten'), e)
        return out
    soup = BeautifulSoup(r.text, 'lxml')
    for a in soup.select(src.get('chon', 'a')):
        text = ' '.join(a.get_text(' ', strip=True).split())
        if len(text) < 12:
            continue
        m = SOHIEU.search(text)
        if not m:
            continue
        so = m.group(0).strip(' .,;')
        ngay = ''
        d = NGAY.search(text)
        if d:
            ngay = '%02d/%02d/%s' % (int(d.group(1)), int(d.group(2)), d.group(3))
        loai = next((x for x in LOAI if x.lower() in text.lower()), '')
        href = a.get('href') or ''
        if href and not href.startswith('http'):
            from urllib.parse import urljoin
            href = urljoin(src['url'], href)
        out.append({
            'so': so, 'ngay': ngay, 'loai': loai,
            'cq': src.get('co_quan', ''), 'cap': src.get('cap', ''),
            'ty': text[:300], 'nguon': href or src['url'], 'quet_luc': datetime.date.today().isoformat()
        })
    print(src.get('ten'), '->', len(out))
    return out

def main():
    found, seen = [], set()
    for src in load_sources():
        for it in scan(src):
            if it['so'] in seen:
                continue
            seen.add(it['so'])
            found.append(it)
    # giữ lại tối đa 300 văn bản mới nhất, không trùng lần quét trước
    old_path = os.path.join(DATA, 'vanban-moi.json')
    old = []
    if os.path.exists(old_path):
        try:
            old = json.load(open(old_path, encoding='utf-8'))
        except Exception:
            old = []
    old_so = {x.get('so') for x in old}
    merged = found + [x for x in old if x.get('so') not in seen]
    merged = merged[:300]
    json.dump(merged, open(old_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('Tong cong', len(merged), 'van ban trong danh sach cho duyet;', len([x for x in found if x['so'] not in old_so]), 'moi hom nay')

if __name__ == '__main__':
    main()
