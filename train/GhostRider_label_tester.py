import cv2
import sys
import matplotlib.pyplot as plt

def draw_labels(image_path, label_path):

    img = cv2.imread(image_path)


    with open(label_path, "r") as file:
        for line in file.readlines():
            tokens = line.strip().split()
            class_id = int(tokens[0])
            x_center, y_center, width, height = map(float, tokens[1:])


            x_center, y_center, width, height = x_center * img.shape[1], y_center * img.shape[0], width * img.shape[1], height * img.shape[0]


            x_min, y_min, x_max, y_max = int(x_center - width/2), int(y_center - height/2), int(x_center + width/2), int(y_center + height/2)


            cv2.rectangle(img, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)


            cv2.putText(img, str(class_id), (x_min, y_min - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)


    labeled_image_path = "labeled_" + image_path
    cv2.imwrite(labeled_image_path, img)


    plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    plt.title("Labeled Image")
    plt.show()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python draw_labels.py <image_path> <label_path>")
        sys.exit()

    image_path = sys.argv[1]
    label_path = sys.argv[2]

    draw_labels(image_path, label_path)
