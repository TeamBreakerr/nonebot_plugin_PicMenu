from typing import List, Union

from pydantic import BaseModel

# 功能的数据信息
class FuncData(BaseModel):
    func: str
    trigger_condition: str
    trigger_method: Union[str, None] = None  # 可选字段
    brief_des: Union[str, None] = None  # 可选字段
    detail_des: Union[str, None] = None  # 可选字段

# 插件菜单的数据信息
class PluginMenuData(BaseModel):
    name: str
    description: str
    usage: Union[str, None] = None  # 可选字段
    funcs: Union[List[FuncData], None] = None
    template: str = 'default'
    visible: bool = True  # 控制插件是否在菜单中展示
