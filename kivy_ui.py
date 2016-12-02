from random import random
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.clock import Clock

import simple_packet_print
import limit_ports


from kivy.config import Config
Config.set('graphics', 'width', '1000')
Config.set('graphics', 'height', '1000')


from threading import Thread

class PortInfo(BoxLayout):
    def __init__(self, **kwargs):
        super(PortInfo, self).__init__(**kwargs)
        i = kwargs['item']
        self.net_data = i

        self.port_label = Label(text=str(kwargs['port']))
        self.total_label = Label()
        self.raw_speed_label = Label()
        self.speed_label = Label()
        self.add_widget(self.port_label)
        self.add_widget(self.total_label)
        self.add_widget(self.raw_speed_label)
        self.add_widget(self.speed_label)

        self.up_limit = TextInput()
        self.down_limit = TextInput()
        self.enable_limit = ToggleButton(text="limit?")
        self.add_widget(self.up_limit)
        self.add_widget(self.down_limit)
        self.add_widget(self.enable_limit)
    def update(self, v):
        self.net_data = v
        self.speed_label.text = "{:.1f}".format(v['speed']/1000.0)
        self.total_label.text = "{:.1f}".format(v['total']/1000.0)
        self.raw_speed_label.text = "{:.1f}".format(v['speed_raw']/1000.0)

sort_key = 'speed'

class TableHeader(BoxLayout):
    def __init__(self, **kwargs):
        super(TableHeader, self).__init__(**kwargs)

        self.port_label = Button(text="port", on_release=self.set_sort)
        self.port_label.sort_key = "port"
        self.total_label = Button(text="total\nkb", on_release=self.set_sort)
        self.total_label.sort_key = "total"
        self.raw_speed_label = Button(text="raw\nspd kb", on_release=self.set_sort)
        self.raw_speed_label.sort_key = "speed_raw"
        self.speed_label = Button(text="speed\nkb", on_release=self.set_sort)
        self.speed_label.sort_key = "speed"
        self.add_widget(self.port_label)
        self.add_widget(self.total_label)
        self.add_widget(self.raw_speed_label)
        self.add_widget(self.speed_label)

        self.up_limit_label = Label(text="up\nlimit")
        self.down_limit_label = Label(text="down\nlimit")
        self.enable_limit_label = Label(text="enable\nlimit")
        self.add_widget(self.up_limit_label)
        self.add_widget(self.down_limit_label)
        self.add_widget(self.enable_limit_label)

        self.size_hint_y = 0.1
    def set_sort(self, obj):
        global sort_key
        sort_key = obj.sort_key
        print sort_key

def cmp_PI(ix, iy):
    x = ix.net_data[sort_key]
    y = iy.net_data[sort_key]
    if x > y:
        return 1
    elif x == y:
        return 0
    else:  # x < y
        return -1


class MainView(GridLayout):

    def __init__(self, **kwargs):
        kwargs['cols'] = 2
        super(MainView, self).__init__(**kwargs)

        self.main_table = BoxLayout(orientation='vertical')
        self.main_table.add_widget(TableHeader())

        self.main_list = BoxLayout(orientation='vertical')

        self.main_table.add_widget(self.main_list)

        self.add_widget(self.main_table)

        Clock.schedule_interval(self.update_cb, 0.5)

        self.connected_widgets = {}


        self.info_panel = BoxLayout(orientation='vertical')

        clearbtn = Button(text='Apply')
        clearbtn.bind(on_release=self.apply_limits)
        #parent.add_widget(self.painter)
        self.add_widget(self.info_panel)
        self.info_panel.add_widget(Label(text="LinNetLim\n press apply to limit selected ports"))
        self.info_panel.add_widget(clearbtn)

    def apply_limits(self, obj):
        indata = []
        for r in self.main_list.children:
            if r.enable_limit.state == 'down':
                indata.append({
                    "port": int(r.port_label.text),
                    "up_limit": int(r.up_limit.text),
                    "down_limit": int(r.down_limit.text)
                })
        limit_ports.set_from_ports_list(indata)

    def update_cb(self, dt):
        print(dt)
        for k in list(simple_packet_print.portcounts.keys()):
            v = simple_packet_print.portcounts[k]
            w = self.connected_widgets.get(k, None)
            if not w:
                w = PortInfo(port=k,item=v)
                self.connected_widgets[k] = w
                self.main_list.add_widget(w)
            w.update(v)
        self.main_list.children.sort(cmp_PI)



class NetLimitApp(App):

    def build(self):
        parent = MainView()
        self.start_packet_watching()
        self.mainwidget = parent
        return parent
    def start_packet_watching(self):
        t=Thread(
            target=self.launch_watcher,
            kwargs={})
        t.daemon=True
        t.start()
    def launch_watcher(self):
        simple_packet_print.run(max_packets=None)





mainapp = NetLimitApp()



if __name__ == '__main__':
    mainapp.run()
