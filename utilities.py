import cv2
import torch
import numpy as np


class Webcam:
    def __init__(self, cam_num):
        self.cap = cv2.VideoCapture(cam_num, cv2.CAP_DSHOW)
        cv2.namedWindow("ExpMaskV1")
        cv2.createTrackbar("Scale/10 ", "ExpMaskV1", 20, 30, lambda x: None)

    def read(self):
        return self.cap.read()[1]

    def show(self, frame):
        cv2.imshow("ExpMaskV1", frame)

    def mirror(self, frame):
        return cv2.flip(frame, 1)

    def track_pos(self):
        return cv2.getTrackbarPos("Scale/10 ", "ExpMaskV1")

    def set_pos(self, pos):
        cv2.setTrackbarPos("Scale/10 ", "ExpMaskV1", pos)

    def wait(self, delay):
        event = cv2.waitKey(delay)
        if event == ord("c"):
            print("[INFO]: Capturing...")
            return True
        if event == ord("q"):
            self.destroy()
            print("[INFO]: Quitting...")
            quit()

    def destroy(self):
        self.cap.release()
        cv2.destroyAllWindows()


class Page_A:
    def __init__(self, coord):
        self.coord = coord
        self.pts = []

    def render(self, frame, scale):
        self.pts = [(self.coord[0]/2)-((self.coord[2]*scale)/2),
                    (self.coord[1]/2)-((self.coord[3]*scale)/2),
                    self.coord[2]*scale,
                    self.coord[3]*scale]
        self.pts = list(map(int, self.pts))
        cv2.rectangle(frame, (self.pts[0], self.pts[1]),
                      (self.pts[0]+self.pts[2], self.pts[1]+self.pts[3]),
                      (100, 200, 100), 2)
        cv2.rectangle(frame, (188, 362), (188+264, 470), (0, 0, 0), -1)
        cv2.rectangle(frame, (188, 362), (188+264, 470), (200, 200, 200), 2)
        cv2.putText(frame, "Press C To Capture", (216, 402), cv2.FONT_HERSHEY_TRIPLEX,
                    0.6, (100, 200, 200), 1)
        cv2.putText(frame, "Press Q To Quit", (232, 442), cv2.FONT_HERSHEY_TRIPLEX,
                    0.6, (100, 100, 200), 1)

    def grab(self, frame):
        face = frame[self.pts[1]: self.pts[1]+self.pts[3],
                     self.pts[0]: self.pts[0]+self.pts[2]]
        return face


class LandmarkFinder:
    def __init__(self, model_path):
        state_dict = torch.load(model_path, map_location="cpu")
        self.model = torch.nn.Sequential(torch.nn.Conv2d(3, 512, (3, 3), padding=1),
                                         torch.nn.ReLU(),
                                         torch.nn.Conv2d(
                                             512, 512, (3, 3), padding=1),
                                         torch.nn.ReLU(),
                                         torch.nn.MaxPool2d((2, 2), stride=2),
                                         torch.nn.Conv2d(
                                             512, 256, (3, 3), padding=1),
                                         torch.nn.ReLU(),
                                         torch.nn.Conv2d(
                                             256, 256, (3, 3), padding=1),
                                         torch.nn.ReLU(),
                                         torch.nn.MaxPool2d((2, 2), stride=2),
                                         torch.nn.Flatten(),
                                         torch.nn.Linear(256*27*22, 10))
        self.model.load_state_dict(state_dict)
        self.model.eval()

    def prep(self, image):
        image = self.bgr2rgb(image)
        image = self.normalize(image)
        return torch.tensor(image).permute(2, 0, 1).unsqueeze(dim=0)

    def bgr2rgb(self, image):
        return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    def normalize(self, image):
        return np.interp(np.float32(image), (0, 255), (-1, +1))

    def search(self, sample):
        pred = self.model(sample.to(torch.float32))
        pred = pred.detach().cpu().numpy()
        pred = np.int32(pred)
        pred = pred[0]
        return pred

    def draw(self, image, pred):
        for i in range(0, 10, 2):
            pts = pred[i: i+2]
            cv2.circle(image, pts, 2, (255, 0, 0), -1)


