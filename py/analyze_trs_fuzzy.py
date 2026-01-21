import numpy as np
from skfuzzy.cluster import cmeans
from sklearn.preprocessing import StandardScaler  # 可选，用于数据标准化
from scipy.stats import ttest_ind
import trsfile
from pprint import pprint
import sys


    # 选出泄露最大的前num_pois个兴趣点
def select_pois_with_tthresh(traces_group1: np.array, traces_group2: np.array, num_pois=5, t_thresh=4.5):
        """
        使用t检验的t值选择兴趣点(POIs)。
        traces_group1, traces_group2: 分别代表固定不同因子时的侧信道测量数据集，形状为(n_samples, n_points)。
        t_thresh: t值的阈值，默认为4.5。
        返回一个列表，包含t值超过阈值的点的索引。
        """
        # 确保两个数据集有相同的采样点数
        assert traces_group1.shape[1] == traces_group2.shape[1], "两组数据的采样点数不一致"
        
        pois = []  # 存储t值超过阈值的兴趣点索引
        n_points = traces_group1.shape[1]
        t_statistics = []
        for point in range(n_points):
            # 提取当前点的测量值
            group1_values = traces_group1[:, point]         # 提取二维数组中特定列的值构成数组
            group2_values = traces_group2[:, point]
            
            # 执行t检验
            t_statistic, _ = ttest_ind(group1_values, group2_values, equal_var=False)  # 假设方差不等
            
            t_statistics.append(t_statistic)

        t_statistics = np.array(t_statistics)

        
        # 计算t值的绝对值并排序
        abs_t_statistics = np.abs(t_statistics)
        sorted_indices = np.argsort(abs_t_statistics)[::-1]  # 降序排列并获取索引
        top_n_indices = sorted_indices[:num_pois]  # 获取前num_pois个最大的索引
        top_n_values = t_statistics[top_n_indices]  # 根据索引获取对应的值，注意这里值可能有正有负

        print(f"Top {num_pois} t-statistics and their original positions:")
        for value, index in zip(top_n_values, top_n_indices):
            print(f"Value = {value}, Position = {index}")
            # 判断t值是否超过阈值
            if abs(value) > t_thresh:
                pois.append(index)

        return pois

# 解析聚类结果
def get_fuzzy_labels(u):
    labels = np.argmax(u, axis=0)
    return labels

def hamming_weight(hex_string):
    # 将十六进制字符串转换为二进制字符串（去掉前导的'0b'）
    bin_string = bin(int(hex_string, 16))[2:]
    
    # 计算二进制字符串中'1'的个数，即汉明重量
    count = bin_string.count('1')
    
    return count

def hamming_weights_32(hex_string):
    # 确保输入字符串长度是8的倍数，如果不是，可以决定如何处理，这里简单地忽略不足8位的情况
    if len(hex_string) % 8 != 0:
        print("Warning: The length of the input is not a multiple of 8. Trailing characters will be ignored.")
        return    
    for i in range(0, len(hex_string), 8):  # 每8个字符一组
        # 提取8个字符
        hex_group = hex_string[i:i+8]
        
        # 转换为二进制并计算汉明重量
        bin_string = bin(int(hex_group, 16))[2:]  # 转二进制，去掉前导的'0b'
        weight = bin_string.count('1')  # 计算'1'的数量
        
        print(f"Hex Group: {hex_group} -> Hamming Weight: {weight}")



