import os
import random
import re
import tarfile
import sys
import itertools
import random
from math import ceil, floor


from torch.utils import data
import numpy as np

from utils import image_loader, download


def create_datasets(dataroot, train_val_split=0.9):
    if not os.path.isdir(dataroot):
        os.mkdir(dataroot)

    dataroot_files = os.listdir(dataroot)
    data_tarball_file = []
    data_dir_name = []

    if data_dir_name not in dataroot_files:
        if data_tarball_file not in dataroot_files:
            tarball = download(dataroot, DATASET_TARBALL)
        with tarfile.open(tarball, 'r') as t:
            def is_within_directory(directory, target):
                
                abs_directory = os.path.abspath(directory)
                abs_target = os.path.abspath(target)
            
                prefix = os.path.commonprefix([abs_directory, abs_target])
                
                return prefix == abs_directory
            
            def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
            
                for member in tar.getmembers():
                    member_path = os.path.join(path, member.name)
                    if not is_within_directory(path, member_path):
                        raise Exception("Attempted Path Traversal in Tar File")
            
                tar.extractall(path, members, numeric_owner=numeric_owner) 
                
            
            safe_extract(t, dataroot)


  
        
def create_datasetsR(race, number_of_people, dataroot):
    if not os.path.isdir(dataroot):
        os.mkdir(dataroot)


    images_root = os.path.join(dataroot, race)
    names = os.listdir(images_root)
    if len(names) == 0:
        raise RuntimeError('Empty dataset')

    whole_set=[]
    random.shuffle(names)
    names = names[:number_of_people]
    for klass, name in enumerate(names):
          def add_class(image):
            image_path = os.path.join(images_root, name, image)
            return (image_path, klass, name)
          images_of_person = os.listdir(os.path.join(images_root, name))
          whole_set += map(
                    add_class,
                    images_of_person)
           
    return whole_set, len(names)

def fold(folds, dataset):
         tot_length = len(dataset)
         split_length = tot_length // folds
         for i in range(folds):
            train_dataset = DatasetSplit(dataset, (i + 1) * split_length, tot_length - split_length)
            val_dataset = DatasetSplit(dataset, i * split_length, split_length)
            yield (val_dataset, train_dataset)

class DatasetSplit(data.Dataset):
    def __init__(self, dataset, index, length):
        super(DatasetSplit, self).__init__()
        self.dataset = dataset
        self.index = index
        self.length = length
    def __len__(self):
        return self.length
    def __getitem__(self, idx):
        index = (self.index + idx) % len(self.dataset)
        return self.dataset[index]  
   
 
class Dataset(data.Dataset):

    def __init__(self, datasets, transform=None, target_transform=None):
        self.datasets = datasets
        self.num_classes = len(datasets)
        self.transform = transform
        self.target_transform = target_transform

    def __len__(self):
        return len(self.datasets)

    def __getitem__(self, index):
        image = image_loader(self.datasets[index][0])
        if self.transform:
            image = self.transform(image)
        return (image, self.datasets[index][1], self.datasets[index][2])
    
class PairedDataset(data.Dataset):

    def __init__(self, dataroot, pairs_cfg, transform=None, loader=None):
        self.dataroot = dataroot
        self.pairs_cfg = pairs_cfg
        self.transform = transform
        self.loader = loader if loader else image_loader

        self.image_names_a = []
        self.image_names_b = []
        self.matches = []
       
        self._prepare_dataset()

    def __len__(self):
        return len(self.matches)

    def __getitem__(self, index):
        return (self.transform(self.loader(self.image_names_a[index])),
                self.transform(self.loader(self.image_names_b[index])),
                self.matches[index])

    def _prepare_dataset(self):
        raise NotImplementedError
        
class LFWPairedDataset(PairedDataset):

    def _prepare_dataset(self):
        pairs = self._read_pairs(self.pairs_cfg)

        for pair in pairs:
            if len(pair) == 3:
                match = True
                name1, name2, index1, index2 = \
                    pair[0], pair[0], int(pair[1]), int(pair[2])

            else:
                match = False
                name1, name2, index1, index2 = \
                    pair[0], pair[2], int(pair[1]), int(pair[3])

            self.image_names_a.append(os.path.join(
                    self.dataroot,
                    name1, "{}_{:04d}.jpg".format(name1, index1)))

            self.image_names_b.append(os.path.join(
                    self.dataroot,
                    name2, "{}_{:04d}.jpg".format(name2, index2)))
            self.matches.append(match)

    def _read_pairs(self, pairs_filename):
        pairs = []
        with open(pairs_filename, 'r') as f:
            for line in f.readlines():
                pair = line.strip().split()
                pairs.append(pair)
        return pairs