class Page_B:
    def __init__(self, bg):
        self.bg = np.zeros((480, 640, 3), dtype=np.uint8)

    def render(self, images):
        while True:
            self.bg = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.rectangle(self.bg, (113, 20), (527, 178), (200, 200, 200), 8)
            images = [cv2.resize(i, (138, 158)) for i in images]
            self.bg[20: 20+158, 113: 113+138] = images[0]
            self.bg[20: 20+158, 113+138: 113+138+138] = images[1]
            self.bg[20: 20+158, 113+138+138: 113+138+138+138] = images[2]
            cv2.putText(self.bg, "Face", (140, 228), cv2.FONT_HERSHEY_TRIPLEX,
                        0.8, (150, 150, 255), 1)
            cv2.putText(self.bg, "Landmark", (250, 228), cv2.FONT_HERSHEY_TRIPLEX,
                        0.8, (150, 255, 150), 1)
            cv2.putText(self.bg, "Mask", (430, 228), cv2.FONT_HERSHEY_TRIPLEX,
                        0.8, (255, 150, 150), 1)
            cv2.putText(self.bg, "->", (207, 228), cv2.FONT_HERSHEY_COMPLEX, 
                        0.7, (200, 200, 200), 3)
            cv2.putText(self.bg, "->", (393, 228), cv2.FONT_HERSHEY_COMPLEX, 
                        0.7, (200, 200, 200), 3)
            cv2.rectangle(self.bg, (170, 350), (445, 480), (40, 40, 40), -1)
            cv2.rectangle(self.bg, (170, 350), (445, 480), (200, 200, 200), 3)
            cv2.putText(self.bg, "Press R To Return", (180, 380), cv2.FONT_HERSHEY_TRIPLEX,
                        0.8, (100, 200, 200), 1)
            cv2.putText(self.bg, "Press S To Save", (200, 420), cv2.FONT_HERSHEY_TRIPLEX,
                        0.8, (200, 200, 100), 1)
            cv2.putText(self.bg, "Press Q To Quit", (212, 460), cv2.FONT_HERSHEY_TRIPLEX,
                        0.7, (100, 100, 200), 1)
            cv2.imshow("ExpMaskV1(result)", self.bg)
            event = cv2.waitKey(1)
            event = self.check_event(event, images)
            if event == "r":
                return "r"
        
    def check_event(self, event, images):
        if event == ord("r"):
            print("[INFO]: Returning...")
            return "r"
        
        elif event == ord("s"):
            print("[INFO]: Saving 'Original.jpg'...")
            cv2.imwrite("Original.jpg", images[0])
            print("[INFO]: Saving 'Landmarks.jpg'...")
            cv2.imwrite("Landmarks.jpg", images[1])
            print("[INFO]: Saving 'Mask.jpg'...")
            cv2.imwrite("Mask.jpg", images[2])
            
        elif event == ord("q"):
            quit()


class Reshape(torch.nn.Module):
    def __init__(self, size):
        super().__init__()
        self.size = size

    def forward(self, x):
        return x.view(x.size(0), *self.size)

class MaskGenerator:
    def __init__(self, model_path):
        state_dict = torch.load(model_path, map_location="cpu")
        self.model = torch.nn.Sequential(
            torch.nn.Linear(10, 512*27*22),
            Reshape((512, 27, 22)),
            torch.nn.Upsample(scale_factor=2, mode="bilinear",
                              align_corners=False),
            torch.nn.ConvTranspose2d(512, 512, (3, 3), padding=1),
            torch.nn.SELU(),
            torch.nn.ConvTranspose2d(512, 256, (3, 3), padding=1),
            torch.nn.SELU(),
            torch.nn.Upsample(scale_factor=2, mode="bilinear",
                              align_corners=False),
            torch.nn.ConvTranspose2d(256, 256, (3, 3), padding=1),
            torch.nn.SELU(),
            torch.nn.ConvTranspose2d(256, 128, (3, 3), padding=1),
            torch.nn.SELU(),
            torch.nn.ConvTranspose2d(128, 3, (1, 1)),
            torch.nn.Tanh()
        )
        self.model.load_state_dict(state_dict)
        self.model.eval()
        
    def prep(self, sample):
        return torch.tensor(sample).reshape(1, 10).to(torch.float32)
    
    def denormalize(self, pred):
        pred = (pred + 1.0)/2.0
        pred = pred.permute(1, 2, 0).detach().cpu().numpy()
        pred = pred * 255
        return pred
    
    def generate(self, sample):
        pred = self.model(sample).squeeze()
        pred = self.denormalize(pred)
        pred = cv2.cvtColor(np.uint8(pred), cv2.COLOR_RGB2BGR)
        return pred