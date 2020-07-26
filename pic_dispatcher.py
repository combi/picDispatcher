import os
import sys
import shutil
import time

import pyexiv2
import imghdr
from PySide import QtGui, QtCore

'''
IMPORTANT: Je suis tombe sur cette commande qui semble faire exactement ce que je veux:
exiftool -d %Y-%m-%d "-directory<datetimeoriginal" *.jpg
https://www.185vfx.com/2018/11/organize-images-by-date/
'''


def timeIt(func):
    def func_decorated(*args, **kwargs):
        startTime = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time()-startTime
        print '[%s time] (%ss)' %(func.__name__, elapsed)
        return result

    return func_decorated

def buildPrintFromDicts(dicts, reverse=False, offset=0, sort=True, associatedTypes=False):
    '''
    input: dicts (list of dicts)
    Un petite fonction pour printer de facon propre les dictionnaires passes en argument.
    '''
    toPrint = ''

    # Pour pouvoir printer de facon propre, je souhaite connaitre la longueur
    # maximale des cles de tous les dicts passes en argument
    all_keys = []
    for d in dicts:
        all_keys.extend(d.keys())

    if not len(all_keys):
        return 'Dicts are empty'

    offsetStr = ' '*offset
    tabVal = len(max(map(str, all_keys), key=len)) +4

    for d in dicts:
        dictContent = d.items()
        if sort:
            # dictContent = sorted(dictContent, key=lambda x: str(x[0]).zfill(1000).lower())
            dictContent.sort()
        if associatedTypes:
            for k,v in dictContent:
                toPrint += '{4}{0:.<{3}}{1} ({2})\n'.format(str(k), str(v), type(v), tabVal, str(offsetStr))  # Je sais je sais, c'est imbitable, mais ca permet de faire du print super propre avec peu de code

        else:
            for k,v in dictContent:
                toPrint += '{3}{0:.<{2}}{1}\n'.format(str(k), str(v), tabVal, str(offsetStr))  # Je sais je sais, c'est imbitable, mais ca permet de faire du print super propre avec peu de code

        toPrint += '\n'

    return toPrint

def buildPrintFromListTupleSet(iterable, offset=0, sort=False, associatedTypes=False):
    toPrint = ''
    if sort:
        for x in sorted(iterable):
            toPrint += '%s%s\n' %(' '*offset, x)
    else:
        for x in iterable:
            if associatedTypes:
                toPrint += '%s%s (%s)\n' %(' '*offset, x, type(x))
            else:
                toPrint += '%s%s\n' %(' '*offset, x)
    return toPrint

def buildSmartPrintStr(toPrint, header=None, offset=0, sort=False, associatedTypes=False):
    toPrintType = type(toPrint)
    if header:
        print '%s:' %header
    if isinstance(toPrint, dict):
        return buildPrintFromDicts([toPrint], offset=offset, sort=sort, associatedTypes=associatedTypes)
    elif toPrintType in (tuple, list, set):
        return buildPrintFromListTupleSet(toPrint, offset=offset, sort=sort, associatedTypes=associatedTypes)


def touch(fname, times=None):
    with open(fname, 'a'):
        os.utime(fname, times)


def get_image_detailed_infos(imagePath, verbose=False):
    if verbose:
        print
        print 'imagePath =', imagePath


    imageInfos  = {}

    tagsToCheck = []
    tagsToCheck.append('Exif.Image.Make')
    tagsToCheck.append('Exif.Image.Model')
    tagsToCheck.append('Exif.Photo.DateTimeOriginal')
    tagsToCheck.append('Exif.Image.Orientation')
    tagsToCheck.append('Exif.Image.ImageWidth')
    tagsToCheck.append('Exif.Image.ImageLength')

    try:
        metadata = pyexiv2.ImageMetadata(imagePath)
        metadata.read()
        for tag in tagsToCheck:
            tagRawValue = None
            try:
                tagRawValue = metadata[tag].raw_value
            except:
                pass
            key = tag.split('.')[-1]
            if key in ('Orientation','ImageWidth','ImageLength'):
                tagRawValue = int(tagRawValue)
                print 'tagRawValue =', tagRawValue
            imageInfos[key] = tagRawValue  # on ne garde que le dernier id du tag pour etre plus concis

        if verbose:
            for t, tv in imageInfos.items():
                print t, ':', tv
    except:
        pass

    return imageInfos


