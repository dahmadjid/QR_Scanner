import kivy
from kivy.config import Config
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')
import os, sys
from kivy.resources import resource_add_path, resource_find
from kivy.config import Config
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.core.window import Window
from kivy.utils import get_color_from_hex as hex
from kivy.uix.scrollview import ScrollView
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.uix.popup import Popup
from kivy.graphics.texture import Texture
import cv2
from pyzbar.pyzbar import decode
from functools import partial
import os
import time
import json
from kivy.uix.textinput import TextInput
import socket 
import threading
from kivy.uix.screenmanager import ScreenManager, Screen,FadeTransition,NoTransition
from kivy.uix.filechooser import FileChooserIconView

Window.clearcolor = hex("#eeeeee")
Window.maximize()

def ResizeWithAspectRatio(image, width=None, height=None, inter=cv2.INTER_AREA):
    dim = None
    (h, w) = image.shape[:2]
    d = h-w
    if d >0:
        cv2.transpose(image,image)
    (h, w) = image.shape[:2]
    if width is None and height is None:
        return image
    if width is None:
        r = height / float(h)
        dim = (int(w * r), height)
    else:
        r = width / float(w)
        dim = (width, int(h * r))

    return cv2.resize(image, dim, interpolation=inter)

def removeSpace(string):
    newstring = ''
    for char in string:
        if char != " ":
            newstring = newstring + char
    return newstring

def configNotFound():   #Bool return if config file exists
    config_not_found = False

    if not os.path.exists("config.json"):
        config_not_found = True
    return config_not_found    

    
#c105 com:1 c117 sensors:2 c204 display:3 c206 actuators:4

s1t = 1613806200
s2t = 1613813400
s3t = 1613820600
s4t = 1613824200
    
room_schedule = [['1','2','3','4'],['2','1','4','3'],['3','4','1','2'],['4','3','2','1']] #first index is the session and the second is the room_index and the value is the grp for those specifc session and room index
rooms = ['C105','C117','C204','C206']

def openCSV(csv_file,room_index):
    csv_list = []
    if os.path.exists("attendance_result"+rooms[int(room_index)-1]+".csv") == True:
        with open("attendance_result"+rooms[int(room_index)-1]+".csv",'r') as f:
            for line in f:
                
                if line == '\n':
                    continue
                
                row=line.strip().split(',')
                csv_list.append(row)
    else:
        with open(csv_file,'r') as f:
            for line in f:
                if line == "\n":
                    continue
                row=line.strip().split(',')
                csv_list.append(row)
    return csv_list
def getSession():
    
    with open("config.json") as f:
        config_dict = json.load(f)
        session = int(config_dict["session"])
    return session     
    # current_time = time.time()
    # if current_time < s2t:
    #     return 1
    # elif current_time >= s2t and current_time < s3t:
    #     return 2
    # elif current_time >= s3t and current_time < s4t:
    #     return 3
    # else:
    #     return 4             
      
def getFileAndRoom():
    with open("config.json") as f:
        config_dict = json.load(f)
        room_index = int(config_dict["room"])
        csv_file = config_dict["csvfile"]
    return csv_file,room_index
    
def getCorrectGroupForRoom(r_index):
    
    session = getSession()
    
    print("session: ",session) 
    correct_grp = room_schedule[session-1][int(r_index)-1]
    print("correct group: ", correct_grp)
    return correct_grp

class Widgets():
    def __init__(self):
        self.tab_list = [] 

widgets = Widgets()


def threadedRunServer(instance):
    def runServer():
        print(socket.gethostbyname(socket.gethostname()))
        if sys.platform == "win32":
            os.system("python -m http.server 8080")
        elif sys.platform == "linux":
            os.system("python3 -m http.server 8080")
    thread = threading.Thread(target=runServer)
    thread.daemon = True
    thread.start()    

def tabsWidget(sm):
    def switchScreen(instance,name="QRScanner"):
        sm.current = name
        for tab in widgets.tab_list: 
            if tab.text == name:
                tab.color = hex("#0000ff")
            else:
                tab.color = hex("#000000")    
    grid = GridLayout(cols=1,size_hint=(0.1, 1),pos_hint={'x':0, 'y':0},spacing = 1)
    names = ["QRScanner","Settings"]
    for name in names:
        tab = Button(text=name,background_normal="",background_down="",background_color = hex("#e1e1e1"),color = hex("#212121"),size_hint_y=None,height = Window.height*0.05,font_size = 18)
        print(tab.text)
        if name == "Settings":
            tab.bind(on_press = settingsPopup)
        else:    
            tab.bind(on_press = partial(switchScreen,name=name)) 
         
        widgets.tab_list.append(tab)
        grid.add_widget(tab)
    widgets.tab_list[0].color = hex("#0000ff") 
    return grid

