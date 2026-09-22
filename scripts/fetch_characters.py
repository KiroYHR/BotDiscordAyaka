import urllib.request
import json
import os

print("Bắt đầu cào dữ liệu nhân vật Genshin Impact từ nguồn mở...")

url = "https://raw.githubusercontent.com/EnkaNetwork/API-docs/master/store/characters.json"
try:
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    response = urllib.request.urlopen(req)
    data = json.loads(response.read())
    
    characters_json = {"genshin": [], "hsr": [], "zzz": []}
    
    # Chỉ lấy tạm 50 nhân vật đầu tiên để minh họa
    count = 0
    for char_id, char_info in data.items():
        if count >= 50:
            break
        
        # Enka format
        quality = char_info.get("QualityType", "QUALITY_PURPLE")
        rarity = "SSR" if "ORANGE" in quality else "SR"
        if "PROTAGONIST" in quality:
            rarity = "L"
            
        element = char_info.get("Element", "None")
        
        characters_json["genshin"].append({
            "id": f"gs_{char_id}",
            "name": f"Nhân vật {char_id} (Cần mapping tên)",
            "rarity": rarity,
            "element": element,
            "image": "https://api.ambr.top/assets/UI/UI_AvatarIcon_Side_PlayerBoy.png", # Placeholder
            "bio": "Dữ liệu được tự động cào từ nguồn mở."
        })
        count += 1
        
    print(f"Đã cào thành công {count} nhân vật Genshin!")
    print("Do thiếu API chuẩn hóa tên (tiếng Việt) và hình ảnh đẹp, dữ liệu trên web HoYoWiki vẫn là lý tưởng nhất.")
    print("Nếu muốn cào từ HoYoWiki, bạn sẽ cần dùng một thư viện trình duyệt ảo (như Selenium) để vượt qua Cloudflare.")
    
except Exception as e:
    print(f"Lỗi: {e}")
