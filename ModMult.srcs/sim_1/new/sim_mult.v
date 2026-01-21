`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 2023/12/07 10:41:35
// Design Name: 
// Module Name: sim_mult
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

module sim_mult;
    reg clk;
    reg rst;
    reg [255:0] data_m;
    reg [255:0] data_a, data_b;
    
    reg [31:0] mult1, mult2;
    
    wire [63:0] mult_res;
    
    wire [255:0] data_c;
    wire done;
    
    //Mont_mult_32 m32(.clk(clk), .rst(rst), .data_a(data_a), .data_b(data_b), .data_m(data_m), .m4u(1), .data_c(data_c), .done(done));
    
    Mont_mult_8_8 m8(.clk(clk), .rst(rst), .din_rdy(1), .data_a(data_a), .data_b(data_b), .data_m(data_m), .m4u(1), .data_c(data_c), .done(done));

//    Mont_mult_16_16 m16(.clk(clk), .rst(rst), .data_a(data_a), .data_b(data_b), .data_m(data_m), .m4u(1), .data_c(data_c), .done(done));
    
//    Mont_mult_32bit m32(.clk(clk), .rst(rst), .data_a(data_a), .data_b(data_b), .data_m(data_m), .m4u(1), .data_c(data_c), .done(done));
//    Mont_mult_32bit_ex m32dsp(.clk(clk), .rst(rst), .data_a(data_a), .data_b(data_b), .data_m(data_m), .m4u(1), .data_c(data_c), .done(done));
//    Mont_mult_32_32_ex m32ex(.clk(clk), .rst(rst), .data_a(data_a), .data_b(data_b), .data_m(data_m), .m4u(1), .data_c(data_c), .done(done));
//    Mont_mult_8bit_ex m8(.clk(clk), .rst(rst), .data_a(data_a), .data_b(data_b), .data_m(data_m), .m4u(1), .data_c(data_c), .done(done));
//    Mont_mult_16bit_ex m16(.clk(clk), .rst(rst), .data_a(data_a), .data_b(data_b), .data_m(data_m), .m4u(1), .data_c(data_c), .done(done));
//      wallace_mul8 mul0(.a(mult1), .b(mult2), .data_valid(1), .sum(mult_res)); 
//      booth_m32 mul(.x(mult1), .y(mult2), .product(mult_res)); 

    initial
    begin
        clk = 0;
        rst = 0;
        data_m  = 256'hFFFFFFFEFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF00000000FFFFFFFFFFFFFFFF;
        data_a = 256'h32C4AE2C1F1981195F9904466A39C9948FE30BBFF2660BE1715A4589334C74C7;
        data_b = 256'hBC3736A2F4F6779C59BDCEE36B692153D0A9877CC62A474002DF32E52139F0A0;
        mult1 = 32'h1111;
        mult2 = 32'h1111;
        
        
        
        #25 rst = ~rst;

    end
    
    always #5 clk = ~clk;

endmodule
