# 海报设计应用项目文档

## 1. 项目概述

这是一个用于处理PSD文件的Web应用，主要功能包括上传PSD文件、移除文本图层、检测并移除图像中的文本，以及下载处理后的文件。项目采用前后端分离架构，前端使用Vue.js构建响应式界面，后端使用FastAPI提供RESTful API服务。

### 1.1 主要功能

- 上传和处理PSD文件
- 移除PSD文件中的文本图层
- 使用OCR技术检测并移除图像中的文本
- 支持多种输出格式（PNG、JPG等）
- 提供响应式Web界面
- 支持文件下载功能

### 1.2 技术栈

#### 前端
- Vue 3.4
- TypeScript
- Element Plus
- Pinia
- Vue Router
- psd.js（PSD文件解析）
- axios（HTTP请求）

#### 后端
- Python 3.9+
- FastAPI
- psd-tools（PSD文件处理）
- pytesseract（OCR文本识别）
- OpenCV（图像处理）
- Pillow（图像处理）

#### 部署
- Docker & Docker Compose

## 2. 项目架构

项目采用经典的前后端分离架构，主要包含前端应用和后端API服务两个核心模块。

### 2.1 整体架构

```
├── front_end/  # Vue.js前端应用
├── back_end/   # FastAPI后端服务
└── docker-compose.yml  # Docker部署配置
```

### 2.2 前端架构

前端采用Vue 3组合式API和TypeScript开发，主要结构如下：

- **路由管理**：使用Vue Router处理页面导航
- **状态管理**：使用Pinia管理全局状态
- **UI组件**：基于Element Plus构建用户界面
- **API交互**：使用axios与后端API通信
- **文件处理**：集成psd.js进行前端PSD解析

### 2.3 后端架构

后端采用FastAPI框架，遵循RESTful API设计规范：

- **API层**：处理HTTP请求和响应
- **服务层**：实现业务逻辑
- **工具层**：提供PSD处理、OCR识别等功能
- **配置管理**：使用pydantic-settings管理应用配置

## 3. 核心模块详细说明

### 3.1 前端模块

#### 3.1.1 主页面模块

位于`src/views/Psd.vue`，是PSD处理功能的主入口页面，包含以下功能：

- 展示PSD文件处理工具的功能介绍
- 集成PSDUploader组件处理文件上传
- 提供功能特点展示区域

#### 3.1.2 PSD上传组件

位于`src/components/PSDUploader.vue`，负责PSD文件的上传和处理流程：

- 提供文件拖放和点击上传功能
- 文件类型和大小验证（支持PSD/PSB文件，最大20MB）
- 实时显示处理进度
- 提供处理结果下载功能
- 错误处理和用户反馈

#### 3.1.3 API服务

位于`src/api/psd.ts`，封装了与后端通信的API调用：

- `processPSD`：处理PSD文件的API调用
- `downloadProcessedFile`：下载处理后文件的API调用

### 3.2 后端模块

#### 3.2.1 API路由

位于`back_end/app/api/psd.py`，提供PSD处理相关的API端点：

- `/api/psd/process`：处理PSD文件
- `/api/psd/download/{file_path}`：下载处理后的文件

#### 3.2.2 PSD服务

位于`back_end/app/services/psd_service.py`，实现PSD文件处理的业务逻辑：

- 文件保存和路径管理
- PSD处理流程协调
- 错误处理和结果返回

#### 3.2.3 PSD处理工具

位于`back_end/app/utils/psd_utils.py`，核心的PSD处理功能实现：

- 文本图层识别和删除
- 图像文本检测（OCR）
- PSD文件处理和导出

#### 3.2.4 独立处理脚本

位于`back_end/process_psd_layers.py`，提供命令行方式处理PSD文件的能力：

- 递归删除文本图层
- 多方法OCR文本检测
- 图层导出功能
- 详细的日志输出

## 4. 核心功能实现

### 4.1 PSD文件解析与处理

项目使用两种方式处理PSD文件：

1. **前端解析**：使用psd.js在浏览器中进行初步解析
2. **后端处理**：使用psd-tools在服务器端进行深度处理

后端处理流程：
1. 接收上传的PSD文件
2. 递归遍历PSD图层结构
3. 识别并删除文本图层
4. 对图像图层进行OCR文本检测（可选）
5. 删除包含文本的图像图层（如果OCR检测开启）
6. 将处理后的PSD导出为指定格式的图像

### 4.2 OCR文本检测

