import torch
import numpy as np
from PIL import Image, ImageOps
import os
import json
import folder_paths

class ImageRepeatConfig:
    """图像重复配置节点 - 用于设置复制参数"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "rows": ("INT", {
                    "default": 2,
                    "min": 1,
                    "max": 100,
                    "step": 1,
                    "display": "number"
                }),
                "columns": ("INT", {
                    "default": 3,
                    "min": 1,
                    "max": 100,
                    "step": 1,
                    "display": "number"
                }),
                "horizontal_spacing": ("INT", {
                    "default": 10,
                    "min": 0,
                    "max": 1000,
                    "step": 1,
                    "display": "number"
                }),
                "vertical_spacing": ("INT", {
                    "default": 10,
                    "min": 0,
                    "max": 1000,
                    "step": 1,
                    "display": "number"
                }),
                "background_color": (["transparent", "white", "black", "custom"],),
                "custom_color_hex": ("STRING", {
                    "default": "#FFFFFF",
                    "multiline": False
                }),
                "rotation_angle": ("FLOAT", {
                    "default": 0.0,
                    "min": -360.0,
                    "max": 360.0,
                    "step": 1.0,
                    "display": "number"
                }),
                "scale": ("FLOAT", {
                    "default": 1.0,
                    "min": 0.01,
                    "max": 10.0,
                    "step": 0.01,
                    "display": "number"
                }),
                "mirror_horizontal": ("BOOLEAN", {"default": False}),
                "mirror_vertical": ("BOOLEAN", {"default": False}),
                "mirror_horizontal_spacing": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 1000,
                    "step": 1,
                    "display": "number"
                }),
                "mirror_vertical_spacing": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 1000,
                    "step": 1,
                    "display": "number"
                }),
                "opacity": ("FLOAT", {
                    "default": 1.0,
                    "min": 0.0,
                    "max": 1.0,
                    "step": 0.01,
                    "display": "number"
                }),
            }
        }
    
    RETURN_TYPES = ("IMAGE", "REPEAT_CONFIG",)
    RETURN_NAMES = ("图像", "配置",)
    FUNCTION = "create_config"
    CATEGORY = "图像/变换"
    
    def create_config(self, image, rows, columns, horizontal_spacing, vertical_spacing,
                     background_color, custom_color_hex, rotation_angle, scale,
                     mirror_horizontal, mirror_vertical, mirror_horizontal_spacing, mirror_vertical_spacing, opacity):
        config = {
            "rows": rows,
            "columns": columns,
            "horizontal_spacing": horizontal_spacing,
            "vertical_spacing": vertical_spacing,
            "background_color": background_color,
            "custom_color_hex": custom_color_hex,
            "rotation_angle": rotation_angle,
            "scale": scale,
            "mirror_horizontal": mirror_horizontal,
            "mirror_vertical": mirror_vertical,
            "mirror_horizontal_spacing": mirror_horizontal_spacing,
            "mirror_vertical_spacing": mirror_vertical_spacing,
            "opacity": opacity
        }
        return (image, config,)


class ImageRepeatPreview:
    """图像重复预览节点 - 实时显示复制效果"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "config": ("REPEAT_CONFIG",),
            }
        }
    
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("输出图像",)
    FUNCTION = "repeat_image"
    OUTPUT_NODE = True
    CATEGORY = "图像/变换"
    
    def repeat_image(self, image, config):
        # 将tensor转换为PIL图像
        i = 255. * image[0].cpu().numpy()
        img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))
        
        # 获取配置参数
        rows = config["rows"]
        columns = config["columns"]
        h_spacing = config["horizontal_spacing"]
        v_spacing = config["vertical_spacing"]
        bg_color = config["background_color"]
        custom_color_hex = config["custom_color_hex"]
        rotation_angle = config["rotation_angle"]
        scale_factor = config["scale"]
        mirror_h = config["mirror_horizontal"]
        mirror_v = config["mirror_vertical"]
        mirror_h_spacing = config["mirror_horizontal_spacing"]
        mirror_v_spacing = config["mirror_vertical_spacing"]
        opacity = config["opacity"]
        
        # 解析hex颜色
        custom_color = self._hex_to_rgb(custom_color_hex)
        
        # 应用变换（镜像、缩放、旋转）
        img = self._apply_transformations(img, rotation_angle, scale_factor, mirror_h, mirror_v, opacity)
        
        # 获取变换后的图像尺寸
        orig_width, orig_height = img.size
        
        # 计算输出图像尺寸（考虑镜像间距）
        total_h_spacing = h_spacing
        total_v_spacing = v_spacing
        if mirror_h:
            total_h_spacing += mirror_h_spacing
        if mirror_v:
            total_v_spacing += mirror_v_spacing
            
        output_width = orig_width * columns + total_h_spacing * (columns - 1)
        output_height = orig_height * rows + total_v_spacing * (rows - 1)
        
        # 确定背景颜色
        if bg_color == "transparent":
            # 创建透明背景
            output_img = Image.new('RGBA', (output_width, output_height), (0, 0, 0, 0))
            # 确保原图也是RGBA模式
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
        elif bg_color == "white":
            output_img = Image.new('RGB', (output_width, output_height), (255, 255, 255))
            if img.mode == 'RGBA':
                # 白色背景上合成RGBA图像
                temp_img = Image.new('RGB', img.size, (255, 255, 255))
                temp_img.paste(img, mask=img.split()[3] if len(img.split()) == 4 else None)
                img = temp_img
        elif bg_color == "black":
            output_img = Image.new('RGB', (output_width, output_height), (0, 0, 0))
            if img.mode == 'RGBA':
                temp_img = Image.new('RGB', img.size, (0, 0, 0))
                temp_img.paste(img, mask=img.split()[3] if len(img.split()) == 4 else None)
                img = temp_img
        else:  # custom
            output_img = Image.new('RGB', (output_width, output_height), custom_color)
            if img.mode == 'RGBA':
                temp_img = Image.new('RGB', img.size, custom_color)
                temp_img.paste(img, mask=img.split()[3] if len(img.split()) == 4 else None)
                img = temp_img
        
        # 复制图像到网格中
        for row in range(rows):
            for col in range(columns):
                x = col * (orig_width + h_spacing)
                y = row * (orig_height + v_spacing)
                
                if output_img.mode == 'RGBA' and img.mode == 'RGBA':
                    # 透明模式下使用alpha合成
                    output_img.paste(img, (x, y), img)
                else:
                    output_img.paste(img, (x, y))
        
        # 转换回tensor
        output_array = np.array(output_img).astype(np.float32) / 255.0
        if len(output_array.shape) == 2:  # 灰度图
            output_array = np.expand_dims(output_array, axis=2)
        if output_array.shape[2] == 4:  # RGBA
            # 保留alpha通道
            pass
        elif output_array.shape[2] == 1:  # 灰度
            output_array = np.repeat(output_array, 3, axis=2)
        
        output_tensor = torch.from_numpy(output_array).unsqueeze(0)
        
        # 保存临时预览图像
        temp_dir = folder_paths.get_temp_directory()
        temp_file = os.path.join(temp_dir, "image_repeat_preview.png")
        output_img.save(temp_file)
        
        return {
            "ui": {
                "images": [
                    {
                        "filename": "image_repeat_preview.png",
                        "subfolder": "",
                        "type": "temp"
                    }
                ]
            },
            "result": (output_tensor,)
        }
    
    def _hex_to_rgb(self, hex_color):
        """将hex颜色转换为RGB元组"""
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 6:
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        return (255, 255, 255)  # 默认白色
    
    def _apply_transformations(self, img, rotation, scale, mirror_h, mirror_v, opacity):
        """应用镜像、缩放、旋转和不透明度变换"""
        # 确保图像有alpha通道以支持不透明度
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        # 镜像
        if mirror_h:
            img = ImageOps.mirror(img)
        if mirror_v:
            img = ImageOps.flip(img)
        
        # 缩放
        if scale != 1.0:
            new_width = int(img.width * scale)
            new_height = int(img.height * scale)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # 旋转（保持透明度）
        if rotation != 0:
            img = img.rotate(rotation, expand=True, resample=Image.Resampling.BICUBIC)
        
        # 应用不透明度
        if opacity < 1.0:
            alpha = img.split()[3]
            alpha = alpha.point(lambda p: int(p * opacity))
            img.putalpha(alpha)
        
        return img


