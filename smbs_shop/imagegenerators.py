from imagekit import ImageSpec, register
from imagekit.processors import Thumbnail, ResizeToFill


class BaseCover(ImageSpec):
    format = 'WEBP'
    options = {'quality': 100}


class ShopCover320x320(BaseCover):
    WIDTH = 320
    HEIGHT = 320
    processors = [Thumbnail(WIDTH, HEIGHT)]


class ShopCover320x160(BaseCover):
    WIDTH = 320
    HEIGHT = 160
    processors = [Thumbnail(WIDTH, HEIGHT)]


class ShopCover600x300(BaseCover):
    WIDTH = 600
    HEIGHT = 300
    processors = [ResizeToFill(WIDTH, HEIGHT)]


class ShopCover1200x600(BaseCover):
    WIDTH = 1200
    HEIGHT = 600
    processors = [ResizeToFill(WIDTH, HEIGHT)]


register.generator('smbs_shop:cover320x320', ShopCover320x320)
register.generator('smbs_shop:cover320x160', ShopCover320x160)
register.generator('smbs_shop:cover600x300', ShopCover600x300)
register.generator('smbs_shop:cover1200x600', ShopCover1200x600)