OCR文本检测是项目的核心功能之一，实现在`psd_utils.py`和`process_psd_layers.py`中：

- 使用Tesseract OCR引擎进行文本识别
- 支持中英文文本识别（chi_sim+eng）
- 采用多种检测策略提高准确率：
  1. 基础OCR检测
  2. 二值化后OCR检测
  3. 反色后OCR检测
  4. 边缘增强后OCR检测
- 文本过滤和验证，减少误判

### 4.3 文件上传与下载

- **文件上传**：使用Element Plus的上传组件，支持拖放和点击上传
- **文件保存**：后端使用UUID生成唯一文件名，避免文件冲突
- **文件下载**：提供HTTP端点用于下载处理后的文件
- **安全措施**：实现路径验证，防止目录遍历攻击

## 5. 项目部署

### 5.1 Docker部署

项目提供Docker和Docker Compose支持，简化部署流程：

```bash
docker-compose up --build
```

服务访问地址：
- 前端应用：http://localhost:8080
- 后端API：http://localhost:8000
- API文档：http://localhost:8000/docs

### 5.2 环境配置

后端需要配置以下环境变量（`.env`文件）：

```env
DEBUG=True
CORS_ORIGINS=["http://localhost:8080", "http://127.0.0.1:8080"]
UPLOAD_FOLDER=./uploads
TESSERACT_CMD=/usr/bin/tesseract
```

## 6. 核心代码解析

### 6.1 PSD处理核心逻辑

```python
# 递归删除文本图层的核心逻辑
def remove_text_layers_recursive(self, layer, parent=None, parent_layers=None, index=None):
    # 检查是否为文本图层
    if hasattr(layer, 'kind') and layer.kind == 'type':
        return True
    
    # 如果是组图层,递归处理子图层
    if hasattr(layer, 'is_group') and layer.is_group():
        for i in range(len(layer) - 1, -1, -1):
            sub_layer = layer[i]
            if self.remove_text_layers_recursive(sub_layer, layer, layer._layers, i):
                del layer._layers[i]
    
    return False
```

### 6.2 OCR文本检测

```python
# OCR文本检测函数
def detect_text_in_image(self, image_data, layer_name: str) -> bool:
    try:
        # 转换为灰度
        gray = cv2.cvtColor(np.array(image_data), cv2.COLOR_RGBA2GRAY)
        
        # 使用Tesseract进行文本识别
        text = pytesseract.image_to_string(gray)
        
        # 如果检测到文本，返回True
        return len(text.strip()) > 0
        
    except Exception as e:
        print(f"Error in text detection for layer {layer_name}: {str(e)}")
        return False
```

### 6.3 前端文件上传处理

```typescript
const processPSDFile = async (file: File) => {
  try {
    processing.value = true
    statusMessage.value = 'Uploading file...'
    progressStatus.value = ''

    const response = await processPSD(
      file,
      {
        skipOcr: false,
        outputFormat: 'png'
      },
      (uploadProgress: number) => {
        progress.value = Math.min(90, uploadProgress) // 进度条上限90%
      }
    )

    statusMessage.value = 'Processing file...'
    progress.value = 95
    
    // 小延迟以显示处理状态
    await new Promise(resolve => setTimeout(resolve, 500))
    
    result.value = response
    progress.value = 100
    progressStatus.value = 'success'
    statusMessage.value = 'Processing complete!'
    
    ElMessage.success('PSD processed successfully')
  } catch (error: any) {
    console.error('Error processing PSD:', error)
    progressStatus.value = 'exception'
    statusMessage.value = 'Error processing file: ' + (error.message || 'Unknown error')
    ElMessage.error('Failed to process PSD: ' + (error.message || 'Unknown error'))
  } finally {
    processing.value = false
  }
}
```

## 7. 总结

本项目是一个功能完整的PSD文件处理应用，专注于文本图层移除和图像文本检测功能。通过前后端分离架构，实现了良好的用户体验和高效的文件处理能力。项目具有以下特点：

1. **功能实用**：针对设计工作流中的实际需求，提供PSD文本移除功能
2. **技术先进**：采用Vue 3、FastAPI等现代技术栈
3. **扩展性强**：模块化设计使功能易于扩展
4. **部署简便**：提供Docker支持，简化部署流程
5. **用户友好**：直观的界面和良好的用户反馈机制

该项目可广泛应用于设计团队、营销部门等需要批量处理PSD文件的场景，提高工作效率，减少手动操作。