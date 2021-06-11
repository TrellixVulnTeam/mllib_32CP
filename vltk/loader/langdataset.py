import inspect
# note if we do not immport a pacakage correctly in this class, no loops or exps will be present
import json
import math
import os
import random
import resource
import sys
from collections import Iterable
from copy import deepcopy

import torch
import vltk
# disable logging from datasets
from datasets.utils.logging import set_verbosity_error
from vltk.loader.basedataset import BaseDataset, CollatedVLSets
from vltk.utils.adapters import Data

__import__("tokenizers")
TOKENIZERS = {
    m[0]: m[1]
    for m in inspect.getmembers(sys.modules["tokenizers"], inspect.isclass)
    if "Tokenizer" in m[0]
}

rlimit = resource.getrlimit(resource.RLIMIT_NOFILE)
resource.setrlimit(resource.RLIMIT_NOFILE, (6144, rlimit[1]))

set_verbosity_error()

VOCABPATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "libdata/bert-base-uncased-vocab.txt")
).replace("loader/", "")
TOKENIZEDKEY = "encoded"
os.environ["TOKENIZERS_PARALLELISM"] = "False"

_data_procecessors = Data()


class LangDataset(BaseDataset):
    def __init__(
        self,
    ):
        super().__init()
        """
        Implementation for LangDataset is not completed or really developed at all yet.

        This serves as a placeholder class for all relevant pure-text
        processing in the VisnLang Dataset so that I can have that class inherit from
        VisionDataset + LangDataset while I perform this refactoring
        """

    def update_labels(self, path_or_dict):
        if isinstance(path_or_dict, str):
            path_or_dict = json.load(open(path_or_dict))
        else:
            pass
        self.answer_to_id = path_or_dict
        self.uniq_labels = set(path_or_dict.keys())

    def lang_processor_args(self):
        max_rand_sents = 1 if not self.config.img_first else 32
        return {
            "tokenizer": self.tokenizer,
            "config": self.config,
            "random_sents": [self.random_sent() for i in range(max_rand_sents)],
            "special_ids": self.special_ids,
            "answer_to_id": self.answer_to_id,
            "all_ids": self.all_ids,
            "n_ids": len(self.all_ids),
        }

    @staticmethod
    def text_map_function(x, proc_args, from_transformers=False):
        config = proc_args.get("config")
        tokenizer = proc_args.get("tokenizer")
        answer_to_id = proc_args.get("answer_to_id")
        text_processors = config.text_processors
        if text_processors is not None:
            if "matched_sentence_modeling" in text_processors:
                proc_func = _data_procecessors.get("matched_sentence_modeling")
                x = proc_func(x, **proc_args)

        if not from_transformers:
            encoded = tokenizer.encode(x.pop(vltk.text))
            x.pop(vltk.imgid, None)
            x[vltk.text_attention_mask] = encoded.attention_mask
            x[vltk.input_ids] = encoded.ids
            x[vltk.type_ids] = encoded.type_ids
        else:
            encoded = tokenizer(
                x.pop(vltk.text),
                padding="max_length",
                truncation="longest_first",
                max_length=proc_args["config"].lang.max_seq_length,
                return_token_type_ids=True,
            )
            x[vltk.text_attention_mask] = encoded["attention_mask"]
            x[vltk.input_ids] = encoded["input_ids"]
            x[vltk.type_ids] = encoded["token_type_ids"]

        if vltk.label in x:
            label = x.pop(vltk.label)
            raise Exception(label, answer_to_id)
            if label != config.lang.ignore_id:
                lids = []
                for l in label:
                    lid = answer_to_id[l]
                    lids.append(lid)
                x[vltk.label] = lids

        # now we do other text processors
        if text_processors is not None:
            for proc in text_processors:
                if proc == "one_hot_label" and vltk.label not in x:
                    continue
                if proc == "matched_sentence_modeling":
                    continue
                proc_func = _data_procecessors.get(proc)
                proc_func(x, **proc_args)

        # now we do label proccesor
        if config.label_processor is not None:
            proc_func = _data_procecessors.get(config.label_processor)
            proc_func(x, **proc_args)

        return x

    def __len__(self):
        return int(math.floor(len(self.datasets) * self.config.percent))

    def random_sent(self):
        rand_ind = random.randint(0, len(self.datasets) - 1)
        text_info = self.datasets[rand_ind]
        rand_sent = text_info[vltk.text]
        return rand_sent

    def _map(self, small_visnlangdatasetadapter):
        proc_args = self.lang_processor_args()
        return small_visnlangdatasetadapter.map(
            lambda x: LangDataset.text_map_function(
                x, proc_args=proc_args, from_transformers=self.from_transformers
            )
        )

    def _handle_text_annotations(self, img_id):
        annotation_pointer = self.annotations
        if annotation_pointer is None:
            raise Exception
            return
        anno_dict = annotation_pointer.get(img_id)
        labels = anno_dict[vltk.label]
        labels = torch.Tensor([self.object_to_id[int(l)] for l in labels])
        anno_dict[vltk.label] = labels
        for k, v in anno_dict.items():
            if (
                k is vltk.label
                or k is vltk.img
                or (isinstance(v, Iterable) and not isinstance(v[0], list))
            ):
                continue

            anno_dict[k] = list(map(lambda x: torch.Tensor(x), v))

        return anno_dict

    def _init_text_annotation_dict(self, annotationdict):
        if annotationdict is None:
            self._annotations = None
            return
        annotations = list(annotationdict.values())
        raise Exception("HERE", annotations)
        self._annotations = CollatedVLSets(*annotations)
