# todo: document
import wx

from .common_coil_config_panel import CommonCoilConfigPanel
from .footprint_config_panel import FootprintConfigPanel
from .helper import get_default_obj_spacing
from .trace_config_panel import TraceConfigPanel
from .via_diameter_config_panel import ViaDiameterConfigPanel


class CoilGeneratorUI(wx.Frame):
    WINDOW_TITLE: str = "Coil Generator"
    GENERATE_BUTTON_LABEL: str = "Generate Coil"
    SAVE_FOOTPRINT_BUTTON_LABEL: str = " Save as Project Footprint"
    GENERATE_BUTTON_TOOLTIP: str = "Generates the specified coil and pastes it in PCBNew"
    SAVE_FOOTPRINT_BUTTON_TOOLTIP: str = (
        "Generates the specified coil and stores it as a footprint "
        "with the specified footprint name in the project's footprint library"
    )

    def __init__(self, parent):
        # setting window size to fixed
        style = wx.DEFAULT_FRAME_STYLE & ~(wx.RESIZE_BORDER | wx.MAXIMIZE_BOX)
        super().__init__(parent, title=self.WINDOW_TITLE, style=style)

        # generating config panels
        footprint_config = FootprintConfigPanel(self)
        common_config = CommonCoilConfigPanel(self)
        trace_config = TraceConfigPanel(self)
        via_diameter_config = ViaDiameterConfigPanel(self)
        self.config_panels = [footprint_config, common_config, trace_config, via_diameter_config]

        # generating buttons
        self.button_generate = wx.Button(
            self, label=self.GENERATE_BUTTON_LABEL)
        self.button_generate.SetToolTip(self.GENERATE_BUTTON_TOOLTIP)
        self.button_save_footprint = wx.Button(
            self, label=self.SAVE_FOOTPRINT_BUTTON_LABEL)
        self.button_save_footprint.SetToolTip(self.SAVE_FOOTPRINT_BUTTON_TOOLTIP)

        # pushing buttons into layout to stick to edges of window
        button_bar_sizer = wx.BoxSizer(wx.HORIZONTAL)
        button_bar_sizer.Add(self.button_generate, 0,
                             wx.ALL, get_default_obj_spacing())
        button_bar_sizer.AddStretchSpacer(1)
        button_bar_sizer.Add(self.button_save_footprint, 0,
                             wx.ALL, get_default_obj_spacing())

        # ordering config panels below each other followed by buttons
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        for panel in self.config_panels:
            main_sizer.Add(panel, 0, wx.ALL, get_default_obj_spacing())
        main_sizer.Add(button_bar_sizer, 0, wx.EXPAND | wx.ALL, 0)
        self.SetSizer(main_sizer)

        self.Bind(wx.EVT_SHOW, self.__sync_config_column_start_width)
        self.Bind(wx.EVT_BUTTON, self.__generate_callback)
        self.Bind(wx.EVT_BUTTON, self.__save_footprint_callback)

        self.Fit()

    def __sync_config_column_start_width(self, event: wx.Event):
        # todo: catch and log exceptions here. they will not be propagated
        # continue processing event after this handler finishes
        event.Skip()

        # only run size calculation when window transitions to being shown
        # any other events should not be processed
        # also: somehow one had to bind to wx.EVT_SHOW but compare to wx.wxEVT_SHOW
        if event.GetEventType() == wx.wxEVT_SHOW and event.IsShown():
            biggest_column_width = [0, 0, 0]

            # going over every panel to determine the biggest column width
            for panel in self.config_panels:
                current_column_width = panel.get_current_min_row_width()

                for column in range(0, 3):
                    if biggest_column_width[column] < current_column_width[column]:
                        biggest_column_width[column] = current_column_width[column]

            for panel in self.config_panels:
                panel.set_min_column_width(tuple(biggest_column_width))

            self.Fit()

    def __generate_callback(self, event: wx.Event):
        # continue processing event after this handler finishes
        event.Skip()

        # only processing button press events
        if event.GetEventType() == wx.wxEVT_BUTTON:
            # close window
            self.Destroy()

            # todo: generate coil

    def __save_footprint_callback(self, event: wx.Event):
        # continue processing event after this handler finishes
        event.Skip()

        # only processing button press events
        if event.GetEventType() == wx.wxEVT_BUTTON:
            # close window
            self.Destroy()

            # todo: save footprint
