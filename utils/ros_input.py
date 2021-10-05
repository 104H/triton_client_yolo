import rospy
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import os
import numpy as np

from tritonclient.grpc import service_pb2, service_pb2_grpc
import tritonclient.grpc.model_config_pb2 as mc
from utils.postprocess import extract_boxes_triton

class RealSenseNode(object):
    def __init__(self, grpc_stub, input_name, output_name, FLAGS, dtype, c, h, w):
        # Params
        self.image = None
        self.br = CvBridge()
        self.stub = grpc_stub
        self.FLAGS = FLAGS
        self.class_names = self.load_class_names()

        self.input = service_pb2.ModelInferRequest().InferInputTensor()
        self.input.name = input_name
        self.input.datatype = dtype

        self.request = service_pb2.ModelInferRequest()
        self.request.model_name = FLAGS.model_name
        self.request.model_version = FLAGS.model_version

        self.output0 = service_pb2.ModelInferRequest().InferRequestedOutputTensor()
        self.output0.name = output_name[0]
        self.output1 = service_pb2.ModelInferRequest().InferRequestedOutputTensor()
        self.output1.name = output_name[1]
        self.request.outputs.extend([self.output0, self.output1])

        self.detection = rospy.Publisher('/camera/color/detection', Image, queue_size=10)
        # self.input.shape.extend([c, h, w])

        if format == mc.ModelInput.FORMAT_NHWC:
            self.input.shape.extend([h, w, c])
        else:
            self.input.shape.extend([c, h, w])
        # Node cycle rate (in Hz).
        # self.loop_rate = rospy.Rate(1)

        # Publishers
        # self.pub = rospy.Publisher('imagetimer', Image,queue_size=10)

        # Subscribers
        rospy.init_node("realsense_infer")
        rospy.Subscriber("/camera/color/image_raw", Image, self.callback)
        rospy.spin()


    def callback(self, msg):
        # rospy.loginfo('Image received...')
        cv_image = self.br.imgmsg_to_cv2(msg, desired_encoding='rgb8')
        # rospy.loginfo('Image size: {} {}'.format(cv_image.shape[0], cv_image.shape[1]))
        # cv2.imshow('test', cv2.cvtColor(cv_image, cv2.COLOR_RGB2BGR))
        # cv2.waitKey()
        self.image = self.image_adjust(cv_image)
        if self.image is not None:
            self.request.ClearField("inputs")
            self.request.ClearField("raw_input_contents")
            self.request.inputs.extend([self.input])
            self.request.raw_input_contents.extend([self.image.tobytes()])
            self.response = self.stub.ModelInfer(self.request)
            self.prediction = extract_boxes_triton(self.response)

            for object in self.prediction[0]:  # predictions array has the order [x1,y1, x2,y2, confidence, confidence, class ID]
                box = np.array(object[0:4], dtype=np.float32) * 512
                cv2.rectangle(cv_image,
                              pt1=(int(box[0]), int(box[1])),
                              pt2=(int(box[2]), int(box[3])),
                              color=(0, 255, 0),
                              thickness=1)
                cv2.putText(cv_image,
                            '{:.2f} {}'.format(object[-2], self.class_names[int(object[-1])]),
                            org=(int(box[0]), int(box[1])),
                            fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                            fontScale=0.5,
                            thickness=2,
                            color=(0, 255, 0))
            self.msg_frame = self.br.cv2_to_imgmsg(cv_image, encoding="rgb8")
            self.msg_frame.header.stamp = rospy.Time.now()
            self.detection.publish(self.msg_frame)
            # cv2.imshow('Prediction', cv2.cvtColor(cv_image, cv2.COLOR_RGB2BGR))
            # cv2.waitKey()




    def start(self):
        # rospy.loginfo("Timing images")
        #rospy.spin()
        while not rospy.is_shutdown():
            # rospy.loginfo('publishing image')
            #br = CvBridge()

                print('hold')
            # self.loop_rate.sleep()

    def load_class_names(self, namesfile='./data/coco.names'):
        class_names = []
        with open(namesfile, 'r') as fp:
            lines = fp.readlines()
        for line in lines:
            line = line.rstrip()
            class_names.append(line)
        return class_names

    def image_adjust(self, cv_image):
        # pad = np.zeros((16, 1280, 3), dtype=np.uint8)
        # cv_image = np.concatenate((cv_image, pad), axis=0)
        # orig = cv_image.copy()
        cv_image = np.transpose(cv_image, (2, 0, 1)).astype(np.float32)
        cv_image = np.expand_dims(cv_image, axis=0)
        cv_image /= 255.0

        return cv_image

if __name__ == '__main__':
    rospy.init_node("imagetimer111", anonymous=True)
    my_node = RealSenseNode()
    my_node.start()