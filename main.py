# coding = utf-8
import os
import subprocess
import time
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
    "cnb.cool": "CNB Cool",
    "github.com": "GitHub Repository"
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
    ping_result = ""
    temp_log += ("=" * 20 + "\n" + "正在检查 " + targeting_hosts[this_hostname] + " 的网络连接情况\n")
    
    nslookup = Nslookup(dns_servers=local_dns)
    try:
        ip_answer = nslookup.dns_lookup(this_hostname).answer[0]
        ip_result = ip_answer
    except Exception as e:
        ip_result = f"DNS lookup failed: {e}"
    temp_log += ("期待 IP 地址: " + str(ip_result) + "\n")
    
    doh_result = dns_utils.doh_checker(this_hostname)
    temp_log += ("DoH 查询结果: " + str(doh_result) + "\n")
    
    try:
        ping_process = subprocess.check_output("ping " + this_hostname)
        try:
            ping_result = ping_process.decode("gbk")
        except UnicodeDecodeError:
            possible_encoding = ["utf-8", "gb2312", "cp1252"]
            for encoding in possible_encoding:
                try:
                    ping_result = ping_process.decode(encoding)
                except UnicodeDecodeError:
                    continue
                else:
                    break
    except subprocess.CalledProcessError as e:
        temp_log += (e.output.decode("gbk", errors="ignore") + "\n")
        ping_result = "Ping 命令错误"
    temp_log += (str(ping_result) + "\n")
    
    print(f"Starting traceroute test for {this_hostname}...")
    try:
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
    except subprocess.CalledProcessError as e:
        tracert_result = "Tracert error: " + e.output.decode("gbk", errors="ignore")
    except Exception as ex:
        tracert_result = "Tracert exception: " + str(ex)
    
    temp_log += (tracert_result + "\n")
    return this_hostname, temp_log


def is_loopback_exempt(package_name):
    """
    检查给定的UWP应用包名（Package Family Name）是否已经解除本地回环访问限制。
    返回 True 表示已解除（应用在回环免除列表中），False 表示未解除。
    若检测过程中出现错误（如权限不足或命令不可用），则抛出异常。
    """
    try:
        # 调用 CheckNetIsolation 列出所有已免除回环限制的应用
        ps_result = subprocess.run(
            ["CheckNetIsolation.exe", "LoopbackExempt", "-s"],
            capture_output=True, text=True, check=False
        )
        # Log the subprocess output as a string into the overall output log.
        log("Loopback query subprocess output: " + ps_result.stdout, True)
    except FileNotFoundError:
        # 系统中找不到 CheckNetIsolation 可执行文件
        raise RuntimeError("无法找到 CheckNetIsolation.exe，请确保在 Windows 环境下运行。")

    output = ps_result.stdout
    if ps_result.returncode != 0:
        # 返回码非0表示可能有错误，例如权限不足
        error_msg = ps_result.stderr if ps_result.stderr else output
        if "Access is denied" in error_msg or "requires elevation" in error_msg:
            raise PermissionError("检查操作需要管理员权限，请以管理员身份运行。")
        else:
            raise RuntimeError(f"执行 CheckNetIsolation 时出现错误: {error_msg.strip()}")

    # CheckNetIsolation -s 输出每个豁免的应用包含“Name:”一行以及对应的SID一行
    is_exempt = False
    for line in output.splitlines():
        line_stripped = line.strip().lower()
        if line_stripped.startswith("name:"):
            app_name = line_stripped.split(":", 1)[1].strip()
            if package_name.lower() in app_name:
                is_exempt = True
                break
    return is_exempt


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

    # 检查 UWP 应用是否解除本地回环限制
    package = "60568DGPStudio.SnapHutao_wbnnev551gwxy"
    try:
        result = is_loopback_exempt(package)
        if result:
            print(f"{package} 的本地回环限制 **已解除**。")
        else:
            print(f"{package} 没有解除本地回环限制或未安装。")
    except Exception as e:
        print(f"检查过程中发生错误: {e}")

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
