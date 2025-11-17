#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PSD文件处理脚本 - 改进版
功能：
1. 递归删除所有文本图层（包括组内的）
2. 检测包含文字的图片图层并删除
3. 导出剩余图层为单独的图像文件
"""

import os
import sys
import argparse
import cv2
import numpy as np
from PIL import Image
import pytesseract
from psd_tools import PSDImage


def remove_text_layers_recursive(layer, parent=None, parent_layers=None, index=None):
    """
    递归删除所有文本图层
    
    Args:
        layer: 当前图层对象
        parent: 父图层对象
        parent_layers: 父图层的图层列表
        index: 当前图层在父图层列表中的索引
        
    Returns:
        bool: 如果图层被删除返回True
    """
    # 检查是否为文本图层
    if hasattr(layer, 'kind') and layer.kind == 'type':
        print(f"  删除文本图层: {layer.name}")
        return True
    
    # 如果是组图层,递归处理子图层
    if hasattr(layer, 'is_group') and layer.is_group():
        # 反向遍历以安全删除
        for i in range(len(layer) - 1, -1, -1):
            sub_layer = layer[i]
            if remove_text_layers_recursive(sub_layer, layer, layer._layers, i):
                # 删除子图层
                del layer._layers[i]
    
    return False


def collect_all_layers(layer, layers_list=None):
    """
    递归收集所有图层(包括组内的)
    
    Args:
        layer: 图层对象
        layers_list: 用于存储图层的列表
        
    Returns:
        list: 所有图层的列表
    """
    if layers_list is None:
        layers_list = []
    
    # 如果是组图层,递归处理
    if hasattr(layer, 'is_group') and layer.is_group():
        for sub_layer in layer:
            collect_all_layers(sub_layer, layers_list)
    else:
        # 底层图层,添加到列表
        layers_list.append(layer)
    
    return layers_list


def detect_text_in_image(image_data, layer_name):
    """
    使用多种方法检测图片中是否包含文字
    
    Args:
        image_data: PIL Image对象
        layer_name: 图层名称(用于日志)
        
    Returns:
        bool: 如果图片包含文字返回True
    """
    try:
        # 检查图像尺寸,太小的图像跳过
        if image_data.width < 10 or image_data.height < 10:
            print(f"    图像太小,跳过检测")
            return False
        
        # 将PIL Image转换为numpy数组
        img_array = np.array(image_data)
        
        # 处理不同的图像格式
        if len(img_array.shape) == 2:
            # 灰度图
            gray = img_array
        elif len(img_array.shape) == 3:
            if img_array.shape[2] == 4:
                # RGBA: 检查alpha通道,如果完全透明则跳过
                alpha = img_array[:, :, 3]
                if np.all(alpha == 0):
                    print(f"    图层完全透明,跳过")
                    return False
                # 转换为RGB
                img_array = cv2.cvtColor(img_array, cv2.COLOR_RGBA2RGB)
            # 转为灰度
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            print(f"    不支持的图像格式")
            return False
        
        # 方法1: 基础OCR检测
        print(f"    方法1: 标准OCR检测...")
        config1 = '--oem 3 --psm 11'
        text1 = pytesseract.image_to_string(gray, lang='chi_sim+eng', config=config1)
        
        # 方法2: 二值化后OCR检测
        print(f"    方法2: 二值化OCR检测...")
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        config2 = '--oem 3 --psm 6'  # PSM 6 = 假设有统一的文本块
        text2 = pytesseract.image_to_string(thresh, lang='chi_sim+eng', config=config2)
        
        # 方法3: 反色后检测(针对白底黑字或黑底白字)
        print(f"    方法3: 反色OCR检测...")
        inverted = cv2.bitwise_not(gray)
        text3 = pytesseract.image_to_string(inverted, lang='chi_sim+eng', config=config1)
        
        # 方法4: 边缘增强后检测
        print(f"    方法4: 边缘增强OCR检测...")
        edges = cv2.Canny(gray, 50, 150)
        dilated = cv2.dilate(edges, np.ones((3,3), np.uint8), iterations=1)
        text4 = pytesseract.image_to_string(dilated, lang='chi_sim+eng', config=config1)
        
        # 合并所有检测结果
        all_text = f"{text1} {text2} {text3} {text4}"
        
        # 过滤掉单个字符或特殊符号(容易误判)
        cleaned_text = ''.join(c for c in all_text if c.isalnum() or c.isspace())
        
        if cleaned_text.strip():
            # 统计有意义的字符数量
            meaningful_chars = ''.join(c for c in cleaned_text if not c.isspace())
            if len(meaningful_chars) >= 2:  # 至少2个字符才认为是文字
                preview = cleaned_text.strip()[:100]
                print(f"    ✓ 检测到文字({len(meaningful_chars)}字符): {preview}{'...' if len(cleaned_text.strip()) > 100 else ''}")
                return True
        
        print(f"    ✗ 未检测到文字")
        return False
        
    except Exception as e:
        print(f"    OCR检测出错: {str(e)}")
        return False


def find_and_mark_parent_groups(layer, target_layer, marked_groups):
    """
    查找并标记包含目标图层的所有父组
    
    Args:
        layer: 当前检查的图层
        target_layer: 要删除的目标图层
        marked_groups: 已标记的组集合
        
    Returns:
        bool: 如果找到目标图层返回True
    """
    if layer == target_layer:
        return True
    
    if hasattr(layer, 'is_group') and layer.is_group():
        for sub_layer in layer:
            if find_and_mark_parent_groups(sub_layer, target_layer, marked_groups):
                marked_groups.add(id(layer))
                return True
    
    return False


def remove_layer_from_tree(psd, layer_to_remove):
    """
    从PSD图层树中删除指定图层
    
    Args:
        psd: PSD对象
        layer_to_remove: 要删除的图层
        
    Returns:
        bool: 删除成功返回True
    """
    def remove_from_parent(parent):
        if not hasattr(parent, '_layers'):
            return False
        
        for i, child in enumerate(parent._layers):
            if child == layer_to_remove:
                del parent._layers[i]
                return True
            
            if hasattr(child, 'is_group') and child.is_group():
                if remove_from_parent(child):
                    return True
        
        return False
    
    return remove_from_parent(psd)


def process_psd(input_path, output_path, skip_ocr=False):
    """
    主处理函数
    
    Args:
        input_path: 输入PSD文件路径
        output_path: 输出图像路径
        skip_ocr: 是否跳过OCR检测(仅删除文本图层)
    """
    print(f"正在处理PSD文件: {input_path}")
    print(f"图像将保存至: {output_path}\n")
    
    # 读取PSD文件
    psd = PSDImage.open(input_path)
    print(f"PSD尺寸: {psd.width} x {psd.height}")
    print(f"顶层图层数: {len(psd)}\n")
    
    # 步骤1: 递归删除所有文本图层
    print("=" * 60)
    print("步骤1: 删除文本图层")
    print("=" * 60)
    text_layer_count = 0
    for i in range(len(psd) - 1, -1, -1):
        layer = psd[i]
        if remove_text_layers_recursive(layer, psd, psd._layers, i):
            del psd._layers[i]
            text_layer_count += 1
        else:
            # 递归处理组内的文本图层
            if hasattr(layer, 'is_group') and layer.is_group():
                for j in range(len(layer) - 1, -1, -1):
                    sub_layer = layer[j]
                    remove_text_layers_recursive(sub_layer, layer, layer._layers, j)
    
    print(f"\n文本图层删除完成,共删除 {text_layer_count} 个顶层文本图层\n")
    
    # 步骤2: 删除包含文字的图片图层
    if not skip_ocr:
        print("=" * 60)
        print("步骤2: 检测并删除包含文字的图片图层")
        print("=" * 60)
        
        # 收集所有底层图层
        all_layers = []
        for layer in psd:
            all_layers.extend(collect_all_layers(layer))
        
        print(f"共找到 {len(all_layers)} 个底层图层\n")
        
        # 检测包含文字的图片图层
        layers_to_remove = []
        for idx, layer in enumerate(all_layers, 1):
            if hasattr(layer, 'kind') and layer.kind == 'pixel':
                print(f"[{idx}/{len(all_layers)}] 检查图片图层: {layer.name}")
                
                try:
                    layer_image = layer.composite()
                    
                    if layer_image is not None:
                        if detect_text_in_image(layer_image, layer.name):
                            layers_to_remove.append(layer)
                            print(f"    >>> 标记为删除\n")
                        else:
                            print(f"    >>> 保留\n")
                    else:
                        print(f"    无法提取图像,跳过\n")
                        
                except Exception as e:
                    print(f"    处理出错: {str(e)}\n")
        
        # 删除标记的图层
        if layers_to_remove:
            print(f"正在删除 {len(layers_to_remove)} 个包含文字的图片图层...")
            removed_count = 0
            for layer in layers_to_remove:
                if remove_layer_from_tree(psd, layer):
                    print(f"  ✓ 已删除: {layer.name}")
                    removed_count += 1
                else:
                    print(f"  ✗ 删除失败: {layer.name}")
            print(f"成功删除 {removed_count} 个图层\n")
        else:
            print("未发现包含文字的图片图层\n")
    else:
        print("\n跳过OCR检测(使用 --skip-ocr 参数)\n")
    
    # 步骤3: 导出各个图层
    print("=" * 60)
    print("步骤3: 导出各个图层")
    print("=" * 60)
    
    # 创建输出目录
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 收集所有剩余的图层
    remaining_layers = []
    for layer in psd:
        remaining_layers.extend(collect_all_layers(layer))
    
    print(f"共找到 {len(remaining_layers)} 个剩余图层\n")
    
    # 逐个导出图层
    exported_count = 0
    for idx, layer in enumerate(remaining_layers, 1):
        print(f"[{idx}/{len(remaining_layers)}] 导出图层: {layer.name}")
        
        try:
            # 使用图层的composite方法生成图像
            layer_image = layer.composite()
            
            if layer_image is not None:
                # 生成输出文件路径
                # 移除文件扩展名并添加图层索引和名称
                base_name = os.path.splitext(os.path.basename(output_path))[0]
                layer_name_safe = "".join(c for c in layer.name if c.isalnum() or c in (' ', '-', '_')).rstrip()
                layer_output_path = os.path.join(output_dir, f"{base_name}_layer_{idx}_{layer_name_safe}.png")
                
                # 保存图像
                layer_image.save(layer_output_path)
                file_size = os.path.getsize(layer_output_path) / 1024
                print(f"  ✓ 图层图像已保存: {layer_output_path} ({file_size:.2f} KB)")
                exported_count += 1
            else:
                print(f"  ✗ 无法生成图层图像")
                
        except Exception as e:
            print(f"  ✗ 导出图层出错: {str(e)}")
    
    print(f"\n成功导出 {exported_count} 个图层图像")
    
    print("\n" + "=" * 60)
    print("处理完成!")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description='处理PSD文件,移除文本图层和包含文字的图片图层',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 基本用法
  python3 process_psd.py input.psd output_dir/
  
  # 仅删除文本图层,跳过OCR检测
  python3 process_psd.py input.psd output_dir/ --skip-ocr
        """
    )
    parser.add_argument('input', help='输入PSD文件路径')
    parser.add_argument('output', help='输出目录路径')
    parser.add_argument('--skip-ocr', action='store_true', 
                       help='跳过OCR检测,仅删除文本图层')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        print(f"错误: 输入文件 {args.input} 不存在")
        sys.exit(1)
    
    # 确保输出路径是目录
    if not os.path.exists(args.output):
        os.makedirs(args.output)
    elif not os.path.isdir(args.output):
        print(f"错误: 输出路径 {args.output} 必须是目录")
        sys.exit(1)
    
    # 生成输出文件的基本名称
    input_name = os.path.splitext(os.path.basename(args.input))[0]
    output_file = os.path.join(args.output, f"{input_name}_layer.png")
    
    process_psd(args.input, output_file, args.skip_ocr)


if __name__ == "__main__":
    main()