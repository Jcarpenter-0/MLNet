import subprocess
import time

# Network

# Example MahiMahi


# Learners

# Example Basic RL - the run script in for the learner, 0 or 1 for training or not, port
learners = subprocess.Popen(['./learners/cc-rl/run.py','0','8080'])

# Start Apps

# Example Chromium targeting websites
chromium = subprocess.Popen(['chromium-browser','www.google.com'])

time.sleep(3)

chromium.kill()
chromium.wait()

print('Closed')