from ftdi_interface import *
import random
import math
import serial
import time


class SM2hard:

    def __init__(self):
        self.ADDR_CONT = 0x0002
        self.ADDR_ENRECV = 0x0008
        self.ADDR_MODE = 0x000C
        self.ADDR_LNUM = 0x000E
        self.ADDR_INK = 0x0100
        self.ADDR_INRAN = 0x0140
        self.ADDR_INGX = 0x0150
        self.ADDR_INGY = 0x0170

        self.ADDR_OUTQX = 0x0190
        self.ADDR_OUTQY = 0x0210

        # 设置为签名或验签，目前只有签名
        self.MODE_SIG = 0x0000
        self.MODE_VER = 0x0001

        # self.ftdi = SaseboGii()

        try:
            # 设置读取超时时间为1s
            self.data_com = serial.Serial("COM4", 19200, timeout=1, write_timeout=0)
        except IOError:
            raise IOError("UART Port Open Error")


    # rst
    def _open(self):
        rst = '01000200040100020000'
        rst_send = bytes.fromhex(rst)
        self.data_com.write(rst_send)
        # self.ftdi.write(self.ADDR_CONT, 0x0004)
        # self.ftdi.write(self.ADDR_CONT, 0x0000)

    def _close(self):
        self.data_com.close()

    # 向sasebo输入数据，随机数，密钥等

    # 设置标量
    def _setK(self, dat: bytes):
        k_addr = ['010100', '010102', '010104', '010106', '010108', '01010A', '01010C', '01010E', '010110', '010112', '010114', '010116', '010118', '01011A', '01011C', '01011E']
        k_send = [bytes.fromhex(k_addr[n]) + dat[2*n : 2*n + 2] for n in range(16)]         # 地址+数据
        self.data_com.write(b''.join(k_send))         # 将字节数组连接成一个字节串


    # 设置随机数种子
    def _setRanSeed(self, dat: bytes):
        ran_addr = ['010140', '010142', '010144']
        ran_send = [bytes.fromhex(ran_addr[n]) + dat[2*n : 2*n + 2] for n in range(3)]         # 地址+数据
        self.data_com.write(b''.join(ran_send))
        
    # 设置完整随机数
    def _setRan(self, dat: bytes):
        ran_addr = ['010120', '010122', '010124', '010126', '010128', '01012A', '01012C', '01012E', '010130', '010132', '010134', '010136', '010138', '01013A', '01013C', '01013E']
        ran_send = [bytes.fromhex(ran_addr[n]) + dat[2*n : 2*n + 2] for n in range(16)]         # 地址+数据
        self.data_com.write(b''.join(ran_send))

    # 设置标量乘中的点
    def _setGx(self, dat: bytes):
        gx_addr = ['010150', '010152', '010154', '010156', '010158', '01015A', '01015C', '01015E', '010160', '010162', '010164', '010166', '010168', '01016A', '01016C', '01016E']
        gx_send = [bytes.fromhex(gx_addr[n]) + dat[2*n : 2*n + 2] for n in range(16)]         # 地址+数据
        self.data_com.write(b''.join(gx_send))         # 将字节数组连接成一个字节串

    def _setGy(self, dat: bytes):
        gy_addr = ['010170', '010172', '010174', '010176', '010178', '01017A', '01017C', '01017E', '010180', '010182', '010184', '010186', '010188', '01018A', '01018C', '01018E']
        gy_send = [bytes.fromhex(gy_addr[n]) + dat[2*n : 2*n + 2] for n in range(16)]         # 地址+数据
        self.data_com.write(b''.join(gy_send))         # 将字节数组连接成一个字节串


    # 用于模乘中的参数设置
    def _setA(self, dat: bytes):
        a_addr = ['010100', '010102', '010104', '010106', '010108', '01010A', '01010C', '01010E', '010110', '010112', '010114', '010116', '010118', '01011A', '01011C', '01011E']
        a_send = [bytes.fromhex(a_addr[n]) + dat[2*n : 2*n + 2] for n in range(16)]         # 地址+数据
        self.data_com.write(b''.join(a_send))         # 将字节数组连接成一个字节串

    # 用于模乘中的参数设置
    def _setB(self, dat: bytes):
        b_addr = ['010120', '010122', '010124', '010126', '010128', '01012A', '01012C', '01012E', '010130', '010132', '010134', '010136', '010138', '01013A', '01013C', '01013E']
        b_send = [bytes.fromhex(b_addr[n]) + dat[2*n : 2*n + 2] for n in range(16)]         # 地址+数据
        self.data_com.write(b''.join(b_send))         # 将字节数组连接成一个字节串

    def _setMod(self, dat: bytes):
        mod_addr = ['010150', '010152', '010154', '010156', '010158', '01015A', '01015C', '01015E', '010160', '010162', '010164', '010166', '010168', '01016A', '01016C', '01016E']
        mod_send = [bytes.fromhex(mod_addr[n]) + dat[2*n : 2*n + 2] for n in range(16)]         # 地址+数据
        self.data_com.write(b''.join(mod_send))         # 将字节数组连接成一个字节串


    # 读取设备输出消息
    # def _readR(self, length:int):
    #     return self.ftdi.readBurst(self.ADDR_OUTR, length)
    #
    # def _readS(self, length:int):
    #     return self.ftdi.readBurst(self.ADDR_OUTS, length)

    def _readQx(self, length: int):
        outqx_addr = ['000190', '000192', '000194', '000196', '000198', '00019A', '00019C', '00019E', '0001A0', '0001A2', '0001A4', '0001A6', '0001A8', '0001AA', '0001AC', '0001AE']
        outqx_send = [bytes.fromhex(outqx_addr[n]) for n in range(16)]
        self.data_com.write(b''.join(outqx_send))
        return  self.data_com.read(32)                  # 读取16个地址对应的32个字节

        # return self.ftdi.readBurst(self.ADDR_OUTQX, length)

    def _readQy(self, length: int):
        outqy_addr = ['000210', '000212', '000214', '000216', '000218', '00021A', '00021C', '00021E', '000220', '000222', '000224', '000226', '000228', '00022A', '00022C', '00022E']
        outqy_send = [bytes.fromhex(outqy_addr[n]) for n in range(16)]
        self.data_com.write(b''.join(outqy_send))
        return  self.data_com.read(32)                  # 读取16个地址对应的32个字节

    def _readC(self, length: int):
        outc_addr = ['000190', '000192', '000194', '000196', '000198', '00019A', '00019C', '00019E', '0001A0', '0001A2', '0001A4', '0001A6', '0001A8', '0001AA', '0001AC', '0001AE']
        outc_send = [bytes.fromhex(outc_addr[n]) for n in range(16)]
        self.data_com.write(b''.join(outc_send))
        return  self.data_com.read(length)                  # 读取16个地址对应的32个字节

    def _readT1y(self, length: int):
        out_addr = ['000230', '000232', '000234', '000236', '000238', '00023A', '00023C', '00023E', '000240', '000242', '000244', '000246', '000248', '00024A', '00024C', '00024E']
        out_send = [bytes.fromhex(out_addr[n]) for n in range(16)]
        self.data_com.write(b''.join(out_send))
        return  self.data_com.read(32)                  # 读取16个地址对应的32个字节

    def _readT2x(self, length: int):
        out_addr = ['000250', '000252', '000254', '000256', '000258', '00025A', '00025C', '00025E', '000260', '000262', '000264', '000266', '000268', '00026A', '00026C', '00026E']
        out_send = [bytes.fromhex(out_addr[n]) for n in range(16)]
        self.data_com.write(b''.join(out_send))
        return  self.data_com.read(32)                  # 读取16个地址对应的32个字节

    def _readT2y(self, length: int):
        out_addr = ['000270', '000272', '000274', '000276', '000278', '00027A', '00027C', '00027E', '000280', '000282', '000284', '000286', '000288', '00028A', '00028C', '00028E']
        out_send = [bytes.fromhex(out_addr[n]) for n in range(16)]
        self.data_com.write(b''.join(out_send))
        return  self.data_com.read(32)                  # 读取16个地址对应的32个字节

    # 控制位传输
    def _blkdrdy(self):
        self.data_com.write(bytes.fromhex('0100020008'))


    def _iffinished(self):
        self.data_com.write(bytes.fromhex('000002'))
        finish_num = self.data_com.read(2)
        if int.from_bytes(finish_num, 'big') == 0:      # 标量乘完毕且结果有效
            return 1
        else:
            if int.from_bytes(finish_num, 'big') == 2:     # 标量乘完毕但结果无效
                return 2
            else:                   # 标量乘未完成
                return 0

    def ModMult(self, a: bytes, b:bytes, mod:bytes):
        self._open()
        flag = -1
        out_c = bytearray(32)
        if a is None or b is None or mod is None:
            print('it has error')
            self._close()
            return flag, "no c"
        # 设置运算数
        self._setA(a)
        self._setB(b)
        self._setMod(mod)

        self._blkdrdy()

        c = 0
        finish_return = 0
        # 检测是否完成，并设置超时时间
        while finish_return == 0:
            finish_return = self._iffinished()
            if c>0:
                time.sleep(0.05) 
            c += 1
            if c>100:
                self._close()
                print("Executing timeout")
                return flag, "no c"

        if finish_return == 1:
            out_c = self._readC(32)
            # 读取未超时
            if out_c != b'':
                flag = 0
        self._close()
        return flag, out_c


    def KG(self, k: bytes, Gx: bytes, Gy: bytes, ran_num: bytes):
        self._open()
        flag = -1
        out_qx = bytearray(32)
        out_qy = bytearray(32)
        out_t1_y = bytearray(32)
        out_t2_x = bytearray(32)
        out_t2_y = bytearray(32)
        if k is None or Gx is None or Gy is None:
            print('message or key has error')
            self._close()
            return flag, "no qx", "no qy"
        # 标量
        self._setK(k)
        # 随机数
        self._setRan(ran_num)

        self._setGx(Gx)
        self._setGy(Gy)

        self._blkdrdy()

        finish_return = 0
        while finish_return == 0:
            finish_return = self._iffinished()
        if finish_return == 1:
            out_qx = self._readQx(32)
            out_qy = self._readQy(32)
            out_t1_y = self._readT1y(32)
            out_t2_x = self._readT2x(32)
            out_t2_y = self._readT2y(32)
            flag = 0
        elif finish_return == 2:
            print("finished, but result is invalid")
            flag = -1

        self._close()
        return flag, out_qx, out_qy, out_t1_y, out_t2_x, out_t2_y



