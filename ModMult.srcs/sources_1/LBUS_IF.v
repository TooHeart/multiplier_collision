`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 2019/09/17 11:20:57
// Design Name: 
// Module Name: LBUS_IF
// Project Name: 
// Target Devices: 
// Tool Versions: 
// Description: 
// 
// Dependencies: 
// 
// Revision:
// Revision 0.01 - File Created
// Additional Comments:
// 
//////////////////////////////////////////////////////////////////////////////////


module LBUS_IF(
   lbus_a, lbus_di, lbus_do, lbus_wr, lbus_rd, // Local bus
   in_a, in_b, in_mod, en_recv, 
   out_c,
   blk_drdy, 
   //all_drdy, 
   blk_dvld,
   blk_encdec, blk_rstn,
   clk, rst
    );
       //------------------------------------------------
    // Local bus
    input [15:0]   lbus_a;  // Address
    input [15:0]   lbus_di; // Input data  (Controller -> Cryptographic module)
    input          lbus_wr; // Assert input data
    input          lbus_rd; // Assert output data
    output [15:0]  lbus_do; // Output data (Cryptographic module -> Controller)
 
    // 输出给模乘模块的数据
    output [255:0] in_a;         //由PC输入的标量k
    output [255:0] in_b;       //由PC输入的用于签名的48位随机数种子
    output [255:0] in_mod;
    
    input         en_recv;
    //output [127:0] blk_din;
    //由模乘模块输出的c
    input [255:0]  out_c;
    //input [127:0]  blk_dout;
    output         blk_drdy;
    //, all_drdy;        //前者对应签名模块中的din_rdy, 后者对应签名模块中的all_rdy
    input          blk_dvld;        //dvld表示标量乘完成
    output         blk_encdec;                //表示签名或验签（暂时默认均为签名）
    output         blk_rstn;                  //输出到下一模块的rst，在下一模块中0表示复位   
    // Clock and reset
    input         clk, rst;
 
    //------------------------------------------------
    reg [15:0]    lbus_do;
    
    reg [255:0]   in_a;  
    reg [255:0]   in_b;
    reg [255:0]  in_mod;
//    reg [31:0]    in_din;
//    reg [5:0]     last_num;             //最后一个消息分组的长度
    wire          en_recv;              //表示是否可以接收新的消息输入分组
    //reg [127:0]   blk_kin,  blk_din;
    //reg           blk_krdy;
    //reg [127:0]      blk_dout_reg;
    reg [255:0]   out_reg_c;
    reg           blk_drdy;
//    reg           all_drdy;
    reg           blk_encdec;
    reg           blk_rstn;
    
    reg [1:0]     wr;
    reg           trig_wr;
    wire          ctrl_wr;
    reg [2:0]     ctrl;
    //reg [3:0]     blk_trig;             //为什么将它设置为4位
 
    //------------写入状态获取-----------------------
    always @(posedge clk or posedge rst)
      if (rst) wr <= 2'b00;
      else     wr <= {wr[0],lbus_wr};
    
    always @(posedge clk or posedge rst)
      if (rst)            trig_wr <= 0;
      else if (wr==2'b01) trig_wr <= 1;
      else                trig_wr <= 0;
    
    //读入地址为0002时，读取到的数据为控制位信息
    assign ctrl_wr = (trig_wr & (lbus_a==16'h0002));
    
    
    //通过ctrl信号获取芯片内部执行状态，由PC端进行读取
    always @(posedge clk or posedge rst) 
      if (rst) ctrl <= 3'b001;
      else begin
         //if (blk_drdy)       ctrl[0] <= 1;
         //else 
         if (blk_dvld)  ctrl[0] <= 0;          //来自下层模块反馈，表示签名完毕
 
//         if (blk_dvld)     ctrl[1] <= 0;           //来自下层模块反馈，表示结果有效
//         else                           ctrl[1] <= 1;           //来自下层模块反馈，表示结果有效
         
         ctrl[2] <= ~blk_rstn;                      //rst时，ctrl2为1         
      end
 
    //获取标量乘模块的输出结果，存在寄存器中
    always @(posedge clk or posedge rst) 
      if (rst)
      begin
            out_reg_c <= 256'h0;
      end
      else 
      if (blk_dvld) 
      begin
            out_reg_c <= out_c;
      end
      
    //blk_trig用来表示和控制签名数据的传输
    //表示是否所有签名消息输入完毕
//    always @(posedge clk or posedge rst) 
//      if (rst)          blk_trig <= 4'h0;
//      else if (ctrl_wr) blk_trig <= {lbus_di[0],3'h0};
//      else              blk_trig <= {1'h0,blk_trig[3:1]};
      //此处不直接将di[0]赋值给blk_trig[0]，而是再经过3个周期后赋值到trig[0]，即blk_drdy上，
      //猜测是为了将赋值阶段与执行阶段分开？
    //assign blk_drdy = blk_trig[0];
    
    //all_drdy,表示所有签名消息已输入完毕（在最后一组消息输入时，该标志应在blk_drdy前进行）
//    //all_drdy赋值为1后，不在恢复为0 
//    always@(posedge clk or posedge rst)
//    begin
//        if(rst)             all_drdy <= 0;
//        else if(ctrl_wr)    all_drdy <= lbus_di[4];
//    end    
    
    //blk_drdy，表示该组32位消息输入完毕.由输入数据的第四位判断
    always@(posedge clk or posedge rst)
    begin
        if(rst)             blk_drdy <= 0;
        //else if(ctrl_wr)    blk_drdy <= lbus_di[3];
        else if(ctrl_wr)    blk_drdy <= lbus_di[3];
        else                blk_drdy <= 0;
    end
 
    //当crtl_wr为1时，若lbus_di[1]为1，表示密钥已准备好，传输完毕
//    always @(posedge clk or posedge rst) 
//      if (rst)          blk_krdy <= 0;
//      else if (ctrl_wr) blk_krdy <= lbus_di[1];
//      else              blk_krdy <= 0;
 
    //在crtl_wr为1的情况下，传输复位信号。
    always @(posedge clk or posedge rst) 
      if (rst)          blk_rstn <= 1;
      else if (ctrl_wr) blk_rstn <= ~lbus_di[2];
      else              blk_rstn <= 1;
    
    //------------------------------------------------
    //通过地址将签名密钥、随机数、待签名消息进行传入。PC中设置的低位数据在芯片中位于高位
    always @(posedge clk or posedge rst) begin
       if (rst) begin
          blk_encdec <= 0;              //用来标志签名或验签（目前只有签名功能）
          
          in_a <= 256'h0;                   //模乘操作数a,共256位，从地址0100开始
          in_b <= 256'h0;            //模乘操作数a,共256位，从地址从0140开始
          in_mod <= 256'h0;              // 模数
          //blk_kin <= 128'h0;
          //blk_din <= 128'h0;
       end else if (trig_wr) begin
          if (lbus_a==16'h000C) blk_encdec <= lbus_di[0];
          
//          //
//          if (lbus_a==16'h000E) last_num   <= lbus_di[5:0];
          
          //通过相应的地址输入标量k
          if (lbus_a==16'h0100) in_a[255:240] <= lbus_di;
          if (lbus_a==16'h0102) in_a[239:224] <= lbus_di;
          if (lbus_a==16'h0104) in_a[223:208] <= lbus_di;
          if (lbus_a==16'h0106) in_a[207:192] <= lbus_di;
          if (lbus_a==16'h0108) in_a[191:176] <= lbus_di;
          if (lbus_a==16'h010A) in_a[175:160] <= lbus_di;
          if (lbus_a==16'h010C) in_a[159:144] <= lbus_di;
          if (lbus_a==16'h010E) in_a[143:128] <= lbus_di;
          if (lbus_a==16'h0110) in_a[127:112] <= lbus_di;
          if (lbus_a==16'h0112) in_a[111:96] <= lbus_di;
          if (lbus_a==16'h0114) in_a[95:80] <= lbus_di;
          if (lbus_a==16'h0116) in_a[79:64] <= lbus_di;
          if (lbus_a==16'h0118) in_a[63:48] <= lbus_di;
          if (lbus_a==16'h011A) in_a[47:32] <= lbus_di;
          if (lbus_a==16'h011C) in_a[31:16] <= lbus_di;
          if (lbus_a==16'h011E) in_a[15:0] <= lbus_di;
          
          //通过相应的地址输入随机点的x
          if (lbus_a == 16'h0120) in_b[255:240] <= lbus_di;
          if (lbus_a == 16'h0122) in_b[239:224] <= lbus_di;
          if (lbus_a == 16'h0124) in_b[223:208] <= lbus_di;
          if (lbus_a == 16'h0126) in_b[207:192] <= lbus_di;
          if (lbus_a == 16'h0128) in_b[191:176] <= lbus_di;
          if (lbus_a == 16'h012A) in_b[175:160] <= lbus_di;
          if (lbus_a == 16'h012C) in_b[159:144] <= lbus_di;
          if (lbus_a == 16'h012E) in_b[143:128] <= lbus_di;
          if (lbus_a == 16'h0130) in_b[127:112] <= lbus_di;
          if (lbus_a == 16'h0132) in_b[111:96] <= lbus_di;
          if (lbus_a == 16'h0134) in_b[95:80] <= lbus_di;
          if (lbus_a == 16'h0136) in_b[79:64] <= lbus_di;
          if (lbus_a == 16'h0138) in_b[63:48] <= lbus_di;
          if (lbus_a == 16'h013A) in_b[47:32] <= lbus_di;
          if (lbus_a == 16'h013C) in_b[31:16] <= lbus_di;
          if (lbus_a == 16'h013E) in_b[15:0] <= lbus_di;
          
          // 通过相应的地址输入点的横坐标
          if (lbus_a == 16'h0150) in_mod[255:240] <= lbus_di;
          if (lbus_a == 16'h0152) in_mod[239:224] <= lbus_di;
          if (lbus_a == 16'h0154) in_mod[223:208] <= lbus_di;
          if (lbus_a == 16'h0156) in_mod[207:192] <= lbus_di;
          if (lbus_a == 16'h0158) in_mod[191:176] <= lbus_di;
          if (lbus_a == 16'h015A) in_mod[175:160] <= lbus_di;
          if (lbus_a == 16'h015C) in_mod[159:144] <= lbus_di;
          if (lbus_a == 16'h015E) in_mod[143:128] <= lbus_di;
          if (lbus_a == 16'h0160) in_mod[127:112] <= lbus_di;
          if (lbus_a == 16'h0162) in_mod[111:96] <= lbus_di;
          if (lbus_a == 16'h0164) in_mod[95:80] <= lbus_di;
          if (lbus_a == 16'h0166) in_mod[79:64] <= lbus_di;
          if (lbus_a == 16'h0168) in_mod[63:48] <= lbus_di;
          if (lbus_a == 16'h016A) in_mod[47:32] <= lbus_di;
          if (lbus_a == 16'h016C) in_mod[31:16] <= lbus_di;
          if (lbus_a == 16'h016E) in_mod[15:0] <= lbus_di;
           
       end
    end
                 
    //-----------------向PC输出的数据（签名值r和s）-------------------------
    always @(posedge clk or posedge rst)
      if (rst) 
        lbus_do <= 16'h0;
      else if (~lbus_rd)
        lbus_do <= mux_lbus_do(lbus_a, ctrl, en_recv, blk_encdec);
    
    function  [15:0] mux_lbus_do;
       input [15:0]   lbus_a;
       input [2:0]    ctrl;
       input          en_recv;
       input          blk_encdec;
       
       case(lbus_a)
         16'h0002: mux_lbus_do = ctrl;
         16'h0008: mux_lbus_do = en_recv;               //输出是否可以接收新的签名消息输入
         16'h000C: mux_lbus_do = blk_encdec;
         //输出din
//         16'h0170: mux_lbus_do = in_din[31:16];
//         16'h0172: mux_lbus_do = in_din[15:0] ;
         //输出drdy
         16'h0174: mux_lbus_do = blk_drdy;
         //输出in_Da
//         16'h0100: mux_lbus_do = in_da[255:240];
//         16'h0102: mux_lbus_do = in_da[239:224];
//         16'h0104: mux_lbus_do = in_da[223:208];
//         16'h0106: mux_lbus_do = in_da[207:192];
//         16'h0108: mux_lbus_do = in_da[191:176];
//         16'h010A: mux_lbus_do = in_da[175:160];
//         16'h010C: mux_lbus_do = in_da[159:144];
//         16'h010E: mux_lbus_do = in_da[143:128];
//         16'h0100: mux_lbus_do = in_da[127:112];
//         16'h0112: mux_lbus_do = in_da[111:96];
//         16'h0114: mux_lbus_do = in_da[95:80];
//         16'h0116: mux_lbus_do = in_da[79:64];
//         16'h0118: mux_lbus_do = in_da[63:48];
//         16'h011A: mux_lbus_do = in_da[47:32];
//         16'h011C: mux_lbus_do = in_da[31:16];
//         16'h011E: mux_lbus_do = in_da[15:0];

         //输出out_r
         16'h0190: mux_lbus_do = out_reg_c[255:240];
         16'h0192: mux_lbus_do = out_reg_c[239:224];
         16'h0194: mux_lbus_do = out_reg_c[223:208];
         16'h0196: mux_lbus_do = out_reg_c[207:192];
         16'h0198: mux_lbus_do = out_reg_c[191:176];
         16'h019A: mux_lbus_do = out_reg_c[175:160];
         16'h019C: mux_lbus_do = out_reg_c[159:144];
         16'h019E: mux_lbus_do = out_reg_c[143:128];
         16'h01A0: mux_lbus_do = out_reg_c[127:112];
         16'h01A2: mux_lbus_do = out_reg_c[111:96];
         16'h01A4: mux_lbus_do = out_reg_c[95:80];
         16'h01A6: mux_lbus_do = out_reg_c[79:64];
         16'h01A8: mux_lbus_do = out_reg_c[63:48];
         16'h01AA: mux_lbus_do = out_reg_c[47:32];
         16'h01AC: mux_lbus_do = out_reg_c[31:16];
         16'h01AE: mux_lbus_do = out_reg_c[15:0];

         16'hFFFC: mux_lbus_do = 16'h4702;
         default:  mux_lbus_do = 16'h0000;
       endcase
    endfunction

endmodule
