// Gacha Collection UI Logic

async function loadGachaCollection() {
    try {
        const response = await fetch('/api/gacha/collection');
        const data = await response.json();
        
        if (!data.success) {
            console.error("Lỗi lấy dữ liệu Gacha:", data.msg);
            return;
        }

        const userPrimogems = data.primogems || 0;
        const gemEl = document.getElementById('gacha-primo-count');
        if(gemEl) gemEl.textContent = userPrimogems;

        const collection = data.collection || [];
        const ownedMap = {};
        collection.forEach(item => {
            ownedMap[item.character_id] = item.copies;
        });

        // Tải danh sách nhân vật mẫu
        const charRes = await fetch('/data/characters.json');
        if (!charRes.ok) return;
        const charData = await charRes.json();

        renderGameCollection('genshin', charData.genshin, ownedMap);
        renderGameCollection('hsr', charData.hsr, ownedMap);
        renderGameCollection('zzz', charData.zzz, ownedMap);

    } catch (error) {
        console.error("Lỗi tải bộ sưu tập gacha:", error);
    }
}

function renderGameCollection(gameId, characterList, ownedMap) {
    const container = document.getElementById(`gacha-${gameId}-grid`);
    if (!container || !characterList) return;
    
    container.innerHTML = '';
    
    characterList.forEach(char => {
        const copies = ownedMap[char.id] || 0;
        const isOwned = copies > 0;
        
        const card = document.createElement('div');
        card.className = `gacha-card rarity-${char.rarity.toLowerCase()} ${isOwned ? 'owned' : 'unowned'}`;
        
        card.innerHTML = `
            <div class="card-image-wrapper">
                <img src="${char.image}" alt="${char.name}" loading="lazy" onerror="this.src='https://cdn.discordapp.com/embed/avatars/0.png'">
                ${isOwned ? `<div class="copies-badge">C${copies-1}</div>` : ''}
            </div>
            <div class="card-info">
                <h4>${char.name}</h4>
                <p class="element">${char.element || char.path || ''}</p>
            </div>
        `;
        
        card.onclick = () => showCharacterDetails(char, copies);
        
        container.appendChild(card);
    });
}

function showCharacterDetails(char, copies) {
    alert(`Tên: ${char.name}\nĐộ hiếm: ${char.rarity}\nCung Mệnh/Tinh Hồn: ${Math.max(0, copies-1)}\nTiểu sử: ${char.bio}`);
}

document.addEventListener('DOMContentLoaded', () => {
    const gachaBtn = document.getElementById('btn-tab-gacha');
    if (gachaBtn) {
        gachaBtn.addEventListener('click', loadGachaCollection);
    }
});