class ImageRepeatSimple:
    """图像重复节点 - 简化版（单节点完成所有功能）"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "rows": ("INT", {
                    "default": 2,
                    "min": 1,
                    "max": 100,
                    "step": 1,
                    "display": "number"
                }),
                "columns": ("INT", {
                    "default": 3,
                    "min": 1,
                    "max": 100,
                    "step": 1,
                    "display": "number"
                }),
                "horizontal_spacing": ("INT", {
                    "default": 10,
                    "min": 0,
                    "max": 1000,
                    "step": 1,
                    "display": "number"
                }),
                "vertical_spacing": ("INT", {
                    "default": 10,
                    "min": 0,
                    "max": 1000,
                    "step": 1,
                    "display": "number"
                }),
                "background_color": (["transparent", "white", "black", "custom"],),
                "custom_color_hex": ("STRING", {
                    "default": "#FFFFFF",
                    "multiline": False
                }),
                "rotation_angle": ("FLOAT", {
                    "default": 0.0,
                    "min": -360.0,
                    "max": 360.0,
                    "step": 1.0,
                    "display": "number"
                }),
                "scale": ("FLOAT", {
                    "default": 1.0,
                    "min": 0.01,
                    "max": 10.0,
                    "step": 0.01,
                    "display": "number"
                }),
                "mirror_horizontal": ("BOOLEAN", {"default": False}),
                "mirror_vertical": ("BOOLEAN", {"default": False}),
                "mirror_horizontal_spacing": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 1000,
                    "step": 1,
                    "display": "number"
                }),
                "mirror_vertical_spacing": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 1000,
                    "step": 1,
                    "display": "number"
                }),
                "opacity": ("FLOAT", {
                    "default": 1.0,
                    "min": 0.0,
                    "max": 1.0,
                    "step": 0.01,
                    "display": "number"
                }),
            }
        }
    
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("输出图像",)
    FUNCTION = "repeat_image"
    CATEGORY = "图像/变换"
    
    def repeat_image(self, image, rows, columns, horizontal_spacing, vertical_spacing,
                    background_color, custom_color_hex, rotation_angle, scale,
                    mirror_horizontal, mirror_vertical, mirror_horizontal_spacing, mirror_vertical_spacing, opacity):
        # 将tensor转换为PIL图像
        i = 255. * image[0].cpu().numpy()
        img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))
        
        # 解析hex颜色
        custom_color = self._hex_to_rgb(custom_color_hex)
        
        # 应用变换（镜像、缩放、旋转、不透明度）
        img = self._apply_transformations(img, rotation_angle, scale, mirror_horizontal, mirror_vertical, opacity)
        
        # 获取变换后的图像尺寸
        orig_width, orig_height = img.size
        
        # 计算输出图像尺寸（考虑镜像间距）
        total_h_spacing = horizontal_spacing
        total_v_spacing = vertical_spacing
        if mirror_horizontal:
            total_h_spacing += mirror_horizontal_spacing
        if mirror_vertical:
            total_v_spacing += mirror_vertical_spacing
            
        output_width = orig_width * columns + total_h_spacing * (columns - 1)
        output_height = orig_height * rows + total_v_spacing * (rows - 1)
        
        if background_color == "transparent":
            output_img = Image.new('RGBA', (output_width, output_height), (0, 0, 0, 0))
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
        elif background_color == "white":
            output_img = Image.new('RGB', (output_width, output_height), (255, 255, 255))
            if img.mode == 'RGBA':
                temp_img = Image.new('RGB', img.size, (255, 255, 255))
                temp_img.paste(img, mask=img.split()[3] if len(img.split()) == 4 else None)
                img = temp_img
        elif background_color == "black":
            output_img = Image.new('RGB', (output_width, output_height), (0, 0, 0))
            if img.mode == 'RGBA':
                temp_img = Image.new('RGB', img.size, (0, 0, 0))
                temp_img.paste(img, mask=img.split()[3] if len(img.split()) == 4 else None)
                img = temp_img
        else:  # custom
            output_img = Image.new('RGB', (output_width, output_height), custom_color)
            if img.mode == 'RGBA':
                temp_img = Image.new('RGB', img.size, custom_color)
                temp_img.paste(img, mask=img.split()[3] if len(img.split()) == 4 else None)
                img = temp_img
        
        # 复制图像到网格中
        for row in range(rows):
            for col in range(columns):
                x = col * (orig_width + horizontal_spacing)
                y = row * (orig_height + vertical_spacing)
                
                if output_img.mode == 'RGBA' and img.mode == 'RGBA':
                    output_img.paste(img, (x, y), img)
                else:
                    output_img.paste(img, (x, y))
        
        # 转换回tensor
        output_array = np.array(output_img).astype(np.float32) / 255.0
        if len(output_array.shape) == 2:
            output_array = np.expand_dims(output_array, axis=2)
        if output_array.shape[2] == 4:  # RGBA保留alpha
            pass
        elif output_array.shape[2] == 1:
            output_array = np.repeat(output_array, 3, axis=2)
        
        output_tensor = torch.from_numpy(output_array).unsqueeze(0)
        
        return (output_tensor,)
    
    def _hex_to_rgb(self, hex_color):
        """将hex颜色转换为RGB元组"""
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 6:
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        return (255, 255, 255)  # 默认白色
    
    def _apply_transformations(self, img, rotation, scale, mirror_h, mirror_v, opacity):
        """应用镜像、缩放、旋转和不透明度变换"""
        # 确保图像有alpha通道以支持不透明度
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        # 镜像
        if mirror_h:
            img = ImageOps.mirror(img)
        if mirror_v:
            img = ImageOps.flip(img)
        
        # 缩放
        if scale != 1.0:
            new_width = int(img.width * scale)
            new_height = int(img.height * scale)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # 旋转（保持透明度）
        if rotation != 0:
            img = img.rotate(rotation, expand=True, resample=Image.Resampling.BICUBIC)
        
        # 应用不透明度
        if opacity < 1.0:
            alpha = img.split()[3]
            alpha = alpha.point(lambda p: int(p * opacity))
            img.putalpha(alpha)
        
        return img


# 注册节点
NODE_CLASS_MAPPINGS = {
    "ImageRepeatConfig": ImageRepeatConfig,
    "ImageRepeatPreview": ImageRepeatPreview,
    "ImageRepeatSimple": ImageRepeatSimple,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ImageRepeatConfig": "图像重复配置",
    "ImageRepeatPreview": "图像重复预览",
    "ImageRepeatSimple": "图像重复",
}
