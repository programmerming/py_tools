#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk
import json
import os
import sys
import winreg
import pathlib

class TaskTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("任务追踪器")
        self.root.geometry("500x400")
        self.root.attributes('-topmost', True)  # 窗口置顶
        self.root.attributes('-alpha', 0.8)  # 初始透明度80%
        self.root.resizable(False, False)  # 禁止调整窗口大小
        
        # 数据文件路径
        self.data_file = "tasks.json"
        
        # 任务数据结构：{任务ID: {"name": 任务名称, "progress": 进度值}}
        self.tasks = {}
        self.current_task_id = None
        self.next_task_id = 1
        self.startup_enabled = tk.BooleanVar(value=False)
        
        # 变量
        self.task_var = tk.StringVar(value="当前任务")
        self.progress_var = tk.DoubleVar(value=0)
        self.alpha_var = tk.DoubleVar(value=80)
        
        # 创建界面组件
        self.create_widgets()
        
        # 绑定窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # 读取保存的数据
        self.load_data()
    
    def create_widgets(self):
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建左右分栏
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 10))
        
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 左侧：任务列表
        task_list_label = ttk.Label(left_frame, text="任务列表:")
        task_list_label.pack(anchor=tk.W, pady=(5, 0))
        
        # 任务列表框
        self.task_listbox = tk.Listbox(left_frame, width=20, height=15, selectmode=tk.SINGLE)
        self.task_listbox.pack(fill=tk.BOTH, expand=True, pady=5)
        self.task_listbox.bind('<<ListboxSelect>>', self.on_task_select)
        
        # 任务操作按钮
        button_frame = ttk.Frame(left_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        add_button = ttk.Button(button_frame, text="添加任务", command=self.add_task)
        add_button.pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        
        delete_button = ttk.Button(button_frame, text="删除任务", command=self.delete_task)
        delete_button.pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        
        # 右侧：任务详情
        # 任务名称
        task_label = ttk.Label(right_frame, text="任务名称:")
        task_label.pack(anchor=tk.W, pady=(5, 0))
        
        task_entry = ttk.Entry(right_frame, textvariable=self.task_var, width=40)
        task_entry.pack(fill=tk.X, pady=5)
        task_entry.bind('<KeyRelease>', self.update_task_name)
        
        # 进度显示
        progress_label = ttk.Label(right_frame, text="任务进度:")
        progress_label.pack(anchor=tk.W, pady=(5, 0))
        
        # 进度条
        progress_bar = ttk.Progressbar(right_frame, variable=self.progress_var, maximum=100, length=250)
        progress_bar.pack(fill=tk.X, pady=5)
        
        # 进度值显示
        self.progress_value_label = ttk.Label(right_frame, text="0%")
        self.progress_value_label.pack(anchor=tk.CENTER, pady=2)
        
        # 进度调节滑块
        progress_scale = ttk.Scale(right_frame, from_=0, to=100, variable=self.progress_var, 
                                  orient=tk.HORIZONTAL, length=250, command=self.update_progress)
        progress_scale.pack(fill=tk.X, pady=5)
        
        # 透明度调节
        alpha_label = ttk.Label(right_frame, text="窗口透明度:")
        alpha_label.pack(anchor=tk.W, pady=(5, 0))
        
        alpha_scale = ttk.Scale(right_frame, from_=10, to=100, variable=self.alpha_var, 
                               orient=tk.HORIZONTAL, length=250, command=self.update_alpha)
        alpha_scale.pack(fill=tk.X, pady=5)
        
        # 透明度值显示
        self.alpha_value_label = ttk.Label(right_frame, text="80%")
        self.alpha_value_label.pack(anchor=tk.CENTER, pady=2)
        
        # 自启动设置
        startup_frame = ttk.Frame(right_frame)
        startup_frame.pack(fill=tk.X, pady=(15, 0))
        
        startup_checkbox = ttk.Checkbutton(startup_frame, text="Windows启动时自动运行", 
                                         variable=self.startup_enabled, command=self.toggle_startup)
        startup_checkbox.pack(anchor=tk.W)
    
    def add_task(self):
        # 添加新任务
        task_id = self.next_task_id
        self.next_task_id += 1
        
        # 默认任务名称
        task_name = f"任务 {task_id}"
        
        # 添加到任务字典
        self.tasks[task_id] = {"name": task_name, "progress": 0}
        
        # 添加到列表框
        self.task_listbox.insert(tk.END, task_name)
        
        # 选择新添加的任务
        self.task_listbox.selection_clear(0, tk.END)
        self.task_listbox.selection_set(tk.END)
        self.on_task_select(None)
    
    def delete_task(self):
        # 删除选中的任务
        selected_index = self.task_listbox.curselection()
        if not selected_index:
            return
        
        # 获取任务ID
        task_id = list(self.tasks.keys())[selected_index[0]]
        
        # 从字典中删除
        del self.tasks[task_id]
        
        # 从列表框中删除
        self.task_listbox.delete(selected_index)
        
        # 如果删除的是当前任务，选择第一个任务
        if self.current_task_id == task_id:
            if self.task_listbox.size() > 0:
                self.task_listbox.selection_set(0)
                self.on_task_select(None)
            else:
                # 如果没有任务了，添加一个新任务
                self.add_task()
    
    def on_task_select(self, event):
        # 当选择任务时更新界面
        selected_index = self.task_listbox.curselection()
        if not selected_index:
            return
        
        # 获取任务ID
        task_id = list(self.tasks.keys())[selected_index[0]]
        self.current_task_id = task_id
        
        # 获取任务数据
        task = self.tasks[task_id]
        
        # 更新界面
        self.task_var.set(task["name"])
        self.progress_var.set(task["progress"])
        self.progress_value_label.config(text=f"{int(task['progress'])}%")
    
    def update_task_name(self, event):
        # 更新任务名称
        selected_index = self.task_listbox.curselection()
        if not selected_index:
            return
        
        # 获取任务ID
        task_id = list(self.tasks.keys())[selected_index[0]]
        
        # 获取新名称
        new_name = self.task_var.get()
        
        # 更新任务字典
        self.tasks[task_id]["name"] = new_name
        
        # 更新列表框
        self.task_listbox.delete(selected_index)
        self.task_listbox.insert(selected_index, new_name)
        self.task_listbox.selection_set(selected_index)
        
        # 保持输入框焦点和光标位置，提升用户体验
        event.widget.focus_set()
        cursor_pos = event.widget.index(tk.INSERT)
        event.widget.icursor(cursor_pos)
    
    def update_progress(self, value):
        # 更新进度值显示和任务数据
        progress = float(value)
        self.progress_value_label.config(text=f"{int(progress)}%")
        
        # 更新任务字典
        if self.current_task_id is not None:
            self.tasks[self.current_task_id]["progress"] = progress
    
    def update_alpha(self, value):
        # 更新窗口透明度和显示值
        alpha = float(value) / 100
        self.root.attributes('-alpha', alpha)
        self.alpha_value_label.config(text=f"{int(float(value))}%")
    
    def save_data(self):
        # 保存任务数据到JSON文件
        data = {
            "tasks": self.tasks,
            "next_task_id": self.next_task_id,
            "startup_enabled": self.startup_enabled.get()
        }
        
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load_data(self):
        # 从JSON文件读取任务数据
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    
                # 恢复任务数据
                if "tasks" in data:
                    self.tasks = data["tasks"]
                    
                    # 恢复列表框
                    self.task_listbox.delete(0, tk.END)
                    for task_id, task in self.tasks.items():
                        # 确保任务ID为整数
                        task_id = int(task_id)
                        self.task_listbox.insert(tk.END, task["name"])
                    
                    # 更新下一个任务ID
                    if "next_task_id" in data:
                        self.next_task_id = data["next_task_id"]
                    else:
                        # 如果没有next_task_id，使用当前最大ID+1
                        if self.tasks:
                            max_id = max(int(task_id) for task_id in self.tasks.keys())
                            self.next_task_id = max_id + 1
                    
                    # 选择第一个任务
                    if self.task_listbox.size() > 0:
                        self.task_listbox.selection_set(0)
                        self.on_task_select(None)
                    else:
                        # 如果没有任务，添加一个初始任务
                        self.add_task()
                
                # 恢复自启动设置
                if "startup_enabled" in data:
                    self.startup_enabled.set(data["startup_enabled"])
                else:
                    # 默认关闭自启动
                    self.startup_enabled.set(False)
                    
                # 应用自启动设置到注册表
                self.update_startup_registry()
            except (json.JSONDecodeError, IOError) as e:
                print(f"读取数据失败: {e}")
                # 如果读取失败，添加一个初始任务
                self.add_task()
        else:
            # 如果文件不存在，添加一个初始任务
            self.add_task()
            # 设置默认自启动状态
            self.startup_enabled.set(False)
    
    def toggle_startup(self):
        # 切换自启动设置
        self.update_startup_registry()
        self.save_data()
    
    def check_startup_status(self):
        # 检查注册表中的自启动状态
        try:
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ) as key:
                # 尝试获取TaskTracker的自启动项
                try:
                    value = winreg.QueryValueEx(key, "TaskTracker")[0]
                    self.startup_enabled.set(True)
                except FileNotFoundError:
                    self.startup_enabled.set(False)
        except Exception as e:
            print(f"检查自启动状态失败: {e}")
            self.startup_enabled.set(False)
    
    def update_startup_registry(self):
        # 更新Windows注册表中的自启动项
        try:
            # 获取当前脚本的完整路径
            script_path = pathlib.Path(sys.argv[0]).resolve()
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            
            if self.startup_enabled.get():
                # 添加自启动项
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
                    winreg.SetValueEx(key, "TaskTracker", 0, winreg.REG_SZ, f'"{script_path}"')
            else:
                # 删除自启动项
                try:
                    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS) as key:
                        winreg.DeleteValue(key, "TaskTracker")
                except FileNotFoundError:
                    # 如果键不存在，忽略错误
                    pass
        except Exception as e:
            print(f"自启动设置失败: {e}")
    
    def on_close(self):
        # 关闭窗口时保存数据
        self.save_data()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = TaskTracker(root)
    root.mainloop()