import abc
import json
from pathlib import Path
from typing import Tuple, List

from PIL import Image
from nonebot import logger

from .data_struct import PluginMenuData, FuncData
from .img_tool import simple_text, multi_text, calculate_text_size, ImageFactory, Box, auto_resize_text

class PicTemplate(metaclass=abc.ABCMeta):  # 模板类
    def __init__(self):
        pass

    @abc.abstractmethod
    def load_resource(self):
        """
        模板文件加载抽象方法
        """
        pass

    @abc.abstractmethod
    def generate_main_menu(self, data: Tuple[List, List]) -> Image:
        """
        生成一级菜单抽象方法
        :param data: Tuple[List(插件名), List(插件des)]
        :return: Image对象
        """
        pass

    @abc.abstractmethod
    def generate_plugin_menu(self, plugin_data: PluginMenuData) -> Image:
        """
        生成二级菜单抽象方法
        :param plugin_data: PluginMenuData对象
        :return: Image对象
        """
        pass

    @abc.abstractmethod
    def generate_original_plugin_menu(self, plugin_data: PluginMenuData) -> Image:
        """
        在插件的PluginMetadata中extra无menu_data的内容时，使用该方法生成简易版图片
        :param plugin_data: PluginMetadata对象
        :return: Image对象
        """
        pass

    @abc.abstractmethod
    def generate_command_details(self, func_data: FuncData) -> Image:
        """
        生成三级级菜单抽象方法
        :param func_data: FuncData对象
        :return: Image对象
        """
        pass


