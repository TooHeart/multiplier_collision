`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 2019/12/16 16:15:30
// Design Name: 
// Module Name: Mont_mult_32
// Project Name: 
// Target Devices: 
// Tool Versions: 
// Description: 
//  以32位为基底的蒙哥马利模乘，此时-m的逆模2的32次方为1
// Dependencies: 
// 
// Revision:
// Revision 0.01 - File Created
// Additional Comments:
// 
//////////////////////////////////////////////////////////////////////////////////


module Mont_mult_32(
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
    
    reg [255:0] reg_a;
    reg [31:0] f1;
    wire [63:0] u_temp;      //32位乘法结果
    wire [31:0] u;
    wire [287:0] mult_temp1, mult_temp2;        //32*256的结果
    wire [256:0] result_A, next_A;
    wire [288:0] before_A;
    
    reg [256:0] reg_result_A;         //蒙哥马利模乘结果
    reg [3:0] count;                  //记录迭代轮数
    
    reg reg_trig;

    //标记状态
    reg [2:0] state, nextstate;
    
    parameter START = 0, LOOP_START = 1, LOOP = 2, CHECK_SUB = 3, SUB = 4, 
    DONE = 5;
    //组合逻辑
    assign mult_temp1 = f1 * data_b;
    //初始第一轮时为0
    assign result_A = reg_result_A;
    //mult_temp1[63:0] 相当于a_i * y_0 
    assign u_temp = result_A[31:0] + mult_temp1[63:0];
    assign u = u_temp[31:0] * m4u;        //mod b
    assign mult_temp2 = u * data_m;
    assign before_A = result_A + mult_temp1 + mult_temp2;
    assign next_A = before_A >> 32;
    
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
        if(count < 'd8)//此条件会使得count最终为8
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
        f1 <= 0;
        reg_result_A <= 0;
        count <= 0;
        reg_a <= data_a[255:0];
        reg_trig <= 0;              // 标记触发
    end
    LOOP_START:begin
        reg_trig <= 1;              // 标记触发
        f1 <= reg_a[31:0];
        reg_result_A <= 0;
        count <= count + 1;
        reg_a <= reg_a >> 32;
    end
    LOOP:begin
        f1 <= reg_a[31:0];
        reg_result_A <= next_A;
        reg_a <= reg_a >>32;
        count <= count + 1;
    end
    SUB:reg_result_A <= reg_result_A - data_m;
    DONE: reg_trig <= 0;

    endcase
    end
    
//    always@(posedge clk or negedge rst)
//    begin
//        if(!rst)
//        begin
//        //进入轮迭代，此周期用于稳定输入端口
//          count <= 15;
//          finish <= 0;
//        end
//        else
//        begin
//            if(count == 15)
//            begin
//                f1 <= 0;
//                reg_result_A <= 0;
//                count <= 0;
//                reg_a <= data_a;
//                finish <= 0;
//            end
//            else
//            begin
//                //第一轮
//                if(count==0)
//                begin
//                    f1 <= reg_a[31:0];
//                    reg_result_A <= 0;
//                    reg_a <= reg_a >>32;
//                    count <= count + 1;
//                end
//                else
//                begin
//                if(count != 0 && count< 8)
//                begin
//                    f1 <= reg_a[31:0];
//                    reg_result_A <= next_A;
//                    reg_a <= reg_a >>32;
//                    count <= count + 1;
//                end
//                else
//                begin
//                    finish <= 1;
//                end
//                end
//            end
//        end
//    end
    
endmodule
