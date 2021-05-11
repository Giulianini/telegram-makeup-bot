from typing import List

import cv2
import matplotlib.pyplot as plt
import numpy as np

from file_manager.path_utilities import get_model_path
from image_utils.conversion import image_resize_with_border, image_resize_restore_ratio
from segmentation import conversions
from segmentation.configuration import color_configuration
from segmentation.configuration.keras_backend import set_keras_backend

CLASSES_TO_SEGMENT = {'skin': True, 'nose': True, 'eye': True, 'brow': True, 'ear': True, 'mouth': True,
                      'hair': True, 'neck': True, 'cloth': False}


class FaceSegmenter:
    def __init__(self):
        set_keras_backend()
        # Configuration
        from segmentation import model
        self.image_size = 256
        # Load the model
        self.inference_model = model.load_model(get_model_path('unet.h5'))

    def segment_image(self, img):
        img = cv2.resize(img, (self.image_size, self.image_size))
        img = img.reshape((1, img.shape[0], img.shape[1], img.shape[2])).astype('float')
        img1_normalized = img / 255.0
        images_predicted = self.inference_model.predict(img1_normalized)
        image_predicted = images_predicted[0]
        return image_predicted

    def segment_images(self, images: List[np.ndarray]):
        # Output images
        predicted_images = []
        # Images
        for img in images:
            predicted_images.append(self.segment_image(img))
        return predicted_images

    def segment_image_keep_aspect_ratio(self, img):
        resized, old_size, border = image_resize_with_border(img, size=self.image_size)
        segmented = self.segment_image(resized)
        restored = image_resize_restore_ratio(segmented, old_size, border)
        return restored

    def segment_images_keep_aspect_ratio(self, images: List[np.ndarray]):
        # Output images
        predicted_images = []
        # Images
        for img in images:
            predicted_images.append(self.segment_image_keep_aspect_ratio(img))
        return predicted_images


def denormalize_and_convert_rgb(masks):
    colors_values_list = color_configuration.get_classes_colors(CLASSES_TO_SEGMENT)
    rgb_images = []
    for mask in masks:
        img_rgb = conversions.denormalize(mask)
        img_rgb = conversions.mask_channels_to_rgb(img_rgb, 8, colors_values_list)
        rgb_images.append(img_rgb)
    return rgb_images
