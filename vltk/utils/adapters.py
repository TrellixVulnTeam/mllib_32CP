import json
import os
from collections import defaultdict

import numpy as np
import torch
import torchvision.transforms.functional as FV
import vltk
from pycocotools import mask as coco_mask
from skimage import measure
from tqdm import tqdm
from vltk.processing.image import (Image, get_pad, get_rawsize, get_scale,
                                   get_size)

PATH = os.path.join(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..")), "libdata"
)
ANS_CONVERT = json.load(open(os.path.join(PATH, "convert_answers.json")))
CONTRACTION_CONVERT = json.load(open(os.path.join(PATH, "convert_answers.json")))


def histogram_from_counter(counter):
    # credits to stack overflow
    # TODO: add credits to stack overflow for other functions that I am using form there
    import matplotlib.pyplot as plt

    labels, values = zip(*counter.items())
    indexes = np.arange(len(labels))
    width = 1
    plt.bar(indexes, values, width)
    plt.xticks(indexes + width * 0.5, labels)
    plt.show()


def imagepoints_to_polygon(points):
    img = imagepoints_to_mask(points)
    polygon = mask_to_polygon(img)
    return polygon


# source: https://github.com/ksrath0re/clevr-refplus-rec/
def imagepoints_to_mask(points, size):
    # raise Exception(points)
    # npimg = []
    img = []
    cur = 0
    for num in points:
        # if cur == 0:
        #     part = np.zeros(int(num))
        # else:
        #     part = np.concatenate((part, np.ones(int(num))))
        # npimg.append(part)
        num = int(num)
        img += [cur] * num
        cur = 1 - cur
    img = torch.tensor(img).reshape(tuple(size.tolist()))
    # npimg = np.stack(npimg)
    # raise Exception(part.shape)
    # part = part.reshape(tuple(size.tolist()))
    return img


def mask_to_polygon(mask):
    contours = measure.find_contours(mask, 0.5)
    seg = []
    for contour in contours:
        contour = np.flip(contour, axis=1)
        segmentation = contour.ravel().tolist()
        seg.append(segmentation)
    return seg


def rescale_box(boxes, hw_scale):
    # boxes = (n, (x, y, w, h))
    # x = top left x position
    # y = top left y position
    h_scale = hw_scale[0]
    w_scale = hw_scale[1]
    y_centroids = (boxes[:, 1] - boxes[:, 3] / 2) * h_scale
    x_centroids = (boxes[:, 0] + boxes[:, 2] / 2) * w_scale
    boxes[:, 2] *= w_scale
    boxes[:, 3] *= h_scale
    boxes[:, 0] = x_centroids - boxes[:, 2] / 2  # scaled xs
    boxes[:, 1] = y_centroids + boxes[:, 3] / 2  # scaled ys
    return boxes


def seg_to_mask(segmentation, h, w):
    segmentation = coco_mask.decode(coco_mask.frPyObjects(segmentation, h, w))
    if len(segmentation.shape) < 3:
        segmentation = segmentation[..., None]
    segmentation = np.any(segmentation, axis=-1).astype(np.uint8)
    return segmentation


# def resize_mask(mask, transforms_dict):
#     if "Resize" in transforms_dict:
#         return transforms_dict["Resize"](mask)
#     else:
#         return mask


def resize_binary_mask(array, img_size, pad_size=None):
    if not isinstance(array, torch.Tensor):
        array = torch.from_numpy(array)

    img_size = (img_size[0], img_size[1])
    if array.shape != img_size:
        array = torch.as_tensor(FV.resize(array.unsqueeze(0), img_size).squeeze(0))
        return array
    else:
        return array


def uncompress_mask(compressed, size):
    mask = np.zeros(size, dtype=np.uint8)
    mask[compressed[0], compressed[1]] = 1
    return mask


def clean_label(ans):
    if len(ans) == 0:
        return ""
    ans = ans.lower()
    ans = ans.replace(",", "")
    if ans[-1] == ".":
        ans = ans[:-1].strip()
    if ans.startswith("a "):
        ans = ans[2:].strip()
    if ans.startswith("an "):
        ans = ans[3:].strip()
    if ans.startswith("the "):
        ans = ans[4:].strip()
    ans = " ".join(
        [
            CONTRACTION_CONVERT[a] if a in CONTRACTION_CONVERT else a
            for a in ans.split(" ")
        ]
    )
    if ans in ANS_CONVERT:
        ans = ANS_CONVERT[ans]
    return ans


def soft_score(occurences):
    if occurences == 0:
        return 0
    elif occurences == 1:
        return 0.3
    elif occurences == 2:
        return 0.6
    elif occurences == 3:
        return 0.9
    else:
        return 1


