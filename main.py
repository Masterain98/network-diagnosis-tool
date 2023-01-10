import subprocess
from time import gmtime, strftime

import dns.exception
import dns.resolver
import requests
import speedtest
from nslookup import Nslookup

log_message = ""

targeting_hosts = {
    "hutao-metadata.snapgenshin.com": "元数据",
    "static.hut.ao": "静态资源 - 1",
    "static.snapgenshin.com": "静态资源 - 2",
    "homa.snapgenshin.com": "胡桃数据库",
    "hut.ao": "胡桃工具箱 - 主页",
    "snapgenshin.com": "Snap.Genshin - 主页",
}

dns_resolver = dns.resolver.Resolver()


def get_local_ip():
    return requests.get('https://myip.ipip.net/').text


def get_local_dns():
    return dns_resolver.nameservers


def nslookup_checker(requested_hostname: str):
    try:
        answer = dns_resolver.resolve(requested_hostname, "A")
        return answer
    except dns.resolver.NoAnswer:
        return None
    except dns.exception.DNSException as err:
        print("DNS Error: " + str(err))


def log(message, next_line: bool = False):
    global log_message
    message = str(message)
    if next_line:
        log_message += message + "\n"
        print(message + "\n")
    else:
        log_message += message
        print(message)


if __name__ == '__main__':
    print("正在诊断网络环境...")
    print("这可能需要至多10分钟，请耐心等待。")
    print("诊断程序可以在最小化的情况下运行，结束后将生成报告文件。\n")
    # 系统信息
    local_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())
    time_zone = strftime("%Z", gmtime())
    log("本地时间: " + local_time)
    log("本机时区: " + time_zone, True)

    # 本地 DNS
    local_dns = get_local_dns()
    for dns_server in local_dns:
        log("本地 DNS: " + dns_server, False)
    log("")
    try:
        dns_pollution_checker = nslookup_checker("whether.114dns.com")
        if dns_pollution_checker is None:
            log("DNS 可能有污染或被劫持")
        else:
            dns_pollution_checker = dns_pollution_checker.response.answer[0].to_rdataset().to_text()
            if not dns_pollution_checker.endswith("127.0.0.1"):
                log("DNS 可能有污染或被劫持")
    except Exception as err:
        log("DNS 可能有污染或被劫持" + str(err))
    
    # 本地 IP
    try:
        local_ip = get_local_ip()
        log(local_ip, False)
    except Exception as e:
        log("无法获取本地 IP 地址: " + str(e))

    # 网络检查
    for hostname in targeting_hosts.keys():
        log("=" * 20 + "\n" + "正在检查 " + targeting_hosts[hostname] + " 的网络连接情况")
        nslookup = Nslookup(dns_servers=local_dns)
        ip_result = nslookup.dns_lookup(hostname).answer[0]
        log("期待 IP 地址: " + ip_result)

        try:
            ping_process = subprocess.check_output("ping " + hostname)
            ping_result = ping_process.decode("gbk")
        except subprocess.CalledProcessError as e:
            log(e.output.decode("gbk"), True)
            ping_result = "Ping 命令错误"
        except UnicodeDecodeError:
            try:
                ping_result = ping_process.decode("utf-8")
            except UnicodeDecodeError:
                try:
                    ping_result = ping_process.decode("gb2312")
                except UnicodeDecodeError:
                    ping_result = ping_process.decode("cp1252")
        log(ping_result, True)

        print("正在进行 traceroute 测试，请耐心等待...")
        tracert_process = subprocess.check_output("tracert -d " + hostname)
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
        log(tracert_result, True)

    # Speedtest
    log("=" * 20 + "\n" + "正在进行 Speedtest 测试")
    s = speedtest.Speedtest()
    s.get_best_server()
    s.download(threads=8)
    s.upload(threads=8)
    results_dict = s.results.dict()
    download_speed = results_dict["download"] / 1024 / 1024
    upload_speed = results_dict["upload"] / 1024 / 1024
    server = results_dict["server"]["name"] + " - " + results_dict["server"]["sponsor"]

    log("下载速度: " + str(round(download_speed, 2)) + " Mbps")
    log("上传速度: " + str(round(upload_speed, 2)) + " Mbps")
    log("服务器: " + server, True)

    # 保存日志
    with open("hutao-network-log.txt", "w", encoding='utf-8') as f:
        f.write(log_message)
    print("=" * 20 + "\n" + "日志已保存至 hutao-network-log.txt")
    print("请提交 hutao-network-log.txt 文件至 GitHub 或管理员")
    input("测试结束。你可以点击回车或者直接关闭该窗口")
