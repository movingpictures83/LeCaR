from disk_struct import Disk
from page_replacement_algorithm import  page_replacement_algorithm
from priorityqueue import priorityqueue
from CacheLinkedList import CacheLinkedList
import time
import numpy as np
import Queue
import heapq
# import matplotlib.pyplot as plt
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
# sys.path.append(os.path.abspath("/home/giuseppe/))

## Keep a LRU list.
## Page hits:
##      Every time we get a page hit, mark the page and also move it to the MRU position
## Page faults:
##      Evict an unmark page with the probability proportional to its position in the LRU list.
class LeCaR5(page_replacement_algorithm):

#     def __init__(self, N, visualization = True):
    def __init__(self, cache_size, learning_rate=0, initial_weight=0.5, discount_rate=1, visualize=0):

        #assert 'cache_size' in param

        self.N = int(cache_size)

        if self.N < 10:
            self.N = 10
        self.H = int(self.N * 0.5)
        #self.H = int(1 * self.N * int(param['history_size_multiple'])) if 'history_size_multiple' in param else self.N
        self.learning_rate = learning_rate
        #float(param['learning_rate']) if 'learning_rate' in param else 0
        # self.learning_rate = 0.1
        self.initial_weight = initial_weight
        #float(param['initial_weight']) if 'initial_weight' in param else 0.5
        self.discount_rate = discount_rate
        #float(param['discount_rate']) if 'discount_rate' in param else 1
        self.Visualization = visualize
        #'visualize' in param and bool(param['visualize'])
        # self.discount_rate = 0.005**(1/self.N)
        np.random.seed(123)



        self.CacheRecency = CacheLinkedList(self.N)

        self.freq = {}
        self.PQ = []

        self.Hist1 = CacheLinkedList(self.H)
        self.Hist2 = CacheLinkedList(self.H)

        ## Accounting variables
        self.time = 0
        self.W = np.array([self.initial_weight,1-self.initial_weight], dtype=np.float32)

        self.X = []
        self.Y1 = []
        self.Y2 = []

        self.unique = {}
        self.unique_cnt = 0
        self.pollution_dat_x = []
        self.pollution_dat_y = []

        self.info = {
                'lru_misses':0,
                'lfu_misses':0,
                'lru_count':0,
                'lfu_count':0,
            }

    def get_N(self) :
        return self.N

    def __contains__(self, q):
        return q in self.CacheRecency

    def visualize(self, ax):
        lbl = []
        if self.Visualization:
            X = np.array(self.X)
            Y1 = np.array(self.Y1)
            Y2 = np.array(self.Y2)
#             ax = plt.subplot(2,1,1)
            ax.set_xlim(np.min(X), np.max(X))

#             l3, = plt.plot(self.pollution_dat_x,self.pollution_dat_y, 'g-', label='hoarding',linewidth=3)
#             l1, = plt.plot(X,Y1, 'y-', label='W_lru',linewidth=2)
#             l2, = plt.plot(X,Y2, 'b-', label='W_lfu',linewidth=1)

            ax.plot(X, Y1, 'y-', label='W_lru', linewidth=2)
            ax.plot(X, Y2, 'b-', label='W_lfu', linewidth=1)

            print("lru_misses = ", self.info['lru_misses'])
            print("lru_count   = ", self.info['lru_count'])
            print("lfu_misses = ", self.info['lfu_misses'])
            print("lfu_count  = ", self.info['lfu_count'])

#             lbl.append(l1)
#             lbl.append(l2)
#             lbl.append(l3)

        return lbl

    def getWeights(self):
        return np.array([self. X, self.Y1, self.Y2,self.pollution_dat_x,self.pollution_dat_y ]).T
