import ctypes
import sys
import time
import numpy as np
import io
import struct
from picosdk.ps5000a import ps5000a as ps
import matplotlib.pyplot as plt
from picosdk.functions import adc2mV, assert_pico_ok, mV2adc
from picosdk.constants import PICO_STATUS, PICO_STATUS_LOOKUP
from sm2_hard import *
import os
from sympy import mod_inverse, is_quad_residue, sqrt_mod

from picosdk.discover import find_all_units
from msvcrt import getch

class Acquire_kG:
    def __init__(self):
        self.chandle = ctypes.c_int16()     # handle
        self.resolution = ps.PS5000A_DEVICE_RESOLUTION["PS5000A_DR_8BIT"]  # resolution
        self.maxADC = ctypes.c_int16()
        self.status = {}
        self.num_samples = 1000
        self.time_interval = 0.0001 
        self.measure_samples = []           # 存执行采集
        self.trigger_samples = []           # 存触发曲线
        self.output_exe_file = None
        self.output_trigger_file = None
        # self.binary_writer = None
        self.inputRanges = [10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000]
        # status["openunit"] = ps.ps5000aOpenUnit(ctypes.byref(self.chandle), None, self.resolution)
        # 椭圆曲线参数
        self.a = int('fffffffbfffffffffffffffffffffffffffffffc00000003fffffffffffffffc',16)
        self.b = int('240fe188ba20e2c8527981505ea51c3c71cf379ae9b537ab90d230632bc0dd42', 16)
        self.p = int('FFFFFFFEFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF00000000FFFFFFFFFFFFFFFF', 16)
        self.r = 2**256
# Get Device Info
    def GetDeviceInfo(self):
        description = "Driver Version"
        required_size = ctypes.c_int16(0)
        line = ctypes.create_string_buffer(80)

        ps.ps5000aGetUnitInfo(self.chandle, line, 80, ctypes.byref(required_size), 0)

        print(f"{description}: {line.value}")

# Power Source Switch
    def PowerSourceSwitch(self, chandle: ctypes.c_int16, status):
        if status == PICO_STATUS['PICO_POWER_SUPPLY_NOT_CONNECTED']:
            print("5V Power Supply not connected") 
            print("Powering the unit via USB")
            status = ps.ps5000aChangePowerSource(chandle, status)
        elif status == PICO_STATUS['PICO_POWER_SUPPLY_CONNECTED']:
            print("5V Power Supply connected")
            status = ps.ps5000aChangePowerSource(chandle, status)
        elif status == PICO_STATUS['PICO_POWER_SUPPLY_UNDERVOLTAGE']:
            while status != PICO_STATUS['PICO_POWER_SUPPLY_REQUEST_INVALID']:
                print("USB not supplying required voltage. Please plug in the +5V power supply, then hit a key to continue, or Esc to exit...")
                ch = ord(getch())
                if ch == 0x1B:  # 检查是否按下Esc键（ASCII码为0x1B）
                    sys.exit(0)
                status = self.PowerSourceSwitch(chandle, PICO_STATUS['PICO_POWER_SUPPLY_CONNECTED'])
        
        return status

# Open Device
    def deviceOpen(self):
        status = ps.ps5000aOpenUnit(ctypes.byref(self.chandle), None, self.resolution)
        if status != PICO_STATUS['PICO_OK']:
            status = self.PowerSourceSwitch(self.chandle, status)
            if status == PICO_STATUS['PICO_POWER_SUPPLY_UNDERVOLTAGE']:
                status = self.PowerSourceSwitch(self.chandle, status)
            elif status == PICO_STATUS['PICO_USB3_0_DEVICE_NON_USB3_0_PORT']:
                status = self.PowerSourceSwitch(self.chandle, PICO_STATUS['PICO_POWER_SUPPLY_NOT_CONNECTED'])
        
        if status != PICO_STATUS['PICO_OK']:
            print(f"Failed to open unit: {PICO_STATUS_LOOKUP[status]}")
        else:
            print("handle:", str(self.chandle))

        return status
    
