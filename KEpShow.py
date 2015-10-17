#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" tool to help keeping updated with diffusion date of TV Shows """
# pyuic4 -o ui_KEpShow.py KEpShow.ui
# File : KEpShow.py
import datetime, locale, os, re, sys, time, urllib.request, urllib.error, urllib.parse, warnings
from PyQt4 import QtCore, QtGui

from ui_KEpShow import Ui_MainQWidget

# display deprecation warnings
warnings.simplefilter('default')

XML_FILENAME = "KEpShow_dirs.xml"
DIRECTORIES_TO_PARSE = []

TODAY = datetime.datetime.now().strftime("%d/%m/%Y")

SHOW_SEEN_TO = {}

################################################################################
################################################################################
def parse_page(view, page, dirpath):
    """ Parse epguides webpage """
    locale.setlocale(locale.LC_ALL, 'C')
    url  = "http://epguides.com/"
    url += str(page)
    request = urllib.request.Request(url)
    request.add_header('Cookie', 'ListDisplay=tvrage.com')
    webpage = urllib.request.urlopen(request).readlines()
    found_first = 0
    model = QtGui.QStandardItemModel(0, 3)

    found = 0
    dir_content = []
    for files in os.listdir(dirpath):
        if os.path.isfile(dirpath + "/" + files):
            dir_content.append(files.lower())
        else:
            for child_files in os.listdir(dirpath + "/" + files):
                if os.path.isfile(
                    os.path.join(str(dirpath + "/" + files), child_files)
                ):
                    dir_content.append(child_files)

    for line in webpage:
        line = line.decode("ISO-8859-1") # 'UTF-8'
        if found_first == 0:
            if line[0:17] == '<div id="eplist">':
                found_first += 1
        else:
            split_line = re.search(
                "\d*\s*(\d*)[-](\d*).{15}\s*(\d*)[/]([a-zA-Z]*)[/](\d*)",line)
            if split_line:
                diffusion_date = time.strptime(
                                        "%02d" % int(split_line.group(3))
                                        + "/" +
                                        split_line.group(4)
                                        + "/" +
                                        split_line.group(5),
                                    "%d/%b/%y")

                season_nb  = int(split_line.group(1))
                episode_nb = int(split_line.group(2))
                str_cat = "s" + "%02d" % season_nb + "e" + "%02d" % episode_nb
                found = 0
                filename = ""

                lowpage = str(page).lower()

                if lowpage in SHOW_SEEN_TO:
                    split_ep = re.search("(\d*)[e](\d*)",
                                  SHOW_SEEN_TO[str(lowpage)])
                    if split_ep:
                        if season_nb < int(split_ep.group(1)):
                            found = 2
                        elif season_nb == int(split_ep.group(1)):
                            if episode_nb <= int(split_ep.group(2)):
                                found = 2

                # replace 720p by a space to avoid
                # detecting it as an episode number
                for mkv in dir_content:
                    if mkv.lower().find("zip") == -1 & mkv.lower().find("srt") == -1 & mkv.lower().find("ass") == -1 & mkv.lower().find("nfo") == -1:
                        if mkv.replace("720p", "", 1).lower().find(str_cat) != -1:
                            dir_content.remove(mkv)
                            filename = mkv
                            found = 1
                        elif mkv.replace("720p", "", 1).lower().find(
                                str(season_nb) + str("%02d" % episode_nb)) != -1:
                            dir_content.remove(mkv)
                            filename = mkv
                            found = 1
                        elif mkv.replace("720p", "", 1).lower().find(
                                str(season_nb) + "x" + str("%02d" % episode_nb)
                                ) != -1:
                            dir_content.remove(mkv)
                            filename = mkv
                            found = 1
                    #else:
                        #print "Found zip,srt,ass or nfo files"

                diffusion_date = datetime.datetime(*diffusion_date[0:7]).strftime("%d/%m/%Y")

                check = datetime.datetime.strptime(diffusion_date,"%d/%m/%Y") - datetime.datetime.strptime(TODAY,"%d/%m/%Y")

                color = "#86FF68"
                # not aired yet
                if check.days > 0:
                    color = "#8BB2FF"
                # today date
                elif check.days == 0:
                    color = "#FFF55C"
                add_root_node(model, "", found)
                add_child_node(model, 0, str_cat)
                add_child_node(model, 1, diffusion_date, color)
                if len(filename)>0:
                    rar_extension = re.search("r(\d*)$", filename)
                    if rar_extension:
                        add_child_node(model, 2, "RAR FILES " + filename)
                    else:
                        add_child_node(model, 2, filename)#color)

    model.sort(0)
    view.setModel(model)


