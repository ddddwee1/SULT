import tensorflow as tf 
import dyn.model_attention as M 

bn_training = True

reuse_att = False
reuse_enc = False
reuse_gen = False
reuse_dis = False
reuse_feat = False
reuse_dis2 = False
reuse_dis_f = False
reuse_genatt = False
reuse_agecls = False
reuse_agecls_r = False
reuse_age_enc = {}

def feat_encoder(inp):
	global reuse_enc,bn_training
	with tf.variable_scope('encoder',reuse=reuse_enc):
		mod = M.Model(inp)
		mod.set_bn_training(bn_training)
		mod.convLayer(5,16,stride=1,activation=M.PARAM_LRELU,batch_norm=True) #128
		mod.convLayer(5,32,stride=2,activation=M.PARAM_LRELU,batch_norm=True) #64
		mod.convLayer(5,64,stride=2,activation=M.PARAM_LRELU,batch_norm=True) #32
		mod.convLayer(5,128,stride=2,activation=M.PARAM_LRELU,batch_norm=True) #16
		mod.SelfAttention(32)
		mod.convLayer(3,256,stride=2,activation=M.PARAM_LRELU,batch_norm=True) #8
		mod.convLayer(3,512,stride=2,activation=M.PARAM_LRELU,batch_norm=True) #4
		mod.convLayer(3,512,stride=2,activation=M.PARAM_LRELU,batch_norm=True) #2
		reuse_enc = True
	return mod.get_current_layer()

def age_encoder(inp,ind):
	global reuse_age_enc
	name = 'decoder'+str(ind)
	if not name in reuse_age_enc:
		reuse = False
	else:
		reuse = True
	with tf.variable_scope(name,reuse=reuse):
		mod = M.Model(inp)
		mod.fcLayer(2*2*512,activation=M.PARAM_RELU)
		mod.SelfAttention(is_fc=True,residual=True)
		reuse_age_enc[name] = 1
	return mod.get_current_layer()

def generator(inp):
	global reuse_gen,bn_training
	with tf.variable_scope('generator',reuse=reuse_gen):
		mod = M.Model(inp)
		mod.set_bn_training(bn_training)
		mod.reshape([-1,2,2,512])
		mod.deconvLayer(3,512,stride=2,activation=M.PARAM_LRELU,batch_norm=True) #4
		mod.deconvLayer(3,256,stride=2,activation=M.PARAM_LRELU,batch_norm=True) #8
		mod.deconvLayer(3,128,stride=2,activation=M.PARAM_LRELU,batch_norm=True) #16
		mod.SelfAttention(32)
		mod.deconvLayer(5,64,stride=2,activation=M.PARAM_LRELU,batch_norm=True) #32
		mod.deconvLayer(5,32,stride=2,activation=M.PARAM_LRELU,batch_norm=True) #64
		mod.deconvLayer(5,16,stride=2,activation=M.PARAM_LRELU,batch_norm=True) #128
		mod.deconvLayer(5,3,activation=M.PARAM_TANH) #output
		reuse_gen = True
	return mod.get_current_layer()

def discriminator(inp,age_size):
	global reuse_dis,bn_training
	with tf.variable_scope('discriminator',reuse=reuse_dis):
		mod = M.Model(inp)
		mod.set_bn_training(bn_training)
		mod.convLayer(7,16,stride=2,activation=M.PARAM_LRELU,batch_norm=True) # 32
		mod.convLayer(5,32,stride=2,activation=M.PARAM_LRELU,batch_norm=True) # 16
		mod.SelfAttention(4)
		mod.convLayer(5,64,stride=2,activation=M.PARAM_LRELU,batch_norm=True) # 8
		feat = mod.convLayer(3,128,stride=2,activation=M.PARAM_LRELU,batch_norm=True) # 4 
		adv = mod.convLayer(3,1)
		mod.set_current_layer(feat)
		mod.convLayer(3,128,stride=2,activation=M.PARAM_LRELU,batch_norm=True)
		mod.flatten()
		mod.fcLayer(512,activation=M.PARAM_LRELU,batch_norm=True)
		age = mod.fcLayer(age_size)
		reuse_dis = True
	return adv,age

