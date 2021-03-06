import logging
import os
import torch
from torch.utils.data import DataLoader
from models.C3D_altered import C3D_altered
from models.my_fc6 import my_fc6
from models.score_regressor import score_regressor
from opts import *
import numpy as np
import cv2 as cv
import tempfile
from torchvision import transforms

from flask import Flask, jsonify
app = Flask(__name__)


@app.route('/predict', methods=['POST'])
def predict():
    return jsonify({'class_id': 'IMAGE_NET_XXX', 'class_name': 'Cat'})


def center_crop(self, img, dim):
    """Returns center cropped image

    Args:Image Scaling
    img: image to be center cropped
    dim: dimensions (width, height) to be cropped from center
    """
    width, height = img.shape[1], img.shape[0]
    #process crop width and height for max available dimension
    crop_width = dim[0] if dim[0]<img.shape[1] else img.shape[1]
    crop_height = dim[1] if dim[1]<img.shape[0] else img.shape[0]
    mid_x, mid_y = int(width/2), int(height/2)
    cw2, ch2 = int(crop_width/2), int(crop_height/2)
    crop_img = img[mid_y-ch2:mid_y+ch2, mid_x-cw2:mid_x+cw2]
    return crop_img


def preprocess_one_video(self, video_file):
    if video_file is not None:
        tfile = tempfile.NamedTemporaryFile(delete=False)
        tfile.write(video_file.read())

        vf = cv.VideoCapture(tfile.name)

        # https: // discuss.streamlit.io / t / how - to - access - uploaded - video - in -streamlit - by - open - cv / 5831 / 8
        frames = None
        while vf.isOpened():
            ret, frame = vf.read()
            if not ret:
                break
            frame = cv.resize(frame, input_resize, interpolation=cv.INTER_LINEAR) #frame resized: (128, 171, 3)
            frame = self.center_crop(frame, (H, H))
            frame = self.transform(frame).unsqueeze(0)
            if frames is not None:
                frame = np.vstack((frames, frame))
                frames = frame
            else:
                frames = frame


        vf.release()
        cv.destroyAllWindows()
        rem = len(frames) % 16
        rem = 16 - rem

        if rem != 0:
            padding = np.zeros((rem, C, H, H))
            print(padding.shape)
            frames = np.vstack((frames, padding))

        frames = np.expand_dims(frames, axis=0)
        print(f"frames shape: {frames.shape}")
        # frames shape: (137, 3, 112, 112)
        frames = DataLoader(frames, batch_size=test_batch_size, shuffle=False)

def inference_with_one_video_frames(self, frames):
    with torch.no_grad():
        pred_scores = [];
        # true_scores = []
        if with_dive_classification:
            pred_position = [];
            pred_armstand = [];
            pred_rot_type = [];
            pred_ss_no = [];
            pred_tw_no = []
            true_position = [];
            true_armstand = [];
            true_rot_type = [];
            true_ss_no = [];
            true_tw_no = []

        model_CNN.eval()
        model_my_fc6.eval()
        model_score_regressor.eval()

        for video in frames:
            print(f"video shape: {video.shape}") # video shape: torch.Size([1, 144, 3, 112, 112])
            video = video.transpose_(1, 2)
            video = video.double()
            clip_feats = torch.Tensor([])
            for i in np.arange(0, len(video), 16):
                print(i)
                clip = video[:, :, i:i + 16, :, :]
                print(f"clip shape: {clip.shape}") # clip shape: torch.Size([1, 3, 16, 112, 112])
                print(f"clip type: {clip.type()}") # clip type: torch.DoubleTensor
                model_CNN = model_CNN.double()
                clip_feats_temp = model_CNN(clip)

                print(f"clip_feats_temp shape: {clip_feats_temp.shape}")
                # clip_feats_temp shape: torch.Size([9, 8192])

                clip_feats_temp.unsqueeze_(0)

                print(f"clip_feats_temp unsqueeze shape: {clip_feats_temp.shape}")
                # clip_feats_temp unsqueeze shape: torch.Size([1, 9, 8192])

                clip_feats_temp.transpose_(0, 1)

                print(f"clip_feats_temp transposes shape: {clip_feats_temp.shape}")
                # clip_feats_temp transposes shape: torch.Size([9, 1, 8192])

                clip_feats = torch.cat((clip_feats, clip_feats_temp), 1)

                print(f"clip_feats shape: {clip_feats.shape}")
                # clip_feats shape: torch.Size([9, 1, 8192])

            clip_feats_avg = clip_feats.mean(1)

            print(f"clip_feats_avg shape: {clip_feats_avg.shape}") # clip_feats_avg shape: torch.Size([9, 8192])
            # clip_feats_avg shape: torch.Size([9, 8192])

            model_my_fc6 = model_my_fc6.double()
            sample_feats_fc6 = model_my_fc6(clip_feats_avg)
            model_score_regressor = model_score_regressor.double()
            temp_final_score = model_score_regressor(sample_feats_fc6)
            pred_scores.extend([element[0] for element in temp_final_score.data.cpu().numpy()])

            print('Predicted scores: ', pred_scores)
            return pred_scores


