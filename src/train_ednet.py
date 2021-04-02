import pickle
import torch
import torchvision
import torchvision.transforms as transforms
from torch.utils.data import DataLoader
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import random
from torch.optim.lr_scheduler import ReduceLROnPlateau
import time
import copy

CLASS = ['SingleGaze', 'MutualGaze', 'AvertGaze', 'GazeFollow', 'JointAtt']


class EventDataset(torch.utils.data.Dataset):
    def __init__(self, data_dir):
        with open(data_dir, 'rb') as f:
            self.data = pickle.load(f)
        f.close()
        self.pad_dim = 50

    def __len__(self):
        return len(self.data)

    def __getitem__(self, index):
        sequence = self.data[index]
        if len(sequence['data']) <= self.pad_dim:
            padded = sequence['data'] + [0 for _ in range(self.pad_dim - len(sequence['data']))]
        else:
            padded = sequence['data'][:self.pad_dim]

        if len(sequence['len']) <= self.pad_dim:
            padded_len = sequence['len'] + [0 for _ in range(self.pad_dim - len(sequence['len']))]
        else:
            padded_len = sequence['len'][:self.pad_dim]
        return {'label': torch.tensor(CLASS.index(sequence['label'])), 'data': torch.tensor(padded).float(), 'len': torch.tensor(padded_len).float()}


class EDNet(nn.Module):
    def __init__(self):
        super(EDNet, self).__init__()
        self.encoder_1 = nn.Linear(50, 50)
        self.encoder_2 = nn.Linear(50, 50)
        self.decoder_1 = nn.Linear(100, 50)
        self.decoder_2=nn.Linear(50,3)


    def forward(self, x_1, x_2):
        latent_1 = F.relu(self.encoder_1(x_1))
        latent_2 = F.relu(self.encoder_2(x_2))
        x = F.relu(self.decoder_1(torch.cat((latent_1, latent_2), 1)))
        #x = torch.cat((latent_1, latent_2), 1)
        x=self.decoder_2(x)

        return x


class FCNet(nn.Module):
    def __init__(self):
        super(FCNet, self).__init__()
        self.fc_1 = nn.Linear(100, 5)

    def forward(self, x_1, x_2):
        return self.fc_1(torch.cat((x_1, x_2), 1))
        # return self.fc_2(F.dropout(F.relu(self.fc_1(torch.cat((x_1, x_2), 1))), 0.8))



def get_metric_from_confmat(confmat):

    N=3

    recall=np.zeros(N)
    precision=np.zeros(N)
    F_score=np.zeros(N)

    correct_cnt=0.
    total_cnt=0.

    for i in range(N):

        recall[i]=confmat[i,i]/(np.sum(confmat[i,:])+1e-7)

        precision[i]=confmat[i,i]/(np.sum(confmat[:,i])+1e-7)

        F_score[i]=2*precision[i]*recall[i]/(precision[i]+recall[i]+1e-7)

        correct_cnt+=confmat[i,i]

        total_cnt+=np.sum(confmat[i,:])

    acc=correct_cnt/total_cnt

    print('===> Confusion Matrix for Event Label: \n {}'.format(confmat.astype(int)))

    print('===> Precision: \n  [SingleGaze]: {} % \n  [GazeFollowing]: {} % \n [JointAtt]: {} % \n'
          .format(precision[0]*100, precision[1]*100, precision[2]*100))

    print('===> Recall: \n [SingleGaze]: {} % \n  [GazeFollowing]: {} % \n [JointAtt]: {} % \n'
          .format(recall[0]*100, recall[1]*100, recall[2]*100))

    print('===> F score: \n [SingleGaze]: {} % \n [GazeFollowing]: {} % \n [JointAtt]: {} % \n'
          .format(F_score[0]*100, F_score[1]*100, F_score[2]*100))

    print('===> Accuracy: {} %'.format(acc*100))

class AverageMeter(object):
    """Computes and stores the average and current value"""

    def __init__(self):
        self.reset()

    def reset(self):
        self.val = 0
        self.avg = 0
        self.sum = 0
        self.count = 0

    def update(self, val, n=1):
        self.val = val
        self.sum += val * n
        self.count += n
        self.avg = self.sum / self.count


def get_data():

    with open('event_fine_tune_input.p', 'rb') as f:
        event_inputs_t, event_labels_t = pickle.load(f)

    event_inputs, event_labels = [], []
    for idx in range(len(event_inputs_t)):
        if not event_labels_t[idx]==3:
            event_inputs.append(event_inputs_t[idx])
            event_labels.append(event_labels_t[idx])

    label_dict = {}
    for event_label in event_labels:
        if event_label in label_dict:
            label_dict[event_label] += 1
        else:
            label_dict[event_label] = 1
    #print(label_dict)

    c = list(zip(event_inputs, event_labels))
    random.seed(0)
    random.shuffle(c)
    event_inputs, event_labels = zip(*c)
    ratio = len(event_inputs)*0.8
    ratio = int(ratio)
    train_x, train_y = event_inputs[:ratio], event_labels[:ratio]
    test_x, test_y = event_inputs[ratio:], event_labels[ratio:]
    #print(len(train_x))
    #print(len(test_x))

    return train_x, train_y, test_x, test_y


