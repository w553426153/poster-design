import json
import os
import urllib.parse
from oss import Upload

def parse_templates_json(json_file_path):
    """解析templates.json文件，提取所有image_url路径"""
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    image_urls = []
    templates = data.get('templates', [])
    
    for template in templates:
        # data字段是JSON字符串，需要再次解析
        template_data = json.loads(template.get('data', '[]'))
        
        # 根据实际结构，template_data是一个包含单个字典的列表，字典有global和layers键
        layers = []
        if isinstance(template_data, list) and len(template_data) > 0:
            # 第一个元素是包含global和layers的字典
            first_element = template_data[0]
            if isinstance(first_element, dict):
                layers = first_element.get('layers', [])
        elif isinstance(template_data, dict):
            # 如果是字典格式，直接获取layers
            layers = template_data.get('layers', [])
        
        # 遍历layers中的所有元素
        for layer in layers:
            if layer.get('type') == 'w-image':
                image_url = layer.get('image_url')
                img_url = layer.get('imgUrl')
                if image_url:
                    image_urls.append({
                        'image_url': image_url,
                        'img_url': img_url,
                        'layer_uuid': layer.get('uuid')
                    })
    
    return image_urls

def get_local_file_path(image_url):
    """根据image_url获取本地文件路径"""
    # 解码URL编码的路径
    decoded_path = urllib.parse.unquote(image_url)
    # 构建完整的本地文件路径
    local_file_path = os.path.join('/Users/xiaojiazi1/poster-design/back_end/uploads', decoded_path)
    return local_file_path

def upload_images_to_oss(image_urls):
    """上传图片到OSS并返回新的URL映射"""
    uploader = Upload()
    url_mapping = {}
    uploaded_files = {}  # 存储已上传文件的映射关系 {local_path: oss_url}
    
    # 收集所有唯一的目录路径
    directory_paths = set()
    for item in image_urls:
        image_url = item['image_url']
        local_file_path = get_local_file_path(image_url)
        directory_path = os.path.dirname(local_file_path)
        directory_paths.add(directory_path)
    
    # 上传每个目录中的所有图片，并记录映射关系
    for directory_path in directory_paths:
        if os.path.exists(directory_path):
            print(f"上传目录中的图片: {directory_path}")
            # 上传目录中的所有图片
            oss_urls = uploader.upload_directory_images_multithreaded(directory_path, 'image/template_images')
            print(f"目录 {directory_path} 上传完成，成功上传 {len(oss_urls)} 个文件")
            
            # 记录该目录下所有文件的映射关系
            for file_name in os.listdir(directory_path):
                local_file_path = os.path.join(directory_path, file_name)
                # 构造OSS URL（基于上传逻辑）
                oss_url = f"https://obsv3.cn-lflt-1.enncloud.cn/ennova-bigdata-test/image/template_images/{file_name}"
                uploaded_files[local_file_path] = oss_url
        else:
            print(f"目录不存在: {directory_path}")
    
    # 建立原始imgUrl到新OSS URL的映射关系
    for item in image_urls:
        image_url = item['image_url']
        local_file_path = get_local_file_path(image_url)
        
        if os.path.exists(local_file_path):
            if local_file_path in uploaded_files:
                oss_url = uploaded_files[local_file_path]
                url_mapping[item['img_url']] = oss_url
                print(f"映射: {item['img_url']} -> {oss_url}")
            else:
                print(f"文件未上传成功: {local_file_path}")
        else:
            print(f"文件不存在: {local_file_path}")
    
    return url_mapping

def replace_image_urls_in_json(json_file_path, url_mapping, output_file_path):
    """替换JSON中的图片URL并保存到新文件"""
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    templates = data.get('templates', [])
    
    for template in templates:
        # data字段是JSON字符串，需要再次解析
        template_data = json.loads(template.get('data', '[]'))
        
        # 根据实际结构，template_data是一个包含单个字典的列表，字典有global和layers键
        layers = []
        first_element = None
        if isinstance(template_data, list) and len(template_data) > 0:
            # 第一个元素是包含global和layers的字典
            first_element = template_data[0]
            if isinstance(first_element, dict):
                layers = first_element.get('layers', [])
        elif isinstance(template_data, dict):
            # 如果是字典格式，直接获取layers
            first_element = template_data
            layers = template_data.get('layers', [])
        
        # 遍历layers中的所有元素
        for layer in layers:
            if layer.get('type') == 'w-image':
                old_img_url = layer.get('imgUrl')
                if old_img_url in url_mapping:
                    layer['imgUrl'] = url_mapping[old_img_url]
        
        # 更新template_data中的layers
        if isinstance(template_data, list) and len(template_data) > 0:
            # 如果是列表格式，更新第一个元素中的layers
            if isinstance(template_data[0], dict):
                template_data[0]['layers'] = layers
        elif isinstance(template_data, dict):
            # 如果是字典格式，直接更新layers
            template_data['layers'] = layers
        
        # 更新template的data字段
        template['data'] = json.dumps(template_data, ensure_ascii=False)
    
    # 保存到新文件
    with open(output_file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"已保存更新后的JSON到: {output_file_path}")

def main():
    json_file_path = '/Users/xiaojiazi1/poster-design/back_end/app/data/templates.json'
    output_file_path = '/Users/xiaojiazi1/poster-design/back_end/app/data/templates_updated.json'
    
    # 解析JSON文件，提取image_url路径
    image_urls = parse_templates_json(json_file_path)
    print(f"找到 {len(image_urls)} 个图片URL")
    
    # 上传图片到OSS
    url_mapping = upload_images_to_oss(image_urls)
    print(f"成功建立 {len(url_mapping)} 个URL映射")
    
    # 替换JSON中的图片URL并保存到新文件
    replace_image_urls_in_json(json_file_path, url_mapping, output_file_path)
    print("处理完成！")

if __name__ == "__main__":
    main()