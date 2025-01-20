import cv2
import numpy as np

def order_points(pts):
    """Order points as top-left, top-right, bottom-right, bottom-left."""
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    return rect

cap = cv2.VideoCapture('input_video2.mp4')
screen_recording = cv2.VideoCapture('screen_recording2.mp4')

lower_green = np.array([35, 35, 40])  # Lower bound for green
upper_green = np.array([85, 255, 255])  # Upper bound for green

fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter('output_video.mp4', fourcc, 30.0, (int(cap.get(3)), int(cap.get(4))))

prev_pts = None
last_good_matrix = None
alpha = 0.7

frame_count = 0

while cap.isOpened() and screen_recording.isOpened():
    ret, frame = cap.read()
    ret_sr, sr_frame = screen_recording.read()
    if not ret or not ret_sr:
        break

    frame_count += 1

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, lower_green, upper_green)
    mask = cv2.dilate(mask, np.ones((5, 5), np.uint8), iterations=2)

    cv2.imshow("Green Mask", mask)  # Debugging mask visualization

    contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    print(f"Frame {frame_count}: Number of contours detected: {len(contours)}")

    contour_found = False

    if contours:
        max_contour = max(contours, key=cv2.contourArea)
        if cv2.contourArea(max_contour) > 500:  # Check for minimum area
            epsilon = 0.01 * cv2.arcLength(max_contour, True)
            approx = cv2.approxPolyDP(max_contour, epsilon, True)
            print(f"Frame {frame_count}: Approx points: {len(approx)}")

            if len(approx) >= 4:  # Ensure we have at least 4 points for a rectangle
                sorted_pts = np.array(sorted(approx[:, 0, :], key=lambda x: (x[1], x[0])), dtype='float32')
                if len(sorted_pts) == 4:  # Ensure exactly 4 points
                    smoothed_pts = order_points(sorted_pts)
                    contour_found = True

                    if prev_pts is not None:
                        delta = np.linalg.norm(smoothed_pts - prev_pts, axis=1)
                        if np.all(delta < 50):  # Ensure changes are within a reasonable threshold
                            smoothed_pts = alpha * prev_pts + (1 - alpha) * smoothed_pts
                        else:
                            smoothed_pts = prev_pts

                    prev_pts = smoothed_pts

                    h, w, _ = sr_frame.shape
                    dst_pts = np.array([[0, 0], [w, 0], [w, h], [0, h]], dtype='float32')
                    last_good_matrix = cv2.getPerspectiveTransform(dst_pts, smoothed_pts)

    if last_good_matrix is not None:
        h, w, _ = sr_frame.shape
        dst_pts = np.array([[0, 0], [w, 0], [w, h], [0, h]], dtype='float32')
        warped_sr_frame = cv2.warpPerspective(sr_frame, last_good_matrix, (frame.shape[1], frame.shape[0]))

        green_screen_mask = np.zeros_like(frame, dtype=np.uint8)
        if contour_found:
            cv2.fillPoly(green_screen_mask, [smoothed_pts.astype(int)], (255, 255, 255))
        else:
            src_pts = cv2.perspectiveTransform(dst_pts.reshape(-1, 1, 2), last_good_matrix).reshape(-1, 2).astype(int)
            cv2.fillPoly(green_screen_mask, [src_pts], (255, 255, 255))

        green_screen_mask_inv = cv2.bitwise_not(green_screen_mask)
        background = cv2.bitwise_and(frame, green_screen_mask_inv)
        overlayed_frame = cv2.add(background, warped_sr_frame)
        frame = overlayed_frame

    out.write(frame)
    cv2.imshow("Frame", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
screen_recording.release()
out.release()
cv2.destroyAllWindows()