# MCP 高并发架构设计文档

## 一、背景与问题

### 1.1 当前架构
```
MCPClient (线程) ──stdio──→ MCPServer (子进程)
```

当前是 **1:1 绑定**：每个 MCPClient 启动一个独立的 MCPServer 子进程。

### 1.2 存在的问题

| 问题 | 描述 |
|------|------|
| 资源浪费 | 100个AI实例 = 100个Server进程 |
| 无法共享 | stdio协议天然1:1，无法多路复用 |
| 无调度 | 没有负载均衡，任务分配不均 |
| 无弹性 | 无法动态扩缩容 |

---

## 二、目标架构

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        外部调用层                            │
│         (多个AI实例、业务模块等)                              │
└─────────────────────┬───────────────────────────────────────┘
                      │ submit(task) / get_result(uuid)
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                      MCPManager                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  TX 队列    │  │  RX 字典    │  │   调度器            │  │
│  │ (任务入口)  │  │ (结果存储)  │  │ (负载均衡+因子计算) │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
│  ┌─────────────────────────────────────────────────────────┐│
│  │                    客户端池                              ││
│  │  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐        ││
│  │  │Client 1│  │Client 2│  │Client 3│  │备用池..│        ││
│  │  │ load=3 │  │ load=5 │  │ load=2 │  │ load=0 │        ││
│  │  └───┬────┘  └───┬────┘  └───┬────┘  └────────┘        ││
│  └──────┼───────────┼───────────┼──────────────────────────┘│
└─────────┼───────────┼───────────┼───────────────────────────┘
          │stdio      │stdio      │stdio
          ▼           ▼           ▼
     ┌────────┐  ┌────────┐  ┌────────┐
     │Server 1│  │Server 2│  │Server 3│
     └────────┘  └────────┘  └────────┘
```

### 2.2 核心组件

| 组件 | 职责 |
|------|------|
| **TX队列** | 统一任务入口，所有任务先进队列 |
| **RX字典** | 结果存储，key=UUID，value=result |
| **调度器** | 负载均衡，选择最优Client执行任务 |
| **客户端池** | 管理多个MCPClient实例 |
| **备用池** | 预创建的空闲实例，应对突发流量 |

---

## 三、负载因子均衡算法

### 3.1 因子定义

每个任务有一个**负载因子(load_factor)**，表示该任务的"重量"。

```python
# 任务因子示例
TASK_FACTORS = {
    # 轻量级任务
    "add": 1,
    "subtract": 1,
    "multiply": 1,
    "divide": 1,

    # 中等任务
    "read_line": 2,
    "read_all": 3,
    "write_JSON": 3,

    # 重量级任务
    "database_query": 5,
    "file_batch_process": 8,
    "complex_calculation": 10,

    # 默认因子
    "default": 3
}
```

### 3.2 客户端负载计算

每个Client维护当前负载值：

```python
class ClientWrapper:
    def __init__(self, client: MCPClient):
        self.client = client
        self.current_load = 0      # 当前负载
        self.max_load = 100        # 最大负载阈值
        self.task_count = 0        # 当前任务数
        self.lock = threading.Lock()

    def add_load(self, factor: int):
        with self.lock:
            self.current_load += factor
            self.task_count += 1

    def remove_load(self, factor: int):
        with self.lock:
            self.current_load -= factor
            self.task_count -= 1

    def is_available(self) -> bool:
        return self.current_load < self.max_load
```

### 3.3 调度算法

**最小负载优先(Least Load First)**：

```python
def select_client(self, task_factor: int) -> ClientWrapper:
    """
    选择负载最小的可用Client
    """
    available_clients = [c for c in self.active_pool if c.is_available()]

    if not available_clients:
        # 所有Client都满了，从备用池激活一个
        return self.activate_standby()

    # 选择负载最小的
    return min(available_clients, key=lambda c: c.current_load)
```

### 3.4 负载均衡示意

```
任务到达: task_A (factor=5)

当前状态:
  Client 1: load=30
  Client 2: load=45
  Client 3: load=25  ← 最小，选中

分配后:
  Client 1: load=30
  Client 2: load=45
  Client 3: load=30  (25+5)
