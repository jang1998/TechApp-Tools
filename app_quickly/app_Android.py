import tkinter as tk
from tkinter import filedialog, scrolledtext, Button, Label, StringVar, Text, messagebox
import subprocess
import threading
import os
import re
import sys
import time

class APKCommandTool:
    def __init__(self, root):
        self.root = root
        self.root.title("APK命令工具")
        self.root.geometry("900x700")
        self.root.configure(padx=10, pady=10)
        
        # 设置字体，确保中文显示正常
        self.font = ('SimHei', 10)
        
        # 变量存储APK路径和包名
        self.apk_path = StringVar()
        self.package_name = StringVar()
        self.target_server = StringVar(value="your_target_server")
        self.process_name = StringVar(value="your_process")
        
        # 命令执行状态
        self.log_collecting = False
        self.log_process = None
        self.screen_recording = False  # 录屏状态
        self.active_processes = []  # 跟踪所有活跃进程
        self.screen_record_process = None  # 单独跟踪录屏进程
        
        # AAPT工具路径
        self.aapt_path = "C:/Users/BCTC/AppData/Local/Programs/Python/Python311/Lib/site-packages/drozer/lib/aapt.exe"
        
        # 创建日志显示区域（需要先于append_log调用）
        self.log_text = scrolledtext.ScrolledText(self.root, width=80, height=20, font=self.font)
        
        # 尝试检测系统默认编码
        self.system_encoding = sys.getdefaultencoding()
        self.append_log(f"系统默认编码: {self.system_encoding}")
        
        # 创建界面组件
        self.create_widgets()

        Button(self.drozer_frame, text="启动drozer控制台", command=self.start_drozer_console, font=self.font, width=15).pack(side="left", padx=2)
    # 先定义append_log方法，确保在__init__中可以调用
    def start_drozer_console(self):
        """启动drozer控制台并支持交互式命令输入"""
        # 先执行端口转发
        forward_cmd = "adb forward tcp:31415 tcp:31415"
        self.append_log(f"执行命令: {forward_cmd}")
        
        # 启动drozer控制台进程
        try:
            # 创建专门的drozer命令窗口
            drozer_window = tk.Toplevel(self.root)
            drozer_window.title("Drozer 控制台")
            drozer_window.geometry("800x600")
            
            # 日志显示区域
            log_frame = tk.Frame(drozer_window)
            log_frame.pack(fill="both", expand=True, padx=5, pady=5)
            
            tk.Label(log_frame, text="Drozer 输出:", font=self.font).pack(anchor="w")
            drozer_log = scrolledtext.ScrolledText(log_frame, font=self.font)
            drozer_log.pack(fill="both", expand=True)
            
            # 命令输入区域
            input_frame = tk.Frame(drozer_window)
            input_frame.pack(fill="x", padx=5, pady=5)
            
            tk.Label(input_frame, text="输入命令:", font=self.font).pack(side="left")
            cmd_entry = tk.Entry(input_frame, font=self.font)
            cmd_entry.pack(side="left", fill="x", expand=True, padx=5)
            
            # 启动drozer进程
            self.drozer_process = subprocess.Popen(
                "drozer console connect",
                shell=True,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            self.active_processes.append(self.drozer_process)
            
            # 实时读取输出
            def read_output():
                while self.drozer_process.poll() is None:
                    line = self.drozer_process.stdout.readline()
                    if line:
                        drozer_log.insert(tk.END, line)
                        drozer_log.see(tk.END)
                drozer_log.insert(tk.END, "Drozer 控制台已退出")
            
            # 启动输出读取线程
            threading.Thread(target=read_output, daemon=True).start()
            
            # 命令发送函数
            def send_command(event=None):
                cmd = cmd_entry.get().strip()
                if cmd and self.drozer_process.poll() is None:
                    drozer_log.insert(tk.END, f"> {cmd}\n")
                    self.drozer_process.stdin.write(cmd + "\n")
                    self.drozer_process.stdin.flush()
                    cmd_entry.delete(0, tk.END)
            
            # 绑定回车发送命令
            cmd_entry.bind("<Return>", send_command)
            tk.Button(input_frame, text="发送", command=send_command, font=self.font).pack(side="left", padx=5)
            
            # 窗口关闭时终止进程
            def on_close():
                if self.drozer_process and self.drozer_process.poll() is None:
                    self.drozer_process.terminate()
                    if self.drozer_process in self.active_processes:
                        self.active_processes.remove(self.drozer_process)
                drozer_window.destroy()
            
            drozer_window.protocol("WM_DELETE_WINDOW", on_close)
            
        except Exception as e:
            self.append_log(f"启动drozer控制台失败: {str(e)}")
            messagebox.showerror("错误", f"启动drozer控制台失败:\n{str(e)}")

    def append_log(self, text):
        """向日志区域添加内容，确保在主线程执行"""
        def update():
            self.log_text.insert(tk.END, text + "\n")
            self.log_text.see(tk.END)
        self.root.after(0, update)  # 确保UI操作在主线程
    
    def create_widgets(self):
        # 第一行：APK文件选择
        row = 0
        Label(self.root, text="APK文件路径:", font=self.font).grid(row=row, column=0, padx=5, pady=5, sticky="w")
        self.apk_entry = tk.Entry(self.root, textvariable=self.apk_path, width=60, font=self.font)
        self.apk_entry.grid(row=row, column=1, padx=5, pady=5)
        Button(self.root, text="浏览", command=self.browse_apk, font=self.font).grid(row=row, column=2, padx=5, pady=5)
        
        # 第二行：包名输入（自动填充）
        row += 1
        Label(self.root, text="应用包名:", font=self.font).grid(row=row, column=0, padx=5, pady=5, sticky="w")
        self.package_entry = tk.Entry(self.root, textvariable=self.package_name, width=60, font=self.font)
        self.package_entry.grid(row=row, column=1, padx=5, pady=5)
        
        # 第三行：目标服务器和进程名
        row += 1
        Label(self.root, text="目标服务器:", font=self.font).grid(row=row, column=0, padx=5, pady=5, sticky="w")
        tk.Entry(self.root, textvariable=self.target_server, width=30, font=self.font).grid(row=row, column=1, padx=5, pady=5, sticky="w")
        
        Label(self.root, text="进程名:", font=self.font).grid(row=row, column=1, padx=5, pady=5, sticky="e")
        tk.Entry(self.root, textvariable=self.process_name, width=25, font=self.font).grid(row=row, column=2, padx=5, pady=5, sticky="w")
        
        # 工具分类按钮区域 - ADB工具
        row += 1
        Label(self.root, text="ADB工具命令:", font=self.font, fg="green").grid(row=row, column=0, padx=5, pady=5, sticky="w")
        self.adb_frame = tk.Frame(self.root)
        self.adb_frame.grid(row=row, column=1, columnspan=2, padx=5, pady=5, sticky="we")
        
        Button(self.adb_frame, text="截图", command=self.take_screenshot, font=self.font, width=10).pack(side="left", padx=2)
        Button(self.adb_frame, text="开始录屏", command=self.start_screen_record, font=self.font, width=10).pack(side="left", padx=2)
        Button(self.adb_frame, text="停止录屏", command=self.stop_screen_record, font=self.font, width=10).pack(side="left", padx=2)
        Button(self.adb_frame, text="查看目录权限", command=self.show_directory_permissions, font=self.font, width=12).pack(side="left", padx=2)
        Button(self.adb_frame, text="日志收集", command=self.toggle_log_collect, font=self.font, width=10).pack(side="left", padx=2)
        
        # 工具分类按钮区域 - Drozer工具
        row += 1
        Label(self.root, text="Drozer工具命令:", font=self.font, fg="green").grid(row=row, column=0, padx=5, pady=5, sticky="w")
        self.drozer_frame = tk.Frame(self.root)
        self.drozer_frame.grid(row=row, column=1, columnspan=2, padx=5, pady=5, sticky="we")
        
        Button(self.drozer_frame, text="接口安全检测", command=self.show_interface_security, font=self.font, width=15).pack(side="left", padx=2)
        Button(self.drozer_frame, text="组件信息查询", command=self.show_component_info, font=self.font, width=15).pack(side="left", padx=2)
        
        # 工具分类按钮区域 - 其他工具
        row += 1
        Label(self.root, text="其他工具命令:", font=self.font, fg="green").grid(row=row, column=0, padx=5, pady=5, sticky="w")
        self.other_frame = tk.Frame(self.root)
        self.other_frame.grid(row=row, column=1, columnspan=2, padx=5, pady=5, sticky="we")

        # 替换原"抗攻击检测"按钮为以下两个
        Button(self.other_frame, text="查看签名", command=self.show_signature, font=self.font, width=15).pack(side="left", padx=2)
        Button(self.other_frame, text="前端劫持", command=self.show_frontend_hijack, font=self.font, width=15).pack(side="left", padx=2)
        Button(self.other_frame, text="数据防窃取检测", command=self.show_data_anti_steal, font=self.font, width=15).pack(side="left", padx=2)
        Button(self.other_frame, text="通讯安全检测", command=self.show_communication_security, font=self.font, width=15).pack(side="left", padx=2)
        Button(self.other_frame, text="清空命令框", command=self.clear_command, font=self.font, width=10).pack(side="left", padx=2)

        # 命令输入区域
        row += 1
        Label(self.root, text="命令输入:", font=self.font).grid(row=row, column=0, padx=5, pady=5, sticky="nw")
        self.command_text = Text(self.root, height=5, width=80, font=self.font)
        self.command_text.grid(row=row, column=1, columnspan=2, padx=5, pady=5, sticky="we")
        
        # 命令执行按钮
        row += 1
        self.cmd_btn_frame = tk.Frame(self.root)
        self.cmd_btn_frame.grid(row=row, column=0, columnspan=3, padx=5, pady=5)
        
        Button(self.cmd_btn_frame, text="执行命令", command=self.execute_command, font=self.font, bg="#4CAF50", fg="white").pack(side="left", padx=10)
        Button(self.cmd_btn_frame, text="终止所有进程", command=self.terminate_all_processes, font=self.font, bg="#ff9800", fg="white").pack(side="left", padx=10)
        
        # 状态标签
        self.status_var = StringVar(value="就绪")
        Label(self.root, textvariable=self.status_var, font=self.font, fg="blue").grid(row=row, column=2, padx=5, pady=5, sticky="e")
        
        # 日志显示区域
        row += 1
        Label(self.root, text="输出日志:", font=self.font).grid(row=row, column=0, padx=5, pady=5, sticky="nw")
        self.log_text.grid(row=row, column=1, columnspan=2, padx=5, pady=5, sticky="nsew")
        
        # 设置网格权重，使日志区域可拉伸
        self.root.grid_rowconfigure(row, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
    
    def browse_apk(self):
        """浏览并选择APK文件，然后自动提取包名"""
        file_path = filedialog.askopenfilename(filetypes=[("APK文件", "*.apk")])
        if file_path:
            self.apk_path.set(file_path)
            self.status_var.set("正在提取包名...")
            # 在单独线程中提取包名，避免界面冻结
            thread = threading.Thread(target=self.extract_package_name, args=(file_path,))
            thread.daemon = True
            thread.start()
    
    def extract_package_name(self, apk_path):
        """使用aapt工具提取APK的包名，修复编码问题"""
        self.append_log(f"正在提取APK包名: {apk_path}")
        self.append_log(f"使用AAPT工具路径: {self.aapt_path}")
        
        try:
            # 检查aapt工具是否存在
            if not os.path.exists(self.aapt_path):
                error_msg = f"AAPT工具不存在于指定路径: {self.aapt_path}"
                self.append_log(error_msg)
                self.root.after(0, lambda: messagebox.showerror("文件不存在", error_msg))
                self.status_var.set("就绪")
                return
            
            # 检查APK文件是否存在
            if not os.path.exists(apk_path):
                error_msg = f"APK文件不存在: {apk_path}"
                self.append_log(error_msg)
                self.root.after(0, lambda: messagebox.showerror("文件不存在", error_msg))
                self.status_var.set("就绪")
                return
            
            # 构建命令
            cmd = f'"{self.aapt_path}" dump badging "{apk_path}"'
            self.append_log(f"执行命令: {cmd}")
            
            # 执行命令，以字节流方式读取输出，避免编码问题
            process = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=0  # 无缓冲
            )
            
            self.active_processes.append(process)
            
            # 实时读取输出，处理编码问题
            output = []
            encodings_to_try = ['utf-8', 'gbk', 'cp936', 'iso-8859-1']  # 尝试多种编码
            
            while True:
                # 读取字节流
                byte_line = process.stdout.readline()
                if not byte_line and process.poll() is not None:
                    break
                
                if byte_line:
                    # 尝试多种编码解码
                    decoded_line = None
                    for encoding in encodings_to_try:
                        try:
                            decoded_line = byte_line.decode(encoding)
                            break
                        except UnicodeDecodeError:
                            continue
                    
                    # 如果所有编码都失败，使用替换错误模式
                    if decoded_line is None:
                        decoded_line = byte_line.decode('utf-8', errors='replace')
                        self.append_log(f"警告：无法完全解码字节序列 {byte_line.hex()}，已替换不可识别字符")
                    
                    stripped_line = decoded_line.strip()
                    output.append(stripped_line)
                    self.append_log(stripped_line)
            
            # 从输出中解析包名
            full_output = "\n".join(output)
            match = re.search(r"package: name='([^']+)'", full_output)
            if match:
                package_name = match.group(1)
                self.package_name.set(package_name)
                self.append_log(f"成功提取包名: {package_name}")
                self.status_var.set("就绪")
            else:
                self.append_log("无法从APK中找到包名")
                self.append_log(f"AAPT输出: {full_output[:500]}...")
                self.root.after(0, lambda: messagebox.warning("解析失败", "无法从APK输出中识别包名"))
                self.status_var.set("就绪")
                
        except Exception as e:
            self.append_log(f"提取包名时发生错误: {str(e)}")
            self.root.after(0, lambda: messagebox.showerror("错误", f"提取包名时发生错误:\n{str(e)}"))
            self.status_var.set("就绪")
        finally:
            # 移除进程
            if 'process' in locals() and process in self.active_processes:
                self.active_processes.remove(process)
    
    def run_command(self, cmd):
        """在新线程中执行命令，处理编码问题（修复录屏进程终止逻辑）"""
        self.root.after(0, lambda: self.status_var.set(f"正在执行命令..."))
        self.append_log(f"执行命令: {cmd}")
        
        try:
            # 执行命令，以字节流方式读取输出
            process = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=0  # 无缓冲
            )
            
            # 关键：如果是录屏命令，单独记录进程，不加入通用active_processes（避免被强制终止）
            if "screenrecord" in cmd:
                self.screen_record_process = process
            else:
                self.active_processes.append(process)
            
            # 实时读取输出，处理编码
            encodings_to_try = ['utf-8', 'gbk', 'cp936', 'iso-8859-1']
            
            while True:
                byte_line = process.stdout.readline()
                if not byte_line and process.poll() is not None:
                    break
                
                if byte_line:
                    # 尝试多种编码解码
                    decoded_line = None
                    for encoding in encodings_to_try:
                        try:
                            decoded_line = byte_line.decode(encoding)
                            break
                        except UnicodeDecodeError:
                            continue
                    
                    if decoded_line is None:
                        decoded_line = byte_line.decode('utf-8', errors='replace')
                        self.append_log(f"警告：无法完全解码字节序列 {byte_line.hex()}")
                    
                    self.append_log(decoded_line.strip())
                
                # 检查日志收集是否已停止（仅处理日志进程）
                if "logcat" in cmd and not self.log_collecting:
                    process.terminate()
                    break
                # 检查录屏是否已停止（仅处理录屏进程，且不主动终止，等待优雅关闭）
                if "screenrecord" in cmd and not self.screen_recording:
                    break  # 仅退出循环，不强制终止，让系统处理数据写入
            
            # 检查返回代码（录屏进程正常退出码为0，强制终止为1）
            return_code = process.poll()
            if return_code != 0:
                # 排除录屏优雅终止的情况（手动停止时返回码可能非0，但文件正常）
                if "screenrecord" not in cmd or (self.screen_recording and return_code != 0):
                    self.append_log(f"命令执行完毕，返回代码: {return_code}")
                
        except Exception as e:
            self.append_log(f"命令执行错误: {str(e)}")
        finally:
            # 清理：录屏进程单独处理，其他进程正常移除
            if "screenrecord" in cmd:
                self.screen_record_process = None  # 重置录屏进程
            elif 'process' in locals() and process in self.active_processes:
                self.active_processes.remove(process)
            self.root.after(0, lambda: self.status_var.set("就绪"))
    
    def execute_command(self):
        """执行命令输入框中的所有命令（按行分割）"""
        cmd_text = self.command_text.get("1.0", tk.END).strip()
        if not cmd_text:
            messagebox.showwarning("警告", "请输入要执行的命令")
            return
        
        # 按行分割命令，忽略空行
        commands = [line.strip() for line in cmd_text.split('\n') if line.strip()]
        
        if not commands:
            messagebox.showwarning("警告", "没有有效的命令")
            return
        
        self.append_log(f"即将执行 {len(commands)} 条命令...")
        
        # 定义一个递归函数来逐条执行命令
        def run_commands(command_list):
            if not command_list:
                self.append_log("所有命令执行完毕")
                self.root.after(0, lambda: self.status_var.set("就绪"))
                return
            
            # 取出第一条命令执行
            current_cmd = command_list[0]
            remaining_commands = command_list[1:]
            
            self.root.after(0, lambda: self.status_var.set(f"正在执行命令 {len(commands) - len(remaining_commands)}/{len(commands)}..."))
            
            try:
                # 执行当前命令
                process = subprocess.Popen(
                    current_cmd,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    bufsize=0
                )
                
                self.active_processes.append(process)
                
                # 实时读取输出
                encodings_to_try = ['utf-8', 'gbk', 'cp936', 'iso-8859-1']
                
                while True:
                    byte_line = process.stdout.readline()
                    if not byte_line and process.poll() is not None:
                        break
                    
                    if byte_line:
                        decoded_line = None
                        for encoding in encodings_to_try:
                            try:
                                decoded_line = byte_line.decode(encoding)
                                break
                            except UnicodeDecodeError:
                                continue
                        
                        if decoded_line is None:
                            decoded_line = byte_line.decode('utf-8', errors='replace')
                            self.append_log(f"警告：无法完全解码字节序列 {byte_line.hex()}")
                        
                        self.append_log(decoded_line.strip())
                
                return_code = process.poll()
                if return_code != 0:
                    self.append_log(f"命令执行完毕，返回代码: {return_code}")
                    
            except Exception as e:
                self.append_log(f"命令执行错误: {str(e)}")
            finally:
                if 'process' in locals() and process in self.active_processes:
                    self.active_processes.remove(process)
                
                # 递归执行下一条命令
                self.root.after(0, lambda: run_commands(remaining_commands))
        
        # 在新线程中启动命令执行序列
        thread = threading.Thread(target=run_commands, args=(commands,))
        thread.daemon = True
        thread.start()
    
    def toggle_log_collect(self):
        """切换日志收集状态（开始/停止）"""
        if self.log_collecting:
            self.stop_log_collect()
        else:
            self.start_log_collect()
    
    def start_log_collect(self):
        """开始收集日志"""
        pkg = self.package_name.get()
        if not pkg:
            messagebox.showwarning("警告", "请先选择APK文件或输入包名")
            return
        
        if self.log_collecting:
            messagebox.showinfo("提示", "日志收集已在进行中")
            return
            
        self.log_collecting = True
        self.append_log(f"开始收集 {pkg} 的日志...")
        self.status_var.set("正在收集日志...")
        
        # 启动日志收集线程
        thread = threading.Thread(target=self.run_command, args=(f"adb logcat | findstr {pkg}",))
        thread.daemon = True
        thread.start()
    
    def stop_log_collect(self):
        """停止收集日志"""
        if not self.log_collecting:
            messagebox.showinfo("提示", "没有正在进行的日志收集")
            return
            
        self.log_collecting = False
        self.append_log("正在停止日志收集...")
        
        # 终止所有logcat进程
        for process in self.active_processes[:]:
            try:
                # 检查进程是否还在运行
                if process.poll() is None:
                    # 尝试获取进程命令行
                    cmd_line = getattr(process, 'args', '')
                    if "logcat" in str(cmd_line):
                        process.terminate()
                        self.append_log("日志收集进程已终止")
            except Exception as e:
                self.append_log(f"终止日志进程时出错: {str(e)}")
        
        self.status_var.set("就绪")
    
    def take_screenshot(self):
        """使用ADB进行截图并保存到本地"""
        try:
            # 创建截图保存目录
            if not os.path.exists("screenshots"):
                os.makedirs("screenshots")
            
            # 生成带时间戳的文件名
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            local_path = f"screenshots/screenshot_{timestamp}.png"
            device_path = "/sdcard/screenshot_temp.png"
            
            # 执行截图命令
            self.append_log("正在进行截图...")
            commands = [
                f"adb shell screencap -p {device_path}",
                f"adb pull {device_path} {local_path}",
                f"adb shell rm {device_path}"
            ]
            
            # 在命令框中显示并执行
            self.command_text.delete("1.0", tk.END)
            self.command_text.insert(tk.END, "\n".join(commands))
            
            # 自动执行截图命令
            thread = threading.Thread(target=self.run_command, args=(" && ".join(commands),))
            thread.daemon = True
            thread.start()
            
            self.append_log(f"截图将保存至: {os.path.abspath(local_path)}")
            
        except Exception as e:
            self.append_log(f"截图失败: {str(e)}")
            messagebox.showerror("错误", f"截图失败:\n{str(e)}")
    
    def start_screen_record(self):
        """开始屏幕录制（简化版，使用指定命令）"""
        if self.screen_recording:
            messagebox.showinfo("提示", "录屏已在进行中")
            return
            
        try:
            # 创建录屏保存目录（确保本地有目录存储）
            if not os.path.exists("screenrecords"):
                os.makedirs("screenrecords")
            
            # 生成带时间戳的本地文件名（避免覆盖）
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            self.record_filename = f"screenrecords/record_{timestamp}.mp4"
            self.device_record_path = "/sdcard/test.mp4"  # 固定设备路径，匹配手动命令
            
            self.screen_recording = True
            self.append_log(f"开始录屏（设备路径：{self.device_record_path}），按停止按钮结束")
            self.status_var.set("正在录屏...")
            
            # 执行简化录屏命令（与手动CMD完全一致）
            cmd = f"adb shell screenrecord {self.device_record_path}"
            thread = threading.Thread(target=self.run_command, args=(cmd,))
            thread.daemon = True
            thread.start()
            
        except Exception as e:
            self.append_log(f"录屏启动失败: {str(e)}")
            messagebox.showerror("错误", f"录屏启动失败:\n{str(e)}")
            self.screen_recording = False
    
    def stop_screen_record(self):
        """停止屏幕录制（优雅终止，与手动Ctrl+C一致）"""
        if not self.screen_recording:
            messagebox.showinfo("提示", "没有正在进行的录屏")
            return
            
        self.screen_recording = False
        self.append_log("正在停止录屏（等待数据写入...）")
        self.status_var.set("正在保存录屏...")
        
        # 关键步骤：模拟手动Ctrl+C，向录屏进程发送SIGINT信号（优雅终止）
        if self.screen_record_process and self.screen_record_process.poll() is None:
            try:
                # Windows系统使用CTRL_C_EVENT信号，模拟Ctrl+C
                if sys.platform == "win32":
                    subprocess.Popen("taskkill /F /PID " + str(self.screen_record_process.pid), shell=True)
                else:
                    # 非Windows系统发送SIGINT信号
                    import signal
                    self.screen_record_process.send_signal(signal.SIGINT)
                self.append_log("已向录屏进程发送停止信号，等待数据写入")
            except Exception as e:
                self.append_log(f"发送停止信号失败: {str(e)}")
        
        # 等待2秒，确保Android系统完成数据写入（关键延迟，不可省略）
        time.sleep(2)
        
        # 执行简化拉取命令（与手动CMD完全一致，拉取到本地目录）
        if hasattr(self, 'record_filename') and hasattr(self, 'device_record_path'):
            pull_cmd = f"adb pull {self.device_record_path} {self.record_filename}"
            # 拉取命令加入通用进程管理
            thread = threading.Thread(target=self.run_command, args=(pull_cmd,))
            thread.daemon = True
            thread.start()
            
            # 验证文件是否存在且有效
            local_full_path = os.path.abspath(self.record_filename)
            if os.path.exists(local_full_path) and os.path.getsize(local_full_path) > 1024:
                self.append_log(f"录屏成功保存至: {local_full_path}（大小：{os.path.getsize(local_full_path)/1024:.1f}KB）")
                # 可选：自动打开目录，方便查看
                os.startfile(os.path.dirname(local_full_path))
            else:
                self.append_log(f"警告：录屏文件可能损坏，路径：{local_full_path}（大小：{os.path.getsize(local_full_path)/1024:.1f}KB）")
        
        self.status_var.set("就绪")
    
    def show_directory_permissions(self):
        """查看应用目录权限"""
        pkg = self.package_name.get()
        if not pkg:
            messagebox.showwarning("警告", "请先选择APK文件或输入包名")
            return
            
        commands = [
            f"adb shell run-as {pkg} ls -l /data/data/{pkg}",
            f"adb shell run-as {pkg} ls -l /data/data/{pkg}/files",
            f"adb shell run-as {pkg} ls -l /data/data/{pkg}/databases",
            f"adb shell run-as {pkg} ls -l /data/data/{pkg}/shared_prefs"
        ]
        
        self.command_text.delete("1.0", tk.END)
        self.command_text.insert(tk.END, "\n".join(commands))
        self.append_log(f"已加载 {pkg} 的目录权限查看命令")
    
    def terminate_all_processes(self):
        """终止所有活跃进程（排除录屏进程，避免误杀）"""
        if not self.active_processes:
            messagebox.showinfo("提示", "没有活跃进程")
            return
            
        count = 0
        for process in self.active_processes[:]:
            try:
                if process.poll() is None:  # 进程仍在运行
                    process.terminate()
                    count += 1
            except Exception as e:
                self.append_log(f"终止进程时出错: {str(e)}")
        
        self.active_processes.clear()
        self.log_collecting = False
        # 若有录屏进程，单独优雅终止
        if self.screen_recording and self.screen_record_process:
            self.stop_screen_record()
        else:
            self.screen_recording = False
        self.status_var.set("就绪")
        self.append_log(f"已终止 {count} 个活跃进程")
    
    def clear_command(self):
        """清空命令输入框"""
        self.command_text.delete("1.0", tk.END)
    
    def show_interface_security(self):
        pkg = self.package_name.get() or "{package_name}"
        commands = [
            f"run app.package.attacksurface {pkg}",
            f"run app.provider.info -a {pkg}",
            f"run scanner.provider.finduris -a {pkg}",
            f"run scanner.provider.injection -a {pkg}",
            f"run scanner.provider.traversal -a {pkg}"
        ]
        self.command_text.delete("1.0", tk.END)
        self.command_text.insert(tk.END, "\n".join(commands))
    
    def show_component_info(self):
        pkg = self.package_name.get() or "{package_name}"
        commands = [
            f"run app.package.list",
            f"run app.package.info -a {pkg}",
            f"run app.activity.info -a {pkg}",
            f"run app.activity.start --component {pkg} {pkg}.Activity",
            f"run app.service.info -a {pkg}",
            f"run app.service.start --component {pkg} {pkg}.Service"
        ]
        self.command_text.delete("1.0", tk.END)
        self.command_text.insert(tk.END, "\n".join(commands))
    
    def show_signature(self):
        """查看应用签名信息"""
        apk = self.apk_path.get() or "youapp.apk"
        commands = [
            f"keytool -printcert -jarfile {apk}",
        ]
        self.command_text.delete("1.0", tk.END)
        self.command_text.insert(tk.END, "\n".join(commands))
        self.append_log("已加载应用签名查看命令")

    def show_frontend_hijack(self):
        """前端劫持检测"""
        commands = [
            "adb shell am start com.test.uihijack/.MainActivity",
        ]
        self.command_text.delete("1.0", tk.END)
        self.command_text.insert(tk.END, "\n".join(commands))
        self.append_log("已加载前端劫持检测命令")

    
    def show_data_anti_steal(self):
        pkg = self.package_name.get() or "{package_name}"
        commands = [
            f"adb shell am dumpheap {pkg} /data/local/tmp/a.hprof",
            "adb pull /data/local/tmp/a.hprof C:\\Users\\BCTC\\Desktop",
            "hprof-conv C:\\Users\\BCTC\\Desktop\\a.hprof loginpwd1.hprof",
            "adb push D:\\BaiduSyncdisk\\Code\\Mobile\\app_quickly\\findsensitive.sh  /data/local/tmp",
            "adb push D:\\BaiduSyncdisk\\Code\\Mobile\\app_quickly\\search.txt  /data/local/tmp",
            "adb shell \"chmod +x /data/local/tmp/findsensitive.sh\"",
            "adb shell \"/data/local/tmp/findsensitive.sh \""
        ]
        self.command_text.delete("1.0", tk.END)
        self.command_text.insert(tk.END, "\n".join(commands))
    
    def show_communication_security(self):
        target = self.target_server.get()
        process = self.process_name.get()
        pkg = self.package_name.get() or "{package_name}"
        commands = [
            f"nmap --script ssl-enum-ciphers -p 443 {target}"
        ]
        self.command_text.delete("1.0", tk.END)
        self.command_text.insert(tk.END, "\n".join(commands))

if __name__ == "__main__":
    root = tk.Tk()
    app = APKCommandTool(root)
    root.mainloop()
