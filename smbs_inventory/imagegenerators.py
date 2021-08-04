from imagekit import ImageSpec, register
from imagekit.processors import Thumbnail, ResizeToFill, ResizeToFit, Anchor, ResizeCanvas


class Cover320x320(ImageSpec):
    processors = [Thumbnail(320, 320)]
    format = 'JPEG'
    options = {'quality': 100}


class Cover400x200(ImageSpec):
    processors = [ResizeToFit(400, 200, anchor=Anchor.CENTER), ResizeCanvas(400, 200)]
    format = 'JPEG'
    options = {'quality': 100}


class Cover1000x500(ImageSpec):
    processors = [ResizeToFit(1000, 500, anchor=Anchor.CENTER), ResizeCanvas(1000, 500)]
    format = 'JPEG'
    options = {'quality': 100}


register.generator('smbs_inventory:cover320x320', Cover320x320)
register.generator('smbs_inventory:cover400x200', Cover400x200)
register.generator('smbs_inventory:cover1000x500', Cover1000x500)