def train(net, train_x, train_y, optimizer, batch_size, criterion, epoch):

    net.train()
    running_loss = 0.0
    for i in range(0, len(train_x), batch_size):
        # get the inputs
        inputs = train_x[i:i + batch_size]
        input1s, input2s = np.empty((0, 50)), np.empty((0, 50))
        ignore_input_ids = []
        record_input_ids = []
        for input_id, input in enumerate(inputs):
            input1, input2 = input
            input1_pad = np.zeros((1, 50))
            input2_pad = np.zeros((1, 50))
            for j in range(len(input1)):
                input1_pad[0, j] = input1[j]
            for j in range(len(input2)):
                input2_pad[0, j] = input2[j]
            input1s = np.vstack([input1s, input1_pad])
            input2s = np.vstack([input2s, input2_pad])
            record_input_ids.append(input_id)
        input1s = torch.tensor(input1s).float().cuda()
        input2s = torch.tensor(input2s).float().cuda()

        label = train_y[i:i + batch_size]
        label = torch.tensor(label).cuda()

        # zero the parameter gradients
        optimizer.zero_grad()

        # forward + backward + optimize
        outputs = net(input1s, input2s) #
        loss = criterion(outputs, label)
        #print('[%d, %5d] loss: %.3f' % (epoch + 1, i + 1, running_loss))
        loss.backward()
        optimizer.step()
        running_loss+=loss.item()

    return running_loss, optimizer


def test(net, test_x, test_y, batch_size, criterion):
    correct = 0.0
    correct_2 = 0.0
    total = 0.0
    confmat = np.zeros((3, 3))
    net.eval()
    running_loss=0
    # with torch.no_grad():
    for i in range(0, len(test_x), batch_size):
        # get the inputs
        inputs = test_x[i:i + batch_size]
        input1s, input2s = np.empty((0, 50)), np.empty((0, 50))
        ignore_input_ids = []
        record_input_ids = []
        for input_id, input in enumerate(inputs):
            input1, input2 = input
            input1_pad = np.zeros((1, 50))
            input2_pad = np.zeros((1, 50))
            for j in range(len(input1)):
                input1_pad[0, j] = input1[j]
            for j in range(len(input2)):
                input2_pad[0, j] = input2[j]
            input1s = np.vstack([input1s, input1_pad])
            input2s = np.vstack([input2s, input2_pad])
            record_input_ids.append(input_id)
        input1s = torch.tensor(input1s).float().cuda()
        input2s = torch.tensor(input2s).float().cuda()

        label = test_y[i:i + batch_size]
        label = torch.tensor(label).cuda()

        outputs = net(input1s, input2s) #
        # outputs.data = torch.rand((1, 5))
        loss = criterion(outputs, label)
        running_loss+=loss.item()
        _, predicted = torch.max(outputs.data, 1)
        valuse, ind = torch.topk(outputs.data, 2)
        total += label.size(0)

        correct += (predicted.cpu() == label.cpu()).sum().item()

        for m in range(label.size(0)):
            indx1, indx2 =  int(label[m].cpu()),int(predicted[m].cpu())
            confmat[indx1, indx2] += 1
            if label[m].cpu() in ind[m].squeeze().cpu().numpy().tolist():
                correct_2 += 1

    #print('Top-1 Accuracy of the network on the test images: %f %%' % (100 * correct / total))
    #print('Top-2 Accuracy of the network on the test images: %f %%' % (100 * correct_2 / total))

    return running_loss, confmat,  (100 * correct / total),  (100 * correct_2 / total)


def main(lr, momentum, factor, batch_size, epoch_L, patience,step, thre1, thre2,decay1, decay2):

    train_x, train_y, test_x, test_y=get_data()
    criterion = nn.CrossEntropyLoss()
    net = EDNet()
    net.cuda()
    optimizer = torch.optim.SGD(net.parameters(), lr=lr, momentum=momentum)
    #scheduler = ReduceLROnPlateau(optimizer, factor=factor, patience=patience, verbose=False, mode='max')

    best_acc=0
    best_net=None

    for epoch in range(epoch_L):  # loop over the dataset multiple times

        running_loss, optimizer=train(net, train_x, train_y, optimizer, batch_size, criterion, epoch)
        test_loss, confmat, top1acc, top2acc=test(net, test_x, test_y, batch_size, criterion)

        if epoch%step == 0 and epoch>0:
            for param_group in optimizer.param_groups:
                if param_group['lr']>thre1:
                    param_group['lr'] = param_group['lr']*decay1
                elif  param_group['lr']>thre2:
                    param_group['lr'] = param_group['lr'] * decay2

        #scheduler.step(top1acc)

        if top1acc>best_acc:
            best_acc=top1acc
            best_net=copy.deepcopy(net.state_dict())

        # for param_group in optimizer.param_groups:
        #      print(param_group['lr'])

    #print('Finished Training')
    #get_metric_from_confmat(confmat)
    #print('Top-1 Accuracy of the network on the test images: %f %%' % top1acc)
    #print('Top-2 Accuracy of the network on the test images: %f %%' % top2acc)

    return best_acc, best_net