def qrScreen():
    qr = Screen(name="QRScanner")
    qr.add_widget(root())
    return qr
def fileSharingScreen():
    file_sharing =  Screen(name="File Sharing",size_hint=(.76,1),pos_hint={'x':.12, 'y':0})
    flt = FloatLayout(size_hint=(1,1),pos_hint={'x':0, 'y':0})
    back_img = Image(source = "back3k.jpg",size_hint=(1,1),pos_hint = {'x':0,'y':0})
    flt.add_widget(back_img)
    btn = Button(text='Start Server', background_normal=''
            ,background_color = hex("#eeeeee"),color = hex("212121"),size_hint = (0.2,.2),pos_hint={"x":.4,"y":.4})    
    btn.bind(on_release = threadedRunServer)
    flt.add_widget(btn)
    file_sharing.add_widget(flt)
    return file_sharing

def settingsPopup(instance):

    flt = FloatLayout()
    def chooseFile(instance):
        def submit(instance,selection,touch):
            if os.path.splitext(selection[0])[1] == ".csv":

                
                csv_input.select_all()
                csv_input.delete_selection()
                csv_input.insert_text(selection[0])     
                popup4.dismiss()
            else:
                error_lbl2 = Label(text = "Make sure to select a CSV file" ,color = hex("#EEEEEE"),font_size = 18)
                popup5 = Popup(title='Invalid Format', content=error_lbl2,
                size_hint=(0.25,0.15))
                popup5.open()    
        flt = FloatLayout()
        background = Button(text = "",background_disabled_normal='',disabled=True,background_color=hex("212121"),size_hint=(1,1),pos_hint={'x':0, 'y':0})
        filechooser = FileChooserIconView(path = os.getcwd(),size_hint=(1,1),pos_hint={'x':0, 'y':0})
        flt.add_widget(background)
        flt.add_widget(filechooser)
        popup4 = Popup(title='', content=flt,separator_height = 0,
            size_hint=(.8,.8),border = (0,0,0,0))
        popup4.open()
        filechooser.bind(on_submit = submit)
    def confirm(instance):
        if room_input.text in ["1","2","3","4"]:
            config_dict['room'] = room_input.text
        else:
            error_lbl3 = Label(text = "Enter room from 1 to 4" ,color = hex("#EEEEEE"),font_size = 18)
            popup6 = Popup(title='Invalid Room', content=error_lbl3,
            size_hint=(0.25,0.15))
            popup6.open()
            return

        if session_input.text in ["1","2","3","4"]:
            config_dict['session'] = session_input.text     
        else:
            error_lbl = Label(text = "Enter session from 1 to 4" ,color = hex("#EEEEEE"),font_size = 18)
            popup3 = Popup(title='Invalid Session', content=error_lbl,
            size_hint=(0.25,0.15))
            popup3.open()
            return
         
        if os.path.splitext(csv_input.text)[1] == ".csv" and os.path.exists(csv_input.text):
            config_dict["csvfile"] = csv_input.text
        else:
            error_lbl4 = Label(text = "Enter a valid CSV file" ,color = hex("#EEEEEE"),font_size = 18)
            popup7 = Popup(title='Invalid CSV', content=error_lbl4,
            size_hint=(0.25,0.15))
            popup7.open()
            return

        with open("config.json",'w+') as f:
            json.dump(config_dict,f,indent = 1)
        popup2.dismiss()
    print(configNotFound())

    if configNotFound():
        config_dict = {'room': '', 'session': '', 'csvfile': ''}
    else:    
        with open("config.json") as f:
            config_dict = json.load(f)
            print(config_dict)
    
    room_label = Label(text = "Room:",color = hex("#212121"),size_hint=(.2,1),pos_hint={'x':.25, 'y':0},font_size = 18)
    room_input = TextInput(text = config_dict['room'],multiline = False,size_hint=(.03,.6),pos_hint={'x':.40, 'y':0.2})
   
    session_label = Label(text = "Session:",color = hex("#212121"),size_hint=(.3,1),pos_hint={'x':.45, 'y':0},font_size = 18)
    session_input = TextInput(text = config_dict['session'],multiline = False,size_hint=(.03,.6),pos_hint={'x':.65, 'y':.2})

    csv_label = Label(text = "Participants .CSV File:",color = hex("#212121"),size_hint=(.2,1),pos_hint={'x':0.05, 'y':0},font_size = 18)
    csv_input = TextInput(text = config_dict['csvfile'],hint_text = "Path to the CSV File",multiline = False,size_hint=(.5,.6),pos_hint={'x':.25, 'y':.2})
    csv_browse_btn = Button(text='Browse'
            ,background_color = hex("#d1d1d1"),background_normal='',color = hex("#212121"),size_hint=(.2,.6),pos_hint={'x':.75, 'y':0.2})
    csv_browse_btn.bind(on_release = chooseFile)
    csv_flt = FloatLayout(size_hint=(1,.1),pos_hint={'x':0, 'y':0.5})
    csv_flt.add_widget(csv_label)
    csv_flt.add_widget(csv_input)
    csv_flt.add_widget(csv_browse_btn)

    room_session_flt = FloatLayout(size_hint=(1,.1),pos_hint={'x':0, 'y':0.7})
    room_session_flt.add_widget(room_label)
    room_session_flt.add_widget(room_input)
    room_session_flt.add_widget(session_label)
    room_session_flt.add_widget(session_input)
    
    
    popup2 = Popup(title='', content=flt,separator_height = 0,
            size_hint=(.5,.6),border = (0,0,0,0))

    cancel_btn =Button(text='Cancel', background_normal='',background_disabled_normal=''
            ,background_color = hex("#d1d1d1"),color = hex("#212121"),size_hint=(0.24,.1),pos_hint={'x':.25, 'y':0.25})
    if configNotFound():
        popup2.auto_dismiss = False
        cancel_btn.disabled = True
    else:    
        cancel_btn.bind(on_release = popup2.dismiss)
    confirm_btn =Button(text='OK', background_normal=''
            ,background_color = hex("#d1d1d1"),color = hex("#212121"),size_hint=(.24,.1),pos_hint={'x':.51, 'y':0.25})
    confirm_btn.bind(on_release = confirm) 

    background = Button(text = "",background_disabled_normal='',disabled=True,background_color=hex("f1f1f1"),size_hint=(1,1),pos_hint={'x':0, 'y':0})
    flt.add_widget(background)
    flt.add_widget(room_session_flt) 
    flt.add_widget(csv_flt)
    flt.add_widget(cancel_btn)
    flt.add_widget(confirm_btn)
    
    popup2.open()  

    # popup_grid = GridLayout(spacing = 2)
    # popup_grid.col = 1

    
    # room_txt_label = Label(text = "Room: "+str(room_index) ,color = hex("#eeeeee"),size_hint = (1,None),pos_hint = {"x":0,"y":0},font_size = 20)
    # session_flt = FloatLayout()
    # session_txt_label = Label(text = "Session: " ,color = hex("#eeeeee"),size_hint = (0.8,None))
    # session_txt_input = TextInput()
    
    # confirm_btn =Button(text='Confirm', background_normal=''
    #         ,background_color = hex("#eeeeee"),color = hex("#212121"))
    
    # popup_grid.add_widget(room_txt_label)
    # session_flt.add_widget(session_txt_label)
    # session_flt.add_widget(session_txt_input)
    # popup_grid.add_widget(session_flt)
 
    # popup2 = Popup(title='Settings', content=popup_grid,separator_height = 4)
    # popup2.open()


