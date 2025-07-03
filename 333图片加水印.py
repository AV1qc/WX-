import os
from PIL import Image

def resize_image(image, target_width, target_height):
    width, height = image.size
    if width > height:
        # 横图
        new_width = target_width
        new_height = int(target_width * height / width)
    else:
        # 竖图
        new_height = target_height
        new_width = int(target_height * width / height)
    return image.resize((new_width, new_height), Image.LANCZOS)

def resize_watermark(watermark, base_image):
    base_width, base_height = base_image.size
    max_width = base_width // 5
    max_height = base_height // 5

    watermark_width, watermark_height = watermark.size
    if watermark_width > max_width or watermark_height > max_height:
        ratio = min(max_width / watermark_width, max_height / watermark_height)
        new_width = int(watermark_width * ratio)
        new_height = int(watermark_height * ratio)
        watermark = watermark.resize((new_width, new_height), Image.LANCZOS)
    return watermark

def add_watermark(image, watermark):
    watermark = resize_watermark(watermark, image)
    watermark = watermark.convert("RGBA")
    image = image.convert("RGBA")
    
    # 获取图片和水印的尺寸
    image_width, image_height = image.size
    watermark_width, watermark_height = watermark.size
    
    # 计算水印的位置
    position = (image_width - watermark_width, image_height - watermark_height)
    
    # 添加水印
    transparent = Image.new('RGBA', (image_width, image_height), (0, 0, 0, 0))
    transparent.paste(image, (0, 0))
    transparent.paste(watermark, position, mask=watermark)
    return transparent.convert("RGB")

def process_images(input_folder, output_folder, watermark_path):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    try:
        watermark = Image.open(watermark_path)
    except Exception as e:
        print(f"无法打开水印图片: {e}")
        return
    
    for filename in os.listdir(input_folder):
        if filename.lower().endswith(('png', 'jpg', 'jpeg', 'bmp', 'gif')):
            image_path = os.path.join(input_folder, filename)
            try:
                image = Image.open(image_path)
            except Exception as e:
                print(f"无法打开图片 {filename}: {e}")
                continue
            
            # 调整图片大小
            resized_image = resize_image(image, 700, 600)
            
            # 添加水印
            watermarked_image = add_watermark(resized_image, watermark)
            
            # 保存处理后的图片
            output_path = os.path.join(output_folder, filename)
            watermarked_image.save(output_path)
            print(f'输出 {filename}')

def main():
    input_folder = 'C:\\Users\\联想\\Desktop\\原图'  # 固定输入文件夹路径
    output_folder = 'C:\\Users\\联想\\Desktop\\批处理照片'  # 固定输出文件夹路径
    watermark_path = 'F:\\视频包装\\大众网、海报新闻单独LOGO\\2023.4水印\\彩色图标.png'  # 固定水印图片路径
    
    process_images(input_folder, output_folder, watermark_path)

if __name__ == "__main__":
    main()