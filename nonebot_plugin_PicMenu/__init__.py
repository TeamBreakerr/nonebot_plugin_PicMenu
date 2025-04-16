import re
import logging

from nonebot import get_driver
from nonebot.matcher import Matcher
from nonebot.params import Depends
from nonebot.plugin.on import on_startswith, on_fullmatch
from nonebot.adapters.onebot.v11 import Event
from nonebot.adapters.onebot.v11.message import MessageSegment
from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11.permission import GROUP_ADMIN
from nonebot import logger

# 使用 nonebot 的 logger 输出调试信息
# nonebot 的 logger 不支持 setLevel 方法
# 我们使用 logger.opt(colors=True).debug() 来输出调试信息

from .manager import MenuManager
from .img_tool import img2b64
from .metadata import __plugin_meta__


driver = get_driver()
@driver.on_bot_connect
async def _():
    print("[DEBUG] 机器人连接事件触发")
    if not menu_manager.data_manager.plugin_menu_data_list:
        print("[DEBUG] 插件菜单数据列表为空，开始加载插件信息")
        menu_manager.load_plugin_info()
    else:
        print(f"[DEBUG] 插件菜单数据列表不为空，已加载 {len(menu_manager.data_manager.plugin_menu_data_list)} 个插件的菜单数据")

menu_manager = MenuManager()
menu = on_startswith('菜单', priority=5)
switch = on_fullmatch('开关菜单', permission=SUPERUSER | GROUP_ADMIN, priority=5)


menu_switch = True
@switch.handle()
async def _():
    global menu_switch
    menu_switch = not menu_switch
    if menu_switch:
        await switch.finish(MessageSegment.text('菜单已开启'))
    else:
        await switch.finish(MessageSegment.text('菜单已关闭'))

async def check_switch(matcher: Matcher):
    if not menu_switch:
        matcher.skip()

@menu.handle()
async def _(event: Event, check=Depends(check_switch)):
    print("[DEBUG] 菜单命令触发")
    msg = str(event.get_message())
    print(f"[DEBUG] 收到消息: {msg}")
    if match_result := re.match(r'^菜单 (.*?) (.*?)$|^/菜单 (.*?) (.*?)$', msg):
        print("[DEBUG] 匹配到三级菜单模式")
        result = [x for x in match_result.groups() if x is not None]
        plugin_name = result[0]
        cmd = result[1]
        print(f"[DEBUG] 插件名: {plugin_name}, 命令: {cmd}")
        temp = menu_manager.generate_func_details_image(plugin_name, cmd)
        print(f"[DEBUG] 生成的图片类型: {type(temp)}")
        if isinstance(temp, str):
            print(f"[DEBUG] 生成图片失败, 错误信息: {temp}")
            if temp == 'PluginIndexOutRange':
                await menu.finish(MessageSegment.text('插件序号不存在'))
            elif temp == 'CannotMatchPlugin':
                await menu.finish(MessageSegment.text('插件名过于模糊或不存在'))
            elif temp == 'PluginNoFuncData':
                await menu.finish(MessageSegment.text('该插件无功能数据'))
            elif temp == 'CommandIndexOutRange':
                await menu.finish(MessageSegment.text('命令序号不存在'))
            else:
                await menu.finish(MessageSegment.text('命令过于模糊或不存在'))
        else:
            print("[DEBUG] 生成图片成功, 返回图片")
            await menu.finish(MessageSegment.image('base64://' + img2b64(temp)))
    elif match_result := re.match(r'^菜单 (.*)$|^/菜单 (.*)$', msg):
        print("[DEBUG] 匹配到二级菜单模式")
        result = [x for x in match_result.groups() if x is not None]
        plugin_name = result[0]
        print(f"[DEBUG] 插件名: {plugin_name}")
        temp = menu_manager.generate_plugin_menu_image(plugin_name)
        print(f"[DEBUG] 生成的图片类型: {type(temp)}")
        if isinstance(temp, str):
            print(f"[DEBUG] 生成图片失败, 错误信息: {temp}")
            if temp == 'PluginIndexOutRange':
                await menu.finish(MessageSegment.text('插件序号不存在'))
            else:
                await menu.finish(MessageSegment.text('插件名过于模糊或不存在'))
        else:
            print("[DEBUG] 生成图片成功, 返回图片")
            await menu.finish(MessageSegment.image('base64://' + img2b64(temp)))
    else:
        print("[DEBUG] 匹配到一级菜单模式")
        print("[DEBUG] 开始生成主菜单图片")
        img = menu_manager.generate_main_menu_image()
        print(f"[DEBUG] 生成的图片类型: {type(img)}")
        print("[DEBUG] 生成图片成功, 返回图片")
        await menu.finish(MessageSegment.image('base64://' + img2b64(img)))
