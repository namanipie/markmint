import httpx
import re
import json
import time

class CompetitorScraper:
    def __init__(self):
        self.base_url = "https://The competitor-eta.vercel.app"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5'
        }
        self.courses_data = []

    def get_sitemap_urls(self):
        """Extract all internal URLs from the XML sitemap to bypass UI navigation."""
        print("[*] Bypassing React Router UI by hitting the XML Sitemap...")
        try:
            r = httpx.get(f"{self.base_url}/sitemap.xml", headers=self.headers, timeout=10.0)
            if r.status_code == 200:
                urls = re.findall(r'<loc>([^<]+)</loc>', r.text)
                print(f"[+] Successfully extracted {len(urls)} hidden routes from sitemap.")
                return urls
            else:
                print(f"[-] Failed to fetch sitemap. Status: {r.status_code}")
                return []
        except Exception as e:
            print(f"[-] Error fetching sitemap: {e}")
            return []

    def extract_react_server_components(self, html):
        """
        The competitor uses Next.js App Router which hides data in React Server Component (RSC) chunks
        instead of standard API endpoints. We have to parse the raw chunk streams.
        """
        chunks = re.findall(r'self\.__next_f\.push\(\[1,"(.*?)"]\)', html)
        full_payload = ""
        for chunk in chunks:
            try:
                # Basic unescaping of the RSC chunk stream
                cleaned = chunk.replace('\\"', '"').replace('\\n', '\n').replace('\\\\', '\\')
                full_payload += cleaned
            except:
                continue
        return full_payload

    def scrape_course(self, url):
        """Scrape a specific course page and extract syllabus, CT1, and CT2 data."""
        print(f"[*] Scraping: {url.replace(self.base_url, '')}")
        try:
            r = httpx.get(url, headers=self.headers, timeout=15.0)
            if r.status_code != 200:
                return None
                
            payload = self.extract_react_server_components(r.text)
            
            # Use regex to find course titles, syllabus units, and question references
            course_title_match = re.search(r'{"title":"([^"]+)","description"', payload)
            course_title = course_title_match.group(1) if course_title_match else url.split('/')[-1]
            
            units = re.findall(r'(Unit \d+|Module \d+).*?(?=Unit \d+|Module \d+|$)', r.text, re.IGNORECASE)
            
            ct_refs = re.findall(r'(CT[- ]?[1234])', r.text, re.IGNORECASE)
            
            if len(units) > 0 or len(ct_refs) > 0:
                return {
                    'url': url,
                    'title': course_title,
                    'units_found': len(units),
                    'ct_mentions': len(ct_refs),
                    'raw_payload_size': len(payload)
                }
            return None
            
        except Exception as e:
            print(f"[-] Error on {url}: {e}")
            return None

    def run(self):
        print("="*50)
        print("COMPETITOR DATA EXTRACTION PROTOCOL INITIALIZED")
        print("="*50)
        
        all_urls = self.get_sitemap_urls()
        
        # Filter for URLs that look like specific semesters/courses
        target_urls = [u for u in all_urls if '/srm/' in u and len(u.split('/')) > 4]
        print(f"[*] Found {len(target_urls)} potential syllabus targets.")
        
        print("\n[*] Initiating extraction (Showing first 5 for test)...\n")
        
        for url in target_urls[:5]:
            time.sleep(1) # Be nice to their servers
            data = self.scrape_course(url)
            if data:
                self.courses_data.append(data)
                print(f"  [+] Success! Extracted {data['units_found']} units and {data['ct_mentions']} CT exams.")
            else:
                print(f"  [-] No academic data found on route.")
                
        # Save output to be ingested by MarkMint backend
        if self.courses_data:
            with open("backend/scripts/competitor_dump.json", "w") as f:
                json.dump(self.courses_data, f, indent=2)
            print(f"\n[+] Successfully dumped {len(self.courses_data)} courses to competitor_dump.json")
            print("[*] Ready for MarkMint ingestion.")

if __name__ == "__main__":
    scraper = CompetitorScraper()
    scraper.run()
