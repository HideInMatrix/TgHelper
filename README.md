## 单独使用
本项目深度适配faker3的TG线报脚本，在_config.py那里配置你的TG信息,然后改名成config.py
然后执行`docker build -t davidkms/jdxb:0.0.2 .`
之后再运行`docker compose up -d`

注意，一定要在你的QL里面新建配置
进入青龙容器

```sh
青龙10版本执行
touch /ql/config/qlva.sh
青龙11以后执行
touch /ql/data/config/qlva.sh

青龙面板 修改配置文件 config.sh
10添加 source /ql/config/qlva.sh
11以后添加 source /ql/data/config/qlva.sh
可以在配置文件的文件看到qlva.sh文件
```

## 配合PagerMaid-Proy使用
直接把pagermaid_plugin_jdxb.py丢入到PagerMaid-Proy文件夹中的plugins下面然后重启。依旧是要按上面操作创建青龙配置文件