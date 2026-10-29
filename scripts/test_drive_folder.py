import urllib.request
import re

folder_id = '1J3K6-KkxmmT-2S2wL1gzCHmZfNAoLCkK'  # PYQ CT Papers folder for Chemistry
url = f'https://drive.google.com/embeddedfolderview?id={folder_id}#list'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

req = urllib.request.Request(url, headers=headers)
try:
    with urllib.request.urlopen(req, timeout=15) as resp:
        html = resp.read().decode('utf-8', errors='ignore')
        print(f"HTML Length: {len(html)}")
        
        # Look for flip-entry or items in the folder
        entries = re.findall(r'<div class="flip-entry"[^>]*>([\s\S]*?)</div>\s*</div>', html)
        print(f"Found {len(entries)} flip-entry items:")
        for e in entries:
            name_m = re.search(r'aria-label="([^"]+)"', e)
            id_m = re.search(r'id="entry-([^"]+)"', e)
            if name_m and id_m:
                print(f" - ID: {id_m.group(1)} | Name: {name_m.group(1)}")
                
        # Also find all file/d/ links
        file_ids = set(re.findall(r'/file/d/([a-zA-Z0-9_\-]+)', html))
        print("File IDs in folder:", file_ids)
except Exception as e:
    print(f"Error: {e}")