class DivingHandler:
    def __init__(self):
        self.__transform = transforms.Compose([transforms.ToTensor(),
                                        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])])

    def preprocess(self, video):
        return self.preprocess_one_video(video)

    def inference(self, frames):
        return self.inference_with_one_video_frames(frames)

    def postprocess(self, preds):
        return preds * 17 #TODO: double check the scalar

    def center_crop(self, img, dim):
        """Returns center cropped image

        Args:Image Scaling
        img: image to be center cropped
        dim: dimensions (width, height) to be cropped from center
        """
        width, height = img.shape[1], img.shape[0]
        #process crop width and height for max available dimension
        crop_width = dim[0] if dim[0]<img.shape[1] else img.shape[1]
        crop_height = dim[1] if dim[1]<img.shape[0] else img.shape[0]
        mid_x, mid_y = int(width/2), int(height/2)
        cw2, ch2 = int(crop_width/2), int(crop_height/2)
        crop_img = img[mid_y-ch2:mid_y+ch2, mid_x-cw2:mid_x+cw2]
        return crop_img

    def preprocess_one_video(self, video_file):

        if video_file is not None:
            tfile = tempfile.NamedTemporaryFile(delete=False)
            tfile.write(video_file.read())

            vf = cv.VideoCapture(tfile.name)

            # https: // discuss.streamlit.io / t / how - to - access - uploaded - video - in -streamlit - by - open - cv / 5831 / 8
            frames = None
            while vf.isOpened():
                ret, frame = vf.read()
                if not ret:
                    break
                frame = cv.resize(frame, input_resize, interpolation=cv.INTER_LINEAR) #frame resized: (128, 171, 3)
                frame = self.center_crop(frame, (H, H))
                frame = self.transform(frame).unsqueeze(0)
                if frames is not None:
                    frame = np.vstack((frames, frame))
                    frames = frame
                else:
                    frames = frame


            vf.release()
            cv.destroyAllWindows()
            rem = len(frames) % 16
            rem = 16 - rem

            if rem != 0:
                padding = np.zeros((rem, C, H, H))
                print(padding.shape)
                frames = np.vstack((frames, padding))

            frames = np.expand_dims(frames, axis=0)
            print(f"frames shape: {frames.shape}")
            # frames shape: (137, 3, 112, 112)
            frames = DataLoader(frames, batch_size=test_batch_size, shuffle=False)

    def inference_with_one_video_frames(self, frames):
        with torch.no_grad():
            pred_scores = [];
            # true_scores = []
            if with_dive_classification:
                pred_position = [];
                pred_armstand = [];
                pred_rot_type = [];
                pred_ss_no = [];
                pred_tw_no = []
                true_position = [];
                true_armstand = [];
                true_rot_type = [];
                true_ss_no = [];
                true_tw_no = []

            model_CNN.eval()
            model_my_fc6.eval()
            model_score_regressor.eval()

            for video in frames:
                print(f"video shape: {video.shape}") # video shape: torch.Size([1, 144, 3, 112, 112])
                video = video.transpose_(1, 2)
                video = video.double()
                clip_feats = torch.Tensor([])
                for i in np.arange(0, len(video), 16):
                    print(i)
                    clip = video[:, :, i:i + 16, :, :]
                    print(f"clip shape: {clip.shape}") # clip shape: torch.Size([1, 3, 16, 112, 112])
                    print(f"clip type: {clip.type()}") # clip type: torch.DoubleTensor
                    model_CNN = model_CNN.double()
                    clip_feats_temp = model_CNN(clip)

                    print(f"clip_feats_temp shape: {clip_feats_temp.shape}")
                    # clip_feats_temp shape: torch.Size([9, 8192])

                    clip_feats_temp.unsqueeze_(0)

                    print(f"clip_feats_temp unsqueeze shape: {clip_feats_temp.shape}")
                    # clip_feats_temp unsqueeze shape: torch.Size([1, 9, 8192])

                    clip_feats_temp.transpose_(0, 1)

                    print(f"clip_feats_temp transposes shape: {clip_feats_temp.shape}")
                    # clip_feats_temp transposes shape: torch.Size([9, 1, 8192])

                    clip_feats = torch.cat((clip_feats, clip_feats_temp), 1)

                    print(f"clip_feats shape: {clip_feats.shape}")
                    # clip_feats shape: torch.Size([9, 1, 8192])

                clip_feats_avg = clip_feats.mean(1)

                print(f"clip_feats_avg shape: {clip_feats_avg.shape}") # clip_feats_avg shape: torch.Size([9, 8192])
                # clip_feats_avg shape: torch.Size([9, 8192])

                model_my_fc6 = model_my_fc6.double()
                sample_feats_fc6 = model_my_fc6(clip_feats_avg)
                model_score_regressor = model_score_regressor.double()
                temp_final_score = model_score_regressor(sample_feats_fc6)
                pred_scores.extend([element[0] for element in temp_final_score.data.cpu().numpy()])

                print('Predicted scores: ', pred_scores)
                return pred_scores

if __name__ == '__main__':
    print('PyCharm')
    model_CNN = C3D_altered()
    model_CNN.load_state_dict(torch.load(m1_path, map_location={'cuda:0': 'cpu'}))

    # loading our fc6 layer
    model_my_fc6 = my_fc6()
    model_my_fc6.load_state_dict(torch.load(m2_path, map_location={'cuda:0': 'cpu'}))

    # loading our score regressor
    model_score_regressor = score_regressor()
    model_score_regressor.load_state_dict(torch.load(m3_path, map_location={'cuda:0': 'cpu'}))
    print('Using Final Score Loss')