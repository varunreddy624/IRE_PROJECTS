from posixpath import split
import sys, xml.sax, re, nltk, string, Stemmer
from turtle import title
from nltk.corpus import stopwords
from nltk.stem.porter import *
from collections import defaultdict
import time


startTime = time.time()

'''
0 - t - title
1 - i - infobox
2 - b - body
3 - c - category
4 - l - links
5 - r - references

try to create a dictionaty to these is used more than once
'''


path_to_wiki_dump = 'tiny.xml'
path_to_inverted_index = 'index.txt'

print(path_to_wiki_dump)


nltk.download('stopwords')
stop_words = set(stopwords.words("english"))
urlStopWords = ['ac', 'archives', 'com', 'edu', 'ftp', 'gov', 'htm', 'html', 'http', 'https', 'in', 'jgeg', 'jpg', 'net', 'net', 'org', 'pdf', 'png', 'redirect', 'txt', 'uk', 'ww3', 'www']
stemmer = Stemmer.Stemmer('english')

title_file = open('titles.txt','w')
index_file = open(path_to_inverted_index,'w')

globalIndex = defaultdict(lambda:[])

class MyHandler(xml.sax.handler.ContentHandler):
    def __init__(self):
        self.infoBoxFlag = False
        self.textCurrent = 'b'

        self.page = 1
        self.pageIndex = defaultdict(lambda:[0,0,0,0,0,0,0])
        
    
    def split_data(self,data):
        data = data.encode('ascii','ignore').decode() 
        data = re.sub("https*\S+", " ", data) 
        data = re.sub("\'\w+", '', data) 
        data = re.sub('[%s]' % re.escape(string.punctuation), ' ', data)
        data = re.sub(r'&nbsp;|&lt;|&gt;|&amp;|&quot;|&apos;', r' ', data) 
        data = [word.lower() for word in data.split(' ') if word not in stop_words ]
        data = ' '.join(stemmer.stemWords(data))
        return data.split()
    
    def split_urls(self,urls):
        data = urls.encode('ascii','ignore').decode()
        data = re.sub("\'\w+", '', data)
        data = re.sub('[%s]' % re.escape(string.punctuation), ' ', data)
        data = re.sub(r'&nbsp;|&lt;|&gt;|&amp;|&quot;|&apos;', r' ', data)
        data = [word.lower() for word in data.split(' ') if word not in stop_words]
        data = ' '.join(stemmer.stemWords(data))
        return data.split()


    def write_index_to_file(self):
        for i in sorted(globalIndex.keys()):
            s=i+f";{len(globalIndex[i])};"
            for j in globalIndex[i]:
                if j[0]!=0:
                    s+=f"t{j[0]}"
                if j[1]!=0:
                    s+=f"i{j[1]}"
                if j[2]!=0:
                    s+=f"b{j[2]}"
                if j[3]!=0:
                    s+=f"c{j[3]}"
                if j[4]!=0:
                    s+=f"r{j[4]}"
                if j[5]!=0:
                    s+=f"l{j[5]}"
                s+=";"
            index_file.write(s+"\n")
    
    def get_info(self,data):
        info = re.search(r'\{\{Infobox(.*?)\}\}',data,re.DOTALL)
        if info:
            print('success')
            data = self.split_data(info.groups(1))
        return data
    
    def get_links(self,data):
        urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', data)
        res = []
        if len(urls) > 0:
            res = self.split_urls(' '.join(urls))
        return res

    def get_category(self,data):
        cat = re.findall(r'\[\[Category:(.*?)\]\]',data)
        res = self.split_data(' '.join(cat))
        return res
    
    def get_references(self,data):
        refs = re.findall(r'\{\{refbegin\}\}(.*?)\{\{refend\}\}',data)
        data = self.tokenize_data(' '.join(refs))
        return data


    def startElement(self,name,attrs):
        self.current = name
    
    def characters(self,content):
        if self.current == 'title':
            title_file.write(content+"\n")
            tokens = self.split_data(content)
            for i in tokens:
                self.pageIndex[i][0]=self.page
                self.pageIndex[i][1]+=1

        elif self.current == 'text':
            # info_tokens = self.get_info(content)
            # for i in info_tokens:
            #     self.pageIndex[i][0]=self.page
            #     self.pageIndex[i][2]+=1

            cat = self.get_category(content)
            for i in cat:
                self.pageIndex[i][0]=self.page
                self.pageIndex[i][3]+=1

            links = self.get_links(content)
            for i in links:
                self.pageIndex[i][0]=self.page
                self.pageIndex[i][5]+=1
            
            # refs = self.get_references(content)
            # for i in refs:
            #     self.pageIndex[i][0]=self.page
            #     self.pageIndex[i][6]+=1
        
    def endElement(self,name):
        if name == 'page':
            self.page += 1
            for i in self.pageIndex:
                globalIndex[i].append(self.pageIndex[i])
            self.pageIndex = defaultdict(lambda:[0,0,0,0,0,0,0])

        self.current = ''

if __name__ == "__main__" :
    handler = MyHandler()
    parser = xml.sax.make_parser()
    parser.setContentHandler(handler)
    parser.parse(open(path_to_wiki_dump))
    handler.write_index_to_file()

    print(f"time for execution: {time.time()-startTime}")



# python3 indexer.py /Users/saivarunreddybhavanam/Library/CloudStorage/OneDrive-InternationalInstituteofInformationTechnology/3rd sem related/IRE/PROJECTS/MINI PROJECT/PHASE-1/enwiki-20220720-pages-articles-multistream15.xml