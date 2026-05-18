# GPUStack SSO 单点登录对接指南

> 本文档梳理 GPUStack 与外部身份认证系统（SSO）的对接方案。
>
> GPUStack 已**内置支持 OIDC 和 SAML 2.0**，无需额外开发。不支持 LDAP。

---

## 一、GPUStack 认证体系概览

GPUStack 采用多方式认证架构：

| 认证方式 | 适用场景 |
|----------|----------|
| **本地用户名/密码** | 默认方式，适合内部小团队 |
| **API Key** | 程序调用 API、推理服务对接 |
| **JWT Session Cookie** | 浏览器登录后的会话保持 |
| **OIDC (OAuth2)** | ⭐ 企业 SSO 对接（推荐） |
| **SAML 2.0** | 企业 SSO 对接（传统 IdP） |
| **System/Worker 认证** | Worker 节点注册到 Server |

> **注意**：启用 SSO 后，本地用户名/密码登录仍然可用（用于 admin 后备登录），但登录页会出现 SSO 登录按钮。

---

## 二、支持的 SSO 协议

### 2.1 OIDC / OAuth2（推荐）

- 自动发现：`https://<issuer>/.well-known/openid-configuration`
- 标准授权码流程（Authorization Code Flow）
- 支持 UserInfo 端点或 ID Token 解码获取用户信息
- 支持 RP-initiated Logout（登出后回调）

**适用 IdP**：Keycloak、Authing、Auth0、Azure AD、Okta、Dex、GitLab、Gitea 等任何标准 OIDC 提供商。

### 2.2 SAML 2.0

- 基于 `python3-saml` 实现
- 支持 SP-initiated 和 IdP-initiated 登录
- 支持单点登出（SLO）

**适用 IdP**：企业 AD FS、Shibboleth、OneLogin、部分国产身份认证平台。

### 2.3 不支持的协议

| 协议 | 状态 | 说明 |
|------|------|------|
| LDAP / Active Directory | ❌ 不支持 | 需通过 LDAP-to-OIDC 桥接（如 Dex） |
| CAS | ❌ 不支持 | 需通过 CAS-to-OIDC 桥接 |

---

## 三、OIDC 对接流程

### 3.1 IdP 侧配置（以 Keycloak 为例）

1. 在 Keycloak 中创建 **Client**
2. Client 类型选择 **openid-connect**
3. 设置 **Valid Redirect URIs**：
   ```
   https://<gpustack-server>/auth/oidc/callback
   ```
4. 开启 **Standard Flow**（授权码流程）
5. 记录 **Client ID** 和 **Client Secret**
6. 记录 **Issuer URL**（如 `https://keycloak.example.com/realms/master`）

### 3.2 GPUStack 侧配置

#### 方式一：命令行参数

```bash
gpustack start \
  --oidc-issuer "https://keycloak.example.com/realms/master" \
  --oidc-client-id "gpustack" \
  --oidc-client-secret "<your-client-secret>" \
  --oidc-redirect-uri "https://gpustack.example.com/auth/oidc/callback" \
  --external-auth-name "preferred_username" \
  --external-auth-full-name "name"
```

#### 方式二：环境变量

```bash
export GPUSTACK_OIDC_ISSUER="https://keycloak.example.com/realms/master"
export GPUSTACK_OIDC_CLIENT_ID="gpustack"
export GPUSTACK_OIDC_CLIENT_SECRET="<your-client-secret>"
export GPUSTACK_OIDC_REDIRECT_URI="https://gpustack.example.com/auth/oidc/callback"
export GPUSTACK_EXTERNAL_AUTH_NAME="preferred_username"
export GPUSTACK_EXTERNAL_AUTH_FULL_NAME="name"

gpustack start
```

#### 方式三：配置文件（YAML）

```yaml
# config.yaml
oidc_issuer: "https://keycloak.example.com/realms/master"
oidc_client_id: "gpustack"
oidc_client_secret: "<your-client-secret>"
oidc_redirect_uri: "https://gpustack.example.com/auth/oidc/callback"
external_auth_name: "preferred_username"
external_auth_full_name: "name"
```

启动时指定：
```bash
gpustack start --config-file config.yaml
```

### 3.3 OIDC 配置参数详解

