import numpy as np
from scipy.spatial import distance as dist

class TrackAbnormal(object):
    def __init__(self, max_dist=10):
        self.max_dist = max_dist
        self.prev_objects = []

    def update(self, current_objects) -> bool:
        if len(current_objects) == 0:
            return True
        
        inputCentroid = np.zeros((len(current_objects), 2))

        for i, (x, y, w, h) in enumerate(current_objects):
            cx = x + w//2
            cy= y + h//2
            inputCentroid[i] = (cx, cy)

        if len(self.prev_objects) == 0:
            for i in range(len(inputCentroid)):
                self.prev_objects.append(inputCentroid[i])
            return False
        else:
            # matrix len(self.prev_objects) x len(inputCentroid)
            pair_dists = dist.cdist(np.array(self.prev_objects), inputCentroid)
            
            # find closest dist
            closest_to_prev = pair_dists.min(axis=1)
            
            # compare to threshold
            state = np.any(closest_to_prev < self.max_dist)
            
            self.prev_objects.clear()
            for i in range(len(inputCentroid)):
                self.prev_objects.append(inputCentroid[i])
            
            return state

if __name__ == '__main__':
    # objectCentroids = np.random.uniform(size=(2, 2))
    
    track_abnormal = TrackAbnormal(max_dist=0.6)
    
    i = 1
    
    while True:
        centroids = np.random.uniform(size=(i, 4)).tolist()
        state = track_abnormal.update(centroids)
        i += 1
        if i == 5: break
    
