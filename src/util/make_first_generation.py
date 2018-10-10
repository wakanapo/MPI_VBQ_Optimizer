from scipy.stats import norm
import numpy as np
import random
import os
pwd = os.getcwd()
import sys
sys.path.append(pwd+'/src/protos')
import genom_pb2

def make_normal(n):
    ranges = []
    for i in range(1, n + 1, 2):
        a,_ = norm.interval(alpha=i/(n+2), loc=0, scale=1)
        ranges.append(a)
    ranges = np.asarray(ranges)
    ranges /= abs(max(ranges, key=abs))
    return np.sort(ranges) * random.uniform(0.1, 0.7)

def make_linear(n):
    return np.linspace(0, 1.0, n) * random.uniform(0.1, 0.7)

def make_log(n):
     ranges = np.logspace(-1, 2.0, num=2*n)[::2]
     ranges /= abs(max(ranges, key=abs))
     return np.sort(ranges) * random.uniform(0.1, 0.7)

def make_random(n):
    ranges = 1.0 * np.random.rand(n)
    return np.sort(ranges) * random.uniform(0.1, 0.7)

def main(bit, genom_num, filename, flag):
    if flag == "intent":
        genes = [make_normal(bit), make_linear(bit), make_log(bit)]
    else:
        genes = []
    for _ in range(genom_num*repeat_times - len(genes)):
        genes.append(make_random(bit))

    message = genom_pb2.Generation();
    for i in range(genom_num):
        individual = message.individuals.add()
        for j in range(repeat_times):
            genom = individual.genoms.genom.add()
            genom.gene.extend(genes[i*repeat_times+j])

    with open("{}/data/{}.pb".format(pwd, filename), "wb") as f:
        f.write(message.SerializeToString())

if __name__ =="__main__":
    argv = sys.argv
    if len(argv) != 5:
        print("Usage: Python {} partition# genom# filename flag".format(argv[0]))
        quit()
    if argv[4].isdecimal():
        repeat_times = int(argv[4])
    else:
        repeat_times = 1
    main(int(argv[1]), int(argv[2]), argv[3], argv[4])
