# 3. Worker 节点接入

## 3.1 前置复核（每台节点）

- [ ] GPU 驱动 ≥570、nvidia-container-toolkit 可用（见 1-prerequisites）
- [ ] 磁盘余量 ≥25G + 模型体积
- [ ] 模型目录已创建（默认 `/home/ubuntu/models`），模型文件已落盘
- [ ] 安全组：server 可访问本节点 **10150** 端口
- [ ] server 可达（`curl -s http://<server>:8080/healthz` 返回 200）

## 3.2 生成接入命令

UI → 集群 → 对应集群 → **添加节点**，按向导填写（额外挂载务必填模型目录），
生成的命令按 `../acr-image-mirror.md` §2 模板核对后执行。命令必须满足：

1. 镜像为 `registry.cn-chengdu.aliyuncs.com/lmzjai/gpustack-custom:<完整40位SHA>`，且 SHA 与 server 一致；
2. 含 `GPUSTACK_RUNTIME_DOCKER_PAUSE_IMAGE` / `GPUSTACK_RUNTIME_DOCKER_UNHEALTHY_RESTART_IMAGE` 两个 env（指向 `lmzjai/runtime`）；
3. 挂载齐全：docker.sock、`gpustack-data:/var/lib/gpustack`、模型目录；
4. `--runtime nvidia`（GPU 节点）。

> 若镜像行不是 lmzjai 完整 SHA（出现 quay.io 或短 tag），**停止执行**——
> 检查 server 的 `GPUSTACK_IMAGE_NAME_OVERRIDE` 是否生效（`docker exec
> gpustack-server printenv GPUSTACK_IMAGE_NAME_OVERRIDE`）。

## 3.3 执行与确认

```bash
# 在节点上执行命令后：
docker logs -f gpustack-worker
# 期望：registered with worker_id N → Worker startup completed
# 异常排查：出现 Version mismatch → server/worker SHA 不一致（见上方 3.2-1）
```

UI → 节点页：节点出现且 **READY**，GPU 数量/型号正确，心跳持续更新。

## 3.4 已知坑位（历史事故清单，遇到先查）

| 症状 | 首查 |
|---|---|
| `Missing cluster_id for worker registration` | server 库 `clusters.system_principal_id` 是否指向集群 SYSTEM principal（见 Issue #29） |
| 实例循环重启、报 `gpustack/runner` 拉取失败 | 镜像 ref 是否被解析到不存在的仓库；确认 version_configs 与 ACR 仓库（`../acr-image-mirror.md`） |
| 注册成功但实例 PENDING「0/1 workers by READY」 | worker 是否真正 READY；server→worker:10150 是否连通（调度需远程读 config.json） |
| 时钟异常（日志时间与实际差） | 节点 NTP/时区（影响 TLS 与心跳判断） |