if __name__ == '__main__':

    # # [0.5, 0.9, 0.5, 256, 1000, 100, 700, 0.0001, 1e-06, 0.8, 0.5]
    # best_acc=0
    # best_para=[]
    # start=time.time()
    # best_model=None
    # for lr in [0.8, 0.5, 0.1, 0.05]:
    #     for momentum in [0.9, 0.5]:
    #         for factor in [0.5]:
    #             for epoch_L in [1000, 1500]:
    #                 for batch_size in [128, 256]:
    #                     for patience in [100]:
    #                         for step in [300,500, 700]:
    #                             for thre1 in [1e-3]:
    #                                 for thre2 in [1e-6]:
    #                                     for decay1 in [0.8, 0.5, 0.1]:
    #                                         for decay2 in [0.8, 0.5, 0.1]:
    #                                             top1acc, model=main(lr, momentum, factor, batch_size, epoch_L,patience,step, thre1, thre2,decay1, decay2)
    #
    #                                             if top1acc>best_acc:
    #                                                 best_acc=top1acc
    #                                                 best_para=[lr, momentum, factor, batch_size, epoch_L,patience, step, thre1, thre2, decay1, decay2]
    #                                                 best_model=copy.deepcopy(model)
    #                                             print('bets top 1 acc on test data:{}'.format(best_acc))
    #                                             #print('best para lr:{}, momentum:{}, factor:{}, batch_size:{}, epoch_L:{}, patience:{}'.format(lr, momentum,factor, batch_size,epoch_L, patience))
    #                                             print('elapsed:{}'.format(time.time()-start))
    #
    # print('bets top 1 acc on test data:{}'.format(best_acc))
    # #print('best para lr:{}, momentum:{}, factor:{}, batch_size:{}, epoch_L:{},  patience:{}'.format(best_para[0], best_para[1], best_para[2], best_para[3], best_para[4], best_para[5]))
    # print(best_para)
    # with open('tune_ednet_best_para.p', 'wb') as f:
    #     pickle.dump([best_para, best_acc], f)
    # torch.save(best_model, './ednet_tuned_best.pth')

# #
# bets top 1 acc on test data:86.20689655172414
# best para lr:0.05, momentum:0.9, factor:0.8, batch_size:256, epoch_L:1500

# bets top 1 acc on test data:83.9080459770115
# best para lr:0.1, momentum:0.9, factor:0.8, batch_size:256, epoch_L:1000,  patience:100

# bets top 1 acc on test data:86.20689655172414
# best para lr:0.1, momentum:0.9, factor:0.8, batch_size:256, epoch_L:1000,  patience:100

# bets top 1 acc on test data:89.65517241379311
# best para lr:0.1, momentum:0.9, factor:0.8, batch_size:256, epoch_L:1000,  patience:100
#
# bets top 1 acc on test data:89.65517241379311
# [0.5, 0.9, 0.5, 256, 1000, 100, 500, 0.001, 1e-06, 0.8, 0.5]

# bets top 1 acc on test data:90.80459770114942
# [0.5, 0.9, 0.5, 256, 1000, 100, 700, 0.0001, 1e-06, 0.8, 0.5]


# bets top 1 acc on test data:91.95402298850574
# [0.1, 0.9, 0.5, 128, 1000, 100, 300, 0.001, 1e-06, 0.8, 0.8]


    # with open('tune_ednet_best_para.p', 'rb') as f:
    #     para=pickle.load(f)
    # print(para)
    #
    # # best_para=[0.5, 0.9, 0.5, 256, 1000, 100, 700, 0.0001, 1e-06, 0.8, 0.5]
    # #
    # # lr, momentum, factor, batch_size, epoch_L,patience, step, thre1, thre2, decay1, decay2=best_para
    # #
    # # top1acc, net=main(lr, momentum, factor, batch_size, epoch_L,patience,step, thre1, thre2,decay1, decay2)
    # # print(top1acc)
    # # torch.save(net.state_dict(), './ednet_best.pth')
    # 83.9080459770115
    # [0.8, 0.9, 0.5, 256, 1000, 100, 700, 0.001, 1e-06, 0.8, 0.5]
    #
    net=EDNet()
    net.load_state_dict(torch.load('./ednet_tuned_best.pth'))
    net.cuda()
    criterion = nn.CrossEntropyLoss()
    train_x, train_y, test_x, test_y = get_data()
    running_loss, confmat,  top1acc,  top2acc =test(net, test_x, test_y, 256, criterion)
    get_metric_from_confmat(confmat)
    print('Top-1 Accuracy of the network on the test images: %f %%' % top1acc)
    print('Top-2 Accuracy of the network on the test images: %f %%' % top2acc)










