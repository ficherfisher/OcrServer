import argparse
import os
import sys
import cv2
import numpy as np
import math
from paddle import inference

work_bash = os.path.join(os.path.dirname(__file__), "..")

det_model_dir = os.path.join(work_bash, "models/ch_PP-OCRv2_det_infer/")
cls_model_dir = os.path.join(work_bash, "models/ch_ppocr_server_v2.0_cls_infer_1/")
rec_model_dir = os.path.join(work_bash, "models/ch_PP-OCRv2_rec_infer/")
rec_char_dict_path = os.path.join(work_bash, "ppocr/utils/ppocr_keys_v1.txt")
vis_font_path = os.path.join(work_bash, "fonts/simfang.ttf")
e2e_char_dict_path = os.path.join(work_bash, "ppocr/utils/ic15_dict.txt")
image_dir = os.path.join(work_bash, "temp_picture/1.jpg")


def str2bool(v):
    return v.lower() in ("true", "t", "1")


def init_args():
    parser = argparse.ArgumentParser()
    # params for prediction engine
    parser.add_argument("--use_gpu", type=str2bool, default=False)
    parser.add_argument("--ir_optim", type=str2bool, default=True)
    parser.add_argument("--use_tensorrt", type=str2bool, default=False)
    parser.add_argument("--min_subgraph_size", type=int, default=15)
    parser.add_argument("--precision", type=str, default="fp32")
    parser.add_argument("--gpu_mem", type=int, default=500)

    # params for text detector
    parser.add_argument("--image_dir", type=str, default=image_dir)
    parser.add_argument("--det_algorithm", type=str, default='DB')
    parser.add_argument("--det_limit_side_len", type=float, default=960)
    parser.add_argument("--det_limit_type", type=str, default='max')

    # DB parmas
    parser.add_argument("--det_db_thresh", type=float, default=0.3)
    parser.add_argument("--det_db_box_thresh", type=float, default=0.6)
    parser.add_argument("--det_db_unclip_ratio", type=float, default=1.5)
    parser.add_argument("--max_batch_size", type=int, default=10)
    parser.add_argument("--use_dilation", type=str2bool, default=False)
    parser.add_argument("--det_db_score_mode", type=str, default="fast")
    # EAST parmas
    parser.add_argument("--det_east_score_thresh", type=float, default=0.8)
    parser.add_argument("--det_east_cover_thresh", type=float, default=0.1)
    parser.add_argument("--det_east_nms_thresh", type=float, default=0.2)

    # SAST parmas
    parser.add_argument("--det_sast_score_thresh", type=float, default=0.5)
    parser.add_argument("--det_sast_nms_thresh", type=float, default=0.2)
    parser.add_argument("--det_sast_polygon", type=str2bool, default=False)

    # params for text recognizer
    parser.add_argument("--rec_algorithm", type=str, default='CRNN')
    parser.add_argument("--rec_image_shape", type=str, default="3, 32, 320")
    parser.add_argument("--rec_char_type", type=str, default='ch')
    parser.add_argument("--rec_batch_num", type=int, default=6)
    parser.add_argument("--max_text_length", type=int, default=25)
    parser.add_argument(
        "--rec_char_dict_path",
        type=str,
        default=rec_char_dict_path)
    parser.add_argument("--use_space_char", type=str2bool, default=True)
    parser.add_argument(
        "--vis_font_path", type=str, default=vis_font_path)
    parser.add_argument("--drop_score", type=float, default=0.7)

    # params for e2e
    parser.add_argument("--e2e_algorithm", type=str, default='PGNet')
    parser.add_argument("--e2e_model_dir", type=str)
    parser.add_argument("--e2e_limit_side_len", type=float, default=768)
    parser.add_argument("--e2e_limit_type", type=str, default='max')

    # PGNet parmas
    parser.add_argument("--e2e_pgnet_score_thresh", type=float, default=0.5)
    parser.add_argument(
        "--e2e_char_dict_path", type=str, default=e2e_char_dict_path)
    parser.add_argument("--e2e_pgnet_valid_set", type=str, default='totaltext')
    parser.add_argument("--e2e_pgnet_polygon", type=str2bool, default=True)
    parser.add_argument("--e2e_pgnet_mode", type=str, default='fast')

    # params for text classifier
    parser.add_argument("--use_angle_cls", type=str2bool, default=False)
    parser.add_argument("--cls_image_shape", type=str, default="3, 48, 192")
    parser.add_argument("--label_list", type=list, default=['0', '180'])
    parser.add_argument("--cls_batch_num", type=int, default=6)
    parser.add_argument("--cls_thresh", type=float, default=0.9)

    parser.add_argument("--enable_mkldnn", type=str2bool, default=False)
    parser.add_argument("--cpu_threads", type=int, default=10)
    parser.add_argument("--use_pdserving", type=str2bool, default=False)
    parser.add_argument("--warmup", type=str2bool, default=False)

    # multi-process
    parser.add_argument("--use_mp", type=str2bool, default=False)
    parser.add_argument("--total_process_num", type=int, default=1)
    parser.add_argument("--process_id", type=int, default=0)

    parser.add_argument("--benchmark", type=str2bool, default=False)
    parser.add_argument("--save_log_path", type=str, default="")

    parser.add_argument("--show_log", type=str2bool, default=True)
    return parser


