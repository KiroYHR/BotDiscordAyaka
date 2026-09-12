import discord
from discord.ext import commands
import logging
import asyncio
import os
import aiohttp
from google import genai
from google.genai import types
import config
from prompts import AYAKA_SYSTEM_PROMPT

logger = logging.getLogger("AyakaRAG")

class RAGCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        try:
            self.client = genai.Client(api_key=config.GEMINI_API_KEY)
        except Exception as e:
            logger.error(f"Lỗi khởi tạo Gemini Client trong RAGCog: {e}")
            self.client = None

    async def download_file(self, attachment: discord.Attachment) -> str:
        """Tải file đính kèm xuống local tạm thời"""
        os.makedirs("temp_docs", exist_ok=True)
        file_path = os.path.join("temp_docs", attachment.filename)
        await attachment.save(file_path)
        return file_path

    @commands.command(name="askpdf", aliases=["doc", "hoitailieu"])
    async def ask_pdf(self, ctx, *, question: str = "Tóm tắt nội dung chính của tài liệu này giúp tớ nhé."):
        """
        Đọc và phân tích tài liệu (PDF, TXT, DOCX, CSV...).
        Sử dụng: Đính kèm file (hoặc reply tin nhắn có file) và gõ `!askpdf [câu hỏi]`
        """
        if not self.client:
            await ctx.reply("❌ Lõi AI đang bị mất kết nối, không thể đọc tài liệu lúc này.")
            return

        # Tìm file đính kèm
        attachment = None
        if ctx.message.attachments:
            attachment = ctx.message.attachments[0]
        elif ctx.message.reference and ctx.message.reference.resolved:
            if ctx.message.reference.resolved.attachments:
                attachment = ctx.message.reference.resolved.attachments[0]
                
        if not attachment:
            await ctx.reply("🌸 Cậu cần đính kèm một tài liệu (PDF, TXT, DOCX...) hoặc Reply tin nhắn có tài liệu thì tớ mới đọc được nhé!")
            return
            
        # Kiểm tra dung lượng (giới hạn an toàn 25MB)
        if attachment.size > 25 * 1024 * 1024:
            await ctx.reply("❌ Tài liệu này nặng quá (>25MB), thư viện của tớ không chứa nổi rồi!")
            return
            
        msg = await ctx.reply("⏳ Đang tải tài liệu vào Tàng thư các của hiệp hội Yashiro...")
        
        try:
            # Tải file về local
            local_path = await self.download_file(attachment)
            
            await msg.edit(content="⏳ Đang nạp tài liệu vào tiềm thức AI, cậu đợi tớ đọc xíu nhé (có thể mất vài chục giây)...")
            
            loop = asyncio.get_event_loop()
            
            def process_document():
                # 1. Upload file to Gemini
                uploaded_file = self.client.files.upload(file=local_path)
                
                # 2. Tạo config (bắt buộc trả lời chuyên nghiệp, chuẩn xác)
                sys_prompt = "Bạn là Kamisato Ayaka. Nhiệm vụ của bạn là đọc kỹ tài liệu người dùng cung cấp và trả lời câu hỏi một cách chuẩn xác, chuyên nghiệp. Không bịa đặt thông tin ngoài tài liệu."
                config_options = types.GenerateContentConfig(
                    system_instruction=sys_prompt,
                    temperature=0.2, # Độ sáng tạo thấp để bám sát tài liệu
                )
                
                # 3. Phân tích tài liệu
                response = self.client.models.generate_content(
                    model=config.GEMINI_MODEL_NAME,
                    contents=[uploaded_file, question],
                    config=config_options
                )
                
                # 4. Xóa file trên Cloud để bảo mật
                self.client.files.delete(name=uploaded_file.name)
                
                return response.text
                
            # Chạy trong Thread để tránh block bot
            answer = await loop.run_in_executor(None, process_document)
            
            # Xóa file local
            if os.path.exists(local_path):
                os.remove(local_path)
                
            # Cắt bớt nếu câu trả lời quá dài (>2000 ký tự Discord limit)
            if len(answer) > 1950:
                answer = answer[:1950] + "...\n*(Câu trả lời đã bị cắt do quá dài)*"
                
            await msg.edit(content=f"📑 **Phân tích tài liệu:** {attachment.filename}\n\n{answer}")
            
        except Exception as e:
            logger.error(f"Lỗi RAG askpdf: {e}", exc_info=True)
            error_msg = str(e)
            if "503" in error_msg and "UNAVAILABLE" in error_msg:
                await msg.edit(content="❌ Băng thông kết nối tới máy chủ Google hiện đang quá tải (Lỗi 503). Cậu đợi một chút rồi thử lại nhé! 🌸")
            else:
                if len(error_msg) > 1000:
                    error_msg = error_msg[:1000] + "... (Lỗi quá dài)"
                await msg.edit(content=f"❌ Rất tiếc, tớ không thể đọc được tài liệu này. Chi tiết lỗi: {error_msg}")

    @commands.command(name="summary", aliases=["tomtat", "hongbien"])
    async def summary(self, ctx, limit: int = 50):
        """
        Tóm tắt N tin nhắn gần nhất trong kênh hiện tại.
        Sử dụng: `!summary 50` (Tối đa 200 tin nhắn)
        """
        if not self.client:
            await ctx.reply("❌ Lõi AI đang bị mất kết nối.")
            return
            
        if limit < 5 or limit > 200:
            await ctx.reply("🌸 Cậu hãy chọn số lượng tin nhắn từ 5 đến 200 thôi nhé!")
            return
            
        msg = await ctx.reply(f"⏳ Đang thu thập {limit} tin nhắn gần nhất để làm bản tin hóng hớt...")
        
        try:
            # Lấy lịch sử chat
            messages = []
            async for m in ctx.channel.history(limit=limit + 2):
                if m.id == ctx.message.id or m.id == msg.id:
                    continue
                if m.content:
                    messages.append(f"[{m.author.display_name}]: {m.content}")
                    
            messages.reverse() # Xếp theo thứ tự thời gian cũ -> mới
            chat_log = "\n".join(messages)
            
            if len(messages) < 3:
                await msg.edit(content="❌ Không có đủ tin nhắn để tóm tắt đâu cậu ạ.")
                return
                
            await msg.edit(content="⏳ Đang tổng hợp thành bản tin nội bộ...")
            
            loop = asyncio.get_event_loop()
            def process_summary():
                sys_prompt = "Bạn là Kamisato Ayaka, một tiểu thư dễ thương, thanh lịch nhưng cũng rất hài hước. Hãy đóng vai một MC Bản Tin Nội Bộ, đọc đoạn lịch sử trò chuyện sau đây và tóm tắt lại những sự kiện, biến căng, hoặc những đoạn hội thoại nổi bật nhất. Sử dụng giọng văn hài hước, dễ thương, có emoji."
                
                config_options = types.GenerateContentConfig(
                    system_instruction=sys_prompt,
                    temperature=0.8,
                )
                
                prompt = f"Đây là lịch sử trò chuyện gần nhất trong kênh (cũ nhất ở trên, mới nhất ở dưới):\n\n{chat_log}\n\nHãy tóm tắt lại cho tôi dưới dạng một bản tin hài hước!"
                
                response = self.client.models.generate_content(
                    model=config.GEMINI_MODEL_NAME,
                    contents=prompt,
                    config=config_options
                )
                return response.text
                
            answer = await loop.run_in_executor(None, process_summary)
            
            if len(answer) > 1950:
                answer = answer[:1950] + "...\n*(Bản tin quá dài đã bị cắt bớt)*"
                
            await msg.edit(content=f"📰 **Bản Tin Bổ Dưa Ayaka (Tin Tức Kênh)** 🌸\n\n{answer}")
            
        except Exception as e:
            logger.error(f"Lỗi RAG summary: {e}", exc_info=True)
            error_msg = str(e)
            if "503" in error_msg and "UNAVAILABLE" in error_msg:
                await msg.edit(content="❌ Băng thông kết nối tới máy chủ Google hiện đang quá tải (Lỗi 503). Cậu đợi một chút rồi thử lại nhé! 🌸")
            else:
                if len(error_msg) > 1000:
                    error_msg = error_msg[:1000] + "... (Lỗi quá dài)"
                await msg.edit(content=f"❌ Tớ gặp lỗi khi cố tóm tắt tin nhắn rồi: {error_msg}")

async def setup(bot):
    await bot.add_cog(RAGCog(bot))
