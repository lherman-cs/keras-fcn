import keras

from keras.models import Model
from keras.layers import (
    Input
)

from keras.layers.convolutional import (
    Conv2D
)

from keras_fcn.layers import CroppingLike2D
from keras_fcn.blocks import (
    vgg_deconv,
    vgg_score
)


def Decoder(pyramid, blocks):
    """A Functional decoder.

    :param: pyramid: A list of features in pyramid, scaling from large
                    receptive field to small receptive field.
                    The bottom of the pyramid is the input image.
    :param: blocks: A list of functions that takes a feature from the feature
                    pyramid, x, applies upsampling and accumulate the result
                    from the top of the pyramid.
                    The first block should expect the accumulated result, y,
                    is None. For example, see keras_fcn.blocks.vgg_deconv
                    The last block should simply apply a cropping on y to match
                    the shape of x. For example, see keras_fcn.blocks.vgg_score
    """
    if len(blocks) != len(pyramid):
        raise ValueError('`blocks` needs to match the length of'
                         '`pyramid`.')
    # decoded feature
    decoded = None
    for feat, blk in zip(pyramid, blocks):
        decoded = blk(feat, decoded)

    return decoded


def VGGDecoder(pyramid, scales, classes):
    """A Functional decoder for the VGG Nets.

    :param: pyramid: A list of features in pyramid, scaling from large
                    receptive field to small receptive field.
                    The bottom of the pyramid is the input image.
    :param: scales: A list of weights for each of the feature map in the
                    pyramid, sorted in the same order as the pyramid.
    :param: classes: Integer, number of classes.
    """
    if len(scales) != len(pyramid) - 1:
        raise ValueError('`scales` needs to match the length of'
                         '`pyramid` - 1.')
    blocks = []

    features = pyramid[:-1]
    for i in range(len(features)):
        block_name = 'feat{}'.format(i + 1)
        if i < len(features) - 1:
            block = vgg_deconv(classes=classes, scale=scales[i],
                               kernel_size=(4, 4), strides=(2, 2),
                               crop_offset='centered',
                               block_name=block_name)
        else:
            block = vgg_deconv(classes=classes, scale=scales[i],
                               kernel_size=(16, 16), strides=(8, 8),
                               crop_offset='centered',
                               block_name=block_name)
        blocks.append(block)

    # Crop the decoded feature to match the image
    blocks.append(vgg_score(crop_offset='centered'))

    return Decoder(pyramid=pyramid, blocks=blocks)
