# coding: utf-8
"""
create on July 7, 2022 By Wayne YU
Email: ieeflsyu@outlook.com

Function:

根据全球IPv4地址扫描的80、443端口信息，结合高总的IP地址定位信息，近似统计我国IDC分布

"""

from ipdb import City
import time
import csv


def write_to_csv(res_list, des_path, title_line):
    """
    把给定的List，写到指定路径的文件中
    :param res_list:
    :param des_path:
    :param title_line:
    :return: None
    """
    print("write file <%s> ..." % des_path)
    csv_file = open(des_path, 'w', newline='', encoding='gbk')
    try:
        writer = csv.writer(csv_file, delimiter=",")
        writer.writerow(title_line)
        for i in res_list:
            writer.writerow(i)
    except Exception as e:
        print(e)
    finally:
        csv_file.close()
    print("write finish!")


def deal():
    """
    处理并保存
    :return:
    """
    db = City("../000LocalData/ipdb/caict_ipv4.ipdb")
    # db = City("../000LocalData/ipdb/caict_full.ipdb")
    print("ipdb.build.time:", db.build_time())
    print(db.find("223.255.207.197", "CN"))
    result_list = []

    print("跑443")
    file_in = "../000LocalData/IPPorts/zmap_20220306024714_443.csv"
    file_read = open(file_in, 'r', encoding='utf-8')
    cnt = 0
    for line in file_read.readlines():
        line = line.strip().split(",")
        aim_ip = line[0]
        try:
            geo_info = db.find(aim_ip, "CN")
        except Exception as e:
            geo_info = [e]
        if geo_info[0] == "中国":
            temp_info = [aim_ip]
            temp_info.extend(geo_info)
            temp_info.append("443")
            print(temp_info)
            result_list.append(temp_info)
            cnt += 1
            if cnt > 10:
                break
                # pass

    print("跑80")
    file_in = "../000LocalData/IPPorts/zmap_20220307101747_80.csv"
    file_read = open(file_in, 'r', encoding='utf-8')
    cnt = 0
    for line in file_read.readlines():
        line = line.strip().split(",")
        aim_ip = line[0]
        try:
            geo_info = db.find(aim_ip, "CN")
        except Exception as e:
            geo_info = [e]

        if geo_info[0] == "中国":
            temp_info = [aim_ip]
            temp_info.extend(geo_info)
            temp_info.append("80")
            print(temp_info)
            result_list.append(temp_info)
            cnt += 1
            if cnt > 10:
                break
                # pass

    save_path = "./map_idc.csv"
    write_to_csv(result_list, save_path, [])


if __name__ == "__main__":
    time_start = time.time()  # 记录启动的时间
    deal()
    print("=>Scripts Finish, Time Consuming:", (time.time() - time_start), "S")
