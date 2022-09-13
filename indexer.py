from posixpath import split
from turtle import title
from nltk.corpus import stopwords
from nltk.stem.porter import *
from collections import defaultdict
import sys, xml.sax, re, nltk, string, Stemmer, time, heapq, os

startTime = time.time()

'''
0 - page index
1 - t - title
2 - i - infobox
3 - b - body
4 - c - category
5 - l - links
6 - r - references

try to create a dictionary to these if used more than once
'''


# path_to_wiki_dump = 'tiny.xml'

path_to_wiki_dump = " ".join(sys.argv[1:])

path_to_inverted_index = 'index.txt'

print(path_to_wiki_dump)


nltk.download('stopwords')
stop_words = set(stopwords.words("english"))
urlStopWords = set(['ac', 'archives', 'com', 'edu', 'ftp', 'gov', 'htm', 'html', 'http', 'https', 'in', 'jgeg', 'jpg', 'net', 'net', 'org', 'pdf', 'png', 'redirect', 'txt', 'uk', 'ww3', 'www'])
stemmer = Stemmer.Stemmer('english')

title_file = open('titles.txt','w')
titleIndex = open('titleIndex.txt','w+')
secondaryIndex = open('secondaryIndex.txt','w+')
invertedindex_stat_file = open('invertedindex_stat.txt','a')

'''
global index 
contains words and their posting list
list of elements which contain docid, and compressed representation of
t,i,b,c,l,r count of words
'''

NUMBER_OF_DOCS_PER_SAVE = 5000
NUMBER_OF_WORDS_PER_SAVE = 20000
SIZE_THEROSHOLD_ON_GLOBAL_INDEX_FILE = 10**7

