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
class LeCaR_unnorm(page_replacement_algorithm):

    def __init__(self, N, visualization = True):
        self.N = N
        self.CacheRecency = CacheLinkedList(N)

        self.freq = {}
        self.PQ = []
        
        self.Hist1 = CacheLinkedList(N)        
        self.Hist2 = CacheLinkedList(N)        
        
        ## Config variables
        self.epsilon = 0.90
        self.error_discount_rate = (0.005)**(1.0/N)
        
        ## 
        self.policy = 0
        self.evictionTime = {}
        self.policyUsed = {}
        self.weightsUsed = {}
        
        ## Accounting variables
        self.time = 0
        self.W = np.array([.5,.5], dtype=np.float32)
        
        self.Visualization = visualization
        self.X = np.array([],dtype=np.int32)
        self.Y1 = np.array([])
        self.Y2 = np.array([])
        
        ###
        self.q = Queue.Queue()
        self.sum = 0
        self.NewPages = []
        
        
        self.TR = {}
        
    def get_N(self) :
        return self.N
    
    def visualize(self, plt):
        lbl = []
        if self.Visualization:
            ax = plt.subplot(2,1,1)
            ax.set_xlim(np.min(self.X), np.max(self.X))
            l1, = plt.plot(self.X,self.Y1, 'y-', label='W_lru')
            l2, = plt.plot(self.X,self.Y2, 'b-', label='W_lfu')
            lbl.append(l1)
            lbl.append(l2)
#         totaltime = 0
#         total2  = 0
#         for tc in self.TR:
#             if tc is not 'total':
#                 totaltime += self.TR[tc]
#              
#         for tc in self.TR:
#             if tc is not 'total':
#                 print '%s = %% %f' % (tc, 100*self.TR[tc] / totaltime)
#                 total2 += self.TR[tc]
#                  
#         print '%s = %f' % ('total2', total2)
#         print '%s = %f' % ('total', self.TR['total'])
#         
        return lbl
    
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
#         if len(self.PQ) < self.N :
#             print self.PQ
#         assert len(self.PQ) >= self.N, 'PQ should be full %d' % len(self.PQ)
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
        if r == f :
            pageToEvit,policyUsed = r,-1
        elif policy == 0:
            pageToEvit,policyUsed = r,0
        elif policy == 1:
            pageToEvit,policyUsed = f,1
            
#         assert pageToEvit in self.CacheRecency
        
        return pageToEvit,policyUsed
    
    def evictPage(self, pg):
        assert pg in self.CacheRecency
        self.CacheRecency.delete(pg)
        
    
    ############################################
    ## Choose a page based on the q distribution
    ############################################
    def chooseRandom(self):
        r = np.random.rand()
        
        p1 = self.W[0] / np.sum(self.W)
        
        if r < p1:
            return 0
        return 1
    
    def addToHistory(self, poly, cacheevict):
        histevict = None
        if (poly == 0) or (poly==-1 and np.random.rand() <0.5):
            if self.Hist1.size() == self.N :
                histevict = self.Hist1.getFront()
                assert histevict in self.Hist1
                self.Hist1.delete(histevict)
            self.Hist1.add(cacheevict)
        else:
            if self.Hist2.size() == self.N :
                histevict = self.Hist2.getFront()
                assert histevict in self.Hist2
                self.Hist2.delete(histevict)
            self.Hist2.add(cacheevict)
            
        if histevict is not None :
            del self.evictionTime[histevict]
            del self.policyUsed[histevict]
            del self.freq[histevict]
    
    def setTime(self, key, t):
        if key not in self.TR:
            self.TR[key] = 0
        self.TR[key] += t 
            
    ########################################################################################################################################
    ####REQUEST#############################################################################################################################
    ########################################################################################################################################
    def request(self,page) :
        starttime = time.time()
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
#         if self.Visualization:
#             self.X  = np.append(self.X, self.time)
#             self.Y1 = np.append(self.Y1, self.W[0] / np.sum(self.W))
#             self.Y2 = np.append(self.Y2, self.W[1] / np.sum(self.W))
        
        ##########################
        ## Process page request 
        ##########################
        if page in self.CacheRecency:
            st = time.time()
            page_fault = False
            self.pageHitUpdate(page)
            self.setTime('pageHitUpdate',time.time()-st)
        else :
            
            #####################################################
            ## Learning step: If there is a page fault in history
            #####################################################
            pageevict = None
            st = time.time()

            reward = np.array([0,0], dtype=np.float32)
            if page in self.Hist1:
                pageevict = page
                self.Hist1.delete(page)
                reward[1] = self.error_discount_rate ** (self.time - self.evictionTime[pageevict])
                reward_hat = reward 
            elif page in self.Hist2:
                pageevict = page
                self.Hist2.delete(page)
                reward[0] = self.error_discount_rate ** (self.time - self.evictionTime[pageevict])
                reward_hat = reward 
            
            #################
            ## Update Weights
            #################
            if pageevict is not None and self.policyUsed[pageevict] != -1 :
                self.W = self.W * np.exp(self.epsilon * reward_hat / 2)
#                 self.W = self.W / np.sum(self.W)
                
                if np.sum(self.W) > 1e9 :
                    self.W = self.W / 2.0
                
            self.setTime('Hit in history and update weights',time.time()-st)
            ####################
            ## Remove from Cache
            ####################
            if self.CacheRecency.size() == self.N:
                
                ################
                ## Choose Policy
                ################
                st = time.time()
                act = self.chooseRandom()
                self.setTime('chooseRandom',time.time()-st)
                
                st = time.time()
                cacheevict,poly = self.selectEvictPage(act)
                self.policyUsed[cacheevict] = poly
                self.evictionTime[cacheevict] = self.time
                self.setTime('selectEvictPage',time.time()-st)
                
                ###################
                ## Remove from Cache and Add to history
                ###################
                st = time.time()
                self.evictPage(cacheevict)
                self.addToHistory(poly, cacheevict)
                self.setTime('selectEvictPage',time.time()-st)
                
            st = time.time()
            self.addToCache(page)
            self.setTime('addToCache',time.time()-st)
            
            page_fault = True
        
#         st = time.time()
#         self.q.put(notInHistory)
#         self.sum += notInHistory
#         if self.q.qsize() > self.N:
#             self.sum -= self.q.get()
#         self.NewPages.append(1.0*self.sum / (self.N))
#         self.setTime('New pages',time.time()-st)
        
        self.setTime('total', time.time() - starttime)
        
        return page_fault

    def get_list_labels(self) :
        return ['L']

