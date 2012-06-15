#!/usr/bin/python
# -*- coding: utf-8 -*-

# freeseer - vga/presentation capture software
#
#  Copyright (C) 2011  Free and Open Source Software Learning Centre
#  http://fosslc.org
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

# For support, questions, suggestions or any other inquiries, visit:
# http://wiki.github.com/Freeseer/freeseer/

import ConfigParser
import logging
import os
import sys

from PyQt4 import QtGui, QtCore

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

from freeseer import project_info
from freeseer.framework.core import FreeseerCore
from freeseer.frontend.qtcommon.AboutDialog import AboutDialog
from freeseer.frontend.qtcommon.Resource import resource_rc
from freeseer.framework.plugin import IOutput

from ConfigToolWidget import ConfigToolWidget
from GeneralWidget import GeneralWidget
from AVWidget import AVWidget
from PluginLoaderWidget import PluginLoaderWidget
from LoggerWidget import LoggerWidget

__version__ = project_info.VERSION

class ConfigToolApp(QtGui.QMainWindow):
    '''
    ConfigTool is used to tune settings used by the Freeseer Application
    '''

    def __init__(self, core=None):
        QtGui.QMainWindow.__init__(self)
        
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8(":/freeseer/logo.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.setWindowIcon(icon)
        
        # Initialize geometry, to be used for restoring window positioning.
        self.geometry = None

        self.mainWidget = ConfigToolWidget()
        self.setCentralWidget(self.mainWidget)
        
        self.currentWidget = None
        self.mainWidgetLayout = QtGui.QVBoxLayout()
        self.mainWidget.rightPanelWidget.setLayout(self.mainWidgetLayout)
        
        # Load all ConfigTool Widgets
        self.aboutDialog = AboutDialog()
        self.generalWidget = GeneralWidget()
        self.avWidget = AVWidget()
        self.pluginloaderWidget = PluginLoaderWidget()
        self.loggerWidget = LoggerWidget()
        
        # Only instantiate a new Core if we need to
        if core is None:
            self.core = FreeseerCore()
        else:
            self.core = core
        
        self.config = self.core.get_config()
        self.plugman = self.core.get_plugin_manager()
        
        #
        # Translator
        #
        self.current_language = None
        self.uiTranslator = QtCore.QTranslator()
        self.uiTranslator.load(":/languages/tr_en_US.qm")
        self.langActionGroup = QtGui.QActionGroup(self)
        self.langActionGroup.setExclusive(True)
        QtCore.QTextCodec.setCodecForTr(QtCore.QTextCodec.codecForName('utf-8'))
        self.connect(self.langActionGroup, QtCore.SIGNAL('triggered(QAction *)'), self.translate)
        # --- Translator
        
        #
        # Setup Menubar
        #
        self.menubar = QtGui.QMenuBar()
        self.setMenuBar(self.menubar)
        
        self.menubar.setGeometry(QtCore.QRect(0, 0, 566, 26))
        self.menubar.setObjectName(_fromUtf8("menubar"))
        self.menuFile = QtGui.QMenu(self.menubar)
        self.menuFile.setObjectName(_fromUtf8("menuFile"))
        self.menuOptions = QtGui.QMenu(self.menubar)
        self.menuOptions.setObjectName(_fromUtf8("menuOptions"))
        self.menuLanguage = QtGui.QMenu(self.menuOptions)
        self.menuLanguage.setObjectName(_fromUtf8("menuLanguage"))
        self.menuHelp = QtGui.QMenu(self.menubar)
        self.menuHelp.setObjectName(_fromUtf8("menuHelp"))
        
        exitIcon = QtGui.QIcon.fromTheme("application-exit")
        self.actionExit = QtGui.QAction(self)
        self.actionExit.setShortcut("Ctrl+Q")
        self.actionExit.setObjectName(_fromUtf8("actionExit"))
        self.actionExit.setIcon(exitIcon)
        
        self.actionAbout = QtGui.QAction(self)
        self.actionAbout.setObjectName(_fromUtf8("actionAbout"))
        self.actionAbout.setIcon(icon)
        
        # Actions
        self.menuFile.addAction(self.actionExit)
        self.menuHelp.addAction(self.actionAbout)
        self.menuOptions.addAction(self.menuLanguage.menuAction())
        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuOptions.menuAction())
        self.menubar.addAction(self.menuHelp.menuAction())
        
        self.connect(self.actionExit, QtCore.SIGNAL('triggered()'), self.close)
        self.connect(self.actionAbout, QtCore.SIGNAL('triggered()'), self.aboutDialog.show)
        
        self.setupLanguageMenu()
        # --- End Menubar

        # connections
        self.connect(self.mainWidget.closePushButton, QtCore.SIGNAL('clicked()'), self.close)
        self.connect(self.mainWidget.optionsTreeWidget, QtCore.SIGNAL('itemSelectionChanged()'), self.change_option)
        
        #
        # general tab connections
        #
        self.connect(self.generalWidget.languageComboBox, QtCore.SIGNAL('currentIndexChanged(int)'), self.set_default_language)
        self.connect(self.generalWidget.recordDirPushButton, QtCore.SIGNAL('clicked()'), self.browse_video_directory)
        self.connect(self.generalWidget.recordDirLineEdit, QtCore.SIGNAL('editingFinished()'), self.update_record_directory)
        self.connect(self.generalWidget.autoHideCheckBox, QtCore.SIGNAL('toggled(bool)'), self.toggle_autohide)
        
        #
        # AV tab connections
        #
        self.connect(self.avWidget.audioGroupBox, QtCore.SIGNAL('toggled(bool)'), self.toggle_audiomixer_state)
        self.connect(self.avWidget.audioMixerComboBox, QtCore.SIGNAL('activated(const QString&)'), self.change_audiomixer)
        self.connect(self.avWidget.audioMixerSetupPushButton, QtCore.SIGNAL('clicked()'), self.setup_audio_mixer)
        self.connect(self.avWidget.videoGroupBox, QtCore.SIGNAL('toggled(bool)'), self.toggle_videomixer_state)
        self.connect(self.avWidget.videoMixerComboBox, QtCore.SIGNAL('activated(const QString&)'), self.change_videomixer)
        self.connect(self.avWidget.videoMixerSetupPushButton, QtCore.SIGNAL('clicked()'), self.setup_video_mixer)
        self.connect(self.avWidget.fileGroupBox, QtCore.SIGNAL('toggled(bool)'), self.toggle_record_to_file)
        self.connect(self.avWidget.fileComboBox, QtCore.SIGNAL('activated(const QString&)'), self.change_file_format)
        self.connect(self.avWidget.fileSetupPushButton, QtCore.SIGNAL('clicked()'), self.setup_file_format)
        self.connect(self.avWidget.streamGroupBox, QtCore.SIGNAL('toggled(bool)'), self.toggle_record_to_stream)
        self.connect(self.avWidget.streamComboBox, QtCore.SIGNAL('activated(const QString&)'), self.change_stream_format)
        self.connect(self.avWidget.streamSetupPushButton, QtCore.SIGNAL('clicked()'), self.setup_stream_format)
        # GUI Disabling/Enabling Connections
        self.connect(self.avWidget.audioGroupBox, QtCore.SIGNAL("toggled(bool)"), self.avWidget.audioMixerLabel.setEnabled)
        self.connect(self.avWidget.audioGroupBox, QtCore.SIGNAL("toggled(bool)"), self.avWidget.audioMixerComboBox.setEnabled)
        self.connect(self.avWidget.audioGroupBox, QtCore.SIGNAL("toggled(bool)"), self.avWidget.audioMixerSetupPushButton.setEnabled)
        self.connect(self.avWidget.videoGroupBox, QtCore.SIGNAL("toggled(bool)"), self.avWidget.videoMixerLabel.setEnabled)
        self.connect(self.avWidget.videoGroupBox, QtCore.SIGNAL("toggled(bool)"), self.avWidget.videoMixerComboBox.setEnabled)
        self.connect(self.avWidget.videoGroupBox, QtCore.SIGNAL("toggled(bool)"), self.avWidget.videoMixerSetupPushButton.setEnabled)
        self.connect(self.avWidget.fileGroupBox, QtCore.SIGNAL("toggled(bool)"), self.avWidget.fileLabel.setEnabled)
        self.connect(self.avWidget.fileGroupBox, QtCore.SIGNAL("toggled(bool)"), self.avWidget.fileComboBox.setEnabled)
        self.connect(self.avWidget.fileGroupBox, QtCore.SIGNAL("toggled(bool)"), self.avWidget.fileSetupPushButton.setEnabled)
        self.connect(self.avWidget.streamGroupBox, QtCore.SIGNAL("toggled(bool)"), self.avWidget.streamLabel.setEnabled)
        self.connect(self.avWidget.streamGroupBox, QtCore.SIGNAL("toggled(bool)"), self.avWidget.streamComboBox.setEnabled)
        self.connect(self.avWidget.streamGroupBox, QtCore.SIGNAL("toggled(bool)"), self.avWidget.streamSetupPushButton.setEnabled)
        
        #
        # Logger Widget Connections
        #
        self.connect(self.loggerWidget.consoleLoggerGroupBox,
                     QtCore.SIGNAL('toggled(bool)'),
                     self.toggle_console_logger)
        self.connect(self.loggerWidget.consoleLoggerLevelComboBox,
                     QtCore.SIGNAL('activated(const QString&)'),
                     self.change_console_loglevel)
        self.connect(self.loggerWidget.syslogLoggerGroupBox,
                     QtCore.SIGNAL('toggled(bool)'),
                     self.toggle_syslog_logger)
        self.connect(self.loggerWidget.syslogLoggerLevelComboBox,
                     QtCore.SIGNAL('activated(const QString&)'),
                     self.change_syslog_loglevel)
        
        self.retranslate()

        # load active plugin widgets
        self.load_plugin_widgets()
        
        # Start off with displaying the General Settings
        items = self.mainWidget.optionsTreeWidget.findItems("General", QtCore.Qt.MatchExactly)
        if len(items) > 0:
            item = items[0]
            self.mainWidget.optionsTreeWidget.setCurrentItem(item)

    ###
    ### Translation
    ###
    
    def retranslate(self):
        self.setWindowTitle(self.uiTranslator.translate("ConfigToolApp", "Freeseer ConfigTool"))
        
        #
        # Menubar
        #
        self.menuFile.setTitle(self.uiTranslator.translate("ConfigToolApp", "&File"))
        self.menuOptions.setTitle(self.uiTranslator.translate("ConfigToolApp", "&Options"))
        self.menuLanguage.setTitle(self.uiTranslator.translate("ConfigToolApp", "&Language"))
        self.menuHelp.setTitle(self.uiTranslator.translate("ConfigToolApp", "&Help"))
        self.actionExit.setText(self.uiTranslator.translate("ConfigToolApp", "&Quit"))
        self.actionAbout.setText(self.uiTranslator.translate("ConfigToolApp", "&About"))
        # --- End Menubar
        
        #
        # ConfigToolWidget
        #
        self.generalString = self.uiTranslator.translate("ConfigToolApp", "General")
        self.avString = self.uiTranslator.translate("ConfigToolApp", "Recording")
        self.pluginsString = self.uiTranslator.translate("ConfigToolApp", "Plugins")
        self.audioInputString = self.uiTranslator.translate("ConfigToolApp", "AudioInput")
        self.audioMixerString = self.uiTranslator.translate("ConfigToolApp", "AudioMixer")
        self.videoInputString = self.uiTranslator.translate("ConfigToolApp", "VideoInput")
        self.videoMixerString = self.uiTranslator.translate("ConfigToolApp", "VideoMixer")
        self.outputString = self.uiTranslator.translate("ConfigToolApp", "Output")
        self.loggerString = self.uiTranslator.translate("ConfigToolApp", "Logger")
        self.metadataString = self.uiTranslator.translate("ConfigToolApp", "Metadata")
        
        self.mainWidget.optionsTreeWidget.topLevelItem(0).setText(0, self.generalString)
        self.mainWidget.optionsTreeWidget.topLevelItem(1).setText(0, self.avString)
        self.mainWidget.optionsTreeWidget.topLevelItem(2).setText(0, self.pluginsString)
        self.mainWidget.optionsTreeWidget.topLevelItem(2).child(0).setText(0, self.audioInputString)
        self.mainWidget.optionsTreeWidget.topLevelItem(2).child(1).setText(0, self.audioMixerString)
        self.mainWidget.optionsTreeWidget.topLevelItem(2).child(2).setText(0, self.videoInputString)
        self.mainWidget.optionsTreeWidget.topLevelItem(2).child(3).setText(0, self.videoMixerString)
        self.mainWidget.optionsTreeWidget.topLevelItem(2).child(4).setText(0, self.outputString)
        self.mainWidget.optionsTreeWidget.topLevelItem(3).setText(0, self.loggerString)
        
        self.mainWidget.closePushButton.setText(self.uiTranslator.translate("ConfigToolApp", "Close"))
        # --- End ConfigToolWidget
        
        #
        # GeneralWidget
        #
        self.generalWidget.MiscGroupBox.setTitle(self.uiTranslator.translate("ConfigToolApp", "Miscellaneous"))
        self.generalWidget.languageLabel.setText(self.uiTranslator.translate("ConfigToolApp", "Default Language"))
        self.generalWidget.recordDirLabel.setText(self.uiTranslator.translate("ConfigToolApp", "Record Directory"))
        self.generalWidget.autoHideCheckBox.setText(self.uiTranslator.translate("ConfigToolApp", "Enable Auto-Hide"))
        # --- End GeneralWidget
        
        #
        # AV Widget
        #
        self.avWidget.audioGroupBox.setTitle(self.uiTranslator.translate("ConfigToolApp", "Audio Input"))
        self.avWidget.audioMixerLabel.setText(self.uiTranslator.translate("ConfigToolApp", "Audio Mixer"))
        self.avWidget.audioMixerSetupPushButton.setText(self.uiTranslator.translate("ConfigToolApp", "Setup"))
        
        self.avWidget.videoGroupBox.setTitle(self.uiTranslator.translate("ConfigToolApp", "Video Input"))
        self.avWidget.videoMixerLabel.setText(self.uiTranslator.translate("ConfigToolApp", "Video Mixer"))
        self.avWidget.videoMixerSetupPushButton.setText(self.uiTranslator.translate("ConfigToolApp", "Setup"))
        # --- End AV Widget
        
        #
        # Logger Widget
        #
        self.loggerWidget.consoleLoggerGroupBox.setTitle(self.uiTranslator.translate("ConfigToolApp", "Console Logger"))
        self.loggerWidget.consoleLoggerLevelLabel.setText(self.uiTranslator.translate("ConfigToolApp", "Log Level"))
        self.loggerWidget.syslogLoggerGroupBox.setTitle(self.uiTranslator.translate("ConfigToolApp", "Syslog Logger"))
        self.loggerWidget.syslogLoggerLevelLabel.setText(self.uiTranslator.translate("ConfigToolApp", "Log Level"))
        # --- End LoggerWidget
        
        self.aboutDialog.retranslate(self.current_language)
        
    def translate(self, action):
        '''
        When a language is selected from the language menu this function is called
        The language to be changed to is retrieved
        '''
        self.current_language = str(action.data().toString()).strip("tr_").rstrip(".qm")
        
        logging.info("Switching language to: %s" % action.text())
        self.uiTranslator.load(":/languages/tr_%s.qm" % self.current_language)
        
        self.retranslate()

    def setupLanguageMenu(self):
        languages = QtCore.QDir(":/languages").entryList()
        
        if self.current_language is None:
            self.current_language = QtCore.QLocale.system().name()    #Retrieve Current Locale from the operating system
            logging.debug("Detected user's locale as %s" % self.current_language)
        
        for language in languages:
            translator = QtCore.QTranslator()   #Create a translator to translate Language Display Text
            translator.load(":/languages/%s" % language)
            language_display_text = translator.translate("Translation", "Language Display Text")
            
            languageAction = QtGui.QAction(self)
            languageAction.setCheckable(True)
            languageAction.setText(language_display_text)
            languageAction.setData(language)
            self.menuLanguage.addAction(languageAction)
            self.langActionGroup.addAction(languageAction)
            self.generalWidget.languageComboBox.addItem(language_display_text, language)
            
            if self.current_language == str(language).strip("tr_").rstrip(".qm"):
                languageAction.setChecked(True)

    ###
    ### General
    ###
        
    def change_option(self):
        option = self.mainWidget.optionsTreeWidget.currentItem().text(0)
        
        if self.currentWidget is not None:
            self.mainWidgetLayout.removeWidget(self.currentWidget)
            self.currentWidget.hide()
          
        if option == self.generalString:
            self.load_general_widget()
        elif option == self.avString:
            self.load_av_widget()
        elif option == self.pluginsString:
            pass
        elif option == self.audioInputString:
            self.load_option_audioinput_plugins()
        elif option == self.audioMixerString:
            self.load_option_audiomixer_plugins()
        elif option == self.videoInputString:
            self.load_option_videoinput_plugins()
        elif option == self.videoMixerString:
            self.load_option_videomixer_plugins()
        elif option == self.outputString:
            self.load_option_output_plugins()
        elif option == self.loggerString:
            self.load_logger_widget()
        elif option == self.metadataString:
            self.load_option_metadata_plugins()
        else:
            pass
        
    def load_general_widget(self):
        self.mainWidgetLayout.addWidget(self.generalWidget)
        self.currentWidget = self.generalWidget
        self.currentWidget.show()
        
        # Load default language
        i = self.generalWidget.languageComboBox.findData(self.config.default_language)
        self.generalWidget.languageComboBox.setCurrentIndex(i)
        actions = self.menuLanguage.actions()
        for action in actions:
            if action.data().toString() == self.config.default_language:
                action.setChecked(True)
                self.translate(action)
                break
        
        # Recording Directory Settings
        self.generalWidget.recordDirLineEdit.setText(self.config.videodir)
        
        # Load Auto Hide Settings
        if self.config.auto_hide == True:
            self.generalWidget.autoHideCheckBox.setChecked(True)
        else:
            self.generalWidget.autoHideCheckBox.setChecked(False)
            
    def set_default_language(self, language):
        language_file = str(self.generalWidget.languageComboBox.itemData(language).toString())
        self.config.default_language = language_file
        self.config.writeConfig()

    def browse_video_directory(self):
        directory = self.generalWidget.recordDirLineEdit.text()
        
        newDir = QtGui.QFileDialog.getExistingDirectory(self, "Select Video Directory", directory)
        if newDir == "": newDir = directory
        
        videodir = os.path.abspath(str(newDir))
        self.generalWidget.recordDirLineEdit.setText(videodir)
        self.generalWidget.recordDirLineEdit.emit(QtCore.SIGNAL("editingFinished()"))

    def update_record_directory(self):
        self.config.videodir = str(self.generalWidget.recordDirLineEdit.text())
        self.config.writeConfig()

    def toggle_autohide(self, state):
        self.config.auto_hide = state
        self.config.writeConfig()
            
    ###
    ### AV Related
    ###        
    
    def load_av_widget(self):
        self.mainWidgetLayout.addWidget(self.avWidget)
        self.currentWidget = self.avWidget
        self.currentWidget.show()
        
        #
        # Set up Audio
        #
        if self.config.enable_audio_recoding == True:
            self.avWidget.audioGroupBox.setChecked(True)
        else:
            self.avWidget.audioGroupBox.setChecked(False)
            self.avWidget.audioMixerComboBox.setEnabled(False)
            self.avWidget.audioMixerSetupPushButton.setEnabled(False)
            
        n = 0 # Counter for finding Audio Mixer to set as current.
        self.avWidget.audioMixerComboBox.clear()
        plugins = self.plugman.plugmanc.getPluginsOfCategory("AudioMixer")
        for plugin in plugins:
            self.avWidget.audioMixerComboBox.addItem(plugin.plugin_object.get_name())
            if plugin.plugin_object.get_name() == self.config.audiomixer:
                self.avWidget.audioMixerComboBox.setCurrentIndex(n)
            n += 1
        
        #
        # Set up Video
        #
        if self.config.enable_video_recoding == True:
            self.avWidget.videoGroupBox.setChecked(True)
        else:
            self.avWidget.videoGroupBox.setChecked(False)
            self.avWidget.videoMixerComboBox.setEnabled(False)
            self.avWidget.videoMixerSetupPushButton.setEnabled(False)
            
        n = 0 # Counter for finding Video Mixer to set as current.
        self.avWidget.videoMixerComboBox.clear()
        plugins = self.plugman.plugmanc.getPluginsOfCategory("VideoMixer")
        for plugin in plugins:
            self.avWidget.videoMixerComboBox.addItem(plugin.plugin_object.get_name())
            if plugin.plugin_object.get_name() == self.config.videomixer:
                self.avWidget.videoMixerComboBox.setCurrentIndex(n)
            n += 1
                
        #
        # Set up File Format
        #
        if self.config.record_to_file == True:
            self.avWidget.fileGroupBox.setChecked(True)
        else:
            self.avWidget.fileGroupBox.setChecked(False)
            self.avWidget.fileComboBox.setEnabled(False)
            self.avWidget.fileSetupPushButton.setEnabled(False)
            
        n = 0 # Counter for finding File Format to set as current
        self.avWidget.fileComboBox.clear()
        plugins = self.plugman.plugmanc.getPluginsOfCategory("Output")
        for plugin in plugins:
            if plugin.plugin_object.get_recordto() == IOutput.FILE:
                self.avWidget.fileComboBox.addItem(plugin.plugin_object.get_name())
                if plugin.plugin_object.get_name() == self.config.record_to_file_plugin:
                    self.avWidget.fileComboBox.setCurrentIndex(n)
                n += 1
        
        #
        # Set up Stream Format
        #
        if self.config.record_to_stream == True:
            self.avWidget.streamGroupBox.setChecked(True)
        else:
            self.avWidget.streamGroupBox.setChecked(False)
            self.avWidget.streamComboBox.setEnabled(False)
            self.avWidget.streamSetupPushButton.setEnabled(False)

    def toggle_audiomixer_state(self, state):
        self.config.enable_audio_recoding = state
        self.config.writeConfig()
        
    def change_audiomixer(self, audiomixer):
        self.config.audiomixer = audiomixer
        self.config.writeConfig()

    def setup_audio_mixer(self):
        mixer = str(self.avWidget.audioMixerComboBox.currentText())
        plugin = self.plugman.plugmanc.getPluginByName(mixer, "AudioMixer")
        plugin.plugin_object.get_dialog()
            
    def toggle_videomixer_state(self, state):
        self.config.enable_video_recoding = state
        self.config.writeConfig()
        
    def change_videomixer(self, videomixer):
        self.config.videomixer = videomixer
        self.config.writeConfig()
    
    def setup_video_mixer(self):
        mixer = str(self.avWidget.videoMixerComboBox.currentText())
        plugin = self.plugman.plugmanc.getPluginByName(mixer, "VideoMixer")
        plugin.plugin_object.get_dialog()

    def toggle_record_to_file(self, state):
        self.config.record_to_file = state
        self.config.writeConfig()
        
    def change_file_format(self, format):
        self.config.record_to_file_plugin = format
        self.config.writeConfig()
    
    def setup_file_format(self):
        output = str(self.avWidget.fileComboBox.currentText())
        plugin = self.plugman.plugmanc.getPluginByName(output, "Output")
        plugin.plugin_object.get_dialog()
        
    def toggle_record_to_stream(self, state):
        self.config.record_to_stream = state
        self.config.writeConfig()
        
    def change_stream_format(self, format):
        self.config.record_to_stream_plugin = format
        self.config.writeConfig()
    
    def setup_stream_format(self):
        output = str(self.avWidget.streamComboBox.currentText())
        plugin = self.plugman.plugmanc.getPluginByName(output, "Output")
        plugin.plugin_object.get_dialog()    

    ###
    ### Plugin Loader Related
    ###
        
    def load_plugin_list(self, plugin_type):
        self.pluginloaderWidget.listWidget.clear()
        for plugin in self.plugman.plugmanc.getPluginsOfCategory(plugin_type):
            item = QtGui.QListWidgetItem()
            
            size = QtCore.QSize(64, 64)
            item.setSizeHint(size)
            self.pluginloaderWidget.listWidget.addItem(item)
            
            # The list item will be a fancy widget.
            widget = self.pluginloaderWidget.getListWidgetPlugin(plugin,
                                                                 plugin_type,
                                                                 self.plugman)
            self.pluginloaderWidget.listWidget.setItemWidget(item, widget)

    def load_option_audioinput_plugins(self):
        self.mainWidgetLayout.addWidget(self.pluginloaderWidget)
        self.currentWidget = self.pluginloaderWidget
        self.currentWidget.show()

        self.load_plugin_list("AudioInput")
            
    def load_option_audiomixer_plugins(self):
        self.mainWidgetLayout.addWidget(self.pluginloaderWidget)
        self.currentWidget = self.pluginloaderWidget
        self.currentWidget.show()

        self.load_plugin_list("AudioMixer")
        
    def load_option_videoinput_plugins(self):
        self.mainWidgetLayout.addWidget(self.pluginloaderWidget)
        self.currentWidget = self.pluginloaderWidget
        self.currentWidget.show()

        self.load_plugin_list("VideoInput")
            
    def load_option_videomixer_plugins(self):
        self.mainWidgetLayout.addWidget(self.pluginloaderWidget)
        self.currentWidget = self.pluginloaderWidget
        self.currentWidget.show()

        self.load_plugin_list("VideoMixer")
    
    def load_option_output_plugins(self):
        self.mainWidgetLayout.addWidget(self.pluginloaderWidget)
        self.currentWidget = self.pluginloaderWidget
        self.currentWidget.show()
        
        self.load_plugin_list("Output")
        
    def load_option_metadata_plugins(self):
        self.mainWidgetLayout.addWidget(self.pluginloaderWidget)
        self.currentWidget = self.pluginloaderWidget
        self.currentWidget.show()
        
        self.load_plugin_list("Metadata")
    
    def load_plugin_widgets(self):
        for plugin in self.plugman.plugmanc.getAllPlugins():
            plugin.plugin_object.set_gui(self)

    def show_plugin_widget_dialog(self, widget):
        self.dialog = QtGui.QDialog(self)
    
        self.dialog_layout = QtGui.QVBoxLayout()
        self.dialog.setLayout(self.dialog_layout)
        self.dialog_layout.addWidget(widget)
        
        self.dialog.closeButton = QtGui.QPushButton("Close")
        self.dialog_layout.addWidget(self.dialog.closeButton)
        self.connect(self.dialog.closeButton, QtCore.SIGNAL('clicked()'), self.dialog.close)
        self.dialog.show()
            
    def get_plugin_settings_widget(self, plugin):
        widget = plugin.plugin_object.get_widget()
        return widget
    
    #
    # Logger Widget Related
    # 
    def load_logger_widget(self):
        self.mainWidgetLayout.addWidget(self.loggerWidget)
        self.currentWidget = self.loggerWidget
        self.currentWidget.show()
        
        # Get the config details
        config = ConfigParser.ConfigParser()
        config.readfp(open(self.core.logger.logconf))
        handlers = config.get('logger_root', 'handlers')
        handler_list = handlers.split(',')
        
        consoleLogger = False
        syslogLogger = False
        for handler in handler_list:
            if handler == "consoleHandler":
                consoleLogger = True
            elif handler == "syslogHandler":
                syslogLogger = True
                
        consoleLoggerLevel = config.get('handler_consoleHandler', 'level')
        syslogLoggerLevel = config.get('handler_syslogHandler', 'level')
        # --- End Get config details
        
        #
        # Set the Widget with the details gathered from config
        #
        log_levels = ["NOTSET", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        
        # Console Logger
        if consoleLogger is True:
            self.loggerWidget.consoleLoggerGroupBox.setChecked(True)
        else:
            self.loggerWidget.consoleLoggerGroupBox.setChecked(False)
        
        n = 0
        for level in log_levels:
            self.loggerWidget.consoleLoggerLevelComboBox.addItem(level)
        
            if level == consoleLoggerLevel:
                self.loggerWidget.consoleLoggerLevelComboBox.setCurrentIndex(n)
            n += 1
        # --- End Console Logger
        
        # Syslogger
        if syslogLogger is True:
            self.loggerWidget.syslogLoggerGroupBox.setChecked(True)
        else:
            self.loggerWidget.syslogLoggerGroupBox.setChecked(False)
            
        n = 0
        for level in log_levels:
            self.loggerWidget.syslogLoggerLevelComboBox.addItem(level)
        
            if level == syslogLoggerLevel:
                self.loggerWidget.syslogLoggerLevelComboBox.setCurrentIndex(n)
            n += 1
        # --- End Syslogger
    
    def toggle_console_logger(self, state):
        config = ConfigParser.ConfigParser()
        config.readfp(open(self.core.logger.logconf))
        handlers = config.get("logger_root", "handlers")
        handler_list = handlers.split(',')
        
        if self.loggerWidget.consoleLoggerGroupBox.isChecked():
            new_list = "consoleHandler,"
        else:
            new_list = ""
        
        for handler in handler_list:
            if handler == "consoleHandler": continue
            new_list += handler + ","
        new_list = new_list.rstrip(',')
        
        config.set("logger_root", "handlers", new_list)
        
        with open(self.core.logger.logconf, 'w') as configfile:
            config.write(configfile)
    
    def change_console_loglevel(self, level):
        config = ConfigParser.ConfigParser()
        config.readfp(open(self.core.logger.logconf))
        config.set("handler_consoleHandler", "level", level)
        with open(self.core.logger.logconf, 'w') as configfile:
            config.write(configfile)
            
    def toggle_syslog_logger(self, state):
        config = ConfigParser.ConfigParser()
        config.readfp(open(self.core.logger.logconf))
        handlers = config.get("logger_root", "handlers")
        handler_list = handlers.split(',')
        
        if self.loggerWidget.syslogLoggerGroupBox.isChecked():
            new_list = "syslogHandler,"
        else:
            new_list = ""
        
        for handler in handler_list:
            if handler == "syslogHandler": continue
            new_list += handler + ","
        new_list = new_list.rstrip(',')
        
        config.set("logger_root", "handlers", new_list)
        
        with open(self.core.logger.logconf, 'w') as configfile:
            config.write(configfile)
    
    def change_syslog_loglevel(self, level):
        config = ConfigParser.ConfigParser()
        config.readfp(open(self.core.logger.logconf))
        config.set("handler_syslogHandler", "level", level)
        with open(self.core.logger.logconf, 'w') as configfile:
            config.write(configfile)

    # Override
    
#    def area_select(self):
#        self.area_selector = QtAreaSelector(self)
#        self.area_selector.show()
#        self.core.logger.log.info('Desktop area selector started.')
#        self.hide()
#
#    def desktopAreaEvent(self, start_x, start_y, end_x, end_y):
#        self.start_x = self.core.config.start_x = start_x
#        self.start_y = self.core.config.start_y = start_y
#        self.end_x = self.core.config.end_x = end_x
#        self.end_y = self.core.config.end_y = end_y
#        self.core.logger.log.debug('area selector start: %sx%s end: %sx%s' % (self.start_x, self.start_y, self.end_x, self.end_y))
#        self.show()
#    

    def closeEvent(self, event):
        logging.info('Exiting configtool...')
        self.geometry = self.saveGeometry()
        event.accept()
