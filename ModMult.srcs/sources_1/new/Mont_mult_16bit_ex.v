`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 2024/09/10 11:17:54
// Design Name: 
// Module Name: Mont_mult_16bit_ex
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


module Mont_mult_16bit_ex(
    input clk,
    input rst,
    input din_rdy,
    input [255:0] data_a,
    input [255:0] data_b,
    input [255:0] data_m,        //模数p
    input [15:0]  m4u,           // 用来计算u的变量，由m计算出，作为预计算结果输入。当基底为32时，此值为1 
    output [255:0] data_c,       //模乘结果
    output trigger,             // 能量采集的触发
    output done                 //模乘完成标志位
    );
    
    reg [255:0] reg_b;          // 记录运算过程的中间值

    wire [31:0] u_temp;
    wire [15:0] u;

    wire [271:0] single_xy, single_um, tmp_xy_um;         // 循环中计算的中间结果

    wire [256:0] next_A;
    wire [272:0] before_A;                    // 移位前的A
    
    wire [256:0] result_A;
    reg [256:0] reg_result_A;         //蒙哥马利模乘结果

    // 8位乘法器
    reg [15:0] mult_a;
    // 存储b对应的乘法因子
    reg [15:0] b0, b1, b2, b3, b4, b5, b6, b7, b8, b9, b10, b11, b12, b13, b14, b15;
    wire [31:0] ab0, ab1, ab2, ab3, ab4, ab5, ab6, ab7, ab8, ab9, ab10, ab11, ab12, ab13, ab14, ab15;
    
    // 存储m对应的乘法因子
    reg [15:0] m0, m1, m2, m3, m4, m5, m6, m7, m8, m9, m10, m11, m12, m13, m14, m15;
    wire [31:0] um0, um1, um2, um3, um4, um5, um6, um7, um8, um9, um10, um11, um12, um13, um14, um15;

    reg [5:0] count;                  //记录迭代轮数，
        
    //标记状态
    reg [4:0] state, nextstate;
    
    reg reg_trig;
    
    parameter START = 0, LOOP_START = 1, LOOP = 2,  CHECK_SUB = 3, SUB = 4,  DONE = 5; 
    
    //组合逻辑
//    assign mult_res = mult1 * mult2;
    mult_gen_1 mul1(.A(mult_a), .B(b0), .P(ab0));
    mult_gen_1 mul2(.A(mult_a), .B(b1), .P(ab1));
    mult_gen_1 mul3(.A(mult_a), .B(b2), .P(ab2));
    mult_gen_1 mul4(.A(mult_a), .B(b3), .P(ab3));
    mult_gen_1 mul5(.A(mult_a), .B(b4), .P(ab4));
    mult_gen_1 mul6(.A(mult_a), .B(b5), .P(ab5));
    mult_gen_1 mul7(.A(mult_a), .B(b6), .P(ab6));
    mult_gen_1 mul8(.A(mult_a), .B(b7), .P(ab7));
    mult_gen_1 mul9(.A(mult_a), .B(b8), .P(ab8));
    mult_gen_1 mul10(.A(mult_a), .B(b9), .P(ab9));
    mult_gen_1 mul11(.A(mult_a), .B(b10), .P(ab10));
    mult_gen_1 mul12(.A(mult_a), .B(b11), .P(ab11));
    mult_gen_1 mul13(.A(mult_a), .B(b12), .P(ab12));
    mult_gen_1 mul14(.A(mult_a), .B(b13), .P(ab13));
    mult_gen_1 mul15(.A(mult_a), .B(b14), .P(ab14));
    mult_gen_1 mul16(.A(mult_a), .B(b15), .P(ab15));

//    assign ab0 = mult_a * b0;
//    assign ab1 = mult_a * b1;
//    assign ab2 = mult_a * b2;
//    assign ab3 = mult_a * b3;
//    assign ab4 = mult_a * b4;
//    assign ab5 = mult_a * b5;
//    assign ab6 = mult_a * b6;
//    assign ab7 = mult_a * b7;
//    assign ab8 = mult_a * b8;
//    assign ab9 = mult_a * b9;
//    assign ab10 = mult_a * b10;
//    assign ab11 = mult_a * b11;
//    assign ab12 = mult_a * b12;
//    assign ab13 = mult_a * b13;
//    assign ab14 = mult_a * b14;
//    assign ab15 = mult_a * b15;
    
    assign single_xy = ab0 + (ab1 << 16) + (ab2 << 32) + (ab3 << 48) + (ab4 << 64) + (ab5 << 80) + (ab6 << 96) + (ab7 << 112) + (ab8 << 128) 
    + (ab9 << 144) + (ab10 << 160) + (ab11 << 176) + (ab12 << 192) + (ab13 << 208) + (ab14 << 224) + (ab15 << 240);

    //初始第一轮时为0
    assign result_A = reg_result_A;
    //mult_temp1[63:0] 相当于a_i * y_0 
    assign u_temp = result_A[15:0] + single_xy[31:0];
    assign u = u_temp[15:0] * m4u;        //mod b

    mult_gen_1 mul17(.A(u), .B(m0), .P(um0));
    mult_gen_1 mul18(.A(u), .B(m1), .P(um1));
    mult_gen_1 mul19(.A(u), .B(m2), .P(um2));
    mult_gen_1 mul20(.A(u), .B(m3), .P(um3));
    mult_gen_1 mul21(.A(u), .B(m4), .P(um4));
    mult_gen_1 mul22(.A(u), .B(m5), .P(um5));
    mult_gen_1 mul23(.A(u), .B(m6), .P(um6));
    mult_gen_1 mul24(.A(u), .B(m7), .P(um7));
    mult_gen_1 mul25(.A(u), .B(m8), .P(um8));
    mult_gen_1 mul26(.A(u), .B(m9), .P(um9));
    mult_gen_1 mul27(.A(u), .B(m10), .P(um10));
    mult_gen_1 mul28(.A(u), .B(m11), .P(um11));
    mult_gen_1 mul29(.A(u), .B(m12), .P(um12));
    mult_gen_1 mul30(.A(u), .B(m13), .P(um13));
    mult_gen_1 mul31(.A(u), .B(m14), .P(um14));
    mult_gen_1 mul32(.A(u), .B(m15), .P(um15));

//    assign um0 = u * m0;
//    assign um1 = u * m1;
//    assign um2 = u * m2;
//    assign um3 = u * m3;
//    assign um4 = u * m4;
//    assign um5 = u * m5;
//    assign um6 = u * m6;
//    assign um7 = u * m7;
//    assign um8 = u * m8;
//    assign um9 = u * m9;
//    assign um10 = u * m10;
//    assign um11 = u * m11;
//    assign um12 = u * m12;
//    assign um13 = u * m13;
//    assign um14 = u * m14;
//    assign um15 = u * m15;

    
    assign single_um = um0 + (um1 << 16) + (um2 << 32) + (um3 << 48) + (um4 << 64) + (um5 << 80) + (um6 << 96) + (um7 << 112) + (um8 << 128) 
    + (um9 << 144) + (um10 << 160) + (um11 << 176) + (um12 << 192) + (um13 << 208) + (um14 << 224) + (um15 << 240);

    assign before_A = reg_result_A + single_xy + single_um;

    assign next_A = before_A >> 16;          // 每次循环完成后右移8位
    
    assign done = (state==DONE)?1:0;
    assign data_c = (state==DONE)?reg_result_A:0;       //0表示未完成
    
    assign trigger = reg_trig;
    
    //状态转移
    always@(posedge clk or negedge rst)
    begin
        if(!rst)
            state <= START;
        else
            state <= nextstate;
    end
    
    
    //次态逻辑
    always@(*)
    begin
    case(state)
    START:
        if(!rst || !din_rdy)
           nextstate = START;
        else
            nextstate = LOOP_START;
    LOOP_START:nextstate = LOOP;
    LOOP:
    begin
        if(count < 'd16)//进行16轮的循环
            nextstate = LOOP;
        else
            nextstate = CHECK_SUB;
    end
    CHECK_SUB:
    begin
        if(reg_result_A > data_m)
            nextstate = SUB;
        else
            nextstate = DONE;
    end
    SUB:nextstate = DONE;
    DONE:nextstate = DONE;
    endcase
    end
    
    always@(posedge clk)
    begin
    case(state)
    START:begin
        mult_a <= 0;
        reg_result_A <= 0;
        count <= 0;
        reg_b <= data_b[255:0];
        reg_trig <= 0;              // 标记触发
        b0 <= 0; b1 <=0; b2<=0;b3<=0;b4<=0;b5<=0;b6<=0;b7<=0;b8<=0;b9<=0;b10<=0;b11<=0;
        b12 <= 0; b13 <=0; b14<=0;b15<=0;
        m0 <= 0; m1 <=0; m2<=0;m3<=0;m4<=0;m5<=0;m6<=0;m7<=0;m8<=0;m9<=0;m10<=0;m11<=0;
        m12 <= 0; m13 <=0; m14<=0;m15<=0;

    end
    LOOP_START:begin
        reg_trig <= 1;
        reg_result_A <= 0;
        count <= count + 1;
        mult_a <= reg_b[15:0];
        reg_b <= reg_b >>16;

        b0 <= data_a[15:0]; b1 <=data_a[31:16]; b2<=data_a[47:32];b3<=data_a[63:48];b4<=data_a[79:64];b5<=data_a[95:80];
        b6<=data_a[111:96];b7<=data_a[127:112];b8<=data_a[143:128];b9<=data_a[159:144];b10<=data_a[175:160];b11<=data_a[191:176];
        b12 <= data_a[207:192]; b13 <=data_a[223:208]; b14<=data_a[239:224];b15<=data_a[255:240];
        
        m0 <= data_m[15:0]; m1 <=data_m[31:16]; m2<=data_m[47:32];m3<=data_m[63:48];m4<=data_m[79:64];m5<=data_m[95:80];
        m6<=data_m[111:96];m7<=data_m[127:112];m8<=data_m[143:128];m9<=data_m[159:144];m10<=data_m[175:160];m11<=data_m[191:176];
        m12 <= data_m[207:192]; m13 <=data_m[223:208]; m14<=data_m[239:224];m15<=data_m[255:240];

    end
    LOOP:begin
        mult_a <= reg_b[15:0];
        reg_b <= reg_b >>16;
        reg_result_A <= next_A;
        count <= count + 1;
    end
    SUB:reg_result_A <= reg_result_A - data_m;
    DONE: reg_trig <= 0;
    
    endcase
    end

    
    
endmodule