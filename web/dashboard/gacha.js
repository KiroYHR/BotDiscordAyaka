// Gacha Collection UI Logic - Multi-game & Advanced Filtering

let gachaState = {
    selectedGame: 'genshin',
    selectedRarity: 'all',
    selectedOwnership: 'all',
    searchQuery: '',
    charData: { genshin: [], hsr: [], zzz: [] },
    ownedMap: {},
    userPrimogems: 0
};

async function loadGachaCollection() {
    try {
        // 1. Tải danh sách nhân vật mẫu
        const charRes = await fetch('/data/characters.json');
        if (charRes.ok) {
            gachaState.charData = await charRes.json();
        }

        // 2. Tải dữ liệu bộ sưu tập của user đăng nhập
        const response = await fetch('/api/gacha/collection');
        const data = await response.json();
        
        if (data.success) {
            gachaState.userPrimogems = data.primogems || 0;
            const gemEl = document.getElementById('gacha-primo-count');
            if (gemEl) gemEl.textContent = Number(gachaState.userPrimogems).toLocaleString();

            const collection = data.collection || [];
            gachaState.ownedMap = {};
            collection.forEach(item => {
                gachaState.ownedMap[item.character_id] = item.copies;
            });
        }

        updateTabCounters();
        renderCurrentGachaView();

    } catch (error) {
        console.error("Lỗi tải bộ sưu tập gacha:", error);
    }
}

function updateTabCounters() {
    ['genshin', 'hsr', 'zzz'].forEach(gameKey => {
        const list = gachaState.charData[gameKey] || [];
        const total = list.length;
        const owned = list.filter(c => (gachaState.ownedMap[c.id] || 0) > 0).length;
        const countEl = document.getElementById(`count-${gameKey}`);
        if (countEl) {
            countEl.textContent = `(${owned}/${total})`;
        }
    });
}

function selectGachaGame(gameKey) {
    gachaState.selectedGame = gameKey;
    
    // Cập nhật active class cho 3 tab game
    document.querySelectorAll('.gacha-game-tab').forEach(tab => {
        if (tab.getAttribute('data-game') === gameKey) {
            tab.classList.add('active');
        } else {
            tab.classList.remove('active');
        }
    });

    const titleMap = {
        'genshin': 'Genshin Impact',
        'hsr': 'Honkai: Star Rail',
        'zzz': 'Zenless Zone Zero'
    };
    const titleEl = document.getElementById('gacha-current-game-title');
    if (titleEl) titleEl.textContent = titleMap[gameKey] || 'Bộ Sưu Tập';

    renderCurrentGachaView();
}

function setRarityFilter(rarity) {
    gachaState.selectedRarity = rarity;
    document.querySelectorAll('#rarity-filters .filter-btn').forEach(btn => {
        if (btn.getAttribute('data-rarity') === rarity) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });
    renderCurrentGachaView();
}

function setOwnershipFilter(ownership) {
    gachaState.selectedOwnership = ownership;
    document.querySelectorAll('#ownership-filters .filter-btn').forEach(btn => {
        if (btn.getAttribute('data-owned') === ownership) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });
    renderCurrentGachaView();
}

function onGachaSearch(query) {
    gachaState.searchQuery = (query || '').trim().toLowerCase();
    renderCurrentGachaView();
}

function renderCurrentGachaView() {
    const container = document.getElementById('gacha-collection-grid');
    if (!container) return;

    const gameList = gachaState.charData[gachaState.selectedGame] || [];
    const totalInGame = gameList.length;
    const ownedInGame = gameList.filter(c => (gachaState.ownedMap[c.id] || 0) > 0).length;
    const pct = totalInGame > 0 ? Math.round((ownedInGame / totalInGame) * 100) : 0;

    const progressEl = document.getElementById('gacha-progress-text');
    if (progressEl) {
        progressEl.textContent = `Tiến độ sưu tập: ${ownedInGame} / ${totalInGame} (${pct}%)`;
    }

    // Lọc theo điều kiện
    let filtered = gameList.filter(char => {
        // Lọc Bậc
        if (gachaState.selectedRarity !== 'all' && char.rarity !== gachaState.selectedRarity) {
            return false;
        }
        // Lọc Sở Hữu
        const copies = gachaState.ownedMap[char.id] || 0;
        if (gachaState.selectedOwnership === 'owned' && copies <= 0) {
            return false;
        }
        if (gachaState.selectedOwnership === 'unowned' && copies > 0) {
            return false;
        }
        // Lọc Tìm Kiếm
        if (gachaState.searchQuery) {
            const matchName = char.name.toLowerCase().includes(gachaState.searchQuery);
            const matchElem = (char.element || char.path || '').toLowerCase().includes(gachaState.searchQuery);
            if (!matchName && !matchElem) return false;
        }
        return true;
    });

    container.innerHTML = '';

    if (filtered.length === 0) {
        container.innerHTML = `
            <div style="grid-column: 1 / -1; text-align: center; padding: 40px; color: #888;">
                <i class="fa-solid fa-ghost" style="font-size: 2.5rem; margin-bottom: 10px; opacity: 0.5;"></i>
                <p>Không tìm thấy nhân vật nào phù hợp với bộ lọc hiện tại.</p>
            </div>
        `;
        return;
    }

    // Render cards
    filtered.forEach(char => {
        const copies = gachaState.ownedMap[char.id] || 0;
        const isOwned = copies > 0;
        const rarityKey = (char.rarity || 'R').toLowerCase();

        const card = document.createElement('div');
        card.className = `gacha-card rarity-${rarityKey} ${isOwned ? 'owned' : 'unowned'}`;

        const starsCount = (char.rarity === 'SSR' || char.rarity === 'L') ? 5 : (char.rarity === 'SR' ? 4 : 3);
        const starsStr = '★'.repeat(starsCount);
        const tagText = char.element || char.path || char.role || '';

        card.innerHTML = `
            <div class="card-image-wrapper">
                <img src="${char.image}" alt="${char.name}" loading="lazy" onerror="this.src='https://cdn.discordapp.com/embed/avatars/0.png'">
                ${isOwned ? `<div class="copies-badge">${copies >= 7 ? 'MAX C6' : `C${copies-1}`}</div>` : ''}
                ${tagText ? `<div class="element-badge">${tagText}</div>` : ''}
                <div class="rarity-badge rarity-tag-${rarityKey}">${char.rarity}</div>
            </div>
            <div class="card-info">
                <h4>${char.name}</h4>
                <div class="stars">${starsStr}</div>
            </div>
        `;

        card.onclick = () => showCharacterDetails(char, copies);
        container.appendChild(card);
    });
}

