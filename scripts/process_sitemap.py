#!/usr/bin/env python3
# scripts/process_sitemap.py
# Purpose:
#  - Fetch sitemap.xml
#  - For each new <loc> (not yet tracked), fetch page (Blogger-compatible),
#    extract Title, Thumbnail, find data-encrypted values, decode them,
#    detect playlist URLs (m3u8/m3u/mpd/mp4/ts/etc).
#  - Append new locs to sitemap_urls.txt and new playlists to found_playlists.txt
#  - Write /tmp/new_posts.txt with Title, Thumbnail, Playlist blocks for workflow/telegram.

import sys, os, re, time, argparse
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

# config
TIMEOUT = 20
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; Bot/1.0)"}
TMP_OUT = "/tmp/new_posts.txt"
PLAYLIST_RE = re.compile(
    r'(https?://[^\s"\'<>]+?\.(?:m3u8|m3u|mpd|mp4|ts|aac|mkv)(?:\?[^\s"\'<>]*)?)',
    flags=re.IGNORECASE
)

def fetch_text(url):
    try:
        r = requests.get(url, timeout=TIMEOUT, headers=HEADERS)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"[!] fetch failed: {url} -> {e}")
        return None

def extract_loc_from_sitemap(xml_text):
    return re.findall(r'<loc>(.*?)</loc>', xml_text, flags=re.IGNORECASE | re.DOTALL)

def read_tracked(path):
    s = set()
    if not os.path.exists(path):
        return s
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"): continue
            s.add(line)
    return s

def append_tracked(path, items):
    if not items: return
    with open(path, 'a', encoding='utf-8') as f:
        f.write("\n# added on %s\n" % time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
        for it in items:
            f.write(it.strip() + "\n")

def extract_title(html, base_url=None):
    try:
        soup = BeautifulSoup(html, "html.parser")
        og = soup.find("meta", property="og:title")
        if og and og.get("content"): return og["content"].strip()
        mt = soup.find("meta", attrs={"name":"title"})
        if mt and mt.get("content"): return mt["content"].strip()
        if soup.title and soup.title.string: return soup.title.string.strip()
        h = soup.find(["h1","h2"])
        if h and h.get_text(): return h.get_text().strip()
    except Exception:
        pass
    return "No Title"

def extract_thumbnail(html, page_url=None):
    try:
        soup = BeautifulSoup(html, "html.parser")
        og = soup.find("meta", property="og:image")
        if og and og.get("content"):
            return urljoin(page_url or "", og["content"].strip())

        tw = soup.find("meta", attrs={"name":"twitter:image"})
        if tw and tw.get("content"):
            return urljoin(page_url or "", tw["content"].strip())

        ip = soup.find(attrs={"itemprop":"image"})
        if ip:
            if ip.name == "meta" and ip.get("content"):
                return urljoin(page_url or "", ip["content"].strip())
            if ip.name == "img" and ip.get("src"):
                return urljoin(page_url or "", ip["src"].strip())

        lnk = soup.find("link", rel=lambda v: v and "image_src" in v)
        if lnk and lnk.get("href"):
            return urljoin(page_url or "", lnk["href"].strip())

        for sel in [".post-body img", ".post img", "article img", ".entry-content img"]:
            el = soup.select_one(sel)
            if el and el.get("src"):
                return urljoin(page_url or "", el["src"].strip())

        nos = soup.find("noscript")
        if nos:
            ns_soup = BeautifulSoup(nos.get_text(), "html.parser")
            img = ns_soup.find("img")
            if img and img.get("src"):
                return urljoin(page_url or "", img["src"].strip())

        img = soup.find("img")
        if img and img.get("src"):
            return urljoin(page_url or "", img["src"].strip())
    except Exception:
        pass
    return "No Thumbnail"

def extract_data_encrypted(html):
    # common attribute
    arr = re.findall(r'data-encrypted=["\']([^"\']+)["\']', html, flags=re.IGNORECASE)
    return arr

def normalize_base64(s):
    t = re.sub(r'\s+', '', s)
    t = t.replace('-', '+').replace('_', '/')
    while len(t) % 4 != 0:
        t += '='
    return t

def decode_base64(s):
    try:
        import base64
        nb = normalize_base64(s)
        raw = base64.b64decode(nb)
        try:
            return raw.decode('utf-8', 'ignore')
        except:
            return raw.decode('latin1', 'ignore')
    except Exception:
        return None

def find_playlists(text):
    if not text: return []
    return list(dict.fromkeys(PLAYLIST_RE.findall(text)))

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--sitemap', required=True)
    p.add_argument('--tracked-file', default='sitemap_urls.txt')
    p.add_argument('--playlists-file', default='found_playlists.txt')
    p.add_argument('--out', default=TMP_OUT)
    args = p.parse_args()

    sitemap_url = args.sitemap
    tracked_file = args.tracked_file
    playlists_file = args.playlists_file
    out_file = args.out

    print("[*] fetching sitemap:", sitemap_url)
    sitemap_text = fetch_text(sitemap_url)
    if not sitemap_text:
        print("[!] cannot fetch sitemap")
        sys.exit(1)

    locs = extract_loc_from_sitemap(sitemap_text)
    print(f"[*] sitemap contains {len(locs)} loc entries")

    tracked = read_tracked(tracked_file)
    new_locs = [l for l in locs if l not in tracked]
    print(f"[*] new locs to check: {len(new_locs)}")

    found_posts = []
    found_playlists = []

    for loc in new_locs:
        print("[*] processing:", loc)
        html = fetch_text(loc)
        if not html:
            print("[-] failed to fetch page:", loc)
            continue

        title = extract_title(html, loc)
        thumb = extract_thumbnail(html, loc)

        # 1) decode data-encrypted values
        encs = extract_data_encrypted(html)
        decoded_texts = []
        for e in encs:
            d = decode_base64(e)
            if d:
                decoded_texts.append(d)

        # 2) find playlists in decoded texts first
        playlist_urls = []
        for dt in decoded_texts:
            playlist_urls += find_playlists(dt)

        # 3) fallback scan page html itself
        playlist_urls += find_playlists(html)
        # unique preserve order
        seen = set()
        playlist_urls = [x for x in playlist_urls if not (x in seen or seen.add(x))]

        if playlist_urls:
            final = playlist_urls[0]
            found_posts.append({"loc": loc, "title": title, "thumbnail": thumb, "playlist": final})
            found_playlists.append(final)
            print("[+] FOUND playlist:", final, "title:", title)
        else:
            print("[-] no playlist found for:", loc)

        time.sleep(0.6)

    # write results to tmp out for the workflow
    if found_posts:
        with open(out_file, 'w', encoding='utf-8') as f:
            for p in found_posts:
                f.write(p['title'] + "\n")
                f.write(p['thumbnail'] + "\n")
                f.write(p['playlist'] + "\n")
                f.write(p['loc'] + "\n")
                f.write("---\n")

        # append playlists to playlists_file (tracked)
        append_tracked(playlists_file, found_playlists)

        # append processed locs to sitemap tracked file
        append_tracked(tracked_file, [p['loc'] for p in found_posts])

        print("[*] wrote", len(found_posts), "new posts to", out_file)
    else:
        # remove out file if exists
        if os.path.exists(out_file):
            try: os.remove(out_file)
            except: pass
        print("[*] no new playlist posts discovered")

if __name__ == "__main__":
    main()
