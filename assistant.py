import io
import cmd
import time
import utils
import tkinter as tk

from multiprocessing import Queue
from tkinter import scrolledtext


class Assistant(cmd.Cmd):
    def __init__(self, stdout, queue1, queue2, prompt='(user) ', intro='欢迎使用合成校徽辅助命令行界面', parent=None):
        super().__init__(stdout=stdout)
        self.parent = parent
        self.prompt = prompt
        self.send_queue = queue1
        self.receive_queue = queue2
        self.intro = intro

    def do_pause(self, arg):
        '暂停游戏'
        self.send_queue.put('pause')
        self.stdout.write('游戏已暂停\n')
    
    def do_resume(self, arg):
        '恢复游戏'
        self.send_queue.put('resume')
        self.stdout.write('游戏已恢复\n')
    
    def do_exit(self, arg):
        '处理退出游戏的命令。如果参数是 cmd，它将然后退出当前命令行。无参数以及其他参数将退出游戏。'
        params = arg.split()
        if len(params) == 1 and params[0] == 'cmd':
            self.stdout.write('即将退出......\n')
            self.parent.root.update()
            
            time.sleep(1.5)
            self.parent.root.quit()
        else:
            self.send_queue.put('exit')
            self.stdout.write('游戏已退出\n')
    
    def do_save(self, arg):
        '保存当前游戏'
        self.send_queue.put('save')
        self.stdout.write('游戏已保存\n')
    
    def do_load(self, arg):
        '加载游戏'
        if len(arg) == 0:
            self.stdout.write('请提供一个存档名\n')
        self.send_queue.put('load')
        self.send_queue.put(arg)
        self.stdout.write('游戏已加载\n')
    
    def do_detect_save(self, arg):
        '检测存档'
        self.send_queue.put('detect_save')
        self.stdout.write('存档检测中......\n')

        saves = self.receive_queue.get()
        if len(saves) == 0:
            self.stdout.write('没有存档\n')
            return
        else:
            saves = ' '.join(saves)

        self.stdout.write(saves + '\n')
    
    def do_login(self, arg):
        '登录'
        if len(arg) == 0:
            self.stdout.write('请提供一个用户名\n')
            return
        


class RedirectText(io.StringIO):
    def __init__(self, text_ctrl):
        super().__init__()
        self.text_ctrl = text_ctrl

    def write(self, string):
        self.text_ctrl.insert(tk.END, string)
        self.text_ctrl.see(tk.END)

class App:
    def __init__(self, root, queue1, queue2):
        self.root: tk.Tk = root

        self.root.geometry('300x600+100+100')
        
        self.root.title("命令行界面")
        self.text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=50, height=25)
        self.text_area.pack(padx=10, pady=10)
        
        self.entry = tk.Entry(root, width=50)
        self.entry.pack(padx=10, pady=10)
        
        self.button = tk.Button(root, text="执行", command=self.execute_command)
        self.button.pack(padx=10, pady=10)

        self.redirectorO = RedirectText(self.text_area)

        self.text_area.configure(state='normal', font=("Source Code Pro", 11), bg='black', fg='white')
        # self.text_area.configure(state='normal')
        self.entry.configure(font=("Source Code Pro", 11))
        self.button.configure(font=("Source Code Pro", 11))

        self.cmd = Assistant(self.redirectorO, queue1, queue2, parent=self)

        self.entry.bind('<Return>', lambda event: self.execute_command())

    def execute_command(self):
        command = self.entry.get()
        if command:
            self.text_area.insert(tk.END, f"{self.cmd.prompt}{command}\n")
            self.cmd.onecmd(command)
            self.entry.delete(0, tk.END)

def run(queue1: Queue, queue2: Queue):
    app = App(tk.Tk(), queue1, queue2)
    app.root.mainloop()
