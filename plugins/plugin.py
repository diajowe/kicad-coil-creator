import os
import logging
import json

import wx # type: ignore
import pcbnew # type: ignore

from .lib import menu
from .lib import coilgenerator

# WX GUI form that show coil settings
class CoilGeneratorUI(wx.Frame):
	def __init__(self, pcbnew_frame):
		super(CoilGeneratorUI, self).__init__()

		self.width_label = 120
		self.width_content = 180
		self.padding = 5

		self.board = pcbnew.GetBoard()
		self.path_project = os.path.dirname(self.board.GetFileName())
		self.path_footprint_folder_name = "/coil_footprints/"
		self.path_footprint_folder = self.path_project + self.path_footprint_folder_name
		self.path_fp_lib_table = self.path_project + "/fp-lib-table"

		self._init_logger()
		self.logger = logging.getLogger(__name__)
		self.logger.log(logging.DEBUG, "Running Coil Generator")

		self._pcbnew_frame = pcbnew_frame

		wx.Dialog.__init__(
			self,
			None,
			id = wx.ID_ANY,
			title = u"Coil Generator",
			pos = wx.DefaultPosition,
			size = wx.DefaultSize,
			style = wx.DEFAULT_DIALOG_STYLE
		)

		self.sizer_box = wx.BoxSizer(wx.VERTICAL)

		# self.app = wx.PySimpleApp()
		icon = wx.Icon(os.path.join(os.path.dirname(__file__), 'icon.png'))
		self.SetIcon(icon)
		self.SetBackgroundColour(wx.LIGHT_GREY)

		self._prepare_defaults_from_cached_settings(menu.structure)

		for entry in menu.structure:
			if entry["type"] == "choices":
				entry["wx_elem"] = self._make_choices(entry["label"], entry["choices"], entry["default"], entry["unit"])
				self.Bind(wx.EVT_CHOICE, self._on_choice_change, entry["wx_elem"])
				self.logger.log(logging.DEBUG, "[UI] Adding Choices")

			if entry["type"] == "checkbox":
				entry["wx_elem"] = self._make_checkbox(entry["label"], entry["default"], entry["unit"])
				self.Bind(wx.EVT_CHECKBOX, self._on_value_change, entry["wx_elem"])
				self.logger.log(logging.DEBUG, "[UI] Adding Checkbox")

			if entry["type"] == "slider":
				entry["wx_elem"] = self._make_slider(entry["label"], entry["min"], entry["max"], entry["default"], entry["unit"])
				self.Bind(wx.EVT_SCROLL, self._on_value_change, entry["wx_elem"])
				self.logger.log(logging.DEBUG, "[UI] Adding Slider")

			if entry["type"] == "text":
				entry["wx_elem"] = self._make_textbox(entry["label"], entry["default"], entry["unit"])
				self.Bind(wx.EVT_TEXT, self._on_value_change, entry["wx_elem"])
				self.logger.log(logging.DEBUG, "[UI] Adding Textfield")

			self.logger.log(logging.DEBUG, entry)

		elem_button_generate = wx.Button(self, label="Generate Coil")
		elem_button_generate.Bind(wx.EVT_BUTTON, self._on_generate_button_klick)

		elem_button_save = wx.Button(self, label="Save as Project Footprint")
		elem_button_save.Bind(wx.EVT_BUTTON, self._on_save_button_klick)

		self.sizer_box.Add(elem_button_generate, 0, wx.ALL, self.padding)
		self.sizer_box.Add(elem_button_save, 0, wx.ALL, self.padding)

		self.SetSizer(self.sizer_box)
		self.Layout()
		self.sizer_box.Fit(self)
		self.Centre(wx.BOTH)

	def _on_choice_change(self, event):
		identifier = ""

		for entry in menu.structure:
			if entry["wx_elem"] == event.GetEventObject():
				identifier = entry["id"]

		self._update_cached_setting(identifier, event.GetEventObject().GetSelection())

	def _on_value_change(self, event):
		identifier = ""

		for entry in menu.structure:
			if entry["wx_elem"] == event.GetEventObject():
				identifier = entry["id"]

		self._update_cached_setting(identifier, event.GetEventObject().GetValue())

	def _make_choices(self, label, choices, default = 0, unit = None):
		elem_label = wx.StaticText(self, label=label)
		elem_choices = wx.Choice(self, choices=choices)

		elem_choices.SetSelection(default)

		self._add_content(
			elem_label,
			elem_choices,
			unit
		)

		return elem_choices

	def _make_checkbox(self, label, default = 0, unit = None):
		elem_label = wx.StaticText(self, label=label)
		elem_check = wx.CheckBox(self)

		elem_check.SetValue(default)

		self._add_content(
			elem_label,
			elem_check,
			unit
		)

		return elem_check

	def _make_slider(self, label, min, max, default = 0, unit = None):
		elem_label = wx.StaticText(self, label=label)
		elem_slider = wx.Slider(self, value = 50, minValue = min, maxValue = max, style = wx.SL_HORIZONTAL | wx.SL_LABELS)

		elem_slider.SetValue(default)

		self._add_content(
			elem_label,
			elem_slider,
			unit
		)

		return elem_slider

	def _make_textbox(self, label, default = 0, unit = None):
		elem_label = wx.StaticText(self, label=label)
		elem_text = wx.TextCtrl(self)

		elem_text.SetValue(str(default))

		self._add_content(
			elem_label,
			elem_text,
			unit
		)

		return elem_text

	def _add_content(self, elem_label, elem_content, unit):
		elem_label.SetMinSize((self.width_label, -1))
		elem_content.SetMinSize((self.width_content, -1))

		sizer = wx.BoxSizer(wx.HORIZONTAL)
		sizer.Add(elem_label, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, self.padding)
		sizer.Add(elem_content, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, self.padding)

		if unit:
			unit_label = wx.StaticText(self, label=unit)

			# decrease the content box size:
			elem_content.SetMinSize((self.width_content - unit_label.GetSize().GetWidth() - 2 * self.padding, -1))

			sizer.Add(unit_label, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, self.padding)

		self.sizer_box.Add(sizer, 0, wx.ALL, self.padding)

	def _parse_data(self, identifier):
		self.logger.log(logging.INFO, "Finding value for: " + identifier)
		for entry in menu.structure:
			if entry["id"] != identifier:
				continue

			self.logger.log(logging.INFO, "Located element, extracting data...")

			val = None

			if entry["type"] == "choices":
				val = entry["choices_data"][entry["wx_elem"].GetSelection()]
			elif entry["type"] == "checkbox":
				val = entry["wx_elem"].GetValue()
			elif entry["type"] == "slider":
				val = entry["wx_elem"].GetValue()
			elif entry["type"] == "text":
				val = entry["wx_elem"].GetValue()

			self.logger.log(logging.INFO, "Raw data: " + str(val))

			if entry["datatype"] == "float":
				return float(val)
			elif entry["datatype"] == "int":
				return int(val)
			elif entry["datatype"] == "bool":
				return bool(val)
			else:
				return str(val)

	def _update_cached_setting(self, identifier, value):
		cache_file = os.path.join(os.path.dirname(__file__), "dynamic/lastconfig.json")

		with open(cache_file, "r") as file:
			data = json.load(file)

		data[identifier] = value

		with open(cache_file, "w") as file:
			json.dump(data, file, indent=4)

	def _prepare_defaults_from_cached_settings(self, menu_array):
		cache_file = os.path.join(os.path.dirname(__file__), "dynamic/lastconfig.json")

		with open(cache_file, "r") as file:
			data = json.load(file)

		for entry in menu_array:
			try:
				id = entry["id"]
				thisdefault = data[id]
				entry["default"] = thisdefault
			except KeyError:
				continue

	def _handle_coil_generation(self):
		self.Destroy()

		self.logger.log(logging.INFO, "Generating coil ...")

		template = coilgenerator.generate(
			self._parse_data("layer_count"),
			self._parse_data("turn_direction"),
			self._parse_data("turns_count"),
			self._parse_data("trace_width"),
			self._parse_data("trace_spacing"),
			self._parse_data("via_outer"),
			self._parse_data("via_drill"),
			self._parse_data("outer_diameter"),
			self._parse_data("name")
		)

		self.logger.log(logging.INFO, "Done.")

		return template
	
	def _add_to_fp_lib(self):
		entry = "  (lib (name \"PCB Coils\")"
		entry += "(type \"KiCad\")"
		entry += "(uri \"${KIPRJMOD}" + self.path_footprint_folder_name + "\")"
		entry += "(options \"\")"
		entry += "(descr \"auto-generated coil footprints\"))"

		if os.path.exists(self.path_fp_lib_table):
			# Read the existing content of fp-lib-table
			with open(self.path_fp_lib_table, "r") as file:
				lines = file.readlines()


			# Find the position of the closing bracket
			closing_bracket_index = None
			for i, line in enumerate(lines):
				if line.strip() == ")":
					closing_bracket_index = i

					break

			# Insert the new entry just before the closing bracket
			if closing_bracket_index is not None:
				lines.insert(closing_bracket_index, entry)

			self.logger.log(logging.INFO, "Inserted into footprint library file")
		else:
			lines = [
				"(fp_lib_table\n",
  				"  (version 7)\n",
				entry + "\n",
				")\n"
			]

			self.logger.log(logging.INFO, "Creating new footprint library file")

		# Write the modified content back to the file
		with open(self.path_fp_lib_table, "w") as file:
			file.writelines(lines)
			file.close()

		# reload footprints not really possible?
		pcbnew.Refresh() # Refresh the user interface

	def _on_save_button_klick(self, event):
		template = self. _handle_coil_generation()

		# if the folder does not exist yet, it should be created and added to
		# the project library path
		if not os.path.exists(self.path_footprint_folder):
			os.makedirs(self.path_footprint_folder)

			self._add_to_fp_lib()

			self.logger.log(logging.INFO, "Created new footprint folder, added to project library")
		else:
			self.logger.log(logging.INFO, "Footprint folder already exists")

		with open(self.path_footprint_folder + get_safe_name(self._parse_data("name")) + ".kicad_mod", "w") as file:
			file.write(template)
			file.close()

	def _on_generate_button_klick(self, event):
		template = self. _handle_coil_generation()

		# copy the generated footprint into clipboard
		clipboard = wx.Clipboard.Get()
		if clipboard.Open():
			self.logger.log(logging.DEBUG, "Adding to clipboard")

			clipboard.SetData(wx.TextDataObject(template))
			clipboard.Close()
		else:                    
			self.logger.log(logging.DEBUG, "Clipboard error")

			return
		
		# paste generated footprint into the pcbview
		try:
			evt = wx.KeyEvent(wx.wxEVT_CHAR_HOOK)
			evt.SetKeyCode(ord('V'))
			evt.SetControlDown(True)
			self.logger.log(logging.INFO, "Using wx.KeyEvent for paste")
	
			wnd = [i for i in self._pcbnew_frame.Children if i.ClassName == 'wxWindow'][0]

			self.logger.log(logging.INFO, "Injecting event: {} into window: {}".format(evt, wnd))
			wx.PostEvent(wnd, evt)
		except:
			# Likely on Linux with old wx python support :(
			self.logger.log(logging.INFO, "Using wx.UIActionSimulator for paste")
			keyinput = wx.UIActionSimulator()
			self._pcbnew_frame.Raise()
			self._pcbnew_frame.SetFocus()
			wx.MilliSleep(100)
			wx.Yield()
			# Press and release CTRL + V
			keyinput.Char(ord("V"), wx.MOD_CONTROL)
			wx.MilliSleep(100)

	def _init_logger(self):
		root = logging.getLogger()
		root.handlers.clear()
		root.setLevel(logging.DEBUG)

		log_file = os.path.join(os.path.dirname(__file__), "dynamic/coilgenerator.log")

		handler = logging.FileHandler(log_file)
		handler.setLevel(logging.DEBUG)

		formatter = logging.Formatter(
			"%(asctime)s %(name)s %(lineno)d:%(message)s", datefmt="%m-%d %H:%M:%S"
		)

		handler.setFormatter(formatter)

		root.addHandler(handler)