def checkPresence(student_name,csv_list,room_index):
    
    print(repr(student_name))
    i = 0
    for row in csv_list:
        print(row[1] + " " + row[2],print(student_name))
        if removeSpace(row[1] + " " + row[2]).lower() == removeSpace(student_name).lower():
            if row[3] != getCorrectGroupForRoom(room_index):
                session = getSession()
                correct_room_index = room_schedule[session-1][int(row[3])-1]
                correct_room = rooms[int(correct_room_index) -1]
                
                print("wrong grp")
                return (False,correct_room)

        
        if row[1] + " " + row[2] == student_name:
            csv_list[i][int(room_index)+3] = '1'
            return (True,None)
            break
        i += 1

    return ("wtf",None)    

def updateCsv(csv_list,room_index):
    text = ''    
    with open("attendance_result"+rooms[int(room_index)-1]+".csv",'w') as f:
        for row in csv_list:
            for col in row:
                text = text + col +','
            text = text[:-1]
            text = text + '\n'
        f.write(text)
    # try:
    #     with open(os.path.expanduser("~")+"\\"+"attendance_result"+rooms[int(room_index)-1]+".csv",'w') as f:
    #         for row in csv_list:
    #             for col in row:
    #                 text = text + col +','
    #             text = text[:-1]
    #             text = text + '\n'
    #         f.write(text)
    # except:
    #     pass        