#         return np.array([self.pollution_dat_x,self.pollution_dat_y ]).T

    def getStats(self):
        d={}
        d['weights'] = np.array([self. X, self.Y1, self.Y2]).T
        d['pollution'] = np.array([self.pollution_dat_x, self.pollution_dat_y ]).T
        return d

    ##############################################################
    ## There was a page hit to 'page'. Update the data structures
    ##############################################################
    def pageHitUpdate(self, page):
        assert page in self.CacheRecency and page in self.freq
        self.CacheRecency.moveBack(page)
        self.freq[page] += 1
        heapq.heappush(self.PQ, (self.freq[page],page))

    ##########################################
    ## Add a page to cache using policy 'poly'
    ##########################################
    def addToCache(self, page):
        self.CacheRecency.add(page)
        if page not in self.freq :
            self.freq[page] = 0
        self.freq[page] += 1
        heapq.heappush(self.PQ, (self.freq[page],page))

    def getHeapMin(self):
        while self.PQ[0][1] not in self.CacheRecency or self.freq[self.PQ[0][1]] != self.PQ[0][0] :
            heapq.heappop(self.PQ)
        return self.PQ[0][1]

    ######################
    ## Get LFU or LFU page
    ######################
    def selectEvictPage(self, policy):
        r = self.CacheRecency.getFront()
        f = self.getHeapMin()

        pageToEvit,policyUsed = None, None
        #if r == f :
            #pageToEvit,policyUsed = r,-1
        if policy == 0:
            pageToEvit,policyUsed = r,0
        elif policy == 1:
            pageToEvit,policyUsed = f,1

        return pageToEvit,policyUsed

    def evictPage(self, pg):
        assert pg in self.CacheRecency
        self.CacheRecency.delete(pg)


    def getQ(self):
        lamb = 0.05
        return (1-lamb)*self.W + lamb
    ############################################
    ## Choose a page based on the q distribution
    ############################################
    def chooseRandom(self):
        r = np.random.rand()
        if r < self.W[0] :
            return 0
        return 1

    def addToHistory(self, poly, cacheevict):
        histevict = None

        if self.Hist1.size() + self.Hist2.size() == self.H :
            p = 1.0 * self.Hist1.size() / (self.Hist1.size() + self.Hist2.size())
            if np.random.rand() < p:
                histevict = self.Hist1.getFront()
                self.Hist1.delete(histevict)
            else:
                histevict = self.Hist2.getFront()
                self.Hist2.delete(histevict)

        if (poly == 0) or (poly==-1 and np.random.rand() <0.5):
            self.Hist1.add(cacheevict)
            self.info['lru_count'] += 1
        else:
            self.Hist2.add(cacheevict)
            self.info['lfu_count'] += 1

        if histevict is not None :
            del self.freq[histevict]

    ########################################################################################################################################
    ####REQUEST#############################################################################################################################
    ########################################################################################################################################
    def request(self,page) :
        page_fault = False
        self.time = self.time + 1

        ###########################
        ## Clean up
        ## In case PQ get too large
        ##########################
        if len(self.PQ) > 2*self.N:
            newpq = []
            for pg in self.CacheRecency:
                newpq.append((self.freq[pg],pg))
            heapq.heapify(newpq)
            self.PQ = newpq
            del newpq

        #####################
        ## Visualization data
        #####################
        if self.Visualization:
            self.X.append(self.time)
            self.Y1.append(self.W[0])
            self.Y2.append(self.W[1])


        ##########################
        ## Process page request
        ##########################
        if page in self.CacheRecency:
            page_fault = False
            self.pageHitUpdate(page)
        else :
            #####################################################
            ## Learning step: If there is a page fault in history
            #####################################################
            pageevict = None

            reward = np.array([0,0], dtype=np.float32)
            if page in self.Hist1:
                pageevict = page
                self.Hist1.delete(page)
                reward[0] = -1
                self.info['lru_misses'] +=1

            elif page in self.Hist2:
                pageevict = page
                self.Hist2.delete(page)
                reward[1] = -1
                self.info['lfu_misses'] +=1

            #################
            ## Update Weights
            #################
            if pageevict is not None  :
                self.W = self.W * np.exp(self.learning_rate * reward)
                self.W = self.W / np.sum(self.W)

            ####################
            ## Remove from Cache
            ####################
            if self.CacheRecency.size() == self.N:

                ################
                ## Choose Policy
                ################
                act = self.chooseRandom()
                cacheevict,poly = self.selectEvictPage(act)

                ###################
                ## Remove from Cache and Add to history
                ###################
                self.evictPage(cacheevict)
                self.addToHistory(poly, cacheevict)

            self.addToCache(page)

            page_fault = True

        ## Count pollution


#         if page_fault:
#             self.unique_cnt += 1
#         self.unique[page] = self.unique_cnt
#
#         if self.time % self.N == 0:
#             pollution = 0
#             for pg in self.CacheRecency:
#                 if self.unique_cnt - self.unique[pg] >= 2*self.N:
#                     pollution += 1
#
#             self.pollution_dat_x.append(self.time)
#             self.pollution_dat_y.append(100* pollution / self.N)

        return page_fault

    def get_list_labels(self) :
        return ['L']