def get_safe_name(name, keepcharacters = (' ','.','_')):
    return "".join(c for c in name if c.isalnum() or c in keepcharacters).rstrip()

# use this class to track the last focused page
class FocusTracker(wx.EvtHandler):
	def __init__(self):
		wx.EvtHandler.__init__(self)
		self.prev_focused_window = None

	def OnFocus(self, event):
		self.prev_focused_window = event.GetEventObject()

# Plugin definition
class Plugin(pcbnew.ActionPlugin):
	def __init__(self):
		self.name = "Coil Generator"
		self.category = "Manufacturing"
		self.description = "Toolkit to automatically generate coils for KiCad"
		self.pcbnew_icon_support = hasattr(self, "show_toolbar_button")
		self.show_toolbar_button = True
		self.icon_file_name = os.path.join(os.path.dirname(__file__), 'icon.png')
		self.dark_icon_file_name = os.path.join(os.path.dirname(__file__), 'icon.png')

		self.focus_tracker = FocusTracker()

		# if a window loses focus, this event updates the last focused window
		for window in wx.GetTopLevelWindows():
			window.Bind(wx.EVT_SET_FOCUS, self.focus_tracker.OnFocus)
			
	def Run(self):
		CoilGeneratorUI(self.focus_tracker.prev_focused_window).Show()
