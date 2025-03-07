import sys
import os
import numpy as np

def read_label(label_path):
    if label_path.endswith(".bin"):
        dict = np.fromfile(label_path, dtype='int64').reshape(25000,)
        print(dict)
        return dict
    else:
        print("Label file should be endswith *.bin, Please check your input!")
        return 0

if __name__ == "__main__":
    output_path = sys.argv[1]
    label_path = sys.argv[2]
    label_dict = read_label(label_path)
    offset = 0
    output_num = 0
    check_num = 0
    files = os.listdir(output_path)
    files.sort()
    for file in files:
        if file.endswith(".bin"):
            output_num += 1
            tmp = np.fromfile(output_path+'/'+file, dtype='float32')
            inf_label = float(tmp)
            if inf_label >0.5:
                inf_label =1
            else:
                inf_label =0
            try:
                pic_name = int(file.split("_output")[0])
                print("%s, inference label:%d, gt_label:%d"%(pic_name,inf_label,label_dict[pic_name]))
                if inf_label == int(label_dict[pic_name]):
                    #print("%s inference result Ok!"%pic_name)
                    check_num += 1
            except:
                print("Can't find %s in the label file: %s"%(pic_name,label_path))
    top1_accuarcy = check_num/output_num
    print("Totol pic num: %d, Top1 accuarcy: %.4f"%(output_num,top1_accuarcy))





