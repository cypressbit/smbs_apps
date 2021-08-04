import yaml

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper


class SMBSTemplate:

    def __init__(self, name):
        self.name = name

    def load_template(name):
        template = yaml.load(open('page_templates/{}/template.yaml'.format(name), 'rb'), Loader=Loader)
        return template

    def
