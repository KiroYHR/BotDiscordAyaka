document.addEventListener('DOMContentLoaded', () => {

    // Hàm gọi API lấy trạng thái bot
    async function fetchStatus() {
        try {
            const response = await fetch('/api/status');
            const data = await response.json();

            document.getElementById('guild-count').textContent = data.guilds;
            document.getElementById('user-count').textContent = data.users;
            document.getElementById('ping-value').textContent = data.latency + ' ms';
            document.getElementById('bot-name').textContent = data.bot_name;

        } catch (error) {
            console.error('Lỗi khi lấy trạng thái:', error);
        }
    }

    // Biến lưu trữ trạng thái HTML hiện tại
    let currentMusicHTML = "";

    // Hàm gọi API lấy thông tin bài hát
    async function fetchMusic() {
        try {
            const response = await fetch('/api/music');
            const data = await response.json();

            const musicContainer = document.getElementById('music-container');
            let newHTML = "";

            if (data.playing && data.tracks.length > 0) {
                data.tracks.forEach(track => {
                    newHTML += `
                        <div class="track-item">
                            <div class="track-icon">
                                <i class="fa-solid fa-music"></i>
                            </div>
                            <div class="track-info">
                                <h4>${track.title}</h4>
                                <p><i class="fa-solid fa-server"></i> Server: ${track.server}</p>
                            </div>
                            <div style="margin-left: auto;">
                                <i class="fa-solid fa-compact-disc fa-spin" style="color: var(--primary-color);"></i>
                            </div>
                        </div>
                    `;
                });
            } else {
                newHTML = `
                    <div class="empty-state">
                        <i class="fa-solid fa-compact-disc"></i>
                        <p>Không có âm điệu nào đang được gảy...</p>
                    </div>
                `;
            }

            // Chỉ cập nhật DOM nếu có sự thay đổi thực sự
            if (currentMusicHTML !== newHTML) {
                musicContainer.innerHTML = newHTML;
                currentMusicHTML = newHTML;
            }

        } catch (error) {
            console.error('Lỗi khi lấy thông tin nhạc:', error);
        }
    }

    // Logic thay đổi Tâm trạng ngẫu nhiên
    const moods = [
        "Đang rất háo hức 🌸",
        "Hơi bối rối một chút... ❄️",
        "Vui vẻ như ngày hội mùa hè 🎆",
        "Đang tập trung suy nghĩ 📚",
        "Cảm thấy bình yên 🍵",
        "Muốn ăn Sakura Mochi 🍡",
        "Muốn gặp nhà lữ hành 🗡️",
        "Hơi xấu hổ một chút 😳",
        "Nhớ nhà 🎐",
    ];

    function updateMood() {
        // Random từ 1 đến 8 tương ứng với AyakaEmoji.jpg đến AyakaEmoji8.jpg
        let num = Math.floor(Math.random() * 8) + 1;
        let filename = num === 1 ? 'AyakaEmoji.jpg' : `AyakaEmoji${num}.jpg`;

        let randomMoodText = moods[Math.floor(Math.random() * moods.length)];

        const moodImg = document.getElementById('mood-avatar');
        const moodText = document.getElementById('mood-text');

        if (moodImg && moodText) {
            const newSrc = `/assets/emojis/${filename}`;

            // Hiệu ứng mờ dần khi đổi
            moodImg.style.opacity = 0;
            moodText.style.opacity = 0;

            setTimeout(() => {
                moodImg.src = newSrc;
                moodText.textContent = randomMoodText;

                moodImg.style.opacity = 1;
                moodText.style.opacity = 1;
            }, 300);
        }
    }

    // Cài đặt transition cho mượt
    if (document.getElementById('mood-avatar')) document.getElementById('mood-avatar').style.transition = 'opacity 0.3s ease';
    if (document.getElementById('mood-text')) document.getElementById('mood-text').style.transition = 'opacity 0.3s ease';

    // Logic tạo hạt tuyết và hoa đào ngẫu nhiên
    function createParticles() {
        const container = document.getElementById('particles-container');
        if (!container) return;

        const numParticles = 20; // Tổng số hạt muốn tạo
        const icons = ['❄️', '🌸']; // Ký tự rơi

        for (let i = 0; i < numParticles; i++) {
            const particle = document.createElement('div');
            // Gán class chung và quyết định loại hạt
            const isSakura = Math.random() > 0.5;
            particle.classList.add('particle', isSakura ? 'sakura' : 'snow');

            // Emoji tương ứng
            particle.textContent = isSakura ? '🌸' : '❄️';

            // Random vị trí từ 1% đến 99% màn hình (tránh tập trung một chỗ)
            const leftPos = Math.random() * 98 + 1;
            particle.style.left = `${leftPos}%`;

            // Random thời gian rơi (8s - 18s) để rơi tự nhiên
            const duration = Math.random() * 10 + 8;
            // Random delay (0s - 10s) để không rơi cùng lúc
            const delay = Math.random() * 10;

            particle.style.animationDuration = `${duration}s, 4s`;
            particle.style.animationDelay = `${delay}s, ${delay}s`;

            // Random kích thước hạt (0.8em - 1.5em)
            const size = Math.random() * 0.7 + 0.8;
            particle.style.fontSize = `${size}em`;

            container.appendChild(particle);
        }
    }

    // Khởi chạy ngay lần đầu
    createParticles();
    fetchStatus();
    fetchMusic();
    updateMood();

    // Tự động cập nhật mỗi 3 giây (Dữ liệu)
    setInterval(fetchStatus, 3000);
    setInterval(fetchMusic, 3000);

    // Tự động đổi tâm trạng mỗi 10 giây
    setInterval(updateMood, 10000);
});