def are_images_exif_identical(imageA, imageB):
    return get_image_detailed_infos(imageA) == get_image_detailed_infos(imageB)


def get_image_date_time(image):
    ''' http://tilloy.net/dev/pyexiv2/api.html '''
    date = None
    try:
        metadata = pyexiv2.ImageMetadata(image)
        metadata.read()
        datetimeTag = metadata['Exif.Photo.DateTimeOriginal']
        date = datetimeTag.value.strftime('%Y-%m-%d')
    except:
        pass
    return date

def get_image_orientation(image):
    result = None
    try:
        metadata = pyexiv2.ImageMetadata(image)
        metadata.read()
        result = metadata['Exif.Image.Orientation']
    except:
        pass
    return result


def print_dir_times(dirPath):
    for f in get_dir_content(dirPath):
        print '%s : %s' % (f, get_image_date_time(f))


def colors(col):
    cols = {}
    cols['header'] = '\033[95m'
    cols['blue']   = '\033[94m'
    cols['green']  = '\033[92m'
    cols['warn']   = '\033[93m'
    cols['fail']   = '\033[91m'
    cols['end']    = '\033[0m'
    return cols.get(col, '')


def ensure_dir(dirPath):
    # from http://stackoverflow.com/questions/273192/check-if-a-directory-exists-and-create-it-if-necessary
    try:
        os.makedirs(dirPath)
    except OSError:
        if not os.path.isdir(dirPath):
            # There was an error on creation, so make sure we know about it
            raise


def get_dir_content(dirPath, dirNamesToSkip=[]):
    foundFiles = []
    parsedDirs = [dirPath]

    for root, dirs, files in os.walk(dirPath):
        for d in dirNamesToSkip:
            if d in dirs:
                dirs.remove(d)
        tmp = [os.path.join(root, d) for d in dirs]
        parsedDirs.extend(tmp)

        for f in files:
            foundFiles.append(os.path.join(root, f))

    return (foundFiles,parsedDirs)


def find_no_image_files(filesToCheck):
    result = []
    for f in filesToCheck:
        if not imghdr.what(f):  # files that are not images
            result.append(f)
            continue

    return result


def find_no_date_image_files(filesToCheck):
    result = []

    for f in filesToCheck:
        src_imageInfos = get_image_detailed_infos(f)
        src_datetime   = src_imageInfos['DateTimeOriginal']
        if src_datetime is None:  # files that have no date time
            result.append(f)

    return result


def filter_images_with_date(filesToCheck):
    result = dict()

    for f in filesToCheck:
        imageInfos = get_image_detailed_infos(f)
        datetime   = imageInfos['DateTimeOriginal']
        if datetime is None:  # files that have no date time
            continue
        result[f] = imageInfos

    return result


def filter_files(filesToCheck):
    imagesWithDate   = dict()
    imagesWithNoDate = []
    otherFiles       = []

    for f in filesToCheck:
        if not imghdr.what(f):  # files that are not images
            otherFiles.append(f)
        else:
            imageInfos = get_image_detailed_infos(f)
            datetime   = imageInfos['DateTimeOriginal']
            if datetime is None:  # files that have no date time
                imagesWithNoDate.append(f)
            else:
                imagesWithDate[f] = imageInfos

    return(imagesWithDate,imagesWithNoDate, otherFiles)




def getFilesMetadatas(filesToCheck):
    imagesWithDate   = dict()

    for f in filesToCheck:
        imageInfos = None
        if imghdr.what(f):  # files that are not images
            imageInfos = get_image_detailed_infos(f)

        imagesWithDate[f] = imageInfos

    return imagesWithDate