if __name__ == '__main__':

    hw_diff = 30
    test_folder = "8mults_32bit_256_125M_hwdiff" + str(hw_diff) + "/"

    acq_group_num = 10

    rate = [0]*acq_group_num

    for i in range(acq_group_num):
        # 打开待聚类的trsfile文件
        trs_num = 256
        # traces = trsfile.open("8bit_10mults_32bit_256_500M_hwdiff0/trace_1.trs", 'r') 
        traces = trsfile.open(test_folder + "trace_" + str(i) + ".trs", 'r') 
        samples_list = []       # 每条曲线的sampletes
        data_list = []          # 每条曲线的data
        for trace in traces:
            samples_list.append(trace.samples)        # 使用前100个点
            data_list.append(trace.parameters.get('LEGACY_DATA', None))

        # 使用StandardScaler进行数据标准化
        scaler = StandardScaler()
        standardized_data = scaler.fit_transform(samples_list)

        # 将每个bytearray转换为一个NumPy数组，并使用np.uint8作为数据类型。然后，使用np.vstack()将所有数组堆叠成一个二维数组，其中每一行对应一个原始的bytearray。
        # pois = [14,4,19,9,52]        # 对第30个点聚类


        seg_A = np.array(samples_list[:int(trs_num/2)])
        seg_B = np.array(samples_list[int(-trs_num/2):])
        pois = select_pois_with_tthresh(seg_A, seg_B, 5)

        # pois = [16008, 13758, 11508, 11522, 13772]
        # [9764, 7514, 16513, 9751, 763            3425, 3438, 3439, 7925, 7938
         # print(pois)
        # pois = [3425,3438, 3439, 7925, 7938]
        # pois = [9764, 7514, 16513] 16008, 13758, 11508, 11522, 13772,
        # data_array = np.array([sample[pos] for sample in samples_list for pos in m]).T  # 注意调整为正确的维度排列

        # [15791, 2291, 17166, 14916, 8166, 9041, 3666, 11291, 1416, 5916] DOM
        # [15791, 2291, 17166, 14916, 8166, 9041, 3666, 11291, 5916, 1416] SOSD
        # [2291, 17166, 3666, 8166, 5916, 14916, 15791, 1416, 5499, 9999] SOST
        # [18112, 18145, 17166, 3666, 18151, 2291, 5916, 1416, 18118, 14916] MIA

        # [13541, 8166, 3666, 1416, 12666, 7499, 44, 17291, 2999, 10427]
        # [13541, 8166, 12666, 1416, 3666, 17291, 2291, 7499, 17166, 41]
        # [3417, 5667, 2999, 7499, 1416, 10167, 14249, 11999, 3666, 12666]
        # [3417, 3438, 5667, 3425, 10167, 7925, 14680, 16925, 12430, 7917]
        # pois = [18112]

        data_array = np.array([[sample[pos] for pos in pois] for sample in samples_list]).T


        # 设定模糊聚类参数
        c = 2  # 假设我们选择C（聚类数量）为2
        m = 2  # 模糊化参数，一般取值在1到无穷大，这里取一个简单例子
        error = 0.000001  # 允许误差

        # 执行模糊C均值聚类
        _, u, _, _, _, _, _ = cmeans(data_array, c, m, error, maxiter=1000)

        # 假设u是你的模糊隶属度矩阵
        high_positions = np.argwhere(u > 0.99)

        print(high_positions)

        cluster_labels = get_fuzzy_labels(u)

        # print(cluster_labels)

        # 以下部分保持不变
        clustered_result = [[] for _ in range(c)]
        for j, label in enumerate(cluster_labels):
            clustered_result[label].append(j)

        cntA = 0
        for j in range(len(clustered_result[0])):
            if clustered_result[0][j] < int(trs_num/2):
                cntA += 1

        cntB = 0
        for j in range(len(clustered_result[1])):
            if clustered_result[1][j] >= int(trs_num/2):
                cntB += 1


        rate[i] = (cntA + cntB) / 256.0
        if(rate[i] < 0.5):
            rate[i] = 1 - rate[i] 

        print(len(clustered_result[0]))
        print(len(clustered_result[1]))
        print(rate[i])

        print(clustered_result[0])
        print(clustered_result[1])

    ave_rate = sum(rate)/acq_group_num
    print(test_folder + "的平均区分率为" + str(ave_rate))
