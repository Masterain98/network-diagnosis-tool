# network-diagnosis-tool
A network diagnosis tool designed for [Snao.Hutao Project at DGP-Studio](https://github.com/DGP-Studio/Snap.Hutao)

## How to use
- Downlaod the [latest release](https://github.com/Masterain98/network-diagnosis-tool/releases/latest)
- Run `network-diagnosis-hutao.exe`
- Open the network issue in [Snap.Hutao repository](https://github.com/DGP-Studio/Snap.Hutao/issues/new/choose)
- Choose `network issue`
- Upload the diagnosis report (txt file)

## What is included
- Local DNS configuration 
- Local IP address
- Traceroute to target hosts
- Ping test
- Speedtest

## How to modify the diagnosis target
- Modify the `targeting_hosts` dictionary in the `main.py`
   - the structure is 
     ``` python
     targeting_hosts: {
      "target_hostname": "description"
     }
     ```
   - sample is 
     ``` python
     targeting_hosts: {
      "www.google.com": "Google main website"
     }
     ```
