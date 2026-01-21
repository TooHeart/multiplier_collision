import ctypes
import os
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


from picosdk.discover import find_all_units
from msvcrt import getch

class Acquire_mult:
    def __init__(self):
        self.chandle = ctypes.c_int16()     # handle
        self.resolution = ps.PS5000A_DEVICE_RESOLUTION["PS5000A_DR_8BIT"]  # resolution
        self.maxADC = ctypes.c_int16()
        self.status = {}
        self.num_samples = 1000
        self.time_interval = 0.0001
        self.measure_samples = []
        self.output_file = None
        # self.binary_writer = None
        self.inputRanges = [10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000]
        # status["openunit"] = ps.ps5000aOpenUnit(ctypes.byref(self.chandle), None, self.resolution)

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
        chBRange = ps.PS5000A_RANGE["PS5000A_2V"]
        setB = ps.ps5000aSetChannel(self.chandle, ps.PS5000A_CHANNEL["PS5000A_CHANNEL_B"], 1, ps.PS5000A_COUPLING["PS5000A_DC"], chBRange, 0)
        if setB != PICO_STATUS['PICO_OK']:
            print("Failed to set channel B")
            return False
        
        self.status["maximumValue"] = ps.ps5000aMaximumValue(self.chandle, ctypes.byref(self.maxADC))
        assert_pico_ok(self.status["maximumValue"])
        
        # 设置触发信号，通道B作为触发信号
        source = ps.PS5000A_CHANNEL["PS5000A_CHANNEL_B"]
        threshold = int(mV2adc(100,chBRange, self.maxADC))      # 100mv

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
    def getOneTrace(self, samples, startPercent, bt_a, bt_b, bt_mod):

        
        # 设置采样率
        preTriggerSamples = samples*startPercent
        postTriggerSamples = samples * (1 - startPercent)
        maxSamples = samples

        # 在5000系列的ps5000aGetTimebase中（8bit分辨率），timebase = 0对应1000M， 1对应500M, 2对应250M, 3对应125M, 4对应62.5M, 5对应41.7M, 6对应31M, 7对应25M.
        timebase = 3

        timeIntervalns = ctypes.c_float()
        returnedMaxSamples = ctypes.c_int32()

        # 获取最大采样点数，设置采样率500M
        self.status["getTimebase"] = ps.ps5000aGetTimebase(self.chandle, timebase, maxSamples, ctypes.byref(timeIntervalns), ctypes.byref(returnedMaxSamples), 0)
        assert_pico_ok(self.status["getTimebase"])

        # print(timeIntervalns)
        # print(returnedMaxSamples)
        
        # 开始测量
        self.status["runBlock"] = ps.ps5000aRunBlock(self.chandle, preTriggerSamples, postTriggerSamples, timebase, None, 0, None, None)
        assert_pico_ok(self.status["runBlock"])
        time.sleep(0.05)

        # 执行硬件上的运算，其中设置超时自动关闭
        sm2 = SM2hard()
        flag, bt_c = sm2.ModMult(bt_a, bt_b, bt_mod)

        if flag == -1:
            return False
        
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
                return False
        
        # set buffer
        bufferA = (ctypes.c_int16 * maxSamples)()         # 创建一个长度为maxsamples的数组
        source = ps.PS5000A_CHANNEL["PS5000A_CHANNEL_A"]

        self.status["setDataBufferA"] = ps.ps5000aSetDataBuffer(self.chandle, source, bufferA, maxSamples, 0, 0)
        assert_pico_ok(self.status["setDataBufferA"])


        # 单条曲线测量完毕
        overflow = ctypes.c_int16()
        cmaxSamples = ctypes.c_int32(maxSamples)
        self.status["getValues"] = ps.ps5000aGetValues(self.chandle, 0, ctypes.byref(cmaxSamples), 0, 0, 0, ctypes.byref(overflow))
        assert_pico_ok(self.status["getValues"])

        self.measure_samples = bufferA             # 保存采集到的曲线

        return True
    
    # 关闭示波器
    def closeScope(self):
        self.status["stop"] = ps.ps5000aStop(self.chandle)
        assert_pico_ok(self.status["stop"])
        self.status["close"]=ps.ps5000aCloseUnit(self.chandle)
        assert_pico_ok(self.status["close"])

    # 将采集信息输出至文件，生成trs文件等
    # 打开输出文件
    def openOutputFile(self, filename):
        self.output_file = open(filename, 'wb')
        # self.binary_writer = io.BytesIO()

    # 关闭输出文件
    def closeOutputFile(self):
        self.output_file.close()
        # self.binary_writer.close()

    # 写默认trs文件头

    def write_file_header(self, trace_num, sample_num, sample_coding, crypto_data_len, x_scale, y_scale):
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
        self.output_file.write(struct.pack("<BBi", MARK_TRACE_NUM, LEN_TRACE_NUM, trace_num))

        # 写SampleNum
        self.output_file.write(struct.pack("<BBi", MARK_SAMPLE_NUM, LEN_SAMPLE_NUM, sample_num))

        # 写SampleCoding
        self.output_file.write(struct.pack("<BBB", MARK_SAMPLE_CODING, LEN_SAMPLE_CODING, sample_coding))

        # 写CryptoDataLen, H表示16比特无符号zheng'shu
        self.output_file.write(struct.pack("<BBH", MARK_CRYPTO_DATA_LEN, LEN_CRYPTO_DATA_LEN, crypto_data_len))

        # 写XScale
        self.output_file.write(struct.pack("<BBf", MARK_X_SCALE, LEN_X_SCALE, x_scale))

        # 写YScale
        self.output_file.write(struct.pack("<BBf", MARK_Y_SCALE, LEN_Y_SCALE, y_scale))

        # 写结束标志
        self.output_file.write(struct.pack("<BB", MARK_END, LEN_END))

    # 在trs文件中写入数据，曲线等
    def write_trs(self, data: bytearray, samples: bytearray):
        self.output_file.write(data)
        self.output_file.write(samples)


    def set_4bytes_with_hamming_weight(self, hamming_weight):
        # 检查汉明重量是否在有效范围内
        if hamming_weight < 0 or hamming_weight > 32:
            raise ValueError("汉明重量必须在 0 到 32 之间")
        # 初始化 32 位二进制数为 0
        binary_num = 0
        # 存储已经设置为 1 的位的索引
        used_positions = set()
        while len(used_positions) < hamming_weight:
            # 随机选择一个 0 到 31 之间的位索引
            position = random.randint(0, 31)
            if position not in used_positions:
                # 将对应位设置为 1
                binary_num |= (1 << position)
                used_positions.add(position)
        return binary_num


    # 进行采集，执行示波器和密码设备的开启，并进行多条曲线的采集等
    def MeasureTraces(self, output_filename, bt_mod, sample_num, trace_num, data_len, startPercent, hw_diff):
        samplecoding = 0x02
        XScale = 1e-8
        YScale = self.inputRanges[ps.PS5000A_RANGE['PS5000A_10MV']] / 1000 * 0.001     # 待确定

        # 打开示波器
        print("Opening scope...")
        flag = self.prepareScope(sample_num, 1)
        if flag == 0:
            print("Opening scope failed!")
            return
        
        # 打开输出文件
        print("Opening output file...")
        self.openOutputFile(output_filename)

        # 写文件头
        print("Writing file header...")
        self.write_file_header(trace_num, sample_num, samplecoding, data_len, XScale, YScale)

        # 执行采集循环
        print("Measuring traces...")
        i= 0


        str_share1 = '32C4AE2C1F1981195F9904466A39C9948FE30BBFF2660BE1715A4589334C0FF0'
        str_share2 = 'BC3736A2F4F6779C59BDCEE36B692153D0A9877CC62A474002DF32E52139F0A0'

        str_share3 = 'BC0000A21111079C59BDCEE360691111D0A98000C62A474002DF32050000F0A0'
        str_share3_ = 'BC3736A2F4F6779C000000006B692153D0A9877CC62A474002DF32E52139F0A0'

        str_share4 = 'BC0000A00001079C59B0000360600000D0A98000C6200040020032050000F0A0'

        str_share5 = 'BC000000000000000000000000600000D0A08000C6200040020032050000F0A0'

        str_share6 = '1111111111111111111111111111111111111111111111111111111111111111'

        str_share7 = '1001100110011001100110011001100110011001100110011001100110011001'

        # 与share6的汉明重量差距大
        str_share8 = 'FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF'
        str_share9 = 'FFFF0000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF'

        str_share10 = 'C4322CAE00001981995F4604396A94C9E38FBF0B66F2E10B5A7189454C33C774'

        str_share11 = 'FFFFFFFFFFFFFFFFFFFF0000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF'
        str_share12 = '1001100110011001100110011001100110011001100110011001100110010000'
        str_mod = 'FFFFFFFEFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF00000000FFFFFFFFFFFFFFFF'

        bt_share1 = bytearray.fromhex(str_share1)
        bt_share2 = bytearray.fromhex(str_share2)
        bt_share3 = bytearray.fromhex(str_share3) 
        bt_share3_ = bytearray.fromhex(str_share3_) 
        bt_share4 = bytearray.fromhex(str_share4) 
        bt_share5 = bytearray.fromhex(str_share5)
        bt_share6 = bytearray.fromhex(str_share6)
        bt_share7 = bytearray.fromhex(str_share7)
        bt_share8 = bytearray.fromhex(str_share8)
        bt_share9 = bytearray.fromhex(str_share9)
        bt_share10 = bytearray.fromhex(str_share10)        
        bt_share11 = bytearray.fromhex(str_share11)
        bt_share12 = bytearray.fromhex(str_share12)
        bt_mod = bytearray.fromhex(str_mod)


        bt_share1 = bytearray(32)
        for m in range(32):
            bt_share1[m] = random.randint(0, 255)

        # 依据汉明重量之差随机生成两个汉明重量
        # hw_diff = 0
        lhw = random.randint(0, 32-hw_diff)
        hhw = lhw + hw_diff

        binary_num = self.set_4bytes_with_hamming_weight(lhw)

        bt_share1[3] = (binary_num >> 24) & 0xFF
        bt_share1[2] = (binary_num >> 16) & 0xFF
        bt_share1[1] = (binary_num >> 8) & 0xFF
        bt_share1[0] = binary_num & 0xFF
        

        bt_another = bytearray(32)
        for m in range(32):
            bt_another[m] = random.randint(0, 255)

        binary_num = self.set_4bytes_with_hamming_weight(hhw)

        bt_another[3] = (binary_num >> 24) & 0xFF
        bt_another[2] = (binary_num >> 16) & 0xFF
        bt_another[1] = (binary_num >> 8) & 0xFF
        bt_another[0] = binary_num & 0xFF

        # 为了使AC采样在0附近，预先执行两次采样
        self.getOneTrace(sample_num, startPercent, bt_share1, bt_share2, bt_mod)
        self.getOneTrace(sample_num, startPercent, bt_share1, bt_share2, bt_mod)
        while i < trace_num:
            bt_a = bytearray(32)
            for m in range(32):
                bt_a[m] = random.randint(0, 255)


            print("Measuring trace %d..." % (i + 1))
            # bt_b = bt_share6
            if(i < trace_num/2):
                bt_b = bt_share1
            else:
                bt_b = bt_another
                
            # flag = self.getOneTrace(sample_num, startPercent, bt_a, bt_b, bt_mod)
            flag = self.getOneTrace(sample_num, startPercent, bt_a, bt_b, bt_mod)
            if flag == False:
                i = i-1
            else:
                print("Writing trace %d..." % (i + 1))
                merged_bt = bytearray()
                merged_bt.extend(bt_a)
                merged_bt.extend(bt_b)
                merged_bt.extend(bt_mod)
                bt_samples = b''.join(struct.pack('<h', value) for value in self.measure_samples)
                self.write_trs(merged_bt, bt_samples)
            i = i + 1

        print("Finished!")
        self.closeOutputFile()

        self.closeScope()
        
        return

