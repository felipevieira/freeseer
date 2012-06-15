#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
freeseer - vga/presentation capture software

Copyright (C) 2011  Free and Open Source Software Learning Centre
http://fosslc.org

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

For support, questions, suggestions or any other inquiries, visit:
http://wiki.github.com/Freeseer/freeseer/

@author: Jordan Klassen
'''
# Form implementation generated from reading ui file 'VideoUploader.ui'
#
# Created: Sat Oct 15 09:20:29 2011
#      by: pyside-uic 0.2.13 running on PySide 1.0.7
#

#from PySide import QtCore, QtGui
from PyQt4 import QtCore, QtGui
from ServerDetailsGroupBox import ServerDetailsGroupBox
from FileSelectGroupBox import FileSelectGroupBox
import resource_rc
from freeseer.framework.metadata import FreeseerMetadataLoader
from freeseer.framework.plugin import IMetadataReader
import functools

class UploaderWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.verticalLayout_central = QtGui.QVBoxLayout(self)
        self.verticalLayout_central.setObjectName("verticalLayout_central")
        
        ### top half ###
        self.serverdetails = ServerDetailsGroupBox(self)
        self.setObjectName("serverdetails")
        self.verticalLayout_central.addWidget(self.serverdetails)
        
        ### bottom half ###
        self.fileselect = FileSelectGroupBox(self)
        self.setObjectName("fileselect")
        self.verticalLayout_central.addWidget(self.fileselect)
        
        ### bottom button bar ###
        self.buttonbar = UploaderButtonBar(self)
        self.buttonbar.setObjectName("buttonbar")
        self.verticalLayout_central.addWidget(self.buttonbar)

class UploaderButtonBar(QtGui.QDialogButtonBox):
    def __init__(self, parent=None):
        QtGui.QDialogButtonBox.__init__(self, parent)
        
        ## uploadbutton ##
        self.pushButton_upload = QtGui.QPushButton(self)
        modfont = QtGui.QFont(self.pushButton_upload.font())
        modfont.setPointSize(modfont.pointSize() + 4)
#        modfont.setBold(True)
        self.pushButton_upload.setFont(modfont)
        self.pushButton_upload.setMinimumSize(QtCore.QSize(0, self.pushButton_upload.height()*1.2))
        self.pushButton_upload.setAutoDefault(True)
        self.pushButton_upload.setDefault(True)
        self.pushButton_upload.setObjectName("pushButton_upload")
        self.addButton(self.pushButton_upload, QtGui.QDialogButtonBox.AcceptRole)
        
        ## cancelbutton ##
        self.pushButton_cancel = self.addButton(QtGui.QDialogButtonBox.Cancel)
        
        self.retranslate()
    
    def retranslate(self):
        self.pushButton_upload.setText(self.tr("Upload!"))
    
class UploaderMenuBar(QtGui.QMenuBar):
    def __init__(self, parent = None):
        QtGui.QMenuBar.__init__(self, parent)
        
        self.menuFile = QtGui.QMenu(self)
        self.menuFile.setObjectName("menuFile")
        self.menuEdit = QtGui.QMenu(self)
        self.menuEdit.setObjectName("menuEdit")
        self.menuView = QtGui.QMenu(self)
        self.menuView.setObjectName("menuView")
        
        self.actionOpen_Directory = QtGui.QAction(parent)
        self.actionOpen_Directory.setObjectName("actionOpen_Directory")
        self.actionUpload = QtGui.QAction(parent)
        self.actionUpload.setObjectName("actionUpload")
        self.actionClose = QtGui.QAction(parent)
        self.actionClose.setObjectName("actionClose")
        self.actionSelect_All = QtGui.QAction(parent)
        self.actionSelect_All.setObjectName("actionSelect_All")
        self.actionSelect_None = QtGui.QAction(parent)
        self.actionSelect_None.setObjectName("actionSelect_None")
        self.actionInvert_Selection = QtGui.QAction(parent)
        self.actionInvert_Selection.setObjectName("actionInvert_Selection")
#        self.actionPreferences = QtGui.QAction(parent)
#        self.actionPreferences.setObjectName("actionPreferences")
#        self.actionFilter = QtGui.QAction(parent)
#        self.actionFilter.setObjectName("actionFilter")
#        self.actionFilter.setVisible(False)
        
        self.actionMetadata_Launch_Ex_Falso = QtGui.QAction(parent)
        self.actionMetadata_Launch_Ex_Falso.setObjectName("actionMetadata_Launch_Ex_Falso")
                
        self.menuFile.addAction(self.actionOpen_Directory)
        self.menuFile.addAction(self.actionUpload)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionClose)
        self.menuEdit.addAction(self.actionSelect_All)
        self.menuEdit.addAction(self.actionSelect_None)
        self.menuEdit.addAction(self.actionInvert_Selection)
        self.menuEdit.addSeparator()
        self.menuEdit.addAction(self.actionMetadata_Launch_Ex_Falso)
#        self.menuEdit.addAction(self.actionPreferences)
#        self.menuView.addAction(self.actionFilter)
        self.menuView.addSeparator()
        
        self.loader = None
        self.columnViewActions = []    # [(key, field, action, slot)]
        self.columnViewActionDict = {} # {key: action}
        
        self.addAction(self.menuFile.menuAction())
        self.addAction(self.menuEdit.menuAction())
        self.addAction(self.menuView.menuAction())
        
        self.retranslate()
        self.loadSettings()
        
    def retranslate(self): 
        self.menuFile.setTitle(self.tr("&File"))
        self.menuEdit.setTitle(self.tr("&Edit"))
        self.menuView.setTitle(self.tr("&View"))
        self.actionOpen_Directory.setText(self.tr("&Open Directory..."))
        self.actionUpload.setText(self.tr("&Upload"))
        self.actionClose.setText(self.tr("&Close"))
        self.actionSelect_All.setText(self.tr("Select &All"))
        self.actionSelect_None.setText(self.tr("Select &None"))
        self.actionInvert_Selection.setText(self.tr("&Invert Selection"))
#        self.actionPreferences.setText(self.tr("&Preferences"))
#        self.actionFilter.setText(self.tr("&Filter..."))
        self.actionMetadata_Launch_Ex_Falso.setText(self.tr("Metadata (Launch Ex Falso)"))
        # TODO: iterate through metadata plugins and retranslate their header text.

    def loadSettings(self):
        # TODO: actually load & save the previously checked properties
        # this means moving this function up to videouploader.UploaderApp, 
        #  which will have access to FreeseerCore.config
        pass
    
    def onFieldVisibilityChange(self, field_name, state):
        self.columnViewActionDict[str(field_name)].setChecked(state)
    
    def onFieldsChanged(self):
        self._resetColumnViewActions()
    
    def _resetColumnViewActions(self):
        # TODO:make sure there isn't a memory leak
        # make sure that the actions aren't left around since their parent is still around
        # look at pyqt's documentation on QObject lifecycle
        for _, _, action, slot in self.columnViewActions:
            action.triggered.disconnect(slot)
            self.menuView.removeAction(action)
        self.columnViewActions = []
        self.columnViewActionDict = {}
        if self.loader == None:
            return
        
        for key, field in self.loader.get_fields_sorted():
            assert isinstance(field, IMetadataReader.header)
            # see above: note: we don't set the parent of the qaction so that it
            #                  will be managed by python and get deleted on g.c.
#            action = QtGui.QAction(self.parent())
            action = QtGui.QAction(None)
            action.setText(field.name)
            action.setCheckable(True)
            action.setChecked(field.visible)
            slot = functools.partial(self.loader.set_visible, key)
            action.triggered.connect(slot)
            self.columnViewActions.append((key, field, action, slot))
            self.columnViewActionDict[key] = action
            self.menuView.addAction(action)
            
    def setMetadataLoader(self, loader):
        if self.loader != None:
            self.loader.field_visibility_changed.disconnect(self.onFieldVisibilityChange)
            self.loader.fields_changed.disconnect(self.onFieldsChanged)
        
        self.loader = loader
        self._resetColumnViewActions()
        if loader == None:
            return
        assert isinstance(loader, FreeseerMetadataLoader)
        
        loader.field_visibility_changed.connect(self.onFieldVisibilityChange)
        loader.fields_changed.connect(self.onFieldsChanged)
        
        
if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    main = UploaderWidget()
    main.show()
    sys.exit(app.exec_())
    
