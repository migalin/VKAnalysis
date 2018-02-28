"""
Modified code of OpenNSFW Library (University of California)
See license in CAFFE LISENSE file
"""

import numpy as np
import os
from PIL import Image
import io
os.environ['GLOG_minloglevel'] = '2'
import sys
import inspect
# Добавляем папку с нейронкой в переменные окружения
cmd_folder = os.path.realpath(os.path.abspath(os.path.split(inspect.getfile( inspect.currentframe() ))[0]))
cmd_subfolder = os.path.realpath(
    os.path.abspath(os.path.join(os.path.split(inspect.getfile(inspect.currentframe()))[0], "caffe/")))
if cmd_folder not in sys.path:
     sys.path.insert(0, cmd_folder)
if cmd_subfolder not in sys.path:
     sys.path.insert(0, cmd_subfolder)
import caffe


class Classifier:
    """
    Класс для обработки изображений на предмет NSFW контента
    """

    def __init__(self, vk_session, nsfw_net=None):

        #Оозначаем директории
        pycaffe_dir = os.path.dirname(__file__)
        proto = os.path.join(pycaffe_dir, 'nsfw_model/deploy.prototxt')
        model = os.path.join(pycaffe_dir, 'nsfw_model/resnet_50_1by2_nsfw.caffemodel')

        #инициализируем сессию
        self.vk_session = vk_session

        # Pre-load caffe model.
        if nsfw_net == None:
            self.nsfw_net = caffe.Net(proto,  # pylint: disable=invalid-name
                                      model,
                                      caffe.TEST)
        else:
            self.nsfw_net = nsfw_net

        self.caffe_transformer = caffe.io.Transformer({'data': self.nsfw_net.blobs['data'].data.shape})
        self.caffe_transformer.set_transpose('data', (2, 0, 1))  # move image channels to outermost
        self.caffe_transformer.set_mean('data', np.array([104, 117, 123]))  # subtract the dataset-mean value in each channel
        self.caffe_transformer.set_raw_scale('data', 255)  # rescale from [0, 1] to [0, 255]
        self.caffe_transformer.set_channel_swap('data', (2, 1, 0))  # swap channels from RGB to BGR

    def resize_image(self, img_data, sz=(256, 256)):
        """
        Resize image. Please use this resize logic for best results instead of the
        caffe, since it was used to generate training dataset
        :param str data:
            The image data
        :param sz tuple:
            The resized image dimensions
        :returns bytearray:
            A byte array with the resized image
        """
        im = Image.open(io.BytesIO(img_data))
        if im.mode != "RGB":
            im = im.convert('RGB')
        imr = im.resize(sz, resample=Image.BILINEAR)
        fh_im = io.BytesIO()
        imr.save(fh_im, format='JPEG')
        fh_im.seek(0)
        return bytearray(fh_im.read())

    def caffe_preprocess_and_compute(self, image_data, output_layers=None):
        """
        Run a Caffe network on an input image after preprocessing it to prepare
        it for Caffe.
        :param PIL.Image image_data:
            PIL image to be input into Caffe.
        :param caffe.Net caffe_net:
            A Caffe network with which to process pimg afrer preprocessing.
        :param list output_layers:
            A list of the names of the layers from caffe_net whose outputs are to
            to be returned.  If this is None, the default outputs for the network
            are returned.
        :return:
            Returns the requested outputs from the Caffe net.
        """
        if self.nsfw_net is not None:

            # Grab the default output names if none were requested specifically.
            if output_layers is None:
                output_layers = self.nsfw_net.outputs

            img_data_rs = self.resize_image(image_data, sz=(256, 256))
            image = caffe.io.load_image(io.BytesIO(img_data_rs))

            H, W, _ = image.shape
            _, _, h, w = self.nsfw_net.blobs['data'].data.shape
            h_off = max((H - h) // 2, 0)
            w_off = max((W - w) // 2, 0)
            crop = image[h_off:h_off + h, w_off:w_off + w, :]
            transformed_image = self.caffe_transformer.preprocess('data', crop)
            transformed_image.shape = (1,) + transformed_image.shape

            input_name = self.nsfw_net.inputs[0]
            all_outputs = self.nsfw_net.forward_all(blobs=output_layers,
                        **{input_name: transformed_image})
            outputs = all_outputs[output_layers[0]][0].astype(float)
            return outputs
        else:
            return []

    def check_photo(self, url):
        image_data = self.vk_session.http.get(url).content

        # Classify.
        scores = self.caffe_preprocess_and_compute(image_data=image_data)
        return {'picture': image_data, 'score': scores[1]}
