from imagekit import ImageSpec, register
from imagekit.processors import Thumbnail, ResizeToFill


class ShopCover320x320(ImageSpec):
    processors = [Thumbnail(320, 320)]
    format = 'WEBP'
    options = {'quality': 100}


class ShopCover320x160(ImageSpec):
    processors = [Thumbnail(320, 160)]
    format = 'WEBP'
    options = {'quality': 100}


class ShopCover600x300(ImageSpec):
    processors = [ResizeToFill(600, 300)]
    format = 'WEBP'
    options = {'quality': 100}


class ShopCover1200x600(ImageSpec):
    processors = [ResizeToFill(1200, 600)]
    format = 'WEBP'
    options = {'quality': 100}


register.generator('smbs_shop:cover320x320', ShopCover320x320)
register.generator('smbs_shop:cover320x160', ShopCover320x160)
register.generator('smbs_shop:cover600x300', ShopCover600x300)
register.generator('smbs_shop:cover1200x600', ShopCover1200x600)
