# AI Web Search

OpenAI API 兼容的联网搜索中间层。服务会先判断用户问题是否需要搜索，必要时调用可配置的搜索引擎，再把整理后的参考信息拼接给调用方指定的最终模型。

## 本地启动

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
uvicorn src.main:app --host 0.0.0.0 --port 18080
```

配置文件默认读取 `config/config.yaml`，也可以通过 `AI_WEB_SEARCH_CONFIG` 指定其他路径。缺少搜索引擎密钥时，健康检查会把对应引擎标记为不可用；非联网流程仍可使用。

## 核心接口

- `POST /v1/client/init` 初始化最终回答模型客户端。
- `POST /v1/chat/completions` OpenAI 兼容对话接口，支持 `search_options` 扩展。
- `POST /v1/search` 只执行搜索。
- `GET /health` 健康检查。
- `GET /ready` 就绪检查。
- `GET /v1/search/engines` 搜索引擎状态。
- `GET /v1/stats` 运行统计。
- `POST /v1/cache/clear` 清理缓存。

## 示例

```powershell
$client = Invoke-RestMethod -Method Post http://localhost:18080/v1/client/init `
  -ContentType "application/json" `
  -Body '{"api_key":"sk-xxx","base_url":"https://api.openai.com/v1","model":"gpt-4o-mini"}'

Invoke-RestMethod -Method Post http://localhost:18080/v1/chat/completions `
  -ContentType "application/json" `
  -Body (@{
    client_id = $client.client_id
    messages = @(@{role="user"; content="今天北京天气怎么样？"})
    search_options = @{ force_search = $true; max_results = 5 }
  } | ConvertTo-Json -Depth 5)
```