def discriminator_feature(inp):
	global reuse_dis2,bn_training
	with tf.variable_scope('discriminator_feature',reuse=reuse_dis2):
		mod = M.Model(inp)
		mod.set_bn_training(bn_training)
		mod.fcLayer(256,activation=M.PARAM_LRELU,batch_norm=True)
		mod.fcLayer(64,activation=M.PARAM_LRELU,batch_norm=True)
		mod.fcLayer(1)
		reuse_dis2 = True
	return mod.get_current_layer()

def attention_blk(features):
	global reuse_att
	with tf.variable_scope('attention_blk',reuse=reuse_att):
		# get q0
		f_dim = features.get_shape().as_list()[-1]
		q0 = tf.get_variable('q0',[1,f_dim],initializer=tf.random_normal_initializer(),dtype=tf.float32)
		BSIZE = tf.shape(features[0])
		q0 = tf.tile(q0,[BSIZE,1])

		mod = M.Model(q0)
		mod.QAttention(features)
		mod.fcLayer(f_dim,activation=M.PARAM_TANH)
		mod.QAttention(features)
		reuse_att = True
	return mod.get_current_layer()

def discriminator_f(inp,id_num):
	global reuse_dis_f,bn_training
	with tf.variable_scope('dis_f',reuse=reuse_dis_f):
		mod = M.Model(inp)
		mod.set_bn_training(bn_training)
		mod.flatten()
		mod.fcLayer(512,activation=M.PARAM_LRELU,batch_norm=True)
		feat = mod.fcLayer(512,activation=M.PARAM_LRELU,batch_norm=True)
		adv = mod.fcLayer(1)
		mod.set_current_layer(feat)
		ip = mod.fcLayer(id_num)
		reuse_dis_f = True
	return adv,ip

def generator_att(inp):
	global reuse_genatt,bn_training
	with tf.variable_scope('gen_att',reuse=reuse_genatt):
		mod = M.Model(inp)
		mod.set_bn_training(bn_training)
		mod.deconvLayer(3,512,stride=2,activation=M.PARAM_LRELU,batch_norm=True) #4
		mod.deconvLayer(3,256,stride=2,activation=M.PARAM_LRELU,batch_norm=True) #8
		mod.deconvLayer(3,128,stride=2,activation=M.PARAM_LRELU,batch_norm=True) #16
		mod.SelfAttention(32)
		mod.deconvLayer(5,64,stride=2,activation=M.PARAM_LRELU,batch_norm=True) #32
		mod.deconvLayer(5,32,stride=2,activation=M.PARAM_LRELU,batch_norm=True) #64
		feat = mod.deconvLayer(5,16,stride=2,activation=M.PARAM_LRELU,batch_norm=True) #128
		A = mod.convLayer(5,3,activation=M.PARAM_SIGMOID) #output_attention
		mod.set_current_layer(feat)
		C = mod.convLayer(5,3,activation=M.PARAM_TANH)
		reuse_genatt = True
	return A,C

def age_classify(inp,age_size):
	global reuse_agecls, bn_training
	with tf.variable_scope('age_cls',reuse=reuse_agecls):
		mod = M.Model(inp)
		mod.set_bn_training(bn_training)
		mod.flatten()
		mod.fcLayer(512,activation=M.PARAM_LRELU)
		mod.fcLayer(256,activation=M.PARAM_LRELU)
		mod.fcLayer(age_size)
		reuse_agecls = True
	return mod.get_current_layer()

def age_classify_r(inp,age_size):
	global reuse_agecls_r, bn_training
	with tf.variable_scope('age_cls_r',reuse=reuse_agecls_r):
		mod = M.Model(inp)
		mod.set_bn_training(bn_training)
		mod.gradient_flip_layer()
		mod.flatten()
		mod.fcLayer(512,activation=M.PARAM_LRELU)
		mod.fcLayer(256,activation=M.PARAM_LRELU)
		mod.fcLayer(age_size)
		reuse_agecls = True
	return mod.get_current_layer()