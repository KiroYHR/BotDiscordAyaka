// Gacha Collection UI Logic - Multi-game, Priority Sorting (L -> SSR -> SR -> R) & Web Roll

let gachaState = {
    selectedGame: 'genshin',
    selectedRarity: 'all',
    selectedOwnership: 'all',
    searchQuery: '',
    charData: { genshin: [], hsr: [], zzz: [] },
    ownedMap: {},
    userPrimogems: 0
};

// Thứ tự ưu tiên độ hiếm: L -> SSR -> SR -> R
const RARITY_WEIGHT = {
    'L': 1,
    'SSR': 2,
    'SR': 3,
    'R': 4
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

    const rawList = gachaState.charData[gachaState.selectedGame] || [];
    
    // SẮP XẾP ƯU TIÊN THEO BẬC: L -> SSR -> SR -> R (thay vì theo nguyên tố)
    const gameList = [...rawList].sort((a, b) => {
        const rA = RARITY_WEIGHT[a.rarity] || 99;
        const rB = RARITY_WEIGHT[b.rarity] || 99;
        if (rA !== rB) return rA - rB;
        return a.name.localeCompare(b.name, 'vi');
    });

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
                ${isOwned 
                    ? `<div class="copies-badge">${copies >= 7 ? 'MAX C6' : `C${copies-1}`}</div>` 
                    : `<div class="lock-overlay"><i class="fa-solid fa-lock"></i> Chưa có</div>`
                }
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

// Hàm Cầu Nguyện x1 và x10 trực tiếp từ Web Dashboard
async function rollGachaWeb(count) {
    const cost = count === 10 ? 1600 : 160;
    
    const btn = document.getElementById(count === 10 ? 'btn-roll-10' : 'btn-roll-1');
    if (btn) btn.disabled = true;

    try {
        const res = await fetch('/api/gacha/roll', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ count: count })
        });
        const data = await res.json();
        
        if (data.success) {
            showGachaResultModal(data, count);
            loadGachaCollection();
        } else {
            alert(`❌ ${data.msg || "Không thể thực hiện cầu nguyện."}`);
        }
    } catch (e) {
        alert("Lỗi kết nối tới máy chủ khi cầu nguyện.");
    } finally {
        if (btn) btn.disabled = false;
    }
}

function showGachaResultModal(data, count) {
    const modal = document.getElementById('custom-modal');
    if (!modal) {
        alert(data.results.join('\n'));
        return;
    }

    const titleEl = document.getElementById('modal-title');
    const msgEl = document.getElementById('modal-message');
    const iconEl = document.getElementById('modal-icon');
    const okBtn = document.getElementById('modal-btn-ok');

    if (titleEl) titleEl.innerHTML = `🌠 Kết Quả Cầu Nguyện x${count}`;
    if (iconEl) iconEl.className = 'modal-icon fa-solid fa-wand-magic-sparkles';

    const cardsHtml = (data.pulled_cards || []).map(c => {
        const rKey = (c.rarity || 'r').toLowerCase();
        return `
            <div style="display: flex; align-items: center; gap: 10px; padding: 6px 10px; margin-bottom: 6px; border-radius: 8px; background: rgba(0,0,0,0.25); border-left: 4px solid ${rKey === 'l' ? '#ff0055' : (rKey === 'ssr' ? '#f5af19' : (rKey === 'sr' ? '#a855f7' : '#60a5fa'))};">
                <img src="${c.image}" style="width: 38px; height: 38px; border-radius: 6px; object-fit: cover;" onerror="this.src='https://cdn.discordapp.com/embed/avatars/0.png'">
                <div style="flex: 1; text-align: left;">
                    <div style="font-weight: bold; font-size: 0.9em;">${c.name} <span class="rarity-tag-${rKey}">[${c.rarity}]</span></div>
                    <div style="font-size: 0.75em; opacity: 0.8;">${c.element || ''} ${c.is_refund ? '• 🔁 Đã quy đổi vé' : `• Bản thứ ${c.copies}/7`}</div>
                </div>
            </div>
        `;
    }).join('');

    const refundText = data.refund_primos > 0 
        ? `<div style="margin-top: 10px; padding: 8px; border-radius: 8px; background: rgba(255, 215, 0, 0.15); color: #ffd700; font-weight: bold; font-size: 0.88em;">💎 Quy đổi hoàn trả: +${data.refund_primos.toLocaleString()} Nguyên Thạch!</div>` 
        : '';

    if (msgEl) {
        msgEl.innerHTML = `
            <div style="max-height: 320px; overflow-y: auto; padding-right: 5px; margin-bottom: 10px;">
                ${cardsHtml}
            </div>
            ${refundText}
            <div style="font-size: 0.82em; color: #8ACBEB; margin-top: 8px;">
                Bảo hiểm hiện tại: SR (${data.pity_4star}/10) • SSR (${data.pity_5star}/100)
            </div>
        `;
    }

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
