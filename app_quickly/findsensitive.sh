#!/bin/sh

# 检查search.txt文件是否存在
if [ ! -f "search.txt" ]; then
    echo "错误：search.txt文件不存在！"
    exit 1
fi

# 读取应用名（第一行）
appname=$(head -n 1 "search.txt" | tr -d '\r')  # 移除可能的回车符

# 读取敏感信息列表（从第二行开始）
sensitiveinfos=$(tail -n +2 "search.txt" | tr -d '\r')  # 移除回车符

# 构建搜索路径（确保路径无多余字符）
path="/data/user/0/$appname"
# 再次检查路径是否存在（更严格的判断）
if [ ! -d "$path" ]; then
    echo "警告：路径 $path 不存在！"
    # 继续执行但可能无结果
fi

# 遍历每个敏感信息进行搜索
while IFS= read -r info; do
    # 跳过空行
    if [ -z "$info" ]; then
        continue
    fi

    # 生成格式1: 每个字符转为16进制并用\x00分隔（兼容处理）
    format1=""
    len=${#info}
    i=0
    while [ $i -lt $len ]; do
        char="${info:$i:1}"
        # 将字符转为十六进制（兼容特殊字符）
        hex=$(printf "%x" "'$char" 2>/dev/null)
        # 拼接格式
        if [ -z "$format1" ]; then
            format1="\\x$hex"
        else
            format1="$format1\\x00\\x$hex"
        fi
        i=$((i + 1))
    done

    # 生成格式2: 字符间用空格分隔（优化sed命令）
    format2=$(echo "$info" | sed 's/./& /g; s/ $//')  # 移除末尾多余空格

    # 执行三个搜索命令（适配BusyBox grep，移除不支持的选项）
    echo -e "\n------待查字符串已变形，开始进行敏感信息检索-----"
    
    # 命令1：去掉-P（不支持Perl正则）和-U（不支持二进制模式）
    echo "查询命令1: grep -rnba '$format1' \"$path\""
    grep -rnba "$format1" "$path" 2>/dev/null  # 忽略错误输出
    echo -e "\n"

    # 命令2：保留-i（不区分大小写），用双引号包裹路径避免空格问题
    echo "查询命令2: grep -rni '$format2' \"$path\""
    grep -rni "$format2" "$path" 2>/dev/null
    echo -e "\n"

    # 命令3：同样用双引号包裹路径
    echo "查询命令3: grep -rni '$info' \"$path\""
    grep -rni "$info" "$path" 2>/dev/null

done <<< "$sensitiveinfos"
