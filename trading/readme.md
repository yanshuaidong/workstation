更改迁移计划；

目前的情况

/Users/zxxk/ysd/ysdproject/workstation/test/assistant；test实验下的 老策略；

/Users/zxxk/ysd/ysdproject/workstation/test/trend；是test实验下的新策略；

后端地址：/Users/zxxk/ysd/ysdproject/workstation/automysqlback；

前端地址：/Users/zxxk/ysd/ysdproject/workstation/workfront；

数据采集：/Users/zxxk/ysd/ysdproject/workstation/database/fut_pulse；


目标；
在下面目录下面；做新的信号面板；操作建议；持仓盈亏；资金曲线；

/Users/zxxk/ysd/ysdproject/workstation/trading/strategies；
要保证独立性；不要引用test下的逻辑，配置；
strategies的定位是：从线上mysql获取数据，处理数据，将结果存储到mysql的独立模块；



信号面板：包含全部品种；仅是信号的提醒；
操作建议；是池子a中的品种；（有的会做，有的不会做）
持仓盈亏；程序自动选择的品种；
持仓盈亏；
k线展示：保持不变；

不区分机械账户和LLM 账户；之前有两个概念；经过实验llm策略并不好；

机械账户更换名字为自动化账户；


历史数据怎么办；
因为策略调整，所以历史数据需要清理；

两个策略差别巨大，之前的表结构不能用了，要如何调整；

删除之前的表结构或表；
构建适配新策略的表结构和表；






