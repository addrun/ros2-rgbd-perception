# Position and undirected principal axis are in the TargetArray optical frame.
string label
float32 confidence
# Pixel coordinates in the original colour image: x1,y1,x2,y2.
float32[4] bbox_xyxy
geometry_msgs/Point position
# PCA axis is an unsigned line, not an object heading or full orientation.
geometry_msgs/Vector3 principal_axis
bool axis_valid
