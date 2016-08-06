import nltk.data
import string
import re
import logging  # use the same root logger
sent_detector = nltk.data.load('tokenizers/punkt/english.pickle')  # text2sent
printable = set(string.printable)  # filter non-ascii
  
''' Dump caption pairs in dumpPath '''
def dumpVTT(dumpPath, newCapPairs):
    Newcaps = 'WEBVTT\nKind: captions\nLanguage: en\n\n'
    for it in newCapPairs:
        Newcaps += it[0] + '\n'
        Newcaps += it[1] + '\n\n'
    with open(dumpPath, 'w') as f:
        f.write(Newcaps)

''' Merge two adjacent time stamps '''
def mergeTimestamp(ts1, ts2):
    return ts1.split('-->')[0] + '-->' + ts2.split('-->')[1]
# mergeTimestamp('00:00:48.000 --> 00:00:52.700', '00:00:53.000 --> 00:00:57.990')

''' Convert time stamp to seconds '''
def time2Second(ts):
    return int(ts[0:2]) * 3600 + int(ts[3:5]) * 60 + int(ts[6:8]) + float(ts[8:])

''' Convert seconds to time stamp '''
def second2Time(s):
    m, s = divmod(s, 60)
    ms = str(s).split('.')[1].ljust(3, '0')
    if len(ms) > 3:
        ms = ms[0:3]
    s = int(str(s).split('.')[0])
    h, m = divmod(m, 60)
    return '%02d:%02d:%02d.%3s' % (h, m, s, ms) 

''' Count time lapse in a caption '''
def timeLapse(ts):
    ts = ts.split(' --> ')
    return time2Second(ts[1]) - time2Second(ts[0])

''' Convert seconds to caption '''
def timestampFormat(t1, t2):
    return second2Time(t1) + ' --> ' + second2Time(t2)
# timeLapse('00:00:00.000 --> 00:00:10.001')
# timestampFormat(0.0, 10.100001)
# second2Time(10.100001)

''' Split text on sentences '''
def split2sents(capPairs):
    logging.info('len before split: ' + str(len(capPairs)))
    newCapPairs = []
    for itt, cap in enumerate(capPairs):
        sentSplit = sent_detector.tokenize(cap[1])
        ''' if contains only 1 sentence '''
        if len(sentSplit) == 1:
            newCapPairs.append((
                    cap[0].strip(), cap[1].strip()))
            continue
        ''' if more than 1 sentence '''
        wordPeriod = timeLapse(cap[0]) / len(cap[1].split())  # time per word
        # print cap
        logging.info('word period: ' + str(wordPeriod))

        begTime = time2Second(cap[0].split(' --> ')[0])
        endTime = begTime
        for singleSent in sentSplit:
            lapse = len(singleSent.split()) * wordPeriod
            endTime += lapse
            # print str(begTime) + ' to ' + str(endTime)
            newCapPairs.append((
                    timestampFormat(begTime, endTime), singleSent.strip() ))
            begTime += lapse
    logging.info('len after split: ' + str(len(newCapPairs)) + '\n')
    return newCapPairs

''' Merge the later incomplete sentence to the previous one '''
def merge2sents(capPairs):
    logging.info('len before merge: ' + str(len(capPairs)))
    for itt, cap in reversed(list(enumerate(capPairs))):  
        cap = capPairs[itt]  # original 'cap' would change
        sentSplit = sent_detector.tokenize(cap[1])
        if itt == 0:
            break
        prevCap = capPairs[itt - 1]
 
        ''' determine using lower case or end punct
            also make sure with no long interval in between '''
        if time2Second(cap[0].split(' --> ')[0]) - \
           time2Second(prevCap[0].split(' --> ')[1]) < 1.1 and \
           (cap[1][0].islower() or prevCap[1].strip()[-1] not in ['.', '!', '?']):
            logging.info('detect: ' + sentSplit[0])

            ''' build new tuples '''
            if len(''.join(sentSplit[1:]).strip()) == 0:  # when empty after merge
                capPairs[itt - 1] = (mergeTimestamp(prevCap[0], cap[0]),
                                     prevCap[1] + ' ' + sentSplit[0])
                capPairs.remove(cap)
                logging.info('new1: ' + prevCap[1])
                logging.info('new2: removed')
            else:
                wordPeriod = timeLapse(cap[0]) / len(cap[1].split())  # time per word
                logging.info('word period: ' + str(wordPeriod))
                begTime = time2Second(prevCap[0].split(' --> ')[0])
                midTime = begTime + timeLapse(prevCap[0]) \
                                  + wordPeriod * len(sentSplit[0].split())
                endTime = time2Second(capPairs[itt][0].split(' --> ')[1])
                capPairs[itt - 1] = (timestampFormat(begTime, midTime), 
                                     prevCap[1] + ' ' + sentSplit[0])
                capPairs[itt] = (timestampFormat(midTime, endTime), 
                                 ''.join(sentSplit[1:]))
                logging.info('new1: ' + str(capPairs[itt - 1]))
                logging.info('new2: ' + str(capPairs[itt]))
    logging.info('len after merge: ' + str(len(capPairs)) + '\n')
    return capPairs

