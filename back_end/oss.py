import json
import time
import os
import subprocess
import requests
from tqdm import tqdm
from urllib.parse import urlparse
from obs import ObsClient
from requests.exceptions import RequestException
from concurrent.futures import ThreadPoolExecutor, as_completed

# 设置环境变量，已有 的video上传的key_id跟 key
os.environ['HWY_ACCESS_KEY_ID'] = 'LVDAJYX7TQFC5IUQCRIT'
os.environ['HWY_SECRET_ACCESS_KEY'] = 'JaR1memzVRUZnTk6ofSeB1JTSr4jHvgvWcwLrBSV'
os.environ['HWY_SCOPE'] = 'cn-lflt-1; cn-nmyd-1'
BASE_SERVER_URL = 'https://obsv3.cn-lflt-1.enncloud.cn'

# BASE_SAVE_PATH = 'image/poi_search'
BASE_SAVE_PATH = 'video/model/wj'
BASE_BUCKET_NAME = 'ennova-bigdata-test'
# BASE_BUCKET_NAME = 'ennova-bigdata-prod'

FILE_LOCAL_PATH = os.path.join(os.path.dirname(__file__), 'imgs')


class Upload:

    def download_file(self, url, overwrite=False, type='video'):
        """
            文件下载
            优先使用 wget，如果没有安装 wget 使用 requests
            :param url: 文件源地址 url
            :param overwrite: 如果目标文件存在是否覆盖
            :return: 上传文件成功后的 地址
        """
        # 创建目录
        file_name = url.split('/')[-1].split('?')[0]  # 去掉文件名中的问号（如果有）
        file_path = os.path.join(FILE_LOCAL_PATH, file_name)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        # 检查文件是否存在
        if os.path.exists(file_path) and not overwrite:
            # log.info(f"文件已存在  {file_path}")
            return file_path
        else:
              # log.info(f"文件不存在，准备下载: {url} -> {file_path}")
            try:
                # wget命令 下载
                subprocess.run(['which', 'wget'], check=True, stdout=subprocess.PIPE)
                # log.info(f"有wget 命令，使用 有wget 下载: {url} ")
                local_file_path = self.download_file_with_wget(url, file_path)
            except subprocess.CalledProcessError:
                # requests 下载
                # log.info(f"无wget 命令，使用 requests 下载: {url} ")
                local_file_path = self.download_file_with_request(url, file_path)
            return local_file_path

    def upload_file(self, file_path, remote_path):
        """
        上传单个文件到oss
        :param file_path: 文件路径
        :param remote_path: 远程存储路径
        :return: 上传obs成功后的url地址
        """
        obs_client, mybucket = self.get_connection_bucket()
        if file_path is None or not os.path.exists(file_path) or obs_client is None or mybucket is None:
            return None
        try:
            start_time = time.time()
            file_name = os.path.basename(file_path)
            base_name, ext = os.path.splitext(file_name)
            print(f'file_name: {file_name} and file_path: {file_path} and new_file_name: {base_name}{ext}')
            object_key = os.path.join(remote_path, f'{base_name}{ext}')
            upload_params = {}
            upload_params['headers'] = {
                    'x-obs-expires': 1
                }
            with open(file_path, 'rb') as f:
                resp = obs_client.putFile(BASE_BUCKET_NAME, object_key, file_path,**upload_params)
                if resp.status < 300:
                    obs_img_url = resp.body.objectUrl
                    print((f"文件上传成功: {json.dumps(resp)}\n  "
                           f"oss_img_url: {obs_img_url}\n "
                           f"cost_time ：{time.time() - start_time}"))
                    return obs_img_url
                else:
                    print(f"文件上传失败: {json.dumps(resp)}")
                    return None
        except Exception as e:
            print(f"上传文件时出错: {e}")
            return None

    def get_connection_bucket(self):
        """
        连接 bucket
        :return: bucket 对象
        """
        access_key_id = os.environ['HWY_ACCESS_KEY_ID']
        secret_access_key = os.environ['HWY_SECRET_ACCESS_KEY']
        obs_client = ObsClient(access_key_id=access_key_id, secret_access_key=secret_access_key,
                               server=BASE_SERVER_URL)
        mybucket = None
        try:
            # 尝试获取 Bucket，如果不存在则创建
            mybucket = obs_client.getBucketAcl(BASE_BUCKET_NAME)
        except Exception as e:
            print(f"获取Bucket时出错: {e}")
        return obs_client, mybucket

    def upload_directory_jpgs_multithreaded(self, directory_path, remote_path=BASE_SAVE_PATH, max_workers=5):
        """
        多线程上传指定目录下的所有JPG文件到OSS

        参数:
        directory_path: 包含JPG文件的目录路径
        remote_path: OSS上的远程存储路径
        max_workers: 最大线程数

        返回:
        包含所有成功上传的JPG文件的OSS URL列表
        """
        if not os.path.exists(directory_path) or not os.path.isdir(directory_path):
            print(f"目录不存在或不是有效目录: {directory_path}")
            return []

        # 获取目录中的所有JPG文件
        jpg_files = []
        for file in os.listdir(directory_path):
            file_path = os.path.join(directory_path, file)
            if os.path.isfile(file_path):
                _, ext = os.path.splitext(file)
                if ext.lower() == '.jpg':
                    jpg_files.append(file_path)

        if not jpg_files:
            print(f"目录中没有找到JPG文件: {directory_path}")
            return []

        print(f"在目录中找到 {len(jpg_files)} 个JPG文件")

        # 存储成功上传的OSS URL
        oss_urls = []

        # 使用线程池并发上传
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有上传任务
            future_to_file = {
                executor.submit(self.upload_file, file_path, remote_path): file_path
                for file_path in jpg_files
            }

            # 处理上传结果
            for future in tqdm(as_completed(future_to_file), total=len(future_to_file), desc="上传进度"):
                file_path = future_to_file[future]
                try:
                    oss_url = future.result()
                    if oss_url:
                        oss_urls.append(oss_url)
                        print(f"文件上传成功: {os.path.basename(file_path)} -> {oss_url}")
                    else:
                        print(f"文件上传失败: {os.path.basename(file_path)}")
                except Exception as e:
                    print(f"上传文件时出错 {os.path.basename(file_path)}: {e}")

        print(f"所有JPG文件上传完成，成功上传 {len(oss_urls)}/{len(jpg_files)} 个文件")
        return oss_urls

    def list_files_in_directory(self, remote_directory_path):
        """
        查询OSS服务器内特定位置文件夹下的文件名及对应URL

        参数:
        remote_directory_path: OSS上的远程目录路径

        返回:
        包含文件名和对应URL的字典列表
        """
        obs_client, mybucket = self.get_connection_bucket()
        if obs_client is None or mybucket is None:
            print("无法连接到OSS Bucket")
            return []

        try:
            # 确保目录路径以 '/' 结尾
            if not remote_directory_path.endswith('/'):
                remote_directory_path += '/'

            # 列出目录下的所有对象
            resp = obs_client.listObjects(BASE_BUCKET_NAME, prefix=remote_directory_path)

            if resp.status < 300:
                file_list = []
                for obj in resp.body.contents:
                    # 获取文件名(不含路径)
                    file_name = os.path.basename(obj.key)
                    # 跳过目录本身
                    if file_name:
                        # 构造完整URL
                        file_url = f"{BASE_SERVER_URL}/{BASE_BUCKET_NAME}/{obj.key}"
                        file_list.append({
                            "file_name": file_name,
                            "file_url": file_url
                        })
                print(f"成功获取目录 {remote_directory_path} 下的 {len(file_list)} 个文件")
                return file_list
            else:
                print(f"查询目录失败: {json.dumps(resp)}")
                return []
        except Exception as e:
            print(f"查询目录时出错: {e}")
            return []

    def get_video_cover(self, video_url, cover_remote_path=None, frame_time='00:00:01'):
        """
        获取视频的封面图并上传到OSS

        参数:
        video_url: 视频的URL地址
        cover_remote_path: 封面图在OSS上的存储路径，默认为视频所在目录下的covers文件夹
        frame_time: 提取封面的时间点，格式为'HH:MM:SS'，默认为第1秒

        返回:
        封面图的OSS URL，如果失败则返回None
        """
        # 下载视频文件
        video_path = self.download_file(video_url, type='video')
        if not video_path:
            print("视频下载失败")
            return None

        try:
            # 检查是否安装了ffmpeg
            subprocess.run(['which', 'ffmpeg'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # 提取视频文件名和目录
            video_filename = os.path.basename(video_path)
            video_basename = os.path.splitext(video_filename)[0]
            cover_filename = f"{video_basename}_cover.jpg"
            cover_path = os.path.join(FILE_LOCAL_PATH, cover_filename)

            # 使用ffmpeg提取封面帧
            print(f"正在从视频中提取封面帧: {video_path}")
            subprocess.run([
                'ffmpeg', '-i', video_path, '-ss', frame_time, '-vframes', '1',
                '-q:v', '2', cover_path
            ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # 确定封面图的远程存储路径
            if not cover_remote_path:
                # 解析视频URL，获取其在OSS上的路径
                parsed_url = urlparse(video_url)
                path_parts = parsed_url.path.split('/')
                # 去掉bucket名称和文件名，获取目录路径
                if len(path_parts) >= 3:
                    video_dir = '/'.join(path_parts[2:-1])
                    cover_remote_path = os.path.join(video_dir, 'covers')
                else:
                    cover_remote_path = 'video/covers'

            # 上传封面图
            cover_url = self.upload_file(cover_path, cover_remote_path)

            # 清理临时文件
            if os.path.exists(cover_path):
                os.remove(cover_path)
            if os.path.exists(video_path):
                os.remove(video_path)

            return cover_url
        except subprocess.CalledProcessError as e:
            print(f"ffmpeg命令执行失败: {e}")
            print("请确保已安装ffmpeg工具")
            return None
        except Exception as e:
            print(f"获取视频封面时出错: {e}")
            return None

    


if __name__ == '__main__':
    # 示例1：使用多线程上传JPG文件
    # upload = Upload()
    # jpg_directory = "/path/to/your/jpg/folder"  # 替换为你的JPG文件目录
    # remote_path = "image/jpg"  # OSS上的远程存储路径
    # max_workers = 10  # 设置最大线程数

    # # 调用多线程上传方法
    # oss_urls = upload.upload_directory_jpgs_multithreaded(
    #     directory_path=jpg_directory,
    #     remote_path=remote_path,
    #     max_workers=max_workers
    # )

    # # 打印上传结果
    # print("\n上传成功的JPG文件URL列表:")
    # for url in oss_urls:
    #     print(url)

    # 示例2：查询OSS文件夹下的文件
    upload = Upload()
    remote_directory = "video/model/wangjun/user_1"  # 替换为你要查询的OSS目录
    print(f"\n查询OSS目录 {remote_directory} 下的文件...")
    file_list = upload.list_files_in_directory(remote_directory)
    if file_list:
        print("\n查询到的文件列表:")
        for file_info in file_list:
            print(f"文件名: {file_info['file_name']}, URL: {file_info['file_url']}")
    else:
        print("未查询到任何文件或查询失败")

