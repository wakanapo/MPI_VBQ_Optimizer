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
        a,b = norm.interval(alpha=i/(n+2), loc=0, scale=1)
        ranges.append(a)
        ranges.append(b)
    ranges = np.asarray(ranges)
    ranges /= abs(max(ranges, key=abs))
    return np.sort(ranges) * random.uniform(0.1, 0.7)

def make_linear(n):
    return np.linspace(-1.0, 1.0, n) * random.uniform(0.1, 0.7)

def make_log(n):
     ranges = np.concatenate((-1 * np.logspace(-1, 2.0, num=n),
                              np.logspace(-1, 2.0, num=n)))
     ranges = ranges[0::2]
     ranges /= abs(max(ranges, key=abs))
     return np.sort(ranges) * random.uniform(0.1, 0.7)

def make_random(n):
    ranges = 2.0 * np.random.rand(n) - 1.0
    return np.sort(ranges) * random.uniform(0.1, 0.7)

def main(bit, genom_num, filename, flag):
    if flag == "random":
        genes = []
    else:
        genes = [make_normal(bit), make_linear(bit), make_log(bit)]
    for _ in range(genom_num - len(genes)):
        genes.append(make_random(bit))

    message = genom_pb2.Generation();
    for gene in genes:
        genoms = message.individuals.add()
        genoms.genom.gene.extend(gene)

    with open("{}/data/{}.pb".format(pwd, filename), "wb") as f:
        f.write(message.SerializeToString())

if __name__ =="__main__":
    argv = sys.argv
    if len(argv) != 5:
        print("Usage: Python {} partition# genom# filename flag".format(argv[0]))
        quit()
    main(int(argv[1]), int(argv[2]), argv[3], argv[4])