function showCharacterDetails(char, copies) {
    const isOwned = copies > 0;
    const constellationText = isOwned ? (copies >= 7 ? 'C6 (Đã mở khóa tối đa)' : `C${copies - 1}`) : 'Chưa sở hữu';
    
    const modal = document.getElementById('custom-modal');
    if (!modal) {
        alert(`Tên: ${char.name}\nĐộ hiếm: ${char.rarity}\nTrạng thái: ${constellationText}\nThuộc tính: ${char.element || char.path || 'Tiêu chuẩn'}\nTiểu sử: ${char.bio || 'Chưa có thông tin.'}`);
        return;
    }

    const titleEl = document.getElementById('modal-title');
    const msgEl = document.getElementById('modal-message');
    const iconEl = document.getElementById('modal-icon');
    const okBtn = document.getElementById('modal-btn-ok');

    if (titleEl) titleEl.innerHTML = `${char.name} <span class="rarity-tag-${char.rarity.toLowerCase()}">[${char.rarity}]</span>`;
    if (msgEl) {
        msgEl.innerHTML = `
            <div style="display: flex; gap: 15px; align-items: center; margin-bottom: 12px; text-align: left;">
                <img src="${char.image}" style="width: 70px; height: 70px; border-radius: 10px; object-fit: cover; border: 2px solid rgba(255,255,255,0.2);">
                <div>
                    <div><strong>Thuộc tính:</strong> ${char.element || char.path || char.role || 'Tiêu chuẩn'}</div>
                    <div><strong>Trạng thái:</strong> <span style="color: ${isOwned ? '#4df8ff' : '#aaa'};">${constellationText}</span></div>
                    <div><strong>Số bản đã quay:</strong> ${copies} / 7</div>
                </div>
            </div>
            <p style="font-size: 0.9em; opacity: 0.85; text-align: left; line-height: 1.5; margin: 0;">${char.bio || 'Một nhân vật ưu tú thuộc đa vũ trụ HoYoverse.'}</p>
        `;
    }
    if (iconEl) iconEl.className = 'modal-icon fa-solid fa-sparkles';
    
    modal.classList.add('active');
    if (okBtn) {
        okBtn.onclick = () => modal.classList.remove('active');
    }
}

document.addEventListener("DOMContentLoaded", () => {
    // Điểm danh ngày
    const btnDaily = document.getElementById("btn-claim-daily");
    if (btnDaily) {
        btnDaily.addEventListener("click", async () => {
            btnDaily.disabled = true;
            try {
                const res = await fetch('/api/daily', { method: 'POST' });
                const data = await res.json();
                if (data.success) {
                    alert(`✅ Thành công! Cậu nhận được ${data.primos_gained} 💎 và ${data.affection_gained} 💖 (Chuỗi: ${data.streak} ngày)`);
                    loadGachaCollection();
                } else {
                    alert(`❌ ${data.msg}`);
                }
            } catch (e) {
                alert("Lỗi kết nối tới máy chủ.");
            }
            btnDaily.disabled = false;
        });
    }

    // Quà tháng
    const btnMonthly = document.getElementById("btn-claim-monthly");
    if (btnMonthly) {
        btnMonthly.addEventListener("click", async () => {
            btnMonthly.disabled = true;
            try {
                const res = await fetch('/api/monthly', { method: 'POST' });
                const data = await res.json();
                if (data.success) {
                    alert(`🎉 Thành công! Cậu nhận được ${data.primos_gained} 💎 quà ưu đãi hằng tháng!`);
                    loadGachaCollection();
                } else {
                    alert(`❌ ${data.msg}`);
                }
            } catch (e) {
                alert("Lỗi kết nối tới máy chủ.");
            }
            btnMonthly.disabled = false;
        });
    }

    const gachaBtn = document.getElementById('btn-tab-gacha');
    if (gachaBtn) {
        gachaBtn.addEventListener('click', loadGachaCollection);
    }
});
