# coding:utf-8
"""
create on July 28, 2020 By Wenyan YU
Email: ieeflsyu@outlook.com

Function:

V2:

在第一版的基础上，新增U和Five的AS号，第一版的数据中重要ISP的AS网络找的不全
这一版把重要ISP所有的注册AS网都剔除（可能存在一些，现网没有通告的AS号，在做剔除的时候，需要先做一个判断）

V3：
在第二版的基础上，新增对不可达AS的信息统计，如IP量（v4地址量）以及IP量所对应的区域
由于之前在caict_display的项目做过一些统计，此处暂时就先用统计后的结果，以节约IP量统计的时间
000LocalData/caict_display/as2ip_quantity_plus.csv
000LocalData/caict_display/as_info_format.csv

"""
import time
import csv
import networkx as nx
from networkx.algorithms.flow import shortest_augmenting_path


def write_to_csv(res_list, des_path):
    """
    把给定的List，写到指定路径的文件中
    :param res_list:
    :param des_path:
    :return: None
    """
    print("write file <%s> ..." % des_path)
    csvFile = open(des_path, 'w', newline='', encoding='gbk')
    try:
        writer = csv.writer(csvFile, delimiter=",")
        for i in res_list:
            writer.writerow(i)
    except Exception as e:
        print(e)
    finally:
        csvFile.close()
    print("write finish!")


def gain_country_info():
    """
    根据国家的缩写，翻译为中文
    :return country_info_dict:
    """
    geo_file = '../000LocalData/as_geo/GeoLite2-Country-Locations-zh-CN.csv'
    country_info_dict = {}
    file_read = open(geo_file, 'r', encoding='utf-8')
    for line in file_read.readlines():
        line = line.strip().split(',')
        # print(line)
        country_info_dict[line[4]] = line[5]
    return country_info_dict


def extract_as_info():
    """
    根据asn_info文件，提取as info 信息
    :return:
    """
    as2country_cn = gain_country_info()
    # file_in = "../000LocalData/as_map/as_core_map_data_new20200701.csv"
    # file_in_read = open(file_in, 'r', encoding='utf-8')
    # as2country_dict = {}  # 存储as号和国家对应关系的字典
    # for line in file_in_read.readlines():
    #     line = line.strip().split("|")
    #     # print(as2country_cn[line[1].split(",")[-1].strip()])
    #     as2country_dict[line[0]] = as2country_cn[line[8]].strip("\"")
    file_in = "../000LocalData/as_Gao/asn_info.txt"
    file_in_read = open(file_in, 'r', encoding='utf-8')
    as2country_dict = {}  # 存储as号和国家对应关系的字典
    for line in file_in_read.readlines():
        line = line.strip().split("\t")
        # print(as2country_cn[line[1].split(",")[-1].strip()])
        as2country_dict[line[0]] = as2country_cn[line[1].split(",")[-1].strip()].strip("\"")
    return as2country_dict


def gain_as_ip_num(as_list):
    """
    根据传入的as_list，以as2ip_quantity_plus.csv作为输入，统计总的ip量
    :param as_list:
    :return global_ip_num:
    :return global_ip_prefix:
    :return has_ip_info_cnt:
    :return has_country_info)_cnt:
    """
    as2country_dict = extract_as_info()  # 存储as2country的中文信息
    # print("IP量统计AS计数:", len(as_list))
    global_ip_num, global_ip_prefix = 0, 0
    as2ip_num_dict = {}
    as2ip_num_file = "../000LocalData/caict_display/as2ip_quantity_plus.csv"
    file_read = open(as2ip_num_file, 'r', encoding='utf-8')
    for line in file_read.readlines():
        line = line.strip().split(",")
        as2ip_num_dict[line[0].strip("AS")] = [line[1], line[2], line[3], line[4]]
    has_ip_info_cnt = 0  # 存储存在IP通告信息统计
    has_country_info_cnt = 0  # 存储存在国家信息统计
    rank_country_ip_num_dict = {}  # 存储每个国家通道IP量的统计
    for item_as in as_list:
        if item_as in as2ip_num_dict.keys():
            global_ip_num += int(as2ip_num_dict[item_as][1])
            global_ip_prefix += int(as2ip_num_dict[item_as][0])
            has_ip_info_cnt += 1
            if item_as in as2country_dict.keys():
                # print(as2country_dict[item_as])
                if as2country_dict[item_as] in rank_country_ip_num_dict.keys():
                    rank_country_ip_num_dict[as2country_dict[item_as]] += int(as2ip_num_dict[item_as][1])
                else:
                    rank_country_ip_num_dict[as2country_dict[item_as]] = int(as2ip_num_dict[item_as][1])
                has_country_info_cnt += 1
    # print(rank_country_ip_num_dict)
    return global_ip_num, global_ip_prefix, has_ip_info_cnt, has_country_info_cnt, rank_country_ip_num_dict


