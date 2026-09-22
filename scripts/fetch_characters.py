import urllib.request
from bs4 import BeautifulSoup
import json
import os

def fetch_genshin_characters():
    print("Đang cào dữ liệu Genshin Impact...")
    url = "https://genshin-impact.fandom.com/wiki/Character/List"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
    
    chars = []
    try:
        response = urllib.request.urlopen(req)
        soup = BeautifulSoup(response.read(), 'html.parser')
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
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
    
    chars = []
    try:
        response = urllib.request.urlopen(req)
        soup = BeautifulSoup(response.read(), 'html.parser')
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

if __name__ == "__main__":
    print("Bắt đầu chạy script cào dữ liệu Fandom Wiki...")
    
    genshin = fetch_genshin_characters()
    hsr = fetch_hsr_characters()
    
    final_data = {
        "genshin": genshin,
        "hsr": hsr,
        "zzz": [] # ZZZ có cấu trúc bảng khác, có thể tự bổ sung sau.
    }
    
    with open("data/characters.json", "w", encoding="utf-8") as f:
        json.dump(final_data, f, ensure_ascii=False, indent=4)
        
    print(f"Hoàn thành! Đã lưu {len(genshin)} NV Genshin, {len(hsr)} NV HSR vào data/characters.json")