| 参数 | 环境变量 | 必填 | 说明 |
|------|----------|------|------|
| `--oidc-issuer` | `GPUSTACK_OIDC_ISSUER` | ✅ | IdP 的 Issuer URL，GPUStack 会自动访问 `/.well-known/openid-configuration` |
| `--oidc-client-id` | `GPUSTACK_OIDC_CLIENT_ID` | ✅ | OIDC Client ID |
| `--oidc-client-secret` | `GPUSTACK_OIDC_CLIENT_SECRET` | ✅ | OIDC Client Secret |
| `--oidc-redirect-uri` | `GPUSTACK_OIDC_REDIRECT_URI` | ✅ | 回调地址，必须为 `<server-url>/auth/oidc/callback` |
| `--oidc-skip-userinfo` | `GPUSTACK_OIDC_SKIP_USERINFO` | ❌ | 跳过 UserInfo 端点，直接从 ID Token 解析用户信息 |

---

## 四、SAML 对接流程

### 4.1 IdP 侧配置

1. 在 SAML IdP 中注册 GPUStack 为 **Service Provider (SP)**
2. 设置 **ACS URL**（Assertion Consumer Service）：
   ```
   https://<gpustack-server>/auth/saml/callback
   ```
3. 设置 **Entity ID**（SP Entity ID）：
   ```
   https://<gpustack-server>
   ```
4. 获取 IdP 的 **Metadata** 或以下信息：
   - IdP Entity ID
   - IdP SSO URL
   - IdP X.509 证书

### 4.2 GPUStack 侧配置

```bash
gpustack start \
  --saml-idp-server-url "https://idp.example.com/saml/sso" \
  --saml-idp-entity-id "https://idp.example.com/entity" \
  --saml-idp-x509-cert "-----BEGIN CERTIFICATE-----\nMIID...\n-----END CERTIFICATE-----" \
  --saml-sp-entity-id "https://gpustack.example.com" \
  --saml-sp-acs-url "https://gpustack.example.com/auth/saml/callback" \
  --external-auth-name "emailaddress" \
  --saml-sp-attribute-prefix "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/"
```

### 4.3 SAML 配置参数详解

| 参数 | 环境变量 | 必填 | 说明 |
|------|----------|------|------|
| `--saml-idp-server-url` | `GPUSTACK_SAML_IDP_SERVER_URL` | ✅ | IdP SSO 服务 URL |
| `--saml-idp-entity-id` | `GPUSTACK_SAML_IDP_ENTITY_ID` | ✅ | IdP Entity ID |
| `--saml-idp-x509-cert` | `GPUSTACK_SAML_IDP_X509_CERT` | ✅ | IdP X.509 证书（PEM 格式） |
| `--saml-sp-entity-id` | `GPUSTACK_SAML_SP_ENTITY_ID` | ✅ | SP Entity ID |
| `--saml-sp-acs-url` | `GPUSTACK_SAML_SP_ACS_URL` | ✅ | SP ACS 回调地址 |
| `--saml-sp-x509-cert` | `GPUSTACK_SAML_SP_X509_CERT` | ❌ | SP X.509 证书（如需签名） |
| `--saml-sp-private-key` | `GPUSTACK_SAML_SP_PRIVATE_KEY` | ❌ | SP 私钥（如需签名） |
| `--saml-sp-attribute-prefix` | `GPUSTACK_SAML_SP_ATTRIBUTE_PREFIX` | ❌ | SAML 属性命名空间前缀，简化属性名配置 |
| `--saml-security` | `GPUSTACK_SAML_SECURITY` | ❌ | SAML 安全设置（JSON 格式） |

---

## 五、用户字段映射（通用）

SSO 登录成功后，GPUStack 需要从外部身份源提取用户信息并创建本地用户。

### 5.1 映射参数

| 参数 | 环境变量 | OIDC 示例 | SAML 示例 |
|------|----------|-----------|-----------|
| `--external-auth-name` | `GPUSTACK_EXTERNAL_AUTH_NAME` | `preferred_username` | `emailaddress`（需配合 prefix） |
| `--external-auth-full-name` | `GPUSTACK_EXTERNAL_AUTH_FULL_NAME` | `name` 或 `firstName+lastName` | `name` |
| `--external-auth-avatar-url` | `GPUSTACK_EXTERNAL_AUTH_AVATAR_URL` | `picture` | `picture` |
| `--external-auth-default-inactive` | `GPUSTACK_EXTERNAL_AUTH_DEFAULT_INACTIVE` | — | 新用户默认禁用 |

