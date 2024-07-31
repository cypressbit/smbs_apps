from imagekit import ImageSpec, register
from imagekit.processors import Thumbnail, ResizeToFill
from PIL import Image, ImageDraw
from django.utils.translation import gettext as _


class BaseCover(ImageSpec):
    format = 'WEBP'
    options = {'quality': 100}

    def generate(self):
        if not self.source:
            # Generate a blank image if no source is provided
            image = Image.new('RGB', (self.WIDTH, self.HEIGHT), color=(255, 255, 255))
            draw = ImageDraw.Draw(image)
            draw.text((150, 130), _("No Image"), fill=(0, 0, 0))
            return image
        return super().generate()


class ShopCover320x320(BaseCover):
    WIDTH = 320
    HEIGHT = 320
    processors = [Thumbnail(WIDTH, HEIGHT)]


class ShopCover320x160(ImageSpec):
    WIDTH = 320
    HEIGHT = 160
    processors = [Thumbnail(WIDTH, HEIGHT)]


class ShopCover600x300(ImageSpec):
    WIDTH = 600
    HEIGHT = 300
    processors = [ResizeToFill(WIDTH, HEIGHT)]


class ShopCover1200x600(ImageSpec):
    WIDTH = 1200
    HEIGHT = 600
    processors = [ResizeToFill(WIDTH, HEIGHT)]


register.generator('smbs_shop:cover320x320', ShopCover320x320)
register.generator('smbs_shop:cover320x160', ShopCover320x160)
register.generator('smbs_shop:cover600x300', ShopCover600x300)
register.generator('smbs_shop:cover1200x600', ShopCover1200x600)
