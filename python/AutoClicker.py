
from pywinauto import Application
from pywinauto import Desktop
import psutil
import pyautogui
import time
import cv2
import numpy as np
import base64
import http.server
import ast
import json

class WindowControl :
    def list_windows_names(self) :
        winlist = []
        for window in Desktop(backend="uia").windows() :
            winlist.append(window.window_text())
        return winlist
    
    def list_windows_pid(self) :
        winlist = []
        for window in Desktop(backend="uia").windows() :
            winlist.append(window.process_id())
        return winlist
    
    def find_window_name(self, contains : str) :
        winlist = self.list_windows_names()
        for window in winlist :
            if contains.lower() in window.lower() :
                return window

    def find_process_pids(self,process : str):
        proclist = []
        for proc in psutil.process_iter():
            if proc.name().lower() == process.lower():
                proclist.append(proc.ppid())
        return proclist
    
    def get_process_pid(self, title) :
        proclist = self.find_process_pids(title)
        winlist = self.list_windows_pid()
        common_pid = list(set(proclist).intersection(winlist))

        if common_pid :
            return common_pid[0]
        else :
            return False

    def move_window(self,window_name,position):
        if position == "front" :
            Application().connect(title=window_name,found_index=0).window(title=window_name,found_index=0).set_focus()
        elif position == "back" :
            Application().connect(title=window_name,found_index=0).window(title=window_name,found_index=0).minimize()
        
    def move_process(self,pid,position):
        if position == "front" :
            Application().connect(process = pid).window().set_focus()
        elif position == "back" :
            Application().connect(process = pid).window().minimize()

    def clic(self,coord,double):
        if coord :
            x,y = coord
            pyautogui.moveTo(x,y)
            time.sleep(0.2)
            if double :
                pyautogui.doubleClick()
            else :
                pyautogui.click()
            
    def write(self, text) :
        pyautogui.write(text,interval=0.1)
        
    def press_key(self, key) :
        pyautogui.press(key)
    
    def press_hotkey(self, keys) :
        pyautogui.hotkey(keys)

wincontrol = WindowControl()

def locate_from_base64(base64_image, threshold = 0.8):
        encoded_data = base64_image.split(',')[1]
        decoded_data = base64.b64decode(encoded_data)
        np_array = np.frombuffer(decoded_data, np.uint8)

        screenshot = cv2.cvtColor(np.array(pyautogui.screenshot()),cv2.COLOR_RGB2GRAY)
        element = cv2.imdecode(np_array, cv2.IMREAD_GRAYSCALE)

        w, h = element.shape[::-1]
        res = cv2.matchTemplate(element,screenshot,cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        if(max_val >= threshold):
            return((max_loc[0]+w/2, max_loc[1]+h/2))
        else :
            return False
        
class RequestHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):

        if '/list_windows' in self.path :
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(str(wincontrol.list_windows_names()).encode())   

        if '/screenshot' in self.path :
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            img = np.array(pyautogui.screenshot())
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR )
            _, img = cv2.imencode('.jpg', img)
            img = img.tobytes()
            img = base64.b64encode(img)
            self.wfile.write(img)  

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')

        if '/find_base64' in self.path :
            loc = locate_from_base64(post_data)
            if loc :
               self.send_response(200)
               self.send_header('Content-type', 'text/plain')
               self.end_headers()
               self.wfile.write(str(loc).encode())    
            else :
                self.send_response(400)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(b'Button not found')  

        if '/move_window' in self.path :
            payload = json.loads(post_data)
            print(payload)
            result = False

            if 'mode' not in payload :
                self.send_response(400)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(b'"mode" key is missing')  
                return
            
            if 'window' not in payload :
                self.send_response(400)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(b'"window" key is missing')  
                return

            if payload['mode']== "name" :
                result = wincontrol.find_window_name(payload['window'])
                if result :
                    wincontrol.move_window(result,'front')
            if payload['mode']== "process" :
               result = wincontrol.get_process_pid(payload['window'])
               if result :
                wincontrol.move_process(result,'front')
            if result :
               self.send_response(200)
               self.send_header('Content-type', 'text/plain')
               self.end_headers()
               self.wfile.write(b'Window moved to front')    
            else :
                self.send_response(404)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(b'Window not found') 
        
        if  '/clic' in self.path :
            if post_data :
                pos = ast.literal_eval(post_data)
                wincontrol.clic(pos, double=False)

                self.send_response(200)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(b'Clicked at : ')
                self.wfile.write(str(pos).encode())
            else :
                self.send_response(400)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(b'Coordinates are missing')
        
        if  '/double_clic' in self.path :
            if post_data :
                pos = ast.literal_eval(post_data)
                wincontrol.clic(pos, double=True)

                self.send_response(200)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(b'Doubled clicked at : ')
                self.wfile.write(str(pos).encode())
            else :
                self.send_response(400)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(b'Coordinates are missing')

        if '/write' in self.path :
            wincontrol.write(post_data)
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Success')
        
        if '/press_key' in self.path :
            key = post_data
            if '[' in post_data :
                key = ast.literal_eval(post_data)
            wincontrol.press_key(key)
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Success')

        if '/press_hotkey' in self.path :
            keys = ast.literal_eval(post_data)
            wincontrol.press_hotkey(keys)
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Success')

host = ''
port = 8000
httpd = http.server.HTTPServer((host, port), RequestHandler)
httpd.serve_forever()



