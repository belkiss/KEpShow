#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" tool to help keeping updated with diffusion date of TV Shows """
# pyuic4 -o ui_KEpShow.py KEpShow.ui
# File : KEpShow.py
import datetime, locale, os, re, csv, signal, sys, html, time, urllib.request, urllib.error, urllib.parse, warnings
from PyQt5 import QtCore, QtGui, QtWidgets

from ui_KEpShow import Ui_MainQWidget

# display deprecation warnings
warnings.simplefilter('default')

XML_FILENAME = "KEpShow_dirs.xml"
DIRECTORIES_TO_PARSE = []

TODAY = datetime.datetime.now().strftime("%Y%m%d")

SHOW_SEEN_TO = {}

SKIPPED_EXTENSIONS = {"zip", "srt", "ass", "nfo"}

################################################################################
################################################################################
def clean_name(filename):
    cleaned_name = filename.replace("720p", "", 1).lower()
    cleaned_name = cleaned_name.replace("1080p", "", 1)
    cleaned_name = cleaned_name.replace("1080", "", 1)
    cleaned_name = cleaned_name.replace("x264", "", 1)
    cleaned_name = cleaned_name.replace("h264", "", 1)
    cleaned_name = cleaned_name.replace("h.264", "", 1)
    cleaned_name = cleaned_name.replace("hdtv", "", 1)
    cleaned_name = cleaned_name.replace("dd5.1", "", 1)
    cleaned_name = cleaned_name.replace("french", "", 1)
    cleaned_name = re.sub("[\._\(]20\d{2}[\._\)]", "", cleaned_name, 1)

    return cleaned_name

################################################################################
################################################################################
def parse_epguides_page(view, page, dirpath):
    """ Parse epguides webpage """
    locale.setlocale(locale.LC_ALL, 'C')
    url  = "http://epguides.com/"
    url += str(page)
    request = urllib.request.Request(url)
    request.add_header('Cookie', 'ListDisplay=tvmaze.com')
    webpage = urllib.request.urlopen(request).readlines()
    found_first = 0
    model = QtGui.QStandardItemModel(0, 3)

    found = 0
    dir_content = []
    originalcase_dir_content = []
    for files in os.listdir(dirpath):
        if os.path.isfile(dirpath + "/" + files):
            clean = clean_name(files)
            if (not clean.endswith("zip")) & (not clean.endswith("srt")) & (not clean.endswith("ass")) & (not clean.endswith("nfo")):
                dir_content.append(clean)
                originalcase_dir_content.append(files)
        else:
            for child_files in os.listdir(dirpath + "/" + files):
                if os.path.isfile(
                    os.path.join(str(dirpath + "/" + files), child_files)
                ):
                    clean = clean_name(child_files)
                    if (not clean.endswith("zip")) & (not clean.endswith("srt")) & (not clean.endswith("ass")) & (not clean.endswith("nfo")):
                        dir_content.append(clean)
                        originalcase_dir_content.append(child_files)

    for line in webpage:
        line = line.decode("ISO-8859-1") # 'UTF-8'
        if found_first == 0:
            if line.lstrip().startswith('<div id="eplist"'):
                found_first += 1
        else:
            split_line = re.search(
                "^\d*\.\s*(\d*)[-](\d*).{15}\s*(\d*)[/ ]([a-zA-Z]*)[/ ](\d*)",line)
            if split_line:
                try:
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
                    for index,mkv in enumerate(dir_content):
                        if mkv.find(str_cat) != -1:
                            filename = originalcase_dir_content[index]
                            found = 1
                        elif mkv.find(
                                str(season_nb) + str("%02d" % episode_nb)) != -1:
                            filename = originalcase_dir_content[index]
                            found = 1
                        elif mkv.find(
                                str(season_nb) + "x" + str("%02d" % episode_nb)
                                ) != -1:
                            filename = originalcase_dir_content[index]
                            found = 1

                    diffusion_date = datetime.datetime(*diffusion_date[0:7]).strftime("%d/%m/%Y")

                    check = datetime.datetime.strptime(diffusion_date,"%d/%m/%Y") - datetime.datetime.strptime(TODAY,"%Y%m%d")

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
                except:
                    print("Something went wrong in " + line);
    model.sort(0)
    view.setModel(model)