class MyHandler(xml.sax.handler.ContentHandler):
    def __init__(self):
        self.page = 1
        self.tokens = 0
        '''
            contains words to page index,t,i,b,c,l,r count in that page
            this is later merged with global index
        '''
        self.title = ''
        self.text = ''
        self.current = ''
        self.pageIndex = defaultdict(lambda:[0,0,0,0,0,0,0])
        self.pageIndexCounter = 1
        self.globalIndex = defaultdict(lambda:[])
        self.globalIndexCounter = 1
        self.titleOffset = 0     
    
    def split_data(self,data, urlFlag=False):
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


    def write_index_to_file(self):
        index_file = open(f"pageIndex/{self.pageIndexCounter}.txt",'w+')
        for i in sorted(self.globalIndex.keys()):
            s=i+f";{len(self.globalIndex[i])};"
            for j in self.globalIndex[i]:
                s+=f"{j[0]}:"
                if j[1]!=0:
                    s+=f"t{j[1]}"
                if j[2]!=0:
                    s+=f"i{j[2]}"
                if j[3]!=0:
                    s+=f"b{j[3]}"
                if j[4]!=0:
                    s+=f"c{j[4]}"
                if j[5]!=0:
                    s+=f"l{j[5]}"
                if j[6]!=0:
                    s+=f"r{j[6]}"
                s+=";"
            index_file.write(s+"\n")

        index_file.close()
        self.pageIndexCounter += 1
        self.globalIndex.clear()
    
    # title is handled in the characters function of this class itself

    def get_info(self,data):
        data = data.split("\n")
        n = len(data)

        infoFlag = False
        infoData = []
        bodyData = []

        for i in range(n):
            if infoFlag:
                if data[i].strip() != "}}":
                    infoData.append(data[i])
                else:
                    bodyData = bodyData + data[i+1:]
                    break
            else:
                info = re.search(r'\{\{[i,I]nfobox',data[i])
                if not info:
                    bodyData.append(data[i])
                else:
                    infoFlag = True
                    infoData.append(re.sub(r'\{\{[i,I]nfobox',' ',data[i]))
                if i>20:
                    break
        if not infoFlag:
            bodyData = bodyData + data[i+1:]
        infoData = " ".join(infoData)
        infoData = self.split_data(infoData)
        return ("\n".join(bodyData)), infoData
    
    # body is handled in the characters function of this class itself
    
    def get_links(self,data):
        data = data.split("\n")
        links = []
        linkRegex = re.compile('https?:\/\/\S+')
        for line in data:
            urls = linkRegex.findall(line)
            links = links + urls
        return self.split_data(' '.join(links),urlFlag=True)

    def get_category(self,data):
        cat = re.findall(r'\[\[[c,C]ategory:(.*?)\]\]',data)
        res = self.split_data(' '.join(cat))
        return res
    
    def get_references(self,data):
        data = data.split("\n")
        refs = []
        for line in data:
            if line and line[0] == '*':
                refs.append(line)
        data = self.split_data(' '.join(refs),urlFlag=True)
        return data


    def startElement(self,name,attrs):
        self.current = name
    
    def characters(self,content):
        if self.current == 'title':
            self.title += " "+content

        elif self.current == 'text':
            self.text += " "+content
        
    def endElement(self,name):
        if name == 'title':
            title_file.write(self.title+"\n")

            titleIndex.write(f"{self.titleOffset}\n")
            currentOffset = title_file.tell()
            self.titleOffset = currentOffset+1

            tokens = self.split_data(self.title)
            for i in tokens:
                self.pageIndex[i][0]=self.page
                self.pageIndex[i][1]+=1
        
        elif name == 'text':
            data, info = self.get_info(self.text)

            for i in info:
                self.pageIndex[i][0]=self.page
                self.pageIndex[i][2]+=1

            links = self.get_links(data)
            for i in links:
                self.pageIndex[i][0]=self.page
                self.pageIndex[i][5]+=1

            data = re.split(r'== ?[r,R]eferences ?==',data)

            body = self.split_data(data[0])
            for i in body:
                self.pageIndex[i][0]=self.page
                self.pageIndex[i][3]+=1

            if len(data) >= 2:
                categories = self.get_category(data[1])
                for i in categories:
                    self.pageIndex[i][0]=self.page
                    self.pageIndex[i][4]+=1

                references = self.get_references(data[1])
                for i in references:
                    self.pageIndex[i][0]=self.page
                    self.pageIndex[i][6]+=1

            
            for i in self.pageIndex:
                self.globalIndex[i].append(self.pageIndex[i])
            
            if self.page % NUMBER_OF_DOCS_PER_SAVE == 0:
                print(self.page)
                self.write_index_to_file()
            
            self.page += 1
            
            self.pageIndex.clear()
            self.title = ''
            self.text = ''
            self.current = ''

    def merge_index(self):
        heap = []

        globalIndex = defaultdict(lambda:[0,''])

        tempCount = 0

        def writeGlobalIndexToFile():
            mergedIndex = open(f'globalIndex/{self.globalIndexCounter}.txt','w+')
            sortedKeys = sorted(list(globalIndex.keys()))
            secondaryIndex.write(f"{sortedKeys[0]}\n")
            for j in sortedKeys:
                self.tokens += 1
                mergedIndex.write(f"{j};{globalIndex[j][0]};{globalIndex[j][1]}\n")
            mergedIndex.close()
            globalIndex.clear()
            self.globalIndexCounter+=1
        
        for i in range(1,4459):
            file =  open(f'./pageIndex/{i}.txt','r')
            t  = file.readline().strip()
            ind = t.find(';')
            character = t[:ind]
            postingList = t[ind+1:]
            heap.append([character,i,postingList,file])

        heapq.heapify(heap)

        while len(heap) != 0:
            [character,i,postingList,filePtr] = heapq.heappop(heap)
            ind = postingList.find(';')
            count = int(postingList[:ind])
            originalList = postingList[ind+1:]

            prevLen = len(globalIndex)

            globalIndex[character][0]+=count
            globalIndex[character][1]+=originalList

            tempCount += len(originalList)

            if len(globalIndex) != prevLen and tempCount >= SIZE_THEROSHOLD_ON_GLOBAL_INDEX_FILE:
                print(self.globalIndexCounter)
                prevVal = globalIndex[character]
                globalIndex.pop(character)
                writeGlobalIndexToFile()

                tempCount = len(originalList)

                globalIndex[character] = prevVal
            
            # if len(globalIndex) == NUMBER_OF_WORDS_PER_SAVE+1:
            #     prevVal = globalIndex[character]
            #     globalIndex.pop(character)
            #     writeGlobalIndexToFile()
            #     globalIndex[character] = prevVal
            

            t = filePtr.readline()
            if t != '':
                t = t.strip()
                ind = t.find(';')
                character = t[:ind]
                postingList = t[ind+1:]
                heapq.heappush(heap,[character,i,postingList,filePtr])
            # else:
            #     os.remove(filePtr.name)


        if len(globalIndex) != 0:
            writeGlobalIndexToFile()

        secondaryIndex.close()


if __name__ == "__main__" :
    handler = MyHandler()
    # parser = xml.sax.make_parser()
    # parser.setContentHandler(handler)
    
    # dump_file = open(path_to_wiki_dump)
    # parser.parse(dump_file)
    
    # if (handler.page-1)%NUMBER_OF_DOCS_PER_SAVE != 0:
    #     print(handler.page)
    #     handler.write_index_to_file()

    handler.merge_index()

    # invertedindex_stat_file.write(str(handler.page-1)+'\n')
    invertedindex_stat_file.write(str(handler.tokens))
    invertedindex_stat_file.close()

    # dump_file.close()
    # title_file.close()
    # titleIndex.close()

    print(f"time for execution: {time.time()-startTime}")

# 23172 seconds - for dividing the files to 5000 documents index
# 1.5hrs - for merging the above individual indexes
# python3 indexer.py /Users/saivarunreddybhavanam/Library/CloudStorage/OneDrive-InternationalInstituteofInformationTechnology/3rd sem related/IRE/PROJECTS/MINI PROJECT/PHASE-1/enwiki-20220720-pages-articles-multistream15.xml