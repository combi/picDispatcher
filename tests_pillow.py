import PIL
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

# Usefull:
# https://github.com/python-pillow/Pillow/issues/5863
# https://pillow.readthedocs.io/en/stable/reference/Image.html#PIL.Image.Exif


def __define_exif_offset_id():
    # if BOB is None:
    for key, value in TAGS.items():
        if value == "ExifOffset":
            return key
def __define_gps_infos_id():
    for key, value in TAGS.items():
        if value == "GPSInfo":
            return key

_EXIF_OFFSET_ID = __define_exif_offset_id()
_GPS_INFOS_ID   = __define_gps_infos_id()


def get_gps_infos_ifd(exif):
    gps_info = exif.get_ifd(_GPS_INFOS_ID)
    return {
        GPSTAGS.get(key, key): value
        for key, value in gps_info.items()
    }

def get_exif_ifd(exif):
    info = exif.get_ifd(_EXIF_OFFSET_ID)
    return {
        TAGS.get(key, key): value
        for key, value in info.items()
    }

def inspect_image(imagePath):

    image = Image.open(imagePath)


    info_dict = {
        "Filename"          : image.filename,
        "Image Size"        : image.size,
        "Image Height"      : image.height,
        "Image Width"       : image.width,
        "Image Format"      : image.format,
        "Image Mode"        : image.mode,
        "Image is Animated" : getattr(image, "is_animated", False),
        "Frames in Image"   : getattr(image, "n_frames", 1)
    }

    for label,value in info_dict.items():
        print(f"{label:25}: {value}")

    exifdata = image.getexif()
    # exifdata = image._getexif()
    print(type(exifdata))
    for tag_id, data in exifdata.items():
        tagname = TAGS.get(tag_id, tag_id)
        # if isinstance(data, bytes):
        #     # print('Bytes detected for tag %s' %tagname)
        #     data = data.decode()
        print(f"{tag_id:<8}{tagname:25}: {data}")

    xx = get_exif_ifd(exifdata)
    print('xx = %s' %(xx))
    yy = get_gps_infos_ifd(exifdata)
    print('yy = %s' %(yy))yy
    # gps_info = {}
    # for key in exifdata['GPSInfo'].keys():
    #     decode = GPSTAGS.get(key,key)
    #     gps_info[decode] = exif_table['GPSInfo'][key]

def dumpExifTags():
    print('GPSTAGS:')
    for k,v in GPSTAGS.items():
        print(f"{k:<6}: {v}")
    print('TAGS:')
    for k,v in TAGS.items():
        print(f"{k:<6}: {v}")

if __name__ == '__main__':
    print('Using Pillow version: %s' %PIL.__version__)
    imagePath = "/home/combi/tests/organize_images_root/sourceFolder/image.jpg"
    # imagePath = "/home/combi/tests/organize_images_root/sourceFolder/image2.jpg"
    # imagePath = "/home/combi/tests/organize_images_root/sourceFolder/image3.jpg"
    i = inspect_image(imagePath)
    # dumpExifTags()
    # test()
