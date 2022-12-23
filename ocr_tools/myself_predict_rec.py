from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import numpy as np

import os
import sys

__dir__ = os.path.dirname(os.path.abspath(__file__))
sys.path.append(__dir__)
sys.path.append(os.path.abspath(os.path.join(__dir__, '..')))

os.environ["FLAGS_allocator_strategy"] = 'auto_growth'

import paddle

from ppocr.data import create_operators, transform
from ppocr.modeling.architectures import build_model
from ppocr.postprocess import build_post_process
from ppocr.utils.save_load import init_model


class my_predict_rec(object):

    def __init__(self):
        import yaml
        pathfile = os.path.split(os.path.realpath(__file__))[0]
        fp = open(os.path.join(pathfile, "rec_model_myself_test.yml"), "r")
        config = yaml.load(fp.read(), Loader=yaml.Loader)
        global_config = config['Global']
        self.post_process_class = build_post_process(config['PostProcess'], global_config)
        if hasattr(self.post_process_class, 'character'):
            char_num = len(getattr(self.post_process_class, 'character'))
            if config['Architecture']["algorithm"] in ["Distillation",
                                                       ]:  # distillation model
                for key in config['Architecture']["Models"]:
                    config['Architecture']["Models"][key]["Head"][
                        'out_channels'] = char_num
            else:  # base rec model
                config['Architecture']["Head"]['out_channels'] = char_num

        self.model = build_model(config['Architecture'])

        init_model(config, self.model)

        transforms = []
        for op in config['Eval']['dataset']['transforms']:
            op_name = list(op)[0]
            if 'Label' in op_name:
                continue
            elif op_name in ['RecResizeImg']:
                op[op_name]['infer_mode'] = True
            elif op_name == 'KeepKeys':
                op[op_name]['keep_keys'] = ['image']
            transforms.append(op)
        global_config['infer_mode'] = True
        self.ops = create_operators(transforms, global_config)

        self.model.eval()

    def __call__(self, pictures_list):
        if len(pictures_list) < 1:
            return
        result = []
        for file in pictures_list:
            with open(file, 'rb') as f:
                img = f.read()
                data = {'image': img}
            batch = transform(data, self.ops)
            images = np.expand_dims(batch[0], axis=0)
            images = paddle.to_tensor(images)
            preds = self.model(images)
            post_result = self.post_process_class(preds)
            result.append(post_result[0])
            # os.remove(os.path.join("D:/programmeProject/paddle_temp_picture/", os.path.basename(file)))
        return result


if __name__ == '__main__':
    pass

