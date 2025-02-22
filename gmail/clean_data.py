import numpy as np
import re

classes = ["walking", "sitting", "table", "stairs", "car"]

# returns -1 if the message is invalid, 0 if it's a valid unlabed sample, otherwise the index + 1 of the class
def classify(message):
    subject, body = message
    if len(body) < 10000 or "9999999999" in body:
        return -1
    
    for i, klass in enumerate(classes):
        if klass in subject.lower():
            return i + 1

    return 0
        
def get_data(line):
    m = re.match("x: (.*), y: (.*), z: (.*), alpha: (.*), beta: (.*), gamma: (.*)", line)
    strings = [m.group(1), m.group(2), m.group(3), m.group(4), m.group(5), m.group(6)]
    for string in strings:
        if string == "None":
            return []
        
    return map(float, strings)

data = np.load('data.npy')

clean_data, labels = [], []
for message in data:
    klass = classify(message)
    if klass != -1:
        body = message[1]
        clean_entry = []
        for line in body.splitlines():
            clean_line = get_data(line)
            if clean_line:
                clean_entry.append(clean_line)
            
        if len(clean_entry) >= 260:
            clean_data.append(clean_entry[:260])
            labels.append(klass)

np.save('clean_data.npy', clean_data)
np.save('labels.npy', labels)
