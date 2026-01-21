`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 2020/07/24 11:05:56
// Design Name: 
// Module Name: CHIP_SASEBO_GIII_kG_pro
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


module CHIP_SASEBO_GIII_ModMult(
// Local bus for GII
   lbus_di_a, lbus_do, lbus_wrn, lbus_rdn,
   lbus_clkn, lbus_rstn,

   // GPIO and LED
   gpio_startn, gpio_endn, gpio_exec, led,

   // Clock OSC
   osc_en_b
    );
     
     // Local bus for GII
     input [15:0]  lbus_di_a;
     output [15:0] lbus_do;
     input         lbus_wrn, lbus_rdn;
     input         lbus_clkn, lbus_rstn;
    
     // GPIO and LED
     output        gpio_startn, gpio_endn, gpio_exec;
     output [9:0]  led;
    
     // Clock OSC
     output        osc_en_b;
    
     //------------------------------------------------
     // Internal clock
     wire         clk, rst;
    
     // Local bus
     reg [15:0]   lbus_a, lbus_di;
     
     // Block cipher
     wire [255:0] in_a;    //由PC输入的模乘运算数a
//     wire [47:0] in_seed;      //由PC输入的随机数
     wire [255:0] in_b;     // 由PC输入的模乘运算数b
     wire [255:0] in_mod;       // 由PC输入的模乘模数mod
     wire [255:0] out_c;          //由签名模块输出的签名信息
     wire         blk_drdy, mult_done, all_drdy;
     wire         blk_encdec, blk_rstn;
     //reg          blk_drdy_delay;
     wire         en;                               //判断签名消息是否可以继续读入
     wire trigger;        //0 -> 1,触发信号； 2019.12.2 将trigger设置为标量乘开始执行的信号   
     //------------------------------------------------
     assign led[0] = rst;
     assign led[1] = lbus_rstn;
     assign led[2] = 1'b0;
     assign led[3] = blk_rstn;
     assign led[4] = blk_encdec;
     assign led[5] = all_drdy;
     assign led[6] = 0;
     assign led[7] = 1'b0;
     assign led[8] = mult_done;
     assign led[9] = ~en;
    
     assign osc_en_b = 1'b0;
     //------------------------------------------------
     always @(posedge clk) if (lbus_wrn)  lbus_a  <= lbus_di_a;
     always @(posedge clk) if (~lbus_wrn) lbus_di <= lbus_di_a;
     
     LBUS_IF lbus_if_pro
       (.lbus_a(lbus_a), .lbus_di(lbus_di), .lbus_do(lbus_do),
        .lbus_wr(lbus_wrn), .lbus_rd(lbus_rdn),
        .in_a(in_a), .in_b(in_b), .in_mod(in_mod), .en_recv(en),
        .out_c(out_c),
        .blk_drdy(blk_drdy), 
        //.all_drdy(all_drdy),
        .blk_dvld(mult_done),
        .blk_encdec(blk_encdec), .blk_rstn(blk_rstn),
        .clk(clk), .rst(rst));
    
     //------------------------------------------------
     assign gpio_startn = trigger;             //下降沿触发接口（即rst_pd由0 -> 1; gpio_startn由1 -> 0），表示开始执行
     //2019.12.3     此时的trigger设置为点倍开始的标志
     assign gpio_endn   = 1'b0; //~blk_dvld;
     assign gpio_exec   = 1'b0; //blk_busy;
    
     //always @(posedge clk) blk_drdy_delay <= blk_drdy;
     
     // 蒙哥马利模乘模块
     // 通过din_drdy控制是否开始执行
      Mont_mult_32_32 mult32(.clk(clk), .rst(blk_rstn), .din_rdy(blk_drdy), .data_a(in_a), .data_b(in_b), .data_m(in_mod), .m4u(1), .data_c(out_c), .trigger(trigger), .done(mult_done));

     //标量乘顶层模块
//     PM_Control_pro pm(.clk(clk), .rst(blk_rstn), .k(in_k), .Gx(in_Gx), .Gy(in_Gy), .in_ran_x(in_ran_x), .Qx(out_Qx), .Qy(out_Qy),
//     .din_rdy(blk_drdy), .valid(blk_vld), .trigger(trigger), .done(pm_done));
//     top_Sign_pro top_Sign_pro(.clk(clk), .rst(blk_rstn), .din(din), .din_rdy(blk_drdy), .last_din_num(last_din_num), 
//     .din_done(all_drdy), .da(in_da), .seed(in_seed), .en_recv(en), .out_r(out_r), .out_s(out_s), .valid(blk_vld), 
//     .trigger(trigger), .done(sig_done));
    
    //    AES_Composite_enc AES_Composite_enc
    //      (.Kin(blk_kin), .Din(blk_din), .Dout(blk_dout),
    //       .Krdy(blk_krdy), .Drdy(blk_drdy_delay), .Kvld(blk_kvld), .Dvld(blk_dvld),
    //       /*.EncDec(blk_encdec),*/ .EN(blk_en), .BSY(blk_busy),
    //       .CLK(clk), .RSTn(blk_rstn));
    
     //------------------------------------------------   
     MK_CLKRST mk_clkrst (.clkin(lbus_clkn), .rstnin(lbus_rstn),
                          .clk(clk), .rst(rst));
    
    endmodule
    
    //================================================ MK_CLKRST
    module MK_CLKRST (clkin, rstnin, clk, rst);
    //synthesis attribute keep_hierarchy of MK_CLKRST is no;
    
    //------------------------------------------------
    input  clkin, rstnin;
    output clk, rst;
    
    //------------------------------------------------
    wire   refclk;
    //   wire   clk_dcm, locked;
    
    //------------------------------------------------ clock
    IBUFG u10 (.I(clkin), .O(refclk)); 
    
    /*
    DCM_BASE u11 (.CLKIN(refclk), .CLKFB(clk), .RST(~rstnin),
                  .CLK0(clk_dcm),     .CLKDV(),
                  .CLK90(), .CLK180(), .CLK270(),
                  .CLK2X(), .CLK2X180(), .CLKFX(), .CLKFX180(),
                  .LOCKED(locked));
    BUFG  u12 (.I(clk_dcm),   .O(clk));
    */
    
    BUFG  u12 (.I(refclk),   .O(clk));
    
    //------------------------------------------------ reset
    MK_RST u20 (.locked(rstnin), .clk(clk), .rst(rst));
    endmodule // MK_CLKRST
    
    
    
    //================================================ MK_RST
    module MK_RST (locked, clk, rst);
    //synthesis attribute keep_hierarchy of MK_RST is no;
    
    //------------------------------------------------
    input  locked, clk;
    output rst;
    
    //------------------------------------------------
    reg [15:0] cnt;
    
    //------------------------------------------------
    always @(posedge clk or negedge locked) 
      if (~locked)    cnt <= 16'h0;
      else if (~&cnt) cnt <= cnt + 16'h1;
    
    assign rst = ~&cnt;

endmodule
