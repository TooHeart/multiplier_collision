`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 2024/08/29 17:49:30
// Design Name: 
// Module Name: full_add8
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

module full_add8(
    input [15:0]a,
    input [15:0]b,
    input [15:0]c,
    output reg [15:0]cin,
    output reg [15:0]sum
    );


    integer i;
    always@(*)
    begin
        for(i=0;i<=15;i=i+1)
        begin
            sum[i]=a[i]^b[i]^c[i];
            cin[i+1]=(a[i]&b[i])|((a[i]|b[i])&c[i]);
        end
    end
     
 
endmodule
