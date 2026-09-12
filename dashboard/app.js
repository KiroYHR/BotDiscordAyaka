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
