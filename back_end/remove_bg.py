from rembg import remove
from PIL import Image

# 打开输入图片
input_path = "/Users/xiaojiazi1/Downloads/产品 2.webp"
output_path = "output.png"

with open(input_path, "rb") as i:
    with open(output_path, "wb") as o:
        input_image = i.read()
        output_image = remove(input_image)  # 自动去除背景
        o.write(output_image)

print("抠图完成！")