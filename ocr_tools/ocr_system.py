import os
import sys
__dir__ = os.path.dirname(os.path.abspath(__file__))
sys.path.append(__dir__)
sys.path.append(os.path.abspath(os.path.join(__dir__, '../..')))
sys.path.append("/home/server_for_ocr/")

import cv2
import copy
import time
import logging
from PIL import Image
import utility as utility
import myself_predict_rec as my_predict_rec
import myself_predict_det as my_predict_det
from ppocr.utils.logging import get_logger
from utility import get_rotate_crop_image


logger = get_logger()


class TextSystem(object):
    def __init__(self, args):
        if not args.show_log:
            logger.setLevel(logging.INFO)

        self.my_text_detector = my_predict_det.my_predict_det()
        self.my_text_recognizer = my_predict_rec.my_predict_rec()
        self.use_angle_cls = args.use_angle_cls
        self.drop_score = args.drop_score

    def print_draw_crop_rec_res(self, img_crop_list, rec_res):
        bbox_num = len(img_crop_list)
        for bno in range(bbox_num):
            cv2.imwrite("./output/img_crop_%d.jpg" % bno, img_crop_list[bno])
            logger.info(bno, rec_res[bno])

    def __call__(self, file, cls=False):
        img = cv2.imread(file)
        ori_im = img.copy()
        dt_boxes = self.my_text_detector(file)    # 1todo  修
        if len(dt_boxes) == 0:
            return None, None
        img_crop_list = []
        picture_lists = []
        dt_boxes = sorted_boxes(dt_boxes)
        for bno in range(len(dt_boxes)):
            tmp_box = copy.deepcopy(dt_boxes[bno])
            img_crop = get_rotate_crop_image(ori_im, tmp_box)
            cv2.imwrite("/home/server_for_ocr/temp_picture/"+str(bno+2)+".jpg", img_crop)   # 1todo  del
            img_crop_list.append(img_crop)
            picture_lists.append("/home/server_for_ocr/temp_picture/"+str(bno+2)+".jpg")
        rec_res = self.my_text_recognizer(picture_lists)
        filter_boxes, filter_rec_res = [], []
        for box, rec_reuslt in zip(dt_boxes, rec_res):
            text, score = rec_reuslt
            if score >= self.drop_score:
                filter_boxes.append(box)
                filter_rec_res.append(rec_reuslt)
        return filter_boxes, filter_rec_res


def sorted_boxes(dt_boxes):
    num_boxes = dt_boxes.shape[0]
    sorted_boxes = sorted(dt_boxes, key=lambda x: (x[0][1], x[0][0]))
    _boxes = list(sorted_boxes)

    for i in range(num_boxes - 1):
        if abs(_boxes[i + 1][0][1] - _boxes[i][0][1]) < 10 and \
                (_boxes[i + 1][0][0] < _boxes[i][0][0]):
            tmp = _boxes[i]
            _boxes[i] = _boxes[i + 1]
            _boxes[i + 1] = tmp
    return _boxes


class run_ocr:
    def __init__(self):
        args = utility.parse_args()[0]
        self.text_sys = TextSystem(args)
        # print("{}: ocr_system running".format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())))

    def usage_text_sys(self, path_url="https://py.pxobgsxly.com/cdnoss/loan/users/img/220108/idcard_image_front/91effca78d7612b695b2e3a8ef3c64b1/220108f952432c47eb925050f9ff0b8aadfd49.jpeg"):
        import save_to_csv
        import uuid
        import requests
        try:
            # import time
            # time_start = time.time()
            filepath = "/home/server_for_ocr/temp_picture/" + str(uuid.uuid4()) + ".jpg"
            response = requests.get(path_url)
            with open(filepath, 'wb') as file:
                file.write(response.content)
            # print("download time:{}".format(time.time() - time_start))
            # time_start1 = time.time()
            dt_boxes, rec_res = self.text_sys(filepath)
            # print("rec time:{}".format(time.time() - time_start1))
            text_dicts = save_to_csv.main(dt_boxes, rec_res)   # 1todo 新的抽取方式
            os.remove(filepath)
            return {"text": text_dicts, "status": 6}
        except Exception as e:
            print("there is something wrong usage_text_sys :{}".format(e))
            return {"text": [], "status": 5}


if __name__ == "__main__":
    run_server = run_ocr()
    import time
    pics = ["https://py.pxobgsxly.com/cdnoss/loan/users/img/220108/idcard_image_front/91effca78d7612b695b2e3a8ef3c64b1/220108f952432c47eb925050f9ff0b8aadfd49.jpeg", "https://py.pxobgsxly.com/cdnoss/loan/users/img/220108/idcard_image_front/91effca78d7612b695b2e3a8ef3c64b1/220108f952432c47eb925050f9ff0b8aadfd49.jpeg", "https://py.pxobgsxly.com/cdnoss/loan/users/img/220108/idcard_image_front/91effca78d7612b695b2e3a8ef3c64b1/220108f952432c47eb925050f9ff0b8aadfd49.jpeg", "https://py.pxobgsxly.com/cdnoss/loan/users/img/220108/idcard_image_front/91effca78d7612b695b2e3a8ef3c64b1/220108f952432c47eb925050f9ff0b8aadfd49.jpeg"]
    time_start = time.time()
    for i in pics:
        run_server.usage_text_sys(i)
    print("total time:{}".format(time.time() - time_start))
