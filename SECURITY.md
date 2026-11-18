# Security Policy

## Supported versions

当前仅维护最新发布版本。

## Reporting a vulnerability

请不要在公开 Issue 中披露可利用细节、密钥或个人课程数据。通过仓库托管平台的私密安全报告功能联系维护者，并附上：

- 影响版本；
- 复现步骤；
- 可能影响的数据范围；
- 建议修复方向。

## Deployment baseline

- 默认只监听 `127.0.0.1`。
- 远程绑定必须设置 `VKS_PASSWORD`。
- 建议在 HTTPS 反向代理后运行。
- `data/state/`、`.env` 和模型凭据不得进入版本控制。
- 课程包来自不可信来源时，先检查路径、媒体格式和许可证。