################################################################################
################################################################################
def get_squared_pics_from_tvshow( in_show_name ):
    """ Get squared thumbnails for tv show name """
    if QtCore.QFile.exists(".thumbs/" + in_show_name):
        image = QtGui.QImage()
        image.load(in_show_name)
        return image
    else:
        url  = "http://mediaicons.org/Services/Find.ashx?term="
        url += str(in_show_name) + "&format=1"
        request = urllib.request.Request(url)
        webpage = urllib.request.urlopen(request).read()

        xml_reader = QtCore.QXmlStreamReader(webpage)

        while not xml_reader.atEnd():
            xml_reader.readNext()
            if xml_reader.isStartElement():
                if xml_reader.name() == "icon":
                    icon_url = xml_reader.attributes().value("url").toString()
                    icon_url.replace("mediaicons.org/GetIcon",
                                    "mediaicons.org/Services/GetIcon", 1)
                    print(icon_url)
                    pic = urllib.request.urlopen(str(icon_url)).read()
                    imag = QtGui.QImage()
                    imag.loadFromData(pic)
                    print("success ?")
                    print(imag.save(".thumbs/" + in_show_name, "PNG"))
                    return imag
        if xml_reader.atEnd():
            return ""


################################################################################
################################################################################
def get_squared_pics_list( in_show_name ):
    """ Get the squared thumbnails list for tv show name """
    url  = "http://mediaicons.org/Services/Find.ashx?term="
    url += str(in_show_name) + "&format=1"
    request = urllib.request.Request(url)
    webpage = urllib.request.urlopen(request).read()

    xml_reader = QtCore.QXmlStreamReader(webpage)
    icons_urls = []
    while not xml_reader.atEnd():
        xml_reader.readNext()
        if xml_reader.isStartElement():
            if xml_reader.name() == "icon":
                icon_url = xml_reader.attributes().value("url").toString()
                icon_url.replace("mediaicons.org/GetIcon",
                                "mediaicons.org/Services/GetIcon", 1)
                #print icon_url
                icons_urls.append(icon_url)
                #pic = urllib2.urlopen(str(icon_url)).read()
                #imag = QtGui.QImage()
                #imag.loadFromData(pic)
                #print "success ?"
                #print imag.save(".thumbs/" + in_show_name, "PNG")
                #return imag

    return icons_urls


################################################################################
################################################################################
# XML TOOLS
def read_dirs_from_xml():
    """ Read xml file for directories """
    xml_file = QtCore.QFile(XML_FILENAME)
    xml_file.open(QtCore.QIODevice.ReadOnly)
    xml_reader = QtCore.QXmlStreamReader(xml_file)
    while not xml_reader.atEnd():
        xml_reader.readNext()
        if xml_reader.isStartElement():
            if xml_reader.name() == "dir":
                DIRECTORIES_TO_PARSE.append(xml_reader.readElementText())

def write_dirs_to_xml():
    """ Write a selected directory to xml file """
    xml_file = QtCore.QFile(XML_FILENAME)
    xml_file.open(QtCore.QIODevice.WriteOnly)
    xml_writer = QtCore.QXmlStreamWriter(xml_file)
    xml_writer.setAutoFormatting(True)
    xml_writer.writeStartDocument()
    ################################################
    xml_writer.writeStartElement("directories")
    for directory_path in DIRECTORIES_TO_PARSE:
        xml_writer.writeTextElement("dir", directory_path)
    xml_writer.writeEndElement()
    ################################################
    xml_writer.writeEndDocument()
