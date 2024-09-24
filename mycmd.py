import cmd
import tkinter as tk
from tkinter import scrolledtext
import sys
import io

class MyCmd(cmd.Cmd):
    prompt = '(mycmd) '

    def __init__(self, ins, outs):
        super().__init__(stdout=outs)

    def do_greet(self, arg):
        '打印问候语:  greet [name]'
        if arg:
            self.stdout.write(f"你好, {arg}!\n")
        else:
            self.stdout.write("你好!\n")

    def do_exit(self, arg):
        '退出程序:  exit'
        self.stdout.write("再见!\n")
        return True

    def do_add(self, arg):
        '计算两个数的和:  add num1 num2'
        try:
            nums = arg.split()
            if len(nums) != 2:
                raise ValueError("需要两个数字")
            num1, num2 = map(float, nums)
            self.stdout.write(f"{num1} + {num2} = {num1 + num2}\n")
        except ValueError as e:
            self.stdout.write(f"错误: {e}\n")

    def do_subtract(self, arg):
        '计算两个数的差:  subtract num1 num2'
        try:
            nums = arg.split()
            if len(nums) != 2:
                raise ValueError("需要两个数字")
            num1, num2 = map(float, nums)
            return f"{num1} - {num2} = {num1 - num2}"
        except ValueError as e:
            return f"错误: {e}"
        
class RedirectText(io.StringIO):
    def __init__(self, text_ctrl):
        super().__init__()
        self.text_ctrl = text_ctrl

    def write(self, string):
        self.text_ctrl.insert(tk.END, string)
        self.text_ctrl.see(tk.END)  # Scroll to the end to show the latest output

class RedirectInput(io.StringIO):
    def __init__(self, input_func):
        super().__init__()
        self.input_func = input_func

    def readline(self, *args):
        return self.input_func()

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("命令行界面")
        self.text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=50, height=20)
        
        # self.text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=50, height=20)
        self.text_area.pack(padx=10, pady=10)
        
        self.entry = tk.Entry(root, width=50)
        self.entry.pack(padx=10, pady=10)
        
        self.button = tk.Button(root, text="执行", command=self.execute_command)
        self.button.pack(padx=10, pady=10)

        self.redirectorI = RedirectInput(self.entry.get)
        self.redirectorO = RedirectText(self.text_area)

        self.text_area.configure(state='normal', font=("Source Code Pro", 11))
        # self.text_area.configure(state='normal')
        self.entry.configure(font=("Source Code Pro", 11))
        self.button.configure(font=("Source Code Pro", 11))

        self.cmd = MyCmd(self.redirectorI, self.redirectorO)

        self.entry.bind('<Return>', lambda event: self.execute_command())
        
    def execute_command(self):
        command = self.entry.get()
        if command:
            self.text_area.insert(tk.END, f"{self.cmd.prompt}{command}\n")
            self.cmd.onecmd(command)
            self.entry.delete(0, tk.END)

if __name__ == '__main__':
    root = tk.Tk()
    app = App(root)
    root.mainloop()