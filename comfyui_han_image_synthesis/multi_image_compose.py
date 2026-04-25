import torch
import numpy as np
from PIL import Image
import os
import folder_paths

class ImageCompose:
    """图像合成节点 - 将两个图像合成（支持透明PNG免抠图）"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "background_image": ("IMAGE",),
                "foreground_image": ("IMAGE",),
            }
        }
    
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("合成图像",)
    FUNCTION = "compose"
    CATEGORY = "图像/合成"
    
    def compose(self, background_image, foreground_image):
        # 将tensor转换为PIL图像
        bg_img = self._tensor_to_pil(background_image)
        fg_img = self._tensor_to_pil(foreground_image)
        
        # 确保前景图像是RGBA模式以支持透明度
        if fg_img.mode != 'RGBA':
            fg_img = fg_img.convert('RGBA')
        
        # 确保背景图像是RGB或RGBA模式
        if bg_img.mode not in ['RGB', 'RGBA']:
            bg_img = bg_img.convert('RGB')
        
        # 如果背景是RGB,转换为RGBA以支持alpha合成
        if bg_img.mode == 'RGB':
            bg_img = bg_img.convert('RGBA')
        
        # 创建与背景同尺寸的画布
        result = bg_img.copy()
        
        # 将前景图像粘贴到背景上(居中)
        x = (bg_img.width - fg_img.width) // 2
        y = (bg_img.height - fg_img.height) // 2
        
        # 使用alpha通道进行合成
        result.paste(fg_img, (x, y), fg_img)
        
        # 转换回tensor
        output_tensor = self._pil_to_tensor(result)
        
        return (output_tensor,)
    
    def _tensor_to_pil(self, tensor):
        """将tensor转换为PIL图像"""
        i = 255. * tensor[0].cpu().numpy()
        img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))
        return img
    
    def _pil_to_tensor(self, pil_img):
        """将PIL图像转换为tensor"""
        output_array = np.array(pil_img).astype(np.float32) / 255.0
        if len(output_array.shape) == 2:
            output_array = np.expand_dims(output_array, axis=2)
            output_array = np.repeat(output_array, 3, axis=2)
        elif output_array.shape[2] == 4:
            # RGBA转RGB(在白色背景上合成)
            rgb_array = output_array[:, :, :3]
            alpha = output_array[:, :, 3:4]
            output_array = rgb_array * alpha + (1 - alpha)
        elif output_array.shape[2] == 1:
            output_array = np.repeat(output_array, 3, axis=2)
        
        return torch.from_numpy(output_array).unsqueeze(0)


class ImageComposePreview(ImageCompose):
    """图像合成预览节点 - 带实时预览"""
    
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("合成图像",)
    FUNCTION = "compose_preview"
    OUTPUT_NODE = True
    CATEGORY = "图像/合成"
    
    def compose_preview(self, background_image, foreground_image):
        # 调用父类方法进行合成
        result = self.compose(background_image, foreground_image)
        output_tensor = result[0]
        
        # 保存预览图像
        output_array = output_tensor[0].cpu().numpy()
        output_img = Image.fromarray((output_array * 255).astype(np.uint8))
        
        temp_dir = folder_paths.get_temp_directory()
        temp_file = os.path.join(temp_dir, "image_compose_preview.png")
        output_img.save(temp_file)
        
        return {
            "ui": {
                "images": [
                    {
                        "filename": "image_compose_preview.png",
                        "subfolder": "",
                        "type": "temp"
                    }
                ]
            },
            "result": (output_tensor,)
        }


# 注册节点
NODE_CLASS_MAPPINGS = {
    "ImageCompose": ImageCompose,
    "ImageComposePreview": ImageComposePreview,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ImageCompose": "图像合成",
    "ImageComposePreview": "图像合成预览",
}
