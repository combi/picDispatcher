import os
import sys
import shutil
import time

import pyexiv2
import imghdr
from PySide import QtGui, QtCore

# modif locale

'''
    IMPORTANT: Je suis tombe sur cette commande qui semble faire exactement ce que je veux:
    exiftool -d %Y-%m-%d "-directory<datetimeoriginal" *.jpg
    https://www.185vfx.com/2018/11/organize-images-by-date/


    TODO - Barre de progression
    TODO - interface
    TODO - respecter dans l'ordre alphabetique
    TODO - indiquer les nombres de photos par categorie
'''


def timeIt(func):
    def func_decorated(*args, **kwargs):
        startTime = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time()-startTime
        print('[%s time] (%ss)' %(func.__name__, elapsed))
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
        print('%s:' %header)
    if isinstance(toPrint, dict):
        return buildPrintFromDicts([toPrint], offset=offset, sort=sort, associatedTypes=associatedTypes)
    elif toPrintType in (tuple, list, set):
        return buildPrintFromListTupleSet(toPrint, offset=offset, sort=sort, associatedTypes=associatedTypes)


def touch(fname, times=None):
    with open(fname, 'a'):
        os.utime(fname, times)


def get_image_detailed_infos(imagePath, verbose=False):
    if verbose:
        print('')
        print('imagePath = %s' %imagePath)


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
            imageInfos[key] = tagRawValue  # on ne garde que le dernier id du tag pour etre plus concis
        imageInfos['filepath'] = imagePath

        if verbose:
            for t, tv in imageInfos.items():
                print('%s : %s' %(t, tv))
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
        print('%s : %s' % (f, get_image_date_time(f)))


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

        print('src_date = %s' %src_date)
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
    print('imagesWithDate = %s' %imagesWithDate)
    return  # DEBUGONLY
    imagesToMove     = find_images_to_move(imagesWithDate, dstDirPath)
    # imagesWithNoDate = images - set(imagesWithDate.keys())
    # imagesOk         = set(imagesWithDate.keys()) - set(imagesToMove.keys())
    # print 'imagesWithDate=', imagesWithDate
    # for k,v in imagesWithDate.iteritems():
    for k,v in imagesToMove.iteritems():
        print(k,v)

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


def buildFilesDatasFromFolder(srcFolder, dirNamesToSkip=[]):
    if not srcFolder:
        return
    srcFolder_ = os.path.normpath(srcFolder)
    filesToCheck, parsedDirs = get_dir_content(srcFolder_, dirNamesToSkip=dirNamesToSkip)
    print(buildSmartPrintStr(filesToCheck, header='filesToCheck', offset=0, sort=False, associatedTypes=False))
    filesAndMetadatas  = getFilesMetadatas(filesToCheck)

    return filesAndMetadatas


def addMovedInfoInMetadatas(filesAndMetadatas, dstFolder):
    if not dstFolder or not os.path.isdir(dstFolder):
        # TODO(combi): Prevoir le cas ou on veut passer un repertoire a creer qui n'existerait pas encore?
        return

    result = dict()
    for filePath, metadatas in filesAndMetadatas.items():
        if not metadatas:
            continue
        fileName = os.path.basename(filePath)
        datetime = metadatas.get('DateTimeOriginal')

        if not datetime:
            continue
        date = datetime.replace(':', '-').split(' ')[0]
        year = '_%s_' %date.split('-')[0]

        movedFilePath = os.path.join(dstFolder, year, date, fileName)
        metadatas['movedFilepath'] = movedFilePath

    return result


def convertFilesToMovedFilesOLD(filesAndMetadatas, dstDir):
    if not dstDir or not os.path.isdir(dstDir):
        # TODO(combi): Prevoir le cas ou on veut passer un repertoire a creer qui n'existerait pas encore?
        return

    result = dict()
    for filePath, metadatas in filesAndMetadatas.items():
        if not metadatas:
            continue
        fileName = os.path.basename(filePath)
        datetime = metadatas.get('DateTimeOriginal')

        if not datetime:
            continue
        date = datetime.replace(':', '-').split(' ')[0]
        year = '_%s_' %date.split('-')[0]


        newFilePath = os.path.join(dstDir, year, date, fileName)
        result[newFilePath] = metadatas

    return result


