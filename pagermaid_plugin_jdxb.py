# 该脚本从bot改过来，主要是pagermaid的插件，菜鸟新手，代码写的很垃圾。

from typing import Any, Union
import re

from pagermaid.enums import Message
from pagermaid.enums import Client
from pagermaid.listener import listener
from pagermaid.utils import lang, client
from pagermaid.single_utils import sqlite

from pyrogram.enums.chat_type import ChatType
from pyrogram.types import Chat


def try_cast_or_fallback(val: Any, t: type) -> Any:
    try:
        return t(val)
    except:
        return val


def check_chat_available(chat: Chat):
    assert chat.type == ChatType.CHANNEL and not chat.has_protected_content


async def make_request(req_type, url, params=None, headers=None, isFile=False) -> Union[str, dict]:
    """函数化一个接口请求"""
    if req_type == "get":
        response = await client.get(url, params=params, headers=headers)
    elif req_type == "post":
        response = await client.post(url, data=params, headers=headers)
    elif req_type == "put":
        response = await client.put(url, json=params, headers=headers)
    elif req_type == "delete":
        response = await client.delete(url, headers=headers)
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


async def get_ql_toke():
    """获取青龙的token"""
    d = dict(sqlite)
    resp = await make_request('get', f'{d.get("jdxb.ql_url")}/open/auth/token',
                              {'client_id': d.get("jdxb.ql_client_id"),
                               'client_secret': d.get("jdxb.ql_client_secret")})
    if resp['code'] != 200:
        _token = -1
    else:
        _token = resp['data']['token']

    return _token


async def get_qlva_config(_token):
    resp = await make_request('get', f'{sqlite["jdxb.ql_url"]}/open/configs/qlva.sh',
                              headers={'Authorization': f'Bearer {_token}'})
    if resp['code'] == 404:
        print('没有该文件')
        return []
    return extract_key_value(resp['data'])


async def update_qlva_config(_token=-1, content=''):
    resp = await make_request("post", f'{sqlite["jdxb.ql_url"]}/open/configs/save',
                              {'name': 'qlva.sh', 'content': content},
                              headers={'Authorization': f'Bearer {_token}'})
    print(f'update {resp["message"]} \n{content}')


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


async def get_corns(_token=-1):
    resp = await make_request('get', f'{sqlite["jdxb.ql_url"]}/open/crons',
                              headers={'Authorization': f'Bearer {_token}'})
    # 处理响应，这里使用示例中的数据
    # data = resp['data']['data']

    # 将数据写入JSON文件
    # file_path = 'data.json'  # 设置要写入的JSON文件路径
    # with open(file_path, 'w') as file:
    #     json.dump(data, file, indent=4)
    return resp['data']['data']


async def run_crons(_token=-1, ids=None):
    if ids is None:
        ids = []

    resp = await make_request('put', f'{sqlite["jdxb.ql_url"]}/open/crons/run',
                              headers={'Authorization': f'Bearer {_token}'},
                              params=ids)
    print(f"任务运行结果{resp}")


def find_config_by_env(configs, env_value, env_key="Env"):
    """在数组对象中找到匹配的对象"""
    matching_configs = []
    for config in configs:
        if env_key in config and env_value in config[env_key]:
            matching_configs.append(config)
    return matching_configs


async def match_script_id(_values, _send_msg, crons, token):
    matching_scripts = find_config_by_env(_values, _send_msg[0]['key'])
    # print(f'获取到到脚本{crons}')

    scipy_names = []
    for matching_script in matching_scripts:
        matching_ql_script = find_config_by_env(crons, matching_script['Script'], env_key='command')
        # print(f'匹配到到青龙脚本{matching_ql_script}')
        # if matching_ql_script is not None:
        #     print(matching_ql_script)
        print(f'匹配到到脚本{matching_script}')
        scipy_names, ids = [], []
        for item in matching_ql_script:
            ids.append(item['id'])
            scipy_names.append(item['name'])

        await run_crons(token, ids)
    return scipy_names


