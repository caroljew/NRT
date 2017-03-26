# -*- coding: utf-8 -*-
"""
Created on Fri Mar 24 17:33:15 2017

@author: weilun
"""

import json
import numpy as np
from keras.utils.np_utils import to_categorical
from keras.models import Sequential
from keras.layers import Dense, Input, Flatten, Dropout, Activation, Merge
from keras.layers import Convolution1D, MaxPooling1D, Embedding, Reshape
from keras.models import Model
from keras.layers.recurrent import LSTM
np.random.seed(2017)

with open('all_subtask_prosody.json', 'r') as dic:
    pro_subtask = json.load(dic)
    
with open('all_subject_sex.json', 'r') as dic:
    sub_sex = json.load(dic)
    
with open('all_subtask_label.json', 'r') as lab:
    all_subtask_label = json.load(lab)

subject=[]
intens=[]
pitch=[]
sex=[]
label=[]

for item,k in pro_subtask.items():
    
    if k!=None:
        
        if '_Cinderella' in item and item[:-11] in sub_sex:
            sex.append(sub_sex[item[:-11]])
            subject.append(item)
            pitch.append(k[0])
            intens.append(k[1])
            label.append(all_subtask_label[item])
        
        if '_Sandwich' in item and item[:-9] in sub_sex:
            sex.append(sub_sex[item[:-9]])
            subject.append(item)
            pitch.append(k[0])
            intens.append(k[1])
            label.append(all_subtask_label[item])
        
def norm(x):
    arr_x=np.asarray(x)
    intens_task = (arr_x-np.mean(arr_x))/np.std(arr_x)
    return intens_task
    
    
norm_intens=list(map(norm,intens))
norm_pitch=list(map(norm,pitch))



l=[]
for item in norm_intens:
    l.append(len(item))

hist=np.histogram(l,bins='auto')

l_norm_intens=[list(x) for x in norm_intens]
l_norm_pitch=[list(x) for x in norm_pitch]

#Pad zeros or truncate values to construct vectors of 3000-length

def trunc_pad_zero(l, max_length=3000):
    for x in l:
        while len(x)< max_length:
            x.append(0)
        while len(x)> max_length:
            x.pop(-1)
    return l

l_norm_intens=trunc_pad_zero(l_norm_intens)
l_norm_pitch=trunc_pad_zero(l_norm_pitch)

data1=np.asarray(l_norm_intens)  # intensity
data2=np.asarray(l_norm_pitch) # pitch
labels=to_categorical(np.asarray(label))


print('Shape of data tensor:', data1.shape)  # intensity
print('Shape of data tensor:', data2.shape)  # pitch
print('Shape of label tensor:', labels.shape) 

MAX_SEQUENCE_LENGTH = 3000

#Split data into training/validation

VALIDATION_SPLIT = 0.1

indices = np.arange(labels.shape[0])
np.random.shuffle(indices)
data1 = data1[indices]
data2 = data2[indices]
labels = labels[indices]
nb_validation_samples = int(VALIDATION_SPLIT * labels.shape[0])

x1_train = np.reshape(data1[:-nb_validation_samples],(data1[:-nb_validation_samples].shape[0],data1[:-nb_validation_samples].shape[1],1))
x2_train = np.reshape(data2[:-nb_validation_samples],(data2[:-nb_validation_samples].shape[0],data2[:-nb_validation_samples].shape[1],1))
y_train = labels[:-nb_validation_samples]



x1_val = np.reshape(data1[-nb_validation_samples:],(data1[-nb_validation_samples:].shape[0],data1[-nb_validation_samples:].shape[1],1))
x2_val = np.reshape(data2[-nb_validation_samples:],(data2[-nb_validation_samples:].shape[0],data2[-nb_validation_samples:].shape[1],1))
y_val = labels[-nb_validation_samples:]



num_hidden_units_conv=1024
nb_hidden_units=1024
nb_filter=128
filter_length=60

branch1=Sequential([
	Convolution1D(nb_filter=nb_filter,
	filter_length=filter_length, 
	border_mode='valid',
	activation='relu', 
	input_shape=(MAX_SEQUENCE_LENGTH,1), name='CONV1'),
	Flatten()

])

branch2=Sequential([
	Convolution1D(nb_filter=nb_filter,
	filter_length=filter_length, 
	border_mode='valid',
	activation='relu', 
	input_shape=(MAX_SEQUENCE_LENGTH,1), name='CONV2'),
	Flatten()

])



model=Sequential([
    Merge([branch1,branch2],mode='mul'),
    Dense(nb_hidden_units, init='uniform', activation='tanh'),
    Dense(nb_hidden_units, init='uniform', activation='tanh'),
    Dropout(0.5),
    Dense(2, init='uniform', activation='softmax'),

])




model.compile(loss='categorical_crossentropy',
              optimizer='rmsprop',
              metrics=['accuracy'])



model.fit([x1_train,x2_train],y_train, validation_data=([x1_val,x2_val],y_val),nb_epoch=25, batch_size=32) 