def convertFilesToMovedFiles(filesAndMetadatas, dstDir):
    if not dstDir:
        # TODO(combi): Prevoir le cas ou on veut passer un repertoire a creer qui n'existerait pas encore?
        return

    result = dict()
    for filePath, metadatas in filesAndMetadatas.items():
        newFilePath = None

        if metadatas:
            fileName = os.path.basename(filePath)
            datetime = metadatas.get('DateTimeOriginal')

            if datetime:
                date = datetime.replace(':', '-').split(' ')[0]
                year = '_%s_' %date.split('-')[0]

                newFilePath = os.path.join(dstDir, year, date, fileName)

        result[filePath] = newFilePath

    # print 'convertFilesToMovedFiles:'
    # print buildSmartPrintStr(result)
    return result


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
    print('MOVE IMAGES START')
    # filesToMoveData est un dict
    for src, dst in filesToMoveData.items():
        if not src or not dst:
            continue
        dstDir = os.path.dirname(dst)
        ensure_dir(dstDir)
        shutil.move(src, dst)
    print('MOVE IMAGES END')




# -------------------------------------
#               UI
# -------------------------------------

# def removeLastSlashFromFolder

class Colors():
    # white          = QtGui.QColor(240, 240, 240)
    # black          = QtGui.QColor(0, 0, 0)
    # dark_grey      = QtGui.QColor(30, 30, 30)
    # light_grey     = QtGui.QColor(230, 230, 230)
    red            = QtGui.QColor(122, 51 ,51)
    # red_stronger   = QtGui.QColor(183, 38 ,30)
    green          = QtGui.QColor(51 ,122,51)
    # green_stronger = QtGui.QColor(25 ,204,25)
    green_dim      = QtGui.QColor(102 ,153,102)
    blue           = QtGui.QColor(56,102,153)
    orange         = QtGui.QColor(255,178,0)
    # salmon         = QtGui.QColor(151,92,122)
    # yellow         = QtGui.QColor(204,255,76)
    # cyan           = QtGui.QColor(17,174,171)
# LES WIDGETS
class LayoutWidget(QtGui.QWidget):
    # TODO(combi): Exporter dans QtLib?
    def __init__(self, mode='vertical', parent=None):
        super(LayoutWidget, self).__init__(parent=parent)
        if mode in ('vertical', 'horizontal'):
            self.layout = QtGui.QBoxLayout(QtGui.QBoxLayout.LeftToRight, parent=self)  # On est oblige de donner une direction a la creation du layout
            if mode == 'horizontal':
                self.layout.setDirection(QtGui.QBoxLayout.LeftToRight)
            elif mode =='vertical':
                self.layout.setDirection(QtGui.QBoxLayout.TopToBottom)
        elif mode == 'grid':
            self.layout = QtGui.QGridLayout(self)  # On est oblige de donner une direction a la creation du layout
        else:
            raise('''[LayoutWidget]: Le mode %s n'est pas supporte''' %mode)

        self.setLayout(self.layout)
        self.layout.setContentsMargins(0, 0, 0, 0)

    def addWidget(self, *args, **kwargs):
        self.layout.addWidget(*args, **kwargs)

    def setmargins(self, left=0, top=0, right=0, bottom=0):
        self.layout.setContentsMargins(left, top, right, bottom)


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
            print('Nothing to do!')
            return
        self.orientation = orientation
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

        self.populate()
        self.setUniformRowHeights(True)
        self.setSortingEnabled(True)
        self.setHeaderLabels(['file'])
        self.setColumnWidth(0, 400)


        self.itemClicked.connect(self.onSelectItem)

    def updateRootAndDatas(self, root, data):
        self.root = root
        self.data = data or {}

    def populate(self):
        self.clear()

        rootItem = QtGui.QTreeWidgetItem(self, [self.root])
        rootItem.path = self.root
        rootItem.setExpanded(True)

        self.insertTopLevelItems(0, [rootItem])

        itemsBank = dict()
        itemsBank[self.root] = rootItem

        for f, metadatas in self.data.items():
            fileFolder, filename = f.rsplit(os.path.sep, 1)

            parentItem = itemsBank.get(fileFolder)
            if not parentItem:
                intermFoldersPath = fileFolder.replace(self.root, '')

                parentItem = rootItem
                intermFolders = intermFoldersPath.split(os.path.sep)[1:]

                prev = self.root

                while intermFolders:
                    folder = intermFolders.pop(0)

                    intermFolder = os.path.join(prev,folder)
                    folderParentItem = itemsBank.get(intermFolder)
                    if not folderParentItem:
                        folderParentItem = QtGui.QTreeWidgetItem(parentItem, [folder])
                        folderParentItem.setExpanded(True)
                        itemsBank[intermFolder] = folderParentItem
                        folderParentItem.path = intermFolder

                        parentItem = folderParentItem

                    prev = intermFolder

            fileItem = QtGui.QTreeWidgetItem(parentItem, [filename])
            fileItem.path = f

            if metadatas:
                tooltipText = '%s\n\n%s' %(filename, buildSmartPrintStr(metadatas))

                imageDate = metadatas.get('DateTimeOriginal')
                if imageDate:
                    fileItem.setForeground(0, QtGui.QBrush(Colors.green))
                    itemFont = fileItem.font(0)
                    itemFont.setBold(True)
                    fileItem.setFont(0, itemFont)
                else:
                    fileItem.setForeground(0, QtGui.QBrush(Colors.green_dim))
            else:
                print('Info: %s is probably not an image' %f)
                tooltipText = '%s\n\nNot an image' %filename
                fileItem.setForeground(0, QtGui.QBrush(Colors.red))

            fileItem.setToolTip(0, tooltipText)

    def onSelectItem(self, item, col):

        newImage = item.path
        print('item.path = %s' %item.path)
        if not os.path.isfile(newImage):
            print('image file not found')
            return

        print('item, col = %s' %item, col)
        print('item.text = %s' %item.text(col))



