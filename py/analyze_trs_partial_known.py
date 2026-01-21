import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import trsfile

# 数据预处理
def preprocess_data(traces_file_path, n_samples_per_trace=100):
    traces = trsfile.open(traces_file, 'r')
    samples = [trace.samples[:n_samples_per_trace] for trace in traces]
    scaler = StandardScaler()
    return scaler.fit_transform(samples)

# K-Means初步聚类
def kmeans_initialization(known_samples, unknown_samples, n_clusters=2):
    combined_samples = np.concatenate((known_samples, unknown_samples))
    km = KMeans(
        n_clusters=n_clusters,
        init='k-means++',
        n_init=10,
        max_iter=300,
        tol=0.0000001,
        verbose=0,
        random_state=None,
        copy_x=True,
        algorithm='elkan'
    ).fit(combined_samples)    # 用已知样本和未知样本一起聚类
    known_cluster_centers = km.cluster_centers_[:len(known_samples)] # 取前n_clusters个作为已知样本的聚类中心
    return known_cluster_centers

# 自定义模糊C均值聚类迭代
def fuzzy_cmeans_iterative(data, initial_centers, m=2, error=0.000001, maxiter=1000):
    # 初始化隶属度矩阵
    u = np.ones((data.shape[0], initial_centers.shape[0])) / initial_centers.shape[0]
    
    for _ in range(maxiter):
        u_old = u.copy()
        # 更新隶属度
        for i in range(data.shape[0]):
            distances = np.linalg.norm(data[i] - initial_centers, axis=1)
            u[i] = 1 / (distances ** (2 / (m - 1))) # 模糊化隶属度更新
        
        # 更新聚类中心
        u_sum = np.sum(u, axis=0)
        for j in range(initial_centers.shape[0]):
            initial_centers[j] = np.sum(data * u[:,j][:, np.newaxis], axis=0) / u_sum[j]
            
        # 检查收敛性
        if np.abs(u - u_old).sum() < error:
            break
    return initial_centers, u

# 加载入数据
traces_file = '32bit-share1-2-1000-500M.trs'
standardized_data = preprocess_data(traces_file)

# 已知样本初始化
known_samples = standardized_data[:2]
unknown_samples = standardized_data[2:]

# K-Means初步聚类
initial_centers = kmeans_initialization(known_samples, unknown_samples)

# 执行模糊C均值聚类
final_centers, u = fuzzy_cmeans_iterative(standardized_data, initial_centers, m=2, error=0.000001)

# 后处理与评估
def assign_labels(u):
    labels = np.argmax(u, axis=1)
    return labels

labels = assign_labels(u)

# # 可以已知信息强化（简化处理）
# for known_sample, known_label in zip(known_samples, labels[:len(known_samples)]):
#     if known_label != 0:  # 假设已知样本应属于第一个类
#         labels[known_samples.index(known_sample)] = 0

print(u)
# 输出
print("Final Cluster Centers:", final_centers)
print("Labels:", labels)