################################################################################
################################################################################
def parse_tvmaze_page(view, page, dirpath):
    """ Parse epguides webpage """
    locale.setlocale(locale.LC_ALL, 'C')

    found_first = 0
    model = QtGui.QStandardItemModel(0, 3)

    found = 0
    dir_content = []
    originalcase_dir_content = []
    ignored_extensions = [".zip", ".srt", ".ass", ".nfo"]
    valid_extensions = [".mkv"]
    for files in os.listdir(dirpath):
        if os.path.isfile(dirpath + "/" + files):
            clean = clean_name(files)
            filename, extension = os.path.splitext(clean)
            if (extension in valid_extensions or not extension in ignored_extensions):
                dir_content.append(clean)
                originalcase_dir_content.append(files)
        else:
            for child_files in os.listdir(dirpath + "/" + files):
                if os.path.isfile(os.path.join(str(dirpath + "/" + files), child_files)):
                    clean = clean_name(child_files)
                    filename, extension = os.path.splitext(clean)
                    if (extension in valid_extensions or not extension in ignored_extensions):
                        dir_content.append(clean)
                        originalcase_dir_content.append(child_files)

    lowpage = str(page).lower()

    last_seen_season = 0
    last_seen_episode = 0
    if lowpage in SHOW_SEEN_TO:
        split_ep = re.search("(\d*)[e](\d*)", SHOW_SEEN_TO[str(lowpage)])
        if split_ep:
            last_seen_season = int(split_ep.group(1))
            last_seen_episode = int(split_ep.group(2))

    season_nb = "?"
    episode_nb = "?"

    if page in TVMAZE_ID:
        url  = "http://epguides.com/common/exportToCSVmaze.asp?maze="
        url += str(TVMAZE_ID[page])
        request = urllib.request.Request(url)
        webpage = urllib.request.urlopen(request).readlines()

        for line in webpage:
            line = line.decode("UTF-8")
            line = html.unescape(line)
            if found_first == 0:
                if line.lstrip().startswith('number,season,episode,airdate,title,tvmaze link'):
                    found_first += 1
            elif line.lstrip().startswith('</pre>'):
                break
            else:
                try:
                    # page downloaded from epguides
                    # current format:
                    # number,season,episode,airdate,title,tvmaze link
                    expected_nb_of_fields = 6
                    csv_reader = csv.reader([line], delimiter=',')
                    for csv_line in csv_reader:
                        nb_fields = len(csv_line)
                        if nb_fields != expected_nb_of_fields:
                            if nb_fields == 0:
                                continue
                            if nb_fields > 0:
                                print("Warning! line {} we just received has {} fields instead of expected {}".format(csv_line, nb_fields, expected_nb_of_fields))

                        season_nb = int(csv_line[1])
                        episode_nb = int(csv_line[2])
                        diffusion_date_string = csv_line[3]
                        episode_title = csv_line[4]

                        str_cat = "s" + "%02d" % season_nb + "e" + "%02d" % episode_nb

                        diffusion_date = time.strptime(diffusion_date_string, "%d %b %y")

                        found = 0
                        filename = ""

                        if season_nb < int(last_seen_season):
                            found = 2
                        elif season_nb == int(last_seen_season):
                            if episode_nb <= int(last_seen_episode):
                                found = 2

                        # replace 720p by a space to avoid
                        # detecting it as an episode number
                        for index,mkv in enumerate(dir_content):
                            if mkv.find(str_cat) != -1:
                                filename = originalcase_dir_content[index]
                                found = 1
                            elif mkv.find(
                                    str(season_nb) + str("%02d" % episode_nb)) != -1:
                                filename = originalcase_dir_content[index]
                                found = 1
                            elif mkv.find(
                                    str(season_nb) + "x" + str("%02d" % episode_nb)
                                    ) != -1:
                                filename = originalcase_dir_content[index]
                                found = 1

                        diffusion_date = datetime.datetime(*diffusion_date[0:7]).strftime("%d/%m/%Y")

                        check = datetime.datetime.strptime(diffusion_date,"%d/%m/%Y") - datetime.datetime.strptime(TODAY,"%Y%m%d")

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
                        else:
                            add_child_node(model, 2, episode_title)
                except:
                    print("Something went wrong in " + line);
    else:
        # replace 720p by a space to avoid
        # detecting it as an episode number
        for index,clean_filename in enumerate(dir_content):
            season_episode_regex = re.search("[sS]?(\d{1,2})[eE]?(\d{1,2})", clean_filename);
            if season_episode_regex:
                season_nb = int(season_episode_regex.group(1))
                episode_nb = int(season_episode_regex.group(2))

            color = "#86FF68"

            found = 1
            if season_nb < int(last_seen_season):
                found = 2
            elif season_nb == int(last_seen_season):
                if episode_nb <= int(last_seen_episode):
                    found = 2

            filename = originalcase_dir_content[index]

            str_cat = "s" + "%02d" % season_nb + "e" + "%02d" % episode_nb

            add_root_node(model, "", found)
            add_child_node(model, 0, str_cat)
            add_child_node(model, 1, "", color)
            add_child_node(model, 2, filename)

    model.sort(0)
    view.setModel(model)