def parse_args():
    parser = init_args()
    return parser.parse_known_args()


def create_predictor(args, mode, logger):
    if mode == "det":
        model_dir = det_model_dir
    elif mode == 'cls':
        model_dir = cls_model_dir
    elif mode == 'rec':
        model_dir = rec_model_dir
    else:
        model_dir = args.e2e_model_dir

    if model_dir is None:
        logger.info("not find {} model file path {}".format(mode, model_dir))
        sys.exit(0)
    model_file_path = model_dir + "/inference.pdmodel"
    params_file_path = model_dir + "/inference.pdiparams"
    if not os.path.exists(model_file_path):
        raise ValueError("not find model file path {}".format(model_file_path))
    if not os.path.exists(params_file_path):
        raise ValueError("not find params file path {}".format(
            params_file_path))

    config = inference.Config(model_file_path, params_file_path)

    if hasattr(args, 'precision'):
        if args.precision == "fp16" and args.use_tensorrt:
            precision = inference.PrecisionType.Half
        elif args.precision == "int8":
            precision = inference.PrecisionType.Int8
        else:
            precision = inference.PrecisionType.Float32
    else:
        precision = inference.PrecisionType.Float32

    if args.use_gpu:
        gpu_id = get_infer_gpuid()
        if gpu_id is None:
            raise ValueError(
                "Not found GPU in current device. Please check your device or set args.use_gpu as False"
            )
        config.enable_use_gpu(args.gpu_mem, 0)
        if args.use_tensorrt:
            config.enable_tensorrt_engine(
                precision_mode=precision,
                max_batch_size=args.max_batch_size,
                min_subgraph_size=args.min_subgraph_size)
            # skip the minmum trt subgraph
        if mode == "det":
            min_input_shape = {
                "x": [1, 3, 50, 50],
                "conv2d_92.tmp_0": [1, 120, 20, 20],
                "conv2d_91.tmp_0": [1, 24, 10, 10],
                "conv2d_59.tmp_0": [1, 96, 20, 20],
                "nearest_interp_v2_1.tmp_0": [1, 256, 10, 10],
                "nearest_interp_v2_2.tmp_0": [1, 256, 20, 20],
                "conv2d_124.tmp_0": [1, 256, 20, 20],
                "nearest_interp_v2_3.tmp_0": [1, 64, 20, 20],
                "nearest_interp_v2_4.tmp_0": [1, 64, 20, 20],
                "nearest_interp_v2_5.tmp_0": [1, 64, 20, 20],
                "elementwise_add_7": [1, 56, 2, 2],
                "nearest_interp_v2_0.tmp_0": [1, 256, 2, 2]
            }
            max_input_shape = {
                "x": [1, 3, 2000, 2000],
                "conv2d_92.tmp_0": [1, 120, 400, 400],
                "conv2d_91.tmp_0": [1, 24, 200, 200],
                "conv2d_59.tmp_0": [1, 96, 400, 400],
                "nearest_interp_v2_1.tmp_0": [1, 256, 200, 200],
                "conv2d_124.tmp_0": [1, 256, 400, 400],
                "nearest_interp_v2_2.tmp_0": [1, 256, 400, 400],
                "nearest_interp_v2_3.tmp_0": [1, 64, 400, 400],
                "nearest_interp_v2_4.tmp_0": [1, 64, 400, 400],
                "nearest_interp_v2_5.tmp_0": [1, 64, 400, 400],
                "elementwise_add_7": [1, 56, 400, 400],
                "nearest_interp_v2_0.tmp_0": [1, 256, 400, 400]
            }
            opt_input_shape = {
                "x": [1, 3, 640, 640],
                "conv2d_92.tmp_0": [1, 120, 160, 160],
                "conv2d_91.tmp_0": [1, 24, 80, 80],
                "conv2d_59.tmp_0": [1, 96, 160, 160],
                "nearest_interp_v2_1.tmp_0": [1, 256, 80, 80],
                "nearest_interp_v2_2.tmp_0": [1, 256, 160, 160],
                "conv2d_124.tmp_0": [1, 256, 160, 160],
                "nearest_interp_v2_3.tmp_0": [1, 64, 160, 160],
                "nearest_interp_v2_4.tmp_0": [1, 64, 160, 160],
                "nearest_interp_v2_5.tmp_0": [1, 64, 160, 160],
                "elementwise_add_7": [1, 56, 40, 40],
                "nearest_interp_v2_0.tmp_0": [1, 256, 40, 40]
            }
            min_pact_shape = {
                "nearest_interp_v2_26.tmp_0": [1, 256, 20, 20],
                "nearest_interp_v2_27.tmp_0": [1, 64, 20, 20],
                "nearest_interp_v2_28.tmp_0": [1, 64, 20, 20],
                "nearest_interp_v2_29.tmp_0": [1, 64, 20, 20]
            }
            max_pact_shape = {
                "nearest_interp_v2_26.tmp_0": [1, 256, 400, 400],
                "nearest_interp_v2_27.tmp_0": [1, 64, 400, 400],
                "nearest_interp_v2_28.tmp_0": [1, 64, 400, 400],
                "nearest_interp_v2_29.tmp_0": [1, 64, 400, 400]
            }
            opt_pact_shape = {
                "nearest_interp_v2_26.tmp_0": [1, 256, 160, 160],
                "nearest_interp_v2_27.tmp_0": [1, 64, 160, 160],
                "nearest_interp_v2_28.tmp_0": [1, 64, 160, 160],
                "nearest_interp_v2_29.tmp_0": [1, 64, 160, 160]
            }
            min_input_shape.update(min_pact_shape)
            max_input_shape.update(max_pact_shape)
            opt_input_shape.update(opt_pact_shape)
        elif mode == "rec":
            min_input_shape = {"x": [1, 3, 32, 10]}
            max_input_shape = {"x": [args.rec_batch_num, 3, 32, 2000]}
            opt_input_shape = {"x": [args.rec_batch_num, 3, 32, 320]}
        elif mode == "cls":
            min_input_shape = {"x": [1, 3, 48, 10]}
            max_input_shape = {"x": [args.rec_batch_num, 3, 48, 2000]}
            opt_input_shape = {"x": [args.rec_batch_num, 3, 48, 320]}
        else:
            min_input_shape = {"x": [1, 3, 10, 10]}
            max_input_shape = {"x": [1, 3, 1000, 1000]}
            opt_input_shape = {"x": [1, 3, 500, 500]}
        config.set_trt_dynamic_shape_info(min_input_shape, max_input_shape,
                                          opt_input_shape)

    else:
        config.disable_gpu()
        if hasattr(args, "cpu_threads"):
            config.set_cpu_math_library_num_threads(args.cpu_threads)
        else:
            # default cpu threads as 10
            config.set_cpu_math_library_num_threads(10)
        if args.enable_mkldnn:
            # cache 10 different shapes for mkldnn to avoid memory leak
            config.set_mkldnn_cache_capacity(10)
            config.enable_mkldnn()

    # enable memory optim
    config.enable_memory_optim()
    config.disable_glog_info()

    config.delete_pass("conv_transpose_eltwiseadd_bn_fuse_pass")
    if mode == 'table':
        config.delete_pass("fc_fuse_pass")  # not supported for table
    config.switch_use_feed_fetch_ops(False)
    config.switch_ir_optim(True)

    # create predictor
    predictor = inference.create_predictor(config)
    input_names = predictor.get_input_names()
    for name in input_names:
        input_tensor = predictor.get_input_handle(name)
    output_names = predictor.get_output_names()
    output_tensors = []
    for output_name in output_names:
        output_tensor = predictor.get_output_handle(output_name)
        output_tensors.append(output_tensor)
    return predictor, input_tensor, output_tensors, config


