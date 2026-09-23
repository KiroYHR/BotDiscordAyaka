import cloudscraper
from bs4 import BeautifulSoup
import json
import os

def fetch_genshin_characters():
    print("Đang cào dữ liệu Genshin Impact...")
    url = "https://genshin-impact.fandom.com/wiki/Character/List"
    scraper = cloudscraper.create_scraper()
    
    chars = []
    try:
        response = scraper.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', {'class': 'article-table'})
        
        for row in table.find_all('tr')[1:]:
            cols = row.find_all('td')
            if len(cols) < 4: continue
            
            name = cols[0].text.strip()
            rarity_img = cols[1].find('img')
            rarity = "SSR" if rarity_img and "5Star" in rarity_img.get('alt', '') else "SR"
            
            if name in ["Aloy", "Traveler"]: rarity = "L"
            
            element_img = cols[2].find('img')
            element = element_img.get('alt', '').replace('Element', '').strip() if element_img else "None"
            
            img_tag = cols[0].find('img')
            image = img_tag.get('data-src') or img_tag.get('src') if img_tag else ""
            if image and image.startswith('data:'): image = "" # Bỏ qua base64 placeholder
            
            # Làm sạch URL ảnh (bỏ phần /revision/...)
            if image:
                image = image.split('/revision/')[0]
                
            chars.append({
                "id": f"gs_{name.lower().replace(' ', '_')}",
                "name": name,
                "rarity": rarity,
                "element": element,
                "image": image,
                "bio": "Một nhân vật trong Genshin Impact."
            })
    except Exception as e:
        print(f"Lỗi Genshin: {e}")
    return chars

def fetch_hsr_characters():
    print("Đang cào dữ liệu Honkai: Star Rail...")
    url = "https://honkai-star-rail.fandom.com/wiki/Character/List"
    scraper = cloudscraper.create_scraper()
    
    chars = []
    try:
        response = scraper.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', {'class': 'article-table'})
        
        for row in table.find_all('tr')[1:]:
            cols = row.find_all('td')
            if len(cols) < 4: continue
            
            name = cols[0].text.strip()
            rarity_img = cols[1].find('img')
            rarity = "SSR" if rarity_img and "5Star" in rarity_img.get('alt', '') else "SR"
            
            if name in ["Trailblazer"]: rarity = "L"
            
            path_img = cols[3].find('img')
            path = path_img.get('alt', '').replace('Path', '').strip() if path_img else "None"
            
            img_tag = cols[0].find('img')
            image = img_tag.get('data-src') or img_tag.get('src') if img_tag else ""
            if image: image = image.split('/revision/')[0]
                
            chars.append({
                "id": f"hsr_{name.lower().replace(' ', '_')}",
                "name": name,
                "rarity": rarity,
                "element": path, # Dùng path thay thế element
                "image": image,
                "bio": "Một nhân vật trong Honkai: Star Rail."
            })
    except Exception as e:
        print(f"Lỗi HSR: {e}")
    return chars

def fetch_zzz_characters():
    print("Đang cào dữ liệu Zenless Zone Zero...")
    url = "https://zenless-zone-zero.fandom.com/wiki/Agent"
    scraper = cloudscraper.create_scraper()
    
    chars = []
    try:
        response = scraper.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', {'class': 'article-table'})
        if not table: return chars
        
        for row in table.find_all('tr')[1:]:
            cols = row.find_all('td')
            if len(cols) < 4: continue
            
            name = cols[0].text.strip()
            rarity_img = cols[1].find('img')
            rarity = "SSR" if rarity_img and "S-Rank" in rarity_img.get('alt', '') else "SR"
            
            element_img = cols[3].find('img')
            element = element_img.get('alt', '').replace('Attribute', '').strip() if element_img else "None"
            
            img_tag = cols[0].find('img')
            image = img_tag.get('data-src') or img_tag.get('src') if img_tag else ""
            if image: image = image.split('/revision/')[0]
                
            chars.append({
                "id": f"zzz_{name.lower().replace(' ', '_')}",
                "name": name,
                "rarity": rarity,
                "element": element,
                "image": image,
                "bio": "Một đặc vụ trong Zenless Zone Zero."
            })
    except Exception as e:
        print(f"Lỗi ZZZ: {e}")
    return chars

if __name__ == "__main__":
    print("Bắt đầu chạy script cào dữ liệu Fandom Wiki...")
    
    # Load old data to avoid overwriting with empty lists on Cloudflare blocks
    old_data = {"genshin": [], "hsr": [], "zzz": []}
    if os.path.exists("data/characters.json"):
        with open("data/characters.json", "r", encoding="utf-8") as f:
            old_data = json.load(f)
            
    genshin = fetch_genshin_characters()
    hsr = fetch_hsr_characters()
    zzz = fetch_zzz_characters()
    
    final_data = {
        "genshin": genshin if genshin else old_data.get("genshin", []),
        "hsr": hsr if hsr else old_data.get("hsr", []),
        "zzz": zzz if zzz else old_data.get("zzz", [])
    }
    
    with open("data/characters.json", "w", encoding="utf-8") as f:
        json.dump(final_data, f, ensure_ascii=False, indent=4)
        
    print(f"Hoàn thành! Đã lưu {len(final_data['genshin'])} NV Genshin, {len(final_data['hsr'])} NV HSR, {len(final_data['zzz'])} NV ZZZ vào data/characters.json")