// --- Logic Custom Modal ---
window.showModal = function(title, message, isConfirm = false, onConfirm = null) {
    const modal = document.getElementById('custom-modal');
    const titleEl = document.getElementById('modal-title');
    const msgEl = document.getElementById('modal-message');
    const btnOk = document.getElementById('modal-btn-ok');
    const btnCancel = document.getElementById('modal-btn-cancel');
    const iconEl = document.getElementById('modal-icon');
    
    titleEl.textContent = title;
    msgEl.textContent = message;
    
    // Đổi icon tùy loại
    if (isConfirm) {
        iconEl.innerHTML = '<i class="fa-solid fa-circle-question"></i>';
        iconEl.className = 'modal-icon warning';
        btnCancel.style.display = 'block';
    } else if (title.toLowerCase().includes('lỗi')) {
        iconEl.innerHTML = '<i class="fa-solid fa-circle-xmark"></i>';
        iconEl.className = 'modal-icon warning';
        btnCancel.style.display = 'none';
    } else {
        iconEl.innerHTML = '<i class="fa-solid fa-circle-check"></i>';
        iconEl.className = 'modal-icon';
        btnCancel.style.display = 'none';
    }
    
    modal.classList.add('active');
    
    // Xóa sự kiện cũ
    const newBtnOk = btnOk.cloneNode(true);
    const newBtnCancel = btnCancel.cloneNode(true);
    btnOk.parentNode.replaceChild(newBtnOk, btnOk);
    btnCancel.parentNode.replaceChild(newBtnCancel, btnCancel);
    
    newBtnOk.onclick = () => {
        modal.classList.remove('active');
        if (onConfirm) onConfirm();
    };
    
    newBtnCancel.onclick = () => {
        modal.classList.remove('active');
    };
};

// --- Logic Quản lý Lịch Trình (Schedules) ---
let channelsData = [];

