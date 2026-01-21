import numpy as np
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler  # 可选，用于数据标准化
import trsfile

# 打开待聚类的trsfile文件
traces =  trsfile.open('32bit-share1-3-1000-500M.trs', 'r') 
samples_list = []       # 每条曲线的sample
data_list = []          # 每条曲线的data
for trace in traces:
    samples_list.append(trace.samples[345:350])        # 使用前100个点
    data_list.append(trace.parameters.get('LEGACY_DATA', None))

# 使用StandardScaler进行数据标准化
# scaler = StandardScaler()
# standardized_data = scaler.fit_transform(samples_list)

# # PCA主成分分析
# pca = PCA(n_components=200)  # 或者指定具体保留的主成分数量，如 n_components=2
# pca.fit(standardized_data)
# pca_data = pca.transform(standardized_data)

# 将每个bytearray转换为一个NumPy数组，并使用np.uint8作为数据类型。然后，使用np.vstack()将所有数组堆叠成一个二维数组，其中每一行对应一个原始的bytearray。

data_array = np.vstack([np.frombuffer(bytes(sample), dtype=np.uint8) for sample in samples_list])

# 假设我们选择K=2作为聚类数量
n_clusters = 2

# 初始化KMeans模型
kmeans = KMeans(n_clusters=n_clusters, algorithm='elkan')  # 使用Hamming距离

# 训练模型（即执行聚类）
kmeans.fit(data_array)

# 获取每个样本的聚类标签
cluster_labels = kmeans.labels_

clustered_result = [[] for _ in range(n_clusters)]
for i, label in enumerate(cluster_labels):
    clustered_result[label].append(i)

cnt = 0
for i in range(len(clustered_result[0])):
    if clustered_result[0][i]< 500:
        cnt += 1

rate = cnt/len(clustered_result[0])
print(clustered_result[0])
print(clustered_result[1])
print(rate)


# 分别查看每个聚类中的数据
# for cluster_id, cluster_trsnum in enumerate(clustered_result):
#     print(f"Cluster {cluster_id}:")
#     for trsnum in cluster_trsnum:
#         print(trsnum)