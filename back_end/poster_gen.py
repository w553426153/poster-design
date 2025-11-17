from __future__ import print_function

import os
import logging
import json
from typing import List, Optional, Dict, Any
from volcengine import visual
from volcengine.visual.VisualService import VisualService
from fastapi import FastAPI, HTTPException

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


SUCCESS_CODE = 0
ERROR_CODE = -1

VOLC_AK = os.environ.get('VOLC_AK', 'AKLTOTE4YWYwZjk1ZDA2NDUzZWE5ODQ0OWU0N2NhNGEwZDA')
VOLC_SK = os.environ.get('VOLC_SK', 'TVdNelpUVmhOV1kyTlRabU5EUTNNR0ZsWkRRMFptRTBPVFEwTlRjd1ltVQ==')


def get_poster(task_id: str, max_retries: int = 20) -> Dict[str, Any]:
    """
    根据任务ID获取生成的海报图片URLs，支持轮询查询任务状态
    
    Args:
        task_id: 任务ID
        max_retries: 最大重试次数，默认为20次（约300s）
    
    Returns:
        Dict: 包含状态码、消息和数据的标准化响应
    """
    import time
    
    try:
        # 参数验证
        if not task_id or not isinstance(task_id, str):
            return {
                "code": ERROR_CODE,
                "message": "任务ID不能为空且必须为字符串",
                "data": None
            }
        
        visual_service = VisualService()
        
        # 使用环境变量中的API密钥
        visual_service.set_ak(VOLC_AK)
        visual_service.set_sk(VOLC_SK)
        
        # 请求Body
        form = {
            "req_key": "jimeng_t2i_v40",
            "task_id": task_id,
            "req_json": json.dumps({
                "logo_info": {
                    "add_logo": False,
                    "position": 0,
                    "language": 0,
                    "opacity": 1,
                    "logo_text_content": "这里是明水印内容"
                },
                "return_url": True
            })
        }
        
        retries = 0
        while retries < max_retries:
            logger.info(f"开始获取海报，任务ID: {task_id}，第 {retries + 1}/{max_retries} 次查询")
            resp = visual_service.cv_sync2async_get_result(form)
            logger.debug(f"API响应: {resp}")
            
            # 检查API响应状态
            if resp.get("ResponseMetadata", {}).get("Error"):
                error = resp["ResponseMetadata"]["Error"]
                logger.error(f"获取海报失败: {error.get('Code')} - {error.get('Message')}")
                return {
                    "code": ERROR_CODE,
                    "message": f"API错误: {error.get('Message')}",
                    "data": None
                }
            
            # 获取任务状态
            data = resp.get("data", {})
            status = data.get("status", "")
            logger.info(f"任务状态: {status}")
            
            # 处理不同的任务状态
            if status == "done":
                # 任务完成，直接检查是否有image_urls
                image_urls = data.get("image_urls", [])
                if image_urls:
                    logger.info(f"成功获取海报，图片URLs数量: {len(image_urls)}, 图片URLs: {image_urls}")
                    return {
                        "code": SUCCESS_CODE,
                        "message": "任务处理完成",
                        "data": {
                            "image_urls": image_urls,
                            "status": "done"
                        }
                    }
                else:
                    # 没有image_urls，认为任务失败
                    message = resp.get("message", "任务处理失败但未返回错误信息")
                    logger.error(f"任务处理失败: {message}")
                    return {
                        "code": ERROR_CODE,
                        "message": f"任务处理失败: {message}",
                        "data": {
                            "status": "done"
                        }
                    }
            
            elif status == "in_queue" or status == "generating":
                # 任务排队中或处理中，等待10秒后重试
                wait_time = 15
                logger.info(f"任务{status}，等待{wait_time}秒后重试")
                time.sleep(wait_time)
                retries += 1
            
            elif status == "not_found":
                # 任务未找到
                logger.error("任务未找到，可能原因是无此任务或任务已过期(12小时)")
                return {
                    "code": ERROR_CODE,
                    "message": "任务未找到，可能原因是无此任务或任务已过期(12小时)",
                    "data": {
                        "status": "not_found"
                    }
                }
            
            elif status == "expired":
                # 任务已过期
                logger.error("任务已过期，请尝试重新提交任务请求")
                return {
                    "code": ERROR_CODE,
                    "message": "任务已过期，请尝试重新提交任务请求",
                    "data": {
                        "status": "expired"
                    }
                }
            
            else:
                # 未知状态
                logger.warning(f"未知任务状态: {status}")
                return {
                    "code": ERROR_CODE,
                    "message": f"未知任务状态: {status}",
                    "data": {
                        "status": status
                    }
                }
        
        # 超过最大重试次数
        logger.error("超过最大重试次数，任务仍在处理中")
        return {
            "code": ERROR_CODE,
            "message": "任务处理超时，请稍后重试",
            "data": None
        }
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON解析错误: {str(e)}")
        return {
            "code": ERROR_CODE,
            "message": f"JSON解析错误: {str(e)}",
            "data": None
        }
    except Exception as e:
        logger.error(f"获取海报失败: {str(e)}")
        return {
            "code": ERROR_CODE,
            "message": f"服务异常或未知错误: {str(e)}",
            "data": None
        }




