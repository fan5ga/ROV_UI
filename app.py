#!/usr/bin/env python
from flask import Flask, render_template, Response, request
import time


# emulated camera
from camera import Camera

#from data import Data
from serialCom import SerialCom

# Raspberry Pi camera module (requires picamera package)
# from camera_pi import Camera
import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
app = Flask(__name__)
comm = SerialCom('/dev/ttyAMA0')

DirectionTab = [[0, 0], [0, 0], [300, 300],
                [-300, -300], [-200, 200], [200, -200]]


@app.route('/')
def index():
    """Video streaming home page."""
    return render_template('index_design.html')


def gen(camera):
    """Video streaming generator function."""
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route('/video_feed')
def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(gen(Camera()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/joystick_keyboard', methods=['POST', 'GET'])
def joystick_keyboard():
    if request.method == 'POST':
        joy = request.form['joystick']
        key = request.form['keyboard']
        light = request.form['light']
        hold = request.form['hold']

        key_value = (key.split(','))
        hold_value = hold.split(',')
        light_value = light.split(',')
        pressed_key = 0
        motor_arg = [0, 0]
        if len(key_value) == 6:
            for num in range(6):
                if key_value[num] == 'Y':
                    motor_arg[0] = motor_arg[0] + DirectionTab[num][0]
                    motor_arg[1] = motor_arg[1] + DirectionTab[num][1]
                    pressed_key = pressed_key + 1
            if pressed_key != 0:
                motor_arg[0] = motor_arg[0] / pressed_key + 1500
                motor_arg[1] = motor_arg[1] / pressed_key + 1500
            else:
                motor_arg = [1500, 1500]
        else:
            motor_arg = [1500, 1500]

        joy_value = (joy.split(','))
        if len(joy_value) == 3 and len(hold_value) ==2 and len(light_value)==2:
            motor_value = [int(joy_value[0]), int(
                joy_value[1]), int(joy_value[2]), int(light_value[1]), int(light_value[0]), int(hold_value[0]), int(hold_value[1]) ]
            comm.send_instruction(motor_value)
        #print hold_value[0]
        #print joy
        #print key
        #print motor_value

    return 'ok'


@app.route('/read_data')
def read_data():
    """"read data"""
    data = comm.get_sensor_data()
    #print data
    data_form = str(round(data[0], 1)) + '/' + str(round(data[1], 1)) + '/' + str(
        round(data[2], 1)) + '/' + str(round(data[3], 1)) + '/' + str(round(data[4], 1))+'/'+str(round(data[5],1))
    return data_form
    # return '1/1/1/1/1'


if __name__ == '__main__':
    comm.run()
    time.sleep(0.2)
    app.run(host='', debug=False, threaded=True)
