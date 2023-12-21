import datetime
from io import BytesIO
import numpy as np
from PIL import Image
import requests
import torch

from func import *


def get_area_detect(img, points):
    # points = points.reshape((-1, 1, 2))
    mask = np.zeros(img.shape[:2], np.uint8)
    cv2.drawContours(mask, [points], -1, (255, 255, 255), -1, cv2.LINE_AA)
    dts = cv2.bitwise_and(img, img, mask=mask)
    return dts


def auto_lane(img, lane=None, center_point=None, roi=None, threshold=1000):
    final = True
    check_ss = {}
    ss = 0
    while final:
        check = center_point[0]
        count = 1
        check_1 = []
        check_1.append(check)
        for point in center_point:
            if abs(check[0] - point[0]) < threshold and check[1] < point[1]:
                cv2.circle(img,tuple(check),10,(0,0,255),-1)
                # print("Point check org :",check)
                count += 1
                check = point
                # print("Point swap :",check)
                # print('Found {} point '.format(count))
                check_1.append(point)

        # print("check 1 :",check_1)
        copy_list = check_1.copy()
        check_ss[str(ss)] = copy_list
        # print("check_ss",check_ss)
        # print("check_ss",check_1)
        for p in check_1:
            center_point.remove(p)
        check_1.clear()
        center_point = list(center_point)
        # print('center point :' ,center_point)
        # print(len(center_point))
        ss += 1
        if len(center_point) < 1:
            final = False

    """
    Trường hợp detect thiếu lane  
    """
    list_lane = None
    print("check_ss len inside yolo:", len(check_ss))
    if len(check_ss) < lane:
        print("không khớp với đàu vào ")
        # x1,y1,x2,y2=roi
        # y_center=int((y2+y1)/2)
        list_sort_y = sorted(roi, key=lambda x: x[1])
        A = list_sort_y[0]
        B = list_sort_y[1]
        C = list_sort_y[2]
        D = list_sort_y[3]
        x_distance_1 = abs(A[0] - B[0])
        y_min = min(A[1], B[1])
        x_distance_2 = abs(C[0] - D[0])
        y_max = max(C[1], D[1])
        list_lane = []
        for i in range(1, lane):
            x1 = int(x_distance_1 * i / lane) + min(A[0], B[0])
            y1 = y_min
            x2 = int(x_distance_2 * i / lane) + min(C[0], D[0])
            y2 = y_max
            list_lane.append([[x1, y1], [x2, y2]])
            print(list_lane)
        # logger.info("list lane :{}".format(list_lane))
    if len(check_ss) == lane:
        print("okkk")
    return check_ss, list_lane


class Detector(object):
    def __init__(self, link) -> None:
        """
        Args:
            roi_area List[List]: [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
        """
        
        self.link = link
    
    def convert_frame(self, frame):
        current_time = int(datetime.datetime.now().timestamp())

        map_time = list(map(int, str(current_time)))
        remainder = frame.shape[0] % 10
        quotient = frame.shape[0] // 10

        output = quotient * map_time
        output.extend(map_time[:remainder])

        add_array = np.array(output)
        add_array = add_array.reshape(1, -1, 1)

        empty_arr = np.zeros_like(frame[:1])

        empty_arr[:, : add_array.shape[1]] = add_array

        # Create a new image with the last row as add_array
        modified_image = np.concatenate((frame, empty_arr), axis=0)
        # byte_array = modified_image.tobytes(order="C")

        send_image = Image.fromarray(modified_image)
        image2bytes = BytesIO()
        send_image.save(image2bytes, format="PNG")
        image2bytes.seek(0)
        return image2bytes.read()

    def detect(self, image):
        image_data = self.convert_frame(image)

        vehicle_URL = self.link
        vehicle_response = requests.post(vehicle_URL, data=image_data)
        
        if vehicle_response.status_code == 200:
            vehicle_data = vehicle_response.json()
            label = vehicle_data[0]["label"]
            bbox = vehicle_data[0]["bbox"]
            
        return bbox, label

    def auto_lane(self, img: np.ndarray, roi_area: list, num_lane: int):
        h, w = img.shape[:2]
        lst_lane = []
        lst_check_ss = []
        if len(roi_area) > 0:
            pts = np.array(roi_area, dtype=np.float32) * np.array([w, h])
            pts = pts.astype(np.int32)
            print(pts)
            # crop frame
            img = get_area_detect(img, pts)
            # cv2.polylines(img, [pts], True, (0, 0, 142), 3)
            bbox, label = self.detect(img)
            # print(label)
            center_point = []
            # print(np.sort(bbox))
            # auto_lane(lane=0,bbox=bbox)
            if len(bbox) > 0:
                for box, l in zip(bbox, label):
                    box = list(map(int, box))
                    if int(l) == 0:
                        mid_point = [
                            int((box[0] + box[2]) / 2),
                            int((box[1] + box[3]) / 2),
                        ]
                        center_point.append(mid_point)

                        # img = cv2.rectangle(
                        #     img, (box[0], box[1]), (box[2], box[3]), (255, 0, 0), 1
                        # )
                center_point = sorted(center_point)
                check_ss, list_lane = auto_lane(
                    img,
                    center_point=center_point,
                    lane=num_lane,
                    threshold=500,
                    roi=pts.astype(np.int32).tolist(),
                )
                if list_lane is None:
                    list_lane = []

                for p in list_lane:
                    lst_lane.append(
                        [p[0][0] / w, p[0][1] / h, p[1][0] / w, p[1][1] / h]
                    )
                    # cv2.line(img, tuple(p[0]), tuple(p[1]), (0, 125, 47), 2)

                for key in check_ss.keys():
                    for index, item in enumerate(check_ss[key]):
                        if index == len(check_ss[key]) - 1:
                            break
                        lst_check_ss.append(
                            [
                                item[0] / w,
                                item[1] / h,
                                check_ss[key][index + 1][0] / w,
                                check_ss[key][index + 1][1] / h,
                            ]
                        )
                    # cv2.line(
                    #     img,
                    #     tuple(item),
                    #     tuple(check_ss[key][index + 1]),
                    #     [127, 255, 0],
                    #     2,
                    # )
        # print("results :", check_ss)
        return lst_lane, lst_check_ss