```

---

## 四、备用实例池机制

### 4.1 设计思路

```
┌─────────────────────────────────────────┐
│              客户端池                    │
│  ┌─────────────────────────────────┐   │
│  │         活跃池 (Active)          │   │
│  │   Client1  Client2  Client3     │   │
│  │   (工作中)  (工作中)  (工作中)    │   │
│  └─────────────────────────────────┘   │
│  ┌─────────────────────────────────┐   │
│  │         备用池 (Standby)         │   │
│  │   Client4  Client5  ...         │   │
│  │   (空闲)    (空闲)               │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

### 4.2 配置参数

```python
class PoolConfig:
    min_active = 3          # 最小活跃实例数
    max_active = 20         # 最大活跃实例数
    standby_count = 2       # 备用实例数量

    scale_up_threshold = 80     # 扩容阈值(平均负载%)
    scale_down_threshold = 20   # 缩容阈值(平均负载%)

    idle_timeout = 300      # 空闲超时(秒)，超时后回收到备用池
```

### 4.3 扩缩容策略

**扩容条件**：
- 所有活跃Client负载 > scale_up_threshold
- 且活跃数 < max_active

**缩容条件**：
- 某Client空闲时间 > idle_timeout
- 且活跃数 > min_active

```python
def check_and_scale(self):
    """定期检查，执行扩缩容"""
    avg_load = self.get_average_load()

    # 扩容
    if avg_load > self.config.scale_up_threshold:
        if len(self.active_pool) < self.config.max_active:
            self.activate_standby()

    # 缩容
    for client in self.active_pool:
        if client.idle_time > self.config.idle_timeout:
            if len(self.active_pool) > self.config.min_active:
                self.deactivate_to_standby(client)
```

---

## 五、数据流设计

### 5.1 任务提交流程

```
1. 外部调用 manager.submit(task_name, args)
2. Manager 计算任务因子 factor = TASK_FACTORS.get(task_name, default)
3. 调度器选择最优Client (最小负载)
4. 生成UUID，任务入TX队列
5. 更新Client负载: client.add_load(factor)
6. 返回UUID给调用者
```

### 5.2 结果获取流程

```
1. 外部调用 manager.get_result(uuid, timeout)
2. 轮询/阻塞等待 RX字典中出现该UUID
3. 取出结果，从RX字典删除
4. 更新Client负载: client.remove_load(factor)
5. 返回结果
```

### 5.3 时序图

```
调用者          MCPManager           Client            Server
  │                │                   │                 │
  │──submit(task)─→│                   │                 │
  │                │──select_client()  │                 │
  │                │──add_to_queue()──→│                 │
  │←──uuid─────────│                   │──call_tool()───→│
  │                │                   │                 │
  │                │                   │←──result────────│
  │                │←──store_result()──│                 │
  │──get_result()─→│                   │                 │
  │←──result───────│                   │                 │
```

---

## 六、线程模型

### 6.1 为什么用线程而非进程

| 因素 | 线程 | 进程 |
|------|------|------|
| MCPClient工作类型 | IO密集型 | - |
| 数据共享 | 直接共享内存 | 需要IPC |
| GIL影响 | IO操作时释放GIL | 无影响 |
| 实现复杂度 | 低 | 高 |

**结论**：Manager层用线程，Server层已经是进程。

### 6.2 线程安全设计

```python
class MCPManager:
    def __init__(self):
        self.tx_queue = queue.Queue()           # 线程安全队列
        self.rx_dict = {}                        # 结果字典
        self.rx_lock = threading.Lock()          # 字典锁
        self.pool_lock = threading.Lock()        # 池操作锁
```

---

## 七、接口设计

### 7.1 MCPManager 对外接口

```python
class MCPManager:
    def start(self) -> None:
        """启动Manager和初始客户端池"""
        pass

    def stop(self) -> None:
        """停止所有客户端，清理资源"""
        pass

    def submit(self, task_name: str, arguments: dict = None,
               factor: int = None) -> str:
        """
        提交任务
        :param task_name: 工具名称
        :param arguments: 参数
        :param factor: 自定义因子(可选)
        :return: 任务UUID
        """
        pass

    def get_result(self, uuid: str, block: bool = True,
                   timeout: float = None) -> Any:
        """
        获取结果
        :param uuid: 任务UUID
        :param block: 是否阻塞
        :param timeout: 超时时间
        :return: 执行结果
        """
        pass

    def get_stats(self) -> dict:
        """获取运行统计信息"""
        pass
```

