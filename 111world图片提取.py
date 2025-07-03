import os
from docx import Document

def extract_images_from_docx(docx_path, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    try:
        doc = Document(docx_path)
    except Exception as e:
        print(f"无法打开文档: {e}")
        return

    rels = doc.part.rels

    for rel in rels:
        if "image" in rels[rel].target_ref:
            img = rels[rel].target_part.blob
            img_name = os.path.basename(rels[rel].target_ref)
            img_path = os.path.join(output_folder, img_name)
            with open(img_path, "wb") as f:
                f.write(img)
            print(f"Extracted {img_name} to {img_path}")

def main():
    docx_path = input("请输入Word文档的路径: ").strip().strip('“”')  # 用户输入Word文档路径并过滤中文双引号
    output_folder = 'C:\\Users\\联想\\Desktop\\原图'  # 固定输出文件夹路径
    
    extract_images_from_docx(docx_path, output_folder)

if __name__ == "__main__":
    main()