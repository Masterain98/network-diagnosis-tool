# coding = utf-8
import dns.exception
import dns.resolver
import dns.message
import requests
import json
import base64
import random


dns_resolver = dns.resolver.Resolver()


def get_local_dns() -> dns.resolver.Resolver.nameservers:
    return dns_resolver.nameservers


def get_remote_dns() -> dict:
    try:
        return requests.get(f"https://{random.randint(10000000, 99999999)}.check.dns.pub/isp").json()
    except requests.HTTPError:
        return {}


def nslookup_checker(requested_hostname: str) -> dns.resolver.Answer | None:
    try:
        answer = dns_resolver.resolve(requested_hostname, "A")
        return answer
    except dns.resolver.NoAnswer:
        return None
    except dns.exception.DNSException as dns_err:
        print("DNS Error: " + str(dns_err))
        return None


def doh_checker(requested_hostname: str) -> list | str:
    doh_url = "https://dns.alidns.com/dns-query"
    rr = "A"
    result = []

    message = dns.message.make_query(requested_hostname, rr)
    dns_req = base64.b64encode(message.to_wire()).decode("UTF8").rstrip("=")
    r = requests.get(doh_url + "?dns=" + dns_req,
                     headers={"Content-type": "application/dns-message"})
    try:
        for answer in dns.message.from_wire(r.content).answer:
            dns_res = answer.to_text().split()
            result.append({"Query": dns_res[0], "TTL": dns_res[1], "RR": dns_res[3], "Answer": dns_res[4]})
    except dns.exception.FormError:
        print("DoH Error: " + r.text)
        return "DoH 查询失败"
    return json.dumps(result, indent=2, ensure_ascii=False)