window.loadChannels = function() {
    const guildSelect = document.getElementById('guild-select');
    const channelSelect = document.getElementById('channel-select');
    
    // Nếu dropdown guild đang trống, tải dữ liệu từ API
    if (guildSelect.options.length <= 1 && channelsData.length === 0) {
        fetch('/api/channels').then(res => res.json()).then(data => {
            channelsData = data;
            const guilds = new Set();
            data.forEach(c => guilds.add(c.guild_id));
            
            guilds.forEach(gid => {
                const guildName = data.find(c => c.guild_id === gid).name.split(' (')[1].replace(')', '');
                const opt = document.createElement('option');
                opt.value = gid;
                opt.textContent = guildName;
                guildSelect.appendChild(opt);
            });
        });
        return;
    }
    
    // Nếu user chọn máy chủ, lọc danh sách kênh
    const selectedGuild = guildSelect.value;
    channelSelect.innerHTML = '<option value="">-- Chọn Kênh --</option>';
    if (selectedGuild) {
        channelsData.filter(c => c.guild_id === selectedGuild).forEach(c => {
            const opt = document.createElement('option');
            opt.value = c.id;
            opt.textContent = c.name.split(' ')[0]; // Lấy tên kênh
            channelSelect.appendChild(opt);
        });
    }
};

window.saveSchedule = async function() {
    const guild_id = document.getElementById('guild-select').value;
    const channel_id = document.getElementById('channel-select').value;
    const time_str = document.getElementById('time-input').value;
    const weather_location = document.getElementById('weather-input').value;
    const prompt = document.getElementById('prompt-input').value;
    
    if (!guild_id || !channel_id || !time_str || !prompt) {
        window.showModal('Thông Báo', 'Vui lòng điền đầy đủ các trường bắt buộc!');
        return;
    }
    
    const btn = document.getElementById('btn-save-schedule');
    btn.textContent = 'Đang lưu...';
    btn.disabled = true;
    
    try {
        const res = await fetch('/api/schedules', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ guild_id, channel_id, time_str, prompt, weather_location })
        });
        const data = await res.json();
        if (data.success) {
            window.showModal('Thành Công', 'Đã lưu lịch trình thành công!');
            // Reset form
            document.getElementById('time-input').value = '';
            document.getElementById('weather-input').value = '';
            document.getElementById('prompt-input').value = '';
            window.loadSchedules();
        } else {
            window.showModal('Lỗi', data.error);
        }
    } catch (e) {
        window.showModal('Lỗi', 'Lỗi kết nối: ' + e);
    }
    btn.textContent = 'Lưu Lịch Trình';
    btn.disabled = false;
};

window.loadSchedules = async function() {
    const list = document.getElementById('schedule-list');
    if (!list) return;
    
    try {
        const res = await fetch('/api/schedules');
        const data = await res.json();
        
        if (data.length === 0) {
            list.innerHTML = '<div class="empty-state"><p>Chưa có lịch trình nào.</p></div>';
            return;
        }
        
        let html = '';
        data.forEach(item => {
            html += `
                <div class="schedule-item">
                    <div class="info">
                        <h4>${item.time_str} - ${item.weather_location ? 'Có báo thời tiết' : 'Chỉ nhắc nhở'}</h4>
                        <p><strong>Nội dung:</strong> ${item.prompt.length > 30 ? item.prompt.substring(0, 30) + '...' : item.prompt}</p>
                    </div>
                    <button class="btn-delete" onclick="deleteSchedule(${item.id})" title="Xóa lịch"><i class="fa-solid fa-trash"></i></button>
                </div>
            `;
        });
        list.innerHTML = html;
    } catch (e) {
        console.error('Lỗi tải lịch trình:', e);
    }
};

window.deleteSchedule = function(id) {
    window.showModal('Xác Nhận', 'Bạn có chắc muốn xóa lịch trình này?', true, async () => {
        try {
            const res = await fetch('/api/schedules?id=' + id, { method: 'DELETE' });
            const data = await res.json();
            if (data.success) {
                window.loadSchedules();
            } else {
                window.showModal('Lỗi', 'Lỗi khi xóa: ' + data.error);
            }
        } catch (e) {
            window.showModal('Lỗi', 'Lỗi kết nối: ' + e);
        }
    });
};

document.addEventListener('DOMContentLoaded', () => {
    window.loadChannels();
    window.loadSchedules();
});