################################################################################
################################################################################


################################################################################
################################################################################
class PicturesSelector(QtGui.QDialog):
    """ Thumbnails selection popup """
    def __init__(self, parent, in_show_name):
        QtGui.QDialog.__init__(self, parent)
        self.setWindowTitle(in_show_name + " thumb Selector")
        #self.setLayout(QGridLayout(self))
        self.setLayout(QtGui.QVBoxLayout(self))
        self.resize(250, 50)

        icons_urls = get_squared_pics_list(in_show_name)

        if len(icons_urls) > 0:
            for url in icons_urls :
                print(url)
                pic = urllib.request.urlopen(str(url)).read()
                imag = QtGui.QImage()
                imag.loadFromData(pic)
                pixm = QtGui.QPixmap.fromImage(
                            imag.scaled(128, 128, QtCore.Qt.KeepAspectRatio)
                        )
                lbl = QtGui.QLabel()
                lbl.setPixmap(pixm)
                self.layout().addWidget(lbl)
        else :
            self.layout().addWidget(QtGui.QLabel("No pictures found"))

        self.show()
    #def leaveEvent(self, event):
        #""" When the mouse leave this widget, destroy it. """
        #self.destroy()


################################################################################
################################################################################
class KEpShow(QtGui.QWidget):
    """ Main class """
    def on_show_activated(self, in_index):
        """ Load found tv show episodes infos """
        index_showname = self.ui.found_tv_shows.model().index(in_index.row(), 1)
        current_disp   = self.ui.found_tv_shows.model().data(index_showname)
        ix_dir         = self.ui.found_tv_shows.model().index(in_index.row(), 2)
        current_dir    = self.ui.found_tv_shows.model().data(ix_dir)
        parse_page(self.ui.tableView, current_disp, current_dir)
        #image = get_squared_pics_from_tvshow(current_disp)
        #if image:
            #self.ui.found_tv_shows.model().setData(self.ui.found_tv_shows.model().index(in_index.row(), 3), QtGui.QPixmap.fromImage(image.scaled(64, 64, QtCore.Qt.KeepAspectRatio)), QtCore.Qt.DecorationRole)

        #print(self.ui.found_tv_shows.model().data(index_showname))

    def icon_selection(self, in_index):
        """ Handler for the thumbnails selection popup """
        if in_index.column() == 3 :
            index_showname = self.ui.found_tv_shows.model().index(in_index.row(), 1)
            #current_disp = self.ui.found_tv_shows.model().data(index_showname).toString()
            print("try to open popup" + index_showname)
            #select = PicturesSelector(self, current_disp)


    def update_global(self, rank):
        """ Load all tv show episodes infos """
        index_showname = self.ui.all_tv_shows.model().index(rank, 1)
        current_disp = self.ui.all_tv_shows.model().data(index_showname).toString()
        parse_page(self.ui.tableView, current_disp, "")
        #print self.ui.found_tv_shows.model().data(index_showname).toString()

    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)

        # Set up the user interface from Designer.
        self.ui = Ui_MainQWidget()
        self.ui.setupUi(self)

        self.ui.tableView.setAlternatingRowColors(True)

        self.connect(self.ui.found_tv_shows,
                     QtCore.SIGNAL("activated(QModelIndex)"),
                     self.on_show_activated)

        #self.connect(self.ui.found_tv_shows, QtCore.SIGNAL("entered(QModelIndex)"), self.icon_selection)
        #self.connect(self.ui.all_tv_shows, QtCore.SIGNAL("currentIndexChanged(int)"), self.update_global)

    def directory_selector(self):
        """ Opens a popup to choose a directory containing tv shows """
        dir_full_path = QtGui.QFileDialog.getExistingDirectory(self,
                                    self.tr("Choose a directory"),
                                    QtCore.QDir.currentPath(),
                                    QtGui.QFileDialog.DontResolveSymlinks |
                                    QtGui.QFileDialog.ShowDirsOnly
                            )
        if not dir_full_path.isEmpty():
            DIRECTORIES_TO_PARSE.append(dir_full_path)
            self.write_dirs_to_xml()


