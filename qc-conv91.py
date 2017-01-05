from keras.models import Sequential
from keras.layers import Dense, Dropout, Activation, Convolution2D, MaxPooling2D, Flatten, BatchNormalization, SpatialDropout2D
from keras.optimizers import SGD

import numpy as np
import h5py

import os
import nibabel

import cPickle as pkl

import matplotlib.pyplot as plt

from sklearn.cross_validation import StratifiedShuffleSplit

images_dir = '/gs/scratch/adoyle/'
cluster = True

if cluster:
    images_dir  = '/gs/scratch/adoyle/'
    scratch_dir = os.environ.get('RAMDISK') + '/'
else:
    images_dir   = '/home/adoyle/'
    scratch_dir  = images_dir

print 'SCRATCH', scratch_dir
print 'IMAGES:', images_dir


def load_data(fail_path, pass_path):
    print "loading data..."
    filenames = []
    labels = []

    f = h5py.File(scratch_dir + 'ibis.hdf5', 'w')


    # First loop through the data we need to count the number of files
    # also check dims
    numImgs = 0
    x_dim, y_dim, z_dim = 0, 0, 0
    for root, dirs, files in os.walk(fail_path, topdown=False):
        for name in files:
            numImgs += 1
            if x_dim == 0:
               img =  nibabel.load(os.path.join(root, name)).get_data()
               print np.shape(img)
               x_dim = np.shape(img)[0]
               y_dim = np.shape(img)[1]
               z_dim = np.shape(img)[2]
        for root, dirs, files in os.walk(pass_path, topdown=False):
            for name in files:
                numImgs += 1

    images = f.create_dataset('ibis_t1', (numImgs, x_dim, y_dim, z_dim), dtype='float32')
    labels = np.zeros((numImgs, 2), dtype='bool')

    # Second time through, write the image data to the HDF5 file
    i = 0
    for root, dirs, files in os.walk(fail_path, topdown=False):
        for name in files:
            img = nibabel.load(os.path.join(root, name)).get_data()
            if np.shape(img) == (x_dim, y_dim, z_dim):
                images[i] = img[80, :, :]
                labels[i] = [1, 0]
                filenames.append(os.path.join(root, name))
                i += 1


    for root, dirs, files in os.walk(pass_path, topdown=False):
        for name in files:
            img = nibabel.load(os.path.join(root, name)).get_data()
            if np.shape(img) == (x_dim, y_dim, z_dim):
                images[i] = img[80, :, :]
                labels[i] = [0, 1]
                filenames.append(os.path.join(root, name))
                i += 1

    indices = StratifiedShuffleSplit(labels, test_size=0.4, n_iter=1, random_state=None)

    train_index, test_index = None, None
    for train_indices, test_indices in indices:
        train_index = train_indices
        test_index  = test_indices

    filename_test = []
    for i, f in enumerate(filenames):
        if i in test_index:
            filename_test.append(f)

    # pkl.dump(labels, images_dir + 'labels.pkl')

    return train_index, test_index, labels, filename_test

def load_in_memory(train_index, test_index, labels):
    f = h5py.File(scratch_dir + 'ibis.hdf5', 'r')
    images = f.get('ibis_t1')

    x_train = np.array(images)[train_index]
    y_train = np.array(labels)[train_index]
    x_test  = np.array(images)[test_index]
    y_test  = np.array(labels)[test_index]

    return x_train, x_text, y_train, y_test

def qc_model():
    nb_classes = 2

    model = Sequential()

    model.add(Convolution2D(16, 15, 15, border_mode='same', input_shape=(1, 256, 224)))
    model.add(Activation('relu'))
    model.add(MaxPooling2D(pool_size=(4, 4)))
    model.add(BatchNormalization())
#    model.add(SpatialDropout2D(0.5))

    model.add(Convolution2D(12, 12, 12, border_mode='same'))
    model.add(Activation('relu'))