################################################################################
################################################################################
def get_squared_pics_from_tvshow( in_show_name ):
    """ Get squared thumbnails for tv show name """
    if QtCore.QFile.exists(".thumbs/" + in_show_name):
        image = QtWidgets.QImage()
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
                    imag = QtWidgets.QImage()
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
                #imag = QtWidgets.QImage()
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
class PicturesSelector(QtWidgets.QDialog):
    """ Thumbnails selection popup """
    def __init__(self, parent, in_show_name):
        QtWidgets.QDialog.__init__(self, parent)
        self.setWindowTitle(in_show_name + " thumb Selector")
        #self.setLayout(QGridLayout(self))
        self.setLayout(QtWidgets.QVBoxLayout(self))
        self.resize(250, 50)

        icons_urls = get_squared_pics_list(in_show_name)

        if len(icons_urls) > 0:
            for url in icons_urls :
                print(url)
                pic = urllib.request.urlopen(str(url)).read()
                imag = QtWidgets.QImage()
                imag.loadFromData(pic)
                pixm = QtWidgets.QPixmap.fromImage(
                            imag.scaled(128, 128, QtCore.Qt.KeepAspectRatio)
                        )
                lbl = QtWidgets.QLabel()
                lbl.setPixmap(pixm)
                self.layout().addWidget(lbl)
        else :
            self.layout().addWidget(QtWidgets.QLabel("No pictures found"))

        self.show()
    #def leaveEvent(self, event):
        #""" When the mouse leave this widget, destroy it. """
        #self.destroy()