################################################################################
################################################################################
def add_root_node(model, name, color):
    """ Add a parent element """
    model.insertRow(0)
    if color == 0:
        color_code = "#FF6767" #red
    elif color == 1:
        color_code = "#86FF68" #green
    elif color == 2:
        color_code = "#EEB95C"
    elif color == 3:
        color_code = "#8BB2FF" #blue
    else:
        color_code = "#FFFFFF"
    model.setData(model.index(0, 0), QtGui.QColor("#000000"), QtCore.Qt.ForegroundRole)
    model.setData(model.index(0, 1), QtGui.QColor("#000000"), QtCore.Qt.ForegroundRole)
    model.setData(model.index(0, 2), QtGui.QColor("#000000"), QtCore.Qt.ForegroundRole)
    model.setData(model.index(0, 3), QtGui.QColor("#000000"), QtCore.Qt.ForegroundRole)
    model.setData(model.index(0, 0), QtGui.QColor(color_code), QtCore.Qt.BackgroundColorRole)
    model.setData(model.index(0, 1), QtGui.QColor(color_code), QtCore.Qt.BackgroundColorRole)
    model.setData(model.index(0, 2), QtGui.QColor(color_code), QtCore.Qt.BackgroundColorRole)
    model.setData(model.index(0, 3), QtGui.QColor(color_code), QtCore.Qt.BackgroundColorRole)
    #model.setData(model.index(0, 0), QtCore.QVariant(name))


################################################################################
################################################################################
def add_child_node(model, in_index, name, in_color_code = ""):
    """ Add a child element at given level with color """
    if len(in_color_code) > 0:
        model.setData(model.index(0, in_index), QtGui.QColor("#000000"),     QtCore.Qt.ForegroundRole)
        model.setData(model.index(0, in_index), QtGui.QColor(in_color_code), QtCore.Qt.BackgroundColorRole)
    model.setData(model.index(0, in_index), name)


################################################################################
################################################################################
def parse_lastshows_file():
    """ Read last shows file for already seen episodes """
    path = "/home/belkiss/download/Series"
    full_path = os.path.join(path, "lastShows")
    file_data = open(full_path, 'r')
    stop = False
    for line in file_data:
        tmp_show_name  = line[0:line.find(' ')]
        if tmp_show_name.find('###############') != -1:
            stop = True
        if stop == False:
            split_line = re.search(".*[s](\d*)[e](\d*).*(\d*)[/](\d*)[/](\d*)",
                                   line)
            if split_line:
                SHOW_SEEN_TO[tmp_show_name.lower()] = split_line.group(1) + "e" + split_line.group(2)
    file_data.close()