// --- Logic Chuyển Tab (Navigation) ---
window.switchTab = function(tabId) {
    // Xóa active khỏi tất cả các nút
    document.querySelectorAll('.nav-btn').forEach(btn => btn.classList.remove('active'));
    // Ẩn tất cả các tab
    document.querySelectorAll('.tab-pane').forEach(tab => tab.classList.remove('active'));
    
    // Thêm active cho nút được bấm
    document.getElementById('btn-tab-' + tabId).classList.add('active');
    // Hiện tab tương ứng
    document.getElementById('tab-' + tabId).classList.add('active');
};

// --- Logic Bảng Xếp Hạng (Leaderboard) ---
window.fetchLeaderboard = async function() {
    try {
        const response = await fetch('/api/leaderboard');
        const users = await response.json();
        const tbody = document.getElementById('lb-body');
        if (!tbody) return;
        
        if (users.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" style="text-align: center;">Chưa có ai trong danh sách!</td></tr>';
            return;
        }

        let html = '';
        users.forEach(user => {
            let rankClass = '';
            if (user.rank === 1) rankClass = 'rank-1';
            else if (user.rank === 2) rankClass = 'rank-2';
            else if (user.rank === 3) rankClass = 'rank-3';

            html += `
                <tr class="lb-row ${rankClass}">
                    <td class="lb-cell">#${user.rank}</td>
                    <td class="lb-cell">
                        <div class="user-info">
                            <img src="${user.avatar}" alt="Avatar" class="user-avatar">
                            <div>
                                <div class="user-name">${user.display_name}</div>
                                <div class="user-tag">@${user.username}</div>
                            </div>
                        </div>
                    </td>
                    <td class="lb-cell">
                        <span class="level-badge">Lv. ${user.level}</span>
                    </td>
                    <td class="lb-cell">
                        ✨ ${user.exp.toLocaleString()} EXP
                    </td>
                </tr>
            `;
        });
        tbody.innerHTML = html;
    } catch (error) {
        console.error("Lỗi:", error);
        const tbody = document.getElementById('lb-body');
        if(tbody) tbody.innerHTML = '<tr><td colspan="4" style="text-align: center; color: red;">Lỗi tải dữ liệu!</td></tr>';
    }
};

document.addEventListener('DOMContentLoaded', () => {
    window.fetchLeaderboard();
    setInterval(window.fetchLeaderboard, 60000);
    
    // Kiểm tra URL Hash để mở đúng tab
    if (window.location.hash) {
        const hash = window.location.hash.substring(1); // Xóa dấu #
        if (['dashboard', 'schedule', 'leaderboard', 'system'].includes(hash)) {
            window.switchTab(hash);
        }
    }
});


// --- Logic Phase 9: Đăng Nhập & Hảo Cảm ---
window.fetchUserProfile = async function() {
    try {
        const response = await fetch('/api/me');
        const data = await response.json();
        if (data.authenticated) {
            document.getElementById('user-name').textContent = data.global_name || data.username;
            document.getElementById('user-avatar').src = data.avatar;
            document.getElementById('user-subtitle').innerHTML = `<span class="level-badge">Lv. ${data.level}</span> - ${data.exp} EXP`;
            
            // Cập nhật tab companion
            document.getElementById('user-affection').textContent = data.affection;
            document.getElementById('user-streak').textContent = data.streak;
            
            // Hiện nút tab Companion
            document.getElementById('btn-tab-companion').style.display = 'block';
            
            // Ẩn nút đăng nhập
            const loginBtn = document.querySelector('.status-badge a[href="/login"]');
            if(loginBtn) loginBtn.parentElement.style.display = 'none';
        }
    } catch (e) {
        console.error("Lỗi lấy thông tin user:", e);
    }
};

