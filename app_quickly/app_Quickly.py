import tkinter as tk
from tkinter import filedialog, scrolledtext, Button, Label, StringVar, Text, messagebox
import subprocess
import threading
import os
import re
import sys
import time
import webbrowser

sys.stdout = sys.__stdout__  # 修复编码重定向问题（可选）

class APKCommandTool:
    SENSITIVE_BROADCASTS = {
        "android.intent.action.PACKAGE_ADDED": "监听应用安装",
        "android.intent.action.PACKAGE_REMOVED": "监听应用卸载",
        "android.intent.action.PACKAGE_REPLACED": "监听应用更新",
        "android.intent.action.BOOT_COMPLETED": "开机自启",
        "android.intent.action.USER_PRESENT": "用户解锁设备",
        "android.intent.action.SCREEN_ON": "屏幕点亮",
        "android.intent.action.SCREEN_OFF": "屏幕关闭",
        "android.net.conn.CONNECTIVITY_CHANGE": "网络状态变化",
        "android.provider.Telephony.SMS_RECEIVED": "接收短信（高危）",
        "android.intent.action.NEW_OUTGOING_CALL": "监听拨出电话（高危）"
    }
    PRIVACY_PERMISSIONS_CN = {
        "android.permission.READ_PHONE_STATE": "读取设备识别码（IMEI/IMSI）",
        "android.permission.READ_PHONE_NUMBERS": "读取手机号码",
        "android.permission.GET_ACCOUNTS": "获取账户列表",
        "android.permission.USE_BIOMETRIC": "使用生物识别（指纹/人脸）",
        "android.permission.BODY_SENSORS": "访问身体传感器（如心率）",
        "android.permission.ACCESS_FINE_LOCATION": "获取精确位置（GPS）",
        "android.permission.ACCESS_COARSE_LOCATION": "获取大致位置（网络）",
        "android.permission.READ_CONTACTS": "读取通讯录",
        "android.permission.WRITE_CONTACTS": "修改通讯录",
        "android.permission.GET_CONTACTS": "访问联系人",
        "android.permission.READ_SMS": "读取短信",
        "android.permission.RECEIVE_SMS": "接收短信",
        "android.permission.SEND_SMS": "发送短信",
        "android.permission.READ_CALL_LOG": "读取通话记录",
        "android.permission.WRITE_CALL_LOG": "写入通话记录",
        "android.permission.PROCESS_OUTGOING_CALLS": "监听/处理呼出电话",
        "android.permission.READ_EXTERNAL_STORAGE": "读取外部存储（照片、文件等）",
        "android.permission.WRITE_EXTERNAL_STORAGE": "写入外部存储",
        "android.permission.MANAGE_EXTERNAL_STORAGE": "管理所有文件（Android 11+）",
        "android.permission.CAMERA": "使用相机（拍照/录像）",
        "android.permission.RECORD_AUDIO": "录音（麦克风）",
        "android.permission.READ_CALENDAR": "读取日历",
        "android.permission.WRITE_CALENDAR": "写入日历",
        "android.permission.BLUETOOTH_CONNECT": "连接蓝牙设备",
        "android.permission.NEARBY_WIFI_DEVICES": "附近 Wi-Fi 设备（Android 13+）",
        "android.permission.QUERY_ALL_PACKAGES": "查询所有已安装应用（高危权限）",
    }
    def __init__(self, root):
        self.root = root
        self.root.title("App Quickly")
        self.root.geometry("950x780")
        self.root.configure(padx=15, pady=15, bg="#f5f5f5")
        
        # 字体设置
        self.font_normal = ('Microsoft YaHei', 10)
        self.font_mono = ('Consolas', 10)
        
        # 变量
        self.apk_path = StringVar()
        self.package_name = StringVar()
        self.target_server = StringVar(value="your_target_server")
        self.process_name = StringVar(value="your_process")
        self.log_collecting = False
        self.log_process = None
        self.screen_recording = False
        self.active_processes = []
        self.screen_record_process = None
        
        # AAPT 路径（相对路径）
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.current_dir = current_dir
        self.aapt_path = os.path.join(current_dir, "tool", "aapt.exe")
        
        # 创建界面
        self.create_widgets()

    def create_widgets(self):
        # === APK 信息区域 ===
        apk_frame = tk.LabelFrame(self.root, text="APK 信息", font=self.font_normal, padx=10, pady=10, bg="#ffffff", relief="groove")
        apk_frame.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0,10))
        
        Label(apk_frame, text="APK文件路径(不能有中文):", font=self.font_normal, bg="#ffffff").grid(row=0, column=0, sticky="w")
        self.apk_entry = tk.Entry(apk_frame, textvariable=self.apk_path, width=60, font=self.font_normal)
        self.apk_entry.grid(row=0, column=1, padx=5)
        Button(apk_frame, text="浏览", command=self.browse_apk, font=self.font_normal, bg="#4CAF50", fg="white").grid(row=0, column=2)

        Label(apk_frame, text="应用包名:", font=self.font_normal, bg="#ffffff").grid(row=1, column=0, sticky="w", pady=(5,0))
        self.package_entry = tk.Entry(apk_frame, textvariable=self.package_name, width=60, font=self.font_normal)
        self.package_entry.grid(row=1, column=1, padx=5, pady=(5,0))

        Label(apk_frame, text="目标服务器:", font=self.font_normal, bg="#ffffff").grid(row=2, column=0, sticky="w", pady=(5,0))
        tk.Entry(apk_frame, textvariable=self.target_server, width=25, font=self.font_normal).grid(row=2, column=1, sticky="w", pady=(5,0))
        Label(apk_frame, text="进程名:", font=self.font_normal, bg="#ffffff").grid(row=2, column=1, sticky="e", pady=(5,0))
        tk.Entry(apk_frame, textvariable=self.process_name, width=20, font=self.font_normal).grid(row=2, column=2, sticky="w", pady=(5,0))

        # === 工具按钮分组 ===
        row = 1
        tool_groups = [
            ("ADB 工具", "#9C27B0", [
                ("截图", self.take_screenshot),
                ("查看私有目录权限", self.show_directory_permissions),
                ("日志收集", self.toggle_log_collect)
            ]),
            ("Drozer 工具", "#2196F3", [
                ("启动控制台", self.start_drozer_console),
                ("接口安全检测", self.show_interface_security),
                ("组件信息查询", self.show_component_info)
            ]),
            ("其他工具", "#FF9800", [
                ("查看签名", self.show_signature),
                ("前端劫持", self.show_frontend_hijack),
                ("数据防窃取", self.show_data_anti_steal),
                ("TLS", self.show_communication_security),
                ("IPv6", self.check_ipv6_support),
                ("加固和SDK分析", self.apkCheckPack) ,
                ("权限分析", self.analyze_permissions) 
            ])
        ]

        for title, color, buttons in tool_groups:
            frame = tk.LabelFrame(self.root, text=title, font=self.font_normal, padx=8, pady=8, bg="#ffffff")
            frame.grid(row=row, column=0, columnspan=3, sticky="ew", pady=5)
            for text, cmd in buttons:
                btn = Button(frame, text=text, command=cmd, font=self.font_normal,
                            bg=color, fg="white", width=12, relief="flat")
                btn.pack(side="left", padx=3, pady=2)
            row += 1

        # === 命令输入区 ===
        cmd_frame = tk.LabelFrame(self.root, text="自定义命令", font=self.font_normal, padx=10, pady=10, bg="#ffffff")
        cmd_frame.grid(row=row, column=0, columnspan=3, sticky="ew", pady=5)
        self.command_text = Text(cmd_frame, height=5, width=80, font=self.font_mono, bg="#f8f8f8")
        self.command_text.pack(fill="x")

        # === 执行按钮 & 状态 ===
        btn_row = row + 1
        btn_frame = tk.Frame(self.root, bg="#f5f5f5")
        btn_frame.grid(row=btn_row, column=0, columnspan=3, pady=10)
        Button(btn_frame, text="执行命令", command=self.execute_command,
               font=self.font_normal, bg="#4CAF50", fg="white", width=12).pack(side="left", padx=10)
        Button(btn_frame, text="终止所有进程", command=self.terminate_all_processes,
               font=self.font_normal, bg="#f44336", fg="white", width=15).pack(side="left", padx=10)
        self.status_var = StringVar(value="就绪")
        Label(btn_frame, textvariable=self.status_var, font=self.font_normal, fg="#2196F3", bg="#f5f5f5").pack(side="right")

        # === 日志输出区 ===
        log_row = btn_row + 1
        log_frame = tk.LabelFrame(self.root, text="执行日志", font=self.font_normal, padx=10, pady=10, bg="#ffffff")
        log_frame.grid(row=log_row, column=0, columnspan=3, sticky="nsew", pady=(0,0))
        self.log_text = scrolledtext.ScrolledText(log_frame, width=90, height=28, font=self.font_mono, bg="#f8f8f8")
        self.log_text.pack(fill="both", expand=True)
        self.log_text.tag_config("privacy", foreground="red")
        # 配置网格权重（支持拉伸）
        self.root.grid_rowconfigure(log_row, weight=1)  # 日志行可垂直拉伸
        for col in range(3):  # 0, 1, 2 三列都设为可水平拉伸
            self.root.grid_columnconfigure(col, weight=1)

    # ========== 核心方法 ==========
    
    def append_log(self, text, tag=None):
        def update():
            if tag:
                self.log_text.insert(tk.END, str(text) + "\n", tag)
            else:
                self.log_text.insert(tk.END, str(text) + "\n")
            self.log_text.see(tk.END)
        self.root.after(0, update)

    def browse_apk(self):
        file_path = filedialog.askopenfilename(filetypes=[("APK文件", "*.apk")])
        if file_path:
            self.apk_path.set(file_path)
            self.status_var.set("正在提取包名...")
            threading.Thread(target=self.extract_package_name, args=(file_path,), daemon=True).start()

    def extract_package_name(self, apk_path):
        """使用aapt工具提取APK的包名，修复编码问题"""
        self.append_log(f"正在提取APK包名: {apk_path}")
        self.append_log(f"使用AAPT工具路径: {self.aapt_path}")
        
        try:
            if not os.path.exists(self.aapt_path):
                error_msg = f"AAPT工具不存在于指定路径: {self.aapt_path}"
                self.append_log(error_msg)
                self.root.after(0, lambda: messagebox.showerror("文件不存在", error_msg))
                self.status_var.set("就绪")
                return
            
            if not os.path.exists(apk_path):
                error_msg = f"APK文件不存在: {apk_path}"
                self.append_log(error_msg)
                self.root.after(0, lambda: messagebox.showerror("文件不存在", error_msg))
                self.status_var.set("就绪")
                return
            
            cmd = f'"{self.aapt_path}" dump badging "{apk_path}"'
            self.append_log(f"执行命令: {cmd}")
            
            process = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=0
            )
            
            self.active_processes.append(process)
            
            output = []
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
                        self.append_log(f"警告：无法完全解码字节序列 {byte_line.hex()}，已替换不可识别字符")
                    
                    stripped_line = decoded_line.strip()
                    output.append(stripped_line)
                    self.append_log(stripped_line)
            
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
            if 'process' in locals() and process in self.active_processes:
                self.active_processes.remove(process)
    
    def run_command(self, cmd):
        self.root.after(0, lambda: self.status_var.set(f"正在执行命令..."))
        self.append_log(f"执行命令: {cmd}")
        
        try:
            process = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=0
            )
            
            if "screenrecord" in cmd:
                self.screen_record_process = process
            else:
                self.active_processes.append(process)
            
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
                
                if "logcat" in cmd and not self.log_collecting:
                    process.terminate()
                    break
                if "screenrecord" in cmd and not self.screen_recording:
                    break
            
            return_code = process.poll()
            if return_code != 0:
                if "screenrecord" not in cmd or (self.screen_recording and return_code != 0):
                    self.append_log(f"命令执行完毕，返回代码: {return_code}")
                
        except Exception as e:
            self.append_log(f"命令执行错误: {str(e)}")
        finally:
            if "screenrecord" in cmd:
                self.screen_record_process = None
            elif 'process' in locals() and process in self.active_processes:
                self.active_processes.remove(process)
            self.root.after(0, lambda: self.status_var.set("就绪"))
    
    def execute_command(self):
        cmd_text = self.command_text.get("1.0", tk.END).strip()
        if not cmd_text:
            messagebox.showwarning("警告", "请输入要执行的命令")
            return
        
        commands = [line.strip() for line in cmd_text.split('\n') if line.strip()]
        
        if not commands:
            messagebox.showwarning("警告", "没有有效的命令")
            return
        
        self.append_log(f"即将执行 {len(commands)} 条命令...")
        
        def run_commands(command_list):
            if not command_list:
                self.append_log("所有命令执行完毕")
                self.root.after(0, lambda: self.status_var.set("就绪"))
                return
            
            current_cmd = command_list[0]
            remaining_commands = command_list[1:]
            
            self.root.after(0, lambda: self.status_var.set(f"正在执行命令 {len(commands) - len(remaining_commands)}/{len(commands)}..."))
            
            try:
                process = subprocess.Popen(
                    current_cmd,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    bufsize=0
                )
                
                self.active_processes.append(process)
                
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
                self.root.after(0, lambda: run_commands(remaining_commands))
        
        thread = threading.Thread(target=run_commands, args=(commands,))
        thread.daemon = True
        thread.start()
    
    def toggle_log_collect(self):
        if self.log_collecting:
            self.stop_log_collect()
        else:
            self.start_log_collect()

    def start_log_collect(self):
        pkg = self.package_name.get()
        if not pkg:
            messagebox.showwarning("警告", "请先选择APK文件或输入包名")
            return
        if self.log_collecting:
            return
        self.log_collecting = True
        self.append_log(f"开始收集 {pkg} 的日志...")
        self.status_var.set("正在收集日志...")
        thread = threading.Thread(target=self.run_command, args=(f"adb logcat | findstr {pkg}",))
        thread.daemon = True
        thread.start()

    def stop_log_collect(self):
        self.log_collecting = False
        self.append_log("正在停止日志收集...")

    def take_screenshot(self):
        try:
            if not os.path.exists("screenshots"):
                os.makedirs("screenshots")
            
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            local_path = f"screenshots/screenshot_{timestamp}.png"
            device_path = "/sdcard/screenshot_temp.png"
            
            self.append_log("正在进行截图...")
            commands = [
                f"adb shell screencap -p {device_path}",
                f"adb pull {device_path} {local_path}",
                f"adb shell rm {device_path}"
            ]
            
            self.command_text.delete("1.0", tk.END)
            self.command_text.insert(tk.END, "\n".join(commands))
            
            thread = threading.Thread(target=self.run_command, args=(" && ".join(commands),))
            thread.daemon = True
            thread.start()
            
            self.append_log(f"截图将保存至: {os.path.abspath(local_path)}")
            
        except Exception as e:
            self.append_log(f"截图失败: {str(e)}")
            messagebox.showerror("错误", f"截图失败:\n{str(e)}")
    

    def show_directory_permissions(self):
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

    def start_drozer_console(self):
        forward_cmd = "adb forward tcp:31415 tcp:31415"
        self.append_log(f"执行命令: {forward_cmd}")
        
        try:
            drozer_window = tk.Toplevel(self.root)
            drozer_window.title("Drozer 控制台")
            drozer_window.geometry("800x600")

            log_frame = tk.Frame(drozer_window)
            log_frame.pack(fill="both", expand=True, padx=5, pady=5)
            tk.Label(log_frame, text="Drozer 输出:", font=self.font_normal).pack(anchor="w")
            drozer_log = scrolledtext.ScrolledText(log_frame, font=self.font_mono)
            drozer_log.pack(fill="both", expand=True)

            input_frame = tk.Frame(drozer_window)
            input_frame.pack(fill="x", padx=5, pady=5)
            tk.Label(input_frame, text="输入命令:", font=self.font_normal).pack(side="left")
            cmd_entry = tk.Entry(input_frame, font=self.font_normal)
            cmd_entry.pack(side="left", fill="x", expand=True, padx=5)

            self.drozer_process = subprocess.Popen(
                "drozer console connect",
                shell=True,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                encoding='utf-8',
                errors='replace'
            )
            self.active_processes.append(self.drozer_process)

            def read_output():
                while self.drozer_process and self.drozer_process.poll() is None:
                    line = self.drozer_process.stdout.readline()
                    if line:
                        drozer_log.insert(tk.END, line)
                        drozer_log.see(tk.END)
                drozer_log.insert(tk.END, "\n[Drozer 控制台已退出]\n")

            threading.Thread(target=read_output, daemon=True).start()

            def send_command(event=None):
                if self.drozer_process and self.drozer_process.poll() is None:
                    cmd = cmd_entry.get().strip()
                    if cmd:
                        drozer_log.insert(tk.END, f"> {cmd}\n")
                        self.drozer_process.stdin.write(cmd + "\n")
                        self.drozer_process.stdin.flush()
                        cmd_entry.delete(0, tk.END)

            cmd_entry.bind("<Return>", send_command)
            tk.Button(input_frame, text="发送", command=send_command, font=self.font_normal).pack(side="left", padx=5)

            def on_close():
                if self.drozer_process and self.drozer_process.poll() is None:
                    self.drozer_process.terminate()
                    self.drozer_process.wait(timeout=2)
                if self.drozer_process in self.active_processes:
                    self.active_processes.remove(self.drozer_process)
                drozer_window.destroy()

            drozer_window.protocol("WM_DELETE_WINDOW", on_close)

        except Exception as e:
            error_msg = f"启动drozer控制台失败: {str(e)}"
            self.append_log(error_msg)
            messagebox.showerror("错误", error_msg)

    # ========== 新增及补全的功能 ==========
    
    def show_interface_security(self):
        pkg = self.package_name.get().strip() or "{package_name}"
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
        pkg = self.package_name.get().strip() or "{package_name}"
        commands = [
            f"run app.package.list",
            f"run app.package.info -a {pkg}",
            f"run app.activity.info -a {pkg}",
            f"run app.activity.start --component {pkg} {pkg}.MainActivity",
            f"run app.service.info -a {pkg}",
            f"run app.service.start --component {pkg} {pkg}.MyService"
        ]
        self.command_text.delete("1.0", tk.END)
        self.command_text.insert(tk.END, "\n".join(commands))
    
    def show_signature(self):
        apk = self.apk_path.get() or "youapp.apk"
        commands = [
            f"keytool -printcert -jarfile \"{apk}\"",
        ]
        self.command_text.delete("1.0", tk.END)
        self.command_text.insert(tk.END, "\n".join(commands))
        self.append_log("已加载应用签名查看命令")

    def show_frontend_hijack(self):
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

    def check_ipv6_support(self):
        target = self.target_server.get()
        commands = [
            f"python ipv6_test.py -u {target}"
        ]
        self.command_text.delete("1.0", tk.END)
        self.command_text.insert(tk.END, "\n".join(commands))
    def apkCheckPack(self):
        apk_path = self.apk_path.get().strip()
        if not apk_path:
            messagebox.showwarning("警告", "请先选择 APK 文件")
            return
        pack_path = os.path.join(self.current_dir, "tool", "ApkCheckPack_windows_amd64.exe")
        if not os.path.exists(pack_path):
            self.append_log(f"工具未找到: {pack_path}", tag="privacy")
            return
        cmd = f'"{pack_path}" -s=false -f "{apk_path}"'
        self.command_text.delete("1.0", tk.END)
        self.command_text.insert(tk.END, cmd)
        self.append_log("已加载 APK 加固与 SDK 分析命令")
    def terminate_all_processes(self):
        count = len(self.active_processes)
        for p in self.active_processes[:]:
            try:
                if p.poll() is None:
                    p.terminate()
            except:
                pass
        self.active_processes.clear()
        messagebox.showinfo("提示", f"已终止 {count} 个活跃进程")

    # ========== 新增：权限分析 & SDK识别 ==========
    
    def analyze_permissions(self):
        """分析 APK 中声明的权限，并对涉及个人信息的权限用红色高亮显示"""
        apk_path = self.apk_path.get().strip()
        if not apk_path or not os.path.exists(apk_path):
            messagebox.showwarning("警告", "请先选择有效的 APK 文件")
            return

        self.append_log("正在分析 APK 权限...")
        try:
            cmd = f'"{self.aapt_path}" dump permissions "{apk_path}"'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8', errors='replace')
            output = result.stdout + result.stderr

            if "package:" not in output:
                self.append_log("无法解析权限信息，请检查 APK 文件完整性或路径是否含中文。")
                return

            permission_lines = [line.strip() for line in output.split('\n') if 'uses-permission:' in line]
            permissions = []
            for line in permission_lines:
                match = re.search(r"\'([^\']+)\'", line)
                if match:
                    perm = match.group(1)
                    permissions.append(perm)

            if not permissions:
                self.append_log("未发现任何权限声明。")
                return

            # 分隔线
            self.append_log("\n=== 权限分析结果（共 {} 项）===".format(len(permissions)))

            privacy_found = False
            for perm in permissions:
                if perm in self.PRIVACY_PERMISSIONS_CN:
                    cn_desc = self.PRIVACY_PERMISSIONS_CN[perm]
                    # 使用红色 tag 输出
                    self.append_log(f"【⚠️ 涉及个人信息】{perm}", tag="privacy")
                    self.append_log(f"    → {cn_desc}", tag="privacy")
                    privacy_found = True
                else:
                    self.append_log(f"【普通权限】{perm}")

            if privacy_found:
                self.append_log("\n📌 提示：红色标出的权限涉及个人信息，需在隐私政策中明示并获用户同意。", tag="privacy")
            else:
                self.append_log("\n✅ 未发现涉及个人信息的敏感权限。")
            self.analyze_broadcast_receivers()
        except Exception as e:
            error_msg = f"权限分析失败: {str(e)}"
            self.append_log(error_msg)
            messagebox.showerror("错误", error_msg)
        
    def analyze_broadcast_receivers(self):
        """分析 APK 中静态注册的敏感广播接收器"""
        apk_path = self.apk_path.get().strip()
        if not apk_path or not os.path.exists(apk_path):
            return

        try:
            self.append_log("\n正在分析广播接收器...")
            cmd = f'"{self.aapt_path}" dump xmltree "{apk_path}" AndroidManifest.xml'
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True,
                encoding='utf-8', errors='replace'
            )
            lines = result.stdout.splitlines()

            found_actions = set()
            in_action = False
            current_name = ""

            # 解析 xmltree 结构：查找 <action android:name="xxx">
            for line in lines:
                line = line.strip()
                if line.startswith('E: action '):
                    in_action = True
                    current_name = ""
                elif in_action and 'A: android:name(0x' in line and '="' in line:
                    try:
                        # 提取引号内的值
                        name = line.split('"')[1]
                        if name in self.SENSITIVE_BROADCASTS:
                            found_actions.add(name)
                        in_action = False
                    except IndexError:
                        in_action = False

            if found_actions:
                self.append_log("【⚠️ 检测到敏感广播接收器】", tag="privacy")
                has_high_risk = False
                for action in sorted(found_actions):
                    desc = self.SENSITIVE_BROADCASTS[action]
                    if "高危" in desc:
                        has_high_risk = True
                    self.append_log(f"  • {desc} → {action}", tag="privacy")

                # 高危行为特别警告
                if has_high_risk:
                    self.append_log(
                        "❗ 警告：检测到短信或通话监听行为，涉嫌违反《个人信息保护法》及工信部规定！",
                        tag="privacy"
                    )
                elif "PACKAGE_ADDED" in found_actions:
                    self.append_log(
                        "📌 建议：应用安装监听需在隐私政策中明确告知用途，并取得用户同意。",
                        tag="privacy"
                    )
            else:
                self.append_log(
                "\n✅ 未发现明显的动态广播注册代码。"
                "\nℹ️ 注意：本工具仅检测静态注册的广播。\n"
                "   动态注册的广播（代码中 registerReceiver）无法通过此方式发现，\n"
                "   如需深度检测，请使用反编译工具（如 Jadx）人工审查。",
                tag=None  # 黑色普通文本
            )

        except Exception as e:
            self.append_log(f"广播分析失败: {str(e)}")

# ========== 主程序入口 ==========
if __name__ == "__main__":
    root = tk.Tk()
    app = APKCommandTool(root)
    root.mainloop()