def find_images_to_move(imagesInfosDict, dstDir):
    result = dict()

    for src_image, src_imageInfos in imagesInfosDict.iteritems():
        # print src_image, src_imageInfos
        # continue
        imageName      = os.path.basename(src_image)
        src_datetime   = src_imageInfos['DateTimeOriginal']
        src_date       = src_datetime.replace(':', '-').split(' ')[0]
        year           = '_%s_' %src_date.split('-')[0]

        # print 'src_date=', src_date
        dst_image      = os.path.join(dstDir, year, src_date, imageName)
        dst_imageInfos = get_image_detailed_infos(dst_image)
        if os.path.isfile(dst_image):
            if dst_imageInfos == src_imageInfos:
                continue
            else:
                image, ext = os.path.splitext(imageName)
                suffix = '__variante_'
                incr   = 1
                suffIncr = '%s%s' %(suffix,incr)
                testFile = image + suffIncr + ext
                testFilePath = os.path.join(dstDir, year, src_date, testFile)
                while(os.path.isfile(testFilePath)):
                    incr+=1
                    suffIncr = '%s%s' %(suffix,incr)
                    testFile = image + suffIncr + ext
                    testFilePath = os.path.join(dstDir, year, src_date, testFile)

                result[src_image] = testFilePath
        else:
            result[src_image] = dst_image

    return result


def ZZZ(srcDirPath, dstDirPath=None, dirNamesToSkip=[]):

    srcDirPath = os.path.normpath(srcDirPath)
    if not dstDirPath:
        dstDirPath = srcDirPath
    else:
        dstDirPath = os.path.normpath(dstDirPath)

    # filesToCheck    = []
    # filesNoImage    = []
    filesToCheck, parsedDirs = get_dir_content(srcDirPath, dirNamesToSkip=dirNamesToSkip)

    filesToCheck     = set(filesToCheck)
    filesNoImage     = set(find_no_image_files(filesToCheck))
    images           = filesToCheck - filesNoImage
    imagesWithDate   = filter_images_with_date(images)
    print 'imagesWithDate=', imagesWithDate
    return  # DEBUGONLY
    imagesToMove     = find_images_to_move(imagesWithDate, dstDirPath)
    # imagesWithNoDate = images - set(imagesWithDate.keys())
    # imagesOk         = set(imagesWithDate.keys()) - set(imagesToMove.keys())
    # print 'imagesWithDate=', imagesWithDate
    # for k,v in imagesWithDate.iteritems():
    for k,v in imagesToMove.iteritems():
        print k,v

    return imagesToMove


def ZZZ2(srcDirPath, dstDirPath=None, dirNamesToSkip=[]):

    srcDirPath = os.path.normpath(srcDirPath)
    if not dstDirPath:
        dstDirPath = srcDirPath
    else:
        dstDirPath = os.path.normpath(dstDirPath)

    filesToCheck, parsedDirs = get_dir_content(srcDirPath, dirNamesToSkip=dirNamesToSkip)
    # print 'filesToCheck =', filesToCheck
    imagesWithDate, imagesWithNoDate, otherFiles = filter_files(filesToCheck)
    # print buildPrintFromDicts([imagesWithDate])
    imagesToMove     = find_images_to_move(imagesWithDate, dstDirPath)

    return imagesToMove


def ZZZ3(srcDirPath, dstDirPath=None, dirNamesToSkip=[]):

    srcDirPath = os.path.normpath(srcDirPath)
    if not dstDirPath:
        dstDirPath = srcDirPath
    else:
        dstDirPath = os.path.normpath(dstDirPath)

    filesToCheck, parsedDirs = get_dir_content(srcDirPath, dirNamesToSkip=dirNamesToSkip)
    filesMetadatas  = getFilesMetadatas(filesToCheck)


    return filesMetadatas


@timeIt
def build_files_data(srcDirPath):
    srcDirPath = os.path.normpath(srcDirPath)
    filesToCheck, parsedDirs = get_dir_content(srcDirPath)

    result   = dict()

    for f in filesToCheck:
        result[f] = {'isImage':False, 'imageData':None}

        if not imghdr.what(f):  # files that are not images
            continue
        imageDatas = get_image_detailed_infos(f)
        if imageDatas['DateTimeOriginal'] is None:
            imageDatas = None

        result[f]['isImage']   = True
        result[f]['imageData'] = imageDatas

    return(result)


def move_images(filesToMoveData):
    # filesToMoveData est un dict
    for src, dst in filesToMoveData.items():
        dstDir = os.path.dirname(dst)
        ensure_dir(dstDir)
        shutil.move(src, dst)