### 5.2 常见 IdP 的字段映射参考

#### Keycloak
```bash
--external-auth-name "preferred_username"
--external-auth-full-name "name"
--external-auth-avatar-url "picture"
```

#### Authing
```bash
--external-auth-name "username"
--external-auth-full-name "name"
--external-auth-avatar-url "photo"
```

#### Azure AD
```bash
--external-auth-name "preferred_username"
--external-auth-full-name "name"
```

#### 国产 SAML IdP（需配合 attribute prefix）
```bash
--saml-sp-attribute-prefix "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/"
--external-auth-name "emailaddress"
--external-auth-full-name "name"
```

---

## 六、用户自动创建机制

### 6.1 首次登录自动创建

SSO 用户首次登录时，GPUStack 会自动创建本地用户：

1. 解析 SSO 返回的用户信息（UserInfo / ID Token / SAML Attributes）
2. 根据 `--external-auth-name` 提取用户名
3. 根据 `--external-auth-full-name` 提取全名
4. 创建 `User` 记录，`source = OIDC` 或 `SAML`
5. 生成对应的 `Principal` 记录（多租户 RBAC）
6. 设置 JWT Cookie，完成登录

### 6.2 用户状态控制

| 参数 | 效果 |
|------|------|
| `--external-auth-default-inactive` | 新 SSO 用户默认处于**禁用**状态，需管理员手动启用 |
| 默认（不设置） | 新 SSO 用户**立即激活**，可直接使用 |

### 6.3 权限管理

SSO 用户创建后默认角色为普通用户。如需赋予管理员权限：
1. 使用本地 admin 账号登录
2. 进入 **Users** 管理页面
3. 找到 SSO 用户，修改角色为 **Admin**

---

## 七、Docker / Docker Compose 部署时的 SSO 配置

### 7.1 通过环境变量配置

在 `docker-compose.server.yaml` 的 `environment` 段添加：

```yaml
services:
  gpustack-server:
    image: registry.cn-chengdu.aliyuncs.com/lmzjai/gpustack-custom:dev
    environment:
      - GPUSTACK_OIDC_ISSUER=https://keycloak.example.com/realms/master
      - GPUSTACK_OIDC_CLIENT_ID=gpustack
      - GPUSTACK_OIDC_CLIENT_SECRET=<secret>
      - GPUSTACK_OIDC_REDIRECT_URI=https://gpustack.example.com/auth/oidc/callback
      - GPUSTACK_EXTERNAL_AUTH_NAME=preferred_username
      - GPUSTACK_EXTERNAL_AUTH_FULL_NAME=name
    ports:
      - "80:80"
```

### 7.2 通过配置文件挂载

```yaml
services:
  gpustack-server:
    image: registry.cn-chengdu.aliyuncs.com/lmzjai/gpustack-custom:dev
    volumes:
      - ./config.yaml:/etc/gpustack/config.yaml:ro
      - gpustack-data:/var/lib/gpustack
    environment:
      - GPUSTACK_CONFIG_FILE=/etc/gpustack/config.yaml
```

---

## 八、登录流程

### 8.1 OIDC 登录流程

```
用户访问 GPUStack 登录页
    ↓
点击 "Login with SSO" 按钮
    ↓
重定向到 IdP 授权端点 (/auth/oidc/login)
    ↓
用户在 IdP 完成认证
    ↓
IdP 重定向回 GPUStack (/auth/oidc/callback?code=...)
    ↓
GPUStack 用 code 换取 access_token + id_token
    ↓
调用 UserInfo 端点（或解码 ID Token）获取用户信息
    ↓
查找或自动创建本地用户
    ↓
设置 JWT Cookie (gpustack_session)
    ↓
登录成功，进入首页
```

### 8.2 登出流程

```
用户点击登出
    ↓
GPUStack 清除本地 JWT Cookie
    ↓
如果配置了 end_session_endpoint，重定向到 IdP 登出页
    ↓
IdP 清除会话后，可选地重定向回 GPUStack
```

---

## 九、常见问题

### Q1: 启用 SSO 后还能用本地账号登录吗？

**可以**。本地用户名/密码登录始终可用，建议保留 admin 本地账号作为后备。

