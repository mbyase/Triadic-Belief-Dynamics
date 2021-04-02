import os
import glob
import joblib
import cv2
import numpy as np
import sys
sys.path.append('../3d_pose2gaze')
import utils
import torch
import mymodel


class ViewMap:
    def __init__(self):
        self.kinect_img_path = '../../data_preprocessing2/post_images/kinect/'
        self.skeleton_path = '../../data_preprocessing2/post_skeletons/'
        self.kinect_box_path = '../../data_preprocessing2/post_neighbor_smooth_newseq/'
        self.kinect_point_path = '/home/shuwen/Downloads/pointclouds/'
        self.battery_img_path = '../../data_preprocessing2/post_images/battery/'
        self.mask_cate_path = '../../data_preprocessing2/track_cate_with_frame/'
        self.save_img_path = '../../data_preprocessing2/view_battery_mapping_record_temp/'
        # self.temp_path = ["test_boelter_3", "test_boelter_24", "test_94342_24", "test_94342_18", "test_94342_7", "test_boelter4_3"]
        self.temp_path = ["test_boelter3_9"]
        self.trackers = {'test1': 'skele1.p', 'test2': 'skele2.p', 'test6': 'skele2.p', 'test7': 'skele1.p',
                    'test_9434_1': 'skele2.p', 'test_9434_3': 'skele2.p', 'test_9434_18': 'skele1.p',
                    'test_94342_0': 'skele2.p', 'test_94342_1': 'skele2.p', 'test_94342_2': 'skele2.p',
                    'test_94342_3': 'skele2.p', 'test_94342_4': 'skele1.p', 'test_94342_5': 'skele1.p',
                    'test_94342_6': 'skele1.p', 'test_94342_7': 'skele1.p', 'test_94342_8': 'skele1.p',
                    'test_94342_10': 'skele2.p', 'test_94342_11': 'skele2.p', 'test_94342_12': 'skele1.p',
                    'test_94342_13': 'skele2.p', 'test_94342_14': 'skele1.p', 'test_94342_15': 'skele2.p',
                    'test_94342_16': 'skele1.p', 'test_94342_17': 'skele2.p', 'test_94342_18': 'skele1.p',
                    'test_94342_19': 'skele2.p', 'test_94342_20': 'skele1.p', 'test_94342_21': 'skele2.p',
                    'test_94342_22': 'skele1.p', 'test_94342_23': 'skele1.p', 'test_94342_24': 'skele1.p',
                    'test_94342_25': 'skele2.p', 'test_94342_26': 'skele1.p',
                    'test_boelter_1': 'skele2.p', 'test_boelter_2': 'skele2.p', 'test_boelter_3': 'skele2.p',
                    'test_boelter_4': 'skele1.p', 'test_boelter_5': 'skele1.p', 'test_boelter_6': 'skele1.p',
                    'test_boelter_7': 'skele1.p', 'test_boelter_9': 'skele1.p', 'test_boelter_10': 'skele1.p',
                    'test_boelter_12': 'skele2.p', 'test_boelter_13': 'skele1.p', 'test_boelter_14': 'skele1.p',
                    'test_boelter_15': 'skele1.p', 'test_boelter_17': 'skele2.p', 'test_boelter_18': 'skele1.p',
                    'test_boelter_19': 'skele2.p', 'test_boelter_21': 'skele1.p', 'test_boelter_22': 'skele2.p',
                    'test_boelter_24': 'skele1.p', 'test_boelter_25': 'skele1.p',
                    'test_boelter2_0': 'skele1.p', 'test_boelter2_2': 'skele1.p', 'test_boelter2_3': 'skele1.p',
                    'test_boelter2_4': 'skele1.p', 'test_boelter2_5': 'skele1.p', 'test_boelter2_6': 'skele1.p',
                    'test_boelter2_7': 'skele2.p', 'test_boelter2_8': 'skele2.p', 'test_boelter2_12': 'skele2.p',
                    'test_boelter2_14': 'skele2.p', 'test_boelter2_15': 'skele2.p', 'test_boelter2_16': 'skele1.p',
                    'test_boelter2_17': 'skele1.p',
                    'test_boelter3_0': 'skele1.p', 'test_boelter3_1': 'skele2.p', 'test_boelter3_2': 'skele2.p',
                    'test_boelter3_3': 'skele2.p', 'test_boelter3_4': 'skele1.p', 'test_boelter3_5': 'skele2.p',
                    'test_boelter3_6': 'skele2.p', 'test_boelter3_7': 'skele1.p', 'test_boelter3_8': 'skele2.p',
                    'test_boelter3_9': 'skele2.p', 'test_boelter3_10': 'skele1.p', 'test_boelter3_11': 'skele2.p',
                    'test_boelter3_12': 'skele2.p', 'test_boelter3_13': 'skele2.p',
                    'test_boelter4_0': 'skele2.p', 'test_boelter4_1': 'skele2.p', 'test_boelter4_2': 'skele2.p',
                    'test_boelter4_3': 'skele2.p', 'test_boelter4_4': 'skele2.p', 'test_boelter4_5': 'skele2.p',
                    'test_boelter4_6': 'skele2.p', 'test_boelter4_7': 'skele2.p', 'test_boelter4_8': 'skele2.p',
                    'test_boelter4_9': 'skele2.p', 'test_boelter4_10': 'skele2.p', 'test_boelter4_11': 'skele2.p',
                    'test_boelter4_12': 'skele2.p', 'test_boelter4_13': 'skele2.p',
                    }



    def extract_gaze(self, skeleton):
        skeleton = np.array(skeleton)
        a = skeleton[21] - skeleton[24]
        b = skeleton[22] - skeleton[24]
        normal = np.cross(a, b)
        if np.linalg.norm(normal) > 0:
            normal = normal / np.linalg.norm(normal)
        normal = normal + np.array([0, 1.2, 0])
        gaze_center = np.vstack([skeleton[21], skeleton[22], skeleton[24]]).mean(axis=0) + np.array([0, 0.2, 0])
        return normal, gaze_center


    def cal_angle(self, normal, obj):
        if np.linalg.norm(obj) > 0:
            obj = obj / np.linalg.norm(obj)
        if np.linalg.norm(normal) > 0:
            normal = normal / np.linalg.norm(normal)
        cosin = obj.dot(normal)
        return cosin


    def point2screen(self, points):
        K = [607.13232421875, 0.0, 638.6468505859375, 0.0, 607.1067504882812, 367.1607360839844, 0.0, 0.0, 1.0]
        K = np.reshape(np.array(K), [3, 3])
        rot_points = np.array(points)
        points_camera = rot_points.reshape(3, 1)
        project_matrix = np.array(K).reshape(3, 3)
        points_prj = project_matrix.dot(points_camera)
        points_prj = points_prj.transpose()
        if not points_prj[:, 2][0] == 0.0:
            points_prj[:, 0] = points_prj[:, 0] / points_prj[:, 2]
            points_prj[:, 1] = points_prj[:, 1] / points_prj[:, 2]
        points_screen = points_prj[:, :2]
        assert points_screen.shape == (1, 2)
        points_screen = points_screen.reshape(-1)
        return points_screen

    def mapping_with_3d_box(self):
        gaze_path = './transformed_normal_new_results/'
        skeleton_path = '../../data_preprocessing2/post_skeletons/'
        video_folders = os.listdir(self.kinect_img_path)
        for video_folder in video_folders:
            clips = os.listdir(self.kinect_img_path + video_folder)
            for clip in clips:
                # if not clip == "test_boelter3_8":
                #     continue
                # if not (len(clip.split('_')) > 1 and ((clip.split('_')[1] == "boelter3") or
                #         (clip.split('_')[1] == "boelter2") or (clip.split('_')[1] == "boelter"))):
                #     continue
                # if os.path.exists('./visualize_gaze_with_skele_flex_angle/' + clip + '.avi'):
                #     continue
                if not os.path.exists(gaze_path + clip + '.p'):
                    continue
                if not os.path.exists(os.path.join(self.kinect_box_path, clip)):
                    continue
                if not os.path.exists(self.kinect_point_path + clip):
                    continue
                if not os.path.exists(self.kinect_point_path + clip):
                    continue

                save_path = self.save_img_path + clip
                if not os.path.exists(self.save_img_path + clip):
                    os.makedirs(save_path)
                # else:
                #     continue
                print(clip)


                kinect_img_names = sorted(glob.glob(os.path.join(self.kinect_img_path, video_folder, clip) + '/*.jpg'))
                battery_img_names = sorted(glob.glob(os.path.join(self.battery_img_path, video_folder, clip) + '/*.jpg'))


                obj_names = sorted(glob.glob(self.kinect_box_path + clip + '/*.p'))
                all_objs = dict()
                for obj_name in obj_names:
                    with open(obj_name, 'rb') as f:
                        all_objs[obj_name] = joblib.load(f)


                with open(self.mask_cate_path + clip + '/' + clip + '.p', 'rb') as f:
                    mask_cates = joblib.load(f)


                with open(gaze_path + clip + '.p', 'rb') as f:
                    gazes = joblib.load(f)

                if self.trackers[clip].split('.')[0][5] == '2':
                    skele_file = skeleton_path + clip + '/skele1.p'
                else:
                    skele_file = skeleton_path + clip + '/skele2.p'
                with open(skele_file, 'rb') as f:
                    skeletons = joblib.load(f)

                point_names = sorted(glob.glob(self.kinect_point_path + clip + '/*.p'))

                kinect_target = []
                battery_gaze = []
                filename1 = './visualize_gaze_new_results/' + clip + '.avi'
                video_shape = (800, 480)
                out = cv2.VideoWriter(filename1, cv2.VideoWriter_fourcc('X','V','I','D'), 24, video_shape)
                count = 0
                for frame_id in range(len(kinect_img_names)):

                    kinect_img = cv2.imread(kinect_img_names[frame_id])
                    battery_img = cv2.imread(battery_img_names[frame_id])
                    print(kinect_img_names[frame_id])
                    if np.array(skeletons[frame_id]).mean() == 0:
                        kinect_target.append(None)
                        battery_gaze.append(None)
                        out.write(cv2.resize(kinect_img, video_shape))
                        continue

                    if not frame_id in gazes:
                        gaze_estimated_normal, gaze_estimated_center = self.extract_gaze(skeletons[frame_id])
                        gaze_normal = gaze_estimated_normal + gaze_estimated_center
                        gaze_center = gaze_estimated_center
                    else:
                        gaze_normal, gaze_center = gazes[frame_id]
                        # gaze_estimated_normal, gaze_estimated_center = self.extract_gaze(skeletons[frame_id])
                        # gaze_angle = self.cal_angle(gaze_estimated_normal, gaze_normal - gaze_center)
                        # if gaze_angle < 0.4:
                        #     gaze_normal = gaze_estimated_normal + gaze_center

                    gaze_normal = gaze_normal #+ np.array([-0.5, 0.1, 0])
                    # gaze_screen = self.point2screen(gaze_normal)
                    # center_screen = self.point2screen(gaze_center)
                    # to_draw = kinect_img.copy()
                    # cv2.line(to_draw, (int(gaze_screen[0]), int(gaze_screen[1])),
                    #          (int(center_screen[0]), int(center_screen[1])), (255, 0, 255), thickness=3)
                    # cv2.imshow('kinect', to_draw)
                    # cv2.waitKey(20)
                    # raw_input('Enter')

                    with open(point_names[frame_id], 'rb') as f:
                        mask_objs = joblib.load(f)
                    candidates = []
                    for obj_name in obj_names:

                        box = all_objs[obj_name][frame_id]
                        if np.mean(np.array(box)) == 0:
                            continue
                        key = './post_box_reid/' + clip + '/' + obj_name.split('/')[-1]

                        if mask_cates[key][frame_id][0] == None:
                            continue

                        mask = mask_objs[mask_cates[key][frame_id][1]][1][mask_cates[key][frame_id][2]]
                        if np.mean(np.array(mask)) == 0:
                            continue

                        mask = np.array(mask)

                        avg_col = np.array(mask).mean(axis=1)
                        obj_center = np.array(mask)[avg_col != 0, :].mean(axis=0)
                        # min_z = np.min(mask[:, 2])
                        # min_x = np.min(mask[:, 0])
                        # min_y = np.min(mask[:, 1])
                        #
                        # max_z = np.max(mask[:, 2])
                        # max_x = np.max(mask[:, 0])
                        # max_y = np.max(mask[:, 1])
                        #
                        # points_candidates = [[min_x, min_y, min_z], [min_x, min_y, max_z], [min_x, max_y, min_z],
                        #                      [min_x, max_y, max_z],
                        #                      [max_x, min_y, min_z], [max_x, min_y, min_z], [max_x, max_y, min_z],
                        #                      [max_x, max_y, max_z]]
                        #
                        # least_cos = 1
                        # for points_candidate_i in points_candidates:
                        #     dist_cos = self.cal_angle(obj_center - gaze_center, np.array(points_candidate_i) - gaze_center)
                        #     if dist_cos < least_cos and dist_cos > 0:
                        #         least_cos = dist_cos
                        #
                        # if least_cos == 1:
                        #     least_cos = 0.85

                        gaze_angle = self.cal_angle(gaze_normal - gaze_center, obj_center - gaze_center)
                        if gaze_angle >= 0.85:
                            candidates.append([obj_name, obj_center, gaze_angle])

                    center_screen = self.point2screen(gaze_center)
                    gaze_screen = self.point2screen(gaze_normal)

                    if len(candidates) == 0:
                        kinect_target.append([None, None])
                        battery_gaze.append(None)
                        to_draw_temp = kinect_img.copy()
                        cv2.line(to_draw_temp, (int(gaze_screen[0]), int(gaze_screen[1])),
                                 (int(center_screen[0]), int(center_screen[1])), (255, 0, 255), thickness=3)
                        out.write(cv2.resize(to_draw_temp, video_shape))
                        continue
                    elif len(candidates) == 1:
                        kinect_target.append(candidates[0])
                        battery_gaze.append(candidates[0][1] - gaze_center)
                    else:
                        # min_dist = 1000
                        # min_idx = None
                        #
                        # for candidate_id, candidate in enumerate(candidates):
                        #     dist_temp = np.linalg.norm(candidate[1] - gaze_center)
                        #     if dist_temp < min_dist:
                        #         min_dist = dist_temp
                        #         min_idx = candidate_id
                        # kinect_target.append(candidates[min_idx])

                        max_dist = 0
                        max_idx = None

                        for candidate_id, candidate in enumerate(candidates):
                            dist_temp = candidate[2]
                            print(candidate_id, dist_temp)
                            if dist_temp > max_dist:
                                max_dist = dist_temp
                                max_idx = candidate_id
                        kinect_target.append(candidates[max_idx])
                        battery_gaze.append(candidates[max_idx][1] - gaze_center)

                    to_draw = kinect_img.copy()


                    cv2.line(to_draw, (int(gaze_screen[0]), int(gaze_screen[1])),
                             (int(center_screen[0]), int(center_screen[1])), (255, 0, 255), thickness=3)
                    if kinect_target[frame_id][0]:
                        obj_screen = self.point2screen(kinect_target[frame_id][1])
                        cv2.line(to_draw, (int(obj_screen[0]), int(obj_screen[1])),
                                 (int(center_screen[0]), int(center_screen[1])), (255, 0, 0), thickness=3)
                        kinect_box = all_objs[kinect_target[frame_id][0]][frame_id]
                        cv2.rectangle(to_draw, (int(kinect_box[0]), int(kinect_box[1])),
                                      (int(kinect_box[0] + kinect_box[2]), int(kinect_box[1] + kinect_box[3])),
                                      (255, 0, 0), thickness=3)

                    shape = (400, 240)
                    new_img = np.hstack(
                        [cv2.resize(to_draw, shape), cv2.resize(battery_img, shape)])
                    out.write(cv2.resize(to_draw, video_shape))
                    count += 1
                    cv2.imshow("img", new_img)
                    cv2.waitKey(20)
                out.release()
                print(count)
                    # raw_input('Enter')
                #     cv2.imwrite(save_path + '/' + '{0:04}'.format(frame_id) + '.jpg', concate_img)
                #
                with open(save_path + '/' + 'target.p', 'wb') as f:
                    joblib.dump(battery_gaze, f)


    def mapping(self):
        gaze_path = './transformed_normal_new_results/'
        skeleton_path = '../../data_preprocessing2/post_skeletons/'
        video_folders = os.listdir(self.kinect_img_path)
        for video_folder in video_folders:
            clips = os.listdir(self.kinect_img_path + video_folder)
            for clip in clips:
                # if not clip == "test_boelter_9":
                #     continue
                # if not (len(clip.split('_')) > 1 and ((clip.split('_')[1] == "boelter3") or
                #         (clip.split('_')[1] == "boelter2") or (clip.split('_')[1] == "boelter"))):
                #     continue
                if not os.path.exists(gaze_path + clip + '.p'):
                    continue
                if not os.path.exists(os.path.join(self.kinect_box_path, clip)):
                    continue
                if not os.path.exists(self.kinect_point_path + clip):
                    continue
                if not os.path.exists(self.kinect_point_path + clip):
                    continue

                save_path = self.save_img_path + clip
                if not os.path.exists(self.save_img_path + clip):
                    os.makedirs(save_path)
                # else:
                #     continue
                print(clip)


                kinect_img_names = sorted(glob.glob(os.path.join(self.kinect_img_path, video_folder, clip) + '/*.jpg'))
                battery_img_names = sorted(glob.glob(os.path.join(self.battery_img_path, video_folder, clip) + '/*.jpg'))


                obj_names = sorted(glob.glob(self.kinect_box_path + clip + '/*.p'))
                all_objs = dict()
                for obj_name in obj_names:
                    with open(obj_name, 'rb') as f:
                        all_objs[obj_name] = joblib.load(f)


                with open(self.mask_cate_path + clip + '/' + clip + '.p', 'rb') as f:
                    mask_cates = joblib.load(f)


                with open(gaze_path + clip + '.p', 'rb') as f:
                    gazes = joblib.load(f)

                if self.trackers[clip].split('.')[0][5] == '2':
                    skele_file = skeleton_path + clip + '/skele1.p'
                else:
                    skele_file = skeleton_path + clip + '/skele2.p'
                with open(skele_file, 'rb') as f:
                    skeletons = joblib.load(f)

                point_names = sorted(glob.glob(self.kinect_point_path + clip + '/*.p'))

                kinect_target = []
                filename1 = './visualize_gaze_new_results/' + clip + '.avi'
                video_shape = (800, 480)
                out = cv2.VideoWriter(filename1, cv2.VideoWriter_fourcc('X','V','I','D'), 24, video_shape)
                count = 0
                for frame_id in range(len(kinect_img_names)):

                    kinect_img = cv2.imread(kinect_img_names[frame_id])
                    battery_img = cv2.imread(battery_img_names[frame_id])
                    print(kinect_img_names[frame_id])
                    if np.array(skeletons[frame_id]).mean() == 0:
                        kinect_target.append(None)
                        out.write(cv2.resize(kinect_img, video_shape))
                        continue

                    if not frame_id in gazes:
                        gaze_estimated_normal, gaze_estimated_center = self.extract_gaze(skeletons[frame_id])
                        gaze_normal = gaze_estimated_normal + gaze_estimated_center
                        gaze_center = gaze_estimated_center
                    else:
                        gaze_normal, gaze_center = gazes[frame_id]
                        gaze_estimated_normal, gaze_estimated_center = self.extract_gaze(skeletons[frame_id])
                        gaze_angle = self.cal_angle(gaze_estimated_normal, gaze_normal - gaze_center)
                        if gaze_angle < 0.4:
                            gaze_normal = gaze_estimated_normal + gaze_center

                    gaze_normal = gaze_normal #+ np.array([-0.5, 0.1, 0])
                    # gaze_screen = self.point2screen(gaze_normal)
                    # center_screen = self.point2screen(gaze_center)
                    # to_draw = kinect_img.copy()
                    # cv2.line(to_draw, (int(gaze_screen[0]), int(gaze_screen[1])),
                    #          (int(center_screen[0]), int(center_screen[1])), (255, 0, 255), thickness=3)
                    # cv2.imshow('kinect', to_draw)
                    # cv2.waitKey(20)
                    # raw_input('Enter')

                    with open(point_names[frame_id], 'rb') as f:
                        mask_objs = joblib.load(f)
                    candidates = []
                    for obj_name in obj_names:

                        box = all_objs[obj_name][frame_id]
                        if np.mean(np.array(box)) == 0:
                            continue
                        key = './post_box_reid/' + clip + '/' + obj_name.split('/')[-1]

                        if mask_cates[key][frame_id][0] == None:
                            continue

                        mask = mask_objs[mask_cates[key][frame_id][1]][1][mask_cates[key][frame_id][2]]
                        if np.mean(np.array(mask)) == 0:
                            continue

                        avg_col = np.array(mask).mean(axis=1)
                        obj_center = np.array(mask)[avg_col != 0, :].mean(axis=0)
                        gaze_angle = self.cal_angle(gaze_normal - gaze_center, obj_center - gaze_center)
                        # center_screen = self.point2screen(gaze_center)
                        # to_draw = kinect_img.copy()
                        # obj_screen = self.point2screen(obj_center)
                        # gaze_screen = self.point2screen(gaze_normal + gaze_center)
                        # cv2.line(to_draw, (int(obj_screen[0]), int(obj_screen[1])),
                        #                       (int(center_screen[0]), int(center_screen[1])), (255, 0, 0), thickness=3)
                        # cv2.line(to_draw, (int(gaze_screen[0]), int(gaze_screen[1])),
                        #          (int(center_screen[0]), int(center_screen[1])), (255, 0, 255), thickness=3)
                        # cv2.rectangle(to_draw, (int(box[0]), int(box[1])),
                        #               (int(box[0] + box[2]), int(box[1] + box[3])),
                        #               (255, 0, 0), thickness=3)
                        # cv2.imshow('kinect', to_draw)
                        # cv2.imshow('battery', cv2.resize(battery_img, (400, 240)))
                        # cv2.waitKey(20)
                        # print(gaze_angle)
                        # raw_input('Enter')
                        if gaze_angle > 0.85:
                            candidates.append([obj_name, obj_center, gaze_angle])

                    center_screen = self.point2screen(gaze_center)
                    gaze_screen = self.point2screen(gaze_normal)

                    if len(candidates) == 0:
                        kinect_target.append([None, None])
                        to_draw_temp = kinect_img.copy()
                        cv2.line(to_draw_temp, (int(gaze_screen[0]), int(gaze_screen[1])),
                                 (int(center_screen[0]), int(center_screen[1])), (255, 0, 255), thickness=3)
                        out.write(cv2.resize(to_draw_temp, video_shape))
                        continue
                    elif len(candidates) == 1:
                        kinect_target.append(candidates[0])
                    else:
                        # min_dist = 1000
                        # min_idx = None
                        #
                        # for candidate_id, candidate in enumerate(candidates):
                        #     dist_temp = np.linalg.norm(candidate[1] - gaze_center)
                        #     if dist_temp < min_dist:
                        #         min_dist = dist_temp
                        #         min_idx = candidate_id
                        # kinect_target.append(candidates[min_idx])

                        max_dist = 0
                        max_idx = None

                        for candidate_id, candidate in enumerate(candidates):
                            dist_temp = candidate[2]
                            if dist_temp > max_dist:
                                max_dist = dist_temp
                                max_idx = candidate_id
                        kinect_target.append(candidates[max_idx])

                    to_draw = kinect_img.copy()


                    cv2.line(to_draw, (int(gaze_screen[0]), int(gaze_screen[1])),
                             (int(center_screen[0]), int(center_screen[1])), (255, 0, 255), thickness=3)
                    if kinect_target[frame_id][0]:
                        obj_screen = self.point2screen(kinect_target[frame_id][1])
                        cv2.line(to_draw, (int(obj_screen[0]), int(obj_screen[1])),
                                 (int(center_screen[0]), int(center_screen[1])), (255, 0, 0), thickness=3)
                        kinect_box = all_objs[kinect_target[frame_id][0]][frame_id]
                        cv2.rectangle(to_draw, (int(kinect_box[0]), int(kinect_box[1])),
                                      (int(kinect_box[0] + kinect_box[2]), int(kinect_box[1] + kinect_box[3])),
                                      (255, 0, 0), thickness=3)

                    shape = (400, 240)
                    new_img = np.hstack(
                        [cv2.resize(to_draw, shape), cv2.resize(battery_img, shape)])
                    out.write(cv2.resize(to_draw, video_shape))
                    count += 1
                    cv2.imshow("img", new_img)
                    cv2.waitKey(20)
                out.release()
                print(count)
                    # raw_input('Enter')
                #     cv2.imwrite(save_path + '/' + '{0:04}'.format(frame_id) + '.jpg', concate_img)
                #
                # with open(save_path + '/' + 'target.p', 'wb') as f:
                #     joblib.dump(kinect_target, f)

    def pose_reformat(self):
        save_prefix = '../../data_preprocessing2/gaze_training/'

        clips = os.listdir(self.skeleton_path)
        for clip in clips:
            save_path = save_prefix + clip
            if not os.path.exists(save_path):
                os.makedirs(save_path)
            print(clip)
            if self.trackers[clip].split('.')[0][5] == '2':
                skele_file = self.skeleton_path + '/' + clip + '/skele1.p'
            else:
                skele_file = self.skeleton_path + '/' + clip + '/skele2.p'
            with open(skele_file, 'rb') as f:
                skeletons = joblib.load(f)

            with open(save_path + '/inference.p', 'wb') as f:
                joblib.dump(skeletons, f)

    def merge2gaze(self):
        save_prefix = '../../data_preprocessing2/merge2gaze/'
        skeleton_path = '../../data_preprocessing2/post_skeletons/'
        gaze_path = '../../data_preprocessing2/view_battery_mapping_record_temp/'
        video_folders = os.listdir(self.kinect_img_path)
        for video_folder in video_folders:
            clips = os.listdir(self.kinect_img_path + video_folder)
            for clip in clips:
                save_path = save_prefix + clip
                if not os.path.exists(save_path + clip):
                    os.makedirs(save_path)
                print(clip)

                if self.trackers[clip].split('.')[0][5] == '2':
                    skele_file = skeleton_path + clip + '/skele1.p'
                else:
                    skele_file = skeleton_path + clip + '/skele2.p'
                with open(skele_file, 'rb') as f:
                    skeletons = joblib.load(f)

                with open(gaze_path + clip + '/target.p', 'rb') as f:
                    gazes = joblib.load(f)

                merged_gazes = []
                for frame_id in range(len(skeletons)):
                    if not np.mean(np.array(skeletons[frame_id])) == 0:
                        estimate_gaze = self.extract_gaze(skeletons[frame_id])
                    else:
                        merged_gazes.append(None)
                        continue
                    if not (gazes[frame_id] is None):
                        merged_gazes.append([gazes[frame_id], estimate_gaze[1]])
                    else:
                        merged_gazes.append(estimate_gaze)

                assert len(merged_gazes) == len(skeletons)
                with open(save_path + '/target.p', 'wb') as f:
                    joblib.dump(merged_gazes, f)





if __name__ == "__main__":
    view_mapper = ViewMap()
    # view_mapper.mapping_with_3d_box()
    view_mapper.merge2gaze()