################################################################################
################################################################################
class KEpShow(QtWidgets.QWidget):
    """ Main class """
    def on_show_activated(self, in_index):
        """ Load found tv show episodes infos """
        index_showname = self.ui.found_tv_shows.model().index(in_index.row(), 1)
        current_disp   = self.ui.found_tv_shows.model().data(index_showname)
        ix_dir         = self.ui.found_tv_shows.model().index(in_index.row(), 2)
        current_dir    = self.ui.found_tv_shows.model().data(ix_dir)
        parse_tvmaze_page(self.ui.tableView, current_disp, current_dir)
        #image = get_squared_pics_from_tvshow(current_disp)
        #if image:
            #self.ui.found_tv_shows.model().setData(self.ui.found_tv_shows.model().index(in_index.row(), 3), QtWidgets.QPixmap.fromImage(image.scaled(64, 64, QtCore.Qt.KeepAspectRatio)), QtCore.Qt.DecorationRole)

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
        parse_epguides_page(self.ui.tableView, current_disp, "")
        #print self.ui.found_tv_shows.model().data(index_showname).toString()

    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)

        # Set up the user interface from Designer.
        self.ui = Ui_MainQWidget()
        self.ui.setupUi(self)

        self.ui.tableView.setAlternatingRowColors(True)

        self.ui.found_tv_shows.activated[QtCore.QModelIndex].connect(self.on_show_activated)

        #self.connect(self.ui.found_tv_shows, QtCore.SIGNAL("entered(QModelIndex)"), self.icon_selection)
        #self.connect(self.ui.all_tv_shows, QtCore.SIGNAL("currentIndexChanged(int)"), self.update_global)

    def directory_selector(self):
        """ Opens a popup to choose a directory containing tv shows """
        dir_full_path = QtWidgets.QFileDialog.getExistingDirectory(self,
                                    self.tr("Choose a directory"),
                                    QtCore.QDir.currentPath(),
                                    QtWidgets.QFileDialog.DontResolveSymlinks |
                                    QtWidgets.QFileDialog.ShowDirsOnly
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
def parse_current_shtml():
    """ Parse the current.shtml file that contains an (old) offline html file of shows """
    path = "current.shtml"
    with open(path, 'r', -1, 'ISO-8859-1') as ALL_SHOW_FILE_DATA:
        FOUND_DATA_BEGINNING = 0
        for element in ALL_SHOW_FILE_DATA:
            if FOUND_DATA_BEGINNING == 0:
                if element[0:18] == '<strong><a name="A':
                    FOUND_DATA_BEGINNING += 1
            else:
                if element[0:16] == '<li><b><a href="':
                    print(element)
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

################################################################################
################################################################################
def parse_all_shows(filename):
    """ Parse the current.shtml file that contains an offline csv file of shows """
    # downloaded from epguides
    # current format:
    # title,directory,tvrage,TVmaze,start date,end date,number of episodes,run time,network,country,onhiatus,onhiatusdesc
    expected_nb_of_fields = 12
    with open(filename, encoding='ISO-8859-1') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        for line in csv_reader:
            nb_fields = len(line)
            if nb_fields != expected_nb_of_fields:
                if nb_fields > 0:
                    print("Error! line {} in file {} has {} fields instead of expected {}".format(csv_reader.line_num, filename, nb_fields, expected_nb_of_fields))
                continue
            show_name = line[0]
            dir_name = line[1]
            tvmaze_id = line[3]
            TVMAZE_ID[dir_name] = tvmaze_id
            DIR_NAMES[dir_name] = show_name
            SHOWNAME_LOWER_TO_UPPER[dir_name.lower()] = dir_name
            #add_root_node(ALL_SHOWS_MODEL, show_name, 4)
            #add_child_node(ALL_SHOWS_MODEL, 0, show_name)
            #add_child_node(ALL_SHOWS_MODEL, 1, dir_name)

################################################################################
################################################################################
if __name__ == "__main__":
    APP = QtWidgets.QApplication(sys.argv)
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    parse_lastshows_file()
    KEPSHOW = KEpShow()
    read_dirs_from_xml()
    #KEPSHOW.directory_selector()

    allshows_filename = "allshows_" + TODAY + ".txt"
    if not os.path.exists(allshows_filename):
        url  = "http://epguides.com/common/allshows.txt"
        print("Downloading new version of allshows.txt from epguides")
        urllib.request.urlretrieve(url, allshows_filename)
        if not os.path.exists(allshows_filename):
            print("Warning! Download failed, use the offline version")
            allshows_filename = "allshows.txt"

    DIR_NAMES = {}
    TVMAZE_ID = {}
    SHOWNAME_LOWER_TO_UPPER = {}

    ALL_SHOWS_MODEL = QtGui.QStandardItemModel(0, 2)
    #parse_current_shtml()
    parse_all_shows(allshows_filename)
    #ALL_SHOWS_MODEL.sort(0)
    #KEPSHOW.ui.all_tv_shows.setModel(ALL_SHOWS_MODEL)

    TMP_DIRS = []
    FOUND_SHOWS_MODEL = QtGui.QStandardItemModel(0, 4)
    for directory in DIRECTORIES_TO_PARSE:
        directory = str(directory)
        print("parsing " + directory)
        for element in os.listdir(directory):
            element_full_path = os.path.join(directory, element)
            if os.path.isdir(element_full_path):
                # AIROUT ONAIR TOWATCH
                for child_element in os.listdir(element_full_path):
                    child_full_path = os.path.join(element_full_path, child_element)
                    if os.path.isdir(child_full_path):
                        element_color = 3
                        if element == "OnAir":
                            element_color = 3
                        elif element == "ToWatch":
                            element_color = 1
                        else:
                            element_color = 0
                        if child_element.lower() in SHOWNAME_LOWER_TO_UPPER:
                            if SHOWNAME_LOWER_TO_UPPER[child_element.lower()] != child_element :
                                print("    rename this " + child_full_path + " to this : " + os.path.join(element_full_path, SHOWNAME_LOWER_TO_UPPER[child_element.lower()]))
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
                            add_child_node(FOUND_SHOWS_MODEL, 2, child_full_path)
                        else:
                            print("    ####### not found : " + child_full_path)
                            add_root_node(FOUND_SHOWS_MODEL, child_element, element_color)
                            add_child_node(FOUND_SHOWS_MODEL, 0, child_element)
                            add_child_node(FOUND_SHOWS_MODEL, 1, child_element)
                            if child_element in TMP_DIRS:
                                print("    " + child_element + " already inside")
                                # CHANGE THE BEHAVIOUR : when already inside, complete the data
                            else:
                                TMP_DIRS.append(child_element)
                            add_child_node(FOUND_SHOWS_MODEL, 2, child_full_path)
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