################################################################################
################################################################################
if __name__ == "__main__":
    APP = QtGui.QApplication(sys.argv)
    parse_lastshows_file()
    KEPSHOW = KEpShow()
    read_dirs_from_xml()
    #KEPSHOW.directory_selector()
    #KEPSHOW.read_dirs_from_xml()

    ALL_SHOW_FILE_DATA = open("current.shtml", 'r', -1, 'ISO-8859-1')
    FOUND_DATA_BEGINNING = 0
    DIR_NAMES = {}
    SHOWNAME_LOWER_TO_UPPER = {}

    ALL_SHOWS_MODEL = QtGui.QStandardItemModel(0, 2)

    for element in ALL_SHOW_FILE_DATA:
        if FOUND_DATA_BEGINNING == 0:
            if element[0:18] == '<strong><a name="A':
                FOUND_DATA_BEGINNING += 1
        else:
            if element[0:16] == '<li><b><a href="':
                found_rank = element.find('">', 16)
                full_url   = element[16:found_rank]
                dir_name   = full_url[full_url.find('.com/')+5:-1]
                show_name  = element[found_rank+2:element.find('</a>',
                                     found_rank+2)]
                DIR_NAMES[dir_name] = show_name
                SHOWNAME_LOWER_TO_UPPER[dir_name.lower()] = dir_name
                add_root_node(ALL_SHOWS_MODEL, show_name, 4)
                add_child_node(ALL_SHOWS_MODEL, 0, show_name)
                add_child_node(ALL_SHOWS_MODEL, 1, dir_name)
                #KEPSHOW.ui.all_tv_shows.addItem(show_name, dir_name)
                #print show_name+ ":"+ dir_name
    ALL_SHOWS_MODEL.sort(0)
    KEPSHOW.ui.all_tv_shows.setModel(ALL_SHOWS_MODEL)


    TMP_DIRS = []
    FOUND_SHOWS_MODEL = QtGui.QStandardItemModel(0, 4)
    for directory in DIRECTORIES_TO_PARSE:
        directory = str(directory)
        print("parsing " + directory)
        for element in os.listdir(directory):
            if os.path.isdir(os.path.join(directory, element)):
                # AIROUT ONAIR TOWATCH
                for child_element in os.listdir(os.path.join(directory, element)):
                    if os.path.isdir(os.path.join(os.path.join(directory, element), child_element)):
                        element_color = 3
                        if element == "OnAir":
                            element_color = 3
                        elif element == "ToWatch":
                            element_color = 1
                        else:
                            element_color = 0
                        if child_element.lower() in SHOWNAME_LOWER_TO_UPPER:
                            if SHOWNAME_LOWER_TO_UPPER[child_element.lower()] != child_element :
                                print("    rename this " + child_element + " to this : " + SHOWNAME_LOWER_TO_UPPER[child_element.lower()])
                            #print("child_element.lower() " + child_element.lower())
                            #print("SHOWNAME_LOWER_TO_UPPER[child_element.lower()] " + SHOWNAME_LOWER_TO_UPPER[child_element.lower()])
                            #print("DIR_NAMES[SHOWNAME_LOWER_TO_UPPER[child_element.lower()]] " + DIR_NAMES[SHOWNAME_LOWER_TO_UPPER[child_element.lower()]])
                            add_root_node(FOUND_SHOWS_MODEL, DIR_NAMES[SHOWNAME_LOWER_TO_UPPER[child_element.lower()]], element_color)
                            add_child_node(FOUND_SHOWS_MODEL, 0, DIR_NAMES[SHOWNAME_LOWER_TO_UPPER[child_element.lower()]])
                            add_child_node(FOUND_SHOWS_MODEL, 1, SHOWNAME_LOWER_TO_UPPER[child_element.lower()])
                            if child_element in TMP_DIRS:
                                print("    " + child_element + " already inside")
                                # CHANGE THE BEHAVIOUR : when already inside, complete the data
                            else:
                                TMP_DIRS.append(child_element)
                            add_child_node(FOUND_SHOWS_MODEL, 2, os.path.join(os.path.join(directory, element), child_element))
                        else:
                            print("    ####### not found : " + child_element)
                            add_root_node(FOUND_SHOWS_MODEL, child_element, element_color)
                            add_child_node(FOUND_SHOWS_MODEL, 0, child_element)
                            add_child_node(FOUND_SHOWS_MODEL, 1, child_element)
                            if child_element in TMP_DIRS:
                                print("    " + child_element + " already inside")
                                # CHANGE THE BEHAVIOUR : when already inside, complete the data
                            else:
                                TMP_DIRS.append(child_element)
                            add_child_node(FOUND_SHOWS_MODEL, 2, os.path.join(os.path.join(directory, element), child_element))
    FOUND_SHOWS_MODEL.sort(0)

    KEPSHOW.ui.found_tv_shows.setModel(FOUND_SHOWS_MODEL)

    ROWS_NB = FOUND_SHOWS_MODEL.rowCount()
    #print ROWS_NB
    #for row in xrange(ROWS_NB):
        #KEPSHOW.ui.found_tv_shows.setRowHeight(row, 64)
    KEPSHOW.ui.found_tv_shows.resizeColumnsToContents()
    KEPSHOW.ui.found_tv_shows.hideColumn(1)
    #KEPSHOW.ui.found_tv_shows.hideColumn(2)
    KEPSHOW.show()
    sys.exit(APP.exec_())
