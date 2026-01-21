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
module Mont_mult_32_8(
    input clk,
    input rst,
    input din_rdy,
    input [255:0] data_a,
    input [255:0] data_b,
    input [255:0] data_m,        //模数p
    input [31:0]  m4u,           // 用来计算u的变量，由m计算出，作为预计算结果输入。当基底为32时，此值为1 
    output [255:0] data_c,       //模乘结果
    output trigger,
    output done                 //模乘完成标志位
    );
    
    (* keep = "true" *)reg [255:0] reg_a, reg_b, reg_m;          // 记录运算过程的中间值

    (* keep = "true" *)reg [31:0] temp_u;

    (* keep = "true" *)reg [287:0] single_xy, single_um, tmp_xy_um;         // 循环中计算的中间结果

//    reg [256:0] next_A;
//    wire [264:0] before_A;                    // 移位前的A
    
    (* keep = "true" *)reg [288:0] reg_result_A;         //蒙哥马利模乘结果
    (* keep = "true" *)reg reg_trig;

    // 32位乘法器
    (* keep = "true" *) reg [31:0] mult1, mult2;
    (* DONT_TOUCH= "TRUE" *) reg [63:0] reg_mult_res, reg_temp1, reg_temp2, reg_temp3, reg_temp4, reg_temp5, reg_temp6, reg_temp7, reg_temp8;
    (* DONT_TOUCH= "TRUE" *)wire [63:0] mult_res;
    
    (* DONT_TOUCH= "TRUE" *)wire [63:0] temp1, temp2, temp3, temp4, temp5, temp6, temp7, temp8;
    

    (* keep = "true" *)reg [5:0] count;                  //记录迭代轮数，
    
    (* keep = "true" *)reg [5:0] mul_cnt;                // 记录乘法过程中的轮数信息，将8*256分成32个8*8进行
    
    //标记状态
    (* keep = "true" *)reg [4:0] state, nextstate;
    
    parameter START = 0, LOOP_START = 1, LOOP = 2, CAL_XiY0 = 3, FINISH_STEP1 = 4, LOOP_XY = 5, CAL_XY = 12, XY_DONE = 15, LOOP_XY_DONE = 6, 
    LOOP_UM = 7, CAL_UM = 13, UM_DONE = 16, LOOP_UM_DONE = 8,
    CAL_A = 14, CHECK_SUB = 9, SUB = 10,  DONE = 11; 
    
    //组合逻辑
    assign mult_res = mult1 * mult2;
    assign temp1 = mult1 * mult2;
    assign temp2 = mult1 * mult2;
    assign temp3 = mult1 * mult2;
    assign temp4 = mult1 * mult2;
    assign temp5 = mult1 * mult2;
    assign temp6 = mult1 * mult2;
    assign temp7 = mult1 * mult2;
    assign temp8 = mult1 * mult2;

    

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
        if(count < 'd8)//此条件会使得count最终为32，进行32轮的循环
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
        if(mul_cnt< 'd7)
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
        if(mul_cnt< 'd7)
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
        
        reg_mult_res <= 0;
        reg_temp1 <= 0;
        reg_temp2 <= 0;
        reg_temp3 <= 0;
        reg_temp4 <= 0;
        reg_temp5 <= 0;
        reg_temp6 <= 0;
        reg_temp7 <= 0;
        reg_temp8 <= 0;
    end
    LOOP_START:begin
        reg_trig <= 1;              // 标记触发
        reg_result_A <= 0;
        count <= count + 1;
    end
    LOOP:begin
        reg_a <= reg_a >>32;
        reg_b <= data_b[255:0];
        reg_m <= data_m[255:0];
        count <= count + 1;
        single_xy <= 0;
        single_um <= 0;
    end
    CAL_XiY0:begin
        mult1 <= reg_a[31:0];
        mult2 <= data_b[31:0];
    end
    FINISH_STEP1:begin
        reg_temp1 <= temp1;
        reg_temp2 <= temp2;
        reg_temp3 <= temp3;
        reg_temp4 <= temp4;
        reg_temp5 <= temp5;
        reg_temp6 <= temp6;
        reg_temp7 <= temp7;
        reg_temp8 <= temp8;

        temp_u <= (reg_result_A[31:0] + mult_res) * m4u;         // 取最低8位
    end
    CAL_XY:begin
        mult1 <= reg_a[31:0];
        mult2 <= reg_b[31:0];
    end
    XY_DONE:begin
        reg_mult_res <= mult_res;
        
        reg_temp1 <= temp1;
        reg_temp2 <= temp2;
        reg_temp3 <= temp3;
        reg_temp4 <= temp4;
        reg_temp5 <= temp5;
        reg_temp6 <= temp6;
        reg_temp7 <= temp7;
        reg_temp8 <= temp8;

        tmp_xy_um <= mult_res << (mul_cnt *32);
    end
    LOOP_XY:begin
        mul_cnt <= mul_cnt + 1;
        single_xy <= single_xy + tmp_xy_um;
        reg_b <= reg_b >> 32;
    end
    LOOP_XY_DONE:begin
        mul_cnt <= 0;
    end
    CAL_UM:begin
        mult1 <= temp_u;
        mult2 <= reg_m[31:0];
    end
    UM_DONE:begin
        tmp_xy_um <= mult_res << (mul_cnt *32);
    end
    LOOP_UM:begin
        mul_cnt <= mul_cnt + 1;
        single_um <= single_um + tmp_xy_um;
        reg_m <= reg_m >> 32;
    end
    LOOP_UM_DONE:begin
        reg_result_A <= reg_result_A +  single_xy + single_um;
        mul_cnt <= 0;
    end
    CAL_A:begin
        reg_result_A <= reg_result_A >> 32;
    end
    SUB:reg_result_A <= reg_result_A - data_m;
    DONE: reg_trig <= 0;

    endcase
    end

    
    
endmodule
