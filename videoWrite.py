# modded https://github.com/krishnachaitanya7/pil_video/blob/main/pil_video/pil_video.py

import os
from PIL import Image  # noqa
import tempfile
import shutil
import imageio
import time as t
from os import path

def make_video(image_list, name=None, fps = 20):
    """The main def for creating a temporary video out of the 
    PIL Image list passed, according to the FPS passed
    Parameters
    ----------
    image_list : list
        A list of PIL Images in sequential order you want the video to be generated
    fps : int
        The FPS of the video
    delete_folder : bool, optional
        If set to False, this will not delete the temporary folder where images and video are saved, by default True
    play_video : bool, optional
        If set to false, the video generated will not be played, by default True
    """
    if name == None:
        name = str(t.time()) + '.mp4'
    # Make an empty directort in temp, which we are gonna delete later
    dirpath = 'N:\\Temp\\aa'   # Example: '/tmp/tmpacxadh7t'
    if path.exists(dirpath):
        shutil.rmtree(dirpath)
    if not path.exists(dirpath):
        os.mkdir(dirpath)
    
    video_filenames = []
    for i, each_image in enumerate(image_list):
        # TODO: Correct the below snippet
        # if not isinstance(each_image, type(Image)):
        #     raise Exception("The element is not an PIL Image instance")
        filename = "{}\\{}.png".format(dirpath, i)
        video_filenames.append(filename)
        each_image.save("{}".format(filename))
        print('saved', filename)
    writer = imageio.get_writer(("E:\\tempvideo\\fisher\\" + name).format(dirpath), fps=fps)
    for each_image in video_filenames:
        writer.append_data(imageio.imread(each_image))
    writer.close()
    if True:
        shutil.rmtree(dirpath)