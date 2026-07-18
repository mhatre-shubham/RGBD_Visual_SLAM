#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/image.hpp>
#include <cv_bridge/cv_bridge.h>
#include <message_filters/subscriber.h>
#include <message_filters/sync_policies/approximate_time.h>
#include <message_filters/synchronizer.h>
#include <opencv2/opencv.hpp>

#include <filesystem>
#include <fstream>
#include <iomanip>
#include <sstream>

// SLAM RGB-D synchronization and dataset recording node
class SlamRgbdSync : public rclcpp::Node
{
public:
    SlamRgbdSync() : Node("slam_rgbd_sync_node")
    {
        rgb_sub_.subscribe(this, "/camera/image_raw");
        depth_sub_.subscribe(this, "/depth/image_raw");

        // Sync RGB and depth frames (approximate timing for AI depth)
        sync_.reset(new Sync(SyncPolicy(20), rgb_sub_, depth_sub_));

        // Register synchronized callback
        sync_->registerCallback(
            std::bind(&SlamRgbdSync::callback, this,
                      std::placeholders::_1,
                      std::placeholders::_2));

        output_path_ = "/home/mhatre/dataset_rgbd";

        // Create dataset folders
        std::filesystem::create_directories(output_path_ + "/rgb");
        std::filesystem::create_directories(output_path_ + "/depth");

        // Open association files
        rgb_file_.open(output_path_ + "/rgb.txt", std::ios::out | std::ios::trunc);
        depth_file_.open(output_path_ + "/depth.txt", std::ios::out | std::ios::trunc);

        frame_count_ = 0;

        RCLCPP_INFO(this->get_logger(), "slam_rgbd_sync node started");
    }

    ~SlamRgbdSync()
    {
        rgb_file_.close();
        depth_file_.close();
    }

private:
    message_filters::Subscriber<sensor_msgs::msg::Image> rgb_sub_;
    message_filters::Subscriber<sensor_msgs::msg::Image> depth_sub_;

    using SyncPolicy = message_filters::sync_policies::ApproximateTime<
        sensor_msgs::msg::Image,
        sensor_msgs::msg::Image>;

    using Sync = message_filters::Synchronizer<SyncPolicy>;
    std::shared_ptr<Sync> sync_;

    // Dataset storage
    std::string output_path_;
    std::ofstream rgb_file_;
    std::ofstream depth_file_;
    int frame_count_;

    void callback(
        const sensor_msgs::msg::Image::ConstSharedPtr &rgb_msg,
        const sensor_msgs::msg::Image::ConstSharedPtr &depth_msg)
    {
        cv::Mat rgb = cv_bridge::toCvShare(rgb_msg, "bgr8")->image;

        // Convert depth image (metric float32)
        cv::Mat depth = cv_bridge::toCvShare(depth_msg, "32FC1")->image;

        // Remove invalid values
        cv::patchNaNs(depth, 0);

        double timestamp = rgb_msg->header.stamp.sec + rgb_msg->header.stamp.nanosec * 1e-9;

        std::ostringstream ss;
        ss << std::fixed << std::setprecision(6) << timestamp;
        std::string ts = ss.str();

        // Relative file paths
        std::string rgb_rel = "rgb/" + ts + ".png";
        std::string depth_rel = "depth/" + ts + ".png";

        // Absolute paths
        std::string rgb_full = output_path_ + "/" + rgb_rel;
        std::string depth_full = output_path_ + "/" + depth_rel;

        cv::imwrite(rgb_full, rgb);

        // Convert depth to ORB-SLAM compatible format
        cv::Mat depth_16u;
        depth.convertTo(depth_16u, CV_16U, 5000.0);

        cv::imwrite(depth_full, depth_16u);

        // Write associations
        rgb_file_ << ts << " " << rgb_rel << "\n";
        depth_file_ << ts << " " << depth_rel << "\n";

        frame_count_++;

        if (frame_count_ % 50 == 0)
            RCLCPP_INFO(this->get_logger(), "Frames saved: %d", frame_count_);
    }
};

int main(int argc, char **argv)
{
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<SlamRgbdSync>());
    rclcpp::shutdown();
    return 0;
}