''' Use .vtt file to create list of caption pairs '''
def creatDict(caps):
    ''' generate a list of begining numbers '''
    begList = []  # stores the begining line of a clip
    for itt, line in enumerate(caps):
        if len(line) > 5 and line[2] == ':' and line[5] == ':':
            begList.append(itt)
    begList.append(itt + 1)
    
    ''' create dictory based on begin numbers '''
    capPairs = []
    for itt, num in enumerate(begList[:-1]):
        capText = ''
        p = num + 1  # next line of time stamp
        while p < begList[itt + 1]:  # before next time stamp
            capText += filter(lambda x: x in printable,  # filter non-ascii 
                              replaceSpecialCode(caps[p].replace('\n', ' ')) )
            p += 1
        capText = capText.strip()
        if len(capText) > 0:  # make sure not empty
            capPairs.append((caps[num], capText))
    return capPairs

''' Replace special unicodes '''
def replaceSpecialCode(cap):
    cap = cap.decode('utf-8')  # convert to code format for matching
    cap = cap.replace(u"\u2018", "'")
    cap = cap.replace(u"\u2019", "'")
    cap = cap.encode('utf-8')  # convert back to symbol [ for translate()]
    return cap

''' Filter out short videos '''
def filterByTime(capPairs, sec):
    logging.info('len before time filter: ' + str(len(capPairs)))
    for it, pair in reversed(list(enumerate(capPairs))):
        if timeLapse(pair[0]) < sec:
            capPairs.remove(pair)
    logging.info('len after time filter: ' + str(len(capPairs)) + '\n')
    return capPairs

''' Clean videos with no letters '''
def filterByLength(capPairs):
    logging.info('len before length filter: ' + str(len(capPairs)))
    for it, capPair in reversed(list(enumerate(capPairs))):
        ''' remove punctuation and space '''
        if len(capPair[1].translate(None, string.punctuation).strip()) == 0:
            capPairs.remove(capPair)
    logging.info('len after length filter: ' + str(len(capPairs)) + '\n')
    return capPairs   

''' Add sec s margin before and after each clip '''
def addMargin(capPairs, sec):
    logging.info('adding ' + str(sec) + 's margin')
    for it, pair in enumerate(capPairs):
        begSecond = time2Second(pair[0].split(' --> ')[0]) - sec
        endSecond = time2Second(pair[0].split(' --> ')[1]) + sec
        if (begSecond < 0) or (it == len(capPairs) - 1):  # avoid crossing bound
            continue
        capPairs[it] = (second2Time(begSecond) + ' --> ' + \
                        second2Time(endSecond), pair[1])
    return capPairs
# addMargin([('00:00:00.111 --> 00:00:02.222', 'aaa'), \
#            ('00:00:03.111 --> 00:00:05.222', 'bbb')])

''' Shift all begining timestamps in a video '''
def shiftBeg(capPairs, sec):
    logging.info('shifting begining timestamp ' + str(sec) + 's')
    for it, pair in enumerate(capPairs):
        begSecond = time2Second(pair[0].split(' --> ')[0]) + sec
        endSecond = time2Second(pair[0].split(' --> ')[1])
        if begSecond < 0:  # avoid crossing previous bound
            continue
        capPairs[it] = (second2Time(begSecond) + ' --> ' + \
                        second2Time(endSecond), pair[1])
    return capPairs

''' Shift all ending timestamps in a video '''
def shiftEnd(capPairs, sec):
    logging.info('shifting ending timestamp ' + str(sec) + 's')
    for it, pair in enumerate(capPairs):
        begSecond = time2Second(pair[0].split(' --> ')[0])
        endSecond = time2Second(pair[0].split(' --> ')[1]) + sec 
        if (it == len(capPairs) - 1):  # avoid crossing ending bound
            continue
        capPairs[it] = (second2Time(begSecond) + ' --> ' + \
                        second2Time(endSecond), pair[1])
    return capPairs

''' Remove name before colons in captions '''
def rmNameBefColon(capPairs):
    logging.info('remove speaker names...')
    for itt, capPair in enumerate(capPairs):
        ''' get the caption '''
        sent = capPair[1]
        if re.search(':', sent) is None:
            continue
            
        ''' remove the words before ':' '''
        pos = re.search(':', sent).start()
        if len(sent[:pos].split()) < 4:  # if less than 4 words before ':'
            capPairs[itt] = (capPair[0], sent[pos+1:])
            logging.info('<' + str(itt + 1) + '>\t' + sent + ' => ' + \
                                                     str(capPairs[itt][1]))
    return capPairs

''' Remove regular expression pattern in sent '''
def rmRegexPattern(sent, regexPatt):
    ''' get a list of patterns found '''
    matchedList = list(re.finditer(regexPatt, sent)) 

    ''' Remove if pattern exist '''
    if len(matchedList) == 0:  # len(list(iter)) will consume the iterator
        return sent
    for matchedIt in matchedList:
        sent = sent.replace(matchedIt.group(0), '')
    return sent

''' Remove special patterns in captions by regular expressions '''
def rmPattern(capPairs):
    logging.info('remove special patterns...')
    for itt, capPair in enumerate(capPairs):
        ''' get the caption '''
        sent = capPair[1]
        
        ''' remove pattern in caption '''
        sent = rmRegexPattern(sent, r"\((.*)\)")  # match all char >=0 times
        sent = rmRegexPattern(sent, r"\<(.*)\>")
        sent = rmRegexPattern(sent, r"\[(.*)\]")
        sent = rmRegexPattern(sent, r"(\!{2,})")  # ! repeats at least 2 times
        
        ''' Create a new caption '''
        if sent == capPair[1]:
            continue
        capPairs[itt] = (capPair[0], sent)
        logging.info('<' + str(itt + 1) + '>\t' + capPair[1] + ' => ' + \
                                                 str(capPairs[itt][1]))
    return capPairs
