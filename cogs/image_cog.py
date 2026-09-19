import discord
from discord.ext import commands
import io
import asyncio
from PIL import Image, ImageFilter
try:
    from rembg import remove, new_session
    HAS_REMBG = True
except ImportError:
    HAS_REMBG = False
import logging

logger = logging.getLogger("AyakaImage")

class ImageCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def get_image_bytes(self, ctx):
        if not ctx.message.attachments:
            if ctx.message.reference and ctx.message.reference.resolved:
                ref_msg = ctx.message.reference.resolved
                if ref_msg.attachments:
                    return await ref_msg.attachments[0].read()
            await ctx.reply("❌ Cậu cần đính kèm một bức ảnh (hoặc Reply một bức ảnh) thì tớ mới xử lý được nhé!")
            return None
            
        attachment = ctx.message.attachments[0]
        if not attachment.content_type or not attachment.content_type.startswith('image/'):
            await ctx.reply("❌ Tập tin đính kèm không phải là ảnh hợp lệ!")
            return None
            
        return await attachment.read()

    @commands.command(name="rmbg", aliases=["removebg", "xoaphong"])
    async def remove_background(self, ctx, model: str = "human"):
        """
        Xóa phông nền ảnh tự động bằng AI (Rembg).
        Cậu có thể chọn model: 
        - u2net: Nhanh, tiêu chuẩn
        - human: Chuyên tách người (cosplay) - Mặc định
        - anime: Chuyên tách ảnh anime 2D
        - hq: Chất lượng cao nhất (rất chậm)
        - hq: Chất lượng cao nhất (rất chậm)
        """
        if not HAS_REMBG:
            await ctx.reply("❌ Rất tiếc, tính năng xóa phông nền AI (Rembg) tạm thời bị vô hiệu hóa do bộ nhớ của máy chủ đám mây miễn phí quá nhỏ (chỉ 512MB RAM), không đủ không gian để nạp lõi AI này.")
            return
            
        image_bytes = await self.get_image_bytes(ctx)
        if not image_bytes:
            return
            
        # Map user input to rembg session names
        model_map = {
            "u2net": "u2net",
            "human": "u2net_human_seg",
            "anime": "isnet-anime",
            "hq": "bria-rmbg"
        }
        
        session_name = model_map.get(model.lower(), "u2net_human_seg")
        
        # Gửi thông báo đang tải model nếu dùng model nặng
        msg = None
        if session_name in ["isnet-anime", "bria-rmbg"]:
            msg = await ctx.reply(f"⏳ Tớ đang nạp lõi AI `{session_name}` (có thể mất chút thời gian tải về lần đầu)...")

        async with ctx.typing():
            try:
                loop = asyncio.get_event_loop()
                
                def process_rmbg():
                    session = new_session(session_name)
                    return remove(image_bytes, session=session)

                output_bytes = await loop.run_in_executor(None, process_rmbg)
                
                result_file = discord.File(io.BytesIO(output_bytes), filename=f"ayaka_rmbg_{model}.png")
                
                if msg:
                    await msg.delete()
                await ctx.reply(f"✨ Tớ đã dùng bí thuật AI lõi `{session_name}` xóa phông ảnh giúp cậu rồi đây!", file=result_file)
            except Exception as e:
                logger.error(f"Lỗi xóa phông ({session_name}): {e}")
                if msg:
                    await msg.edit(content=f"❌ Xóa phông thất bại rồi cậu ạ: {e}")
                else:
                    await ctx.reply(f"❌ Xóa phông thất bại rồi cậu ạ: {e}")

    @commands.command(name="filter", aliases=["boloc"])
    async def apply_filter(self, ctx, filter_type: str = ""):
        """Áp dụng bộ lọc cho ảnh (blur, contour, emboss, bw)"""
        valid_filters = {
            "blur": ImageFilter.GaussianBlur(radius=5),
            "contour": ImageFilter.CONTOUR,
            "emboss": ImageFilter.EMBOSS,
            "bw": "L"  # Convert to Grayscale
        }
        
        filter_type = filter_type.lower()
        if filter_type not in valid_filters:
            await ctx.reply(f"🌸 Tớ hiện chỉ có các bộ lọc này thôi: `{', '.join(valid_filters.keys())}`\nVí dụ: `!filter blur`")
            return
            
        image_bytes = await self.get_image_bytes(ctx)
        if not image_bytes:
            return
            
        async with ctx.typing():
            try:
                loop = asyncio.get_event_loop()
                
                def process_image():
                    img = Image.open(io.BytesIO(image_bytes))
                    if filter_type == "bw":
                        img = img.convert("L")
                    else:
                        img = img.filter(valid_filters[filter_type])
                        
                    output = io.BytesIO()
                    img.save(output, format="PNG")
                    return output.getvalue()

                output_bytes = await loop.run_in_executor(None, process_image)
                
                result_file = discord.File(io.BytesIO(output_bytes), filename=f"ayaka_filter_{filter_type}.png")
                await ctx.reply(f"🎨 Đây là ảnh sau khi gắn bộ lọc **{filter_type}** nhé:", file=result_file)
            except Exception as e:
                logger.error(f"Lỗi filter ảnh: {e}")
                await ctx.reply(f"❌ Chỉnh ảnh thất bại: {e}")

async def setup(bot):
    await bot.add_cog(ImageCog(bot))