def reach_analysis(cn_as, us_as, five_as):
    """
    根据传入的cn_as、us_as、five_as，分别CN网络全球可达性指标r0、r1、r2
    先从简单的实现开始，后面再考虑算法的时间复杂度和空间复杂度
    :param cn_as:
    :param us_as:
    :param five_as:
    :return:
    """
    global_as_graph = nx.Graph()  # 生成空图，用于在内存中构建全球互联网网络拓扑
    print("CN AS Group:", cn_as)
    # print("US AS Group:", us_as)
    # print("Five AS Group:", five_as)
    as_rel_file = "../000LocalData/as_relationships/serial-1/20200701.as-rel.txt"
    file_read = open(as_rel_file, 'r', encoding='utf-8')
    global_as = []  # 存储全球所有的AS号
    global_reach_as = []  # 存储全球所有可达的AS号
    for line in file_read.readlines():
        if line.strip().find("#") == 0:
            continue
        as_0 = str(line.strip().split('|')[0])
        as_1 = str(line.strip().split('|')[1])
        # 根据边构建全球互联网网络拓扑图
        global_as_graph.add_edge(as_0, as_1)
        # print(as_0, as_1)
        global_as.append(as_0)
        global_as.append(as_1)
        # 判断与CN网络直联的网络数量
        if as_0 in cn_as:
            global_reach_as.append(as_1)
        if as_1 in cn_as:
            global_reach_as.append(as_0)

    print("Global AS Count:", len(set(global_as)))
    print("Global Reach AS Count（直联情况）:", len(set(global_reach_as)))

    print("=>根据构建的全球AS拓扑图，统计全球网络拓扑特征")
    print("=>全球互联网网络拓扑图（原始）")
    print("拓扑图节点数量:", global_as_graph.number_of_nodes())
    print("拓扑图连边数量:", global_as_graph.number_of_edges())
    # print("图的平均连接性:", nx.all_pairs_node_connectivity(global_as_graph))
    # print("计算源目之间不相交的节点路径:", nx.node_disjoint_paths(global_as_graph, "4134", "4809"))
    # for item in list(nx.node_disjoint_paths(global_as_graph, "4134", "4809")):
    #     print(item)
    not_reach_as = []  # 存储不可达的网络
    reach_as = []  # 存储可达网络的数量
    for as_item in global_as_graph.nodes():
        reach_flag = 0  # 网络可达标记，默认为不可达
        for cn_as_item in cn_as:
            if nx.has_path(global_as_graph, cn_as_item, as_item):
                reach_flag = 1
                break
        if reach_flag == 1:
            reach_as.append(as_item)
        else:
            not_reach_as.append(as_item)
    print("CN网络到全球可达AS的数量：", len(reach_as))
    print("CN网络到全球不可达AS的数量：", len(not_reach_as))
    print("CN网络到全球可达性(r0):", len(reach_as)/len(set(global_as)))
    global_ip_num, global_ip_prefix, has_ip_info_cnt, has_country_info_cnt, country_ip_dict = gain_as_ip_num(reach_as)
    cn_ip_num = country_ip_dict["中国（大陆）"]
    print("地址统计has_info(IP)校验：", has_ip_info_cnt)
    print("地址统计has_info(Country)校验：", has_country_info_cnt)
    print("CN网络到全球可达前缀数量:", global_ip_prefix)
    print("CN网络到全球可达IP地址数量规模:", (global_ip_num-cn_ip_num))
    original_global_ip_prefix = global_ip_prefix
    original_global_ip_num = global_ip_num - cn_ip_num  # 中国到全球，应该把中国地址刨去
    print("CN网络到全球前缀可达性(r0):", global_ip_prefix/original_global_ip_prefix)
    print("CN网络到全球IPv4地址可达性(r0):", (global_ip_num-cn_ip_num)/original_global_ip_num)

    print("\n=>全球互联网网络拓扑图（剔除U-AS-Group）")
    print("输入剔除的网络个数:", len(us_as))
    remove_cnt = 0  # 记录剔除的网络个数
    for as_item in us_as:
        if as_item in global_as_graph.nodes():
            global_as_graph.remove_node(as_item)
            remove_cnt += 1
    print("实际剔除的网络个数:", remove_cnt)
    print("拓扑图节点数量:", global_as_graph.number_of_nodes())
    print("拓扑图连边数量:", global_as_graph.number_of_edges())
    not_reach_as = []  # 存储不可达的网络
    reach_as = []  # 存储可达网络的数量
    for as_item in global_as_graph.nodes():
        reach_flag = 0  # 网络可达标记，默认为不可达
        for cn_as_item in cn_as:
            if nx.has_path(global_as_graph, cn_as_item, as_item):
                reach_flag = 1
                break
        if reach_flag == 1:
            reach_as.append(as_item)
        else:
            not_reach_as.append(as_item)
    print("CN网络到全球可达AS的数量：", len(reach_as))
    print("CN网络到全球不可达AS的数量：", len(not_reach_as))
    print("CN网络到全球可达性(r1):", len(reach_as)/len(set(global_as)))
    global_ip_num, global_ip_prefix, has_ip_info_cnt, has_country_info_cnt, country_ip_dict = gain_as_ip_num(reach_as)
    print("地址统计has_info(IP)校验：", has_ip_info_cnt)
    print("地址统计has_info(Country)校验：", has_country_info_cnt)
    # print("CN网络到全球可达前缀数量:", global_ip_prefix)
    print("CN网络到全球可达IP地址数量规模:", (global_ip_num-cn_ip_num))
    # print("CN网络到全球前缀可达性(r1):", global_ip_prefix/original_global_ip_prefix)
    print("CN网络到全球IPv4地址可达性(r1):", (global_ip_num-cn_ip_num)/original_global_ip_num)

    print("\n=>全球互联网网络拓扑图（剔除Five-AS-Group）")
    for as_item in five_as:
        if as_item in global_as_graph.nodes():
            global_as_graph.remove_node(as_item)
            remove_cnt += 1
    print("输入剔除的网络个数:", (len(us_as)+len(five_as)))
    print("累计剔除的网络个数:", remove_cnt)
    print("拓扑图节点数量:", global_as_graph.number_of_nodes())
    print("拓扑图连边数量:", global_as_graph.number_of_edges())
    not_reach_as = []  # 存储不可达的网络
    reach_as = []  # 存储可达网络的数量
    for as_item in global_as_graph.nodes():
        reach_flag = 0  # 网络可达标记，默认为不可达
        for cn_as_item in cn_as:
            if nx.has_path(global_as_graph, cn_as_item, as_item):
                reach_flag = 1
                break
        if reach_flag == 1:
            reach_as.append(as_item)
        else:
            not_reach_as.append(as_item)
    print("CN网络到全球可达AS的数量：", len(reach_as))
    print("CN网络到全球不可达AS的数量：", len(not_reach_as))
    print("CN网络到全球可达性(r2):", len(reach_as)/len(set(global_as)))
    global_ip_num, global_ip_prefix, has_ip_info_cnt, has_country_info_cnt, country_ip_dict = gain_as_ip_num(reach_as)
    print("地址统计has_info(IP)校验：", has_ip_info_cnt)
    print("地址统计has_info(Country)校验：", has_country_info_cnt)
    # print("CN网络到全球可达前缀数量:", global_ip_prefix)
    print("CN网络到全球可达IP地址数量规模:", (global_ip_num-cn_ip_num))
    # print("CN网络到全球前缀可达性(r2):", global_ip_prefix/original_global_ip_prefix)
    print("CN网络到全球IPv4地址可达性(r2):", (global_ip_num-cn_ip_num)/original_global_ip_num)