#    model.add(MaxPooling2D(pool_size=(3, 3)))
#    model.add(SpatialDropout2D(0.5))

    model.add(Convolution2D(12, 5, 5, border_mode='same'))
    model.add(Activation('relu'))
    model.add(MaxPooling2D(pool_size=(2, 2)))
#    model.add(SpatialDropout2D(0.2))
#
    model.add(Convolution2D(12, 3, 3, border_mode='same'))
    model.add(Activation('relu'))
    #    model.add(SpatialDropout2D(0.5))

    model.add(Convolution2D(12, 3, 3, border_mode='same'))
    model.add(Activation('relu'))
    model.add(MaxPooling2D(pool_size=(2, 2)))
    model.add(SpatialDropout2D(0.4))

    model.add(Convolution2D(12, 2, 2, border_mode='same'))
    model.add(Activation('relu'))
    model.add(SpatialDropout2D(0.5))

    model.add(Flatten())
    model.add(Dense(256, init='uniform'))
    model.add(Activation('relu'))
    model.add(Dropout(0.5))
    model.add(Dense(nb_classes, init='uniform'))
    model.add(Activation('softmax'))

    model.compile(loss='categorical_crossentropy',
                  optimizer='sgd',
                  metrics=["accuracy"])
	
	return model

def model_train(x_train, x_test, y_train, y_test, filename_test):

    print "shape of training data:", np.shape(x_train)
    print "shape of testing data:", np.shape(x_test)
    print "shape of training labels:", np.shape(y_train)
    print "shape of testing labels:", np.shape(y_test)
    print "filename list:", len(filename_test)

#    data_dim = 160*256


    model.fit(x_train, y_train,
              nb_epoch=200,
              batch_size=50)
    #should return model to workspace so that I can keep training it

    score = model.evaluate(x_test, y_test, batch_size=10)
    print model.metrics_names
    print score

    for i in range(len(x_test)):
        test_case = x_test[i,...]
        label = y_test[i]

        test_case = np.reshape(test_case, (1, 1, np.shape(test_case)[1], np.shape(test_case)[2]))
        predictions = model.predict(test_case, batch_size=1)
        image = np.reshape(test_case[0, 1,...], (256, 224))
        # plt.imshow(image.T)
        # plt.show()
        print "predictions:", predictions
        print "label:", label
#        print "file:", filename_test[i]

def batch(indices, labels, n):
    f = h5py.File(scratch_dir + 'ibis.hdf5', 'r')
    images = f.get('ibis_t1')

    print images
    x_train = np.zeros((n, 1, 256, 224), dtype=np.float32)
    y_train = np.zeros((n, 2), dtype=np.int8)

    while True:
        np.random.shuffle(indices)

        samples_this_batch = 0
        for i, index in enumerate(indices):
            x_train[i%n, 0, :, :] = images[index]
            y_train[i%n, :]   = labels[index]
            samples_this_batch += 1
            if (i+1) % n == 0:
                yield (x_train, y_train)
                samples_this_batch = 0
            elif i == len(indices)-1:
                yield (x_train[0:samples_this_batch, ...], y_train[0:samples_this_batch, :])
		samples_this_batch = 0

if __name__ == "__main__":
    print "Running automatic QC"
    fail_data = images_dir + "T1_Minc_Fail"
    pass_data = images_dir + "T1_Minc_Pass"

    train_indices, test_indices, labels, filename_test = load_data(fail_data, pass_data)

	model = qc_model()
	model.summary()
    model.fit_generator(batch(train_indices, labels, 2), nb_epoch=num_epochs, samples_per_epoch=len(train_indices), validation_data=batch(test_indices, labels, 2), nb_val_samples=len(test_indices))

    model_config = model.get_config()
    pkl.dumps(model_config, 'convnet_2d_model.pkl')

    score = model.evaluate_generator(batch(test_indices, labels, 2), len(test_indices))
	
    #x_train, x_test, y_train, y_test = load_in_memory(train_index, test_index, labels)
