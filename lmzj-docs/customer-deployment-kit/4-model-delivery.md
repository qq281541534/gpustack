# 4. 模型交付

## 4.1 模型文件

- 模型文件放 worker 节点的模型目录（如 `/home/ubuntu/models/<模型名>/`），
  目录内含 `config.json` 等完整 HF 结构；
- UI 部署模型时选择「本地路径」（LOCAL_PATH），路径填容器内可见路径
  （与节点命令的模型目录挂载一致）；
- 跨节点共享模型：每台目标节点都要落盘，或挂载同一共享存储。

## 4.2 部署参数约定

- 后端与版本：使用「推理后端」页登记的版本（如 vLLM 0.11.2）；
  版本对应的 runner 镜像已由 version_configs 钉在 ACR，**不要手改镜像名**；
- 显存参数注意合法性（如 `--max-model-len=8192`，等号后不能有空格——
  历史事故：空格导致 vLLM 启动即崩，见 Issue #29）；
- 24G 卡参考：7B 级模型 `--gpu-memory-utilization=0.9` 起步，叠加
  `--enforce-eager` 省 1–2G。

## 4.3 部署后确认

- 模型实例状态从 PENDING → STARTING → **RUNNING**；
- 长时间 PENDING 看实例 `state_message`：
  - 「No suitable workers / 0/1 READY」→ 节点未就绪或显存不足；
  - 反复 STARTING→ERROR → 看 worker 实例日志（节点上
    `/var/lib/gpustack/log/serve/<实例id>*.log`）。

## 4.4 路由暴露（可选）

- 需要统一入口/多版本灰度时配置「路由」；路由目标与模型须同 Org；
- 路由保存后网关自动收敛（约秒级）；调用模型名 = 路由名
  （平台 Org 下不加前缀）。
