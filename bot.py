from typing import Union
import requests
from pyrogram import Client
from pyrogram.types import Message
import re
import logging
import config
from datetime import datetime

# 配置日志记录
logging.basicConfig(filename='app.log', filemode='w', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# 设置日志等级
logging.getLogger().setLevel(logging.INFO)

api_id = config.API_ID
api_hash = config.API_HASH
bot_token = config.BOT_TOKEN
group_chat_id = config.GROUP_CHAT_ID

ql_url = config.QL_URL
client_id = config.CLIENT_ID
client_secret = config.CLIENT_SECRET

enable_proxy = config.ENABLE_PROXY
proxy_scheme = config.PROXY_SCHEME
proxy_hostname = config.PROXY_HOSTNAME
proxy_port = config.PROXY_PORT

need_notify = config.NEED_NOTIFY
user_id = config.USER_ID


def make_request(req_type, url, params=None, headers=None, isFile=False) -> Union[str, dict]:
    """函数化一个接口请求"""
    if req_type == "get":
        response = requests.get(url, params=params, headers=headers)
    elif req_type == "post":
        response = requests.post(url, data=params, headers=headers)
    elif req_type == "put":
        response = requests.put(url, json=params, headers=headers)
    elif req_type == "delete":
        response = requests.delete(url, headers=headers)
    else:
        raise ValueError("Invalid request type. Supported types are 'get', 'post', 'put', and 'delete'.")

    if isFile:
        return response.text
    else:
        return response.json()


def extract_key_value(text):
    """分解抛出的变量和值"""
    pattern = r'export (\w+)=(".*")'
    matches = re.findall(pattern, text)
    result = []
    if matches:
        for match in matches:
            key, value = match
            result.append({'key': key, 'value': value})
    return result

def extract_key_value_with_title(text):
    """
    分解抛出的变量和值，同时解析标题，去除图标。
    """
    result = {}

    # 修改标题的正则表达式，移除前导表情符号
    title_pattern = r'[\u4e00-\u9fa5\w\s]+·'  # 匹配文字、数字和点号
    title_match = re.search(title_pattern, text)
    if title_match:
        result['title'] = title_match.group(0).replace('·', '').strip()  # 去掉末尾的点号并去除多余空格

    # 解析变量和值
    pattern = r'export (\w+)=(".*?")'
    matches = re.findall(pattern, text)
    if matches:
        result['variables'] = [{'key': key, 'value': value} for key, value in matches]
    else:
        result['variables'] = []

    return result


def get_ql_toke():
    """获取青龙的token"""
    resp = make_request('get', f'{ql_url}/open/auth/token',
                        {'client_id': client_id, 'client_secret': client_secret})
    if resp['code'] != 200:
        _token = -1
    else:
        _token = resp['data']['token']

    return _token


def get_qlva_config(_token=-1):
    resp = make_request('get', f'{ql_url}/open/configs/qlva.sh',
                        headers={'Authorization': f'Bearer {_token}'})
    if resp['code'] == 404:
        print('没有该文件')
        return []
    return extract_key_value(resp['data'])


def update_qlva_config(_token=-1, content=''):
    resp = make_request("post", f"{ql_url}/open/configs/save",
                        {'name': 'qlva.sh', 'content': content},
                        headers={'Authorization': f'Bearer {_token}'})
    logging.info(f'update {resp["message"]} \n{content}')


def parse_config(config_string):
    """分解farker脚本库spy的文档"""
    config_list = []
    items = config_string.split("- Container:")
    for item in items[1:]:
        obj = {}
        lines = item.strip().split("\n")
        for line in lines:
            if line.strip() != "":
                if ": " in line:
                    key, value = line.strip().split(": ")
                    if key == "Container":
                        obj[key] = [value.strip()]
                    elif key in ["Env", "Script"]:
                        obj[key] = value.strip()
                    elif key in ["KeyWord", "Name"]:
                        obj[key] = [value.strip()]
                    else:
                        obj[key] = int(value.strip()) if value.strip().isdigit() else value.strip()
                else:
                    obj['ScriptEnv'] = line.strip()
        config_list.append(obj)
    return config_list


def get_corns(_token=-1):
    resp = make_request('get', f'{ql_url}/open/crons', headers={'Authorization': f'Bearer {_token}'})
    # 处理响应，这里使用示例中的数据
    # data = resp['data']['data']

    # 将数据写入JSON文件
    # file_path = 'data.json'  # 设置要写入的JSON文件路径
    # with open(file_path, 'w') as file:
    #     json.dump(data, file, indent=4)
    return resp['data']['data']

# searchValue: 店铺抽奖
# page: 1
# size: 20
# filters: {}
# queryString: {"filters":null,"sorts":null,"filterRelation":"and"}
# t: 1733450195718
def search_corns_by_name(_name, _token=-1):
     # 获取当前时间的时间戳
    current_time = int(datetime.now().timestamp() * 1000)  # 转为毫秒级时间戳

    resp = make_request('get', f'{ql_url}/open/crons', headers={'Authorization': f'Bearer {_token}'}, params={'searchValue': _name,},)
    # logging.info(f'搜索结果{resp}')
    return resp['data']['data'] 

def run_crons(_token=-1, ids=None):
    if ids is None:
        ids = []

    resp = make_request('put', f'{ql_url}/open/crons/run', headers={'Authorization': f'Bearer {_token}'},
                        params=ids)
    logging.info(f"任务运行结果{resp}")


def find_config_by_env(configs, env_value, env_key="Env"):
    """在数组对象中找到匹配的对象"""
    matching_configs = []
    for config in configs:
        if env_key in config and env_value in config[env_key]:
            matching_configs.append(config)
    return matching_configs


def match_script_id(_values, _send_msg, crons, token):
    matching_scripts = find_config_by_env(_values, _send_msg[0]['key'])
    # print(f'获取到到脚本{crons}')

    scipy_names = []
    for matching_script in matching_scripts:
        matching_ql_script = find_config_by_env(crons, matching_script['Script'], env_key='command')
        # print(f'匹配到到青龙脚本{matching_ql_script}')
        # if matching_ql_script is not None:
        #     print(matching_ql_script)
        logging.info(f'匹配到到脚本{matching_script}')
        scipy_names, ids = [], []
        for item in matching_ql_script:
            ids.append(item['id'])
            scipy_names.append(item['name'])

        run_crons(token, ids)
    return scipy_names
    


def run_success():
    logging.info('启动成功')


def make_app(flag):
    if api_id == '' or api_hash == '' or bot_token == '' \
            or ql_url == '' or client_id == '' or client_secret == '':
        logging.info(f'api_id api_hash bot_token ql_url client_id client_secret 是必须的')
        return None
    if flag:
        proxy = {
            "scheme": proxy_scheme,  # "socks4", "socks5" and "http" are supported
            "hostname": proxy_hostname,
            "port": proxy_port,
        }
        logging.info(f'走了代理')
        _app = Client(
            "JDHelper",
            api_id=api_id,
            api_hash=api_hash,
            bot_token=bot_token,
            proxy=proxy
        )
    else:
        _app = Client(
            "JDHelper",
            api_id=api_id,
            api_hash=api_hash,
            bot_token=bot_token,
        )
        logging.info(f'没走代理')
    return _app


def main():
    # 创建一个APP
    app = make_app(enable_proxy)
    if app is None:
        return
    logging.info("启动中......")

    @app.on_message()
    async def echo(client: Client, message: Message):

        if message.chat.id == group_chat_id:
            # 监听到指定到群组到消息，然后开始回话
            logging.info(f'接受到消息{message.text}')
            # await message.reply(message.text)
            msg = message.text
            token = get_ql_toke()
            flag = False
            if token != -1:
                results = get_qlva_config(token)
                _send_msg = extract_key_value_with_title(msg)

                if len(_send_msg) == 0:
                    logging.info("无关消息，无需处理")
                    return

                for result in results:
                    if _send_msg['variables'][0]['key'] == result['key']:
                        result['value'] = _send_msg['variables'][0]['value']

                        flag = True
                if not flag:
                    results.append(_send_msg['variables'][0])
                update_str = ''
                for result in results:
                    update_str += f'export {result["key"]}={result["value"]}\n'
                update_qlva_config(token, update_str)

                crons = search_corns_by_name(_name=_send_msg['title'], _token=token)

                # scipy_names = match_script_id(_values, _send_msg, crons, token)
                #  crons 得到这样的数组[{id:1,name:xxx}], 将crons的id组成一个数组
                ids = [cron['id'] for cron in crons]
                logging.info(f'ids要执行{ids}{crons}')
                run_crons(token,ids)

                # if need_notify:
                    # await app.send_message(chat_id=user_id, text=f'监听到线报参数\n{",".join(_send_msg['title'])}\n开始自动执行任务')

    try:
        app.run(run_success())
    except ConnectionError as e:
        logging.info(f'启动失败 {e}')


if __name__ == '__main__':
    main()