### Q2: 同一个用户通过 SSO 和本地登录是同一个账号吗？

**不是**。SSO 用户和本地用户是独立的。如果用户名冲突，SSO 用户会创建为新的独立账号（source=OIDC/SAML）。

### Q3: 支持多个 IdP 同时对接吗？

**不支持**。GPUStack 同一时间只能配置一个外部认证源（OIDC 或 SAML）。

### Q4: 如何测试 SSO 配置是否正确？

1. 先用 `--debug` 模式启动 GPUStack，查看日志中的 OIDC/SAML 配置加载信息
2. 访问登录页，确认出现了 SSO 登录按钮
3. 点击 SSO 登录，观察是否成功跳转 IdP
4. 如果回调失败，检查 `--oidc-redirect-uri` / `--saml-sp-acs-url` 是否与 IdP 配置一致

### Q5: LDAP 怎么办？

GPUStack **不支持 LDAP**。如需对接 LDAP/AD，建议使用 **Dex** 作为 LDAP-to-OIDC 桥接：
- Dex 连接 LDAP/AD
- GPUStack 对接 Dex 的 OIDC 接口

---

## 十、本地开发环境启动（含 SSO）

### 10.1 启动命令

```bash
cd ~/thirdComponent/AI/gpustack

GPUSTACK_DATABASE_URL="postgresql://<user>:<password>@127.0.0.1:5432/gpustack?sslmode=disable" \
uv run gpustack start \
  --port 8080 \
  --api-port 38080 \
  --data-dir ~/thirdComponent/AI/gpustack/data/gpustack \
  --gateway-mode disabled \
  --oidc-issuer "http://localhost:8100" \
  --oidc-client-id "<oidc-client-id>" \
  --oidc-client-secret "<oidc-client-secret>" \
  --oidc-redirect-uri "http://localhost:38080/auth/oidc/callback" \
  --external-auth-name "preferred_username" \
  --external-auth-full-name "name"
```

### 10.2 参数说明

| 参数 | 值 | 说明 |
|------|-----|------|
| `--oidc-issuer` | `http://localhost:8100` | 公司 SSO 服务地址 |
| `--oidc-client-id` | `<oidc-client-id>` | OIDC Client ID |
| `--oidc-client-secret` | `<oidc-client-secret>` | OIDC Client Secret |
| `--oidc-redirect-uri` | `http://localhost:38080/auth/oidc/callback` | GPUStack 回调地址 |
| `--external-auth-name` | `preferred_username` | 用户名字段映射 |
| `--external-auth-full-name` | `name` | 全名字段映射 |

### 10.3 测试访问

1. 浏览器打开 `http://localhost:38080/`
2. 登录页显示 **"Login with SSO"** 按钮
3. 点击跳转至公司 SSO 登录页
4. 登录成功后自动返回 GPUStack

### 10.4 常见问题

**登录页没有 SSO 按钮？**
- 强制刷新浏览器（`Cmd+Shift+R`）
- 检查 F12 Console 是否有报错
- 确认前端产物已重新编译同步：
  ```bash
  cd ~/thirdComponent/AI/gpustack-ui && pnpm build
  rm -rf ~/thirdComponent/AI/gpustack/gpustack/ui/*
  cp -r ~/thirdComponent/AI/gpustack-ui/dist/* ~/thirdComponent/AI/gpustack/gpustack/ui/
  ```

---

## 十一、快速参考：OIDC 最小配置

```bash
# 启动参数方式
gpustack start \
  --oidc-issuer "https://keycloak.example.com/realms/master" \
  --oidc-client-id "gpustack" \
  --oidc-client-secret "<secret>" \
  --oidc-redirect-uri "https://gpustack.example.com/auth/oidc/callback" \
  --external-auth-name "preferred_username"

# 环境变量方式
export GPUSTACK_OIDC_ISSUER="https://keycloak.example.com/realms/master"
export GPUSTACK_OIDC_CLIENT_ID="gpustack"
export GPUSTACK_OIDC_CLIENT_SECRET="<secret>"
export GPUSTACK_OIDC_REDIRECT_URI="https://gpustack.example.com/auth/oidc/callback"
export GPUSTACK_EXTERNAL_AUTH_NAME="preferred_username"
gpustack start
```

---

*本文档基于 GPUStack 源码分析整理，如有更新请以官方文档为准。*
