# Merlin2api

基于 [@SMNETSTUDIO/GetMerlin2Api](https://github.com/SMNETSTUDIO/GetMerlin2Api) 的 go 版本改编实现。

## 声明
- 仅用于学术研究和交流学习

## 支持模型
- gpt-3.5-turbo
- gpt-4o
- gpt-4o-mini
- o3-mini
- claude-3-sonnet
- claude-3-haiku
- claude-3.5-haiku
- claude-3.5-sonnet
- deepseek-chat
- deepseek-reasoner
- gemini-1.5-flash
- mistralai/Mixtral-8x7B-Instruct-v0.1

## Docker部署
### 拉取
```bash
docker pull mtxyt/merlin2api:1.0
```
### 运行
```bash
docker run -d -p 8802:8802 mtxyt/merlin2api:1.0
```
如果你想配置key可以用
```bash
docker run -d -p 8802:8802 -e UUID=your_uuid -e AUTH_TOKEN=your_token mtxyt/merlin2api:1.0
```

## 声明
本项目仅供学术交流使用，请勿用于商业用途。

## 致谢
感谢 [@SMNETSTUDIO](https://github.com/SMNETSTUDIO) 的原创项目支持。
