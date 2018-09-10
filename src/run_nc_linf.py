import argparse
import sys
import os
from datetime import datetime

import keras
from keras.models import *
from keras.datasets import cifar10
from keras.datasets import mnist
from keras.applications.vgg16 import VGG16
from keras.preprocessing.image import load_img
from keras.layers import *
from keras import *
from utils import *
from nc_lp import *
from lp_encoding import *
from nc_setup import nc_setup

def run_nc_linf(test_object, outs):

  nc_results, layer_functions, cover_layers, activations, test_cases, adversarials=nc_setup(test_object, outs)

  base_constraints=create_base_constraints(test_object.dnn)

  while True:
    index_nc_layer, nc_pos, nc_value=get_nc_next(cover_layers)
    #print (nc_layer.layer_index, nc_pos, nc_value/nc_layer.pfactor)
    nc_layer=cover_layers[index_nc_layer]
    print (np.array(nc_layer.activations).shape)
    shape=np.array(nc_layer.activations).shape
    pos=np.unravel_index(nc_pos, shape)
    im=test_cases[pos[0]]
    act_inst=eval(layer_functions, im)


    s=pos[0]*int(shape[1]*shape[2])
    if nc_layer.is_conv:
      s*=int(shape[3])*int(shape[4])
    print ('\n::', nc_pos, pos, nc_pos-s)
    print (nc_layer.layer, nc_layer.layer_index)
    print ('the max v', nc_value)

    mkey=nc_layer.layer_index
    if act_in_the_layer(nc_layer.layer) != 'relu':
      mkey+=1
    feasible, d, new_im=negate(test_object.dnn, act_inst, [im], nc_layer, nc_pos-s, base_constraints[mkey])

    cover_layers[index_nc_layer].disable_by_pos(pos)
    if feasible:
      print ('\nis feasible!!!\n')
      test_cases.append(new_im)
      update_nc_map_via_inst(cover_layers, eval(layer_functions, new_im))
      #y1 = test_object.dnn.predict_classes(np.array([im]))[0]
      #y2= test_object.dnn.predict_classes(np.array([new_im]))[0]
      y1 =(np.argmax(test_object.dnn.predict(np.array([new_im])))) 
      y2= (np.argmax(test_object.dnn.predict(np.array([im]))))
      if y1 != y2: 
        adversarials.append([im, new_im])
        inp_ub=test_object.inp_ub
        save_adversarial_examples([new_im/(inp_ub*1.0), '{0}-adv-{1}'.format(len(adversarials), y1)], [im/(inp_ub*1.0), '{0}-original-{1}'.format(len(adversarials), y2)], None, nc_results.split('/')[0]) 
      #old_acts=eval(layer_functions, im)
      #new_acts=eval(layer_functions, new_im)
      #if nc_layer.is_conv:
      #  print ('\n should be < 0', old_acts[nc_layer.layer_index][pos[1]][pos[2]][pos[3]][pos[4]], '\n')
      #  print ('\n should be > 0', new_acts[nc_layer.layer_index][pos[1]][pos[2]][pos[3]][pos[4]], '\n')
    else:
      print ('\nis NOT feasible!!!\n')
    covered, not_covered=nc_report(cover_layers)
    f = open(nc_results, "a")
    f.write('NC-cover: {0} #test cases: {1} #adversarial examples: {2}\n'.format(1.0 * covered / (covered + not_covered), len(test_cases), len(adversarials)))
    f.close()
    #break

