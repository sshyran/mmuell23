from gettext import gettext as _

import gtk, gtk.glade
from gedittools_configure import GeditToolsConfiguration
import gedit
import re
import os
import glib
import string
from ConfigParser import ConfigParser
from countsearchresults import SearchResultCounter
from meldlauncher import MeldLauncher
from xmlhighlighter import XmlHighlighter

ui_str = """<ui>
<menubar name="MenuBar">
<menu name="SearchMenu" action="Search">
<placeholder name="SearchOps_2">
<menuitem name="GeditToolsAction" action="GeditToolsAction"/>
</placeholder>
</menu>
</menubar>
<toolbar name="ToolBar">
<placeholder name="Tool_Opt4"><toolitem name="GeditToolsAction" action="GeditToolsAction"/></placeholder>
</toolbar>
</ui>
"""
#plugin
class GeditToolsWindowHelper:
	def __init__(self, plugin, window):
		self.load_settings()
		self._window = window
		self._plugin = plugin
		self._insert_menu()
		self._highlighted_pairs = {} #pairs of highlighted iters
		self._tag_list = {} #all applied tags by document 
		self._tag_lib = {} #all tags to be assigned
		self._xml_highlighter = XmlHighlighter(self._window)
		
		self._counter = SearchResultCounter(self._window)
		self._meld_launcher = MeldLauncher(self._window)
				
	def load_settings(self):
		#read properties
		properties = os.path.dirname( __file__ ) + "/gedittools.properties"
		self.cfg = ConfigParser()
		self.cfg.read(properties)	

	def deactivate(self):
		self._remove_menu()
		self._window = None
		self._plugin = None
		self._action_group = None
		
	def _insert_menu(self):
		manager = self._window.get_ui_manager()
		self._action_group = gtk.ActionGroup("GeditToolsGroup")
		if self.cfg.get("HighlightingOptions", "enable meld comparing") == "true":
			self._action_group.add_actions([("GeditToolsAction", gtk.STOCK_COPY, _("Compare current file to ..."), '<Control><Shift>c', _("Compare current file to ..."), self.launch_meld)])
		manager.insert_action_group(self._action_group, -1)
		self._ui_id = manager.add_ui_from_string(ui_str)
		
	def _remove_menu(self):
		manager = self._window.get_ui_manager()
		manager.remove_ui(self._ui_id)
		manager.remove_action_group(self._action_group)
		manager.ensure_update()

	def update_ui(self):
		self._action_group.set_sensitive(self._window.get_active_document() != None)
		self._current_doc = self._window.get_active_document()
		self._xml_highlighter.update(self._current_doc)
		self.timer = glib.timeout_add(500, self.general_timer)

	def alert(self, message):		
		self.message_dialog(None, 0, message)
		
	#helper to show a message dialog
	def message_dialog(self, par, typ, msg):
		d = gtk.MessageDialog(par, gtk.DIALOG_MODAL, typ, gtk.BUTTONS_OK, msg)
		d.set_property('use-markup', False)
		d.run()
		d.destroy()

	def close_window(self, window):
		window.hide()

	#general timer. runs always
	def general_timer(self):        
		xml_highlighted = False
		if self._current_doc and self.cfg.get("HighlightingOptions", "highlight xml tree") == "true":
			xml_highlighted = self._xml_highlighter.start_highlighting()

		if not xml_highlighted and self.cfg.get("HighlightingOptions", "highlight selected word") == "true":
			self._xml_highlighter.highlight_selection()

		if self.cfg.get("HighlightingOptions", "count selection in document"):
			self._counter.count_selection(self._current_doc)

	#launch meld
	def launch_meld(self, action):
		self._meld_launcher.compare(self._current_doc)
				
class GeditTools(gedit.Plugin):

	def __init__(self):
		gedit.Plugin.__init__(self)
		self._instances = {}

	def activate(self, window):
		self._instances[window] = GeditToolsWindowHelper(self, window)
	
	def deactivate(self, window):
		self._instances[window].deactivate()
		del self._instances[window]
		
	def update_ui(self, window):
		self._instances[window].update_ui()

	def create_configure_dialog(self):
		config = GeditToolsConfiguration()
		return config.create_configuration_window()
		
