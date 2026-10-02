import httpx
import re

def investigate_paperino():
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    target = "https://paperino-eta.vercel.app/srm/btech/semester-1"
    
    r = httpx.get(target, headers=headers)
    
    # Extract links from the page
    links = set(re.findall(r'href="(/srm/btech/semester-1/[^"]+)"', r.text))
    print(f"Found {len(links)} actual course pages inside semester-1:")
    for l in list(links)[:5]:
        print(l)
        
    if links:
        course_url = f"https://paperino-eta.vercel.app{list(links)[0]}"
        print(f"\nFetching specific course: {course_url}")
        c = httpx.get(course_url, headers=headers)
        
        # Look for question papers / pyq
        print("Looking for question papers or syllabus...")
        if 'CT-1' in c.text or 'ct-1' in c.text.lower():
            print("Found CT-1 references!")
            
        rsc = re.findall(r'self\.__next_f\.push\(\[1,"(.*?)"]\)', c.text)
        for chunk in rsc:
            if 'questions' in chunk.lower() or 'pyq' in chunk.lower() or 'pdf' in chunk.lower():
                print(f"Found data payload chunk: {chunk[:500]}...")
                
if __name__ == "__main__":
    investigate_paperino()
