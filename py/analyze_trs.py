import numpy as np
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler  # 可选，用于数据标准化
import trsfile


# 结合标量值进行的采集和测试
# 打开待聚类的trsfile文件
traces =  trsfile.open('kg_trs_medium_8/kG_power_1114_20_2_seg_y.trs', 'r') 
samples_list = []       # 每条曲线的sample
data_list = []          # 每条曲线的data
for trace in traces:
    samples_list.append(trace.samples)        # 使用前100个点
    data_list.append(trace.parameters.get('LEGACY_DATA', None))

# 使用StandardScaler进行数据标准化
# scaler = StandardScaler()
# standardized_data = scaler.fit_transform(samples_list)

# # PCA主成分分析
# pca = PCA(n_components=200)  # 或者指定具体保留的主成分数量，如 n_components=2
# pca.fit(standardized_data)
# pca_data = pca.transform(standardized_data)

# 将每个bytearray转换为一个NumPy数组，并使用np.uint8作为数据类型。然后，使用np.vstack()将所有数组堆叠成一个二维数组，其中每一行对应一个原始的bytearray。
m_valuelist = []
# for m in range(0, 600, 1):      # 1为单位聚类
m=[14,4,19,9,52]        # 对第30个点聚类
m = [4,9,3,19,10]
m = [2699]
# data_array = np.vstack([np.frombuffer(bytes(sample[m:m+1]), dtype=np.uint8) for sample in samples_list])

data_array = np.array([[sample[pos] for pos in m] for sample in samples_list])
# 假设我们选择K=2作为聚类数量
n_clusters = 2

# 初始化KMeans模型
kmeans = KMeans(n_clusters=n_clusters, algorithm='elkan')  # 使用Hamming距离

# 训练模型（即执行聚类）
kmeans.fit(data_array)

# 获取每个样本的聚类标签
cluster_labels = kmeans.labels_
print(kmeans.cluster_centers_)

clustered_result = [[] for _ in range(n_clusters)]
for i, label in enumerate(cluster_labels):
    clustered_result[label].append(i)



# 根据标量值判断分类是否准确
# 标量值
int_k = int('BC3736A2F4F6779C59BDCEE36B692153D0A9877CC62A474002DF32E52139F0A0', 16)
bin_strk = bin(int_k)[2:]
print(bin_strk)

# 定义两个默认位置对应的是0比特操作
position_0 = [0,257]
position_1 = []

# 遍历二进制字符串，记录每个位置上是0还是1。在samples_list中，由于第0条被占用，记录时均+1
for i in range(len(bin_strk)):
    if bin_strk[i] == '0':
        position_0.append(i+1)
    else:
        position_1.append(i+1)

print(len(position_0))

cnt = 0
for i in range(len(clustered_result[0])):
    if clustered_result[0][i] in position_0:
        cnt += 1

rate = cnt/len(clustered_result[0])

print(len(clustered_result[0]))
print(clustered_result[0])

print(len(clustered_result[1]))
print(rate)

# if rate > 0.9 or rate < 0.1:
#     print(m)
    # print(len(clustered_result[0]))
    # print(len(clustered_result[1]))
    # print(rate)
#     m_valuelist.append(m)

# print(m_valuelist)


    # 分别查看每个聚类中的数据
    # for cluster_id, cluster_trsnum in enumerate(clustered_result):
    #     print(f"Cluster {cluster_id}:")
    #     for trsnum in cluster_trsnum:
    #         print(trsnum)