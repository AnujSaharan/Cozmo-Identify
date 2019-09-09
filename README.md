# Cozmo Identify
Cozmo Identify is a modified version of the Cozmo Voice Commands Framework to add voice activated image recognition to Anki's Cozmo Robot. The current image recognition algortihm is trained on ImageNet's Large Scale Visual Recognition Challenge (ILSVRC) Database from 2012.

# How to Use
Enable Cozmo's SDK mode from the mobile app and then run `python cvc.py` from the connected computer to execute. You can ask Cozmo to do any number of instructions on the screen seperated by the keyword `THEN`. The `Identify` keyword triggers the image classification algorithm and Cozmo takes a photo of whatever's in front of him. The algorithm then identifies the object in the background and then Cozmo says what he thinks he's looking at out loud. 

An example of what you can say to Cozmo -

`Cozmo Drive Forward for 3 seconds, THEN turn right 73 degrees, THEN identify`
