from config import *
from datetime import datetime

if __name__ == "__main__":
    version_div = VERSION.split(".")
    major_v = version_div[0]
    minor_v = version_div[1]
    patch_v = version_div[2]
    build_v = version_div[3]
    this_year = datetime.now().year
    FILE_VERSION = VERSION
    PRODUCT_VERSION = VERSION

    # read template
    with open("./assets/file_version_info.txt.sample", "r", encoding="utf-8") as f:
        info_text = f.read()
    info_text = info_text.format(major_v=major_v, minor_v=minor_v, patch_v=patch_v, build_v=build_v,
                                 COMPANY_NAME=COMPANY_NAME, FILE_DESCRIPTION=FILE_DESCRIPTION,
                                 INTERNAL_NAME=INTERNAL_NAME, COPYRIGHT=COPYRIGHT,
                                 this_year=this_year, PRODUCT_NAME=PRODUCT_NAME, PRODUCT_VERSION=PRODUCT_VERSION,
                                 VERSION=VERSION, FILE_VERSION=FILE_VERSION)
    with open("./file_version_info.txt", "w+", encoding="utf-8") as f:
        f.write(info_text)