if __name__ == '__main__':
    a = Acquire_mult()
    trace_num = 256
    sample_num = 5000   # 62.5MS的采样率，采集8位乘法器实现的模乘，约35000个点。在500M的采样率下，约20000个点可采集完整的一次模乘运算
    startpercent = 0

    # str_a = '32C4AE2C1F1981195F9904466A39C9948FE30BBFF2660BE1715A4589334C74C7'
    # str_b = 'BC3736A2F4F6779C59BDCEE36B692153D0A9877CC62A474002DF32E52139F0A0'
    str_mod = 'FFFFFFFEFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF00000000FFFFFFFFFFFFFFFF'

    # bt_a = bytearray.fromhex(str_a)
    # bt_b = bytearray.fromhex(str_b)
    bt_mod = bytearray.fromhex(str_mod)


    for hw_diff in range(26, 33, 4):
        output_folder = "8mults_32bit_256_125M_hwdiff" + str(hw_diff) + "/"

        if not os.path.exists(output_folder):
            # 如果不存在，则创建文件夹
            os.makedirs(output_folder)

        acq_group_num = 10
        # 采集100组曲线文件，每组中包含256个曲线，每个曲线包含20000个采样点
        for i in range(acq_group_num):
            output_file = output_folder + "trace_" + str(i) + ".trs"
            a.MeasureTraces(output_file, bt_mod, sample_num, trace_num, 96, startpercent, hw_diff)


    print("Done")