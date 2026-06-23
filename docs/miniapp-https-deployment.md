# Geekspace 小程序 HTTPS 测试环境

这一步的目标不是继续调本机局域网，而是把后端挂到一个真正能被微信小程序访问的 `https` 地址。

## 当前项目已经补好的内容

- 后端资料库路径支持环境变量：
  - `GEEKSPACE_VAULT_DIR`
- 后端 API 基地址支持环境变量：
  - `GEEKSPACE_API_BASE_URL`
- 默认模型支持环境变量：
  - `GEEKSPACE_DEFAULT_MODEL`
- 已补齐：
  - `requirements.txt`
  - `wsgi.py`
  - `Dockerfile`
  - `render.yaml`
- 已将运行必须的资料文件收进项目：
  - `runtime/xuanxue-knowledge-vault/wiki/dossiers`
  - `runtime/xuanxue-knowledge-vault/wiki/engine/calculators`

## 推荐测试部署路径

优先建议用 Render 的 Docker Web Service，原因很简单：

- 自动给 `https`
- 不需要你先折腾 Nginx
- 适合先把小程序联调跑通

## Render 部署步骤

1. 把当前项目推到 GitHub
2. 登录 Render
3. New + -> Web Service
4. 选择这个仓库
5. Render 会识别 `render.yaml` 和 `Dockerfile`
6. 在环境变量里补上：
   - `GEEKSPACE_API_KEY=你的真实 key`
   - `GEEKSPACE_API_BASE_URL=https://geekspace.cloud/v1`（如果你还用这个上游）
   - `GEEKSPACE_DEFAULT_MODEL=gpt-5.5`
7. 部署完成后会得到一个类似：
   - `https://geekspace-webchat.onrender.com`

## 部署后先验证

先打开：

- `/api/health`
- `/api/progress`

例如：

- `https://你的域名/api/health`

你需要确认返回里：

- `"ok": true`
- `"vaultReady": true`

## 小程序里要改的地方

编辑：

- `miniapp/config/env.js`

把：

```js
const baseUrl = "https://example.com";
```

改成：

```js
const baseUrl = "https://你的实际域名";
```

## 微信小程序侧必须做的配置

根据微信官方开发文档，小程序网络请求需要满足这些条件：

- 只能请求已配置的服务器域名
- `request` 只能使用 `https`
- 不能使用 `IP` 或 `localhost` 作为正式服务域名
- 域名通常需要 ICP 备案
- HTTPS 证书必须有效，且 TLS 版本满足要求

配置位置：

- 小程序后台 -> 开发 -> 开发设置 -> 服务器域名

把你的后端域名加到：

- `request 合法域名`

## 开发阶段的临时说明

微信官方文档同时说明，在微信开发者工具里可以临时开启：

- `开发环境不校验请求域名、TLS 版本及 HTTPS 证书`

这个只适合开发调试，不适合作为最终方案。

## 关于“手机端现在能不能打开”

结论分两层：

1. 现在这个原生小程序项目可以在微信开发者工具里直接打开并预览
2. 真机非调试状态下，是否能正常请求后端，取决于：
   - 后端是否部署到公网 `https`
   - 域名是否已在小程序后台配置
   - 证书是否有效

## 一个很现实的补充

如果你要把这套能力正式做成面向用户的小程序，而且包含 AI 问答 / 生成式能力，微信类目和合规材料也要提前看。官方类目页里已经明确提到：

- AI 问答 / 文本深度合成类服务，通常涉及相关算法备案要求
- AI 生成内容需要显著标注

所以测试环境可以先跑，但正式上线前最好把这个合规项一起排进计划。
