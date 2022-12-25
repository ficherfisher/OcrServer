## ocr详解

​		基于paddlepaddleOcr，重新训练detective，rec模型

- 使用PPOCRLabel，打标detect数据集

PPOCRLabel是一款适用于OCR领域的半自动化图形标注工具，内置PPOCR模型对数据自动标注和重新识别。使用python3和pyqt5编写，支持矩形框标注和四点标注模式，导出格式可直接用于PPOCR检测和识别模型的训练。[见paddlepaddle  PPOCRLabel](https://github.com/PaddlePaddle/PaddleOCR/blob/release/2.3/PPOCRLabel/README_ch.md)

- 使用PPOCRLabel，打标rec数据集

同上

> PPOCRLabel 在windows 上使用时需要安装c++的编译链。此处提供下载地址：[Google云 ](https://drive.google.com/drive/folders/1npo-iSGj-xh53Bb9YyUxdB44CTQCHU0a)







- 
- OcrServer详解
  - [Ocr](./doc/Ocr.md)
  - [服务器API](./doc/flask_nginx_gunicorn.md)
  - [多级缓存持久化](./doc/redis_mysql.md)
- [联系作者](