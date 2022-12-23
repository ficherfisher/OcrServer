# Copyright (c) 2020 PaddlePaddle Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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

import cv2
import paddle

from ppocr.data import create_operators, transform
from ppocr.utils.logging import get_logger
from ppocr.modeling.architectures import build_model
from ppocr.utils.save_load import init_model, load_dygraph_params
from ppocr.postprocess import build_post_process
import yaml
logger = get_logger()


class my_predict_det(object):

    def __init__(self):
        pathfile = os.path.split(os.path.realpath(__file__))[0]
        fp = open(os.path.join(pathfile, "det_model_myself_test.yml"), "r")
        config = yaml.load(fp.read(), Loader=yaml.Loader)
        global_config = config['Global']

        # build model
        self.model = build_model(config['Architecture'])

        _ = load_dygraph_params(config, self.model, logger, None)
        # build post process
        self.post_process_class = build_post_process(config['PostProcess'])

        # create data ops
        transforms = []
        for op in config['Eval']['dataset']['transforms']:
            op_name = list(op)[0]
            if 'Label' in op_name:
                continue
            elif op_name == 'KeepKeys':
                op[op_name]['keep_keys'] = ['image', 'shape']
            transforms.append(op)

        self.ops = create_operators(transforms, global_config)

        save_res_path = config['Global']['save_res_path']
        if not os.path.exists(os.path.dirname(save_res_path)):
            os.makedirs(os.path.dirname(save_res_path))

        self.model.eval()

    def order_points_clockwise(self, pts):

        xSorted = pts[np.argsort(pts[:, 0]), :]

        leftMost = xSorted[:2, :]
        rightMost = xSorted[2:, :]

        leftMost = leftMost[np.argsort(leftMost[:, 1]), :]
        (tl, bl) = leftMost

        rightMost = rightMost[np.argsort(rightMost[:, 1]), :]
        (tr, br) = rightMost

        rect = np.array([tl, tr, br, bl], dtype="float32")
        return rect

    def clip_det_res(self, points, img_height, img_width):
        for pno in range(points.shape[0]):
            points[pno, 0] = int(min(max(points[pno, 0], 0), img_width - 1))
            points[pno, 1] = int(min(max(points[pno, 1], 0), img_height - 1))
        return points

    def filter_tag_det_res(self, dt_boxes, image_shape):
        img_height, img_width = image_shape[0:2]
        dt_boxes_new = []
        for box in dt_boxes:
            box = self.order_points_clockwise(box)
            box = self.clip_det_res(box, img_height, img_width)
            rect_width = int(np.linalg.norm(box[0] - box[1]))
            rect_height = int(np.linalg.norm(box[0] - box[3]))
            if rect_width <= 3 or rect_height <= 3:
                continue
            dt_boxes_new.append(box)
        dt_boxes = np.array(dt_boxes_new)
        return dt_boxes

    def __call__(self, file):
        ori_img = cv2.imread(file)
        with open(file, 'rb') as f:
            img = f.read()
            data = {'image': img}
        batch = transform(data, self.ops)

        images = np.expand_dims(batch[0], axis=0)
        shape_list = np.expand_dims(batch[1], axis=0)
        images = paddle.to_tensor(images)
        preds = self.model(images)
        post_result = self.post_process_class(preds, shape_list)
        boxes = post_result[0]['points']
        dt_boxes = self.filter_tag_det_res(boxes, ori_img.shape)
        return dt_boxes


if __name__ == '__main__':
    file = "/home/server_for_ocr/temp_picture/aa.jpg"
    a = my_predict_det()
    a(file)



