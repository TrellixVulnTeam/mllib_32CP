import os

from setuptools import setup

"""
ALL BOXES ARE EXPECTED TO GO IN: (X, Y, W, H) FORMAT
"""


# special deliminator
delim = "^"
tokenmap = "tokenmap"
# common keys across library
span = "span"
n_objects = "n_objects"
objects = "objects"
type_ids = "type_ids"
input_ids = "input_ids"
tokenbox = "tokenbox"
text_attention_mask = "text_attention_mask"
rawsize = "rawsize"
padsize = "padsize"
size = "size"
polygons = "poly"
RLE = "RLE"
segmentation = "segmentation"
box = "box"
imgid = "imgid"
label = "label"
text = "text"
score = "score"
label = "label"
img = "image"
filepath = "filepath"
features = "features"
split = "split"
scale = "scale"
boxtensor = "boxtensor"
area = "area"
size = "size"
qid = "qid"

VLOVERLAP = {
    text: "vtext",
    label: "vlabel",
    score: "vscore",
}

SUPPORTEDNAMES = {
    type_ids,
    input_ids,
    text_attention_mask,
    rawsize,
    size,
    segmentation,
    box,
    imgid,
    label,
    text,
    score,
    label,
    text,
    score,
    img,
    filepath,
    features,
    split,
    scale,
    boxtensor,
    area,
    size,
}


SPLITALIASES = {
    "test",
    "dev",
    "eval",
    "val",
    "validation",
    "evaluation",
    "train",
}

# dataset selection values
VLDATA = 0
VDATA = 1
LDATA = 2

# pathes
ANNOTATION_DIR = "annotations"
BASEPATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "."))
VISIONLANG = os.path.join(BASEPATH, "adapters/visionlang")
VISION = os.path.join(BASEPATH, "adapters/vision")
EXTRACTION = os.path.join(BASEPATH, "adapters/vision")
ADAPTERS = os.path.join(BASEPATH, "adapters")
PROCESSORS = os.path.join(BASEPATH, "processing")
SIMPLEPATH = os.path.join(BASEPATH, "experiment")
MODELPATH = os.path.join(BASEPATH, "modeling")
LOOPPATH = os.path.join(BASEPATH, "loop")
SCHEDPATH = os.path.join(BASEPATH, "processing/sched.py")
DATAPATH = os.path.join(BASEPATH, "processing/data.py")
LABELPROCPATH = os.path.join(BASEPATH, "processing/label.py")
IMAGEPROCPATH = os.path.join(BASEPATH, "processing/image.py")
OPTIMPATH = os.path.join(BASEPATH, "processing/optim.py")


"""
:)
"""
