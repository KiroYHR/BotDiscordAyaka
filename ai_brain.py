import logging
from typing import Dict, Any
import config
from prompts import AYAKA_SYSTEM_PROMPT
from google import genai
from google.genai import types
import asyncio
import datetime
from database import db_manager

logger = logging.getLogger("AyakaBrain")

# Vẫn giữ cache trên RAM để chat mượt mà, nhưng sẽ đồng bộ với DB
chat_sessions: Dict[int, Any] = {}

try:
    client = genai.Client(api_key=config.GEMINI_API_KEY)
except Exception as e:
    logger.error(f"Lỗi khởi tạo Gemini Client: {e}")
    client = None

async def get_or_create_chat(channel_id: int):
    """Lấy hoặc khởi tạo một phiên trò chuyện cho kênh, nạp trí nhớ từ Database."""
    if not client:
        return None
        
    if channel_id not in chat_sessions:
        logger.info(f"Khởi tạo phiên trò chuyện mới cho channel {channel_id}")
        config_options = types.GenerateContentConfig(
            system_instruction=AYAKA_SYSTEM_PROMPT,
            temperature=0.75,
            max_output_tokens=4000,
        )
        
        # Lấy lịch sử từ Database
        history_data = await db_manager.get_chat_history(str(channel_id))
        
        # Khôi phục Content objects
        history_contents = []
        for msg in history_data:
            try:
                role = msg.get("role")
                text = msg.get("text")
                if role and text:
                    part = types.Part.from_text(text=text)
                    content = types.Content(role=role, parts=[part])
                    history_contents.append(content)
            except Exception as e:
                logger.error(f"Lỗi khôi phục tin nhắn: {e}")
                
        chat_sessions[channel_id] = client.chats.create(
            model=config.GEMINI_MODEL_NAME,
            config=config_options,
            history=history_contents if history_contents else None
        )
    return chat_sessions[channel_id]

async def sync_history_to_db(channel_id: int):
    """Lưu trữ lịch sử hiện tại của chat_sessions vào DB."""
    if channel_id not in chat_sessions:
        return
        
    chat = chat_sessions[channel_id]
    history_data = []
    
    # Duyệt qua các tin nhắn trong lịch sử chat
    if hasattr(chat, 'get_history'):
        history = chat.get_history()
    elif hasattr(chat, '_history'):
        history = chat._history
    else:
        history = []
        
    for content in history:
        try:
            if hasattr(content, 'role') and hasattr(content, 'parts'):
                role = content.role
                parts = content.parts
                if parts and len(parts) > 0 and hasattr(parts[0], 'text'):
                    history_data.append({"role": role, "text": parts[0].text})
        except:
            pass
            
    if history_data:
        # Chỉ giữ lại 20 tin nhắn gần nhất để tránh phình to
        history_data = history_data[-20:]
        await db_manager.save_chat_history(str(channel_id), history_data)

async def clear_history(channel_id: int):
    """Xóa phiên trò chuyện trong một kênh để reset ký ức."""
    if channel_id in chat_sessions:
        del chat_sessions[channel_id]
    await db_manager.clear_chat_history(str(channel_id))
    logger.info(f"Đã làm mới ký ức channel {channel_id}")

async def ask_ayaka(channel_id: int, user_name: str, message_text: str) -> str:
    """Gửi câu hỏi của Nhà Lữ Hành đến Ayaka và nhận phản hồi."""
    if not client:
        return "Tớ đang bị mất kết nối tâm thức với máy chủ Gemini (Thiếu API Key). Cậu kiểm tra lại nhé! 🌸"

    chat = await get_or_create_chat(channel_id)
    if not chat:
        return "Không thể khởi tạo phiên trò chuyện. 🌸"
    
    # Ép thời gian thực vào câu hỏi để bot không bị ngáo ngày giờ
    current_time = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    user_prompt = f"[Hệ thống: Thời gian thực tế hiện tại là {current_time}]\n[{user_name}]: {message_text}"

    def send_sync():
        return chat.send_message(user_prompt)

    max_retries = 2
    base_delay = 2
    for attempt in range(max_retries):
        try:
            # Chạy đồng bộ trong ThreadPool và giới hạn thời gian chạy tối đa 10s để tránh treo
            loop = asyncio.get_event_loop()
            response = await asyncio.wait_for(
                loop.run_in_executor(None, send_sync),
                timeout=12.0
            )
            
            reply = response.text or "Ayaka lắng nghe cậu... nhưng có một làn gió tuyết thoảng qua. Cậu có thể nhắc lại được không? 🌸"
            
            # Lưu vào DB sau khi chat
            await sync_history_to_db(channel_id)
            
            return reply

        except asyncio.TimeoutError:
            logger.warning(f"Lỗi Timeout khi đợi phản hồi từ Google (Lần {attempt + 1}/{max_retries})")
            if attempt < max_retries - 1:
                await asyncio.sleep(base_delay)
                continue
            else:
                await clear_history(channel_id)
                return "❌ Máy chủ Google đang phản hồi quá chậm (Timeout). Tớ đã thử hết sức nhưng kết nối đã bị ngắt, cậu hãy thử lại sau nhé! 🌸"

        except Exception as e:
            error_msg = str(e).lower()
            if "503" in error_msg or "unavailable" in error_msg or "429" in error_msg or "quota" in error_msg or "rate limit" in error_msg:
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    logger.warning(f"Gặp lỗi máy chủ/quá tải (503/429), đang thử lại lần {attempt + 1}/{max_retries} sau {delay}s...")
                    await asyncio.sleep(delay)
                    continue
                else:
                    logger.error(f"Lỗi 503/429 liên tục sau {max_retries} lần thử.")
                    await clear_history(channel_id)
                    return "❌ Băng thông kết nối tới máy chủ Google hiện đang quá tải. Ayaka không thể liên lạc được tâm thức, cậu thông cảm đợi một lát rồi gọi lại tớ nhé! 🌸"
            
            # Nếu là lỗi khác, hoặc không phải 503 thì báo lỗi luôn
            logger.error(f"Lỗi khi giao tiếp với Gemini AI: {e}", exc_info=True)
            await clear_history(channel_id)
            return f"Xin thứ lỗi thưa cậu, Ayaka đang gặp chút trở ngại khi kết nối tâm thức: `{error_msg}`. Tớ vừa điều tức lại dòng chảy nguyên tố, cậu hãy thử lại nhé! ❄️"
