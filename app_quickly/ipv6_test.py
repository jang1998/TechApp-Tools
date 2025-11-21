from urllib3 import PoolManager
from json import loads as jsload
from pandas import DataFrame
from tqdm import tqdm
from argparse import ArgumentParser
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
版本：         0.1
功能：         IPv6与IPv4访问速度差测试
最后修订日期：   2025-11-21
记录：         功能实现
"""

URL = "https://ipw.cn/api/ping"
USER_AGENT = ("Mozilla/5.0 (Linux; U; Android 15; SM-M145F Build/AP3A.240905.015.A2; wv) AppleWebKit/"
              "537.36 (KHTML, like Gecko) Version/4.0 Chrome/140.0.7339.156 Mobile Safari/537.36 OPR/94.0.2254.78762")

def ping_test(test_type, target_url, area, debug=False):
    """单次PING测试"""
    retry = 0
    http = PoolManager()
    test_headers = {'User-Agent': USER_AGENT}
    test_url = f"{URL}/{test_type}/{target_url}/4/{area}"
    response = http.request('GET', test_url, headers=test_headers)
    if response.status == 200 and jsload(response.data.decode('utf-8'))["pingResultDetail"] is not None:
        while (data := jsload(response.data.decode('utf-8'))["pingResultDetail"])[0].get("pingResult") is None:
            response = http.request('GET', test_url, headers=test_headers)
            while jsload(response.data.decode('utf-8')).get("pingResultDetail") is None:
                response = http.request('GET', test_url, headers=test_headers)
            retry += 1
            print(f"PING失败，第 {retry} 次重试", end="")
            if debug:
                print(f"，响应内容为：\n{data}")
            else:
                print()
    else:
        # if ((_ := input("网站连接失败，是否重试（Y/n）：")).lower() == 'y') or not _:
        #     data = ping_test(test_type, target_url, area, debug)
        # else:
        #     exit(1)
        data = ping_test(test_type, target_url, area, debug)
    return data


def data_analysis(test_type, target_url, area="guangzhou", debug=False):
    """测速函数"""
    __result, __out = {}, {}
    for _ in tqdm(range(3), desc=f"网站 {target_url} 的 {test_type} {area}测试", leave=False):
        results = ping_test(test_type, target_url, area, debug)
        for res in results:
            if res.get("pingResult") is None:
                continue
            try:
                res_area = res['pingServerArea']
                data = res["pingResult"]
            except Exception as e:
                print(e)
                print(res)
                exit(1)
            if res_area not in __result:
                __result[res_area] = {"loss": [], "time": [], "ipaddress": data['pingIP']}
            __result[res_area]["loss"].append(data["lossPacket"])
            __result[res_area]["time"].append(data["rttAvgTime"])
    for _area in __result:
        dataform = DataFrame({"丢失率": __result[res_area]["loss"], "平均响应时间": __result[res_area]["time"]})
        _data = dataform.mean().to_dict()
    # print(f"{result['pingServerArea']}地区的 {test_type} 响应地址为 {data['pingIP']}")
        if debug:
            print(f"{_area}地区的 {test_type} 测试结果为：{_data}")
        __out[_area] = {"data": _data, "ipaddress": __result[res_area]["ipaddress"]}
    return __out


def tally_up(data_v6, data_v4):
    for area in data_v6:
        if area not in data_v4:
            continue
        print(f"{area}地区解析到的 IPv6 地址为 {data_v6[area]['ipaddress']}，测试结果：", end="")
        if (_ := data_v6[area]['data']['丢失率']) > 5.0:
            print(f"丢失率为{_:.2%}，已大于 5%，测试不通过❌；", end="")
        else:
            print(f"丢失率为{_:.2%}，测试通过✅；", end="")
        v6_speed = data_v6[area]['data']['平均响应时间']
        v4_speed = data_v4[area]['data']['平均响应时间']
        if v6_speed < v4_speed:
            print(f"平均响应时间低于 IPv4，测试通过✅")
        elif (speed_gap := v6_speed - v4_speed) < 75:
            print(f"访问延迟为{speed_gap:.2}ms，小于75ms，测试通过✅")
        elif (speed_gap := (v6_speed - v4_speed) / v6_speed) < 0.15:
            print(f"访问延迟为{speed_gap:.2%}, 小于15%，测试通过✅")
        else:
            print(f"访问延迟不符合要求，测试不通过❌；")
    return


if __name__ == '__main__':
    parser = ArgumentParser(description='IPv6 test tool')
    parser.add_argument('-u', '--url', help='Target URL', required=False)
    parser.add_argument('-d', '--debug', help='Open Debug mode', required=False)
    args = parser.parse_args()
    test_URL = "open.qzccbank.com" if not args.url else args.url
    debug_mode = False if not args.debug else args.debug
    # ip_test('ipv4', test_URL)
    v6_res = data_analysis('ipv6', test_URL, "all", debug_mode)
    v4_res = data_analysis('ipv4', test_URL, "all", debug_mode)
    tally_up(v6_res, v4_res)