class PictureFrame(QtGui.QLabel):
    def __init__(self, img=None, orientation=None):
        super(PictureFrame, self).__init__()
        self.setFrameStyle(QtGui.QFrame.StyledPanel)

        self.pixmap = None
        self.orientation = None
        self.img = None

        if self.img:
            self.changePixmap(img, orientation=orientation)

    def paintEvent(self, event):
        if self.pixmap:
            size = self.size()
            painter = QtGui.QPainter(self)
            point = QtCore.QPoint(0,0)

            scaledPix = self.pixmap.scaled(size, QtCore.Qt.KeepAspectRatio)


            # start painting the label from left upper corner
            point.setX((size.width() - scaledPix.width())/2)
            point.setY((size.height() - scaledPix.height())/2)

            painter.drawPixmap(point, scaledPix)

    def changePixmap(self, img, orientation=None):
        # https://sirv.com/help/articles/rotate-photos-to-be-upright/
        if self.img == img:
            print 'Nothing to do!'
            return
        self.orientation = orientation
        print 'self.orientation =', self.orientation
        transform = QtGui.QTransform()
        if self.orientation == 6 :
            transform.rotate(90)
        if self.orientation == 3 :
            transform.rotate(180)
        if self.orientation == 8 :
            transform.rotate(270)

        self.pixmap = QtGui.QPixmap(img).transformed(transform)
        self.repaint()  # repaint() will trigger the paintEvent(self, event), this way the new pixmap will be drawn on the label


class Tree(QtGui.QTreeWidget):
    """docstring for Tree"""
    def __init__(self, data=None, mode='src', root=None):
        super(Tree, self).__init__()
        if data is None:
            return
        self.data = data
        self.root = root

        self.rootItem = QtGui.QTreeWidgetItem(None, [self.root, ''])
        self.insertTopLevelItems(0, [self.rootItem])

        self.addItems([f.replace(root, '') for f in self.data])
        self.setUniformRowHeights(True)
        self.setSortingEnabled(True)

        self.setHeaderLabels(['file', 'tests'])
        self.setColumnWidth(0, 400)

    def addItems(self, toParse):
        # Note(combi): Pour de gros volumes, il faudrait surement proceder en 2 passes:
        # - Grouper les images par repertoire via groupBy
        # - Ajouter les repertoires trouves
        # - Ajouter les images d'un repertoire pour minimiser les lookup du widgetItem sous lequel inserer les images

        hierarchies = set()
        for f in toParse:
            dirs = tuple(f.split('/'))
            hierarchies.add(dirs)

        for hierarchy in hierarchies:
            parentItem = self.rootItem
            for folder in hierarchy:
                entryExists = False
                children = [parentItem.child(i) for i in range(parentItem.childCount())]
                for child in children:
                    if folder == child.text(0):
                        parentItem = child
                        entryExists = True
                        break

                if not entryExists:
                    created = QtGui.QTreeWidgetItem(parentItem, [folder, ''])
                    parentItem = created



class TreeNew(QtGui.QTreeWidget):
    """docstring for Tree"""
    def __init__(self, data=None, mode='src', root=None):
        super(TreeNew, self).__init__()
        if data is None:
            return
        self.data = data
        self.root = root


        self.rootItem = QtGui.QTreeWidgetItem(None, [self.root])
        self.rootItem.imagePath = None

        self.insertTopLevelItems(0, [self.rootItem])

        self.populate()
        self.setUniformRowHeights(True)
        self.setSortingEnabled(True)
        self.setHeaderLabels(['file'])
        self.setColumnWidth(0, 400)



    def populate(self):
        itemsBank = dict()
        itemsBank[self.root] = self.rootItem

        for f, metadatas in self.data.items():
            if not metadatas:
                continue

            fileFolder, filename = f.rsplit(os.path.sep, 1)
            intermFoldersPath = fileFolder.replace(self.root, '')

            parentItem = itemsBank.get(fileFolder)
            if not parentItem:
                parentItem = self.rootItem
                intermFolders = intermFoldersPath.split(os.path.sep)[1:]

                prev = self.root

                while intermFolders:
                    folder = intermFolders.pop(0)

                    intermFolder = os.path.join(prev,folder)
                    newParentItem = itemsBank.get(intermFolder)
                    if not newParentItem:
                        newParentItem = QtGui.QTreeWidgetItem(parentItem, [folder])
                        newParentItem.imagePath = None
                        itemsBank[intermFolder] = newParentItem
                        parentItem = newParentItem

                    prev = intermFolder

            imageItem = QtGui.QTreeWidgetItem(parentItem, [filename])
            imageItem.imagePath = f





