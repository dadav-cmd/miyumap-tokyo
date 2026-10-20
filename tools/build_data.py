"""data/src/*.psv と既存の data/spots.json から、サイト用の data/spots.json と台帳用の data/ledger.csv を作る。

使い方: python tools/build_data.py <丁目代表点JSONのフォルダ>
  丁目代表点は geolonia/japanese-addresses の api/ja/東京都/<区>.json を区ごとに保存したもの。
"""
import csv, glob, json, math, re, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
ADDR_DIR = pathlib.Path(sys.argv[1])
CHECKED_AT = "2026-10-20"

# ウェブで営業状況・開館状況を確認した項目（2026-10-20）
CHECKED = {
    "東京都江戸東京博物館", "荻外荘公園", "世田谷区民会館", "パナソニック汐留美術館", "港区立みなと図書館", "Ginza Sony Park",
    "GLITCH COFFEE & ROASTERS 神保町", "Fuglen Tokyo", "Little Nap COFFEE STAND", "ONIBUS COFFEE 中目黒", "猿田彦珈琲 恵比寿本店",
    "Bear Pond Espresso", "Koffee Mameya Kakeru", "ARiSE COFFEE ROASTERS", "iki ESPRESSO", "ALLPRESS ESPRESSO 東京ロースタリー＆カフェ",
    "LEAVES COFFEE ROASTERS", "ABOUT LIFE COFFEE BREWERS", "茶亭 羽當", "ブルーボトルコーヒー 青山カフェ", "Turret COFFEE",
    "Nui. HOSTEL & BAR LOUNGE", "HAGISO（HAGI CAFE）", "珈琲 古城", "ペリカンカフェ", "名曲喫茶 ルオー", "七つ森", "珈琲天国",
    "minimal 富ヶ谷本店", "Path", "365日", "Bricolage Bread and Company", "パンとエスプレッソと", "CANAL CAFE", "Café 1894",
    "TRUNK(KITCHEN)", "THE ROASTERY BY NOZY COFFEE", "Coffee Wrights 蔵前", "Single O Hamacho", "COFFEE VALLEY",
    "Unlimited Coffee Bar", "FUGLEN ASAKUSA", "SOL'S COFFEE ROASTERY", "ひみつ堂", "カヤバ珈琲", "珈琲西武 本店",
    "名曲・珈琲 新宿 らんぶる", "名曲喫茶ライオン", "さぼうる", "ラドリオ", "ミロンガ・ヌオーバ", "ショパン", "BERG",
    "タカセ 池袋本店", "IVY PLACE", "VIRON 渋谷店", "古桑庵", "HIGASHIYA GINZA", "櫻井焙茶研究所", "笹乃雪", "駒形前川 浅草本店",
    "AKOMEYA TOKYO in la kagu", "THE CONRAN SHOP 代官山", "ACTUS 新宿店", "IDÉE SHOP 自由が丘", "中川政七商店 渋谷店", "SyuRo",
    "カキモリ", "本屋 Title", "新建築書店", "COW BOOKS 中目黒", "BOOK AND SONS", "往来堂書店", "上野桜木あたり", "Playmountain",
    "HOME/WORK VILLAGE", "D&DEPARTMENT TOKYO", "reload", "BEAMS JAPAN", "タワーホール船堀 展望塔",
}
# 自分の座標が丁目の代表点から大きく外れていたため、代表点に置き換える項目
USE_CENTROID = {
    "雑司が谷旧宣教師館", "熊谷守一美術館", "東雲キャナルコートCODAN", "星薬科大学 本館", "世田谷美術館", "台東区立書道博物館",
    "世田谷文学館", "砧公園", "善福寺川緑地", "亀戸中央公園", "北区立中央図書館（赤レンガ図書館）", "レインボーブリッジ 遊歩道",
    "葛飾区郷土と天文の博物館", "D&DEPARTMENT TOKYO", "日暮里繊維街",
}

