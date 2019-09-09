import pickle 
import model3 as M 
import random
import numpy as np 
from text import text_to_sequence

def get_tts_dataset(path, bsize, r):
	with open(f'{path}dataset.pkl','rb') as f:
		dataset = pickle.load(f)

	dataset_ids = []
	mel_lengths = []

	for idd, lenn in dataset:
		if lenn <= config.tts_max_mel_len:
			dataset_ids += [idd]
			mel_lengths += [lenn]

	with open(f'{path}text_dict.pkl','rb') as f:
		text_dict = pickle.load(f)

	trainset = TTSDataSet(path, dataset_ids, text_dict, mel_lengths, bsize, bsize*3)

	return trainset 

class TTSDataSet():
	def __init__(self, path, dataids, text_dict, mel_lengths, bsize, binsize):  # add bsize here
		self.path = path 
		self.dataids = dataids
		self.text_dict = text_dict
		self.mel_lengths = mel_lengths
		self.bsize = bsize
		self.binsize = binsize
		assert self.binsize % self.bsize == 0
		self.idx_sorted = np.argsort(self.mel_lengths)
		self.indices = self.gen_indices()
		# positional pointer 
		self.pos = 0
		self.maxiters = len(self.idx_sorted) // self.bsize + int(len(self.idx_sorted)%self.bsize==0)

	def pad_1d(self, x, max_len):
		return np.pad(x, (0, max_len-len(x)), mode='constant')

	def pad_2d(self, x, max_len):
		return np.pad(x, ((0,0), (0, max_len-x.shape[-1])), mode='constant')

	def collate(self, batch):
		lengths = [len(x[0]) for x in batch]
		max_len = max(lengths)
		chars = np.stack([self.pad_1d(x[0], max_len) for x in batch])
		spec_lengths = [x[1].shape[-1] for x in batch]
		max_spec_length = max(spec_lengths) + 1
		if max_spec_length % r !=0:
			max_spec_length += r - max_spec_length % r 
		mel = np.stack([self.pad_2d(x[1], max_spec_length) for x in batch])
		ids = [x[2] for x in batch]
		mel_lens = [x[3] for x in batch]

		# scale spec to -4~+4
		mel = np.float32(mel)
		mel = mel * 8 - 4

		chars = np.long(chars)
		return chars, mel, ids, mel_lens

	def getitem(self, index):
		idd = self.dataids[index]
		x = util.text_to_sequence(self.text_dict[idd], config.tts_cleaner_names)
		mel = np.load(f'{config.melpath}{idd}.npy')
		mel_len = mel.shape[-1]
		return x, mel, idd, mel_len

	def gen_indices(self):
		bins = []
		for i in range(len(self.idx_sorted)//self.binsize):
			this_bin = self.idx_sorted[i*self.binsize : (i+1)*self.binsize]
			this_bin = list(this_bin)
			random.shuffle(this_bin)
			bins += [this_bin]
		random.shuffle(bins)
		binned_idx = np.stack(np.int32(bins)).reshape([-1])

		if len(binned_idx) < len(self.idx_sorted):
			last_bin = self.idx_sorted[len(binned_idx):]
			last_bin = list(last_bin)
			random.shuffle(last_bin)
			last_bin = np.int32(last_bin)
			binned_idx = np.concatenate([binned_idx, last_bin])
		return binned_idx

	def get_next(self):
		pos2 = min(self.pos + self.bsize, len(self.indices))
		idx = self.indices[self.pos: pos2]
		self.pos = pos2
		batch = []
		for i in idx:
			batch.append(self.getitem(i))
		batch = self.collate(batch)
		return batch
		
	def __len__(self):
		return len(self.dataids)