class MainUI(QtGui.QWidget):
    def __init__(self, parent=None, srcFolder=None, dstFolder=None):
        super(MainUI, self).__init__(parent)
        self.srcFolder = srcFolder or ''
        self.dstFolder = dstFolder or self.srcFolder
        self.srcData   = {}
        self.dstData   = {}


        mainLayout = QtGui.QVBoxLayout(self)
        self.splitter = QtGui.QSplitter(QtCore.Qt.Horizontal)

        self.srcPanel = LayoutWidget(mode='vertical', parent=self.splitter)
        self.dstPanel = LayoutWidget(mode='vertical', parent=self.splitter)


        self.srcFolderLWidget = LayoutWidget(mode='horizontal', parent=self.splitter)
        self.srcFolderLineEdit = QtGui.QLineEdit(self.srcFolder)
        self.srcFolderLineEdit.setPlaceholderText('src folder')
        self.srcFolderBtn = QtGui.QPushButton('...', parent=self.srcFolderLWidget)
        self.srcFolderBtn.setContentsMargins(0,0,0,0)
        self.srcFolderBtn.setMaximumWidth(30)
        self.srcFolderLineEdit.srcOrDst = 'src'
        self.srcFolderBtn.srcOrDst = 'src'
        self.srcFolderLWidget.addWidget(self.srcFolderLineEdit)
        self.srcFolderLWidget.addWidget(self.srcFolderBtn)

        self.dstFolderLWidget = LayoutWidget(mode='horizontal', parent=self.splitter)
        self.dstFolderLineEdit = QtGui.QLineEdit(self.dstFolder)
        self.dstFolderLineEdit.setPlaceholderText('dst folder')
        self.dstFolderBtn = QtGui.QPushButton('...', parent=self.dstFolderLWidget)
        self.dstFolderBtn.setContentsMargins(0,0,0,0)
        self.dstFolderLineEdit.srcOrDst = 'dst'
        self.dstFolderBtn.srcOrDst = 'dst'
        self.dstFolderBtn.setMaximumWidth(30)
        self.dstFolderLWidget.addWidget(self.dstFolderLineEdit)
        self.dstFolderLWidget.addWidget(self.dstFolderBtn)


        self.srcTree = Tree(data=self.srcData, mode='src', root=self.srcFolder)
        self.dstTree = Tree(data=self.dstData, mode='dst', root=self.dstFolder)

        self.srcPanel.addWidget(self.srcFolderLWidget)
        self.dstPanel.addWidget(self.dstFolderLWidget)

        self.srcPicFrame = PictureFrame()
        self.dstPicFrame = PictureFrame()
        # self.srcPicFrame.setVisible(False)
        # self.dstPicFrame.setVisible(False)

        self.srcPanel.addWidget(self.srcFolderLWidget)
        self.srcPanel.addWidget(self.srcTree)
        self.srcPanel.addWidget(self.srcPicFrame)
        self.dstPanel.addWidget(self.dstFolderLWidget)
        self.dstPanel.addWidget(self.dstTree)
        self.dstPanel.addWidget(self.dstPicFrame)


        self.splitter.addWidget(self.srcPanel)
        self.splitter.addWidget(self.dstPanel)


        self.goBTN = QtGui.QPushButton('GO')

        mainLayout.addWidget(self.splitter)
        mainLayout.addWidget(self.goBTN)

        self.setLayout(mainLayout)



        self.srcFolderLineEdit.clearFocus()
        self.dstFolderLineEdit.clearFocus()

        self.setFocus()

        self.updateSrcAndDstDatas()
        self.updateSrcAndDstTrees()


        self.srcTree.itemClicked.connect(self.changeImage)
        # self.dstTree.itemClicked.connect(self.changeImage)

        self.srcFolderBtn.clicked.connect(self.updateFolderPath)
        self.dstFolderBtn.clicked.connect(self.updateFolderPath)

        self.srcFolderLineEdit.returnPressed.connect(self.onFolderChanged)
        self.dstFolderLineEdit.returnPressed.connect(self.onFolderChanged)
        self.goBTN.clicked.connect(self.onGo)


    def updateSrcAndDstDatas(self):
        self.srcData = buildFilesDatasFromFolder(self.srcFolder) or {}
        self.moveMapping  = convertFilesToMovedFiles(self.srcData, self.dstFolder) or {}
        # self.dstData = {self.moveMapping[k]:v for (k,v) in self.srcData.items() if k in self.moveMapping and v}
        self.dstData = {self.moveMapping[k]:v for (k,v) in self.srcData.items() if self.moveMapping.get(k)}

        print(buildSmartPrintStr(self.srcData, header='self.srcData', offset=0, sort=False, associatedTypes=False))
        print(buildSmartPrintStr(self.moveMapping, header='moveMapping', offset=0, sort=False, associatedTypes=False))
        print(buildSmartPrintStr(self.dstData, header='self.dstData', offset=0, sort=False, associatedTypes=False))

    def updateSrcAndDstTrees(self):
        self.srcTree.root = self.srcFolder
        self.srcTree.data = self.srcData
        self.srcTree.populate()

        self.dstTree.root = self.dstFolder or self.srcFolder
        self.dstTree.data = self.dstData
        self.dstTree.populate()

    def updateFolderPath(self):
        print('[updateFolderPath]')
        sender = self.sender()
        srcOrDst = sender.srcOrDst
        print('srcOrDst = %s' %srcOrDst)
        if srcOrDst == 'src':
            self.srcFolderLineEdit.setText('/home/combi/tests/organize_images_root/sourceFolder')
        elif srcOrDst == 'dst':
            self.dstFolderLineEdit.setText('destination folder updated')

        self.onFolderChanged()

    def onFolderChanged(self):
        print('[onFolderChanged]')
        sender = self.sender()
        print('sender = %s'  %sender)
        srcOrDst = sender.srcOrDst
        if srcOrDst == 'src':
            self.srcFolder = self.srcFolderLineEdit.text()
        elif srcOrDst == 'dst':
            self.dstFolder = self.dstFolderLineEdit.text()

        self.updateSrcAndDstDatas()
        self.updateSrcAndDstTrees()

    def changeImage(self, item, col):
        imagesdatas = dict()
        sender = self.sender()
        if sender == self.srcTree:
            print('source tree!')
            imagesdatas = self.srcData
        # elif sender == self.dstTree:
        #     imagesdatas = self.dstData
        #     print 'destination tree!'

        newImage = item.path
        print('item.path =' %item.path)
        if not os.path.isfile(newImage):
            print('image file not found')
            return

        print('item, col = %s' %item, col)
        print('item.text = %s' %item.text(col))




        print('sender = %s' %sender)
        print('item.path = %s' %item.path)

        print('newImage = %s' %newImage)
        metadata = imagesdatas.get(newImage) or {}
        if not metadata:
            return
        orientation = metadata.get('Orientation')
        print('orientation = %s (%s)' %(orientation, type(orientation)))

        self.srcPicFrame.changePixmap(newImage, orientation=orientation)

    def onGo(self):
        print('[ON GO START]')
        move_images(self.moveMapping)
        print('[ON GO END]')

if __name__ == '__main__':


    # if True:
    if False:
        filesAndMetadatas = buildFilesDatasFromFolder('/home/combi/tests/organize_images_root/sourceFolder')
        print('filesAndMetadatas = %s' %buildSmartPrintStr(filesAndMetadatas))
        yyy  = addMovedInfoInMetadatas(filesAndMetadatas, '/home/combi/tests/organize_images_root/destFolder')
        print('yyy = %s' %buildSmartPrintStr(yyy))
        # get_image_detailed_infos('/home/combi/tests/organize_images_root/subfolder1/IMG_20170618_111810.jpg', verbose=True)
        # get_image_detailed_infos('/home/combi/tests/organize_images_root/subfolder1/IMG_20170615_210758.jpg', verbose=True)

    else:
        app = QtGui.QApplication(sys.argv)
        # X = MainUI(srcFolder='/home/combi/tests/organize_images_root/sourceFolder/', dstFolder='/home/combi/tests/organize_images_root/destFolder')
        X = MainUI(srcFolder='/home/combi/tests/organize_images_root/sourceFolder', dstFolder='/home/combi/tests/organize_images_root/destFolder')
        # X = MainUI()
        X.show()
        sys.exit(app.exec_())


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