def generate_poster_pic2pic(query: str, image_urls: List[str], gen_num: int = 2) -> Dict[str, Any]:
    """
    根据参考图片生成海报
    
    Args:
        query: 用户需求描述
        image_urls: 参考图片URL列表，最多10张
        gen_num: 生成图片数量
    
    Returns:
        Dict: 包含状态码、消息和任务ID的标准化响应
    """
    try:
        # 参数验证
        if not query or not isinstance(query, str):
            return {
                "code": ERROR_CODE,
                "message": "生成内容不能为空且必须为字符串",
                "data": None
            }
        
        if not isinstance(image_urls, list) or not image_urls:
            return {
                "code": ERROR_CODE,
                "message": "图片URL列表不能为空且必须为列表格式",
                "data": None
            }
        
        if len(image_urls) > 10:
            return {
                "code": ERROR_CODE,
                "message": "图片URL数量不能超过10张",
                "data": None
            }
        
        if not all(isinstance(url, str) and url for url in image_urls):
            return {
                "code": ERROR_CODE,
                "message": "图片URL必须为非空字符串",
                "data": None
            }
        
        if not isinstance(gen_num, int) or gen_num < 1 or gen_num > 15:
            return {
                "code": ERROR_CODE,
                "message": "生成图片数量必须为1-15之间的整数",
                "data": None
            }
        
        visual_service = VisualService()
        
        # 使用环境变量中的API密钥
        visual_service.set_ak(VOLC_AK)
        visual_service.set_sk(VOLC_SK)
        
        prompt_pic2pic = f"""
# 任务
根据提供的图片数量和类型，选择相应的任务模式：

## 如果仅提供一张图片（背景图）
- 在保持原背景图完全不变的前提下，基于用户的需求生成完整的旅游海报。
- 限制：
 - 所有文字内容必须完整显示，无断行、无截断。
 - 禁止生成任何未在"文字内容"中提供的额外文案。
 - 若无合适留白放置文字，可以进行背景模糊处理，但严格禁止使用抹白背景的方式。
 - 确保字体与排版风格的一致性。

## 如果提供了两张图片且用户的意图为参考[参考图]的字体
- 以第一张图作为字体模板，第二张图为背景图，生成新的海报内容。
- 图片内容：[参考图：默认图1] [背景图：默认图2]
- 参考项：[参考排版]
- 限制：
 - 禁止修改背景图，在保证其不变的基础上生成新的海报。
 - 除用户输入的文字外，严禁生成其他重复的文字。

## 如果提供了两张图片且用户的意图为参考[参考图]的排版
- 以第一张图作为版式模板，第二张图为背景图，生成新的海报内容。
- 图片内容：[参考图：默认图1] [背景图：默认图2]
- 参考项：[参考排版]
- 限制：
 - 禁止修改背景图，在保证其不变的基础上生成新的海报。
 - 文字需要有新设计，禁止与参考图一模一样。

## 如果提供了两张图片且用户的意图为全部参考[参考图]
- 根据提供的文字，基于参考图的版式与风格，将新文案融入其中，生成一张在布局、风格和质感上都与原图高度一致的设计。
- 图片内容：[参考图：图1][背景图：图2]
- 限制：
 - 版式还原：严格按照参考图排版、文字样式进行复刻。
 - 字体风格模仿：主标题及副标题/正文需使用与参考图相匹配的字体风格。
 - 色彩与质感应用：分析参考图的色彩搭配逻辑，严格按照该逻辑为本设计配色。
 - 背景与融合：禁止修改背景图。

# 用户的需求：
{query}

# 要求：对于以上每种情况，请确保：
- 所有文字内容必须完整显示，无断行、无截断。
- 生成的内容排版美观、协调，文字可读性强。
- 生成数量为"{gen_num}"。
"""

        form = {
            "req_key": "jimeng_t2i_v40",
            "image_urls": image_urls,
            "prompt": prompt_pic2pic,
        }
        
        
        logger.info(f"开始生成海报，图片数量: {len(image_urls)}, 生成数量: {gen_num}")
        resp = visual_service.cv_sync2async_submit_task(form)
        logger.debug(f"API响应: {resp}")
        
        # 检查API响应状态
        if resp.get("ResponseMetadata", {}).get("Error"):
            error = resp["ResponseMetadata"]["Error"]
            logger.error(f"生成海报失败: {error.get('Code')} - {error.get('Message')}")
            return {
                "code": ERROR_CODE,
                "message": f"API错误: {error.get('Message')}",
                "data": None
            }
        
        task_id = resp.get("data", {}).get("task_id")
        logger.info(f"成功提交海报生成任务，任务ID: {task_id}")
        logger.info(f"开始轮询任务状态，任务ID: {task_id}")
        # 轮询任务状态
        result = get_poster(task_id)
        
        
        return result
        
    except Exception as e:
        logger.error(f"生成海报失败: {str(e)}")
        return {
            "code": ERROR_CODE,
            "message": f"服务异常或未知错误: {str(e)}",
            "data": None
        }


