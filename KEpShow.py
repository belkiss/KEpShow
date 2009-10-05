# -*- coding: utf-8 -*-
# File : KEpShow.py
import datetime,os,re,string,sys,time,urllib2
from PyQt4 import QtCore, QtGui

from ui_KEpShow import Ui_MainQWidget

def parsePage(view, page, dirpath):
	url  = "http://epguides.com/"
	url += str(page)
	request = urllib2.Request(url)
	request.add_header('Cookie', 'ListDisplay=tvrage.com')
	webpage = urllib2.urlopen(request).readlines()
	found_first = 0
	model = QtGui.QStandardItemModel(0, 2)

	found = 0
	dir_content = []
	for files in os.listdir(dirpath):
		if os.path.isfile(dirpath + "/" + files):
			dir_content.append(string.lower(files))
		else:
			for child_files in os.listdir(dirpath + "/" + files):
				if os.path.isfile(os.path.join(str(dirpath + "/" + files), child_files)):
					dir_content.append(string.lower(child_files))
	
	for line in webpage:
		if found_first == 0:
			if line[0:17] == '<div id="eplist">':
				found_first+=1
		else:
			split_line = re.search("\d*\s*(\d*)[-](\d*).{15}\s*(\d*)[/]([a-zA-Z]*)[/](\d*)",line)
			if split_line:
				diffusion_date = time.strptime("%02d" % int(split_line.group(3)) + "/" + split_line.group(4) + "/" + split_line.group(5),"%d/%b/%y")
				season_nb  = "%02d" % int(split_line.group(1))
				episode_nb = "%02d" % int(split_line.group(2))
				str_cat    = "s" + season_nb +"e"+episode_nb
				found = False
				for mkv in dir_content:
					if string.find(mkv, str_cat) != -1:
						dir_content.remove(mkv)
						found = True
						#print mkv + " " + str_cat + " " + str(string.find(mkv, str_cat))
				addRoot(model, found)
				addLine(model, 0, str_cat)
				addLine(model, 1, datetime.datetime(*diffusion_date[0:7]).strftime("%d/%m/%Y"))

	model.sort(0)
	view.setModel(model)
	

class KEpShow(QtGui.QWidget):
	def updateActions(self, rank):
		ix = self.ui.found_tv_shows.model().index(rank, 1)
		currentDispl = self.ui.found_tv_shows.model().data(ix).toString()
		ix_dir = self.ui.found_tv_shows.model().index(rank, 2)
		currentDir = self.ui.found_tv_shows.model().data(ix_dir).toString()
		parsePage(kepshow.ui.tableView, currentDispl, currentDir)
		#print self.ui.found_tv_shows.model().data(ix).toString()

	def updateAll(self, rank):
		ix = self.ui.all_tv_shows.model().index(rank, 1)
		currentDispl = self.ui.all_tv_shows.model().data(ix).toString()
		parsePage(kepshow.ui.tableView, currentDispl)
		#print self.ui.found_tv_shows.model().data(ix).toString()

	def __init__(self, parent=None):
		QtGui.QWidget.__init__(self,parent)

		# Set up the user interface from Designer.
		self.ui = Ui_MainQWidget()
		self.ui.setupUi(self)

		self.ui.tableView.setAlternatingRowColors(True)

		self.connect(self.ui.found_tv_shows, QtCore.SIGNAL("currentIndexChanged(int)"), self.updateActions)
		#self.connect(self.ui.all_tv_shows, QtCore.SIGNAL("currentIndexChanged(int)"), self.updateAll)

def addRoot(model, name):
	model.insertRow(0)
	if name == False:
		colorCode = "#FF6767"
	else:
		colorCode = "#8BB2FF"
	model.setData(model.index(0, 0), QtGui.QColor(colorCode), QtCore.Qt.BackgroundColorRole)
	model.setData(model.index(0, 1), QtGui.QColor(colorCode), QtCore.Qt.BackgroundColorRole)
	model.setData(model.index(0, 2), QtGui.QColor(colorCode), QtCore.Qt.BackgroundColorRole)
	#model.setData(model.index(0, 0), QtCore.QVariant(name))

def addLine(model, ix, name):
	model.setData(model.index(0, ix), QtCore.QVariant(name))


#if __name__ == "__main__":

app = QtGui.QApplication(sys.argv)
kepshow = KEpShow()

all_list = open("/home/belkiss/Desktop/current.shtml", 'r')
found_first = 0
dirNames = {}
lowerUpper = {}

model_all_shows = QtGui.QStandardItemModel(0, 2)

for line in all_list:
	if found_first == 0:
		if line[0:18] == '<strong><a name="A':
			found_first+=1
	else:
		if line[0:16] == '<li><b><a href="':
			found_rank = string.find(line, '">', 16)
			url        = line[16:found_rank]
			dir_name   = url[string.find(url,'.com/')+5:-1]
			show_name  = line[found_rank+2:string.find(line,'</a>',found_rank+2)]
			dirNames[dir_name] = show_name
			lowerUpper[string.lower(dir_name)] = dir_name
			addRoot(model_all_shows, show_name)
			addLine(model_all_shows, 0, show_name)
			addLine(model_all_shows, 1, dir_name)
			#kepshow.ui.all_tv_shows.addItem(show_name, dir_name)
			#print show_name+ ":"+ dir_name
model_all_shows.sort(0)
kepshow.ui.all_tv_shows.setModel(model_all_shows)


diir = []
model_found_shows = QtGui.QStandardItemModel(0, 3)
for element in os.listdir("/home/belkiss/download/Series"):
	if os.path.isdir(os.path.join("/home/belkiss/download/Series", element)):
		# AIROUT ONAIR TOWATCH
		for child_element in os.listdir(os.path.join("/home/belkiss/download/Series", element)):
			if os.path.isdir(os.path.join("/home/belkiss/download/Series/"+element, child_element)):
				#print child_element
				if string.lower(child_element) in lowerUpper:
					if lowerUpper[string.lower(child_element)] != child_element :
						print "rename this " + child_element + " to this : " + lowerUpper[string.lower(child_element)]
					addRoot(model_found_shows, dirNames[lowerUpper[string.lower(child_element)]])
					addLine(model_found_shows, 0, dirNames[lowerUpper[string.lower(child_element)]])
					addLine(model_found_shows, 1, lowerUpper[string.lower(child_element)])
					if child_element in diir:
						print child_element + "already inside"
					else:
						diir.append(child_element)
					addLine(model_found_shows, 2, os.path.join("/home/belkiss/download/Series/"+element, child_element))
				else:
					print "#######not found" + child_element
model_found_shows.sort(0)
kepshow.ui.found_tv_shows.setModel(model_found_shows)

kepshow.show()
sys.exit(app.exec_())
