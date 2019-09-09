'''
##Customization
You can add as many new commands as you like:
just prefix their function names with the language they are spoken in, *i.e. "it_" for italian, "en_" for english, so for instance you'll create the method "en_smile()" and the voice command you'll have to say will be "smile"*.
Some commands support one argument, for example: if you say *"drive for 10 seconds"*, 10 will be passed to the method *"en_drive"*, any other words will be ignored.
'''
import asyncio
import time
from threading import Timer

import cozmo
from cozmo.util import distance_mm, speed_mmps, degrees
from termcolor import colored, cprint
from subprocess import Popen, PIPE

speed = 80
words_to_numbers = ['one', 'uno', 'i', 'un']

def extract_float(cmd_args, index=0):
    if len(cmd_args) > index:
        try:
            float_val = float(cmd_args[index])
            return float_val
        except ValueError:
            pass
    return None


def extract_next_float(cmd_args, index=0):
    #Loop through arguments to find first float and position!

    for i in range(index, len(cmd_args)):
        try:
            float_val = float(cmd_args[i])
            return float_val#, i #can return position if needed
        except ValueError:
            if "zero" in cmd_args:
                return 0
            #check if cmd_args contains some number as letters and set them accordingly
            if len(set(cmd_args).intersection(words_to_numbers)) != 0:
                return 1
    return None#, None

def turn_off_cube_lights(cubes):
    for cube in cubes:
        cube.set_lights_off()

class VoiceCommands():

    def __init__(self, robot, log=False):
        self.robot = robot
        self.lang_data = None
        self.log = log

    ##### NOT A VOICE COMMAND FOR NOW #####
    def check_charger(self, robot:cozmo.robot.Robot, distance=150, speed=100):
        if robot.is_on_charger:
            if self.log:
                print("I am on the charger. Driving off the charger...")
            robot.drive_off_charger_contacts().wait_for_completed()
            robot.drive_straight(distance_mm(distance), speed_mmps(speed)).wait_for_completed()
            robot.move_lift(-8)

    ###### BLOCKS ######
    def blocks(self, robot:cozmo.robot.Robot = None, cmd_args = None):

        print("looking for my blocks for 1 minute...")
        lookaround = robot.start_behavior(cozmo.behavior.BehaviorTypes.LookAroundInPlace)

        cubes = robot.world.wait_until_observe_num_objects(num=3, object_type=cozmo.objects.LightCube, timeout=60)

        print("found %s cube(s)" % len(cubes))

        lookaround.stop()

        for cube in cubes:
            cube.set_lights(cozmo.lights.green_light.flash())

        Timer(5, turn_off_cube_lights, [cubes]).start()

        if len(cubes) == 0:
            robot.play_anim_trigger(cozmo.anim.Triggers.MajorFail).wait_for_completed()
        elif len(cubes) == 1:
            robot.run_timed_behavior(cozmo.behavior.BehaviorTypes.RollBlock, active_time=60)
        else:
            robot.run_timed_behavior(cozmo.behavior.BehaviorTypes.StackBlocks, active_time=120)
        return
###### DANCE ######

    def dance(self, robot:cozmo.robot.Robot = None, cmd_args = None):

        print("dancing...")
        robot.play_anim("anim_speedtap_wingame_intensity02_01").wait_for_completed()
        return

###### LOOK ######

    def look(self, robot:cozmo.robot.Robot = None, cmd_args = None):

        any_face = None
        print("Looking for a face...")
        robot.set_head_angle(cozmo.robot.MAX_HEAD_ANGLE).wait_for_completed()
        robot.move_lift(-3)
        look_around = robot.start_behavior(cozmo.behavior.BehaviorTypes.FindFaces)

        try:
            any_face = robot.world.wait_for_observed_face(timeout=30)

        except asyncio.TimeoutError:
            print("Didn't find anyone :-(")

        finally:
            # whether we find it or not, we want to stop the behavior
            look_around.stop()

        if any_face is None:
            robot.play_anim_trigger(cozmo.anim.Triggers.MajorFail).wait_for_completed()
            return

        print("Yay, found someone!")

        anim = robot.play_anim_trigger(cozmo.anim.Triggers.LookInPlaceForFacesBodyPause)
        anim.wait_for_completed()
        return

###### FOLLOW ######

    def follow(self, robot:cozmo.robot.Robot = None, cmd_args = None):

        print("Following your face - any face...")
        # Move lift down and tilt the head up
        robot.move_lift(-3)
        robot.set_head_angle(cozmo.robot.MAX_HEAD_ANGLE).wait_for_completed()

        face_to_follow = None

        while True:
            turn_action = None
            if face_to_follow:
            # start turning towards the face
                turn_action = robot.turn_towards_face(face_to_follow)

            if not (face_to_follow and face_to_follow.is_visible):
                # find a visible face, timeout if nothing found after a short while
                try:
                    face_to_follow = robot.world.wait_for_observed_face(timeout=30)
                except asyncio.TimeoutError:
                    return "Didn't find a face - exiting!"

            if turn_action:
                # Complete the turn action if one was in progress
                turn_action.wait_for_completed()
        return
            #time.sleep(.1)

