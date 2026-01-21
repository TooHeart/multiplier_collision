`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 2024/02/26 11:46:43
// Design Name: 
// Module Name: Mont_mult_8bit
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


module Mont_mult_8bit(
    input clk,
    input rst,
    input din_rdy,
    input [255:0] data_a,
    input [255:0] data_b,
    input [255:0] data_m,        //模数p
    input [7:0]  m4u,           // 用来计算u的变量，由m计算出，作为预计算结果输入。当基底为32时，此值为1 
    output [255:0] data_c,       //模乘结果
    output trigger,             // 能量采集的触发
    output done                 //模乘完成标志位
    );
    
    reg [255:0] reg_a;          // 记录运算过程的中间值

    wire [15:0] u_temp;
    wire [7:0] u;

    wire [263:0] single_xy, single_um, tmp_xy_um;         // 循环中计算的中间结果

    wire [256:0] next_A;
    wire [264:0] before_A;                    // 移位前的A
    wire [256:0] result_A;
    reg [256:0] reg_result_A;         //蒙哥马利模乘结果

    // 8位乘法器
    reg [7:0] mult_a;
    // 存储b对应的乘法因子
    reg [7:0] b0, b1, b2, b3, b4, b5, b6, b7, b8, b9, b10, b11, b12, b13, b14, b15, b16, b17, b18, b19, b20, b21, b22, b23, b24, b25, b26, b27, b28, b29, b30, b31;
    wire [15:0] ab0, ab1, ab2, ab3, ab4, ab5, ab6, ab7, ab8, ab9, ab10, ab11, ab12, ab13, ab14, ab15, ab16, ab17, ab18, ab19, ab20, ab21, ab22, ab23, ab24, ab25, ab26, ab27, ab28, ab29, ab30, ab31;
    
    // 存储m对应的乘法因子
    reg [7:0] m0, m1, m2, m3, m4, m5, m6, m7, m8, m9, m10, m11, m12, m13, m14, m15, m16, m17, m18, m19, m20, m21, m22, m23, m24, m25, m26, m27, m28, m29, m30, m31;
    wire [15:0] um0, um1, um2, um3, um4, um5, um6, um7, um8, um9, um10, um11, um12, um13, um14, um15, um16, um17, um18, um19, um20, um21, um22, um23, um24, um25, um26, um27, um28, um29, um30, um31;

    reg [5:0] count;                  //记录迭代轮数，
        
    //标记状态
    reg [4:0] state, nextstate;
    
    reg reg_trig;
    
    parameter START = 0, LOOP_START = 1, LOOP = 2,  CHECK_SUB = 3, SUB = 4,  DONE = 5; 
    
    //组合逻辑
//    assign mult_res = mult1 * mult2;
//    wallace_mul8 mul0(.a(mult_a), .b(b0), .sum(ab0)); 
//    wallace_mul8 mul1(.a(mult_a), .b(b1), .sum(ab1)); 
//    wallace_mul8 mul2(.a(mult_a), .b(b2), .sum(ab2)); 
//    wallace_mul8 mul3(.a(mult_a), .b(b3), .sum(ab3)); 
//    wallace_mul8 mul4(.a(mult_a), .b(b4), .sum(ab4)); 
//    wallace_mul8 mul5(.a(mult_a), .b(b5), .sum(ab5)); 
//    wallace_mul8 mul6(.a(mult_a), .b(b6), .sum(ab6)); 
//    wallace_mul8 mul7(.a(mult_a), .b(b7), .sum(ab7)); 
//    wallace_mul8 mul8(.a(mult_a), .b(b8), .sum(ab8)); 

    assign ab0 = mult_a * b0;
    assign ab1 = mult_a * b1;
    assign ab2 = mult_a * b2;
    assign ab3 = mult_a * b3;
    assign ab4 = mult_a * b4;
    assign ab5 = mult_a * b5;
    assign ab6 = mult_a * b6;
    assign ab7 = mult_a * b7;
    assign ab8 = mult_a * b8;
    assign ab9 = mult_a * b9;
    assign ab10 = mult_a * b10;
    assign ab11 = mult_a * b11;
    assign ab12 = mult_a * b12;
    assign ab13 = mult_a * b13;
    assign ab14 = mult_a * b14;
    assign ab15 = mult_a * b15;
    assign ab16 = mult_a * b16;
    assign ab17 = mult_a * b17;
    assign ab18 = mult_a * b18;
    assign ab19 = mult_a * b19;
    assign ab20 = mult_a * b20;
    assign ab21 = mult_a * b21;
    assign ab22 = mult_a * b22;
    assign ab23 = mult_a * b23;
    assign ab24 = mult_a * b24;
    assign ab25 = mult_a * b25;
    assign ab26 = mult_a * b26;
    assign ab27 = mult_a * b27;
    assign ab28 = mult_a * b28;
    assign ab29 = mult_a * b29;
    assign ab30 = mult_a * b30;
    assign ab31 = mult_a * b31;
    
    assign single_xy = ab0 + (ab1 << 8) + (ab2 << 16) + (ab3 << 24) + (ab4 << 32) + (ab5 << 40) + (ab6 << 48) + (ab7 << 56) + (ab8 << 64) 
    + (ab9 << 72) + (ab10 << 80) + (ab11 << 88) + (ab12 << 96) + (ab13 << 104) + (ab14 << 112) + (ab15 << 120) + (ab16 << 128) + (ab17 << 136)
    + (ab18 << 144) + (ab19 << 152) + (ab20 << 160) + (ab21 << 168) + (ab22 << 176) + (ab23 << 184) + (ab24 << 192) + (ab25 << 200) + (ab26 << 208)
    + (ab27 << 216) + (ab28 << 224) + (ab29 << 232) + (ab30 << 240) + (ab31 << 248);

    //初始第一轮时为0
    assign result_A = reg_result_A;
    //mult_temp1[63:0] 相当于a_i * y_0 
    assign u_temp = result_A[7:0] + single_xy[15:0];
    assign u = u_temp[7:0] * m4u;        //mod b


    assign um0 = u * m0;
    assign um1 = u * m1;
    assign um2 = u * m2;
    assign um3 = u * m3;
    assign um4 = u * m4;
    assign um5 = u * m5;
    assign um6 = u * m6;
    assign um7 = u * m7;
    assign um8 = u * m8;
    assign um9 = u * m9;
    assign um10 = u * m10;
    assign um11 = u * m11;
    assign um12 = u * m12;
    assign um13 = u * m13;
    assign um14 = u * m14;
    assign um15 = u * m15;
    assign um16 = u * m16;
    assign um17 = u * m17;
    assign um18 = u * m18;
    assign um19 = u * m19;
    assign um20 = u * m20;
    assign um21 = u * m21;
    assign um22 = u * m22;
    assign um23 = u * m23;
    assign um24 = u * m24;
    assign um25 = u * m25;
    assign um26 = u * m26;
    assign um27 = u * m27;
    assign um28 = u * m28;
    assign um29 = u * m29;
    assign um30 = u * m30;
    assign um31 = u * m31;

    
    assign single_um = um0 + (um1 << 8) + (um2 << 16) + (um3 << 24) + (um4 << 32) + (um5 << 40) + (um6 << 48) + (um7 << 56) + (um8 << 64) 
    + (um9 << 72) + (um10 << 80) + (um11 << 88) + (um12 << 96) + (um13 << 104) + (um14 << 112) + (um15 << 120) + (um16 << 128) + (um17 << 136)
    + (um18 << 144) + (um19 << 152) + (um20 << 160) + (um21 << 168) + (um22 << 176) + (um23 << 184) + (um24 << 192) + (um25 << 200) + (um26 << 208)
    + (um27 << 216) + (um28 << 224) + (um29 << 232) + (um30 << 240) + (um31 << 248);

    assign before_A = reg_result_A + single_xy + single_um;

    assign next_A = before_A >> 8;          // 每次循环完成后右移8位
    
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
        if(count < 'd32)//此条件会使得count最终为32，进行32轮的循环
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
        reg_a <= data_a[255:0];
        reg_trig <= 0;              // 标记触发
        b0 <= 0; b1 <=0; b2<=0;b3<=0;b4<=0;b5<=0;b6<=0;b7<=0;b8<=0;b9<=0;b10<=0;b11<=0;
        b12 <= 0; b13 <=0; b14<=0;b15<=0;b16<=0;b17<=0;b18<=0;b19<=0;b20<=0;b21<=0;b22<=0;b23<=0;
        b24 <= 0; b25 <=0; b26<=0;b27<=0;b28<=0;b29<=0;b30<=0;b31<=0;
        m0 <= 0; m1 <=0; m2<=0;m3<=0;m4<=0;m5<=0;m6<=0;m7<=0;m8<=0;m9<=0;m10<=0;m11<=0;
        m12 <= 0; m13 <=0; m14<=0;m15<=0;m16<=0;m17<=0;m18<=0;m19<=0;m20<=0;m21<=0;m22<=0;m23<=0;
        m24 <= 0; m25 <=0; m26<=0;m27<=0;m28<=0;m29<=0;m30<=0;m31<=0;

    end
    LOOP_START:begin
        reg_trig <= 1;
        reg_result_A <= 0;
        count <= count + 1;
        mult_a <= reg_a[7:0];
        reg_a <= reg_a >>8;

        b0 <= data_b[7:0]; b1 <=data_b[15:8]; b2<=data_b[23:16];b3<=data_b[31:24];b4<=data_b[39:32];b5<=data_b[47:40];
        b6<=data_b[55:48];b7<=data_b[63:56];b8<=data_b[71:64];b9<=data_b[79:72];b10<=data_b[87:80];b11<=data_b[95:88];
        b12 <= data_b[103:96]; b13 <=data_b[111:104]; b14<=data_b[119:112];b15<=data_b[127:120];b16<=data_b[135:128];
        b17<=data_b[143:136];b18<=data_b[151:144];b19<=data_b[159:152];b20<=data_b[167:160];b21<=data_b[175:168];b22<=data_b[183:176];b23<=data_b[191:184];
        b24 <= data_b[199:192]; b25 <=data_b[207:200]; b26<=data_b[215:208];b27<=data_b[223:216];b28<=data_b[231:224];b29<=data_b[239:232];
        b30<=data_b[247:240];b31<=data_b[255:248];
        
        m0 <= data_m[7:0]; m1 <=data_m[15:8]; m2<=data_m[23:16];m3<=data_m[31:24];m4<=data_m[39:32];m5<=data_m[47:40];
        m6<=data_m[55:48];m7<=data_m[63:56];m8<=data_m[71:64];m9<=data_m[79:72];m10<=data_m[87:80];m11<=data_m[95:88];
        m12 <= data_m[103:96]; m13 <=data_m[111:104]; m14<=data_m[119:112];m15<=data_m[127:120];m16<=data_m[135:128];
        m17<=data_m[143:136];m18<=data_m[151:144];m19<=data_m[159:152];m20<=data_m[167:160];m21<=data_m[175:168];m22<=data_m[183:176];m23<=data_m[191:184];
        m24 <= data_m[199:192]; m25 <=data_m[207:200]; m26<=data_m[215:208];m27<=data_m[223:216];m28<=data_m[231:224];m29<=data_m[239:232];
        m30<=data_m[247:240];m31<=data_m[255:248];
    end
    LOOP:begin
        mult_a <= reg_a[7:0];
        reg_a <= reg_a >>8;
        reg_result_A <= next_A;
        count <= count + 1;
    end
    SUB:reg_result_A <= reg_result_A - data_m;
    DONE: reg_trig <= 0;
    
    endcase
    end

    
    
endmodule
