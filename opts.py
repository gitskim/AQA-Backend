# declaring random seed
randomseed = 0

C, H, W = 3,112,112
input_resize = 171,128#
test_batch_size = 1

m1_path = '/Users/suhyunkim/git/AQATorchDocker/models/model_CNN_94.pth'
m2_path = '/Users/suhyunkim/git/AQATorchDocker/models/model_my_fc6_94.pth'
m3_path = '/Users/suhyunkim/git/AQATorchDocker/models/model_score_regressor_94.pth'
m4_path =with_dive_classification = False
with_caption = False

max_epochs = 100

train_batch_size = 3
test_batch_size = 1

model_ckpt_interval = 1  # in epochs

base_learning_rate = 0.0001

temporal_stride = 16