# 准备示波器，设置采样点数等
    def prepareScope(self, samples, numSegments):
        # 打开示波器
        if self.deviceOpen()!=PICO_STATUS['PICO_OK']:
            print("Failed to open unit")
            return False
       # 获取设备信息
        self.GetDeviceInfo()
        # 设置通道A和B, AC/DC采样，range待定
        chARange = ps.PS5000A_RANGE["PS5000A_10MV"]
        setA = ps.ps5000aSetChannel(self.chandle, ps.PS5000A_CHANNEL["PS5000A_CHANNEL_A"], 1, ps.PS5000A_COUPLING["PS5000A_AC"], chARange, 0)
        if setA != PICO_STATUS['PICO_OK']:
            print("Failed to set channel A")
            return False
        chBRange = ps.PS5000A_RANGE["PS5000A_1V"]
        setB = ps.ps5000aSetChannel(self.chandle, ps.PS5000A_CHANNEL["PS5000A_CHANNEL_B"], 1, ps.PS5000A_COUPLING["PS5000A_DC"], chBRange, 0)
        if setB != PICO_STATUS['PICO_OK']:
            print("Failed to set channel B")
            return False
        
        self.status["maximumValue"] = ps.ps5000aMaximumValue(self.chandle, ctypes.byref(self.maxADC))
        assert_pico_ok(self.status["maximumValue"])
        
        # 设置触发信号，通道B作为触发信号
        source = ps.PS5000A_CHANNEL["PS5000A_CHANNEL_B"]
        threshold = int(mV2adc(200,chBRange, self.maxADC))      # 200mv触发

        # direction = PS5000A_RISING = 2
        # delay = 0 s  
        # auto Trigger = 1000 ms
        self.status["trigger"] = ps.ps5000aSetSimpleTrigger(self.chandle, 1, source, threshold,  2, 0, 1000) # 触发信号设置为通道B，上升沿触发
        assert_pico_ok(self.status["trigger"])
        
        # # 设置内存段个数
        # nMaxSamples = ctypes.c_int32(0)
        # ret = ps.ps5000aMemorySegments(self.chandle, numSegments, ctypes.byref(nMaxSamples))
        # if ret != PICO_STATUS['PICO_OK']:
        #     print("Failed to set memory segments")
        #     return False
        
        return True
    
    # 执行一次采集，包括一次运算
    def getOneTrace(self, samples, startPercent, bt_k, bt_Gx, bt_Gy, bt_ran):

        
        # 设置采样率
        preTriggerSamples = samples*startPercent
        postTriggerSamples = samples * (1 - startPercent)
        maxSamples = samples

        # 在5000系列的ps5000aGetTimebase中（8bit分辨率），timebase = 0对应1000M， 1对应500M, 2对应250M, 3对应125M, 4对应62.5M, 5对应41.7M, 6对应31M, 7对应25M.
        timebase = 2

        timeIntervalns = ctypes.c_float()
        returnedMaxSamples = ctypes.c_int32()

        # 获取最大采样点数，设置采样率500M
        self.status["getTimebase"] = ps.ps5000aGetTimebase(self.chandle, timebase, maxSamples, ctypes.byref(timeIntervalns), ctypes.byref(returnedMaxSamples), 0)
        assert_pico_ok(self.status["getTimebase"])

        # print(timeIntervalns)
        # print(returnedMaxSamples)
        
        # 开始测量
        self.status["runBlock"] = ps.ps5000aRunBlock(self.chandle, int(preTriggerSamples), int(postTriggerSamples), timebase, None, 0, None, None)
        assert_pico_ok(self.status["runBlock"])
        time.sleep(0.05)

        # 执行硬件上的运算，其中设置超时自动关闭
        sm2 = SM2hard()

        flag, bt_qx, bt_qy, bt_t1_y, bt_t2_x, bt_t2_y = sm2.KG(bt_k, bt_Gx, bt_Gy, bt_ran)
        
        # -1说明传入的随机数不符要求
        if flag == -1:
            return False, None, None, None
        
        # 判断采样是否完成
        ifready = ctypes.c_int16(0)
        c = 0
        while ifready == 0:
            ps.ps5000aIsReady(self.chandle, ctypes.byref(ifready))
            if c>0:
                time.sleep(0.05) 
            c += 1
            if c>5:
                print("Sampling timeout")
                return False, None, None, None
        
        # set buffer
        bufferA = (ctypes.c_int16 * maxSamples)()         # 创建一个长度为maxsamples的数组
        source = ps.PS5000A_CHANNEL["PS5000A_CHANNEL_A"]

        self.status["setDataBufferA"] = ps.ps5000aSetDataBuffer(self.chandle, source, bufferA, maxSamples, 0, 0)
        assert_pico_ok(self.status["setDataBufferA"])

        # 保存触发曲线，以区分模乘
        bufferB = (ctypes.c_int16 * maxSamples)() 
        source = ps.PS5000A_CHANNEL["PS5000A_CHANNEL_B"]

        self.status["setDataBufferB"] = ps.ps5000aSetDataBuffer(self.chandle, source, bufferB, maxSamples, 0, 0)
        assert_pico_ok(self.status["setDataBufferB"])

        # 单条曲线测量完毕
        overflow = ctypes.c_int16()
        cmaxSamples = ctypes.c_int32(maxSamples)
        self.status["getValues"] = ps.ps5000aGetValues(self.chandle, 0, ctypes.byref(cmaxSamples), 0, 0, 0, ctypes.byref(overflow))
        assert_pico_ok(self.status["getValues"])

        self.measure_samples = bufferA             # 保存采集到的曲线
        self.trigger_samples = bufferB             #  保存触发曲线
        
        return True, bt_t1_y, bt_t2_x, bt_t2_y
    
    # 关闭示波器
    def closeScope(self):
        self.status["stop"] = ps.ps5000aStop(self.chandle)
        assert_pico_ok(self.status["stop"])
        self.status["close"]=ps.ps5000aCloseUnit(self.chandle)
        assert_pico_ok(self.status["close"])

    # 将采集信息输出至文件，生成trs文件等
    # 打开输出文件
    def openOutputFile(self, filenameA, filenameB):
        self.output_exe_file = open(filenameA, 'wb')
        self.output_trigger_file = open(filenameB, 'wb')
        # self.binary_writer = io.BytesIO()

    # 关闭输出文件
    def closeOutputFile(self):
        self.output_exe_file.close()
        self.output_trigger_file.close()
        # self.binary_writer.close()

    # 写默认trs文件头

    def write_exe_file_header(self, trace_num, sample_num, sample_coding, crypto_data_len, x_scale, y_scale):
        # 定义标记和长度常量
        MARK_TRACE_NUM = 0x41
        LEN_TRACE_NUM = 4
        MARK_SAMPLE_NUM = 0x42
        LEN_SAMPLE_NUM = 4
        MARK_SAMPLE_CODING = 0x43
        LEN_SAMPLE_CODING = 1
        MARK_CRYPTO_DATA_LEN = 0x44
        LEN_CRYPTO_DATA_LEN = 2
        MARK_X_SCALE = 0x4b
        LEN_X_SCALE = 4
        MARK_Y_SCALE = 0x4c
        LEN_Y_SCALE = 4
        MARK_END = 0x5f
        LEN_END = 0

        # 写入文件头
        print("写文件头")

        # 写TraceNum
        self.output_exe_file.write(struct.pack("<BBi", MARK_TRACE_NUM, LEN_TRACE_NUM, trace_num))

        # 写SampleNum
        self.output_exe_file.write(struct.pack("<BBi", MARK_SAMPLE_NUM, LEN_SAMPLE_NUM, sample_num))

        # 写SampleCoding
        self.output_exe_file.write(struct.pack("<BBB", MARK_SAMPLE_CODING, LEN_SAMPLE_CODING, sample_coding))

        # 写CryptoDataLen, H表示16比特无符号zheng'shu
        self.output_exe_file.write(struct.pack("<BBH", MARK_CRYPTO_DATA_LEN, LEN_CRYPTO_DATA_LEN, crypto_data_len))

        # 写XScale
        self.output_exe_file.write(struct.pack("<BBf", MARK_X_SCALE, LEN_X_SCALE, x_scale))

        # 写YScale
        self.output_exe_file.write(struct.pack("<BBf", MARK_Y_SCALE, LEN_Y_SCALE, y_scale))

        # 写结束标志
        self.output_exe_file.write(struct.pack("<BB", MARK_END, LEN_END))


    def write_trigger_file_header(self, trace_num, sample_num, sample_coding, crypto_data_len, x_scale, y_scale):
        # 定义标记和长度常量
        MARK_TRACE_NUM = 0x41
        LEN_TRACE_NUM = 4
        MARK_SAMPLE_NUM = 0x42
        LEN_SAMPLE_NUM = 4
        MARK_SAMPLE_CODING = 0x43
        LEN_SAMPLE_CODING = 1
        MARK_CRYPTO_DATA_LEN = 0x44
        LEN_CRYPTO_DATA_LEN = 2
        MARK_X_SCALE = 0x4b
        LEN_X_SCALE = 4
        MARK_Y_SCALE = 0x4c
        LEN_Y_SCALE = 4
        MARK_END = 0x5f
        LEN_END = 0

        # 写入文件头
        print("写文件头")

        # 写TraceNum
        self.output_trigger_file.write(struct.pack("<BBi", MARK_TRACE_NUM, LEN_TRACE_NUM, trace_num))

        # 写SampleNum
        self.output_trigger_file.write(struct.pack("<BBi", MARK_SAMPLE_NUM, LEN_SAMPLE_NUM, sample_num))

        # 写SampleCoding
        self.output_trigger_file.write(struct.pack("<BBB", MARK_SAMPLE_CODING, LEN_SAMPLE_CODING, sample_coding))

        # 写CryptoDataLen, H表示16比特无符号zheng'shu
        self.output_trigger_file.write(struct.pack("<BBH", MARK_CRYPTO_DATA_LEN, LEN_CRYPTO_DATA_LEN, crypto_data_len))

        # 写XScale
        self.output_trigger_file.write(struct.pack("<BBf", MARK_X_SCALE, LEN_X_SCALE, x_scale))

        # 写YScale
        self.output_trigger_file.write(struct.pack("<BBf", MARK_Y_SCALE, LEN_Y_SCALE, y_scale))

        # 写结束标志
        self.output_trigger_file.write(struct.pack("<BB", MARK_END, LEN_END))


    # 在trs文件中写入数据，曲线等
    def write_exe_trs(self, data: bytearray, samples: bytearray):
        self.output_exe_file.write(data)
        self.output_exe_file.write(samples)

    def write_trigger_trs(self, samples: bytearray):
        self.output_trigger_file.write(samples)
        
    # 根据随机生成的坐标点x计算坐标点y，传入的x是蒙哥马利化后的x
    def cal_y(self, ran_x):
        nmont_x = ran_x * mod_inverse(self.r, self.p) % self.p  # 去蒙哥马利化
        nmont_a = self.a * mod_inverse(self.r, self.p) % self.p

        mont_x = nmont_x*self.r % self.p

        nmont_b = self.b * mod_inverse(self.r, self.p) % self.p

        # 计算 y^2
        y_squared = (nmont_x**3 + nmont_a * nmont_x + nmont_b) % self.p
  
        # 检查 y^2 是否为二次剩余
        if not is_quad_residue(y_squared, self.p):
            return None  # 如果 y^2 不是二次剩余，返回 None
        
        # 计算 y
        y = sqrt_mod(y_squared, self.p)
        
        mont_y = y*self.r % self.p
        
        # print(hex(y))
        
        return mont_y
    
    # 进行采集，执行示波器和密码设备的开启，并进行多条曲线的采集等
    def MeasureTraces(self, exe_filename, trig_filename, sample_num, trace_num, data_len, startPercent):
        samplecoding = 0x02
        exe_XScale = 1e-8
        exe_YScale = self.inputRanges[ps.PS5000A_RANGE['PS5000A_10MV']] / 1000 * 0.001     # 待确定

        trig_XScale = 1e-8
        trig_YScale = self.inputRanges[ps.PS5000A_RANGE['PS5000A_500MV']] / 1000 * 0.001     # 待确定


        # 打开示波器
        print("Opening scope...")
        flag = self.prepareScope(sample_num, 1)
        if flag == 0:
            print("Opening scope failed!")
            return
        
        # 打开输出文件
        print("Opening output file...")
        self.openOutputFile(exe_filename, trig_filename)

        # 写文件头
        print("Writing file header...")
        self.write_exe_file_header(trace_num, sample_num, samplecoding, data_len, exe_XScale, exe_YScale)
        self.write_trigger_file_header(trace_num, sample_num, samplecoding, 0, trig_XScale, trig_YScale)

        # 执行采集循环
        print("Measuring traces...")
        i= 0
        
        # 固定基点
        bt_Gx = bytearray.fromhex('32C4AE2C1F1981195F9904466A39C9948FE30BBFF2660BE1715A4589334C74C7')
        bt_Gy = bytearray.fromhex('BC3736A2F4F6779C59BDCEE36B692153D0A9877CC62A474002DF32E52139F0A0')

        # 标量值
        bt_k = bytearray.fromhex('BC3736A2F4F6779C59BDCEE36B692153D0A9877CC62A474002DF32E52139F0A0')

        # 随机值
        # 生成256位的随机数，用十六进制表示，注将随机点保存到数据中，计算出x对应的y
        bt_ran = os.urandom(32)
        str_ran = bt_ran.hex()



        # 为了使AC采样在0附近，预先执行两次采样
        self.getOneTrace(sample_num, startPercent, bt_k, bt_Gx, bt_Gy, bt_ran)
        self.getOneTrace(sample_num, startPercent, bt_k, bt_Gx, bt_Gy, bt_ran)
        while i < trace_num:
            # 生成256位的随机数，用十六进制表示
            bt_ran = os.urandom(32)
            bt_ran = bt_ran[:-4]+ b'\x00'+ b'\x00'+ b'\x00'+ b'\x00'
            str_ran = bt_ran.hex()
            
            print("Measuring trace %d..." % (i + 1))
            # bt_b = bt_share6
                
            # flag = self.getOneTrace(sample_num, startPercent, bt_a, bt_b, bt_mod)
            flag, bt_t1_y, bt_t2_x, bt_t2_y = self.getOneTrace(sample_num, startPercent, bt_k, bt_Gx, bt_Gy, bt_ran)

            if flag == False:       # 采集失败(随机数错误)，则回退到前一条曲线
                i = i-1
            else:                
                int_y = self.cal_y(int.from_bytes(bt_ran, byteorder='big'))
                print("y: " + hex(int_y))                
                print("y: " + hex(self.p - int_y))
                bt_y = int_y.to_bytes(32, byteorder='big')
                print(bt_t1_y)
                print("Writing trace %d..." % (i + 1))
                merged_bt = bytearray()
                merged_bt.extend(bt_ran)
                merged_bt.extend(bt_t1_y)
                merged_bt.extend(bt_t2_x)
                merged_bt.extend(bt_t2_y)                
                merged_bt.extend(bt_k)
                bt_measure_samples = b''.join(struct.pack('<h', value) for value in self.measure_samples)
                bt_trigger_samples = b''.join(struct.pack('<h', value) for value in self.trigger_samples)
                self.write_exe_trs(merged_bt, bt_measure_samples)
                self.write_trigger_trs(bt_trigger_samples)
            i = i + 1

        print("Finished!")
        self.closeOutputFile()

        self.closeScope()
        
        return

if __name__ == '__main__':
    a = Acquire_kG()
    trace_num = 5
    sample_num = 60000000       # 在250M的采样率下，约60000000个点可采集完整的一次标量乘
    startpercent = 0.0001

    # str_a = '32C4AE2C1F1981195F9904466A39C9948FE30BBFF2660BE1715A4589334C74C7'
    # str_b = 'BC3736A2F4F6779C59BDCEE36B692153D0A9877CC62A474002DF32E52139F0A0'
    str_mod = 'FFFFFFFEFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF00000000FFFFFFFFFFFFFFFF'

    # bt_a = bytearray.fromhex(str_a)
    # bt_b = bytearray.fromhex(str_b)
    bt_mod = bytearray.fromhex(str_mod)

    exe_file = "kg_trs_low_4/kG_power_1115_end32bit0_5.trs"
    trig_file = "kg_trs_low_4/trig_power_1115_end32bit0_5.trs"
    
    
    # 存储的96字节数据包括：随机坐标t1（32字节x+32字节y），t2(64字节)，标量k（32字节）
    a.MeasureTraces(exe_file, trig_file, sample_num, trace_num, 160, startpercent)


    print("Done")

    