def get_infer_gpuid():
    cmd = "nvidia-smi"
    res = os.popen(cmd).readlines()
    if len(res) == 0:
        return None
    cmd = "env | grep CUDA_VISIBLE_DEVICES"
    env_cuda = os.popen(cmd).readlines()
    if len(env_cuda) == 0:
        return 0
    else:
        gpu_id = env_cuda[0].strip().split("=")[1]
        return int(gpu_id[0])


def resize_img(img, input_size=600):
    img = np.array(img)
    im_shape = img.shape
    im_size_max = np.max(im_shape[0:2])
    im_scale = float(input_size) / float(im_size_max)
    img = cv2.resize(img, None, None, fx=im_scale, fy=im_scale)
    return img


def str_count(s):
    import string
    count_zh = count_pu = 0
    s_len = len(s)
    en_dg_count = 0
    for c in s:
        if c in string.ascii_letters or c.isdigit() or c.isspace():
            en_dg_count += 1
        elif c.isalpha():
            count_zh += 1
        else:
            count_pu += 1
    return s_len - math.ceil(en_dg_count / 2)


def get_rotate_crop_image(img, points):
    assert len(points) == 4, "shape of points must be 4*2"
    img_crop_width = int(
        max(
            np.linalg.norm(points[0] - points[1]),
            np.linalg.norm(points[2] - points[3])))
    img_crop_height = int(
        max(
            np.linalg.norm(points[0] - points[3]),
            np.linalg.norm(points[1] - points[2])))
    pts_std = np.float32([[0, 0], [img_crop_width, 0],
                          [img_crop_width, img_crop_height],
                          [0, img_crop_height]])
    M = cv2.getPerspectiveTransform(points, pts_std)
    dst_img = cv2.warpPerspective(
        img,
        M, (img_crop_width, img_crop_height),
        borderMode=cv2.BORDER_REPLICATE,
        flags=cv2.INTER_CUBIC)
    dst_img_height, dst_img_width = dst_img.shape[0:2]
    if dst_img_height * 1.0 / dst_img_width >= 1.5:
        dst_img = np.rot90(dst_img)
    return dst_img


if __name__ == '__main__':
    pass
