# 文件查询系统

这是一个基于React的文件上传和查询系统，提供简单的Web界面来上传文件和执行查询操作。

## 功能特点

- 文件上传：支持拖放或点击选择文件
- 文件查询：可以对上传的文件执行查询操作
- 实时结果显示：查询结果即时展示
- 现代化UI：使用Material-UI组件库

## 技术栈

- React 18
- TypeScript
- Material-UI
- React Dropzone
- AWS SDK for JavaScript

## 安装说明

1. 安装Node.js (推荐版本 14.x 或更高)

2. 安装项目依赖：
```bash
npm install
```

3. 配置AWS凭证：
   - 在项目根目录创建 `.env` 文件
   - 添加以下环境变量：
   ```
   REACT_APP_AWS_ACCESS_KEY_ID=你的AWS访问密钥ID
   REACT_APP_AWS_SECRET_ACCESS_KEY=你的AWS秘密访问密钥
   REACT_APP_AWS_REGION=你的AWS区域
   ```

4. 启动开发服务器：
```bash
npm start
```

## 使用说明

1. 文件上传：
   - 将文件拖放到上传区域，或点击选择文件
   - 点击"上传文件"按钮开始上传

2. 执行查询：
   - 在查询输入框中输入查询内容
   - 点击"提交查询"按钮执行查询
   - 查询结果将显示在下方

## 注意事项

- 请确保AWS凭证配置正确
- 上传文件大小可能有限制
- 建议使用现代浏览器以获得最佳体验 