###### PICTURE ######

    def picture(self, robot:cozmo.robot.Robot = None, cmd_args = None):

        robot.camera.image_stream_enabled = True
        print("taking a picture...")
        message = ""
        pic_filename = "cozmo_pic_" + str(int(time.time())) + ".png"
        robot.say_text("Say cheese!").wait_for_completed()
        latest_image = robot.world.latest_image
        if latest_image:
            latest_image.raw_image.convert('L').save(pic_filename)
            message =  "picture saved as: " + pic_filename
        else:
            message = "no picture saved"
        robot.camera.image_stream_enabled = False
        return message

#####what_is_this#####

    def recognize_img(self,path_to_img):
        # pip install tensorflow
        # cd cozmo_whatIsThis then  clone https://github.com/tensorflow/models
        # python classify_image.py  --model_dir tf/imagenset/ --image_file /tmp/o_100.jpg
        cmd = 'python classify_image.py --model_dir tf/imagenset/ --image_file ' + path_to_img
        p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
        stdout, stderr = p.communicate()
        result = stdout.decode("utf-8").split(",")[0]
        return result

    def what_is_this(self, robot:cozmo.robot.Robot = None, cmd_args = None):

            robot.camera.image_stream_enabled = True
            #  todo : surprise
            print("Taking photo")
            pic_filename = "cozmo_pic_" + "now" + ".png"
            robot.say_text("Let me think!", use_cozmo_voice=True, duration_scalar=0.7, voice_pitch=-1.0, in_parallel=True).wait_for_completed()
            latest_image = robot.world.latest_image
            if latest_image:
                latest_image.raw_image.convert('L').save(pic_filename)
                print ("Picture saved as " + pic_filename)
                recognize_out = self.recognize_img(pic_filename)
                print(recognize_out)
                robot.say_text("I think it is a {}".format(recognize_out), play_excited_animation=True,use_cozmo_voice=True, duration_scalar=0.7, voice_pitch=-1.0).wait_for_completed()
            else:
                print ("no picture saved")
            robot.camera.image_stream_enabled = False
            return

###### DRIVE ######

    def forward(self, robot:cozmo.robot.Robot = None, cmd_args = None, invert=False):

        if self.log:
            print(cmd_args)

        drive_duration = extract_next_float(cmd_args)#[0]

        if drive_duration is not None:

            if invert:
                drive_speed = speed
                drive_duration = -drive_duration
                drive_dir = "backwards"
            else:
                drive_speed = speed
                drive_dir = "forward"

            #robot.drive_wheels(drive_speed, drive_speed, duration=drive_duration)
            robot.drive_straight(distance_mm(drive_duration*drive_speed), speed_mmps(drive_speed), should_play_anim=True).wait_for_completed()
            #time.sleep(drive_duration)

            return "I drove " + drive_dir + " for " + str(drive_duration) + " seconds!"

        return "Error: bad drive duration!"

    def backward(self, robot:cozmo.robot.Robot = None, cmd_args = None):

        self.forward(robot, cmd_args, True)

###### TURN ######

    def left(self, robot:cozmo.robot.Robot = None, cmd_args = None, invert=False):

        drive_angle = extract_next_float(cmd_args)#[0]

        if drive_angle is None:
            drive_angle = 90;

        if invert:
            drive_angle = -drive_angle

        robot.turn_in_place(degrees(drive_angle)).wait_for_completed()
        return "I turned " + str(drive_angle) + " degrees!"

        #return "Error: bad drive angle!"

    def right(self, robot:cozmo.robot.Robot = None, cmd_args = None, invert=False):

        self.left(robot, cmd_args, True)
###### LIFT ######

    def lift(self, robot:cozmo.robot.Robot = None, cmd_args = None):

        lift_height = extract_next_float(cmd_args)#[0]

        if lift_height is not None:
            robot.set_lift_height(height=lift_height/100).wait_for_completed()
            return "I moved lift to " + str(lift_height)

        return "Error: bad height!"

###### HEAD ######

    def head(self, robot:cozmo.robot.Robot = None, cmd_args = None):

        head_angle_100 = extract_next_float(cmd_args)#[0]

        if head_angle_100 is not None:
            #FORMULA: Result = ((Input - InputLow) / (InputHigh - InputLow)) * (OutputHigh - OutputLow) + OutputLow;
            head_angle = head_angle_100/100 * (44 + 25) - 25;
            if self.log:
                print("head angle = ", head_angle)
            head_angle_action = robot.set_head_angle(degrees(head_angle))
            clamped_head_angle = head_angle_action.angle.degrees
            head_angle_action.wait_for_completed()
            resultString = "I moved head to " + "{0:.1f}".format(clamped_head_angle)
            if abs(head_angle - clamped_head_angle) > 0.01:
                resultString += " (clamped to range)"
            return resultString

        return "Error: bad angle!"

