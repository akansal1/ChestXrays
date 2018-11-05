import torchvision.models as models
from torch import nn
import torch.nn.functional as F
from torch.nn.modules.linear import Linear
import torch
from dataset import MyDataLoader, Iterator


def averageCrossEntropy(output, label):
    """
    :param output: Tensor of shape batchSize x Nclasses
    :param label: Tensor of shape batchSize x Nclasses
    :return: Sum of the per class entropies
    """
    loss = torch.zeros(1, requires_grad=False)
    if torch.cuda.is_available():
        loss = loss.cuda()

    crossEntropy = F.binary_cross_entropy
    for i in range(output.size()[1]):
        loss += crossEntropy(output[:, i], label[:, i])

    return loss


def addDropoutRec(module, p):
    if isinstance(module, nn.modules.conv.Conv2d) or isinstance(module, nn.modules.Linear):
        return nn.Sequential(module, nn.Dropout(p))
    for name in module._modules.keys():
        module._modules[name] = addDropoutRec(module._modules[name], p=p)

    return module


def addDropout(net, p=0.1):
    for name in net.features._modules.keys():
        if name != "conv0":
            net.features._modules[name] = addDropoutRec(net.features._modules[name], p=p)
    net.classifier = addDropoutRec(net.classifier, p=p)
    return net


class myDenseNet(nn.Module):
    """
    see https://github.com/pytorch/vision/blob/master/torchvision/models/densenet.py
    """
    def __init__(self, out_features=14):
        super(myDenseNet, self).__init__()
        net = models.densenet121(pretrained=True)
        self.features = net.features
        self.classifier = nn.Sequential(Linear(in_features=1024, out_features=out_features), nn.Sigmoid())

    def forward(self, x):
        activations = []
        for feat in self.features:
            x = feat(x)
            activations.append(x)

        out = F.relu(x, inplace=True)
        out = F.avg_pool2d(out, kernel_size=7, stride=1).view(x.size(0), -1)
        activations.append(out)
        out = self.classifier(out)
        activations.append(out)
        return activations


if __name__ == "__main__":

    ####################################################################################################################
    # Test model
    ####################################################################################################################

    # print([method_name for method_name in dir(models.densenet121(pretrained=True))])

    # Local Dataloader
    datadir = "/home/user1/Documents/Data/ChestXray/images"
    train_csvpath = "/home/user1/Documents/Data/ChestXray/DataTrain.csv"
    # Image Size fed to the network
    inputsize = [224, 224]

    mydensenet = myDenseNet()
    origdensenet = models.densenet121(pretrained=True)

    # print(type(densenet.classifier[0]), type(densenet.classifier[1]))
    #
    for name, param in mydensenet.named_parameters():
        print(name, param.requires_grad)

    quit()

    dataloader_iterator = Iterator(MyDataLoader(datadir, train_csvpath, inputsize, batch_size=16))

    data, label = dataloader_iterator.next()

    mydensenet.eval()

    # print(data.size())
    # print(mydensenet(data)[-1])

    mydensenet = addDropout(mydensenet, p=0.1)

    for name, param in mydensenet.named_parameters():
        print(name, param.requires_grad)

    mydensenet.eval()

    # print(mydensenet(data)[-1])

    # for name, param in mydensenet.named_parameters():
    #     print(name, param.requires_grad)

    # print(origdensenet(data))

    # activations = mydensenet(data)
    # for image in activations:
    #     print(image.size())

    # for name, param in mydensenet.named_parameters():
    #     print(name)
    #
    # print(mydensenet.features.denseblock4.denselayer16.conv2.weight.size())
    # print(mydensenet.features.denseblock3.denselayer24.conv2.weight.size())
    # print(mydensenet.features.denseblock2.denselayer12.conv2.weight.size())
    # print(mydensenet.features.denseblock1.denselayer6.conv2.weight.size())

    quit()

    ####################################################################################################################
    # Test loss function
    ####################################################################################################################

    loss = F.binary_cross_entropy
    input = torch.zeros(3, 5)
    input[1] = 1
    target = torch.zeros(3, 5)  # .random_(5)
    output = loss(input, target)
    #
    # print(input)
    # print(target)
    # print(output)
    #
    # print("type", label.dtype)
    # print("label", label)
    output = mydensenet(data)[-1]

    loss = torch.zeros(1, requires_grad=False)

    crossEntropy = F.binary_cross_entropy
    for i in range(output.size()[1]):
        loss += crossEntropy(label[:, i], label[:, i])

    print(loss)

    print(averageCrossEntropy(mydensenet(data)[-1], label))
    print(averageCrossEntropy(label, label))
