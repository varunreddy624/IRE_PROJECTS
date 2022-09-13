ind = open('titleIndex.txt','w+')
f = open('titles.txt','r')

while True:
    currInd = f.tell()
    t = f.readline()
    if t=='':
        break
    else:
        ind.write(f"{currInd}\n")