window.claimDaily = async function() {
    const btn = document.getElementById('btn-daily-claim');
    btn.disabled = true;
    btn.textContent = 'Đang nhận...';
    try {
        const response = await fetch('/api/daily', { method: 'POST' });
        const data = await response.json();
        if (data.success) {
            window.showModal('Điểm Danh Thành Công 🌸', `Ayaka rất vui vì cậu đã quay lại! Cậu vừa nhận được ${data.affection_gained} 💖 Hảo Cảm.\n\nChuỗi hiện tại: ${data.streak} ngày 🔥`);
            document.getElementById('user-affection').textContent = data.affection;
            document.getElementById('user-streak').textContent = data.streak;
        } else {
            window.showModal('Thông Báo', data.msg);
        }
    } catch (e) {
        window.showModal('Lỗi', 'Không thể kết nối đến máy chủ.');
    }
    btn.disabled = false;
    btn.innerHTML = '<i class="fa-solid fa-gift"></i> Điểm Danh Ngay';
};

document.addEventListener('DOMContentLoaded', () => {
    window.fetchUserProfile();
});


// --- Logic Giai Đoạn 10: Custom Live2D ---
let live2dModel = null;
let live2dApp = null;

window.initLive2D = async function() {
    if (live2dApp) return; // Đã khởi tạo
    
    const canvas = document.getElementById('live2d-canvas');
    if (!canvas) return;
    
    try {
        live2dApp = new PIXI.Application({
            view: canvas,
            transparent: true,
            autoStart: true,
            resizeTo: document.getElementById('live2d-wrapper')
        });
        
        // Dùng tạm mô hình Shizuku miễn phí từ thư viện (Nguồn Github đáng tin cậy)
        const modelUrl = 'https://cdn.jsdelivr.net/gh/guansss/pixi-live2d-display@master/test/assets/shizuku/shizuku.model.json';
        live2dModel = await PIXI.live2d.Live2DModel.from(modelUrl);
        
        live2dApp.stage.addChild(live2dModel);
        
        // Điều chỉnh tỷ lệ kích thước
        live2dModel.scale.set(0.2); 
        live2dModel.x = (live2dApp.renderer.width - live2dModel.width) / 2;
        live2dModel.y = (live2dApp.renderer.height - live2dModel.height) / 2 + 100;
        
        // Xoá chữ Loading
        document.getElementById('live2d-loading').style.display = 'none';
        
        // Tương tác: Nhìn theo chuột
        live2dApp.ticker.add(() => {
            const mousePosition = live2dApp.renderer.plugins.interaction.mouse.global;
            if (mousePosition.x > 0 && mousePosition.y > 0) {
                // Focus: x, y in range [-1, 1]
                const focusX = (mousePosition.x / live2dApp.renderer.width) * 2 - 1;
                const focusY = (mousePosition.y / live2dApp.renderer.height) * 2 - 1;
                live2dModel.focus(focusX, focusY);
            }
        });
        
        // Tương tác: Chạm
        live2dModel.on('hit', (hitAreas) => {
            if (hitAreas.includes('head')) {
                live2dModel.motion('tap_body');
            } else {
                live2dModel.motion('tap_body');
            }
        });
    } catch (error) {
        console.error("Lỗi khi tải Live2D:", error);
        document.getElementById('live2d-loading').innerHTML = "Lỗi khi tải Ayaka :(";
    }
};

// Override lại hàm claimDaily để kết hợp hiệu ứng Live2D
const originalClaimDaily = window.claimDaily;
window.claimDaily = async function() {
    // Kích hoạt hoạt ảnh vui vẻ
    if (live2dModel) {
        try {
            live2dModel.motion('tap_body'); 
        } catch (e) {}
    }
    
    // Chạy lại logic ban đầu
    if (originalClaimDaily) {
        await originalClaimDaily();
    }
};

// Sửa switchTab để khởi tạo Live2D khi nhấn vào tab Đồng Hành
const originalSwitchTab = window.switchTab;
window.switchTab = function(tabId) {
    if (originalSwitchTab) {
        originalSwitchTab(tabId);
    }
    if (tabId === 'companion') {
        window.initLive2D();
    }
};
