import cv2


video = cv2.VideoCapture("")

while True:
    check, frame = video.read()

    cv2.imshow("frame do cel", frame)
    key= cv2.waitKey(1)

    if key==ord("q"):
        break

video.release()
cv2.destroyAllWindows()