import numpy as np

def converter(rep_v):
    rep_v = np.array(rep_v)
    rep_v = np.concatenate((-1*rep_v, rep_v), axis=0)
    def f(arr):
        arr = np.array(arr)
        partition = np.array([(rep_v[i] + rep_v[i+1]) / 2 for i in range(len(rep_v)-1)])
        end_idx = len(partition) - 1
        for i in range(end_idx):
            arr[(arr > partition[i]) & (arr <= partition[i+1])] = rep_v[i+1]
        arr[arr <= partition[0]] = rep_v[0]
        arr[arr > partition[end_idx]] = rep_v[end_idx+1]
        return arr
    return f

if __name__=="__main__":
    rep_v = [-2, -1, 0, 1, 2]
    arr = [-2.5, -1.2, 0.2, 1.4]
    print("actual: ", converter(rep_v)(arr))
    print("expect: ", [-2, -1, 0, 1])
