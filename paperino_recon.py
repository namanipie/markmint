import httpx
import re

def investigate_paperino():
    print('Downloading full sitemap...')
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }
    
    try:
        r = httpx.get('https://paperino-eta.vercel.app/sitemap.xml', headers=headers)
        
        urls = re.findall(r'<loc>([^<]+)</loc>', r.text)
        print(f"Found {len(urls)} URLs in sitemap!")
        
        for url in urls[:20]:
            print(url)
            
    except Exception as e:
        print(f'Error: {e}')

if __name__ == "__main__":
    investigate_paperino()
