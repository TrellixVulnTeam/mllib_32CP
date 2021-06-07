import vltk
from vltk import Features, adapters, compat
from vltk.configs import VisionConfig
from vltk.modeling.frcnn import FRCNN as FasterRCNN


class FRCNN(adapters.VisnExtraction):

    # TODO: currently, this image preprocessing config is not correct
    default_processor = VisionConfig(
        **{
            "transforms": ["ToPILImage", "ToTensor", "ResizeTensor", "Normalize"],
            "size": (800, 1333),
            "mode": "bilinear",
            "pad_value": 0.0,
            "mean": [102.9801, 115.9465, 122.7717],
            "sdev": [1.0, 1.0, 1.0],
        }
    )
    # model_config = compat.Config.from_pretrained("unc-nlp/frcnn-vg-finetuned")
    weights = "unc-nlp/frcnn-vg-finetuned"
    model = FasterRCNN
    model_config = compat.Config.from_pretrained("unc-nlp/frcnn-vg-finetuned")

    def schema(max_detections=36, visual_dim=2048):
        return {
            "attr_ids": Features.ids,
            "object_ids": Features.ids,
            vltk.features: Features.features(max_detections, visual_dim),
            vltk.boxtensor: Features.boxtensor(max_detections),
        }

    def forward(model, entry):

        size = entry["size"]
        scale_hw = entry["scale"]
        image = entry["image"]

        model_out = model(
            images=image.unsqueeze(0),
            image_shapes=size.unsqueeze(0),
            scales_yx=scale_hw.unsqueeze(0),
            padding="max_detections",
            pad_value=0.0,
            return_tensors="np",
            location="cpu",
        )
        return {
            "object_ids": model_out["obj_ids"],
            "attr_ids": model_out["attr_ids"],
            vltk.boxtensor: model_out["normalized_boxes"],
            vltk.features: model_out["roi_features"],
        }
