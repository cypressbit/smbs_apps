from imagekit import ImageSpec, register
from imagekit.processors import Thumbnail, SmartResize


class Cover320x320(ImageSpec):
    processors = [Thumbnail(320, 320)]
    format = 'JPEG'
    options = {'quality': 100}


class Cover320x160(ImageSpec):
    processors = [SmartResize(320, 160)]
    format = 'JPEG'
    options = {'quality': 100}


class Cover600x300(ImageSpec):
    processors = [SmartResize(600, 300)]
    format = 'JPEG'
    options = {'quality': 100}


register.generator('smbs_user_posts:cover320x320', Cover320x320)
register.generator('smbs_user_posts:cover320x160', Cover320x160)
register.generator('smbs_user_posts:cover600x300', Cover600x300)
