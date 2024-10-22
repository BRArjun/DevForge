#include <opencv2/opencv.hpp>
#include <iostream>

int main() {
    std::cout << "OpenCV version: " << CV_VERSION << std::endl;
    cv::Mat image(100, 100, CV_8UC3, cv::Scalar(0, 255, 0));
    std::cout << "Created a " << image.rows << "x" << image.cols << " green image" << std::endl;
    return 0;
}