class MainUI(QtGui.QWidget):
    def __init__(self, parent=None, srcDir=None, dstDir=None):
        super(MainUI, self).__init__(parent)
        self.srcDir = srcDir
        self.dstDir = dstDir or srcDir
        # self.data   = ZZZ(self.srcDir, self.dstDir)
        # self.data   = ZZZ2(self.srcDir, self.dstDir)
        self.data   = ZZZ3(self.srcDir, self.dstDir)


        if self.srcDir.endswith(os.path.sep):
            self.srcDir = self.srcDir[:-1]

        if self.dstDir.endswith(os.path.sep):
            self.dstDir = self.dstDir[:-1]

        tree_src = TreeNew(data=self.data, mode='src', root=self.srcDir)

        gl = QtGui.QHBoxLayout(self)


        # self.picFrame = PictureFrame(img=self.data.keys()[-1], orientation=8)
        self.picFrame = PictureFrame()

        splitter = QtGui.QSplitter(QtCore.Qt.Horizontal)
        splitter.addWidget(tree_src)
        # splitter.addWidget(tree_dst)
        splitter.addWidget(self.picFrame)

        gl.addWidget(splitter)
        self.setLayout(gl)

        tree_src.itemClicked.connect(self.changeImage)

    def changeImage(self, item, col):
        print 'item, col =', item, col
        print 'item.text =', item.text(col)
        # sender = self.sender()
        # print 'sender =', sender
        print 'item.imagePath =', item.imagePath

        newImage = item.imagePath
        orientation = self.data.get(newImage, {}).get('Orientation')
        print 'orientation =', orientation, type(orientation)

        self.picFrame.changePixmap(newImage, orientation=orientation)

if __name__ == '__main__':
    # /home/combi/DEV/PYTHON/pyexiv2_tests.py
    # Pour recuperer la date d'une image passee en argument
    # f = '/home/combi/tests/justTesting.py'
    # print '%s  -  %s' % (f, get_image_detailed_infos(f))
    # root = '/home/combi/tests/'
    # dstFiles= ZZZ(root).values()

    # for key, group in groupby(data_underRoot, lambda x: os.path.dirname(x)):
    #     print
    #     print 'key=', key
    #     print '\n'.join(group)

    '''
    todo - Barre de progression
    todo - interface
    todo - respecter dans l'ordre alphabetique
    todo - indiquer les nombres de photos par categorie
    '''

    # import argparse

    # parser = argparse.ArgumentParser(description='That script do some awesome shits')
    # parser.add_argument('-s', '--source', help='Source folder.')
    # parser.add_argument('-d', '--destination', help='Destination folder')
    # parser.add_argument('-t', '--testMode', default=False, action='store_true', help='You can do a "simulation" with this flag')
    # args = parser.parse_args()

    # _src      = args.source
    # _dst      = args.destination
    # _testMode = args.testMode

    # confirmMessage = '''
    # Src folder      : %s
    # Dst folder      : %s
    # testMode        : %s
    # Continue? (y/n) : ''' %(_src, _dst, _testMode)
    # confirm = raw_input(confirmMessage)

    # if True:
    if False:
        ZZZ3('/home/combi/tests/organize_images_root/')

        get_image_detailed_infos('/home/combi/tests/organize_images_root/subfolder1/IMG_20170618_111810.jpg', verbose=True)
        get_image_detailed_infos('/home/combi/tests/organize_images_root/subfolder1/IMG_20170615_210758.jpg', verbose=True)

    else:
        app = QtGui.QApplication(sys.argv)
        X = MainUI(srcDir='/home/combi/tests/organize_images_root/')
        X.show()
        sys.exit(app.exec_())