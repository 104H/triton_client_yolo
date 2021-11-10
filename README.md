# YOLOv4 gRPC client for Triton server 

This repo is targeted to reproduce a YOLOv4 onnx model export to triton server based on this repo (https://github.com/Tianxiaomo/pytorch-YOLOv4) and gRPC Image client example provided by TRITON here (https://github.com/triton-inference-server/client/blob/main/src/python/examples/grpc_image_client.py). 

## How to use the Deployment Script
The deployment script is designed to be self sufficient in deploying models in onnx. It prepares a model given the parameters and sends it to the remote triton server.

To use the file, open it and enter the correct values for the variables at the top provided and run the script.

## Inferences on ROS with Batching

The `main.py` script runs inferences on ROS be default and an argument need not be specified. In order to run inferences in input from a RealSense Camera, run a `roscore` and the main.py script with the required batch size in the `-b` argument.

