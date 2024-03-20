# coding = utf-8
import os
import subprocess
import time
from time import gmtime, strftime
import requests
from nslookup import Nslookup
import dns_utils
import uuid
import pyminizip
import encryption.encrypt_util
import concurrent.futures
from config import VERSION


log_message = ""

targeting_hosts = {
    "api.snapgenshin.com": "Generic API",
    "homa.snapgenshin.com": "Hutao API",
    "enka-api.hut.ao": "Enka API (Hutao)",
    "hut.ao": "Snap Hutao Home Page",
    "autopatchhk.yuanshen.com": "Genshin Impact Global Update Resource",
    "autopatchcn.yuanshen.com": "Genshin Impact CN Update Resource",
    "sdk-os-static.mihoyo.com": "Genshin Impact Global Update Resource SDK",
    "jihulab.com": "Snap Hutao GitLab Repository",
    "github.com": "GitHub Repository",
}


def get_local_ip() -> str:
    ip_info = requests.get('https://myip.ipip.net/')
    if ip_info.status_code != 200:
        return "获取本地 IP 地址失败"
    else:
        return ip_info.text


def log(message, next_line: bool = False):
    global log_message
    message = str(message)
    if next_line:
        log_message += message + "\n"
        print(message + "\n")
    else:
        log_message += message
        print(message)


def tracert_test(this_hostname: str):
    temp_log = ""
    temp_log += ("=" * 20 + "\n" + "正在检查 " + targeting_hosts[this_hostname] + " 的网络连接情况\n")
    nslookup = Nslookup(dns_servers=local_dns)
    ip_result = nslookup.dns_lookup(this_hostname).answer[0]
    doh_result = dns_utils.doh_checker(this_hostname)
    temp_log += ("期待 IP 地址: " + ip_result + "\n")
    temp_log += ("DoH 查询结果: " + str(doh_result) + "\n")

    try:
        ping_process = subprocess.check_output("ping " + this_hostname)
        ping_result = ping_process.decode("gbk")
    except subprocess.CalledProcessError as e:
        temp_log += (e.output.decode("gbk") + "\n")
        ping_result = "Ping 命令错误"
    except UnicodeDecodeError:
        possible_encoding = ["utf-8", "gb2312", "cp1252"]
        for encoding in possible_encoding:
            try:
                ping_result = ping_process.decode(encoding)
            except UnicodeDecodeError:
                pass
            else:
                break
    temp_log += (str(ping_result) + "\n")

    print(f"Starting traceroute test for {this_hostname}...")
    tracert_process = subprocess.check_output("tracert -d -w 800 " + this_hostname)
    try:
        tracert_result = tracert_process.decode("gbk")
    except UnicodeDecodeError:
        try:
            tracert_result = tracert_process.decode("utf-8")
        except UnicodeDecodeError:
            try:
                tracert_result = tracert_process.decode("gb2312", "ignore")
            except UnicodeDecodeError:
                tracert_result = tracert_process.decode("cp1252", "ignore")
    temp_log += (tracert_result + "\n")
    return this_hostname, temp_log


if __name__ == '__main__':
    print("正在诊断网络环境...")
    print("这可能需要至多10分钟，请耐心等待。")
    print("诊断程序可以在最小化的情况下运行，结束后将生成报告文件。\n")
    log("网络诊断工具版本： " + VERSION)
    # 系统信息
    local_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    time_zone = time.strftime("%Z", time.localtime())
    try:
        time_zone = time_zone.encode('latin-1').decode('UTF-8')
    except UnicodeDecodeError:
        try:
            time_zone = time_zone.encode('latin-1').decode('gbk')
        except UnicodeDecodeError:
            time_zone = "解码时区信息失败，大概是中国用户吧"
    log("本地时间: " + local_time)
    log("本机时区: " + time_zone, True)

    # 本地 DNS
    local_dns = dns_utils.get_local_dns()
    for dns_server in local_dns:
        log("本地 DNS: " + dns_server, True)
    log("")

    # remote_dns = dns_utils.get_remote_dns()
    # log("远程 DNS 判断: " + str(remote_dns), True)

    # 本地 IP
    try:
        local_ip = get_local_ip()
        log("\n" + local_ip, False)
    except Exception as e:
        log("无法获取本地 IP 地址: " + str(e))

    # 网络检查
    pool_size = os.cpu_count()
    with concurrent.futures.ThreadPoolExecutor(max_workers=pool_size) as executor:
        results = list(executor.map(tracert_test, targeting_hosts.keys()))
    host_diagnosis = {hostname: tracert_log for hostname, tracert_log in results}

    for hostname in targeting_hosts.keys():
        log(host_diagnosis[hostname], True)

    # 保存日志
    uuid_str = str(uuid.uuid4())
    file_name = f"SH-Report-{uuid_str}"
    with open(f"{file_name}.txt", "w+", encoding='utf-8') as f:
        f.write(log_message)
    # Zip the log file with password with name of uuid.zip
    pyminizip.compress(f"./{file_name}.txt", None, f"{file_name}.zip",
                       encryption.encrypt_util.generate_password(uuid_str), 5)

    print("=" * 20 + "\n" + f"日志已保存至 {file_name}.txt")
    print(f"请上传 {file_name}.zip 压缩包至 GitHub 议题中")
    print(f"Please upload {file_name}.zip to GitHub Issue.")
    input("测试结束。你可以点击回车或者直接关闭该窗口\nPress Enter to exit...")
