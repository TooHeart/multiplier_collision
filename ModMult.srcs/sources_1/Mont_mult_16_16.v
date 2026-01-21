`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 2022/11/23 11:13:35
// Design Name: 
// Module Name: Mont_mult_8_8
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

// 蒙哥马利模乘，基本模块使用8位乘法器（8*8）完成
module Mont_mult_16_16(
    input clk,
    input rst,
    input din_rdy,
    input [255:0] data_a,
    input [255:0] data_b,
    input [255:0] data_m,        //模数p
    input [15:0]  m4u,           // 用来计算u的变量，由m计算出，作为预计算结果输入。当基底为32时，此值为1 
    output [255:0] data_c,       //模乘结果
    output trigger,
    output done                 //模乘完成标志位
    );
    
    reg [255:0] reg_a, reg_b, reg_m;          // 记录运算过程的中间值

    reg [15:0] temp_u;

    reg [271:0] single_xy, single_um, tmp_xy_um;         // 循环中计算的中间结果

//    reg [256:0] next_A;
//    wire [264:0] before_A;                    // 移位前的A
    
    reg [272:0] reg_result_A;         //蒙哥马利模乘结果

    // 16位乘法器
    reg [15:0] mult1, mult2;
    wire [31:0] mult_res;
    
    reg reg_trig;

    reg [5:0] count;                  //记录迭代轮数，
    
    reg [5:0] mul_cnt;                // 记录乘法过程中的轮数信息，将8*256分成32个8*8进行
    
    //标记状态
    reg [4:0] state, nextstate;
    
    parameter START = 0, LOOP_START = 1, LOOP = 2, CAL_XiY0 = 3, FINISH_STEP1 = 4, LOOP_XY = 5, CAL_XY = 12, XY_DONE = 15, LOOP_XY_DONE = 6, 
    LOOP_UM = 7, CAL_UM = 13, UM_DONE = 16, LOOP_UM_DONE = 8,
    CAL_A = 14, CHECK_SUB = 9, SUB = 10,  DONE = 11; 
    
    //组合逻辑
    assign mult_res = mult1 * mult2;

//    assign before_A = reg_result_A + single_xy + single_um;

//    assign next_A = before_A >> 8;          // 每次循环完成后右移8位
    
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
    LOOP_START:nextstate = CAL_XiY0;
    LOOP:
    begin
        if(count < 'd16)//此条件会使得count最终为32，进行32轮的循环
            nextstate = CAL_XiY0;
        else
            nextstate = CHECK_SUB;
    end
    CAL_XiY0:begin
        nextstate = FINISH_STEP1;
    end
    FINISH_STEP1:nextstate = CAL_XY;
    CAL_XY:nextstate = XY_DONE;
    XY_DONE:nextstate = LOOP_XY;
    LOOP_XY:begin
        if(mul_cnt< 'd15)
            nextstate = CAL_XY;
        else
            nextstate = LOOP_XY_DONE;
    end
    LOOP_XY_DONE:nextstate = CAL_UM;
    CAL_UM:begin
        nextstate = UM_DONE;
    end
    UM_DONE:nextstate = LOOP_UM;
    LOOP_UM:begin
        if(mul_cnt< 'd15)
            nextstate = CAL_UM;
        else
            nextstate = LOOP_UM_DONE;
    end
    LOOP_UM_DONE:nextstate = CAL_A;
    CAL_A:nextstate = LOOP;
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
        reg_result_A <= 0;
        count <= 0;
        reg_a <= data_a[255:0];
        reg_b <= data_b[255:0];
        reg_m <= data_m[255:0];
        single_xy <= 0;
        single_um <= 0;
        mult1 <= 0;
        mult2 <= 0;
        mul_cnt <= 0;
        temp_u <= 0;
        reg_trig <= 0;              // 标记触发
    end
    LOOP_START:begin
        reg_trig <= 1;              // 标记触发
        reg_result_A <= 0;
        count <= count + 1;
    end
    LOOP:begin
        reg_a <= reg_a >>16;
        reg_b <= data_b[255:0];
        reg_m <= data_m[255:0];
        count <= count + 1;
        single_xy <= 0;
        single_um <= 0;
    end
    CAL_XiY0:begin
        mult1 <= reg_a[15:0];
        mult2 <= data_b[15:0];
    end
    FINISH_STEP1:begin
        temp_u <= (reg_result_A[15:0] + mult_res) * m4u;         // 取最低8位
    end
    CAL_XY:begin
        mult1 <= reg_a[15:0];
        mult2 <= reg_b[15:0];
    end
    XY_DONE:begin
        tmp_xy_um <= mult_res << (mul_cnt *16);
    end
    LOOP_XY:begin
        mul_cnt <= mul_cnt + 1;
        single_xy <= single_xy + tmp_xy_um;
        reg_b <= reg_b >> 16;
    end
    LOOP_XY_DONE:begin
        mul_cnt <= 0;
    end
    CAL_UM:begin
        mult1 <= temp_u;
        mult2 <= reg_m[15:0];
    end
    UM_DONE:begin
        tmp_xy_um <= mult_res << (mul_cnt *16);
    end
    LOOP_UM:begin
        mul_cnt <= mul_cnt + 1;
        single_um <= single_um + tmp_xy_um;
        reg_m <= reg_m >> 16;
    end
    LOOP_UM_DONE:begin
        reg_result_A <= reg_result_A +  single_xy + single_um;
        mul_cnt <= 0;
    end
    CAL_A:begin
        reg_result_A <= reg_result_A >> 16;
    end
    SUB:reg_result_A <= reg_result_A - data_m;
    DONE: reg_trig <= 0;

    endcase
    end

    
    
endmodule