@listener(command="jdxb",
          description="京东线报变量传输到指定到青龙面板，具体查看https://github.com/HideInMatrix/TgHelper",
          parameters="set ql_url [ql_url](silent) 设置青龙地址 \n"
                     "set ql_client_id [id](silent) 设置青龙id \n"
                     "set ql_client_secret [secret](silent) 设置青龙secret \n"
                     "set group_id [group_id](silent) 设置监听的群 \n"
                     "set user_id [user_id](silent) 设置通知的用户 \n"
                     "del group_id [group_id](silent) 删除需要监听的群"
          )
async def set_ql_variable(client: Client, message: Message):
    if not message.parameter:
        await message.edit(f"{lang('error_prefix')}{lang('arg_error')}")
        return

    if len(message.parameter) < 3:
        await message.edit(f"{lang('error_prefix')}{lang('arg_error')}")
        return

    if message.parameter[0] == "set":
        # 记录下青龙地址
        if message.parameter[1] == 'ql_url':
            sqlite["jdxb.ql_url"] = message.parameter[2]
            await message.edit('设置青龙地址成功')

        # 记录下青龙的应用信息
        if message.parameter[1] == 'ql_client_id':
            sqlite["jdxb.ql_client_id"] = message.parameter[2]
            await message.edit('设置青龙id成功')
        if message.parameter[1] == 'ql_client_secret':
            sqlite["jdxb.ql_client_secret"] = message.parameter[2]
            await message.edit('设置青龙密钥成功')

        # 监听哪个群
        if message.parameter[1] == 'group_id':
            sqlite[f"jdxb.group_id.{message.parameter[2]}"] = message.parameter[2]
            await message.edit('设置监听群成功')

        # 执行通知
        if message.parameter[1] == 'user_id':
            sqlite["jdxb.user_id"] = message.parameter[2]
            await message.edit('设置反馈用户成功')

    if message.parameter[0] == 'del':
        if message.parameter[1] == 'group_id':
            try:
                del sqlite[f"jdxb.group_id.{message.parameter[2]}"]
            except Exception:
                return await message.edit("emm...当前对话不存在于监听列表中。")
            await message.edit(f"已成功关闭对话 {str(message.parameter[2])} 的监听功能。")


@listener(is_plugin=True, incoming=True, ignore_edited=True)
async def shift_channel_message(bot: Client, message: Message):
    """Event handler to auto forward channel messages."""
    d = dict(sqlite)
    if not d.get('jdxb.ql_client_secret') or not d.get('jdxb.ql_client_id') or not d.get("jdxb.ql_url"):
        await message.edit(f"设置青龙地址ql_url,设置青龙id ql_client_id,设置青龙secret ql_client_secret")
        return
    if not d.get(f'jdxb.group_id.{message.chat.id}'):
        # 未设置监听的群，不用监听
        return

    msg = message.text
    _send_msg = extract_key_value(msg)
    if len(_send_msg) == 0:
        print("无关消息，无需处理")
        return

    token = await get_ql_toke()

    flag = False
    if token != -1:
        results = await get_qlva_config(token)

        for result in results:
            if _send_msg[0]['key'] == result['key']:
                result['value'] = _send_msg[0]['value']

                flag = True
        if not flag:
            results.append(_send_msg[0])
        update_str = ''
        for result in results:
            update_str += f'export {result["key"]}={result["value"]}\n'
        await update_qlva_config(token, update_str)

        crons = await get_corns(token)
        _resp = await make_request('get',
                                   "https://raw.githubusercontent.com/shufflewzc/AutoSpy/master/config/Faker.spy",
                                   isFile=True)
        _values = parse_config(_resp)
        scipy_names = await match_script_id(_values, _send_msg, crons, token)

        if d.get("jdxb.user_id"):
            await bot.send_message(d.get(f"jdxb.user_id"), f'监听到线报参数\n{",".join(scipy_names)}\n开始自动执行任务')