def popupOrient(text,correct_grp,correct_room):
    if correct_grp == True:
        presence = "Attendance Confirmed"
        color = hex('#009624')
        y1 =0.50
        y2 =0.40
    elif correct_grp == False:
        color = hex('#ff0000')
        presence = "Wrong Room\n Please proceed to " + correct_room 
        y1 = 0.55 
        y2 = 0.40
    elif correct_grp == "wtf":
        presence = "This name is not in the list"   
        y1 =0.50
        y2 =0.40  
        color = hex("ff0000") 
    popup_flt = FloatLayout()
    popup_bg = Image(source = "back3k.jpg",size_hint=(1,1),pos_hint = {'x':0,'y':0})
    popup_flt.add_widget(popup_bg)
    #btn = Button(text =text,background_disabled_normal='',disabled=True
        #,background_color = hex('#00781c'),color = hex("#ffffff"),size_hint=(0.1,0.1),font_size = 56)

    name_lbl = Label(text =text,color = hex('#000000'),halign = 'center',size_hint = (None,0.1),font_size = 52,pos_hint = {'x': 0.47,'y':y1})
    presence_lbl = Label(text =presence,color = color,halign = 'center',size_hint = (None,0.1),font_size = 52,pos_hint = {'x': 0.47,'y':y2})
    popup_flt.add_widget(name_lbl)
    popup_flt.add_widget(presence_lbl)
    popup = Popup(title='', content=popup_flt,separator_height = 0,
              size_hint=(0.8,0.8),border = (0,0,0,0))
    popup.open()
    Clock.schedule_once(partial(dismissPopup,popup = popup),5) 
        


def root():
    global root_flt
    root_flt = FloatLayout(size_hint=(1,1),pos_hint={'x':0, 'y':0})
    back_img = Image(source = "back3k.jpg",size_hint=(1,1),pos_hint = {'x':0,'y':0})
    logo_img = Image(source = "wameedh.png",size_hint=(0.15,0.15),pos_hint = {'x':0.675,'y':0.05})
    deadline_img = Image(source = "Schlumberger.png",size_hint=(0.2,0.2),pos_hint = {'x':0.150,'y':0.05})
    bootcamp_img = Image(source = "logoBootcamp.png",size_hint=(0.3,0.3),pos_hint = {'x':0.35,'y':0.005})
    root_flt.add_widget(back_img)
    root_flt.add_widget(logo_img)
    root_flt.add_widget(deadline_img)
    root_flt.add_widget(bootcamp_img)
    root_flt.add_widget(camWidget())
    scan_qr_label = Label(text = "Scan your QR Code",size_hint=(None,0.1),pos_hint={'x':0.45, 'y':0.75},font_size = 40)
    scan_qr_img = Image(source = "qr.png",size_hint=(0.45,0.45),pos_hint = {'x':0.275,'y':0.65})
    root_flt.add_widget(scan_qr_img)
    
        
    return root_flt

def camWidget():
    capture = cv2.VideoCapture(0)
    flt = FloatLayout()
    global cam
    cam = KivyCamera(capture=capture, fps=30,size_hint = (1,1))
    flt.add_widget(cam)
    return flt
def dismissPopup(dt,popup):
    popup.dismiss()

                    

            


class KivyCamera(Image):
    def __init__(self, capture, fps, **kwargs):
        super(KivyCamera, self).__init__(**kwargs)
        self.capture = capture
        Clock.schedule_interval(self.update, 1.0 / fps)

    def update(self, dt):
        ret1, frame = self.capture.read()
        
        frame = ResizeWithAspectRatio(frame,width=720)
        
        frame = frame[75:540-75,100:720-100,:]
        data = decode(frame)
        
        if len(data) > 0:
            csv_file,room_index = getFileAndRoom()
            csv_list = openCSV(csv_file,room_index)
            student_name = data[0].data.decode('utf-8')
            ret2,correct_room = checkPresence(student_name,csv_list,room_index) #return: Correct grp True , Wrong Grp False, "wtf" if name is not in the list
            popupOrient(student_name,ret2,correct_room)
            updateCsv(csv_list,room_index)

        if ret1:
            # convert it to texture
            frame = cv2.flip(frame, 1)
            buf1 = cv2.flip(frame, 0)
            buf = buf1.tostring()
            image_texture = Texture.create(
                size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
            image_texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
            # display image from the texture
            self.texture = image_texture


class CamApp(App):
    def build(self):
        top_root = FloatLayout()
        sm = ScreenManager(size_hint=(1,1),pos_hint={'x':0, 'y':0},transition=NoTransition())
        

        qr = qrScreen()
        file_sharing = fileSharingScreen()

        sm.add_widget(qr)
        sm.add_widget(file_sharing)
        
        if configNotFound():
            Clock.schedule_once(partial(settingsPopup),1)
        tabs = tabsWidget(sm)
        top_root.add_widget(sm)
        top_root.add_widget(tabs)
        return top_root

    def on_stop(self):
        #without this, app will not exit even if the window is closed
        cam.capture.release()

if __name__ == '__main__':
    CamApp().run()
    