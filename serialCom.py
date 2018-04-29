import time
import io
import threading
import serial
import struct


class SerialCom(object):
    thread = None
    port = None

    motor1 = 1460
    motor2 = 1460
    motor3 = 1460
    motor4 = 90

    roll = 1.0
    pitch = 0.0
    yaw = 0.0
    temp = 0.0
    depth = 0.0
    voltage = 0.0

    def __init__(self, portName):
        self.port = serial.Serial(portName, 115200)

        self.a = 0
        self.b = 0
        self.c = 1460
        self.motor4 = 90
        self.light = 0
        self.hold_depth = 0
        self.hold_heading = 0
        self.hold_depth_status = 0
        self.hold_heading_status = 0

        self.pre_err = 0
        self.s = float(11) / 500
        self.p = 16 / 10
        self.d = 86 / 10
        self.err = 0
        self.d_err = 0
        self.pre_err = 0

        self.a2 = 0
        self.b2 = 0
        self.c2 = 1460

    def get_sensor_data(self):
        sensor_data = (self.roll, self.pitch, self.yaw,
                       self.temp, self.depth, self.voltage)
        return sensor_data

    def send_instruction(self, str_ins):
        if len(str_ins) == 7:
            self.a2 = str_ins[0]
            self.b2 = str_ins[1]
            self.c2 = str_ins[2]
            self.motor4 = str_ins[3]
            self.light = str_ins[4]

            if str_ins[6] == 1 and self.hold_depth_status == 0:
                self.hold_depth = self.depth
                print "sbbbbbbbbbbbbbbbbbbbbb"
            self.hold_depth_status = str_ins[6]

            if str_ins[5] == 1 and self.hold_heading_status == 0:
                self.hold_heading = self.yaw
                print "start heading"
                self.pre_err = 0
            self.hold_heading_status = str_ins[5]
            #self.__pid()

    def __pid(self):
        if abs(self.a - self.a2) > 90:
             self.a = self.a - (self.a - self.a2) / abs(self.a - self.a2) * 90
        else:
            self.a = self.a2
        if abs(self.b - self.b2) > 90:
            self.b = self.b - (self.b - self.b2) / abs(self.b - self.b2) * 90
        else:
            self.b = self.b2

        if abs(self.c - self.c2) > 60:
            self.c = self.c - (self.c - self.c2) /  abs(self.c - self.c2) * 60
        else:
            self.c = self.c2

        o1 = 1460 - self.a + self.b
        o2 = 1460 + self.a + self.b
        if self.hold_depth_status == 1:
            if self.c < 1520 and self.c > 1400:
                if self.hold_depth - self.depth > 0.05:
                    self.c = 1553 + (self.hold_depth - self.depth) * 600
                elif self.hold_depth - self.depth < -0.06:
                    self.c = 1405 + (self.hold_depth - self.depth) * 50
                else:
                    self.c = 1553
            else:
                self.hold_depth = self.depth

        if self.c > 1760:
            self.c = 1760
        if self.c < 1160:
            self.c = 1160

        if self.hold_heading_status == 1:
            self.err = self.hold_heading - self.yaw
            if self.err > 180:
                self.err = self.err - 360
            elif self.err < -180:
                self.err = self.err + 360
            print self.err
            self.d_err = self.err - self.pre_err
            print self.d_err
            if abs(self.a) > 60:
                o1 = o1 + self.s * \
                    self.err * (abs(self.a) - 60)
                o1 = o1 + self.s * \
                    self.err * (abs(self.b) - 60)
                if abs(self.b) > 20:
                    print "turning and forwarding"
                    self.hold_heading = self.yaw
                print "a>60"

            else:
                if abs(self.b) < 25:
                    if self.err < -2:
                        o1 = 1410 + self.err * self.p + self.d_err * self.d
                        o2 = o1
                        print "left"
                    elif self.err > 2:
                        o2 = 1510 + self.err * self.p + self.d_err * self.d
                        o1 = o2
                        print "right"
                    else:
                        o1 = 1460 - self.a
                        o2 = 1460 + self.a
                        print "center"
                    self.pre_err = self.err
                else:
                    print "turning"
                    self.hold_heading = self.yaw

        if o1 > 1760:
            o1 = 1760
        if o1 < 1160:
            o1 = 1160
        if o2 > 1760:
            o2 = 1760
        if o2 < 1160:
            o2 = 1160

        self.motor1 = o1
        self.motor2 = o2
        self.motor3 = self.c

    def ser_thread(self):
        pack1_ = struct.Struct('6is')
        unpack_ = struct.Struct('9f')
        # print "aaa"
        while True:
            #if abs(self.motor1 - self.) > 80:
            #     self.motor1 = self.motor1 - \
            #         (self.motor1 - self.a) / \
            #         abs(self.motor1 - self.a) * 80
            # else:
            #     self.motor1 = self.motor1

            # if abs(self.motor2 - self.b) > 80:
            #     self.motor2 = self.motor2 - \
            #         (self.motor2 - self.b) / \
            #         abs(self.motor2 - self.b) * 80
            # else:
            #     self.motor2 = self.b

            # if abs(self.motor3 - self.c) > 80:
            #     self.motor3 = self.motor3 - \
            #         (self.motor3 - self.c) / \
            #         abs(self.motor3 - self.c) * 80
            # else:
            #     self.motor3 = self.c

            # self.motor4 = self.motor4_

            t1 = time.time()
            self.__pid()
            tmp = (self.motor3, self.motor2, self.motor1,
                   self.motor4, self.light, 0, '\n')
            pack_data = pack1_.pack(*tmp)
            self.port.write(b'\x0f')
            self.port.write(pack_data)
            #print tmp

            while True:
                # print "st"
                xx = self.port.read()

                if xx == b'\xf0':
                    a = self.port.read(36)
                    tmp = unpack_.unpack(a)
                    self.roll = tmp[0]
                    self.pitch = tmp[1]
                    self.yaw = tmp[2]
                    self.temp = tmp[3]
                    self.depth = tmp[4]
                    self.voltage = tmp[5]

                    break
            t2 = time.time() - t1
            if t2 <0.1:
                time.sleep(t2/1000)

    def run(self):
        t1 = threading.Thread(target=self.ser_thread)
        t1.start()
        # t1.join()
