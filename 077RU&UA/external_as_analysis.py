# coding:utf-8
"""
create on Mar 3, 2022 By Wayne YU

Function:

俄乌网络分析

俄、乌、中亚六国、中，对外互联情况
其中乌、中亚六国、中要分析其对外互联中俄的占比
俄要分析其对于Tier 1的占比

俄罗斯（RU）
中亚六国哈萨克斯坦（KZ）、吉尔吉斯斯坦(KG)、塔吉克斯坦（TJ）、乌兹别克斯坦(UZ)、土库曼斯坦(TM)、阿富汗斯坦（AF）
中国（CN）
乌克兰（UA）

"""

import time
import csv
import os
import matplotlib.pyplot as plt

tier1_list = ['7018', '3320', '3257', '6830', '3356',
              '2914', '5511', '3491', '1239', '6453',
              '6762', '1299', '12956', '701', '6461']


def write_to_csv(res_list, des_path):
    """
    把给定的List，写到指定路径的文件中
    :param res_list:
    :param des_path:
    :return: None
    """
    print("write file <%s> ..." % des_path)
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


def gain_as2country():
    """
    根据传入的as info file信息获取AS与国家的对应字典
    :return as2country:
    """
    as_info_file = '..\\000LocalData\\as_Gao\\asn_info.txt'
    as2country = {}  # 存储as号到country的映射关系
    file_read = open(as_info_file, 'r', encoding='utf-8')
    for line in file_read.readlines():
        line = line.strip().split("\t")
        as_number = line[0]
        as_country = line[1].strip().split(",")[-1].strip()
        as2country[as_number] = as_country
    return as2country


def gain_as2country_caida():
    """
    根据Caida asn info获取as对应的国家信息
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


def external_as_analysis(country, as2country):
    """
    根据输入的国家，统计该国家的出口AS数量及其互联方向的统计分析
    :param country:
    :param as2country:
    :return:
    """
    print(country)
    # 获取1998-2020年间全球BGP互联关系的存储文件
    file_path = []
    for root, dirs, files in os.walk("..\\000LocalData\\as_relationships\\serial-1"):
        for file_item in files:
            file_path.append(os.path.join(root, file_item))

    for path_item in file_path[-3:-2]:
        except_as_info = []  # 存储缺失信息的AS
        print(path_item)
        # 遍历一次文件，获取该国出口AS的数量
        file_read = open(path_item, 'r', encoding='utf-8')
        external_cnt = 0  # 存储该国出口连边的数量
        external_as_list = []  # 存储出口AS
        external_country_list = []  # 存储该国出口方向的国家
        external_as_out_list = []  # 存储与该国互联的国外网络数量
        for line in file_read.readlines():
            if line.strip().find("#") == 0:
                continue
            try:
                if as2country[str(line.strip().split('|')[0])] == country:
                    if as2country[str(line.strip().split('|')[1])] != country:
                        external_cnt += 1
                        external_as_list.append(str(line.strip().split('|')[0]))
                        external_country_list.append(as2country[str(line.strip().split('|')[1])])
                        external_as_out_list.append(str(line.strip().split('|')[1]))
                else:
                    if as2country[str(line.strip().split('|')[1])] == country:
                        external_cnt += 1
                        external_as_list.append(str(line.strip().split('|')[1]))
                        external_country_list.append(as2country[str(line.strip().split('|')[0])])
                        external_as_out_list.append(str(line.strip().split('|')[0]))
            except Exception as e:
                except_as_info.append(e)

        print("缺失信息的AS数量:", len(except_as_info))
        external_as_list = list(set(external_as_list))
        print("External Edges Count:", external_cnt)
        print("External AS Count:", len(external_as_list))
        print("External Country Count:", len(list(set(external_country_list))))
        print("External AS Count other Country:", len(list(set(external_as_out_list))))

        # 统计互联国家方向的排名
        external_country_rank = {}
        for item in list(set(external_country_list)):
            external_country_rank[item] = 0
        for item in external_country_list:
            external_country_rank[item] += 1
        # print(len(external_country_rank))

        # 统计出口AS互联关系中美国、俄罗斯、日本、中国香港的占比
        if country == "US":
            # print("All External Edges  （US）: %s, %f%%" % (external_country_rank["US"], float(external_country_rank["US"]/external_cnt) * 100))
            print("All External Edges  （UA）: %s, %f%%" % (external_country_rank["UA"], float(external_country_rank["UA"]/external_cnt) * 100))
            print("All External Edges  （CN）: %s, %f%%" % (external_country_rank["CN"], float(external_country_rank["CN"]/external_cnt) * 100))
        else:
            print("All External Edges  （RU）: %s, %f%%" % (external_country_rank["RU"], float(external_country_rank["RU"]/external_cnt) * 100))
            print("All External Edges  （US）: %s, %f%%" % (external_country_rank["US"], float(external_country_rank["US"]/external_cnt) * 100))

        # 将字典转为列表
        external_country_rank_list = []
        temp_list = []
        for item in external_country_rank.keys():
            temp_list.append(item)
            temp_list.append(external_country_rank[item])
            external_country_rank_list.append(temp_list)
            temp_list = []
        external_country_rank_list.sort(reverse=True, key=lambda elem: int(elem[1]))
        print(external_country_rank_list)
        draw_bar(external_country_rank_list, country)


def draw_bar(rank_list, country):
    """
    根据传入的rank_list信息绘制直方图
    :param rank_list:
    :param country:
    :return:
    """
    x_list = []
    y_list = []

    for item in rank_list:
        x_list.append(item[0])
        y_list.append(item[1])
    # 开始绘图
    fig, ax = plt.subplots(1, 1, figsize=(42, 8))
    title_string = "External BGP Relationships Analysis:" + country + "( Date:20200101 )"
    ax.set_title(title_string)
    color = ['blue']
    plt.bar(x_list, y_list, width=0.7, color=color)
    for x, y in zip(x_list, y_list):
        plt.text(x, y + 0.05, '%.0f' % y, ha='center', va='bottom', fontsize=11)
    ax.set_xlabel('Country')
    ax.set_ylabel('Relationships Nums')
    plt.savefig("..\\000LocalData\\RU&UA\\External_BGP_Rel_" + country + ".jpg")


if __name__ == "__main__":
    time_start = time.time()  # 记录启动时间
    # country_to_analysis = ["RU", "KZ", "KG", "TJ", "UZ", "TM", "UA", "CN"]
    country_to_analysis = ["US", "DE", "FR", "CN"]
    as2country_dict = gain_as2country()
    for country_item in country_to_analysis:
        external_as_analysis(country_item, as2country_dict)
    time_end = time.time()
    print("=>Scripts Finish, Time Consuming:", (time_end - time_start), "S")
