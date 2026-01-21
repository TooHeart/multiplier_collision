`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 2024/08/29 17:47:16
// Design Name: 
// Module Name: wallace_mul8
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
module wallace_mul8(
    input [7:0] a,
    input [7:0] b,
    input data_valid,
    output [15:0] sum
    );
 
    reg [15:0]temp[7:0];
    reg [15:0]temp_reg[7:0];
    integer i;
    integer j;
    always@(*)
    begin
        if(data_valid)
        for(i=0;i<=7;i=i+1)
        begin
            temp[i]=16'b0;
            temp_reg[i]=16'b0;
            for(j=0;j<=7;j=j+1)
            begin
            temp[i][j]=(a[j]&b[i]);
            end
        end
        temp_reg[0]=temp[0];
        temp_reg[1]=temp[1]<<1;
        temp_reg[2]=temp[2]<<2;
        temp_reg[3]=temp[3]<<3;
        temp_reg[4]=temp[4]<<4;
        temp_reg[5]=temp[5]<<5;
        temp_reg[6]=temp[6]<<6;
        temp_reg[7]=temp[7]<<7;

    end
     
    wire [15:0]cin_1;
    wire [15:0]sum_1;
    wire [15:0]cin_2;
    wire [15:0]sum_2;
     
    full_add8 inst_full_add (.a(temp_reg[0]), .b(temp_reg[1]), .c(temp_reg[2]), .cin(cin_1), .sum(sum_1));
    full_add8 inst_full_add1 (.a(sum_1), .b(cin_1), .c(temp_reg[3]), .cin(cin_2), .sum(sum_2));
    assign sum=cin_2+sum_2;
 
endmodule
