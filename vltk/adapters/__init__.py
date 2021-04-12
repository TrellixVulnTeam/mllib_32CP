import vltk
from datasets import Dataset
from vltk.abc.extraction import VisnExtraction
from vltk.abc.visnadapter import VisnDataset
from vltk.abc.visnlangadatper import VisnLangDataset
from vltk.inspection import get_classes


class Adapters:
    def __init__(self):
        if "ADAPTERDICT" not in globals():
            global ADAPTERDICT
            ADAPTERDICT = get_classes(vltk.ADAPTERS, Dataset, pkg="vltk.adapters")

    @property
    def dict(self):
        return

    def avail(self):
        return list(ADAPTERDICT.keys())

    def get(self, name):
        return ADAPTERDICT[name]

    def add(self, *args):
        for dset in args:
            ADAPTERDICT[dset.__name__.lower()] = dset
