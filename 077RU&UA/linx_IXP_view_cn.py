# coding:utf-8
"""
create on Mar 14, 2022 By Wenyan YU

Function：

针对LINX终止Rostelecom和MegaFon流量交换服务事件的分析

1）俄网络在全球总接了多少个IX，涉及多少个网络（OPEN PEER）,总的带宽，以及占俄国际带宽的比例;
2）MSK-IX接入成员所属国家，以及带宽的比例统计。

cn版本：

统计中国的网络在IX中的接入带宽

"""
from urllib.request import urlopen
import json
import time
import csv

except_info_list = []  # 存储异常信息


def write_to_csv(res_list, des_path):
    """
    把给定的List，写到指定路径的文件中
    :param res_list:
    :param des_path:
    :return None:
    """
    print("write file<%s> ..." % des_path)
    csv_file = open(des_path, 'w', newline='', encoding='utf-8')
    try:
        writer = csv.writer(csv_file, delimiter=",")
        for i in res_list:
            writer.writerow(i)
    except Exception as e:
        print(e)
    finally:
        csv_file.close()
    print("write finish!")


def gain_as2country_caida():
    """
    根据Caida asninfo获取as对应的国家信息
    :return as2country:
    """
    as_info_file = '..\\000LocalData\\as_Gao\\asn_info_from_caida.csv'
    as2country = {}  # 存储as号到country的映射关系
    file_read = open(as_info_file, 'r', encoding='utf-8')
    for line in file_read.readlines():
        line = line.strip().split(",")
        # print(line)
        as_number = line[0]
        as_country = line[-1]
        as2country[as_number] = as_country
    return as2country


def gain_ix2info_pdb():
    """
    根据pdb的数据获取ix 2 info的信息
    https://www.peeringdb.com/api/ix
    :return ix2info:
    """
    with open("../000LocalData/IXVis/ix.json") as json_file:
        html_json = json.load(json_file)
    ix2info = {}  # ix2info的字典
    for item in html_json['data']:
        ix_id = item['id']
        ix_name = item['name']
        ix_name_long = item['name_long']
        city = item['city']
        country = item['country']
        region = item['region_continent']
        net_count = item['net_count']
        fac_count = item['fac_count']
        if ix_id not in ix2info.keys():
            ix2info[ix_id] = [ix_name, ix_name_long, city, country, region, net_count, fac_count]
    # print("IX原始信息记录表：", len(html_json['data']))
    print("IX信息字典记录：", len(ix2info.keys()))
    return ix2info


def ix_view():
    """
    基于PEERDING DB数据抽取ix和net对应关系，并统计speed信息
    结合AS所属国家信息，构建需要统计的数据项
    """
    as2country_dic = gain_as2country_caida()
    print("AS12389's Country:", as2country_dic['12389'])
    ix2info_dict = gain_ix2info_pdb()
    # html = urlopen(r"https://www.peeringdb.com/api/netixlan")
    # html_json = json.loads(html.read())
    with open("netixlan.json") as json_file:
        html_json = json.load(json_file)
    net_ix_result = []  # 存储网络接入IX的数据
    except_as_ist = []  # 存储异常的AS列表
    for item in html_json['data']:
        ix_id = item['ix_id']
        ix_name = item['name']
        asn = item['asn']
        asn_country = "ZZ"
        try:
            asn_country = as2country_dic[str(asn)]
        except Exception as e:
            except_as_ist.append(e)
        ix_speed = item['speed']
        is_rs_peer = item['is_rs_peer']
        temp_line = [ix_id, ix_name, asn, asn_country, ix_speed, is_rs_peer]
        # print(temp_line)
        net_ix_result.append(temp_line)
    print("已成功统计 %s 个AS-IX的接入关系" % len(net_ix_result))
    # print("存在AS信息缺失记录数量:", len(except_as_ist))
    # print(except_as_ist)
    result_file = "..\\000LocalData\\RU&UA\\as_ix.csv"
    write_to_csv(net_ix_result, result_file)
    """
    基于net_ix_result统计：
    cn 网络在某ix列表中接入带宽的总数
    """
    cn_as_ix_bandwidth = 0  # 记录cn网络接入某ix列表的带宽总数
    group_ix_bandwidth = 0  # 记录某ix列表总的带宽数
    ix_list = ['26', '944', '935', '1812', '1623', '3774', '577',
               '18', '321', '777', '1016', '745', '583', '248',
               '74', '1214', '31', '832', '2587', '2588',
               '2589', '1131', '1149', '1277', '1150', '2531',
               '3446', '3431', '1249', '3378', '3473', '804',
               '3472', '3474', '1002', '2279']
    for item in net_ix_result:
        # print(item)
        if str(item[0]) in ix_list:
            group_ix_bandwidth += int(item[4])
            if item[-3] == "CN":
                cn_as_ix_bandwidth += int(item[4])
    print("Group ix的接入总带宽：", group_ix_bandwidth)
    print("CN网络接入Group ix的总带宽：", cn_as_ix_bandwidth)

    """
    基于net_ix_result统计：
    cn 网络在全球ix列表中接入交换中心以及带宽的总数
    """
    cn_as_ix_bandwidth = 0  # 记录cn网络接入某ix列表的带宽总数
    global_ix_bandwidth = 0  # 记录某ix列表总的带宽数
    us_ix_bandwidth = 0  # 记录cn网络接入美国的总带宽数
    global_ix_list = []  # 统计cn网络接入ix的list

    for item in net_ix_result:
        # print(item)
        global_ix_bandwidth += int(item[4])
        if item[-3] == "CN":
            cn_as_ix_bandwidth += int(item[4])
            global_ix_list.append(item[0])
            ix_country = "ZZ"
            try:
                ix_country = ix2info_dict[item[0]][3]
            except Exception as e:
                except_info_list.append(e)
            # print(ix_country)
            if ix_country == "US":
                print(item)
                us_ix_bandwidth += int(item[4])

    print("Global ix的接入总带宽：", global_ix_bandwidth)
    print("CN网络接入Global ix的总带宽：", cn_as_ix_bandwidth)
    print("CN网络接入US ix的总带宽：", us_ix_bandwidth)
    print("CN网络接入全球ix的数量：", len(set(global_ix_list)))


if __name__ == "__main__":
    time_start = time.time()
    ix_view()
    print("=>Scripts Finish, Time Consuming:", (time.time() - time_start), "S")