def get_span_via_jaccard(words, answers, skipped=None):
    """
    inputs:
        words: tuple of strings (each string == one word)
        answers: list of strings (each string == one word or many words)
        skipped: int or None
    outputs:
        span: list of length `len(words)` of 1's and 0's. 0: is not apart of answer, 1: is apart of answer
        max_jaccard: the similarity metric value 0.0-1.0 for how well answer matched in span
    """
    span = [0] * len(words)
    any_ans = False
    for ans in answers:
        # single word case
        if len(ans.split()) == 1:
            try:
                idx = words.index(ans.lower())
            except Exception:
                continue
            if idx is not None:
                span[idx] = 1
                max_jaccard = 1.0
                any_ans = True
                break

    if not any_ans:
        keep = None
        max_jaccard = -0.1
        for ans in answers:
            if len(ans.split()) == 1:
                for ans in answers:
                    ans = set(ans.lower())
                    for idx, word in enumerate(words):
                        word = set(word.lower())
                        jaccard = len(word & ans) / len(word | ans)
                        if jaccard > max_jaccard:
                            max_jaccard = jaccard
                            keep = idx
            else:
                end_keep = len(words)

                ans = ans.split()
                start_keep = end_keep - len(ans)
                start = ans[0].lower()
                end = ans[-1].lower()
                start = set(start)
                end = set(end)
                jaccards = []
                for idx, word in enumerate(words[: -len(ans)]):
                    temp_jaccard = 0.0
                    for jdx, subans in enumerate(ans):
                        word = set(words[idx + jdx].lower())
                        subans = set(subans)
                        temp_jaccard += len(word & subans) / len(word | subans)
                        jaccards.append(
                            (
                                temp_jaccard / len(ans),
                                (idx, idx + len(ans)),
                            )
                        )
                if not jaccards:
                    continue
                jaccard, (start_keep, end_keep) = sorted(jaccards, key=lambda x: x[0])[
                    -1
                ]
                if jaccard > max_jaccard:
                    keep = (start_keep, end_keep)
                    span[start_keep:end_keep] = [1] * ((end_keep - start_keep) + 1)
                    max_jaccard = jaccard

        if keep is None:
            span = None
        elif isinstance(keep, tuple):
            span[keep[0] : keep[1]] = [1] * ((keep[1] - keep[0]) + 1)
        else:
            span[keep] = 1

    if max_jaccard == 0.0:
        if skipped is not None:
            skipped += 1
        span = None

    return span, max_jaccard


def truncate_and_pad_list(inp_list, max_len, pad_value=""):
    inp_list = inp_list[: min(max_len, len(inp_list))]
    inp_list += [pad_value] * (max_len - len(inp_list))
    return inp_list


def basic_coco_annotations(json_files, splits):
    """
    inputs:
        json_files: a dict of annotation files in  coco format -->
            keys: filename
            values: json file
            ===
            boxes in (x,y,w,h) format
            segmentations are polygons
            ...
        splits: list of respective splits aligned to the keys of json_files
    outputs:
        list of dictionaries:
            keys:
                vltk.imgid
                vltk.box
                vltk.polygons
                vltk.objects
            values:
                str: the image id (stem of the filename)
                list of list of floats: list of bounding boxes
                list of list of list of floats: list of polygons
                list of strings: respective label classes for each object/segmentation
    """
    total_annos = {}
    id_to_cat = {}
    file_to_id_to_stem = defaultdict(dict)
    for file, data in json_files.items():
        info = data["images"]
        for i in info:
            img_id = i["file_name"].split(".")[0]

            file_to_id_to_stem[file][i["id"]] = img_id

    for filename, data in tqdm(json_files.items()):
        categories = data["categories"]
        for cat in categories:
            id_to_cat[cat["id"]] = cat["name"]

        for entry in data["annotations"]:

            img_id = str(file_to_id_to_stem[file][entry["image_id"]])
            bbox = entry["bbox"]
            segmentation = entry["segmentation"]
            category_id = id_to_cat[entry["category_id"]]
            if entry["iscrowd"]:
                seg_mask = []
            else:
                seg_mask = segmentation
                if not isinstance(seg_mask[0], list):
                    seg_mask = [seg_mask]
            img_data = total_annos.get(img_id, None)
            if img_data is None:
                img_entry = defaultdict(list)
                img_entry[vltk.objects].append(category_id)
                img_entry[vltk.box].append(bbox)
                img_entry[vltk.polygons].append(seg_mask)
                total_annos[img_id] = img_entry
            else:
                total_annos[img_id][vltk.box].append(bbox)
                total_annos[img_id][vltk.objects].append(category_id)
                total_annos[img_id][vltk.polygons].append(seg_mask)

    return [{vltk.imgid: img_id, **entry} for img_id, entry in total_annos.items()]
