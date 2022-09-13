from email.policy import default
import re, nltk, string, Stemmer, math
from nltk.corpus import stopwords
from bisect import bisect_right
from collections import defaultdict
import heapq

secondaryIndex = open('secondaryIndex.txt','r')
secondaryIndexList = [i.strip() for i in secondaryIndex.readlines()]

titleIndex = open('titleIndex.txt')
titleIndexList = [int(i.strip()) for i in titleIndex.readlines()]

stat = open('invertedindex_stat.txt','r')
titles = open('titles.txt','r')
queries = open('queries.txt','r')
queryOutput = open('queries_output.txt','w+')

N = int(stat.readline().strip())

nltk.download('stopwords')
stop_words = set(stopwords.words("english"))
urlStopWords = set(['ac', 'archives', 'com', 'edu', 'ftp', 'gov', 'htm', 'html', 'http', 'https', 'in', 'jgeg', 'jpg', 'net', 'net', 'org', 'pdf', 'png', 'redirect', 'txt', 'uk', 'ww3', 'www'])
stemmer = Stemmer.Stemmer('english')

def rankDocs(docDict):
    heap = []

    for i in docDict:
        if len(heap)<10:
            heapq.heappush(heap,[docDict[i],i])
        else:
            if docDict[i] >= heap[0][0]:
                heapq.heappop(heap)
                heapq.heappush(heap,[docDict[i],i])
    
    heap.sort(reverse=True)

    for i in heap:
        titleOffset = titleIndexList[int(i[1])-1]
        titles.seek(titleOffset)
        title = titles.readline().strip()
        queryOutput.write(f"{i[1]}, {title}\n")



def split_data(data, urlFlag=False):
    data = data.encode('ascii','ignore').decode() 
    if not urlFlag:
        data = re.sub("http*\S+", " ", data)
    data = re.sub("\'", '', data)
    data = re.sub('[%s]' % re.escape(string.punctuation), ' ', data)
    data = re.sub(r'&nbsp;|&lt;|&gt;|&amp;|&quot;|&apos;', r' ', data)
    if not urlFlag:
        data = [word for word in data.split(' ') if word not in stop_words ]
    else:
        data = [word for word in data.split(' ') if word not in urlStopWords ]
    data = [word.lower() for word in data if (word.isalpha() and len(word) > 1 )  or (word.isnumeric() and len(word) <= 8) ]
    return stemmer.stemWords(data)


def returnPostingListForWord(word):
    globalIndexFileNumber = bisect_right(secondaryIndexList,word)
    globalIndexFile = open(f'globalIndex/{globalIndexFileNumber}.txt','r')
    for line in globalIndexFile.readlines():
        ind = line.find(';')
        if line[:ind] == word:
            postingList = line[ind+1:]
            ind = postingList.find(';')
            count = int(postingList[:ind])
            originalList = postingList[ind+1:].strip().split(';')[:-1]
            expandedRepn = []
            for entry in originalList:
                [docid,freq] = entry.split(':')
                indices = [m.start(0) for m in re.finditer('[t|i|b|c|l|r]',freq)]
                typeFreq=[0]*6
                for i in range(len(indices)):
                    type=indices[i]
                    if freq[type]=='t':
                        ind = 0
                    elif freq[type]=='i':
                        ind = 1
                    elif freq[type]=='b':
                        ind = 2
                    elif freq[type]=='c':
                        ind = 3
                    elif freq[type]=='l':
                        ind = 4
                    else:
                        ind = 5
                    if i == len(indices)-1:
                        typeFreq[ind] = int(freq[type+1:])
                    else:
                        typeFreq[ind] = int(freq[type+1:indices[i+1]])
                expandedRepn.append([docid,typeFreq])
            return [count,expandedRepn]
    globalIndexFile.close()
    return []

def searchFieldQuery(searchDict):
    docDict = defaultdict(lambda:0)
    for i in range(6):
        if len(searchDict[i])!=0:
            postingListsForQueryTokens = [returnPostingListForWord(j) for j in searchDict[i]]
            for postingList in postingListsForQueryTokens:
                if len(postingList) != 0:
                    docFreq = postingList[0]
                    idf = math.log2(N/(docFreq+1))
                    for docInfo in postingList[1]:
                        docDict[docInfo[0]] += (docInfo[1][i]*idf)
    
    # naive sorting
    
    # rank = [[docDict[i],i] for i in docDict]
    # rank.sort(reverse=True)
    # docIds = [i[1] for i in rank[:min(10,len(rank))]]
    # for docId in docIds:
    #     titleOffset = titleIndexList[int(docId)-1]
    #     titles.seek(titleOffset)
    #     title = titles.readline().strip()
    #     queryOutput.write(f"{docId}, {title}\n")

    # naive sorting

    # heaps

    rankDocs(docDict)

    

'''
    This is considering all docs, optimize it 
    to include only top k results
'''

def searchPlainQuery(tokens):
    docDict = defaultdict(lambda:0)
    postingListsForQueryTokens = [returnPostingListForWord(i) for i in tokens]
    for postingList in postingListsForQueryTokens:
        if len(postingList) != 0:
            docFreq = postingList[0]
            idf = math.log2(N/(docFreq+1))
            for docInfo in postingList[1]:
                docDict[docInfo[0]] += (sum(docInfo[1])*idf)
    
    # naive sorting

    # rank = [[docDict[i],i] for i in docDict]
    # rank.sort(reverse=True)
    # docIds = [i[1] for i in rank[:min(10,len(rank))]]
    # for docId in docIds:
    #     titleOffset = titleIndexList[int(docId)-1]
    #     titles.seek(titleOffset)
    #     title = titles.readline().strip()
    #     queryOutput.write(f"{docId}, {title}\n")

    # naive sorting

    rankDocs(docDict)

def search(searchString):
    s = re.finditer('[t|i|b|c|l|r]:',searchString)
    indices = [[m.start(0), m.end(0)] for m in s]

    # if field query

    if len(indices) >= 1:
        searchDict = [[] for i in range(6)]
        for i in range(len(indices)):
            type=indices[i][0]
            if searchString[type]=='t':
                ind = 0
            elif searchString[type]=='i':
                ind = 1
            elif searchString[type]=='b':
                ind = 2
            elif searchString[type]=='c':
                ind = 3
            elif searchString[type]=='l':
                ind = 4
            else:
                ind = 5
            if i == len(indices)-1:
                fieldString = searchString[type+2:]
            else:
                fieldString = searchString[type+2:indices[i+1][0]]
            searchDict[ind]=split_data(fieldString)
        searchFieldQuery(searchDict)
    
    # else plain query

    else:
        searchPlainQuery(split_data(searchString))

for query in queries.readlines():
    search(query)
    queryOutput.write("\n")

queryOutput.close()