def generate_poster_text2pic(query: str,gen_num: int = 2) -> Dict[str, Any]:
    """
    根据文字描述生成海报
    
    Args:
        query: 用户需求描述
        image_urls: 参考图片URL列表（可选），最多10张
        gen_num: 生成图片数量
    
    Returns:
        Dict: 包含状态码、消息和任务ID的标准化响应
    """
    try:
        # 参数验证
        if not query or not isinstance(query, str):
            return {
                "code": ERROR_CODE,
                "message": "查询内容不能为空且必须为字符串",
                "data": None
            }
        
        # 限制prompt长度不超过800字符
        if len(query) > 800:
            return {
                "code": ERROR_CODE,
                "message": "查询内容长度不能超过800字符",
                "data": None
            }
        
        # 验证图片URL列表
        
        
        if not isinstance(gen_num, int) or gen_num < 1 or gen_num > 15:
            return {
                "code": ERROR_CODE,
                "message": "生成图片数量必须为1-15之间的整数",
                "data": None
            }
        
        visual_service = VisualService()
        
        # 使用环境变量中的API密钥
        visual_service.set_ak(VOLC_AK)
        visual_service.set_sk(VOLC_SK)
        
        prompt_text2pic = f"""
# 任务
根据提供的文字内容，生成相应的旅游海报。

## 输入
{query}

## 输出
- 生成的内容排版美观、协调，文字可读性强。
- 生成数量为"{gen_num}"。
"""
        
        form = {
            "req_key": "jimeng_t2i_v40",
            "prompt": prompt_text2pic,
            "force_single": gen_num == 2  # 根据API文档，强制生成单图
        }
        

        
        logger.info(f"开始文本生成海报，生成数量: {gen_num}")
        resp = visual_service.cv_sync2async_submit_task(form)
        logger.debug(f"API响应: {resp}")
        
        # 检查API响应状态
        if resp.get("ResponseMetadata", {}).get("Error"):
            error = resp["ResponseMetadata"]["Error"]
            logger.error(f"生成海报失败: {error.get('Code')} - {error.get('Message')}")
            return {
                "code": ERROR_CODE,
                "message": f"API错误: {error.get('Message')}",
                "data": None
            }
        
        task_id = resp.get("data", {}).get("task_id")
        logger.info(f"成功提交文本生成海报任务，任务ID: {task_id}")
        result = get_poster(task_id)
        return result
        
    except Exception as e:
        logger.error(f"生成海报失败: {str(e)}")
        return {
            "code": ERROR_CODE,
            "message": f"服务异常或未知错误: {str(e)}",
            "data": None
        }



if __name__ == '__main__':
    # 示例调用 - 生成海报
    query = "请参考第一张图片给我生成海报"
    image_urls = [
        "https://tx.enn.cn/group1/M00/1B/70/CiaAUmkT7mKAKi1QAAjOMkosZis765.jpg",
        "https://tx.enn.cn/group1/M00/1B/70/CiaAUmkT7lKASU8VAAFSfujcKGQ855.jpg",
    ]
    result = generate_poster_pic2pic(query, image_urls)
    # logger.info(f"生成海报结果: {result}")
    
    
    # result = get_poster("7697497273201260787")
    # logger.info(f"获取海报结果: {result}")
    
    
    # text_query = "创建一个展示美丽海滩的旅游海报，包含'夏日度假'的主题"
    # text_result = generate_poster_text2pic(text_query, gen_num=1)
    # logger.info(f"文本生成海报结果: {text_result}")