K = "〇一二三四五六七八九"
def kan(n):
    n = int(n)
    if n < 10: return K[n]
    if n < 20: return "十" + (K[n - 10] if n > 10 else "")
    return K[n // 10] + "十" + (K[n % 10] if n % 10 else "")
norm = lambda s: s.replace("ヶ", "ケ")
towns = {}
for f in ADDR_DIR.glob("*.json"):
    towns[f.stem] = {norm(t["town"]): (t["lat"], t["lng"]) for t in json.load(open(f, encoding="utf-8"))}

def centroid(ward, address):
    rest = address.split(" ")[0]
    rest = rest[len(ward):] if rest.startswith(ward) else rest
    m = re.match(r"([^\d]+)(\d+)?", rest)
    if not m: return None
    town, num = norm(m.group(1)), m.group(2)
    t = towns.get(ward, {})
    if num and int(num) < 100 and town + kan(num) + "丁目" in t: return t[town + kan(num) + "丁目"]
    if town in t: return t[town]
    c = sorted(k for k in t if k.startswith(town))
    return t[c[0]] if c else None

split = lambda s: [x for x in s.split(";") if x] if s else []
def closed(s):
    if s == "": return None
    if s == "-": return []
    return [int(x) for x in s.split(",")]
def flag(s):
    return None if s == "" else s == "1"

existing = json.load(open(ROOT / "data/spots.json", encoding="utf-8"))
base = [s for s in existing["spots"] if re.fullmatch(r"S-0(0\d|1\d|20)", s["id"])]
for s in base:
    s["status"] = "checked" if s["name"] in CHECKED else "unverified"
    s.setdefault("approx", False)

spots = list(base)
n = len(base)
for f in sorted((ROOT / "data/src").glob("*.psv")):
    for line in open(f, encoding="utf-8"):
        if line.startswith("#") or not line.strip(): continue
        c = line.rstrip("\n").split("|")
        assert len(c) == 16, (f, c[1])
        cat, name, ward, address = c[0], c[1], c[2], c[3]
        approx = False
        lat, lng = (float(c[4]), float(c[5])) if c[4] else (None, None)
        if lat is None or name in USE_CENTROID:
            p = centroid(ward, address)
            if p: lat, lng, approx = p[0], p[1], True
        assert lat is not None, name
        n += 1
        designers = split(c[6])
        dtypes = split(c[7]) or (["建築家"] * len(designers))
        spots.append({
            "id": f"S-{n:03d}", "name": name, "category": cat, "tags": split(c[15]),
            "designers": designers, "designerTypes": dtypes, "year": int(c[8]) if c[8] else None,
            "ward": ward, "address": address, "lat": round(lat, 5), "lng": round(lng, 5), "approx": approx,
            "summary": c[9], "highlights": split(c[10]), "visit": c[11] or None,
            "closedDays": closed(c[12]), "free": flag(c[13]), "indoor": c[14] == "1", "url": "",
            "status": "checked" if name in CHECKED else "unverified",
        })

# 同じ座標に重なるピンを少しずらす（約15m）
seen = {}
for s in spots:
    key = (round(s["lat"], 4), round(s["lng"], 4))
    k = seen.get(key, 0)
    if k:
        ang = k * 2.4
        s["lat"] = round(s["lat"] + 0.00013 * math.cos(ang), 5)
        s["lng"] = round(s["lng"] + 0.00016 * math.sin(ang), 5)
    seen[key] = k + 1
for s in spots:
    if s["status"] == "checked": s["checkedAt"] = CHECKED_AT

missing = CHECKED - {s["name"] for s in spots}
assert not missing, missing
out = {"version": CHECKED_AT, "note": "status=checked はウェブで営業・開館状況を確認済み。unverified は未確認。approx=true は位置が丁目単位の概略。", "spots": spots}
json.dump(out, open(ROOT / "data/spots.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

CAT_JA = {"architecture": "建築・アート", "cafe": "カフェ・飲食", "shop": "ショップ", "park": "公園・庭園", "public": "公共施設"}
WD = "日月火水木金土"
with open(ROOT / "data/ledger.csv", "w", encoding="utf-8", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["ID", "名称", "用途カテゴリ", "タグ", "設計者", "設計者区分", "竣工・開業年", "区", "住所", "緯度", "経度", "概要", "見どころ", "見学可否", "営業時間", "休館日", "料金", "公式リンク", "出典", "情報確認日", "掲載状態", "備考"])
    for s in spots:
        cd = s.get("closedDays")
        w.writerow([s["id"], s["name"], CAT_JA[s["category"]], ";".join(s.get("tags", [])), ";".join(s.get("designers", [])),
                    ";".join(s.get("designerTypes", [])), s.get("year") or "", s["ward"], s["address"], s["lat"], s["lng"],
                    s["summary"], ";".join(s.get("highlights", [])), s.get("visit") or "", "",
                    "" if cd is None else ("なし" if not cd else "・".join(WD[d] for d in cd) + "曜"),
                    "" if s.get("free") is None else ("無料" if s["free"] else "有料"), s.get("url", ""), "",
                    s.get("checkedAt", ""), "掲載" if s["status"] == "checked" else "保留",
                    ("位置は丁目単位の概略" if s.get("approx") else "")])

from collections import Counter
print(len(spots), "spots", dict(Counter(s["category"] for s in spots)), "checked", sum(s["status"] == "checked" for s in spots), "approx", sum(s["approx"] for s in spots))
