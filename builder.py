# import PyInstaller.__main__
# PyInstaller.__main__.run(['my_script'])
import cv2
import matplotlib.pyplot as plt
# import imageio.imread

def unpickle(file) -> dict:
    import pickle
    with open(file, 'rb') as fo:
        dict = pickle.load(fo, encoding='bytes')
    return dict

data = unpickle("C:\\Users\\benyo\\Downloads\\cifar-10-python\\cifar-10-batches-py\\data_batch_1")
# print(data)"C:\Users\benyo\Downloads\cifar-10-python\cifar-10-batches-py\data_batch_1"
pics = data['data'.encode('ascii')]
print(pics.shape)
images = image = data['data'.encode('ascii')][20:24]
# plt.figure()
f, axarr = plt.subplots(1,4) 
for i, image in enumerate(images):
# image = data['data'.encode('ascii')][15]
    img = image
    img = img.reshape(3,32,32)
    img = img.transpose(1,2,0)
    axarr[i].imshow(img)
    # plt.imshow(image)
plt.show()