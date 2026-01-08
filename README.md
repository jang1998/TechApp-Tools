# TechApp-Tools
金科认证app测试工具，不定期更新，感谢zjy/0xbinibini/lj等人的代码贡献

BroadcastTest用于广播测试，使用方法：调起cmd, java -jar BroadcastTest.jar

del_pz.py用于删除批注与更新目录，使用方法：放到word初稿终稿内文件夹，python del_pz.py

excel_add_row_hight.py用于增加间距方便导出pdf，放到excel原始目录文档内文件夹，excel_add_row_hight.py

info.py用于自动更新05客户端软件检测总体情况报告，使用方法：放到word初稿终稿内文件夹，python info.py #使用后第五页检测信息概略表会出现少页情况，自行添加换页符。

findsensitive.sh请查看使用文档，用于检索手机app文件夹敏感信息

pdf.py用于没有wps会员情况下word生成pdf，使用方法：放到word初稿终稿内文件夹，python pdf.py





**app_quickly文件夹app_quickly使用说明**

使用环境：python3、drozer（电脑和手机都安装）、java8以上环境（运行keytool.jar文件）、nmap（用于测试TLS，可以替换sslscan等其他工具）、
使用方法：将app_quickly/tool目录加入系统变量即可运行
自行安装后就可以运行了，工具报错缺什么库就pip安装即可

adb行：插入手机连接后，点截图、录屏等功能即可。浏览apk文件后会自动获取包名，可点击查看目录权限；日志收集会收集log日志，自行ctrl+a复制保存就行；

drozer行：先手机打开drozer，点击启动控制台，然后复制接口安全检测，组件等下面的命令输入运行即可；

其他工具：该行命令需要自行点击执行命令，下面的输出会回显命令；前端劫持会调起一个app，需要自行安装uihijack；防窃取需要一行行运行；通讯安全检测是测试TLS版本，IPv6会回显网站结果

11.25
迭代更新内容：增加加固识别、SDK识别和静态广播识别，去除录屏、通讯安全检测改为TLS，页面美化