class DefaultTemplate(PicTemplate):
    def __init__(self):
        super().__init__()
        self.name = 'default'
        self.load_resource()
        self.colors = {
            'blue': (34, 52, 73),
            'yellow': (224, 164, 25),
            'white': (237, 239, 241)
        }
        self.basic_font_size = 25

    def load_resource(self):
        cwd = Path.cwd()
        with (cwd / 'menu_config' / 'config.json').open('r', encoding='utf-8') as fp:
            config = json.loads(fp.read())
        self.using_font = config['default']

    def generate_main_menu(self, data) -> Image:
        print("[DEBUG] 开始生成主菜单图片")
        print(f"[DEBUG] 收到的数据: {data}")

        # 检查数据是否有效
        plugin_names, plugin_descriptions = data
        if not plugin_names:
            print("[ERROR] 插件名列表为空，使用描述列表的索引作为插件名")
            plugin_names = [f"插件 {i+1}" for i in range(len(plugin_descriptions))]
            data = (plugin_names, plugin_descriptions)
            print(f"[DEBUG] 修正后的数据: {data}")

        # 列数
        column_count = len(data) + 1
        # 数据行数
        row_count = len(data[0])

        print(f"[DEBUG] 生成主菜单，插件数量: {row_count}")
        for i in range(row_count):
            print(f"[DEBUG] 插件 {i+1}: {data[0][i]}, 描述: {data[1][i]}")
        # 数据及表头尺寸测算
        row_size_list = [tuple(
                map(lambda _x: calculate_text_size(_x, self.basic_font_size, self.using_font),
                    ('序号', '插件名', '插件描述'))
        )]
        # 计算id，插件名，插件描述的尺寸
        for x in range(row_count):
            index_size = calculate_text_size(str(x + 1), self.basic_font_size, self.using_font)
            plugin_name_size = calculate_text_size(data[0][x], self.basic_font_size, self.using_font)
            plugin_description_size = multi_text(data[1][x],
                                                 default_font=self.using_font,
                                                 default_size=25,
                                                 box_size=(300, 0)
                                                 ).size
            row_size_list.append((index_size, plugin_name_size, plugin_description_size))
        # 单元格边距
        margin = 10
        # 确定每行的行高
        row_height_list = [max(map(lambda i: i[1], row_size_list[x])) + margin * 2 for x in range(row_count + 1)]
        # 确定每列的列宽
        col_max_width_tuple = (
            max((x[0][0] + margin * 2 for x in row_size_list)),
            max((x[1][0] + margin * 2 for x in row_size_list)),
            max((x[2][0] + margin * 2 for x in row_size_list))
        )
        # 确定表格底版的长和宽
        table_width = sum(col_max_width_tuple) + 3
        table_height = sum(row_height_list) + 3
        table = ImageFactory(
            Image.new('RGBA', (table_width, table_height), self.colors['white'])
        )
        # 绘制基点和移动锚点
        initial_point, basis_point = (1, 1), [1, 1]
        # 为单元格添加box和绘制边框
        for row_id in range(row_count + 1):
            for col_id in range(column_count):
                box_size = (col_max_width_tuple[col_id], row_height_list[row_id])
                table.add_box(f'box_{row_id}_{col_id}',
                              tuple(basis_point),
                              tuple(box_size))
                table.rectangle(f'box_{row_id}_{col_id}', outline=self.colors['blue'], width=2)
                basis_point[0] += box_size[0]
            basis_point[0] = initial_point[0]
            basis_point[1] += row_height_list[row_id]
        # 向单元格中填字
        for i, text in enumerate(('序号', '插件名', '插件描述')):
            header = simple_text(text, self.basic_font_size, self.using_font, self.colors['blue'])
            table.img_paste(
                header,
                table.align_box(f'box_0_{i}', header, align='center'),
                isalpha=True
            )
        for x in range(row_count):
            row_id = x + 1
            id_text = simple_text(str(row_id), self.basic_font_size, self.using_font, self.colors['blue'])
            table.img_paste(
                id_text,
                table.align_box(f'box_{row_id}_0', id_text, align='center'),
                isalpha=True
            )
            plugin_name_text = simple_text(data[0][x], self.basic_font_size, self.using_font, self.colors['blue'])
            table.img_paste(
                plugin_name_text,
                table.align_box(f'box_{row_id}_1', plugin_name_text, align='center'),
                isalpha=True
            )
            plugin_description_text = multi_text(data[1][x],
                                                 box_size=(300, 0),
                                                 default_font=self.using_font,
                                                 default_color=self.colors['blue'],
                                                 default_size=self.basic_font_size
                                                 )
            table.img_paste(
                plugin_description_text,
                table.align_box(f'box_{x+1}_2', plugin_description_text, align='center'),
                isalpha=True
            )
        table_size = table.img.size
        # 添加注释
        note_basic_text = simple_text('注：',
                                      size=self.basic_font_size,
                                      color=self.colors['blue'],
                                      font=self.using_font)
        note_text = multi_text('查询菜单的详细使用方法请发送\n[菜单 PicMenu]',
                               box_size=(table_size[0] - 30 - note_basic_text.size[0] - 10, 0),
                               default_font=self.using_font,
                               default_color=self.colors['blue'],
                               default_size=self.basic_font_size,
                               spacing=4,
                               horizontal_align="middle"
                               )
        note_img = ImageFactory(
            Image.new('RGBA',
                      (note_text.size[0] + 10 + note_basic_text.size[0],
                       max((note_text.size[1], note_basic_text.size[1]))),
                      self.colors['white'])
        )
        note_img.img_paste(note_basic_text, (0, 0), isalpha=True)
        note_img.img_paste(note_text, (note_basic_text.size[0] + 10, 0), isalpha=True)
        main_menu = ImageFactory(
            Image.new('RGBA',
                      (table_size[0] + 140, table_size[1] + note_img.img.size[1] + 210),
                      color=self.colors['white'])
        )
        main_menu.img_paste(
            note_img.img,
            main_menu.align_box('self', table.img, pos=(0, 140), align='horizontal')
        )
        main_menu.img_paste(
            table.img,
            main_menu.align_box('self', table.img, pos=(0, 160 + note_img.img.size[1]), align='horizontal')
        )
        main_menu.add_box('border_box',
                          main_menu.align_box('self',
                                              (table_size[0] + 40, table_size[1] + note_img.img.size[1] + 80),
                                              pos=(0, 100),
                                              align='horizontal'),
                          (table_size[0] + 40, table_size[1] + note_img.img.size[1] + 90))
        main_menu.rectangle('border_box', outline=self.colors['blue'], width=5)
        border_box_top_left = main_menu.boxes['border_box'].topLeft
        main_menu.rectangle(Box((border_box_top_left[0] - 25, border_box_top_left[1] - 25),
                                (50, 50)), outline=self.colors['yellow'], width=5)
        main_menu.add_box('title_box', (0, 0), (main_menu.get_size()[0], 100))
        title = auto_resize_text('插件菜单', 60, self.using_font, (table_width-60, 66), self.colors['blue'])
        main_menu.img_paste(title, main_menu.align_box('title_box', title, align='center'), isalpha=True)
        return main_menu.img

    def generate_plugin_menu(self, plugin_data: PluginMenuData) -> Image:
        plugin_name = plugin_data.name
        data = plugin_data.funcs
        column_count = 5
        row_count = len(data)
        # 检查数据中是否有触发方式和功能简述
        has_trigger_method = any(func.trigger_method for func in data)
        has_brief_des = any(func.brief_des for func in data)

        # 准备表头
        headers = ['序号', '功能']
        if has_trigger_method:
            headers.append('触发方式')
        headers.append('触发条件')  # 触发条件始终显示
        if has_brief_des:
            headers.append('功能简述')

        # 打印调试信息
        print(f"[DEBUG] 表头: {headers}")
        print(f"[DEBUG] 有触发方式: {has_trigger_method}, 有功能简述: {has_brief_des}")

        # 数据及表头尺寸测算
        row_size_list = [tuple(
            map(
                lambda _x: calculate_text_size(_x, self.basic_font_size, self.using_font),
                headers
            )
        )]
        for index, func_data in enumerate(data):
            # 准备行数据
            row_data = []

            # 序号和功能始终显示
            index_size = calculate_text_size(str(index + 1), self.basic_font_size, self.using_font)
            row_data.append(index_size)

            func_size = calculate_text_size(func_data.func or "", self.basic_font_size, self.using_font)
            row_data.append(func_size)

            # 触发方式可选
            if has_trigger_method:
                method_size = calculate_text_size(func_data.trigger_method or "", self.basic_font_size, self.using_font)
                row_data.append(method_size)

            # 触发条件始终显示
            condition_size = calculate_text_size(func_data.trigger_condition or "", self.basic_font_size, self.using_font)
            row_data.append(condition_size)

            # 功能简述可选
            if has_brief_des:
                if func_data.brief_des:
                    # 使用更大的文本框宽度来计算多行文本的大小
                    brief_des_size = multi_text(func_data.brief_des,
                                                default_font=self.using_font,
                                                default_size=25,
                                                box_size=(500, 0),  # 进一步增加文本框宽度
                                                spacing=15  # 进一步增加行间距
                                                ).size
                else:
                    brief_des_size = (0, 0)
                row_data.append(brief_des_size)

            # 添加行数据
            row_size_list.append(tuple(row_data))

            # 打印调试信息
            print(f"[DEBUG] 行 {index+1} 数据: {row_data}")
        # 边距
        margin = 10  # 使用与主菜单相同的边距值
        # 测行高 - 为多行文本提供更多空间
        row_height_list = []
        for x in range(row_count+1):
            # 获取当前行中所有单元格的高度
            heights = [i[1] for i in row_size_list[x]]
            max_height = max(heights)

            # 如果是数据行（非表头）且有功能简述列，为其提供额外空间
            if x > 0 and has_brief_des:
                # 获取功能简述列的索引
                brief_des_index = 4 if has_trigger_method else 3
                if len(row_size_list[x]) > brief_des_index:
                    # 为功能简述提供额外的空间，确保文字能完全显示
                    brief_des_height = row_size_list[x][brief_des_index][1]
                    # 如果文本高度超过一定值，说明可能是多行文本，提供少量额外空间
                    if brief_des_height > self.basic_font_size * 1.5:
                        max_height = max(max_height, brief_des_height * 1.1)  # 只增加10%的空间

            row_height_list.append(max_height + margin * 2)

        # 计算列宽度
        col_max_width_list = []
        for col_id in range(len(headers)):
            # 获取当前列的最大宽度
            col_width = max((x[col_id][0] + margin * 2 for x in row_size_list))

            # 如果是功能简述列，提供更多空间
            if has_brief_des:
                brief_des_index = 4 if has_trigger_method else 3
                if col_id == brief_des_index:
                    # 如果是功能简述列，确保宽度适当
                    col_width = max(col_width, 400)

            col_max_width_list.append(col_width)

        # 打印调试信息
        print(f"[DEBUG] 列宽度: {col_max_width_list}")

        # 建立表格画板
        table_width = sum(col_max_width_list) + 3
        table_height = sum(row_height_list) + 3
        table = ImageFactory(
            Image.new('RGBA', (table_width, table_height), self.colors['white'])
        )
        initial_point, basis_point = (1, 1), [1, 1]

        # 列数重新计算
        column_count = len(headers)
        print(f"[DEBUG] 列数: {column_count}")

        # 建立基准box
        for row_id in range(row_count + 1):
            for col_id in range(column_count):
                box_size = (col_max_width_list[col_id], row_height_list[row_id])
                table.add_box(f'box_{row_id}_{col_id}',
                              tuple(basis_point),
                              tuple(box_size))
                table.rectangle(f'box_{row_id}_{col_id}', outline=self.colors['blue'], width=2)
                basis_point[0] += box_size[0]
            basis_point[0] = initial_point[0]
            basis_point[1] += row_height_list[row_id]
        # 向单元格中填入表头
        for i, text in enumerate(headers):
            header = simple_text(text, self.basic_font_size, self.using_font, self.colors['blue'])
            table.img_paste(
                header,
                table.align_box(f'box_0_{i}', header, align='center'),
                isalpha=True
            )
            print(f"[DEBUG] 渲染表头 {i}: {text}")
        # 填字
        for index, func_data in enumerate(data):
            row_id = index + 1
            col_id = 0  # 列索引

            # 第一个cell填id（序号始终显示）
            id_text = simple_text(str(row_id), self.basic_font_size, self.using_font, self.colors['blue'])
            table.img_paste(
                id_text,
                table.align_box(f'box_{row_id}_{col_id}', id_text, align='center'),
                isalpha=True
            )
            col_id += 1

            # 第二个cell里填func（功能始终显示）
            func_text = simple_text(func_data.func or "", self.basic_font_size, self.using_font, self.colors['blue'])
            table.img_paste(
                func_text,
                table.align_box(f'box_{row_id}_{col_id}', func_text, align='center'),
                isalpha=True
            )
            col_id += 1

            # 第三个cell里填trigger_method（触发方式可选）
            if has_trigger_method:
                trigger_method_text = simple_text(func_data.trigger_method or "", self.basic_font_size, self.using_font,
                                                self.colors['blue'])
                table.img_paste(
                    trigger_method_text,
                    table.align_box(f'box_{row_id}_{col_id}', trigger_method_text, align='center'),
                    isalpha=True
                )
                col_id += 1

            # 第四个cell里填trigger_condition（触发条件始终显示）
            trigger_condition_text = simple_text(func_data.trigger_condition or "", self.basic_font_size, self.using_font,
                                                 self.colors['blue'])
            table.img_paste(
                trigger_condition_text,
                table.align_box(f'box_{row_id}_{col_id}', trigger_condition_text, align='center'),
                isalpha=True
            )
            col_id += 1

            # 第五个cell里填brief_des（功能简述可选）
            if has_brief_des:
                # 获取当前列的宽度，减去边距作为文本框的宽度
                col_width = col_max_width_list[col_id] - margin * 2
                # 获取当前行的高度，减去边距作为文本框的高度
                row_height = row_height_list[row_id] - margin * 2

                # 渲染多行文本，使用实际列宽作为文本框宽度
                brief_des_text = multi_text(func_data.brief_des or "",
                                            box_size=(col_width - margin * 2, row_height - margin * 2),  # 进一步减少单元格大小以留出更多边距
                                            default_font=self.using_font,
                                            default_color=self.colors['blue'],
                                            default_size=self.basic_font_size,
                                            spacing=20,  # 进一步增加行间距
                                            h_border_ignore=False,  # 不忽略水平边界
                                            v_border_ignore=False   # 不忽略垂直边界
                                            )

                # 打印调试信息
                print(f"[DEBUG] 功能简述文本大小: {brief_des_text.size}, 单元格大小: ({col_width}, {row_height})")

                table.img_paste(
                    brief_des_text,
                    table.align_box(f'box_{row_id}_{col_id}', brief_des_text, align='center'),
                    isalpha=True
                )
                col_id += 1

            print(f"[DEBUG] 渲染行 {row_id} 完成，共 {col_id} 列")
        # 获取table尺寸
        table_size = table.img.size

        # 初始化usage相关变量
        usage_text_size = (0, 0)
        usage_img = None

        # 只有当usage存在时才渲染
        if plugin_data.usage:
            usage_basic_text = simple_text('用法：',
                                        size=self.basic_font_size,
                                        color=self.colors['blue'],
                                        font=self.using_font)
            usage_text = multi_text(plugin_data.usage,
                                    box_size=(table_size[0] - 30 - usage_basic_text.size[0] - 10, 0),
                                    default_font=self.using_font,
                                    default_color=self.colors['blue'],
                                    default_size=self.basic_font_size,
                                    spacing=10  # 增加行间距
                                    )
            # 合成usage文字图片
            usage_img = ImageFactory(
                Image.new('RGBA',
                        (usage_text.size[0] + 10 + usage_basic_text.size[0],
                        max((usage_text.size[1], usage_basic_text.size[1]))),
                        self.colors['white'])
            )
            usage_img.img_paste(usage_basic_text, (0, 0), isalpha=True)
            usage_img.img_paste(usage_text, (usage_basic_text.size[0] + 10, 0), isalpha=True)
            usage_text_size = usage_img.img.size
        # 底部画板，大小根据table大小和usage文字大小确定
        main_menu = ImageFactory(
            Image.new(
                'RGBA',
                (table_size[0] + 140,
                 table_size[1] + usage_text_size[1] + 210),
                color=self.colors['white']
            )
        )

        # 初始化位置
        pos = (0, 130)

        # 如果有usage，则粘贴usage
        if plugin_data.usage and usage_img:
            pos, _ = main_menu.img_paste(
                usage_img.img,
                main_menu.align_box('self', usage_img.img, pos=pos, align='horizontal'),
                isalpha=True
            )
            # 计算表格的位置，考虑usage的高度
            table_pos = (0, pos[1] + usage_text_size[1] + 20)
        else:
            # 如果没有usage，表格直接放在顶部
            table_pos = pos

        # 在底部画板上粘贴表格
        main_menu.img_paste(
            table.img,
            main_menu.align_box('self', table.img, pos=table_pos, align='horizontal')
        )
        # 给表格添加装饰性边框
        main_menu.add_box('border_box',
                          main_menu.align_box('self',
                                              (table_size[0] + 40, table_size[1] + 70),
                                              pos=(0, 100),
                                              align='horizontal'),
                          (table_size[0] + 40, table_size[1] + usage_text_size[1] + 70))
        main_menu.rectangle('border_box', outline=self.colors['blue'], width=5)
        border_box_top_left = main_menu.boxes['border_box'].topLeft
        main_menu.rectangle(Box((border_box_top_left[0] - 25, border_box_top_left[1] - 25),
                                (50, 50)), outline=self.colors['yellow'], width=5)
        main_menu.add_box('title_box', (0, 0), (main_menu.get_size()[0], 100))
        # 添加插件名title
        title = auto_resize_text(plugin_name, 60, self.using_font, (table_width - 60, 66), self.colors['blue'])
        main_menu.img_paste(title, main_menu.align_box('title_box', title, align='center'), isalpha=True)
        return main_menu.img

    def generate_original_plugin_menu(self, plugin_data: PluginMenuData) -> Image:
        # 初始化usage相关变量
        usage_text_size = (0, 0)
        usage_img = None

        # 只有当usage存在时才渲染
        if plugin_data.usage:
            usage_basic_text = simple_text('用法：',
                                        size=self.basic_font_size,
                                        color=self.colors['blue'],
                                        font=self.using_font)
            usage_text = multi_text(plugin_data.usage,
                                    box_size=(600, 0),
                                    default_font=self.using_font,
                                    default_color=self.colors['blue'],
                                    default_size=self.basic_font_size,
                                    spacing=10  # 增加行间距
                                    )
            # 合成usage文字图片
            usage_img = ImageFactory(
                Image.new('RGBA', (usage_text.size[0] + 10 + usage_basic_text.size[0],
                                max((usage_text.size[1], usage_basic_text.size[1]))),
                        self.colors['white'])
            )
            usage_img.img_paste(usage_basic_text, (0, 0), isalpha=True)
            usage_img.img_paste(usage_text, (usage_basic_text.size[0] + 10, 0), isalpha=True)
            usage_text_size = usage_img.img.size
        # 主画布
        main_menu = ImageFactory(
            Image.new(
                'RGBA',
                (max(usage_text_size[0], 600) + 140,  # 确保有最小宽度
                 usage_text_size[1] + 210),
                color=self.colors['white']
            )
        )

        # 添加边框Box
        border_size = (max(usage_text_size[0], 600) + 60, usage_text_size[1] + 70)
        main_menu.add_box('border_box',
                          main_menu.align_box('self',
                                              border_size,
                                              pos=(0, 100),
                                              align='horizontal'),
                          (border_size[0] + 10, border_size[1]))

        # 只有当usage存在时才粘贴usage文字图片
        if plugin_data.usage and usage_img:
            main_menu.img_paste(
                usage_img.img,
                main_menu.align_box('border_box', usage_img.img, align='center'),
                isalpha=True
            )
        # 添加装饰性边框
        main_menu.rectangle('border_box', outline=self.colors['blue'], width=5)
        border_box_top_left = main_menu.boxes['border_box'].topLeft
        main_menu.rectangle(Box((border_box_top_left[0] - 25, border_box_top_left[1] - 25),
                                (50, 50)), outline=self.colors['yellow'], width=5)
        main_menu.add_box('title_box', (0, 0), (main_menu.get_size()[0], 100))
        # 添加插件名title
        title = auto_resize_text(plugin_data.name,
                                 60,
                                 self.using_font,
                                 (usage_text_size[0] - 40, 66),
                                 self.colors['blue']
                                 )
        main_menu.img_paste(title, main_menu.align_box('title_box', title, align='center'), isalpha=True)
        return main_menu.img

    def generate_command_details(self, func_data: FuncData) -> Image:
        # 准备要显示的数据和标签
        data_items = [
            ('功能：', func_data.func),  # 功能始终显示
            ('触发方式：', func_data.trigger_method),  # 可选
            ('触发条件：', func_data.trigger_condition),  # 触发条件始终显示
            ('详细描述：', func_data.detail_des)  # 可选
        ]

        # 过滤掉空值
        filtered_items = [(label, content) for label, content in data_items if content is not None]

        # 如果没有内容，至少保留功能和触发条件
        if len(filtered_items) < 2:
            filtered_items = [
                ('功能：', func_data.func),
                ('触发条件：', func_data.trigger_condition)
            ]

        # 获取标签文字
        labels = [item[0] for item in filtered_items]
        contents = [item[1] for item in filtered_items]

        # 获取标签文字
        basis_text_list = [simple_text(text, self.basic_font_size, self.using_font, self.colors['blue'])
                           for text in labels]
        # 获取标签文字的大小
        basis_text_size_list = [x.size for x in basis_text_list]
        # 信息起始位置
        info_text_start_x = max([x[0] for x in basis_text_size_list])
        # 将文字转换为图片
        text_img_list = []
        for content in contents:
            text_img_list.append(
                multi_text(content,
                           box_size=(680 - info_text_start_x, 0),
                           default_font=self.using_font,
                           default_color=self.colors['blue'],
                           default_size=self.basic_font_size,
                           spacing=5,  # 减小行间距
                           v_border_ignore=True
                           )
            )
        # 获取文字图片的大小
        text_size_list = [x.size for x in text_img_list]
        # 获取同一行最大高度
        line_max_height_list = [max(x) for x in
                                zip(map(lambda y: y[1], text_size_list), map(lambda y: y[1], basis_text_size_list))]
        # 文字画板，每行间距30
        text_img = ImageFactory(
            Image.new('RGBA',
                      (info_text_start_x + 40 + text_img_list[0].size[0], sum(line_max_height_list) + 30),
                      color=self.colors['white'])
        )
        # 动态添加每个标签和内容
        box_names = []

        # 添加第一个项目
        box_name = 'item_0_box'
        box_names.append(box_name)
        text_img.add_box(box_name, (0, 0), (680, max((basis_text_size_list[0][1], text_size_list[0][1]))))
        pos, _ = text_img.img_paste(basis_text_list[0],
                                   text_img.align_box(box_name, basis_text_list[0]),
                                   isalpha=True)
        text_img.img_paste(text_img_list[0],
                          text_img.align_box(box_name, text_img_list[0],
                                            pos=(info_text_start_x + 40, pos[1])),
                          isalpha=True)

        # 添加其余项目
        for i in range(1, len(basis_text_list)):
            box_name = f'item_{i}_box'
            box_names.append(box_name)
            # 使用前一个box的底部作为起始位置
            text_img.add_box(box_name,
                             (0, text_img.boxes[box_names[i-1]].bottom + 10),
                             (680, max((basis_text_size_list[i][1], text_size_list[i][1]))))
            pos, _ = text_img.img_paste(basis_text_list[i],
                                       text_img.align_box(box_name, basis_text_list[i]),
                                       isalpha=True)
            text_img.img_paste(text_img_list[i],
                              text_img.align_box(box_name, text_img_list[i],
                                                pos=(info_text_start_x + 40, pos[1])),
                              isalpha=True)
        text_img_size = text_img.img.size
        detail_img = ImageFactory(Image.new('RGBA', (800, text_img_size[1] + 120), color=self.colors['white']))
        detail_img.add_box('text_border_box', (20, 100), (760, text_img_size[1] + 20))
        detail_img.rectangle('text_border_box', outline=self.colors['blue'], width=1)
        detail_img.img_paste(text_img.img, detail_img.align_box('text_border_box', text_img.img, align='center'))
        detail_img.add_box('upper_box', (0, 0), (800, 100))
        detail_img.add_box('blue_box', detail_img.align_box('upper_box', (700, 20), align='center'), (700, 20))
        detail_img.rectangle('blue_box', outline=self.colors['blue'], width=5)
        detail_img.add_box('yellow_box',
                           (detail_img.boxes['blue_box'].left - 25, detail_img.boxes['blue_box'].top - 15), (50, 50))
        detail_img.rectangle('yellow_box', outline=self.colors['yellow'], width=5)
        return detail_img.img