### 7.2 使用示例

```python
# 创建Manager
manager = MCPManager(
    min_active=3,
    max_active=10,
    standby_count=2
)

# 启动
manager.start()

# 提交任务
uuid1 = manager.submit("add", {"a": 1, "b": 2})
uuid2 = manager.submit("read_all", {"filepath": "test.txt"})
uuid3 = manager.submit("database_query", {"sql": "SELECT *"}, factor=10)

# 获取结果
result1 = manager.get_result(uuid1, timeout=5)
result2 = manager.get_result(uuid2, timeout=10)
result3 = manager.get_result(uuid3, timeout=30)

# 查看统计
stats = manager.get_stats()
print(f"活跃客户端: {stats['active_count']}")
print(f"平均负载: {stats['avg_load']}")

# 停止
manager.stop()
```

---

## 八、健康检查与故障恢复

### 8.1 健康检查

```python
def health_check(self):
    """定期检查Client健康状态"""
    for client in self.active_pool:
        if not client.is_alive():
            self.handle_dead_client(client)
```

### 8.2 故障恢复

```python
def handle_dead_client(self, dead_client):
    """处理死亡的Client"""
    # 1. 从活跃池移除
    self.active_pool.remove(dead_client)

    # 2. 重新分配该Client的未完成任务
    for task in dead_client.pending_tasks:
        self.tx_queue.put(task)

    # 3. 从备用池激活新Client
    self.activate_standby()
```

---

## 九、补充设计

### 9.1 VIP专用通道（任务优先级）

不采用"插队"机制，而是**预留专用Client**：

```
┌─────────────────────────────────────────┐
│              客户端池                    │
│  ┌─────────────────────────────────┐   │
│  │      普通池 (Normal)             │   │
│  │   Client1  Client2  Client3     │   │
│  │   (排队处理普通任务)              │   │
│  └─────────────────────────────────┘   │
│  ┌─────────────────────────────────┐   │
│  │      VIP池 (Priority)            │   │
│  │   VIP_Client1  VIP_Client2      │   │
│  │   (专门处理特殊任务，不排队)       │   │
│  └─────────────────────────────────┘   │
│  ┌─────────────────────────────────┐   │
│  │      备用池 (Standby)            │   │
│  │   Standby1  Standby2            │   │
│  │   (预热好的空闲实例，随时顶上)     │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

```python
def submit(self, task_name: str, arguments: dict = None,
           priority: bool = False) -> str:
    """
    :param priority: True则走VIP通道
    """
    if priority:
        client = self.select_from_vip_pool()
    else:
        client = self.select_from_normal_pool()
    # ...
```

### 9.2 任务超时处理

超时直接返回错误码，简单明了：

```python
class ErrorCode:
    SUCCESS = 0
    TIMEOUT = -1001
    CLIENT_DEAD = -1002
    TASK_FAILED = -1003

def get_result(self, uuid: str, timeout: float = None):
    start = time.time()
    while True:
        if uuid in self.rx_dict:
            return self.rx_dict.pop(uuid)
        if timeout and (time.time() - start) > timeout:
            return {"error": ErrorCode.TIMEOUT, "msg": "任务超时"}
        time.sleep(0.01)
```

### 9.3 结果不持久化

- RX字典是内存字典
- 结果取走即删除
- 不需要持久化（实时系统，不是存储系统）

### 9.4 备用池的作用

备用池 = **预热好的空闲实例**，作用：

| 场景 | 备用池的作用 |
|------|-------------|
| 突发流量 | 立即顶上，无需等待创建 |
| 扩容 | 直接激活，秒级响应 |
| 故障替换 | Client挂了，备用池补位 |
| 冷启动优化 | 避免首次请求等待初始化 |

```python
def activate_standby(self) -> ClientWrapper:
    """从备用池激活一个Client到活跃池"""
    if not self.standby_pool:
        # 备用池空了，创建新的
        new_client = self.create_client()
        self.active_pool.append(new_client)
        # 同时补充备用池
        self.refill_standby()
        return new_client

    client = self.standby_pool.pop()
    self.active_pool.append(client)
    # 补充备用池
    self.refill_standby_async()
    return client
```

---

## 十、参考

- Python `concurrent.futures.ThreadPoolExecutor`
- Linux 进程调度算法 (CFS)
- Nginx 负载均衡策略
