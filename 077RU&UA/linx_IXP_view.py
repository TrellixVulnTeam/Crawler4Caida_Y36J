# coding:utf-8
"""
create on Mar 14, 2022 By Wenyan YU

Function：

针对LINX终止Rostelecom和MegaFon流量交换服务事件的分析

1）俄网络在全球总接了多少个IX，涉及多少个网络（OPEN PEER）,总的带宽，以及占俄国际带宽的比例;
2）MSK-IX接入成员所属国家，以及带宽的比例统计。

"""
from urllib.request import urlopen
import json
import time
import csv


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


def ix_view():
    """
    基于PEERDING DB数据抽取ix和net对应关系，并统计speed信息
    结合AS所属国家信息，构建需要统计的数据项
    """
    as2country_dic = gain_as2country_caida()
    print("AS12389's Country:", as2country_dic['12389'])
    html = urlopen(r"https://www.peeringdb.com/api/netixlan")
    html_json = json.loads(html.read())
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
    1）俄网络在全球总接了多少个IX，涉及多少个网络（OPEN PEER）,总的带宽，以及占俄国际带宽的比例；
    构建ix_info_dic字典，记录[asn,bandwidth], ....
    """
    ru_as_ix = []  # 记录俄罗斯网络接入的的ix
    ru_as_ix_bandwidth = 0  # 记录俄罗斯网络接入全球ix总的带宽
    global_ix_bandwidth = 0  # 记录全球ix接入带宽
    ix_as_peer_dic = {}  # 统计每个ix中peer网络

    for item in net_ix_result:
        ru_as_ix.append(item[0])
        global_ix_bandwidth += int(item[4])
        if item[-3] == "RU":
            ru_as_ix_bandwidth += int(item[4])
        peer_flag = item[-1]
        if peer_flag:
            if item[0] not in ix_as_peer_dic.keys():
                ix_as_peer_dic[item[0]] = [item[2]]
            else:
                ix_as_peer_dic[item[0]].append(item[2])
    # print(ix_as_peer_dic)

    ru_peer_ix = []  # 存储俄网络在全球的PEER网络
    for key in ix_as_peer_dic.keys():
        temp_as_list = ix_as_peer_dic[key]
        for item_as in temp_as_list:
            item_as_country = "ZZ"
            try:
                item_as_country = as2country_dic[str(item_as)]
            except Exception as e:
                except_as_ist.append(e)
            if item_as_country == "RU":
                ru_peer_ix.extend(ix_as_peer_dic[key])
                break

    print("俄网络在全球的PEER网络:", len(set(ru_peer_ix)))
    print("俄网络在全球总接入ix的数量：", len(set(ru_as_ix)))
    print("俄网络接入全球ix的总带宽：", ru_as_ix_bandwidth)
    print("全球网络接入全球ix的总带宽：", global_ix_bandwidth)

    """
    基于net_ix_result统计：
    2）MSK-IX接入成员所属国家，以及带宽的比例统计。
    """
    country_dic = {}  # 存储莫斯科交换中心总各国国家成员的数量

    ix_count = 0  # 统计莫斯科IX总的接入数量
    ix_bandwidth = 0  # 统计莫斯科IX总的接入带宽
    country_list = ["US", "UK", "UA"]  # 存储待统计的欧美国家
    ix_bandwidth_group = 0  # 统计欧美国家带宽
    for item in net_ix_result:
        if item[0] == 100:
            print(item)
            country = item[3]
            asn = item[2]
            ix_bandwidth += item[-2]
            if country in country_list:
                ix_bandwidth_group += item[-2]

            ix_count += 1
            if country not in country_dic.keys():
                country_dic[country] = [asn]
            else:
                country_dic[country].append(asn)
    print("接入莫斯科交换中心总的数量:", ix_count)
    print("接入莫斯科交换中心总的带宽:", ix_bandwidth)
    print("接入莫斯科交换中心，欧美国家的带宽及其占比：", ix_bandwidth_group, ix_bandwidth_group/ix_bandwidth )
    for key in country_dic.keys():
        print(key, len(country_dic[key]))


if __name__ == "__main__":
    time_start = time.time()
    ix_view()
    print("=>Scripts Finish, Time Consuming:", (time.time() - time_start), "S")