if __name__ == "__main__":
    cn_as_group = ["4134", "4809", "4837", "9929", "58453"]
    us_as_group = ["9265", "8110", "8109", "8108", "8107", "8106", "7882", "7421", "7308", "7210",
                   "6637", "6449", "6242", "6211", "6187", "6177", "6176", "6175", "6174", "6158",
                   "6157", "6156", "6155", "6154", "6153", "5732", "56875", "56514", "5084", "5079",
                   "4999", "4951", "4950", "4938", "4910", "43235", "42451", "41106", "4005", "4004",
                   "4003", "4002", "4001", "4000", "3992", "3991", "3990", "3989", "3988", "3987",
                   "3986", "3985", "3984", "3983", "3982", "3981", "3980", "3979", "3978", "3977",
                   "3973", "3972", "3652", "3651", "3650", "3649", "3648", "3647", "3646", "3645",
                   "3644", "3643", "3483", "33884", "3041", "3040", "3039", "3038", "3037", "3036",
                   "3035", "3034", "3033", "3032", "3031", "3030", "3029", "3028", "3027", "3026",
                   "3025", "3024", "3023", "3022", "3021", "3020", "3019", "3018", "3017", "3016",
                   "3015", "3014", "3013", "3012", "3011", "3010", "3009", "3008", "3007", "3006",
                   "3005", "3004", "3003", "3002", "3001", "3000", "2999", "2998", "2997", "2996",
                   "2995", "2994", "2993", "2992", "2991", "2990", "2989", "2988", "2987", "2986",
                   "2985", "2984", "2983", "2982", "2981", "2980", "2979", "2978", "2977", "2976",
                   "2975", "2974", "2973", "2972", "2971", "2970", "2969", "2968", "2967", "2966",
                   "2965", "2964", "2963", "2962", "2961", "2960", "2959", "2958", "2957", "2956",
                   "2955", "2954", "2953", "2952", "2951", "2950", "2949", "2948", "2947", "2946",
                   "2945", "2944", "2943", "2942", "2938", "270261", "24787", "23044", "21288", "2053",
                   "2050", "197226", "1808", "1807", "1806", "1805", "1804", "1803", "1802", "1801",
                   "1800", "1799", "1795", "1794", "1793", "1792", "1791", "1790", "1789", "17133",
                   "137463", "131786", "1240", "1239", "1238", "11461", "10507",
                   "7922", "7853", "7757", "7725", "7016", "7015", "6161", "53297", "396415", "396021",
                   "396019", "396017", "395980", "395976", "395974", "395848", "393232", "36733", "36732", "36377",
                   "36196", "33668", "33667", "33666", "33665", "33664", "33663", "33662", "33661", "33660",
                   "33659", "33658", "33657", "33656", "33655", "33654", "33653", "33652", "33651", "33650",
                   "33542", "33491", "33490", "33489", "33351", "33287", "269002", "264821", "23266", "23253",
                   "22909", "22258", "21508", "202149", "20214", "16748", "14668", "14042", "13385", "13367",
                   "132401", "11025",
                   "7982", "7458", "7061", "6496", "6494", "6299", "6259", "4550", "22099", "2149", "19164", "174",
                   "16631", "140664", "13129", "12207", "11526", "11220", "11024", "10768",
                   "58682", "138951",
                   "6431", "23143", "140237", "140235", "140234", "140233", "140232", "134537", "134536", "134535",
                   "134534", "134533", "134532", "134531", "134530",
                   "9555", "9194", "9062", "9055", "8768", "8671", "8385", "8243", "817", "816",
                   "815", "814", "813", "8115", "8114", "8113", "8112", "8017", "8016", "7836",
                   "7193", "7192", "705", "7046", "704", "703", "7021", "702", "7014", "701",
                   "6995", "6984", "6976", "6811", "6541", "6350", "6256", "6167", "6113", "6066",
                   "5725", "5621", "5614", "5599", "5586", "50146", "4981", "4908", "4860", "4313",
                   "4239", "4183", "4017", "3966", "3965", "3964", "3963", "394260", "3707", "3493",
                   "33052", "32471", "28625", "284", "2830", "2828", "28122", "2634", "2548", "23626",
                   "23148", "22521", "22394", "21910", "2125", "19973", "19699", "19698", "19262", "19028",
                   "19027", "19026", "19025", "1890", "18654", "18653", "18652", "18573", "1849", "18461",
                   "17106", "16224", "15572", "15429", "15308", "15133", "15060", "15058", "15057", "15056",
                   "14551", "14407", "14406", "14405", "14311", "14210", "14153", "14040", "13671", "13670",
                   "13669", "13668", "13667", "13666", "13665", "13664", "13663", "13662", "13661", "13562",
                   "12702", "12585", "12367", "12234", "12199", "12079", "11486", "11371", "11303", "11149",
                   "11148", "11147", "11146", "11145", "11113", "10805", "10784", "10720", "10719", "10027 ",
                   "6939", "6427", "393338", "20341",
                   "97", "93", "7019", "6944", "685", "62609", "53550", "46108", "396071", "3949", "3948",
                   "3947", "3946", "3945", "3942", "3941", "3940", "3939", "3938", "3937", "3936", "393536",
                   "3934", "3844", "37923", "37900", "3745", "35953", "3150", "2914", "280", "275", "27023",
                   "263", "262", "253", "23461", "21576", "20110", "19810", "19809", "19808", "19807", "19806",
                   "19805", "19804", "19803", "18491", "18490", "18489", "18488", "18487", "18486", "18485",
                   "18484", "17307", "13500", "1294", "1225", "114", "11158", "11018", "10848", "10743",
                   "6453", "6421",
                   "8218", "6461", "4997", "36841", "33321", "32327", "31993", "31933", "31932", "31555",
                   "31367", "27540", "22969", "19158", "19092", "17025", "16503", "13555", "11359",
                   "9057", "7991", "7990", "7989", "7988", "7987", "7986", "7776", "7359", "7191", "7161",
                   "6745", "6640", "6367", "6347", "6227", "6226", "6225", "6224", "6223", "6222", "6100",
                   "5778", "5737", "5668", "4911", "4298", "4297", "4296", "4295", "4294", "4293", "4292",
                   "4291", "4290", "4289", "4288", "4287", "4285", "4284", "4283", "4282", "4281", "4212",
                   "4048", "4015", "3951", "394190", "394179", "394125", "394120", "393789", "393645", "3910",
                   "3909", "3908", "3561", "3447", "32855", "27497", "2379", "23126", "22561", "22186", "209",
                   "202818", "18494", "17402", "17047", "16941", "16835", "16718", "14921", "14910", "14905", "13787",
                   "11538", "11530", "11415", "11412", "11398", "11226", "11225", "11104", "10960", "10833", "10832",
                   "10831", "10830", "10829", "10828", "10827", "10826", "10825", "10424", "10383",
                   "7262", "6279", "3491", "26957", "25178",
                   "3356", "3549", "7018"]

    five_as_group_except_US = ["9901", "9500", "8761", "8760", "8709", "8576", "8546", "8386", "7714", "7657", "6847",
                               "6757", "6751", "6739", "6660", "62211", "5551", "55436", "55410", "5428", "5388",
                               "5378", "50973", "48728", "4768", "4763", "44957", "4445", "41883", "38748", "38442",
                               "38266", "36935", "35080", "34912", "34419", "33915", "33874", "3329", "3273", "3211",
                               "3209", "31654", "31334", "30995", "30722", "29562", "26641", "25310", "25135", "24835",
                               "21625", "21435", "21334", "21044", "20825", "203642", "203237", "201917", "201829",
                               "18291", "17993", "17808", "17435", "16338", "16019", "15924", "15897", "15709",
                               "15524", "15502", "15480", "136987", "134071", "133612", "133580", "13217", "13144",
                               "13143", "13083", "13066", "13017", "12970", "1273", "12663", "12636", "12430",
                               "12420", "12361", "12357", "12353", "12302",
                               "8472", "6871", "6685", "57688", "5400", "3310", "3300", "2856", "2855", "25127",
                               "25041", "204047", "15697", "13205", "12641",
                               "9909", "9904", "9740", "9625", "9582", "9225", "8656", "7543", "4637", "4632",
                               "4629", "38179", "197452", "18193", "18050", "17801", "17744", "135887", "135599",
                               "133931", "132292", "132029", "131073", "1290", "12471", "1221", "10026",
                               "8160", "812", "7780", "54412", "54317", "40383", "393431", "36868", "36676",
                               "3602", "35843", "33041", "31989", "30147", "26788", "26230", "2493", "2492",
                               "2491", "20453", "19835", "18475", "16661", "14472", "14366", "14008", "12021",
                               "855", "831", "830", "829", "8187", "7398", "7122", "684", "6608", "6539", "603",
                               "602", "601", "58147", "577", "50801", "50734", "47509", "45648", "4390", "40957",
                               "40183", "39971", "398027", "394255", "37126", "36522", "11566", "11489",
                               "9325", "59353", "55936", "4771", "38485", "2570", "2569", "208570", "202579", "15170",
                               "135882", "135881", "133473", "133124",
                               "4647"]
    time_start = time.time()  # 记录启动的时间
    reach_analysis(cn_as_group, us_as_group, five_as_group_except_US)
    time_end = time.time()  # 记录结束的时间
    print("=>Scripts Finish, Time Consuming:", (time_end - time_start), "S")