###### SAY ######

    def say(self, robot:cozmo.robot.Robot = None, cmd_args = None):

        entire_message = None
        if len(cmd_args) > 0:
            try:
                entire_message = ""
                for s in cmd_args:
                    entire_message = entire_message + " " + str(s)
                entire_message = entire_message.strip()
            except:
                pass

        if (entire_message is not None) and (len(entire_message) > 0):
            robot.say_text(entire_message).wait_for_completed()
            return 'I said "' + entire_message + '"!'

        return "Error: no message!"

###### CHARGER ######

    def charger(self, robot:cozmo.robot.Robot = None, cmd_args = None):

        trial = 1
        # try to find the charger
        charger = None

        # see if Cozmo already knows where the charger is
        
        if robot.world.charger:
            if robot.world.charger.pose.origin_id == robot.pose.origin_id:
                robot.say_text("I know where the charger is", play_excited_animation=True,use_cozmo_voice=True, duration_scalar=0.7, voice_pitch=-1.0).wait_for_completed()                    
                charger = robot.world.charger
            else:
                pass

        if not charger:
            robot.say_text("I am trying to find the charger", play_excited_animation=True,use_cozmo_voice=True, duration_scalar=0.7, voice_pitch=-1.0, in_parallel=False).wait_for_completed()
            
            look_around = robot.start_behavior(cozmo.behavior.BehaviorTypes.LookAroundInPlace)
            
            try:
                charger = robot.world.wait_for_observed_charger(timeout=None)
                robot.say_text("Found it!", play_excited_animation=True,use_cozmo_voice=True, duration_scalar=0.7, voice_pitch=-1.0, in_parallel=False).wait_for_completed()
            except asyncio.TimeoutError:
                robot.say_text("I couldn't find the charger", play_excited_animation=True,use_cozmo_voice=True, duration_scalar=0.7, voice_pitch=-1.0, in_parallel=False).wait_for_completed()
            finally:
                # whether we find it or not, we want to stop the behavior
                look_around.stop()

        if charger:
            robot.say_text("I will now lift my arms to maneuver to the base", play_excited_animation=True,use_cozmo_voice=True, duration_scalar=0.7, voice_pitch=-1.0, in_parallel=False).wait_for_completed()

            robot.move_lift(10)
            robot.say_text("I am going to align myself, I got this!", play_excited_animation=True,use_cozmo_voice=True, duration_scalar=0.7, voice_pitch=-1.0, in_parallel=False).wait_for_completed()
            
            action = robot.go_to_pose(charger.pose)
            action.wait_for_completed()
            
            print("Completed action: result = %s" % action)
            
            robot.drive_straight(distance_mm(-100), speed_mmps(5000)).wait_for_completed()
            
            robot.say_text("I think I am aligned!", play_excited_animation=True,use_cozmo_voice=True, duration_scalar=0.7, voice_pitch=-1.0, in_parallel=False).wait_for_completed()

            # Turn 180 (and 5) degrees, then goes backwards at full speed
            robot.say_text("And now for the finale, I will turn around", play_excited_animation=True,use_cozmo_voice=True, duration_scalar=0.7, voice_pitch=-1.0, in_parallel=False).wait_for_completed()
            #this value needs to be tweaked (90 or 95)
            
            robot.turn_in_place(degrees(90)).wait_for_completed()
            robot.turn_in_place(degrees(90)).wait_for_completed()
            
            # time.sleep( 1 )
            
            robot.say_text("Almost there!", play_excited_animation=True,use_cozmo_voice=True, duration_scalar=0.7, voice_pitch=-1.0, in_parallel=False).wait_for_completed()
            
            robot.drive_straight(distance_mm(-200), speed_mmps(5000)).wait_for_completed()
            
            robot.say_text("Am I on the base? I will check.", play_excited_animation=True,use_cozmo_voice=True, duration_scalar=0.7, voice_pitch=-1.0, in_parallel=False).wait_for_completed()
            
            if robot.is_on_charger:
                robot.move_lift(-8)
                robot.say_text("I did it! Yay", play_excited_animation=True,use_cozmo_voice=True, duration_scalar=0.7, voice_pitch=-1.0, in_parallel=False).wait_for_completed()
            else:
                robot.say_text("I did not make it, but I am not discouraged", play_excited_animation=True,use_cozmo_voice=True, duration_scalar=0.7, voice_pitch=-1.0, in_parallel=False).wait_for_completed()
                
                robot.world.charger = None
                robot.say_text("I will try again", play_excited_animation=True,use_cozmo_voice=True, duration_scalar=0.7, voice_pitch=-1.0, in_parallel=False).wait_for_completed()
            
                robot.drive_straight(distance_mm(150), speed_mmps(5000)).wait_for_completed()
            
                trial += 1
                if trial < 4:
                    self.charger(robot)
                else:
                    print("I am tired of trying, I will stop trying for now")
        return
