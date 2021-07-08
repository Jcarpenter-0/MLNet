
# Troubleshooting
* Illegal operation (core dumped)
Check tensorflow, it may be running a new version on an older cpu
* Shape input issues? Try ensuring that keras and tensorflow are updated properly

# Tips for doing Machine Learning
* Use only numeric data, text will not translate properly, use a mapping to either numeric values or binary columns to address
* Consider using data that is "relevant" to achieving an end, this is a heuristic
* Predictions returning NAN? Try adjusting the learning rate, optimizer, or examine your data.