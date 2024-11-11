from imagekit import ImageSpec, register
from imagekit.processors import Thumbnail, ResizeToFill


class Cover320x320(ImageSpec):
    processors = [Thumbnail(320, 320)]
    format = 'WEBP'
    options = {'quality': 100}


class Cover320x160(ImageSpec):
    processors = [Thumbnail(320, 160)]
    format = 'WEBP'
    options = {'quality': 100}


class Cover600x300(ImageSpec):
    processors = [ResizeToFill(600, 300)]
    format = 'WEBP'
    options = {'quality': 100}


class Cover1200x600(ImageSpec):
    processors = [ResizeToFill(1200, 600)]
    format = 'WEBP'
    options = {'quality': 100}


register.generator('smbs_blog:cover320x320', Cover320x320)
register.generator('smbs_blog:cover320x160', Cover320x160)
register.generator('smbs_blog:cover600x300', Cover600x300)
register.generator('smbs_blog:cover1200x600', Cover1200x600)
