# Sử dụng Python 3.11 slim để image nhẹ nhất có thể
FROM python:3.11-slim

# Cài đặt ffmpeg và libsodium (bắt buộc cho chức năng phát nhạc của Discord bot)
RUN apt-get update && \
    apt-get install -y ffmpeg libsodium-dev && \
    rm -rf /var/lib/apt/lists/*

# Đặt thư mục làm việc trong container
WORKDIR /app

# Copy các file requirements.txt vào trước để tận dụng Docker cache
COPY requirements.txt .

# Cài đặt toàn bộ thư viện Python cần thiết
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ mã nguồn vào image
COPY . .

# Mở Port 928 cho hệ thống Web Dashboard
EXPOSE 928

# Khởi chạy Bot và Web Dashboard song song
CMD ["python", "bot.py"]
