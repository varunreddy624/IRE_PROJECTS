import re

s1 = '{{infobox varun}}'
s2 = '{{Infobox reddy}}'

info1 = re.search(r'\{\{[i,I]nfobox(.*?)\}\}',s1)
if info1:
    print(info1.groups(1))
else:
    print("no match in s1")

info2 = re.search(r'\{\{[i,I]nfobox(.*?)\}\}',s2)
if info2:
    print(info2.groups(1))
else:
    print("no match in s2")