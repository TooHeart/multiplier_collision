import numpy as np
from scipy.stats import multivariate_normal
from scipy.stats import pearsonr
from scipy.stats import ttest_ind
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt

import trsfile

# 对模乘的模板攻击类
class ModMultiplyTA:
    def __init__(self, traces_A, traces_B, num_pois=5): # traces_A, traces_B: samples的二维list
        self.num_pois = num_pois
        self.mean_matrix = {0: None, 1: None}
        self.cov_matrix = {0: None, 1: None}
        self.scaler = StandardScaler()
        self.pois = []

        # 数据预处理：标准化
        traces_A_scaled = self.scaler.fit_transform(traces_A)
        traces_B_scaled = self.scaler.transform(traces_B)

        # 兴趣点选择
        selected_pois = self.select_pois_with_tthresh(traces_A_scaled, traces_B_scaled, self.num_pois)
        self.pois = selected_pois
        
        # 特征提取与模板建立
        for label, traces_scaled in zip([0, 1], [traces_A_scaled, traces_B_scaled]):
            self._build_template(selected_pois, traces_scaled, label)
            
    def _build_template(self, selected_pois, traces_scaled, label):
        corr_matrix = np.corrcoef(traces_scaled.T)      # 计算相关系数矩阵

        
        # 特征提取
        features = traces_scaled[:, selected_pois]
        
        # 计算均值和协方差
        mean = np.mean(features, axis=0)
        cov = np.cov(features.T)
        
        self.mean_matrix[label] = mean
        self.cov_matrix[label] = cov

    # 选出泄露最大的前num_pois个兴趣点
    def select_pois_with_tthresh(self, traces_group1: np.array, traces_group2: np.array, num_pois=5, t_thresh=4.5):
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

        #------------------------绘制每个点的t检验结果-----------------------------#
        # plt.figure(figsize=(10, 5))
        # plt.plot(range(1, n_points + 1), t_statistics, marker='o', linestyle='-', color='blue', label='T-statistic')
        # plt.axhline(y=t_thresh, color='red', linestyle='--', linewidth=2, label=f'Significance Threshold ({t_thresh})')

        # # 添加图例和标签
        # plt.title('T-statistics for Each Point')
        # plt.xlabel('Point Index')
        # plt.ylabel('T-statistic Value')
        # plt.legend()

        # # 显示图形
        # plt.show()
        #------------------------------END-------------------------------------#

    def attack(self, test_traces):
        # 将待测试曲线标准化，以适应标准化的模板曲线
        traces_scaled = self.scaler.transform(test_traces)
        guessed_label = [0] * len(traces_scaled)
        for i, trace in enumerate(traces_scaled):
            test_trace = [trace[poi] for poi in self.pois]
            
            # 计算两类模乘操作的似然度
            densities = {}
            for label in self.mean_matrix.keys():
                mvn = multivariate_normal(mean=self.mean_matrix[label], cov=self.cov_matrix[label], allow_singular=True)
                densities[label] = mvn.pdf(test_trace)
            
            # print(densities)
            # 判断归属
            guessed_label[i] = max(densities, key=densities.get)
            
        return guessed_label

# 示例使用
if __name__ == "__main__":
    # 假设traces_A和traces_B分别是r1*A和r2*B操作的侧信道能量迹
    traces_A = trsfile.open('32bit-share1-5000-500M.trs', 'r') 
    traces_B = trsfile.open('32bit-share3-5000-500M.trs', 'r') 
    
    A_samples_list = []       # 曲线集A的sample
    B_samples_list = []       # 曲线集B的sample

    A_data_list = []          # 每条曲线的data
    B_data_list = []          # 每条曲线的data

    for trace in traces_A:
        A_samples_list.append(trace.samples)       
        A_data_list.append(trace.parameters.get('LEGACY_DATA', None))


    for trace in traces_B:
        B_samples_list.append(trace.samples)       
        B_data_list.append(trace.parameters.get('LEGACY_DATA', None))

    # 初始化攻击模型
    mod_attacker = ModMultiplyTA(A_samples_list, B_samples_list, num_pois=2)


    print(mod_attacker.mean_matrix[1])

    # 待攻击曲线
    traces_T = trsfile.open('32bit-share1-3-1000-500M.trs', 'r')
    T_samples_list = []     # 待攻击曲线中取出的sample集合
    for trace in traces_T:
        T_samples_list.append(trace.samples)       

    # 假设test_trace是从新模乘运算得到的能量迹
    test_traces = T_samples_list  # 示例数据，需替换为实际待测数据
    
    # 执行攻击
    classification = mod_attacker.attack(test_traces)
    cnt_a = 0
    cnt_b = 0
    for i, label in enumerate(classification):
        if label == 0 and i <len(classification)/2:
            cnt_a += 1
        if label == 1 and i >=len(classification)/2:
            cnt_b += 1
        print(f"测试样例{i}归属: {'A' if label == 0 else 'B'}")

    # 统计识别正确率
    print(f"A识别正确率: {cnt_a/(len(classification)/2)}")
    print(f"B识别正确率: {cnt_b/(len(classification)/2)}")

    #----------------选择兴趣点测试----------------------#
    seg_A = np.array(test_traces[:500])
    seg_B = np.array(test_traces[-500:])


    pois = mod_attacker.select_pois_with_tthresh(seg_A, seg_B, num_pois=100)

    print(pois)
    #----------------------END--------------------------#
